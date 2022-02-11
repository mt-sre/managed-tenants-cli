import pytest

from managedtenants.bundles.addon_bundles import AddonBundles
from managedtenants.bundles.exceptions import BundleError
from tests.testutils.paths import REFERENCE_ADDON, TEST_ROOT


def test_addon_bundles_reference_addon():
    expected_bundles = {
        "addon-operator": {"0.1.0", "0.2.0", "0.3.0"},
        "reference-addon": {
            "0.1.0",
            "0.1.1",
            "0.1.2",
            "0.1.3",
            "0.1.4",
            "0.1.5",
            "0.1.6",
        },
    }
    bundles = AddonBundles(REFERENCE_ADDON).get_all_bundles()

    assert len(bundles) == sum(len(v) for v in expected_bundles.values())
    for bundle in bundles:
        assert bundle.version in expected_bundles[bundle.operator_name]


def test_addon_bundles_invalid_version():
    reference_addon_dir = (
        TEST_ROOT / "testdata" / "addons" / "reference-addon-invalid-versions"
    )
    with pytest.raises(BundleError):
        _ = AddonBundles(reference_addon_dir).get_all_bundles()


def test_addon_bundles_latest_version():
    expected_latest_version = "0.1.6"
    latest = AddonBundles(REFERENCE_ADDON).get_latest_version()

    assert expected_latest_version == str(latest)
