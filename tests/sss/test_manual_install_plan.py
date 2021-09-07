import hypothesis.strategies as hypothesis_strategies
import pytest
import tests.testutils.strategies as custom_strategies
from hypothesis import given
from managedtenants.core.addons_loader.sss import Sss


@given(data=hypothesis_strategies.data())
@pytest.mark.parametrize(
    "case",
    [
        # An empty field is parsed as None by PyYAML
        {"value": "undefined", "expected": None},
        {"value": False, "expected": None},
        {"value": True, "expected": "Manual"},
    ],
)
def test_sss_manual_install_plan(case, data):
    env = data.draw(custom_strategies.environment())
    addon = data.draw(custom_strategies.addon(env))

    if case["value"] == "undefined":
        addon.metadata.pop("manualInstallPlanApproval", None)
    else:
        addon.metadata["manualInstallPlanApproval"] = case["value"]

    # Rerender selectorsyncset.yaml.j2
    addon.sss = Sss(addon=addon)
    walker = addon.sss.walker()
    subscription = walker["sss_deploy"]["spec"]["resources"]["Subscription"][0][
        1
    ]

    if case["expected"] is None:
        with pytest.raises(KeyError):
            _ = subscription["spec"]["installPlanApproval"]
    else:
        assert subscription["spec"]["installPlanApproval"] == case["expected"]
