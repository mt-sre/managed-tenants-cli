import pytest
import yaml
from sretoolbox.container import Image

from managedtenants.core.addons_loader.addon import Addon
from managedtenants.core.addons_loader.exceptions import AddonLoadError
from tests.testutils.addon_helpers import addon_with_bundles  # noqa: F401
from tests.testutils.addon_helpers import addon_with_imageset  # noqa: F401
from tests.testutils.addon_helpers import (  # flake8: noqa: F401
    ADDON_WITH_BUNDLES_TYPE,
    ADDON_WITH_IMAGESET_TYPE,
    addon_metadata_with_imageset_version,
    addon_with_imageset_path,
    load_yaml,
    setup_addon_class_with_stubbed_metadata,
)


@pytest.mark.parametrize(
    "addon,addon_type",
    [
        ("addon_with_bundles", ADDON_WITH_BUNDLES_TYPE),
        ("addon_with_imageset", ADDON_WITH_IMAGESET_TYPE),
    ],
)
def test_addon_metadata(addon, addon_type, request):
    """Test that addon metadata is loaded."""
    addon = request.getfixturevalue(addon)
    assert addon.metadata == load_yaml(addon.path / "metadata/stage/addon.yaml")


@pytest.mark.parametrize(
    "addon,addon_type",
    [
        ("addon_with_bundles", ADDON_WITH_BUNDLES_TYPE),
        ("addon_with_imageset", ADDON_WITH_IMAGESET_TYPE),
    ],
)
def test_addon_bundles(addon, addon_type, request):
    """Test that addon bundles are loaded or not."""
    addon = request.getfixturevalue(addon)
    if addon_type == ADDON_WITH_BUNDLES_TYPE:
        assert addon.bundles is not None
    else:
        assert addon.bundles is None


@pytest.mark.parametrize(
    "addon,addon_type",
    [
        ("addon_with_bundles", ADDON_WITH_BUNDLES_TYPE),
        ("addon_with_imageset", ADDON_WITH_IMAGESET_TYPE),
    ],
)
def test_addon_imageset(addon, addon_type, request):
    """Test that addon bundles are loaded or not."""
    addon = request.getfixturevalue(addon)

    if addon_type == ADDON_WITH_BUNDLES_TYPE:
        assert addon.imageset is None
    else:
        assert addon.imageset is not None
        expect_version = addon.metadata.get("addonImageSetVersion")
        SEMVER_LEN = len("0.0.0")
        version = addon.imageset["name"][-SEMVER_LEN:]
        assert version == expect_version


@pytest.mark.parametrize(
    "addon,addon_type",
    [
        ("addon_with_bundles", ADDON_WITH_BUNDLES_TYPE),
        ("addon_with_imageset", ADDON_WITH_IMAGESET_TYPE),
    ],
)
def test_addon_catalog_image(addon, addon_type, request):
    """Test that addon catalog image is loaded"""
    addon = request.getfixturevalue(addon)
    assert isinstance(addon.catalog_image, Image)


def assert_exceptions_on_addon_initialization(imageset_version, error_to_raise):
    required_metadata = addon_metadata_with_imageset_version(imageset_version)
    original_method = Addon.load_metadata
    setup_addon_class_with_stubbed_metadata(required_metadata=required_metadata)
    try:
        if error_to_raise:
            with pytest.raises(error_to_raise):
                Addon(addon_with_imageset_path(), "stage")
        else:
            # Shouldn't raise any exceptions, if it does, we catch the exception
            # and mark it as test failure.
            Addon(addon_with_imageset_path(), "stage")
    except Exception as e:
        pytest.fail(f"Didnt expect to raise any exceptions, but raised: {e}")
    finally:
        Addon.load_metadata = original_method


@pytest.mark.parametrize(
    "imageset_version,error_klass",
    [("invalid", AddonLoadError), ("1.0.0", None), ("2.0.0", AddonLoadError)],
)
def test_addon_imageset_version(imageset_version, error_klass):
    assert_exceptions_on_addon_initialization(
        imageset_version=imageset_version, error_to_raise=error_klass
    )


def test_addon_imageset_latest():
    addon = Addon(addon_with_imageset_path(), "stage")
    addon.imageset_version = "latest"
    res = addon.load_imageset("latest")
    latest_imageset_path = (
        addon_with_imageset_path() / "imagesets/stage/mock-operator.v1.0.2.yml"
    )
    with open(latest_imageset_path) as file_obj:
        expected_imageset = yaml.safe_load(file_obj.read())
    assert res == expected_imageset


def test_raises_imageset_missing_error():
    addon = Addon(addon_with_imageset_path(), "stage")
    # Doesnt have imagesets for this env
    addon.imagesets_path = addon.path / "imagesets/prod"
    with pytest.raises(AddonLoadError):
        addon.load_imageset(addon.imageset_version)
