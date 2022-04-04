import logging

import docker
from sretoolbox.utils.logger import get_text_logger

from managedtenants.bundles.exceptions import LocalDockerRegistryError
from managedtenants.data.paths import BUNDLES_DIR


class LocalDockerRegistry:
    """
    Runs a local docker registry to act as a bridge between docker local cache
    and containerd local cache. This is because opm tooling uses containerd
    and is unaware of local images.

    The registry allows us to avoid uselessly pushing/pulling images to remote
    registries when using dry_run mode.
    """

    def __init__(self, name="mtbundles-local-registry", port=5555, debug=False):
        self.client = docker.from_env()
        self.port = port
        self.registry = f"localhost:{port}"
        self.name = name
        self.log = get_text_logger(
            "managedtenants-bundle-registry",
            level=logging.DEBUG if debug else logging.INFO,
        )
        self.container = None

    def run(self):
        try:
            self.container = self.client.containers.run(
                "quay.io/openshift/origin-docker-registry:latest",
                name=self.name,
                ports={str(self.port): str(self.port)},
                detach=True,
                environment={
                    "REGISTRY_AUTH": "htpasswd",
                    "REGISTRY_AUTH_HTPASSWD_REALM": "Registry Realm",
                    "REGISTRY_AUTH_HTPASSWD_PATH": "/auth/htpasswd",
                    "REGISTRY_OPENSHIFT_SERVER_ADDR": f"0.0.0.0:{self.port}",
                },
                volumes={
                    f"{BUNDLES_DIR}/auth": {"bind": "/auth", "mode": "ro"},
                },
            )
            self.log.debug(f"Created container: {self.container.id}")

        except docker.errors.APIError as e:
            err_msg = f"failed to run local registry: {e}"
            self.log.error(err_msg)
            raise LocalDockerRegistryError(err_msg)

    def teardown(self):
        try:
            if self.container is not None:
                self.container.remove(force=True)
                self.container = None

        except docker.errors.APIError as e:
            err_msg = f"failed to delete local registry: {e}"
            self.log.error(err_msg)
            raise LocalDockerRegistryError(err_msg)

    def exists(self):
        return self.container is not None
