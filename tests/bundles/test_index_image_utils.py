import sretoolbox
from conftest import REGISTRY_URL
from mock import patch

from managedtenants.bundles.bundle_utils import BundleUtils
from managedtenants.bundles.index_image_utils import IndexImageBuilder
from tests.testutils.addon_helpers import (
    bundles_dockerfile_path,
    mt_bundles_addon_path,
    return_false,
)

HASH_STRING = "int08h"


@patch.object(sretoolbox.container.Image, "__bool__", return_false)
def test_build_push_index_image(mt_bundles_addon_path):
    bundle_util_obj = BundleUtils(
        addon_dir=mt_bundles_addon_path, dry_run=False
    )
    expected_index_image_url = (
        f"{str(REGISTRY_URL)}/reference-addon-index:{HASH_STRING}"
    )
    with patch(
        "managedtenants.bundles.bundle_utils.ensure_quay_repo",
        return_value=True,
    ):
        build_images = bundle_util_obj.build_push_bundle_images_with_deps(
            quay_org_path=REGISTRY_URL,
            versions=[],
            docker_file_path=bundles_dockerfile_path(),
            create_quay_repo=False,
            hash_string=HASH_STRING,
        )
        index_image_builder = IndexImageBuilder(
            addon_dir=mt_bundles_addon_path, dry_run=False
        )
        with patch(
            "managedtenants.bundles.index_image_utils.ensure_quay_repo",
            return_value=True,
        ):
            index_image = index_image_builder.build_push_index_image(
                bundle_images=build_images,
                quay_org_path=REGISTRY_URL,
                hash_string=HASH_STRING,
                create_quay_repo=False,
            )
            assert index_image.url_tag == expected_index_image_url
