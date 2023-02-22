import json

import yaml


class Package:
    def __init__(self, addon):
        self._addon = addon
        self.data = self._get_data()

    @property
    def name(self):
        return f"{self._addon.name}.package.yml"

    @property
    def yaml(self):
        return yaml.dump(self.data, Dumper=yaml.CSafeDumper)

    @property
    def json(self):
        return json.dumps(self.data, indent=4)

    def _get_data(self):
        return {
            "packageName": self._addon.metadata["id"],
            "defaultChannel": self._addon.metadata["defaultChannel"],
            "channels": self._addon.metadata["channels"],
        }

    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self._addon.name)})"
