import sretoolbox
from conftest import HASH_STRING, REGISTRY_URL, get_test_docker_api
from mock import patch

from managedtenants.bundles.bundle_builder import BundleBuilder
from managedtenants.bundles.index_builder import IndexBuilder
from managedtenants.utils.quay_api import QuayAPI
from tests.testutils.addon_helpers import mt_bundles_addon_path


def test_build_push_index_image(mt_bundles_addon_path):
    bundle_builder = BundleBuilder(
        addon_dir=mt_bundles_addon_path,
        docker_api=get_test_docker_api(),
    )
    expected_index_image_url = (
        f"{REGISTRY_URL}/reference-addon-index:{HASH_STRING}"
    )
    build_images = bundle_builder.build_push_bundle_images_with_deps(
        versions=[],
        hash_string=HASH_STRING,
    )
    index_builder = IndexBuilder(
        addon_dir=mt_bundles_addon_path,
        docker_api=get_test_docker_api(),
    )
    index_image = index_builder.build_push_index_image(
        bundle_images=build_images,
        hash_string=HASH_STRING,
    )
    assert index_image.url_tag == expected_index_image_url
