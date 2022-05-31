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


class Addon:
    """
    Loader for addons contained with the 'managed-tenants'
    repository structure. The primary entry point for this
    class is the 'from_path' method which given the path
    of an addon directory will determine the addon format
    and return an appropriate subclass instance.
    """

    def __init__(self, root, metadata, override_manager=None):
        self.root = root
        self.metadata = metadata

        self.manager = AddonManager.UKNOWN

        if override_manager is not None:
            self.manager = override_manager
        elif self.metadata["id"] in _ADDON_OPERATOR_ADDON_IDS:
            self.manager = AddonManager.ADDON_OPERATOR

        self.catalog_image = None
        self.extra_resources_loader = None

        if "extraResources" in metadata:
            self.extra_resources_loader = FileSystemLoader(
                str(root.metadata_dir())
            )

        self.image_tag = (  # Used with .format(hash=...)
            f'{metadata["quayRepo"]}:{root.environment}-{{hash}}'
        )

    @classmethod
    def from_path(
        cls,
        path,
        environment,
        override_manager=None,
        imageset_latest_only=False,
    ):
        """from_path

        :param path: Path to the root of an addon directory
        :type path: pathlib.Path
        :param environment: The addon environment to load. One
        of 'stage', 'integration', 'production'.
        :type environment: string
        :param override_manager: Forces a particular addon manager
        to be used, defaults to None
        :type override_manager: ADDON_MANAGER, optional
        :param imageset_latest_only: Enforces that version specified
        in the addon metadata is the latest imageset version, defaults to False
        :type imageset_latest_only: bool, optional
        :return: An initialized subclass of 'Addon'
        :rtype: ImageSetAddon | IndexImageAddon | LegacyAddon
        """
        root = _AddonRoot(path, environment)

        metadata = _MetadataLoader(root).metadata

        if metadata.get("addonImageSetVersion") is not None:
            return ImageSetAddon(
                root=root,
                metadata=metadata,
                override_manager=override_manager,
                imageset_latest_only=imageset_latest_only,
            )

        if metadata.get("indexImage"):
            return IndexImageAddon(
                root=root,
                metadata=metadata,
                override_manager=override_manager,
            )

        return LegacyAddon(
            root=root,
            metadata=metadata,
            override_manager=override_manager,
        )

    @property
    def name(self):
        return self.root.name()

    def pull_secret_name(self):
        # For metadata's that use the legacy
        # pull secret, pull secret name is hardcoded to
        # "addon-pullsecret" in the SSS.
        if self.metadata.get("pullSecret"):
            return "addon-pullsecret"
        if self.metadata.get("pullSecretName"):
            return self.metadata.get("pullSecretName")
        return None

    def get_subscription_config(self):
        return self.metadata.get("subscriptionConfig")

    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self.name)})"

    @staticmethod
    def requires_bundle_building():
        return False


class ImageSetAddon(Addon):
    def __init__(self, root, metadata, override_manager, imageset_latest_only):
        super().__init__(root, metadata, override_manager)

        version = self.metadata.get("addonImageSetVersion")

        # Do not allow pin-pointing a version
        # Temporary hot-fix for https://issues.redhat.com/browse/SDA-4918
        # See: https://issues.redhat.com/browse/MTSRE-453
        if imageset_latest_only and version != "latest":
            raise AddonLoadError(
                "Pointing to a specific version is not allowed. Please use"
                " only latest. See"
                " https://issues.redhat.com/browse/MTSRE-453 for more info"
            )

        self.imageset = self._load_imageset(root.imagesets_dir(), version)

        self.catalog_image = Image(self.imageset["indexImage"])

        self.sss = Sss(addon=self)

    def _load_imageset(self, path, version):
        if not _version_parsable(version):
            raise AddonLoadError("Addon imageset must be in semantic version")

        if not path.is_dir():
            raise AddonLoadError(
                f"imagesets directory missing at the path: {path}"
            )

        def is_not_none(arg):
            return arg is not None

        imageset_yamls = map(_load_yaml, self._get_available_imagesets(path))
        valid_imagesets = filter(is_not_none, imageset_yamls)
        imageset = self._get_target_imageset(
            imagesets_iter=valid_imagesets, version=version
        )
        _validate_schema_instance(path, imageset, "imageset")
        return imageset

    @staticmethod
    def _get_available_imagesets(path):
        imageset_files = (p for p in path.iterdir() if p.is_file())
        return imageset_files

    @staticmethod
    def _get_target_imageset(imagesets_iter, version):
        def get_version(imageset_yaml):
            return parse_version_from_imageset_name(
                name=imageset_yaml.get("name", "")
            )

        def version_not_none(imageset_yaml):
            return get_version(imageset_yaml) is not None

        valid_imagesets = filter(version_not_none, imagesets_iter)
        # get the latest imageset
        if version == "latest":
            result = max(valid_imagesets, key=get_version)
            if not result:
                raise AddonLoadError("No valid imageset found!")
            return result

        result = _find(
            iterator=valid_imagesets,
            key_func=get_version,
            item=version,
        )
        if not result:
            raise AddonLoadError(
                f'Imageset version "{version}" does not exist.'
            )
        return result

    def get_subscription_config(self):
        return self.imageset.get(
            "subscriptionConfig",
            super().get_subscription_config(),
        )


