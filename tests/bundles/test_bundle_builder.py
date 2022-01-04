from pathlib import Path

import pytest
import sretoolbox
from conftest import QUAY_API, REGISTRY_URL
from mock import patch

from managedtenants.bundles.bundle_builder import BundleBuilder
from managedtenants.bundles.exceptions import BundleBuilderError
from managedtenants.utils.quay_api import QuayApi
from tests.testutils.addon_helpers import (
    bundles_dockerfile_path,
    mt_bundles_addon_path,
    mt_bundles_addon_with_invalid_version_path,
    mt_bundles_with_invalid_dir_structure_path,
    reference_addon_path,
    return_false,
    return_true,
)

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
        with pytest.raises(BundleBuilderError) as err:
            BundleBuilder(addon_dir=addon_dir, dry_run=True, quay_api=QUAY_API)
        assert error_prefix in str(err)
    else:
        try:
            BundleBuilder(addon_dir=addon_dir, dry_run=True, quay_api=QUAY_API)
        except BundleBuilderError:
            pytest.fail("Raised BundleBuilderError when it was not expected!")


def test_csv_objects_instance_variable_initalization(mt_bundles_addon_path):
    addon_dir = mt_bundles_addon_path
    instance = BundleBuilder(addon_dir=addon_dir, dry_run=True, quay_api=QUAY_API)
    expected_csv_versions = {
        "reference-addon": [
            "0.1.0",
            "0.1.1",
            "0.1.2",
            "0.1.3",
            "0.1.4",
            "0.1.5",
            "0.1.6",
        ],
        "addon-operator": ["0.1.0", "0.2.0", "0.3.0"],
    }

    for operator_name, csvs in instance.csv_objects.items():
        expected_versions = expected_csv_versions.get(operator_name)
        assert expected_versions is not None
        received_versions = list(map(lambda obj: obj["spec"]["version"], csvs))
        assert received_versions == expected_versions


@pytest.mark.parametrize(
    "versions, expected_res",
    [
        (
            {
                "reference-addon": [
                    "0.1.0",
                    "0.1.1",
                    "0.1.2",
                    "0.1.2-1",
                    "0.1.2-2",
                    "1.1.3-beta",
                ],
                "addon-operator": ["0.1.0", "0.2.0", "0.3.0"],
            },
            {},
        ),
        (
            {
                "reference-addon": ["1.0.0", "1.1.0", "1.2.0"],
                "addon-operator": ["invalid", "0.1.0", "0.2.0"],
            },
            {"addon-operator": ["invalid"]},
        ),
        (
            {
                "reference-addon": ["1.0.0", "1.1.0", "1.2.0", "13"],
                "addon-operator": ["invalid", "0.1.0", "0.2.0"],
            },
            {"addon-operator": ["invalid"], "reference-addon": ["13"]},
        ),
    ],
)
def test_invalid_csv_versions(versions, expected_res):
    instance = BundleBuilder(
        addon_dir=reference_addon_path(),
        dry_run=True,
        quay_api=QUAY_API
    )
    # Set the correct csv_objects
    current_csv_objects = {}
    for operator_name, verion_arr in versions.items():
        csv_objects = []
        for version in verion_arr:
            curr_csv_object = {"spec": {"version": version}}
            csv_objects.append(curr_csv_object)
        current_csv_objects[operator_name] = csv_objects

    instance.csv_objects = current_csv_objects

    res = instance._invalid_csv_versions()
    assert res == expected_res


