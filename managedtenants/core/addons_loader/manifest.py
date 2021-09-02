import json

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from jinja2.exceptions import UndefinedError

from managedtenants.core.addons_loader.exceptions import ManifestLoadError


class Manifest:
    def __init__(self, path, metadata):
        self.path = path
        self._metadata = metadata
        self.data = self._get_data()

    @property
    def name(self):
        return self.path.name

    @property
    def yaml(self):
        return yaml.dump(self.data, Dumper=yaml.CSafeDumper)

    @property
    def json(self):
        return json.dumps(self.data, indent=4)

    def _get_data(self):
        data = self._load()
        self._validate_csv_install_mode(data)
        return data

    def _load(self):
        if self.path.suffix == ".j2":
            try:
                loader = FileSystemLoader(searchpath=str(self.path.parent))
                env = Environment(loader=loader, undefined=StrictUndefined)
                template = env.get_template(str(self.name))
                content = template.render(**self._metadata["bundleParameters"])
            except UndefinedError as details:
                raise ManifestLoadError(
                    f"error templating {self.path}: {details.message}"
                ) from details
        else:
            with open(self.path, encoding="utf-8") as file_obj:
                content = file_obj.read()
        try:
            return yaml.load(content, Loader=yaml.CSafeLoader)
        except yaml.error.MarkedYAMLError as details:
            raise ManifestLoadError(f"{self.path}: {details}") from details

    def _validate_csv_install_mode(self, data):
        if data["kind"] != "ClusterServiceVersion":
            return

        if "installModes" in data["spec"]:
            expected_csv_install_mode = {
                "supported": True,
                "type": self._metadata["installMode"],
            }
            if expected_csv_install_mode in data["spec"]["installModes"]:
                return

        raise ManifestLoadError(
            f"{self.path}: installMode "
            f'"{self._metadata["installMode"]}" '
            "must be supported by the "
            "ClusterServiceVersion"
        )

    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self.name)})"
