import logging
import os

import docker
import docker.api.build
from requests.exceptions import HTTPError
from sretoolbox.utils.logger import get_text_logger

from managedtenants.bundles.exceptions import DockerError, QuayAPIError
from managedtenants.bundles.quay_api import QuayAPI

# Hack to allow dockerfile as string
# https://github.com/docker/docker-py/issues/2105#issuecomment-613685891
docker.api.build.process_dockerfile = lambda dockerfile, path: (
    "Dockerfile",
    dockerfile,
)


class DockerAPI:
    """
    Class to build and push docker images.

    :param quay_api: (optional) QuayApi object used for pushing images. Default
                     to osd-addons, reading token from QUAY_APIKEY env var.
    :param registry: docker registry to use. Default: quay.io/{quay_api.org}.
    :param dockercfg_path: (optional) Custom path for the Docker config file.
                           If not present, the client does not login.
    :param force_push: overwrite an existing remote image.
    :param debug: Enable debug logging.
    :raise ValueError: If an invalid empty username is provided.
    """

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        quay_api=None,
        registry=None,
        dockercfg_path="/home/.docker/",
        debug=False,
        force_push=False,
    ):
        self.quay_api = (
            quay_api if quay_api is not None else QuayAPI(debug=debug)
        )
        self.registry = (
            registry if registry is not None else f"quay.io/{self.quay_api.org}"
        )
        self.client = docker.from_env()
        self.dockercfg_path = dockercfg_path
        self.force_push = force_push
        self.log = get_text_logger(
            "managedtenants-docker",
            level=logging.DEBUG if debug else logging.INFO,
        )

    def build_bundle(self, bundle):
        dockerfile = """
        FROM scratch
        COPY manifests /manifests/
        COPY metadata /metadata/
        """
        return self._build(
            path=bundle.path,
            dockerfile=dockerfile,
            tag=bundle.image.url_tag,
            labels=bundle.annotations,
        )

    def _build(self, path, dockerfile, tag, labels=None):
        """
        Build a docker image using in-memory dockerfile.

        :param path: Path to the context directory.
        :param dockerfile: A file object to use as the Dockerfile.
        :param tag: Tag for the built image.
        :param labels: (Optional) image labels.

        :raise DockerError: on a build error or if the built image has Size 0.
        """
        try:
            out_image, log_generator = self.client.images.build(
                path=str(path),  # Path(..) obj are not allowed
                dockerfile=dockerfile,
                labels=labels if labels is not None else {},
                tag=tag,
            )
            for log in log_generator:
                self.log.debug(log)

            self.log.debug(out_image.attrs)
            if out_image.attrs.get("Size", -1) == 0:
                raise DockerError(f"Built an empty image for path {path}.")

            return out_image

        except docker.errors.BuildError as e:
            raise DockerError(
                f"Failed to build image for path {path}, got {e}."
            )

    def push(self, image, ensure_repo=True):
        """
        Push an image to a remote repository.

        :param image: Sretoolbox Image(..) to be pushed.

        :raise DockerError: failed to push image.
        """
        try:
            # docker-py add auth headers from cred store
            # https://github.com/docker/docker-py/blob/a48a5a9647761406d66e8271f19fab7fa0c5f582/docker/utils/config.py#L33-L38
            os.environ["DOCKER_CONFIG"] = str(self.dockercfg_path)

            if self._is_quay_registry() and ensure_repo:
                self.log.info(f"Ensuring quay repo: {image.image}.")
                self.quay_api.ensure_repo(image.image)

            if not self._image_exists(image) or self.force_push:
                response = self.client.api.push(
                    image.url_tag, stream=True, decode=True
                )
                for log in response:
                    self.log.debug(log)

        except QuayAPIError as e:
            raise DockerError(
                f"Failed to ensure quay repo {image.repository} got {e}."
            )

        except docker.errors.APIError as e:
            raise DockerError(f"Failed to push {image.url_tag}, got {e}.")

    def _is_quay_registry(self):
        return self.registry.startswith("quay.io")

    def _image_exists(self, image):
        # The Image(...) sretoolbox library requires a valid quay registry.
        if not self._is_quay_registry():
            return False

        try:
            self.log.info(
                f"Skipping pushing {image.url_digest} as it already exists."
            )
            return True
        except HTTPError:
            # image.url_digest, calls digest which raises HTTPError
            # https://github.com/app-sre/sretoolbox/blob/master/sretoolbox/container/image.py#L119
            return False