def _load_yaml(path):
    try:
        with open(path, encoding="utf8") as file_obj:
            data = yaml.load(file_obj.read(), Loader=yaml.CSafeLoader)
            return data
    except yaml.YAMLError:
        return None


def _version_parsable(version):
    if version == "latest":
        return True
    try:
        semver.VersionInfo.parse(version)
        return True
    except ValueError:
        return False


def _find(iterator, item, key_func=None):
    """Returns the first item from the iterator
    which satisfies the given condition."""

    def predicate(arg):
        if key_func:
            return key_func(arg) == item
        return arg == item

    return next(filter(predicate, iterator), None)


# IndexImage addon loader to be removed once migration
# to imagesets is complete
class IndexImageAddon(Addon):
    def __init__(self, root, metadata, override_manager):
        super().__init__(root, metadata, override_manager)

        self.sss = Sss(addon=self)


# Legacy addon loader to be removed once migration to
# managed-tenants-bundles is complete
class LegacyAddon(Addon):
    def __init__(self, root, metadata, override_manager):
        super().__init__(root, metadata, override_manager)

        self.bundles = self._load_bundles(metadata=metadata)
        self.package = Package(addon=self)
        self.catalog_image = self._get_image_name()

        self.sss = Sss(addon=self)

    def _load_bundles(self, metadata):
        bundles_path = self.root.bundles_dir()

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
    def instantiate_bundle(args):
        return Bundle(path=args[0], metadata=args[1])

    @staticmethod
    def _validate_bundle_names(bundles):
        for bundle in bundles:
            try:
                semver.parse(bundle.path.name)
            except ValueError as e:
                raise AddonLoadError(
                    f"{bundle.path} directory must be a semantic version"
                ) from e

    def _get_image_name(self):
        """
        Creates a deterministic image name that is unique per
        bundles + metadata hashed content.
        """
        bundles_dir = self.root.bundles_dir()
        bundles_hash = hash_dir_sha256(path=bundles_dir)

        metadata_dir = self.root.metadata_dir()
        metadata_hash = hash_dir_sha256(path=metadata_dir)

        hash_tag = hash_sha256(items=(bundles_hash, metadata_hash))

        return Image(
            f'{self.metadata["quayRepo"]}:'
            f"{self.root.environment}-{hash_tag[:7]}"
        )

    @staticmethod
    def requires_bundle_building():
        return True


class _MetadataLoader:
    def __init__(self, root):
        self.root = root
        self._metadata = self._load_metadata()

    def _load_metadata(self):
        metadata_path = self.root.metadata_dir() / "addon.yaml"

        try:
            with open(metadata_path, encoding="utf8") as file_obj:
                metadata = yaml.load(file_obj.read(), Loader=yaml.CSafeLoader)
        except yaml.error.MarkedYAMLError as details:
            raise AddonLoadError(f"{metadata_path}: {details}")

        _validate_schema_instance(metadata_path, metadata, "metadata")
        self._validate_extra_resources(metadata)
        self._validate_additional_catalogue_srcs(metadata)
        self._validate_secret_names(metadata)
        self._validate_pull_secret_name(metadata)

        return metadata

    def _validate_extra_resources(self, metadata):
        if "extraResources" not in metadata:
            return

        for resource in metadata["extraResources"]:
            resource_path = self.root.metadata_dir() / resource
            if not resource_path.is_file():
                raise AddonLoadError(
                    f"referenced resource {resource_path} not found"
                )

    def _validate_additional_catalogue_srcs(self, metadata):
        if metadata.get("additionalCatalogSources"):
            ctlg_src_names = [
                obj["name"] for obj in metadata["additionalCatalogSources"]
            ]
            if len(set(ctlg_src_names)) != len(ctlg_src_names):
                raise AddonLoadError(
                    f"{self.root.path} validation error: Additional"
                    " catalog source should have a unique name"
                )

    def _validate_secret_names(self, metadata):
        if metadata.get("secrets"):
            secret_names = [
                secret.get("name") for secret in metadata["secrets"]
            ]
            if len(set(secret_names)) != len(secret_names):
                raise AddonLoadError(
                    f"{self.root.path} validation error: secrets"
                    " should have a unique name"
                )

    def _validate_pull_secret_name(self, metadata):
        if metadata.get("pullSecretName"):
            if not metadata.get("secrets"):
                raise AddonLoadError(
                    f"{self.root.path} validation error: No secrets provided,"
                    " pullSecretName should be one of secrets' names"
                )
            secret_names = [
                secret.get("name") for secret in metadata["secrets"]
            ]
            if not metadata["pullSecretName"] in secret_names:
                raise AddonLoadError(
                    f"{self.root.path} validation error: pullSecretName should"
                    " be one of secrets' names"
                )

    @property
    def metadata(self):
        return self._metadata


def _validate_schema_instance(path, instance, schema_name):
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
            f"{path} validation error: {details.message}"
        ) from details


class _AddonRoot:
    def __init__(self, path, environment):
        self._path = path
        self._environment = environment

    @property
    def path(self):
        return self._path

    @property
    def environment(self):
        return self._environment

    def name(self):
        return self._path.name

    def bundles_dir(self):
        return self._path / "bundles"

    def metadata_dir(self):
        return self._path / "metadata" / self._environment

    def imagesets_dir(self):
        return self._path / "addonimagesets" / self._environment
