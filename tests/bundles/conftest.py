import signal

import pytest

from managedtenants.bundles.docker_api import DockerAPI
from managedtenants.bundles.registry import LocalDockerRegistry
from managedtenants.data.paths import BUNDLES_DIR

LOCAL_REGISTRY_NAME = "mt-bundles-test-registry"
LOCAL_REGISTRY_PORT = 9999
REGISTRY_URL = f"127.0.0.1:{LOCAL_REGISTRY_PORT}"
HASH_STRING = "int08h"


@pytest.fixture(scope="package", autouse=True)
def setup_local_image_registry(request):
    registry = LocalDockerRegistry(
        name=LOCAL_REGISTRY_NAME, port=LOCAL_REGISTRY_PORT, debug=True
    )

    def teardown(signal, _):
        registry.teardown()
        pytest.exit(msg=f"Received signal: {signal}", returncode=1)

    signal.signal(signal.SIGINT, teardown)
    signal.signal(signal.SIGTERM, teardown)

    try:
        registry.run()
        yield
        registry.teardown()

    except Exception as e:
        registry.teardown()
        raise e


def get_test_docker_api():
    return DockerAPI(
        registry=REGISTRY_URL,
        quay_org="dummy",
        dockercfg_path=BUNDLES_DIR / "auth",
        debug=False,
        force_push=True,
    )
