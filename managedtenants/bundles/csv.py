import yaml

from managedtenants.bundles.exceptions import CSVError


class CSV:
    def __init__(self, manifests_dir, operator_name):
        self.manifests_dir = manifests_dir
        self.operator_name = operator_name
        self.path = self._get_path()
        self.data = self._parse_csv()

    def _get_path(self):
        """
        Find the csv manifest path. Only care about the manifest suffix.
        """
        suffix_candidates = [
            f"{csv_name}.{extension}"
            for csv_name in ["csv", "clusterserviceversion"]
            for extension in ["yml", "yaml"]
        ]

        for path in self.manifests_dir.iterdir():
            if not path.is_file():
                continue

            for suffix in suffix_candidates:
                if path.name.endswith(suffix):
                    return path

        raise CSVError(
            f"{self} could not find csv manifest, tried the following suffixes:"
            f" {suffix_candidates}."
        )

    def _parse_csv(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return yaml.load(f, Loader=yaml.CSafeLoader)

        except yaml.YAMLError as e:
            raise CSVError(f"{self}: failed to parse {self.path}: {e}.")

    def get_olm_skip_range_annotation(self):
        """
        Returns the `olm.skipRange` metadata annotation.
        """
        return (
            self.data.get("metadata", {})
            .get("annotations", {})
            .get("olm.skipRange", None)
        )

    def is_replaces_unset(self):
        return self.data.get("spec", {}).get("replaces", None) is None

    def is_skips_unset(self):
        return self.data.get("spec", {}).get("skips", None) is None

    def __str__(self):
        return (
            f"CSV(manifests_dir={self.manifests_dir},"
            f" operator_name={self.operator_name})"
        )
