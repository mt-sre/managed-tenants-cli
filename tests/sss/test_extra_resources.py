import os
import tempfile

import hypothesis.strategies as hypothesis_strategies
import pytest
from hypothesis import given
from jinja2 import FileSystemLoader

import tests.testutils.strategies as custom_strategies
from managedtenants.core.addons_loader.sss import Sss
from tests.testutils.extra_resources import DEADMANSSNITCH, PAGERDUTYINTEGRATION


@pytest.mark.parametrize(
    "is_v2",
    [True, False],
)
@given(data=hypothesis_strategies.data())
def test_multiple_extra_resources_v1(data, is_v2):
    env = data.draw(custom_strategies.environment())
    addon = data.draw(custom_strategies.addon(env))
    addon.metadata["extraResources"] = []

    if is_v2:
        addon.metadata["indexImage"] = custom_strategies.quay_image(
            addon.metadata["id"]
        )

    # override search path for Jinja loader
    addon.extra_resources_loader = FileSystemLoader(tempfile.gettempdir())
    addon.metadata["extraResources"] = create_extra_resources(
        [DEADMANSSNITCH, PAGERDUTYINTEGRATION]
    )

    try:
        # Rerender selectorsyncset.yaml.j2
        addon.sss = Sss(addon=addon)
        walker = addon.sss.walker()

        assert walker["dms"]["metadata"]["name"] == "mtsre-dms-test"
        assert walker["pdi"]["metadata"]["name"] == "mtsre-pdi-test"

    finally:
        delete_extra_resources(addon.metadata["extraResources"])


def create_extra_resources(resources):
    res = []
    for er in resources:
        tmp = tempfile.NamedTemporaryFile(suffix=".yaml.j2", delete=False)
        basename = os.path.basename(tmp.name)

        with open(tmp.name, "w") as f:
            f.write(er)
        res.append(basename)
    return res


def delete_extra_resources(resources):
    tmpdir = tempfile.gettempdir()
    for basename in resources:
        fullname = os.path.join(tmpdir, basename)
        if os.path.isfile(fullname):
            os.remove(fullname)
