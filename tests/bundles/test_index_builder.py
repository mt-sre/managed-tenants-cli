import uuid

from conftest import REGISTRY_URL, get_test_docker_api

from managedtenants.bundles.addon_bundles import AddonBundles
from managedtenants.bundles.bundle_builder import BundleBuilder
from managedtenants.bundles.index_builder import IndexBuilder
from tests.testutils.paths import REFERENCE_ADDON


def test_index_builder_build_and_push():
    hash_string = uuid.uuid4().hex
    docker_api = get_test_docker_api()

    bundles = AddonBundles(REFERENCE_ADDON).get_all_bundles()
    bundle_builder = BundleBuilder(docker_api)
    bundle_builder.build_and_push_all(bundles, hash_string)

    expected_index_image_url = (
        f"{REGISTRY_URL}/reference-addon-index:{hash_string}"
    )

    index_builder = IndexBuilder(docker_api=docker_api)
    index_image = index_builder.build_and_push(bundles, hash_string)

    assert index_image.url_tag == expected_index_image_url
