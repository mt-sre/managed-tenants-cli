from managedtenants.core.addons_loader.exceptions import BundleLoadError
from managedtenants.core.addons_loader.manifest import Manifest


class Bundle:
    def __init__(self, path, metadata):
        self.path = path
        self.manifests = self._load_manifests(metadata=metadata)

    @property
    def name(self):
        return self.path.name

    @staticmethod
    def instantiate_manifest(args):
        return Manifest(path=args[0], metadata=args[1])

    def _load_manifests(self, metadata):
        manifests_to_load = []
        for item in sorted(self.path.iterdir()):
            if item.name == "OWNERS":
                continue

            if item.suffix not in [".yaml", ".yml", ".j2"]:
                raise BundleLoadError(
                    f'{item}: only ".yaml" or ".j2" files are supported'
                )

            manifests_to_load.append((item, metadata))

        # force list to not lazily evaluate the returned iterator of map()
        manifests = list(map(self.instantiate_manifest, manifests_to_load))

        self._validate_number_of_csvs(manifests)

        return manifests

    def _validate_number_of_csvs(self, manifests):
        csv_count = 0
        for manifest in manifests:
            if manifest.data["kind"] != "ClusterServiceVersion":
                continue
            csv_count += 1

        if csv_count == 1:
            return

        raise BundleLoadError(
            f"{self.path}: exactly one ClusterServiceVersion must exist"
        )

    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self.name)})"
