import uuid

import pytest
from conftest import REGISTRY_URL, get_test_docker_api

from managedtenants.bundles.addon_bundles import AddonBundles
from managedtenants.bundles.bundle_builder import BundleBuilder
from tests.testutils.paths import REFERENCE_ADDON, TEST_ROOT


@pytest.mark.parametrize(
    "path,expected_images,single_bundle",
    [
        (
            REFERENCE_ADDON,
            [
                f"{REGISTRY_URL}/reference-addon-bundle:0.1.6-{{hash_string}}",
                f"{REGISTRY_URL}/reference-addon-addon-operator-bundle:0.3.0-{{hash_string}}",
            ],
            True,
        ),
        (
            TEST_ROOT
            / "testdata"
            / "addons"
            / "reference-addon-multiple-bundles",
            [
                f"{REGISTRY_URL}/reference-addon-multiple-bundles-bundle:0.1.5-{{hash_string}}",
                f"{REGISTRY_URL}/reference-addon-multiple-bundles-bundle:0.1.6-{{hash_string}}",
            ],
            False,
        ),
    ],
)
def test_bundle_builder_reference_addon(path, expected_images, single_bundle):
    hash_string = uuid.uuid4().hex
    bundles = AddonBundles(path, single_bundle=single_bundle).get_all_bundles()

    bundle_builder = BundleBuilder(get_test_docker_api(), False, False)
    bundle_builder.build_and_push_all(bundles, hash_string)

    counter = {
        img.format(hash_string=hash_string): 1 for img in expected_images
    }
    for bundle in bundles:
        counter[bundle.image.url_tag] -= 1

    assert sum(counter.values()) == 0
