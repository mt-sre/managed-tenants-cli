from pathlib import Path
from unittest import mock

import pytest
import yaml

from managedtenants.core.addon_manager import AddonManager
from managedtenants.core.addons_loader.addon import Addon
from managedtenants.core.addons_loader.sss import Sss

ADDON_WITH_BUNDLES_TYPE = "with_bundles"
ADDON_WITH_IMAGESET_TYPE = "with_imageset"
ADDON_WITH_INDEXIMAGE_TYPE = "with_indeximage"


def addon_with_imageset_path():
    return Path("tests/testdata/addons/mock-operator-with-imagesets")


def addon_with_bundles_path():
    return Path("tests/testdata/addons/mock-operator-with-bundles")


def addon_with_indeximage_path():
    return Path("tests/testdata/addons/test-operator")


@pytest.fixture
def addon_with_indeximage():
    addon_path = addon_with_indeximage_path()
    return Addon(addon_path, "stage")


@pytest.fixture
def addons_managed_by_addon_cr():
    def create_addon_managed_by_addon_cr(path):
        addon = Addon(path, "stage")
        addon.manager = AddonManager.ADDON_OPERATOR
        addon.sss = Sss(addon=addon)
        return addon

    addon_paths = [addon_with_imageset_path(), addon_with_indeximage_path()]
    return list(map(create_addon_managed_by_addon_cr, addon_paths))


@pytest.fixture
def addon_with_imageset():
    addon_path = addon_with_imageset_path()
    return Addon(addon_path, "stage")


@pytest.fixture
def addon_with_imageset_and_multiple_config():
    addon_path = addon_with_imageset_path()
    return Addon(addon_path, "stage")


@pytest.fixture
def addon_with_imageset_and_no_config():
    addon_path = addon_with_imageset_path()
    addon = Addon(addon_path, "stage")
    updated_metadata = addon.metadata
    # Remove the default subscriptionConfig
    del updated_metadata["subscriptionConfig"]
    # Set imageset to a version that doesnt have
    # subscription config
    updated_metadata["addonImageSetVersion"] = "1.0.2"
    addon.metadata = updated_metadata
    addon.imageset_version = "1.0.2"
    # Reload imageset
    addon.imageset = addon.load_imageset("1.0.2")
    return addon


@pytest.fixture
def addon_with_only_imageset_config():
    addon_path = addon_with_imageset_path()
    addon = Addon(addon_path, "stage")
    updated_metadata = addon.metadata
    # Remove the default subscriptionConfig
    del updated_metadata["subscriptionConfig"]
    addon.metadata = updated_metadata
    return addon


@pytest.fixture
def addon_with_imageset_and_default_config():
    addon_path = addon_with_imageset_path()
    addon = Addon(addon_path, "stage")
    updated_metadata = addon.metadata
    # Set imageset to a version that doesnt have
    # subscription config
    updated_metadata["addonImageSetVersion"] = "1.0.2"
    addon.metadata = updated_metadata
    addon.imageset_version = "1.0.2"
    # Reload imageset
    addon.imageset = addon.load_imageset("1.0.2")
    return addon


@pytest.fixture
def addon_with_bundles():
    addon_path = addon_with_bundles_path()
    return Addon(addon_path, "stage")


def setup_addon_class_with_stubbed_metadata(required_metadata):
    Addon.load_metadata = mock.Mock(return_value=required_metadata)


def load_yaml(path):
    with open(path) as file_obj:
        return yaml.safe_load(file_obj)


def addon_metadata_with_imageset_version(imageset_version):
    addon_path = addon_with_imageset_path()
    addon_imagesets_metadata_path = addon_path / "metadata/stage/addon.yaml"
    with open(addon_imagesets_metadata_path) as file_obj:
        metadata = yaml.safe_load(file_obj.read())

    metadata["addonImageSetVersion"] = imageset_version
    return metadata
