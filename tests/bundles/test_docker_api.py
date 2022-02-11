import uuid

from conftest import get_test_docker_api
from sretoolbox.container.image import Image

from managedtenants.bundles.bundle import Bundle
from tests.testutils.addon_helpers import reference_addon_bundle_annotations
from tests.testutils.paths import REFERENCE_ADDON


def test_bundle_annotations_become_labels():
    path = REFERENCE_ADDON / "main" / "0.1.6"
    hash_string = uuid.uuid4().hex

    docker_api = get_test_docker_api()
    image = Image(
        f"{docker_api.registry}/reference-addon-bundle:0.1.6-{hash_string}"
    )

    bundle = Bundle(
        addon_name="reference-addon",
        operator_name="reference-addon",
        path=path,
        version="0.1.6",
        image=image,
    )

    out_image = docker_api.build_bundle(bundle)
    labels = out_image.attrs["ContainerConfig"].get("Labels", {})
    expected_labels = reference_addon_bundle_annotations()

    assert len(labels) == len(expected_labels)
    for k, v in expected_labels.items():
        assert labels.get(k, None) == v
