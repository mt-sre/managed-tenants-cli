import pytest

from tests.testutils.addon_helpers import addon_with_imageset  # noqa: F401
from tests.testutils.addon_helpers import addon_with_indeximage  # noqa: F401
from tests.testutils.addon_helpers import (  # noqa: F401
    addons_managed_by_addon_cr,
    addon_with_deadmanssnitch,
    addon_with_pagerduty,
)


@pytest.mark.parametrize(
    "addon_str",
    [
        "addon_with_indeximage",
        "addon_with_imageset",
        "addons_managed_by_addon_cr",
        "addon_with_deadmanssnitch",
        "addon_with_pagerduty",
    ],
)
def test_addon_sss_object(addon_str, request):
    """Test that addon metadata is loaded."""
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
            catalogue_src_image = data["spec"]["install"]["olmOwnNamespace"][
                "catalogSourceImage"
            ]
            assert catalogue_src_image is not None
    else:
        addon = request.getfixturevalue(addon_str)
        sss_walker = addon.sss.walker()
        catalogue_src_obj = sss_walker["sss_deploy"]["spec"]["resources"][
            "CatalogSource"
        ]
        assert len(catalogue_src_obj) == 1
        name, data = catalogue_src_obj[0]
        assert name is not None
        assert data is not None
        assert data["spec"]["image"] is not None
