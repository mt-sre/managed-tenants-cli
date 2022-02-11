import pytest

from managedtenants.bundles.bundle import Bundle
from tests.testutils.addon_helpers import reference_addon_bundle_annotations
from tests.testutils.paths import REFERENCE_ADDON


@pytest.mark.parametrize(
    "version, expected_annotations",
    [
        (
            "0.1.6",
            reference_addon_bundle_annotations(),
        ),
        (
            "0.1.5",
            reference_addon_bundle_annotations(),
        ),
    ],
)
def test_bundle_parse_metadata_annotations(version, expected_annotations):
    bundle_path = REFERENCE_ADDON / "main" / version
    bundle = Bundle(
        addon_name="reference-addon",
        path=bundle_path,
        operator_name="reference-addon",
        version=version,
    )

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
