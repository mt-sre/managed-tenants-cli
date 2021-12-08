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
from managedtenants.utils.general_utils import parse_version_from_imageset_name
from managedtenants.utils.hash import hash_dir_sha256, hash_sha256
from managedtenants.utils.schema import (
    load_addon_imageset_schema,
    load_addon_metadata_schema,
)

# IDs of addons that are managed by the addon-operator
# These addon IDs _MUST_ be stable and not changed or bad things will happen
# (this applies to addon IDs in general, but it's worth pointing out here, too)
_ADDON_OPERATOR_ADDON_IDS = ["reference-addon"]
_PERMITTED_SUBSCRIPTION_CONFIGS = ["env"]


class Addon:
    def __init__(self, path, environment):
        self.path = path
        self.extra_resources_loader = None
        self.metadata = self.load_metadata(environment=environment)
        self.imageset_version = self.metadata.get("addonImageSetVersion")
        # If imagebundles are provided
        if self.imageset_version is not None:
            self.imagesets_path = self.path / f"addonimagesets/{environment}"
            self.imageset = self.load_imageset(self.imageset_version)
            self.package = None
            self.bundles = None
            self.catalog_image = Image(self.imageset["indexImage"])
        # remove this after
        elif self.metadata.get("indexImage"):
            self.imagesets_path = None
            self.imageset = None
            self.bundles = None
            self.package = None
            self.catalog_image = None
        else:
            self.imagesets_path = None
            self.imageset = None
            self.bundles = self.load_bundles(metadata=self.metadata)
            self.package = Package(addon=self)
            self.catalog_image = self.get_image_name(environment=environment)
        self.image_tag = (  # Used with .format(hash=...)
            f'{self.metadata["quayRepo"]}:{environment}-{{hash}}'
        )

        if self.metadata["id"] not in _ADDON_OPERATOR_ADDON_IDS:
            self.manager = AddonManager.UKNOWN
        else:
            self.manager = AddonManager.ADDON_OPERATOR

        self.sss = Sss(addon=self)

    @property
    def name(self):
        return self.path.name

    def get_subscription_config(self):
        # If imageset is present, check for subscriptionConfig in the
        # imageset file, otherwise check for the default subscription config
        # in the addon metadata file.
        if self.imageset and self.imageset.get("subscriptionConfig"):
            return self.imageset.get("subscriptionConfig")
        return self.metadata.get("subscriptionConfig")

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
                metadata = yaml.load(file_obj.read(), Loader=yaml.CSafeLoader)
        except yaml.error.MarkedYAMLError as details:
            raise AddonLoadError(f"{metadata_path}: {details}")

        self._validate_schema(metadata)
        self._validate_extra_resources(environment, metadata)

        if "extraResources" in metadata:
            self.extra_resources_loader = FileSystemLoader(str(metadata_dir))

        return metadata

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
        concerned_imageset = self.get_target_imageset(
            imagesets_iter=valid_imagesets
        )
        self._validate_imageset_schema(imageset=concerned_imageset)
        return concerned_imageset

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

    def _validate_imageset_schema(self, imageset):
        try:
            jsonschema.validate(
                instance=imageset, schema=load_addon_imageset_schema()
            )
        except jsonschema.exceptions.SchemaError as details:
            raise AddonLoadError(
                f"imageset schema error: {details.message}"
            ) from details
        except jsonschema.exceptions.ValidationError as details:
            raise AddonLoadError(
                f"{self.path} validation error: {details.message}"
            ) from details

    def _validate_schema(self, metadata):
        try:
            jsonschema.validate(
                instance=metadata, schema=load_addon_metadata_schema()
            )
        except jsonschema.exceptions.SchemaError as details:
            raise AddonLoadError(
                f"schema error: {details.message}"
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
