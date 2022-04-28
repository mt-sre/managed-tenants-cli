import subprocess
from logging import exception
from pathlib import Path
from unittest import mock

import jsonschema
import pytest
import yaml
from conftest import REGISTRY_URL
from sretoolbox.container.image import Image

from managedtenants.bundles.utils import run
from managedtenants.core.addon_manager import AddonManager
from managedtenants.core.addons_loader.addon import Addon
from managedtenants.core.addons_loader.sss import Sss
from managedtenants.data.paths import SCHEMAS_DIR
from managedtenants.utils.schema import load_schema

ADDON_WITH_BUNDLES_TYPE = "with_bundles"
ADDON_WITH_IMAGESET_TYPE = "with_imageset"
ADDON_WITH_INDEXIMAGE_TYPE = "with_indeximage"


def addon_with_imageset_path():
    return Path("tests/testdata/addons/mock-operator-with-imagesets")


def addon_with_bundles_path():
    return Path("tests/testdata/addons/mock-operator-with-bundles")


def addon_with_indeximage_path():
    return Path("tests/testdata/addons/test-operator")


def addon_with_deadmanssnitch_path():
    return Path("tests/testdata/addons/test-operator")


def addon_with_pagerduty_path():
    return Path("tests/testdata/addons/test-operator")


def addon_with_secrets_path():
    return Path("tests/testdata/addons/mock-operator-with-secrets")


@pytest.fixture
def mt_bundles_with_invalid_dir_structure_path():
    return Path("tests/testdata/addons/mock-operator-with-bundles")


@pytest.fixture
def mt_bundles_addon_path():
    return Path("tests/testdata/addons/reference-addon")


@pytest.fixture
def mt_bundles_addon_with_invalid_version_path():
    return Path("tests/testdata/addons/reference-addon-invalid-versions")


@pytest.fixture
def addon_with_indeximage():
    addon_path = addon_with_indeximage_path()
    return Addon(addon_path, "stage")


@pytest.fixture
def addons_managed_by_addon_cr():
    def create_addon_managed_by_addon_cr(path):
        return Addon(
            path, "stage", override_manager=AddonManager.ADDON_OPERATOR
        )

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


@pytest.fixture
def addon_with_secrets():
    addon_path = addon_with_secrets_path()
    return Addon(addon_path, "stage")


@pytest.fixture
def addon_with_deadmanssnitch():
    addon_path = addon_with_deadmanssnitch_path()
    return Addon(addon_path, "stage")


@pytest.fixture
def addon_with_pagerduty():
    addon_path = addon_with_pagerduty_path()
    return Addon(addon_path, "stage")


@pytest.fixture
def addon_with_syncset_migration_step_1():
    addon_path = addon_with_indeximage_path()
    addon = Addon(addon_path, "stage")
    return rerender_addon_with_syncset_migration_step(
        addon, "stage", "step 1 - block installations"
    )


@pytest.fixture
def addon_with_syncset_migration_step_2():
    addon_path = addon_with_indeximage_path()
    addon = Addon(addon_path, "stage")
    return rerender_addon_with_syncset_migration_step(
        addon, "stage", "step 2 - orphan SSS objects"
    )


@pytest.fixture
def addon_with_syncset_migration_step_3():
    addon_path = addon_with_indeximage_path()
    addon = Addon(addon_path, "stage")
    return rerender_addon_with_syncset_migration_step(
        addon, "stage", "step 3 - change SSS label"
    )


@pytest.fixture
def addon_with_syncset_migration_step_4():
    addon_path = addon_with_indeximage_path()
    addon = Addon(addon_path, "stage")
    return rerender_addon_with_syncset_migration_step(
        addon, "stage", "step 4 - enable syncset"
    )


@pytest.fixture
def addon_with_syncset_migration_step_5():
    addon_path = addon_with_indeximage_path()
    addon = Addon(addon_path, "stage")
    return rerender_addon_with_syncset_migration_step(
        addon, "stage", "step 5 - migration complete"
    )


@pytest.fixture
def addon_with_syncset_migration_step_rollback_ocm():
    addon_path = addon_with_indeximage_path()
    addon = Addon(addon_path, "stage")
    return rerender_addon_with_syncset_migration_step(
        addon, "stage", "rollback step 1 - ocm"
    )


@pytest.fixture
def addon_with_syncset_migration_step_rollback_selectorsyncset():
    addon_path = addon_with_indeximage_path()
    addon = Addon(addon_path, "stage")
    return rerender_addon_with_syncset_migration_step(
        addon, "stage", "rollback step 2 - selectorsyncset"
    )


@pytest.fixture
def addon_with_syncset_migration_step_rollback_reset_addon_migration():
    addon_path = addon_with_indeximage_path()
    addon = Addon(addon_path, "stage")
    return rerender_addon_with_syncset_migration_step(
        addon, "stage", "rollback step 3 - reset addon migration"
    )


@pytest.fixture
def addon_with_wrong_syncset_migration_step():
    addon_path = addon_with_indeximage_path()
    addon = Addon(addon_path, "stage")
    return rerender_addon_with_syncset_migration_step(
        addon, "stage", "step not in enum"
    )


def rerender_addon_with_syncset_migration_step(addon, environment, step):
    addon.metadata["syncsetMigration"] = step
    # re-validate the addon metadata
    jsonschema.validate(
        instance=addon.metadata,
        schema=load_schema("metadata"),
        resolver=jsonschema.RefResolver(
            base_uri=f"file://{SCHEMAS_DIR}/",
            referrer="metadata.schema.yaml",
        ),
    )
    addon.sss = Sss(addon=addon)
    return addon


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


def return_false(*args, **kwargs):
    return False


def return_true(*args, **kwargs):
    return True


def reference_addon_bundle_annotations():
    return {
        "operators.operatorframework.io.bundle.mediatype.v1": "registry+v1",
        "operators.operatorframework.io.bundle.manifests.v1": "manifests/",
        "operators.operatorframework.io.bundle.metadata.v1": "metadata/",
        "operators.operatorframework.io.bundle.package.v1": "reference-addon",
        "operators.operatorframework.io.bundle.channels.v1": "alpha",
        "operators.operatorframework.io.bundle.channel.default.v1": "alpha",
    }
