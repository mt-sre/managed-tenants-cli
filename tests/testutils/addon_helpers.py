import random
from pathlib import Path
from unittest import mock

import pytest
import yaml

from managedtenants.core.addon_manager import AddonManager
from managedtenants.core.addons_loader.addon import Addon
from managedtenants.core.addons_loader.sss import Sss

ADDON_WITH_BUNDLES_TYPE = "with_bundles"
ADDON_WITH_IMAGESET_TYPE = "with_imageset"


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
def addon_managed_by_addon_cr():
    addon_path = random.choice(
        [addon_with_imageset_path(), addon_with_indeximage_path()]
    )
    addon = Addon(addon_path, "stage")
    addon.manager = AddonManager.ADDON_OPERATOR
    addon.sss = Sss(addon=addon)
    return addon


@pytest.fixture
def addon_with_imageset():
    addon_path = addon_with_imageset_path()
    return Addon(addon_path, "stage")


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
