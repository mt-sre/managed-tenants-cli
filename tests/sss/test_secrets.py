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
        for secret in sss_walker["template_deploy"]["objects"][0]["spec"][
            "resources"
        ]["Secret"]:
            assert secret[1]["metadata"]["labels"] is not None
            assert "data" in secret[1]
            assert "type" in secret[1]
    else:
        assert sss_walker["template_deploy"] is None
