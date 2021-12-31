import sretoolbox
from conftest import HASH_STRING, QUAY_API, REGISTRY_URL
from mock import patch

from managedtenants.bundles.bundle_builder import BundleBuilder
from managedtenants.bundles.index_builder import IndexBuilder
from managedtenants.utils.quay_api import QuayApi
from tests.testutils.addon_helpers import (
    bundles_dockerfile_path,
    mt_bundles_addon_path,
    return_false,
    return_true,
)


@patch.object(sretoolbox.container.Image, "__bool__", return_false)
@patch.object(QuayApi, "ensure_repo", return_true)
def test_build_push_index_image(mt_bundles_addon_path):
    bundle_builder = BundleBuilder(
        addon_dir=mt_bundles_addon_path,
        dry_run=False,
        quay_api=QUAY_API,
    )
    expected_index_image_url = (
        f"{REGISTRY_URL}/reference-addon-index:{HASH_STRING}"
    )
    build_images = bundle_builder.build_push_bundle_images_with_deps(
        versions=[],
        docker_file_path=bundles_dockerfile_path(),
        hash_string=HASH_STRING,
    )
    index_builder = IndexBuilder(
        addon_dir=mt_bundles_addon_path,
        dry_run=False,
        quay_api=QUAY_API,
    )
    index_image = index_builder.build_push_index_image(
        bundle_images=build_images,
        hash_string=HASH_STRING,
    )
    assert index_image.url_tag == expected_index_image_url
