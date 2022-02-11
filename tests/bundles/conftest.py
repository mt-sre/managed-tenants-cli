import signal
import subprocess

import pytest

from managedtenants.bundles.docker_api import DockerAPI
from managedtenants.bundles.utils import run
from managedtenants.utils.quay_api import QuayAPI
from tests.testutils.paths import TEST_ROOT

LOCAL_REGISTRY_NAME = "mt-bundles-test-registry"
LOCAL_REGISTRY_PORT = 5000
REGISTRY_URL = f"127.0.0.1:{LOCAL_REGISTRY_PORT}"
HASH_STRING = "int08h"


class RegistryTearDownError(Exception):
    pass


def setup_image_registry():
    # Teardown if present
    # registry credentials => testuser:testpassword
    teardown_image_registry(raise_exception=False)
    cmd = [
        "docker",
        "run",
        "-d",
        "-p",
        f"{LOCAL_REGISTRY_PORT}:{LOCAL_REGISTRY_PORT}",
        "--restart=always",
        "-v",
        f"{TEST_ROOT}/bundles/auth:/auth",
        "-e",
        "REGISTRY_AUTH=htpasswd",
        "-e",
        "REGISTRY_AUTH_HTPASSWD_PATH=/auth/htpasswd",
        "--name",
        LOCAL_REGISTRY_NAME,
        # (sblaisdo) Use an image from either quay or catalog.redhat.com because
        # AppSRE Jenkins VMs prohibit pulling images from dockerhub
        "quay.io/openshift/origin-docker-registry:latest",
    ]
    try:
        res = run(cmd)
        res.check_returncode()
    except subprocess.CalledProcessError as e:
        print("Failed to setup local image registry")
        raise e


def teardown_image_registry(raise_exception=True):
    cmd = ["docker", "rm", "-f", LOCAL_REGISTRY_NAME]
    try:
        res = run(cmd)
        res.check_returncode()
    except subprocess.CalledProcessError:
        if raise_exception:
            raise RegistryTearDownError


@pytest.fixture(scope="package", autouse=True)
def setup_local_image_registry(request):
    setup_image_registry()
    install_signal_handlers()
    try:
        # Run tests
        yield
        teardown_image_registry()
    except Exception as e:
        teardown_image_registry()
        raise e


def install_signal_handlers():
    def teardown(signal, _):
        teardown_image_registry(raise_exception=False)
        pytest.exit(msg=f"Received signal: {signal}", returncode=1)

    signal.signal(signal.SIGINT, teardown)
    signal.signal(signal.SIGTERM, teardown)


def get_test_docker_api():
    return DockerAPI(
        registry=REGISTRY_URL,
        quay_api=QuayAPI(org=REGISTRY_URL, token="dummy"),
        dockercfg_path=TEST_ROOT / "bundles" / "auth",
        debug=False,
    )
