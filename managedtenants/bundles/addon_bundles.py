import logging
from functools import lru_cache
from pathlib import Path

import jsonschema
import semver
import yaml
from sretoolbox.utils.logger import get_text_logger

from managedtenants.bundles.bundle import Bundle
from managedtenants.bundles.exceptions import AddonBundlesError
from managedtenants.bundles.imageset import ImageSet
from managedtenants.bundles.utils import get_subdirs
from managedtenants.data.paths import SCHEMAS_DIR
from managedtenants.utils.git import get_short_hash
from managedtenants.utils.schema import load_schema


class AddonBundles:
    """
    Parses an addon_bundles_dir into a list of bundles.

    Example directory structure:
        gpu-operator
            ├── main
            │   ├── 1.8.3
            │   ├── 1.9.0
            └── nfd-operator
                └── 4.8.0

    Lexicography:
      - "gpu-operator" is the main operator
      - "nfd-operator" is a dependency operator

    Notes:
      - there can be an unlimited number of dependency operators
      - each operator contains a list of versioned directories (semver), where
        each directory represents a bundle
    """

    def __init__(self, root_dir, debug=False):
        self.log = get_text_logger(
            "managedtenants-addon-bundles",
            level=logging.DEBUG if debug else logging.INFO,
        )
        self.root_dir = Path(root_dir)
        self.addon_name = self.root_dir.name
        self.main_bundles = self._parse_main_bundles()
        self.dependency_bundles = self._parse_dependency_bundles()
        self.config = self._parse_and_validate_config()

    def _parse_main_bundles(self):
        operator_dir = self.root_dir / "main"
        if not operator_dir.is_dir():
            raise AddonBundlesError(
                f"invalid structure for {self.root_dir}: {operator_dir} does"
                " not exist"
            )
        return self._parse_operator_bundles(operator_dir)

    def _parse_dependency_bundles(self):
        res = []
        for operator_dir in get_subdirs(self.root_dir):
            if operator_dir.name != "main":
                res.extend(self._parse_operator_bundles(operator_dir))
        return res

    def _parse_operator_bundles(self, operator_dir):
        res = []
        for path in get_subdirs(operator_dir):
            bundle = Bundle(
                addon_name=self.addon_name,
                path=path.resolve(),
                operator_name=self._get_bundle_operator_name(operator_dir),
                version=path.name,
            )
            res.append(bundle)

        if len(res) == 0:
            raise AddonBundlesError(
                f"invalid structure for {self.root_dir}:"
                f" {operator_dir} contains zero bundles."
            )
        return res

    def _get_bundle_operator_name(self, operator_dir):
        operator_name = operator_dir.name
        return self.addon_name if operator_name == "main" else operator_name

    def _parse_and_validate_config(self):
        config_file = self.root_dir / "main" / "config.yaml"
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                self._validate_config(config)
                return config

        except FileNotFoundError:
            err_msg = f"missing {config_file} for {self}."
            self.log.error(err_msg)
            raise AddonBundlesError(err_msg)

        except yaml.YAMLError as e:
            raise AddonBundlesError(
                f"failed to parse {config_file} for {self}: {e}."
            )

    def _validate_config(self, config):
        try:
            jsonschema.validate(
                instance=config,
                schema=load_schema("mtbundles"),
                # required to resolve $ref: *.json
                resolver=jsonschema.RefResolver(
                    base_uri=f"file://{SCHEMAS_DIR}/",
                    referrer="mtbundles.schema.yaml",
                ),
            )

        except jsonschema.exceptions.SchemaError as e:
            raise AddonBundlesError(f"mtbundles schema error: {e}")

        except jsonschema.exceptions.ValidationError as e:
            raise AddonBundlesError(f"schema validation error for {self}: {e}")

    @lru_cache(maxsize=None)
    def _get_latest_version(self):
        """
        Returns the latest version amongst the main_bundles.
        """
        all_versions = [bundle.version for bundle in self.main_bundles]
        return max(all_versions, key=semver.VersionInfo.parse)

    def get_all_bundles(self):
        """
        Returns an addon's main_bundles and dependency_bundles.
        """
        return self.main_bundles + self.dependency_bundles

    def get_all_imagesets(self, index_image):
        """
        Produce all imagesets for a given index_image.

        :param index_image_str: representation of an index_image
        """
        res = []

        version = self._get_latest_version()
        ocm_config = self._get_ocm_config()

        for addon in self.config["addons"]:
            for env in addon["environments"]:
                imageset = ImageSet(
                    addon_name=addon["name"],
                    env=env,
                    version=version,
                    index_image=index_image,
                    ocm_config=ocm_config,
                )
                res.append(imageset)

        return res

    def _get_ocm_config(self):
        """
        OCM config is optional in the schema. Defaults have to conform with the
        schema (imageset.schema.yaml).
        """
        ocm_config = self.config.get("ocm", {})

        def ocm_config_getter(k, default):
            return ocm_config.get(k, default)

        return {
            k: ocm_config_getter(k, default)
            for k, default in [
                ("addOnParameters", []),
                ("addOnRequirements", []),
                ("subOperators", []),
                ("subscriptionConfig", {"env": []}),
            ]
        }

    def get_all_metadata_paths(self):
        """
        Returns all metadata paths in managed-tenants related to this
        AddonBundles.
        """
        res = []
        for addon in self.config["addons"]:
            for env in addon["environments"]:
                res.append(f"addons/{addon['name']}/metadata/{env}/addon.yaml")
        return res

    def get_unique_name(self):
        """
        Provide a unique name to identify an AddonBundles. Used for both the
        merge request title and branch name.
        """
        return (
            f"{self.addon_name}-{self._get_latest_version()}-{get_short_hash()}"
        )

    def __str__(self):
        return (
            f"AddonBundles(root_dir={self.root_dir},"
            f" addon_name={self.addon_name},"
            f" latest_version={self._get_latest_version()})"
        )
