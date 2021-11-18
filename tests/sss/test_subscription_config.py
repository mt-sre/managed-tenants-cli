import pytest

from tests.testutils.addon_helpers import addon_with_imageset  # noqa: F401
from tests.testutils.addon_helpers import addon_with_indeximage  # noqa: F401


@pytest.mark.parametrize(
    "addon_str",
    [
        "addon_with_indeximage",
        "addon_with_imageset",
    ],
)
def test_subscription_config(addon_str, request):
    expected_values = [
        {"name": "LOCATION", "value": "Black Mesa Research Facility"},
        {"name": "USER", "value": "Gordon Freeman"},
    ]
    addon = request.getfixturevalue(addon_str)
    sss_walker = addon.sss.walker()
    subscription_obj = sss_walker["sss_deploy"]["spec"]["resources"][
        "Subscription"
    ][0]
    if addon.subscription_config_present():
        _, subscription_contents = subscription_obj
        assert len(subscription_contents["spec"]["config"]["env"]) == 2
        for env_obj in subscription_contents["spec"]["config"]["env"]:
            assert env_obj in expected_values
    else:
        _, subscription_contents = subscription_obj
        res = subscription_contents["spec"].get("config")
        assert res is None
