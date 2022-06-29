from pathlib import Path

import jsonschema
import semver
import yaml
from jinja2 import FileSystemLoader
from sretoolbox.container import Image

from managedtenants.core.addon_manager import AddonManager
from managedtenants.core.addons_loader.bundle import Bundle
from managedtenants.core.addons_loader.exceptions import AddonLoadError
from managedtenants.core.addons_loader.package import Package
from managedtenants.core.addons_loader.sss import Sss
from managedtenants.data.paths import SCHEMAS_DIR
from managedtenants.utils.general_utils import parse_version_from_imageset_name
from managedtenants.utils.hash import hash_dir_sha256, hash_sha256
from managedtenants.utils.schema import load_schema

# IDs of addons that are managed by the addon-operator
# These addon IDs _MUST_ be stable and not changed or bad things will happen
# (this applies to addon IDs in general, but it's worth pointing out here, too)
_ADDON_OPERATOR_ADDON_IDS = []
_PERMITTED_SUBSCRIPTION_CONFIGS = ["env"]


class UniqueYAMLKeyLoader(yaml.CSafeLoader):
    def construct_mapping(self, node, deep=False):
        mapping = set()
        duplicates = []
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in mapping:
                duplicates.append(key)
            mapping.add(key)
        if duplicates:
            raise yaml.error.MarkedYAMLError(
                f"Duplicate key(s) found in addon.yaml : {duplicates}"
            )
        return super().construct_mapping(node, deep)


