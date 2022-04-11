import pytest
from tests.testutils.addon_helpers import addon_with_secrets  # noqa: F401


@pytest.mark.parametrize(
    "addon_str",[
        "addon_with_secrets"
    ]
)
def test_secrets(addon_str,request):
    addon = request.getfixturevalue(addon_str)
    sss_walker = addon.sss.walker()

    if addon.metadata.get("secrets"):
        no_of_secrets = len(addon.metadata.get("secrets"))
        assert len(sss_walker["template_deploy"]['objects'][0]["spec"]["resources"]["Secret"]) == no_of_secrets
    else:
        assert sss_walker["template_deploy"] is None
