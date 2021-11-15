import os

import pytest

from managedtenants.utils.ocm import OcmCli
from tests.testutils.addon_helpers import (  # flake8: noqa: F401
    addon_metadata_with_imageset,
)

OCM_TOKEN = os.environ.get("OCM_TOKEN")


@pytest.mark.parametrize(
    "metadata",
    [(addon_metadata_with_imageset())],
)
def test_ocm_add_addon_version(metadata):
    ocm_cli = OcmCli(
        offline_token=OCM_TOKEN,
    )
    try:
        ocm_cli.add_addon_version(metadata)
    except Exception as e:
        pytest.fail(f"failed to add Addon version: {e}")
