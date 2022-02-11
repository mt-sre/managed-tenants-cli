from pathlib import Path

import semver

from managedtenants.bundles.bundle import Bundle
from managedtenants.bundles.exceptions import AddonBundlesError
from managedtenants.bundles.utils import get_subdirs


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

    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)
        self.addon_name = self.root_dir.name
        self.main_bundles = self._parse_main_bundles()
        self.dependency_bundles = self._parse_dependency_bundles()

    def _parse_main_bundles(self):
        operator_dir = self.root_dir / "main"
        if not operator_dir.is_dir():
            raise AddonBundlesError(
                f"invalid structure for {self.addon_name}: {operator_dir} does"
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
        return res

    def _get_bundle_operator_name(self, operator_dir):
        operator_name = operator_dir.name
        return self.addon_name if operator_name == "main" else operator_name

    def get_latest_version(self):
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
