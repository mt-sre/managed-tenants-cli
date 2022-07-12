import jsonschema
import semver
import yaml
from jinja2 import FileSystemLoader

from managedtenants.core.addons_loader.exceptions import AddonLoadError
from managedtenants.core.addons_loader.sss import Sss
from managedtenants.data.paths import SCHEMAS_DIR
from managedtenants.utils.general_utils import parse_version_from_imageset_name
from managedtenants.utils.schema import load_schema

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
                self.catalog_image = self.imageset["indexImage"]

        elif "indexImage" in self.metadata:
            self.imagesets_path = None
            self.imageset = None
            self.catalog_image = self.metadata["indexImage"]

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
        if self.metadata.get("pullSecretName"):
            return self.metadata.get("pullSecretName")
        return None

    def get_subscription_config(self):
        # If imageset is present, check for subscriptionConfig in the
        # imageset file, otherwise check for the default subscription config
        # in the addon metadata file.
        if self.imageset and self.imageset.get("subscriptionConfig"):
            return self.imageset.get("subscriptionConfig")
        return self.metadata.get("subscriptionConfig")

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
        self._validate_additional_catalogue_srcs(metadata)
        self._validate_secret_names(metadata)
        self._validate_pullSecretName(metadata)

        if "extraResources" in metadata:
            self.extra_resources_loader = FileSystemLoader(str(metadata_dir))

        return metadata

    def _validate_additional_catalogue_srcs(self, metadata):
        if metadata.get("additionalCatalogSources"):
            ctlg_src_names = [
                obj["name"] for obj in metadata["additionalCatalogSources"]
            ]
            if len(set(ctlg_src_names)) != len(ctlg_src_names):
                raise AddonLoadError(
                    f"{self.path} validation error: Additional catalog source"
                    " should have a unique name"
                )

    def _validate_secret_names(self, metadata):
        if metadata.get("secrets"):
            secret_names = [
                secret.get("name") for secret in metadata["secrets"]
            ]
            if len(set(secret_names)) != len(secret_names):
                raise AddonLoadError(
                    f"{self.path} validation error: secrets"
                    " should have a unique name"
                )

    def _validate_pullSecretName(self, metadata):
        if metadata.get("pullSecretName"):
            if not metadata.get("secrets"):
                raise AddonLoadError(
                    f"{self.path} validation error: No secrets provided,"
                    " pullSecretName should be one of secrets' names"
                )
            secret_names = [
                secret.get("name") for secret in metadata["secrets"]
            ]
            if not metadata["pullSecretName"] in secret_names:
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
    def load_yaml(path):
        try:
            with open(path, encoding="utf8") as file_obj:
                data = yaml.load(file_obj.read(), Loader=yaml.CSafeLoader)
                return data
        except yaml.YAMLError:
            return None

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