class Addon:
    def __init__(
        self,
        path,
        environment,
        override_manager=None,
        imageset_latest_only=False,
    ):
        self.path = path
        self.extra_resources_loader = None
        self.metadata = self.load_metadata(environment=environment)

        if "addonImageSetVersion" in self.metadata:
            self.imageset_version = self.metadata.get("addonImageSetVersion")
            self.imageset_latest_only = imageset_latest_only
            if self.imageset_version is None:
                self.imagesets_path = None
                self.imageset = None
                self.bundles = None
                self.package = None
                self.catalog_image = None
            else:
                if all(
                    [
                        self.imageset_latest_only,
                        self.imageset_version != "latest",
                    ]
                ):
                    raise AddonLoadError(
                        "Pointing to a specific version is "
                        "not allowed. Please use only latest. See"
                        " https://issues.redhat.com/browse/MTSRE-453 "
                        "for more info"
                    )
                self.imagesets_path = (
                    self.path / f"addonimagesets/{environment}"
                )
                self.imageset = self.load_imageset(self.imageset_version)
                self.package = None
                self.bundles = None
                self.catalog_image = self.imageset["indexImage"]

        elif "indexImage" in self.metadata:
            self.imagesets_path = None
            self.imageset = None
            self.bundles = None
            self.package = None
            self.catalog_image = self.metadata["indexImage"]
        else:
            # Local bundles doesn't exist anymore,
            # we have to clean this up
            self.imagesets_path = None
            self.imageset = None
            self.bundles = self.load_bundles(metadata=self.metadata)
            self.package = Package(addon=self)
            self.catalog_image = self.get_image_name(environment=environment)
        self.image_tag = (  # Used with .format(hash=...)
            f'{self.metadata["quayRepo"]}:{environment}-{{hash}}'
        )

        # We can only run these validations after the imageset is loaded.
        self._validate_additional_catalogue_srcs()
        self._validate_secret_names()
        self._validate_pullSecretName()

        if self.metadata["id"] not in _ADDON_OPERATOR_ADDON_IDS:
            self.manager = AddonManager.UKNOWN
        else:
            self.manager = AddonManager.ADDON_OPERATOR

        if override_manager is not None:
            self.manager = override_manager

        self.sss = Sss(addon=self)

    @property
    def name(self):
        return self.path.name

    def pull_secret_name(self):
        # For metadata's that use the legacy
        # pull secret, pull secret name is hardcoded to
        # "addon-pullsecret" in the SSS.
        if self.metadata.get("pullSecret"):
            return "addon-pullsecret"
        return self.get_pull_secret_name()

    def get_pull_secret_name(self, src=None):
        if src is None:
            return self.get_pull_secret_name(
                "imageset"
            ) or self.get_pull_secret_name("metadata")
        if src == "imageset" and self.imageset:
            return self.imageset.get("pullSecretName")
        return self.metadata.get("pullSecretName")

    # If src is None, check for config in the
    # imageset file, otherwise check for the default config
    # in the addon metadata file.
    def get_config(self, src=None):
        if src is None:
            return self.get_config(src="imageset") or self.get_config(
                "metadata"
            )
        if src == "imageset" and self.imageset:
            return self.imageset.get("config", {})
        return self.metadata.get("config", {})

    # Try getting the secrets from the imageset first,
    # if not present try getting it from the metadata.
    def get_secrets(self):
        return self.get_config("imageset").get("secrets") or self.get_config(
            "metadata"
        ).get("secrets")

    # Try getting the envs from the imageset first,
    # if not present try getting it from the metadata.
    def get_envs(self):
        return self.get_config("imageset").get("env") or self.get_config(
            "metadata"
        ).get("env")

    def get_additional_catalog_srcs(self, src=None):
        if src is None:
            return self.get_additional_catalog_srcs(
                src="imageset"
            ) or self.get_additional_catalog_srcs(src="metadata")
        if src == "imageset" and self.imageset:
            return self.imageset.get("additionalCatalogSources")
        return self.metadata.get("additionalCatalogSources")

    def get_image_name(self, environment):
        """
        Creates a deterministic image name that is unique per
        bundles + metadata hashed content.
        """
        bundles_dir = self.path / "bundles"
        bundles_hash = hash_dir_sha256(path=bundles_dir)

        metadata_dir = self.path / "metadata" / environment
        metadata_hash = hash_dir_sha256(path=metadata_dir)

        hash_tag = hash_sha256(items=(bundles_hash, metadata_hash))

        return Image(
            f'{self.metadata["quayRepo"]}:{environment}-{hash_tag[:7]}'
        )

    def load_metadata(self, environment):
        metadata_path = self.path / "metadata" / environment / "addon.yaml"
        metadata_dir = self.path / "metadata" / environment

        try:
            with open(metadata_path, encoding="utf8") as file_obj:
                metadata = yaml.load(
                    file_obj.read(), Loader=UniqueYAMLKeyLoader
                )
        except yaml.error.MarkedYAMLError as details:
            raise AddonLoadError(f"{metadata_path}: {details}")

        self._validate_schema_instance(metadata, "metadata")
        self._validate_extra_resources(environment, metadata)

        if "extraResources" in metadata:
            self.extra_resources_loader = FileSystemLoader(str(metadata_dir))
        return metadata

    def _validate_additional_catalogue_srcs(self):
        additional_catalog_srcs = self.get_additional_catalog_srcs()
        if additional_catalog_srcs:
            ctlg_src_names = [obj["name"] for obj in additional_catalog_srcs]
            if len(set(ctlg_src_names)) != len(ctlg_src_names):
                raise AddonLoadError(
                    f"{self.path} validation error: Additional catalog source"
                    " should have a unique name"
                )

    def _validate_secret_names(self):
        secrets = self.get_secrets()
        if secrets:
            secret_names = [secret.get("name") for secret in secrets]
            if len(set(secret_names)) != len(secret_names):
                raise AddonLoadError(
                    f"{self.path} validation error: secrets"
                    " should have a unique name"
                )

    def _validate_pullSecretName(self):
        if self.get_pull_secret_name():
            if not self.get_secrets():
                raise AddonLoadError(
                    f"{self.path} validation error: No secrets provided,"
                    " pullSecretName should be one of secrets' names"
                )
            secret_names = [secret.get("name") for secret in self.get_secrets()]
            if not self.get_pull_secret_name() in secret_names:
                raise AddonLoadError(
                    f"{self.path} validation error: pullSecretName should"
                    " be one of secrets' names"
                )

    def load_imageset(self, imageset_version):
        if not version_parsable(imageset_version):
            raise AddonLoadError("Addon imageset must be in semantic version")

        if not self.imagesets_path.is_dir():
            raise AddonLoadError(
                "imagesets directory missing at the path:"
                f" {self.imagesets_path}"
            )

        def is_not_none(arg):
            return arg is not None

        imageset_yamls = map(self.load_yaml, self.get_available_imagesets())
        valid_imagesets = filter(is_not_none, imageset_yamls)
        imageset = self.get_target_imageset(imagesets_iter=valid_imagesets)
        self._validate_schema_instance(imageset, "imageset")
        return imageset

    def get_available_imagesets(self):
        imageset_files = (
            p for p in self.imagesets_path.iterdir() if p.is_file()
        )
        return imageset_files

    def get_target_imageset(self, imagesets_iter):
        target_version = self.imageset_version

        def get_version(imageset_yaml):
            return parse_version_from_imageset_name(
                name=imageset_yaml.get("name", "")
            )

        def version_not_none(imageset_yaml):
            return get_version(imageset_yaml) is not None

        valid_imagesets = filter(version_not_none, imagesets_iter)
        # get the latest imageset
        if target_version == "latest":
            result = max(valid_imagesets, key=get_version)
            if not result:
                raise AddonLoadError("No valid imageset found!")
            return result

        result = find(
            iterator=valid_imagesets,
            key_func=get_version,
            item=target_version,
        )
        if not result:
            raise AddonLoadError(
                f'Imageset version "{target_version}" does not exist.'
            )
        return result

    def _validate_schema_instance(self, instance, schema_name):
        try:
            jsonschema.validate(
                instance=instance,
                schema=load_schema(schema_name),
                resolver=jsonschema.RefResolver(
                    base_uri=f"file://{SCHEMAS_DIR}/",
                    referrer=f"{schema_name}.schema.yaml",
                ),
            )
        except ValueError as details:
            raise AddonLoadError(
                f"Invalid schema name error: {details}"
            ) from details
        except jsonschema.exceptions.SchemaError as details:
            raise AddonLoadError(
                f"{schema_name} schema error: {details.message}"
            ) from details
        except jsonschema.exceptions.ValidationError as details:
            raise AddonLoadError(
                f"{self.path} validation error: {details.message}"
            ) from details

    def _validate_extra_resources(self, environment, metadata):
        if "extraResources" not in metadata:
            return

        for resource in metadata["extraResources"]:
            resource_path = self.path / "metadata" / environment / resource
            if not resource_path.is_file():
                raise AddonLoadError(
                    f"referenced resource {resource_path} not found"
                )

    @staticmethod
    def instantiate_bundle(args):
        return Bundle(path=args[0], metadata=args[1])

    @staticmethod
    def load_yaml(path):
        try:
            with open(path, encoding="utf8") as file_obj:
                data = yaml.load(file_obj.read(), Loader=yaml.CSafeLoader)
                return data
        except yaml.YAMLError:
            return None

    def load_bundles(self, metadata):
        bundles_path = self.path / "bundles"

        bundles_to_load = []
        for item in sorted(filter(Path.is_dir, bundles_path.iterdir())):
            if item.name == "OWNERS":
                continue

            bundles_to_load.append((item, metadata))

        # force list to not lazily evaluate the returned iterator of map()
        bundles = list(map(self.instantiate_bundle, bundles_to_load))

        self._validate_bundle_names(bundles)

        return bundles

    @staticmethod
    def _validate_bundle_names(bundles):
        for bundle in bundles:
            try:
                semver.parse(bundle.path.name)
            except ValueError as e:
                raise AddonLoadError(
                    f"{bundle.path} directory must be a semantic version"
                ) from e

    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self.name)})"


def find(iterator, item, key_func=None):
    """Returns the first item from the iterator
    which satisfies the given condition."""

    def predicate(arg):
        if key_func:
            return key_func(arg) == item
        return arg == item

    return next(filter(predicate, iterator), None)


def version_parsable(imageset_version):
    if imageset_version == "latest":
        return True
    try:
        semver.VersionInfo.parse(imageset_version)
        return True
    except ValueError:
        return False
