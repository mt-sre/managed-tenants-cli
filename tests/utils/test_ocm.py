from io import StringIO

import pytest
from jsonschema.exceptions import SchemaError

from managedtenants.data.paths import SCHEMAS_DIR
from managedtenants.utils.ocm import OcmCli
from tests.testutils.addon_helpers import (  # noqa: F401; noqa: F401; flake8: noqa: F401
    addon_with_imageset_and_default_config,
    addon_with_imageset_and_multiple_config,
    addon_with_imageset_and_parameter_config,
    addon_with_indeximage,
    addon_with_only_imageset_config,
    addon_without_config,
)


@pytest.mark.parametrize(
    "addon_str,expected_result",
    [
        (
            "addon_with_imageset_and_default_config",
            [{"id": "0", "name": "DEFAULT", "value": "TRUE"}],
        ),
        (
            "addon_with_imageset_and_multiple_config",
            [
                {
                    "id": "0",
                    "name": "LOCATION",
                    "value": "Black Mesa Research Facility",
                },
                {"id": "1", "name": "USER", "value": "Gordon Freeman"},
                {"id": "2", "name": "HUMAN", "value": "true"},
            ],
        ),
        (
            "addon_with_only_imageset_config",
            [
                {
                    "id": "0",
                    "name": "LOCATION",
                    "value": "Black Mesa Research Facility",
                },
                {"id": "1", "name": "USER", "value": "Gordon Freeman"},
                {"id": "2", "name": "HUMAN", "value": "true"},
            ],
        ),
        (
            "addon_with_indeximage",
            [
                {
                    "id": "0",
                    "name": "LOCATION",
                    "value": "Black Mesa Research Facility",
                },
                {"id": "1", "name": "USER", "value": "Gordon Freeman"},
                {"id": "2", "name": "HUMAN", "value": "true"},
            ],
        ),
        (
            # addon without any envs defined.
            "addon_without_config",
            [],
        ),
    ],
)
def test_ocm_addon_environment_variables(addon_str, expected_result, request):
    addon = request.getfixturevalue(addon_str)
    ocm_cli = OcmCli(offline_token=None)
    if addon.imageset:
        ocm_addon = ocm_cli._addon_from_imageset(
            imageset=addon.imageset, metadata=addon.metadata
        )
    else:
        ocm_addon = ocm_cli._addon_from_metadata(metadata=addon.metadata)

    assert (
        ocm_addon.get("config").get("add_on_environment_variables")
        == expected_result
    )


@pytest.mark.parametrize(
    "addon_str,expected_result",
    [
        (
            "addon_with_imageset_and_default_config",
            [{"id": "size"}],
        ),
        (
            "addon_with_imageset_and_parameter_config",
            [{"id": "size"}, {"id": "duration"}],
        ),
    ],
)
def test_ocm_addon_parameters(addon_str, expected_result, request):
    addon = request.getfixturevalue(addon_str)
    ocm_cli = OcmCli(offline_token=None)
    if addon.imageset:
        ocm_addon = ocm_cli._addon_from_imageset(
            imageset=addon.imageset, metadata=addon.metadata
        )
    else:
        ocm_addon = ocm_cli._addon_from_metadata(metadata=addon.metadata)

    params = ocm_addon.get("parameters")
    assert params is not None
    items = params.get("items")
    assert items is not None

    assert len(items) == len(expected_result)

    for idx, item in enumerate(items):
        assert item["id"] == expected_result[idx]["id"]


@pytest.mark.parametrize(
    "addon_str,expected_result",
    [
        (
            "addon_with_imageset_and_default_config",
            [
                {
                    "id": "0",
                    "source_secret": "managed-secret-one",
                    "destination_secret": "managed-secret-one",
                },
                {
                    "id": "1",
                    "source_secret": "pull-secret-one",
                    "destination_secret": "pull-secret-one",
                },
            ],
        ),
        (
            "addon_with_imageset_and_multiple_config",
            [
                {
                    "id": "0",
                    "source_secret": "imageset-secret-1",
                    "destination_secret": "imageset-secret-1",
                },
                {
                    "id": "1",
                    "source_secret": "pull-secret-one",
                    "destination_secret": "pull-secret-one",
                },
            ],
        ),
        (
            "addon_with_only_imageset_config",
            [
                {
                    "id": "0",
                    "source_secret": "imageset-secret-1",
                    "destination_secret": "imageset-secret-1",
                },
                {
                    "id": "1",
                    "source_secret": "pull-secret-one",
                    "destination_secret": "pull-secret-one",
                },
            ],
        ),
        (
            # addon without any secrets defined.
            "addon_without_config",
            [],
        ),
    ],
)
def test_ocm_addon_secrets(addon_str, expected_result, request):
    addon = request.getfixturevalue(addon_str)
    ocm_cli = OcmCli(offline_token=None)
    if addon.imageset:
        ocm_addon = ocm_cli._addon_from_imageset(
            imageset=addon.imageset, metadata=addon.metadata
        )
    else:
        ocm_addon = ocm_cli._addon_from_metadata(metadata=addon.metadata)

    assert (
        ocm_addon.get("config").get("add_on_secret_propagations")
        == expected_result
    )
