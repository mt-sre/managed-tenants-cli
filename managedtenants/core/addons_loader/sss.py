import json
import re
from collections import ChainMap, defaultdict
from copy import deepcopy

import yaml
from jinja2 import ChoiceLoader, Environment, FileSystemLoader, StrictUndefined
from jinja2.exceptions import UndefinedError
from sretoolbox.utils.logger import get_text_logger

from managedtenants.core.addon_manager import AddonManager
from managedtenants.core.addons_loader.exceptions import SssLoadError
from managedtenants.data.paths import DATA_DIR

APP_LOG = get_text_logger("app")


class Sss:
    def __init__(self, addon):
        self._addon = addon
        self._sss_filename = "selectorsyncset.yaml.j2"
        self.data = self._get_data()

    @property
    def yaml(self):
        return yaml.dump(self.data, Dumper=yaml.CSafeDumper)

    @property
    def json(self):
        return json.dumps(self.data, indent=4)

    def walker(self):
        return SssWalker(data=self.data)

    def _get_data(self):
        try:
            loader = FileSystemLoader(searchpath=str(str(DATA_DIR)))
            if self._addon.extra_resources_loader is not None:
                loader = ChoiceLoader(
                    [loader, self._addon.extra_resources_loader]
                )
            env = Environment(
                loader=loader,
                undefined=StrictUndefined,
                # https://ttl255.com/jinja2-tutorial-part-3-whitespace-control/
                trim_blocks=True,  # remove newlines after blocks
                lstrip_blocks=True,  # lstrip whitespace preceding blocks
            )
            # pylint: disable=unnecessary-lambda
            env.filters["merge_dicts"] = lambda d1, d2: ChainMap(d1, d2)
            template = env.get_template(str(self._sss_filename))
            content = template.render(
                AddonManager=AddonManager, ADDON=self._addon
            )
        except UndefinedError as details:
            raise SssLoadError(
                f"error templating {self._sss_filename}: {details.message}"
            ) from details

        try:
            content_yaml = yaml.load(content, Loader=yaml.CSafeLoader)
            self._validate_deadmans_snitch(content_yaml)
            return content_yaml
        except yaml.error.MarkedYAMLError as details:
            APP_LOG.info(
                "Invalid YAML for addon %s. Here is the raw template:",
                self._addon.metadata["id"],
            )
            for line_number, line in enumerate(content.split("\n")):
                APP_LOG.info("%s: %s", line_number + 1, line)
            raise SssLoadError(
                f"invalid YAML: {details} for addon:"
                f" {self._addon.metadata['id']}"
            ) from details

    def _validate_deadmans_snitch(self, content):
        pattern = r"^hive-.*$"
        post_fix = re.compile(pattern)
        for item in content["items"]:
            if item["kind"] != "DeadmansSnitchIntegration":
                continue
            if "snitchNamePostFix" not in item["spec"]:
                raise SssLoadError(
                    "snitchNamePostFix key not found in "
                    "DeadmansSnitchIntegration for addon "
                    f"{self._addon.name}"
                )

            snitch_post_fix = item["spec"]["snitchNamePostFix"]
            if snitch_post_fix == "":
                raise SssLoadError(
                    "snitchNamePostFix in kind "
                    "DeadmansSnitchIntegration is empty for "
                    f"addon {self._addon.name}"
                )

            if post_fix.match(snitch_post_fix):
                raise SssLoadError(
                    "snitchNamePostFix must not start with "
                    "hive- and therefore matches an "
                    f"OSD cluster for addon {self._addon.name}"
                )

    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self._addon.name)})"


PAGERDUTY_KIND = "PagerDutyIntegration"
DEADMANSSNITCH_KIND = "DeadmansSnitchIntegration"
SSS_KIND = "SelectorSyncSet"


class SssWalker:
    """
    Helper class to walk the rendered SSS template data.
    The idea is to transform lists in dictionaries so we can avoid looping over
    the rendered data all over the place.
    """

    def __init__(self, data):
        self.data = self._walk(data)

    def _walk(self, data):
        """Parses the rendered selectorsyncset template in a friendly way."""
        res = {
            "sss_deploy": None,
            "sss_delete": None,
            "pdi": None,
            "dms": None,
        }
        for item in data["items"]:
            if item["kind"] == SSS_KIND:
                if item["metadata"]["name"].endswith("delete"):
                    res["sss_delete"] = self._walk_sss(item)
                else:
                    res["sss_deploy"] = self._walk_sss(item)
            elif item["kind"] == PAGERDUTY_KIND:
                res["pdi"] = item
            elif item["kind"] == DEADMANSSNITCH_KIND:
                res["dms"] = item
            else:
                raise TypeError(
                    f"Unhandled type {item['kind']}. Please update SssWalker."
                )
        return res

    @staticmethod
    def _walk_sss(data):
        """
        Transform sss['resources']['spec'] into a dictionary of lists, indexed
        by Kind. Each Kind is a list of (name, resource) tuples.

        Example of the structure:
        {
            'spec': {
                'resources': {
                    'Namespace': [
                        (<name>, <resource>), # ns 1
                        (<name>, <resource>), # ns 2
                        ...
                    ],
                    'Secret': [
                        (<name>, <resource>), # secret 1
                        (<name>, <resource>), # secret 2
                        ...
                    ],
                    '<kind>': [
                        (<name>, <resource>), # <kind> 1
                        (<name>, <resource>), # <kind> 2
                        ...
                    ]
                }
            }
        }
        """
        sss = deepcopy(data)
        old_resources = deepcopy(data["spec"]["resources"])
        sss["spec"]["resources"] = defaultdict(list)
        for resource in old_resources:
            kind = resource["kind"]
            name = resource["metadata"]["name"]
            sss["spec"]["resources"][kind].append((name, resource))
        return sss

    def __getitem__(self, item):
        return self.data[item]
