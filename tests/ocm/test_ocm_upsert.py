import os

import pytest

from managedtenants.utils.ocm import OcmCli
from tests.testutils.addon_helpers import addon_with_imageset  # noqa: F401
from tests.testutils.addon_helpers import (  # flake8: noqa: F401
    ADDON_WITH_IMAGESET_TYPE,
)

OCM_TOKEN = os.environ.get("OCM_TOKEN")


@pytest.mark.parametrize(
    "addon,addon_type",
    [
        ("addon_with_imageset", ADDON_WITH_IMAGESET_TYPE),
    ],
)
def test_ocm_add_addon_version(addon, addon_type, request):
    addon = request.getfixturevalue(addon)
    ocm_cli = OcmCli(
        offline_token=OCM_TOKEN,
    )
    try:
        ocm_cli.upsert_addon_version(addon.imageset, addon.metadata)
    except Exception as e:
        pytest.fail(f"failed to add Addon version: {e}")
