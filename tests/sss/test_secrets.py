import pytest

from tests.testutils.addon_helpers import addon_with_secrets  # noqa: F401


def test_secrets(addon_with_secrets):
    sss_walker = addon_with_secrets.sss.walker()

    if addon_with_secrets.metadata.get("secrets"):
        no_of_secrets = len(addon_with_secrets.metadata.get("secrets"))
        assert (
            len(
                sss_walker["template_deploy"]["objects"][0]["spec"][
                    "resources"
                ]["Secret"]
            )
            == no_of_secrets
        )
    else:
        assert sss_walker["template_deploy"] is None
