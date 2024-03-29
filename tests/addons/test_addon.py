import pytest
import yaml
from sretoolbox.container import Image

from managedtenants.core.addons_loader.addon import Addon
from managedtenants.core.addons_loader.exceptions import AddonLoadError
from tests.testutils.addon_helpers import addon_with_indeximage  # noqa: F401
from tests.testutils.addon_helpers import addon_with_secrets  # noqa: F401
from tests.testutils.addon_helpers import (  # noqa: F401; noqa: F401; noqa: F401; flake8: noqa: F401
    ADDON_WITH_BUNDLES_TYPE,
    ADDON_WITH_IMAGESET_TYPE,
    ADDON_WITH_INDEXIMAGE_TYPE,
    addon_metadata_with_imageset_version,
    addon_with_duplicate_keys_path,
    addon_with_imageset,
    addon_with_imageset_and_default_config,
    addon_with_imageset_and_multiple_config,
    addon_with_imageset_and_no_config,
    addon_with_imageset_path,
    addon_with_indeximage_path,
    addon_with_metrics_federation_fields,
    addon_with_only_imageset_config,
    addon_with_secrets_path,
    load_yaml,
    sample_additional_catalog_srcs,
    sample_envs,
    sample_secrets,
    setup_addon_class_with_stubbed_metadata,
)


@pytest.mark.parametrize(
    "addon,addon_type",
    [
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
        ("addon_with_imageset", ADDON_WITH_IMAGESET_TYPE),
    ],
)
def test_addon_bundles(addon, addon_type, request):
    """Test that addon bundles are loaded or not."""
    addon = request.getfixturevalue(addon)
    assert addon.bundles is None


@pytest.mark.parametrize(
    "addon,addon_type",
    [
        ("addon_with_imageset", ADDON_WITH_IMAGESET_TYPE),
    ],
)
def test_addon_imageset(addon, addon_type, request):
    """Test that addon bundles are loaded or not."""
    addon = request.getfixturevalue(addon)
    assert addon.imageset is not None
    expect_version = addon.metadata.get("addonImageSetVersion")
    SEMVER_LEN = len("0.0.0")
    version = addon.imageset["name"][-SEMVER_LEN:]
    assert version == expect_version


def test_additional_catalogue_src_name_validation():
    addon = Addon(addon_with_indeximage_path(), "integration")
    metadata = addon.metadata
    duplicate = metadata["additionalCatalogSources"][0]
    metadata["additionalCatalogSources"].append(duplicate)
    with pytest.raises(AddonLoadError):
        addon._validate_additional_catalogue_srcs()


def test_secret_names_validation():
    addon = Addon(addon_with_secrets_path(), "stage")
    metadata = addon.metadata
    duplicate = metadata["config"]["secrets"][0]
    metadata["config"]["secrets"].append(duplicate)
    with pytest.raises(AddonLoadError):
        addon._validate_secret_names()


def test_pullSecretName_validation():
    addon = Addon(addon_with_secrets_path(), "stage")
    metadata = addon.metadata
    """Assigning a random UUID"""
    metadata["pullSecretName"] = "5daad7e9-dea7-4b3a-9fe5-a773df8ec57c"
    with pytest.raises(AddonLoadError):
        addon._validate_pullSecretName()


def test_secret_accessor_methods(request):
    addon = request.getfixturevalue("addon_with_imageset_and_default_config")
    # Should pickup the default secrets from the metadata file
    assert addon.get_secrets() == addon.metadata["config"]["secrets"]
    assert addon.get_pull_secret_name() == "pull-secret-one"

    # Should pickup the secrets defined in the imageset file
    imageset_copy = addon.imageset
    imageset_copy["pullSecretName"] = "test-secret"
    imageset_copy["config"] = {}
    imageset_copy["config"]["secrets"] = sample_secrets("test-secret")
    addon.imageset = imageset_copy
    assert addon.get_secrets() == sample_secrets("test-secret")
    assert addon.get_pull_secret_name() == "test-secret"


def test_env_accessor_method(request):
    addon = request.getfixturevalue("addon_with_imageset_and_default_config")
    assert addon.get_envs() == addon.metadata["config"]["env"]

    imageset_copy = addon.imageset
    imageset_copy["config"] = {}
    imageset_copy["config"]["env"] = sample_envs()
    addon.imageset = imageset_copy
    assert addon.get_envs() == addon.get_envs()


