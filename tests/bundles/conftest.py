import signal
import subprocess
from pathlib import Path

import pytest

from managedtenants.bundles.utils import run

LOCAL_REGISTRY_NAME = "mt-bundles-test-registry"
LOCAL_REGISTRY_PORT = 5000
REGISTRY_URL = Path(f"127.0.0.1:{LOCAL_REGISTRY_PORT}")


class RegistryTearDownError(Exception):
    pass


def setup_image_registry():
    # Teardown if present
    teardown_image_registry(raise_exception=False)
    cmd = [
        "docker",
        "run",
        "-d",
        "-p",
        f"{LOCAL_REGISTRY_PORT}:{LOCAL_REGISTRY_PORT}",
        "--restart=always",
        "--name",
        LOCAL_REGISTRY_NAME,
        "registry:2",
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
