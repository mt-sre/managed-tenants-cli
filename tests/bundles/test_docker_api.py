import pytest
from conftest import get_test_docker_api

from tests.testutils.addon_helpers import mt_bundles_addon_path


def reference_addon_bundle_labels():
    return {
        "operators.operatorframework.io.bundle.mediatype.v1": "registry+v1",
        "operators.operatorframework.io.bundle.manifests.v1": "manifests/",
        "operators.operatorframework.io.bundle.metadata.v1": "metadata/",
        "operators.operatorframework.io.bundle.package.v1": "reference-addon",
        "operators.operatorframework.io.bundle.channels.v1": "alpha",
        "operators.operatorframework.io.bundle.channel.default.v1": "alpha",
    }


@pytest.mark.parametrize(
    "addon_dir, bundle_version, expected_labels",
    [
        (
            "mt_bundles_addon_path",
            "0.1.6",
            reference_addon_bundle_labels(),
        ),
        (
            "mt_bundles_addon_path",
            "0.1.5",
            reference_addon_bundle_labels(),
        ),
    ],
)
def test_build_bundle_labels(
    addon_dir, bundle_version, expected_labels, request
):
    bundle_main = request.getfixturevalue(addon_dir)
    bundle_path = bundle_main / "main" / bundle_version

    docker_api = get_test_docker_api()
    image = docker_api.build_bundle(bundle_path, "test-bundle-labels:latest")
    labels = image.attrs["ContainerConfig"].get("Labels", {})

    assert len(labels) == len(expected_labels)
    for k, v in expected_labels.items():
        assert labels.get(k, None) == v