def test_additional_ctlg_src_accessor_method():
    addon = Addon(addon_with_imageset_path(), "stage")
    assert (
        addon.get_additional_catalog_srcs()
        == addon.metadata["additionalCatalogSources"]
    )

    imageset = addon.imageset
    imageset["additionalCatalogSources"] = sample_additional_catalog_srcs()
    addon.imageset = imageset
    assert (
        addon.get_additional_catalog_srcs() == sample_additional_catalog_srcs()
    )


def test_metrics_federation_loading():
    addon = Addon(addon_with_metrics_federation_fields(), "stage")
    metricsFederationMetadata = addon.metadata.get("metricsFederation", None)
    assert metricsFederationMetadata is not None

    matchLabels = metricsFederationMetadata.get("matchLabels", None)
    assert matchLabels is not None

    assert matchLabels.get("kubernetes.io/app-name", "") == "mock-operator"


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
        addon_with_imageset_path()
        / "addonimagesets/stage/mock-operator.v1.0.2.yml"
    )
    with open(latest_imageset_path) as file_obj:
        expected_imageset = yaml.safe_load(file_obj.read())
    assert res == expected_imageset


def test_raises_imageset_missing_error():
    addon = Addon(addon_with_imageset_path(), "stage")
    # Doesnt have imagesets for this env
    addon.imagesets_path = addon.path / "addonimagesets/prod"
    with pytest.raises(AddonLoadError):
        addon.load_imageset(addon.imageset_version)


@pytest.mark.parametrize(
    "addon_str,expected_result",
    [
        (
            "addon_with_imageset_and_default_config",
            [{"name": "DEFAULT", "value": "TRUE"}],
        ),
        (
            "addon_with_imageset_and_multiple_config",
            [
                {"name": "LOCATION", "value": "Black Mesa Research Facility"},
                {"name": "USER", "value": "Gordon Freeman"},
                {"name": "HUMAN", "value": "true"},
            ],
        ),
        ("addon_with_imageset_and_no_config", None),
        (
            "addon_with_only_imageset_config",
            [
                {"name": "LOCATION", "value": "Black Mesa Research Facility"},
                {"name": "USER", "value": "Gordon Freeman"},
                {"name": "HUMAN", "value": "true"},
            ],
        ),
        (
            "addon_with_indeximage",
            [
                {"name": "LOCATION", "value": "Black Mesa Research Facility"},
                {"name": "USER", "value": "Gordon Freeman"},
                {"name": "HUMAN", "value": "true"},
            ],
        ),
    ],
)
def test_addon_env(addon_str, expected_result, request):
    addon = request.getfixturevalue(addon_str)
    if expected_result:
        res = addon.get_envs()
        assert res == expected_result
    else:
        assert addon.get_envs() is None


@pytest.mark.parametrize(
    "addon,addon_type",
    [
        ("addon_with_indeximage", ADDON_WITH_INDEXIMAGE_TYPE),
        ("addon_with_only_imageset_config", ADDON_WITH_IMAGESET_TYPE),
    ],
)
def test_addon_config_validations(addon, addon_type, request):
    addon = request.getfixturevalue(addon)
    if addon_type == ADDON_WITH_INDEXIMAGE_TYPE:
        updated_metadata = addon.metadata
        updated_metadata["config"]["unsupportedAttr"] = "present"
        with pytest.raises(AddonLoadError):
            addon._validate_schema_instance(updated_metadata, "metadata")
    else:
        updated_imageset = addon.imageset
        updated_imageset["config"]["unsupportedAttr"] = "present"
        with pytest.raises(AddonLoadError):
            addon._validate_schema_instance(updated_imageset, "imageset")


def test_env_value_validation():
    addon = Addon(addon_with_imageset_path(), "stage")
    # Use an imageset with invalid env value
    addon.metadata["addonImageSetVersion"] = "0.0.9"
    addon.imageset_version = "0.0.9"
    # Reload imageset
    with pytest.raises(AddonLoadError):
        addon.imageset = addon.load_imageset("0.0.9")


def test_addon_unique_keys_validation():
    with pytest.raises(AddonLoadError):
        Addon(addon_with_duplicate_keys_path(), "stage")
