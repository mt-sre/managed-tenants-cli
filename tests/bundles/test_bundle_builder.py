import uuid

from conftest import REGISTRY_URL, get_test_docker_api

from managedtenants.bundles.addon_bundles import AddonBundles
from managedtenants.bundles.bundle_builder import BundleBuilder
from tests.testutils.paths import REFERENCE_ADDON


def expected_bundle_images(hash_string):
    return {
        f"{REGISTRY_URL}/reference-addon-bundle:0.1.6-{hash_string}",
        f"{REGISTRY_URL}/reference-addon-addon-operator-bundle:0.2.0-{hash_string}",
        f"{REGISTRY_URL}/reference-addon-addon-operator-bundle:0.3.0-{hash_string}",
        f"{REGISTRY_URL}/reference-addon-bundle:0.1.1-{hash_string}",
        f"{REGISTRY_URL}/reference-addon-bundle:0.1.0-{hash_string}",
        f"{REGISTRY_URL}/reference-addon-bundle:0.1.5-{hash_string}",
        f"{REGISTRY_URL}/reference-addon-bundle:0.1.2-{hash_string}",
        f"{REGISTRY_URL}/reference-addon-bundle:0.1.3-{hash_string}",
        f"{REGISTRY_URL}/reference-addon-bundle:0.1.4-{hash_string}",
        f"{REGISTRY_URL}/reference-addon-addon-operator-bundle:0.1.0-{hash_string}",
    }


def test_bundle_builder_reference_addon():
    hash_string = uuid.uuid4().hex
    bundles = AddonBundles(REFERENCE_ADDON).get_all_bundles()

    bundle_builder = BundleBuilder(get_test_docker_api(), False, False)
    bundle_builder.build_and_push_all(bundles, hash_string)

    expected_images = expected_bundle_images(hash_string)
    for bundle in bundles:
        assert bundle.image.url_tag in expected_images
