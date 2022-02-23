import pytest
from sretoolbox.container import Image

from managedtenants.bundles.addon_bundles import AddonBundles
from managedtenants.bundles.exceptions import AddonBundlesError, BundleError
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
    latest_version = AddonBundles(REFERENCE_ADDON)._get_latest_version()
    assert latest_version == expected_latest_version


@pytest.mark.parametrize(
    "path,raises",
    [
        (REFERENCE_ADDON, False),
        (
            TEST_ROOT
            / "testdata"
            / "addons"
            / "reference-addon-invalid-config",
            True,
        ),
        (
            TEST_ROOT / "testdata" / "addons" / "reference-addon-empty-bundles",
            True,
        ),
    ],
)
def test_addon_bundles_config(path, raises):
    if raises:
        with pytest.raises(AddonBundlesError):
            _ = AddonBundles(path)

    else:
        addon_bundles = AddonBundles(path)
        addon = addon_bundles.config["addons"][0]

        assert addon["name"] == "reference-addon"
        assert addon["environments"] == ["integration", "stage"]

        ocm_config = addon_bundles._get_ocm_config()
        for expected_key in [
            "addOnParameters",
            "addOnRequirements",
            "subOperators",
            "subscriptionConfig",
        ]:
            assert ocm_config[expected_key] is not None


def test_addon_bundles_get_all_imagesets():
    expected_imageset_keys = [
        "name",
        "indexImage",
        "relatedImages",
        "addOnParameters",
        "addOnRequirements",
        "subOperators",
        "subscriptionConfig",
    ]
    expected_names_count = {
        "reference-addon.v0.1.6": 2,
        "reference-addon-alias.v0.1.6": 2,
    }
    expected_paths_found = {
        "addons/reference-addon/addonimagesets/integration/reference-addon.v0.1.6.yaml": False,
        "addons/reference-addon/addonimagesets/stage/reference-addon.v0.1.6.yaml": False,
        "addons/reference-addon-alias/addonimagesets/integration/reference-addon-alias.v0.1.6.yaml": False,
        "addons/reference-addon-alias/addonimagesets/stage/reference-addon-alias.v0.1.6.yaml": False,
    }
    # image has to really exist for url_digest to not throw 404
    expected_index_image = Image(
        "quay.io/osd-addons/reference-addon-index@sha256:2a1ba347fb188c8481ccd643dd6d27825dcec6f102d23cf44a4316fd1f2b2d5a"
    )

    addon_bundles = AddonBundles(REFERENCE_ADDON)
    all_imagesets = addon_bundles.get_all_imagesets(expected_index_image)

    for imageset in all_imagesets:
        assert imageset.index_image == expected_index_image
        assert len(imageset.to_yaml()) > 0
        expected_paths_found[imageset.path] = True
        expected_names_count[imageset.name] -= 1

        # Make sure all imagesets define default values for all fields
        data = imageset._to_schema_instance()
        for k in expected_imageset_keys:
            assert data.get(k, None) is not None

    assert len(all_imagesets) == len(expected_paths_found)
    assert sum([v for v in expected_names_count.values()]) == 0
    assert all([k for k in expected_paths_found.keys()])


def test_addon_bundles_get_all_metadata_paths():
    expected_paths = {
        "addons/reference-addon/metadata/integration/addon.yaml": False,
        "addons/reference-addon/metadata/stage/addon.yaml": False,
        "addons/reference-addon-alias/metadata/integration/addon.yaml": False,
        "addons/reference-addon-alias/metadata/stage/addon.yaml": False,
    }

    addon_bundles = AddonBundles(REFERENCE_ADDON)
    metadata_paths = addon_bundles.get_all_metadata_paths()

    for metadata_path in metadata_paths:
        expected_paths[metadata_path] = True

    assert len(metadata_paths) == len(expected_paths)
    assert all([v for v in expected_paths.values()])
