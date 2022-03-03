import pytest

from managedtenants.bundles.bundle import Bundle
from managedtenants.bundles.exceptions import BundleError
from tests.testutils.addon_helpers import reference_addon_bundle_annotations
from tests.testutils.paths import REFERENCE_ADDON, TEST_ROOT


def test_bundle_parse_metadata_annotations():
    bundle = Bundle(
        addon_name="reference-addon",
        path=REFERENCE_ADDON / "main" / "0.1.6",
        operator_name="reference-addon",
        version="0.1.6",
    )

    expected_annotations = reference_addon_bundle_annotations()
    assert len(bundle.annotations) == len(expected_annotations)
    for k, v in expected_annotations.items():
        assert bundle.annotations.get(k, None) == v


@pytest.mark.parametrize(
    "path, operator_name, expected_bundle_repo",
    [
        (
            REFERENCE_ADDON / "main" / "0.1.6",
            "reference-addon",
            "reference-addon-bundle",
        ),
        (
            REFERENCE_ADDON / "addon-operator" / "0.3.0",
            "addon-operator",
            "reference-addon-addon-operator-bundle",
        ),
    ],
)
def test_bundle_repo_names(path, operator_name, expected_bundle_repo):
    bundle = Bundle(
        addon_name="reference-addon",
        path=path,
        operator_name=operator_name,
        version=path.name,
    )

    assert bundle.bundle_repo_name() == expected_bundle_repo
    assert bundle.index_repo_name() == "reference-addon-index"


@pytest.mark.parametrize(
    "bundle_path,single_bundle",
    [
        (
            TEST_ROOT
            / "testdata"
            / "addons"
            / "reference-addon-missing-olm-skip-range"
            / "main"
            / "0.1.6",
            True,
        ),
        (
            TEST_ROOT
            / "testdata"
            / "addons"
            / "reference-addon-invalid-bundle-version"
            / "main"
            / "abcd",
            False,
        ),
    ],
)
def test_invalid_bundle_raises_BundleError(bundle_path, single_bundle):
    with pytest.raises(BundleError):
        _ = Bundle(
            addon_name="reference-addon",
            path=bundle_path,
            operator_name="reference-addon",
            version=bundle_path.name,
            single_bundle=single_bundle,
        )