@pytest.mark.parametrize(
    "replaces_data, expected_res",
    [
        (
            {
                "reference-addon": [
                    ["0.1.0", {"name": "reference-addon.v0.1.0"}],
                    [
                        "0.2.0",
                        {
                            "replaces": "reference-addon.v0.1.0",
                            "name": "reference-addon.v0.2.0",
                        },
                    ],
                    [
                        "0.3.0",
                        {
                            "replaces": "reference-addon.v0.2.0",
                            "name": "reference-addon.v0.3.0",
                        },
                    ],
                ],
                "addon-operator": [
                    ["0.1.0", {"name": "addon-operator.v.0.1.0"}],
                    [
                        "0.2.0",
                        {
                            "name": "addon-operator.v.0.2.0",
                            "replaces": "addon-operator.v.0.1.0",
                        },
                    ],
                    [
                        "0.3.0",
                        {
                            "name": "addon-operator.v.0.3.0",
                            "replaces": "addon-operator.v.0.2.0",
                        },
                    ],
                ],
            },
            # invalid_objects
            {"reference-addon": [], "addon-operator": []},
        ),
        (
            {
                "reference-addon": [
                    [
                        "0.1.0",
                        {
                            "name": "reference-addon.v0.1.0",
                            "replaces": "reference-addon.v0.0.1",
                        },
                    ],
                    [
                        "0.2.0",
                        {
                            "replaces": "reference-addon.v0.1.0",
                            "name": "reference-addon.v0.2.0",
                        },
                    ],
                    [
                        "0.3.0",
                        {
                            "replaces": "reference-addon.v0.2.0",
                            "name": "reference-addon.v0.3.0",
                        },
                    ],
                ]
            },
            # invalid_objects
            {
                "reference-addon": [
                    [
                        "reference-addon.v0.1.0",
                        "replaces attr not expected for the first csv",
                    ]
                ]
            },
        ),
        (
            {
                "reference-addon": [
                    [
                        "0.1.0",
                        {
                            "name": "reference-addon.v0.1.0",
                        },
                    ],
                    [
                        "0.2.0",
                        {
                            "replaces": "reference-addon.v0.3.0",
                            "name": "reference-addon.v0.2.0",
                        },
                    ],
                    [
                        "0.3.0",
                        {
                            "replaces": "reference-addon.v0.7.0",
                            "name": "reference-addon.v0.3.0",
                        },
                    ],
                    [
                        # No errors
                        "0.4.0",
                        {
                            "replaces": "reference-addon.v0.1.0",
                            "skips": [
                                "reference-addon.v0.3.0",
                                "reference-addon.v0.2.0",
                            ],
                            "name": "reference-addon.v0.4.0",
                        },
                    ],
                    [
                        "0.5.0",
                        {
                            "replaces": "reference-addon.v0.1.0",
                            "skips": [
                                "reference-addon.v0.3.0",
                                "reference-addon.v0.2.0",
                                "reference-addon.v0.5.0",
                            ],
                            "name": "reference-addon.v0.5.0",
                        },
                    ],
                    [
                        "0.6.0",
                        {
                            "replaces": "reference-addon.v0.1.0",
                            "skips": [
                                "reference-addon.v0.3.0",
                                "reference-addon.v0.2.0",
                                "reference-addon.v0.10.0",
                            ],
                            "name": "reference-addon.v0.6.0",
                        },
                    ],
                ]
            },
            # errors
            {
                "reference-addon": [
                    [
                        "reference-addon.v0.2.0",
                        "replaces attr doesnt point to the previous csv",
                    ],
                    [
                        "reference-addon.v0.3.0",
                        "replaces attr refers to a csv thats not present",
                    ],
                    [
                        "reference-addon.v0.3.0",
                        "replaces attr doesnt point to the previous csv",
                    ],
                    [
                        "reference-addon.v0.5.0",
                        "skipped csv version/s are newer than the current csv",
                    ],
                    [
                        "reference-addon.v0.6.0",
                        "skipped csv/csvs are not present in the list of"
                        " bundles",
                    ],
                    [
                        "reference-addon.v0.6.0",
                        "skipped csv version/s are newer than the current csv",
                    ],
                ]
            },
        ),
    ],
)
def test_csvs_with_invalid_replaces_attr(replaces_data, expected_res):
    instance = BundleBuilder(
        addon_dir=reference_addon_path(),
        dry_run=True,
        quay_api=QUAY_API
    )
    csv_objects = {}
    for operator_name, data_objs in replaces_data.items():
        curr_csv_objects = []
        for data in data_objs:
            version = data[0]
            other_attrs = data[1]
            csv = {
                "metadata": {"name": other_attrs["name"]},
                "spec": {
                    "replaces": other_attrs.get("replaces"),
                    "skips": other_attrs.get("skips", []),
                    "version": version,
                },
            }
            curr_csv_objects.append(csv)
        csv_objects[operator_name] = curr_csv_objects
    # Set the passed csv objects
    instance.csv_objects = csv_objects
    res = instance._csvs_with_invalid_replaces_attr()
    assert res == expected_res


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
@patch.object(QuayApi, "ensure_repo", return_true)
def test_build_push_bundle_images_with_deps(
    addon_dir, versions, expected_image_urls, request
):
    mt_bundles_path = request.getfixturevalue(addon_dir)
    bundle_builder = BundleBuilder(
        addon_dir=mt_bundles_path, dry_run=False, quay_api=QUAY_API
    )
    images = bundle_builder.build_push_bundle_images_with_deps(
        versions=versions,
        hash_string=HASH_STRING,
        docker_file_path=bundles_dockerfile_path(),
    )
    returned_image_urls = set(map(lambda image: image.url_tag, images))
    assert returned_image_urls == set(expected_image_urls)


def test_get_all_operator_names(mt_bundles_addon_path):
    bundle_builder = BundleBuilder(
        addon_dir=mt_bundles_addon_path, dry_run=False, quay_api=QUAY_API
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
    res = bundle_builder.get_all_operator_names()
    assert set(expected_operator_names) == set(res)


def test_get_latest_version(mt_bundles_addon_path):
    bundle_builder = BundleBuilder(
        addon_dir=mt_bundles_addon_path, dry_run=False, quay_api=QUAY_API
    )
    returned_max = bundle_builder.get_latest_version()
    expected_max = "0.1.6"
    assert returned_max == expected_max
