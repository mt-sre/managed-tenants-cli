import pytest

from tests.testutils.addon_helpers import addon_with_imageset  # noqa: F401
from tests.testutils.addon_helpers import addon_with_indeximage  # noqa: F401
from tests.testutils.addon_helpers import (  # noqa: F401
    addons_managed_by_addon_cr,
)


@pytest.mark.parametrize(
    "addon_str",
    [
        "addon_with_indeximage",
        "addon_with_imageset",
        "addons_managed_by_addon_cr",
    ],
)
def test_subscription_config(addon_str, request):
    expected_values = [
        {"name": "LOCATION", "value": "Black Mesa Research Facility"},
        {"name": "USER", "value": "Gordon Freeman"},
        {"name": "HUMAN", "value": "true"},
    ]

    if addon_str == "addons_managed_by_addon_cr":
        addons = request.getfixturevalue(addon_str)
        for addon in addons:
            sss_walker = addon.sss.walker()
            addon_cr_obj = sss_walker["sss_deploy"]["spec"]["resources"][
                "Addon"
            ]
            assert len(addon_cr_obj) == 1
            name, data = addon_cr_obj[0]
            assert name is not None
            assert data is not None
            assert data["spec"] is not None
            subscription_config = data["spec"]["install"]["olmOwnNamespace"][
                "config"
            ]
            assert subscription_config is not None
            assert subscription_config["env"] == expected_values
    else:
        addon = request.getfixturevalue(addon_str)
        sss_walker = addon.sss.walker()
        subscription_obj = sss_walker["sss_deploy"]["spec"]["resources"][
            "Subscription"
        ][0]
        if addon.get_subscription_config():
            _, subscription_contents = subscription_obj
            assert len(subscription_contents["spec"]["config"]["env"]) == 3
            for env_obj in subscription_contents["spec"]["config"]["env"]:
                assert env_obj in expected_values
        else:
            _, subscription_contents = subscription_obj
            res = subscription_contents["spec"].get("config")
            assert res is None
