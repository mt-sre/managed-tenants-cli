from pathlib import Path

import pytest
import sretoolbox
from conftest import LOCAL_REGISTRY_PORT
from mock import patch

from managedtenants.bundles.bundle_utils import BundleUtils
from managedtenants.bundles.exceptions import BundleUtilsError
from tests.testutils.addon_helpers import (
    bundles_dockerfile_path,
    mt_bundles_addon_path,
    mt_bundles_addon_with_invalid_version_path,
    mt_bundles_with_invalid_dir_structure_path,
    return_false,
)

REGISTRY_URL = Path(f"127.0.0.1:{LOCAL_REGISTRY_PORT}/")
HASH_STRING = "int08h"


def all_bundle_images(filter_func=None):
    all_image_urls = [
        f"{REGISTRY_URL}/reference-addon-bundle:0.1.6-{HASH_STRING}",
        f"{REGISTRY_URL}/reference-addon-addon-operator-bundle:0.2.0-{HASH_STRING}",
        f"{REGISTRY_URL}/reference-addon-addon-operator-bundle:0.3.0-{HASH_STRING}",
        f"{REGISTRY_URL}/reference-addon-bundle:0.1.1-{HASH_STRING}",
        f"{REGISTRY_URL}/reference-addon-bundle:0.1.0-{HASH_STRING}",
        f"{REGISTRY_URL}/reference-addon-bundle:0.1.5-{HASH_STRING}",
        f"{REGISTRY_URL}/reference-addon-bundle:0.1.2-{HASH_STRING}",
        f"{REGISTRY_URL}/reference-addon-bundle:0.1.3-{HASH_STRING}",
        f"{REGISTRY_URL}/reference-addon-bundle:0.1.4-{HASH_STRING}",
        f"{REGISTRY_URL}/reference-addon-addon-operator-bundle:0.1.0-{HASH_STRING}",
    ]
    if filter_func:
        return list(filter(filter_func, all_image_urls))
    return all_image_urls


def bundle_images_for(versions):
    def filter_versions(image_url):
        # Always allow dependent operator bundles
        if "addon-operator-bundle" in image_url:
            return True
        for version in versions:
            if f"reference-addon-bundle:{version}" in image_url:
                return True
        return False

    return all_bundle_images(filter_func=filter_versions)


# Tests all public API's
@pytest.mark.parametrize(
    "addon_name, path, error_prefix",
    [
        ("reference-addon", "mt_bundles_addon_path", None),
        (
            "mock-operator-with-bundles",
            "mt_bundles_with_invalid_dir_structure_path",
            "Main addon directory not present for the addon",
        ),
        (
            "reference-addon-invalid-versions",
            "mt_bundles_addon_with_invalid_version_path",
            "Unable to parse the version number in the followingbundles",
        ),
    ],
)
def test_class_initialization_validation(
    addon_name, path, error_prefix, request
):
    """Tests initial BundleUtils class initialization validation"""
    addon_dir = request.getfixturevalue(path)
    if error_prefix:
        with pytest.raises(BundleUtilsError) as err:
            BundleUtils(addon_dir=addon_dir, dry_run=True)
        assert error_prefix in str(err)
    else:
        try:
            BundleUtils(addon_dir=addon_dir, dry_run=True)
        except BundleUtilsError:
            pytest.fail("Raised BundleUtilsError when it was not expected!")


@pytest.mark.parametrize(
    "addon_dir, versions, expected_image_urls",
    [
        ("mt_bundles_addon_path", [], all_bundle_images()),
        (
            "mt_bundles_addon_path",
            ["0.1.1", "0.1.2", "0.1.3"],
            bundle_images_for(["0.1.1", "0.1.2", "0.1.3"]),
        ),
    ],
)
@patch.object(sretoolbox.container.Image, "__bool__", return_false)
def test_build_push_bundle_images_with_deps(
    addon_dir, versions, expected_image_urls, request
):
    mt_bundles_path = request.getfixturevalue(addon_dir)
    bundle_builder = BundleUtils(addon_dir=mt_bundles_path, dry_run=False)
    with patch(
        "managedtenants.bundles.bundle_utils.ensure_quay_repo",
        return_value=True,
    ):
        images = bundle_builder.build_push_bundle_images_with_deps(
            quay_org_path=REGISTRY_URL,
            versions=versions,
            hash_string=HASH_STRING,
            docker_file_path=bundles_dockerfile_path(),
            create_quay_repo=False,
        )
        returned_image_urls = set(map(lambda image: image.url_tag, images))
        assert returned_image_urls == set(expected_image_urls)


def test_get_all_operator_names(mt_bundles_addon_path):
    bundle_util_obj = BundleUtils(
        addon_dir=mt_bundles_addon_path, dry_run=False
    )
    expected_operator_names = [
        "addon-operator.v0.1.0",
        "addon-operator.v0.2.0",
        "addon-operator.v0.3.0",
        "reference-addon.v0.1.0",
        "reference-addon.v0.1.1",
        "reference-addon.v0.1.2",
        "reference-addon.v0.1.3",
        "reference-addon.v0.1.4",
        "reference-addon.v0.1.5",
        "reference-addon.v0.1.6",
    ]
    res = bundle_util_obj.get_all_operator_names()
    assert set(expected_operator_names) == set(res)


def test_get_latest_version(mt_bundles_addon_path):
    bundle_util_obj = BundleUtils(
        addon_dir=mt_bundles_addon_path, dry_run=False
    )
    returned_max = bundle_util_obj.get_latest_version()
    expected_max = "0.1.6"
    assert returned_max == expected_max
