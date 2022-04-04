import logging
import subprocess

from sretoolbox.container import Image
from sretoolbox.utils.logger import get_text_logger

from managedtenants.bundles.binary_deps import OPM
from managedtenants.bundles.exceptions import DockerError, IndexBuilderError
from managedtenants.utils.git import get_short_hash


class IndexBuilder:
    def __init__(
        self,
        docker_api,
        dry_run=False,
        debug=False,
    ):
        self.dry_run = dry_run
        self.docker_api = docker_api
        self.log = get_text_logger(
            "managedtenants-index-builder",
            level=logging.DEBUG if debug else logging.INFO,
        )

    def build_and_push(self, bundles, hash_string=get_short_hash()):
        """
        Build and push an index image.

        :params bundles: List of Bundle to be added to the index image.
        :return: An Index image that has been pushed.
        """

        index_image = self._build(bundles, hash_string)
        return self._push(index_image)

    def _build(self, bundles, hash_string):
        if len(bundles) == 0:
            raise IndexBuilderError("invalid empty bundles list")

        # all bundles for a given addon produce the same index_repo
        index_image = Image(
            f"{self.docker_api.registry}/"
            f"{bundles[0].index_repo_name()}:{hash_string}"
        )
        self.log.info(f'Building index image "{index_image.url_tag}".')
        self.log.debug(
            f"Index image contains {len(bundles)} bundles: {bundles}."
        )

        cmd = [
            "index",
            "--container-tool",
            "docker",
            "add",
            "--permissive",
            "--bundles",
            ",".join([bundle.image.url_tag for bundle in bundles]),
            "--tag",
            index_image.url_tag,
        ]

        try:
            OPM.run(*cmd)
            self.docker_api.validate_image(index_image.url_tag)
            return index_image

        except subprocess.CalledProcessError as e:
            raise IndexBuilderError(
                f"Failed to build index image {index_image.url_tag} with opm"
                f" version {OPM.version}: {e.stdout.decode()}."
            )

        except DockerError as e:
            raise IndexBuilderError(f"Built invalid index_image: {e}")

    def _push(self, index_image):
        # skip pushing on dry_run
        if self.dry_run:
            return index_image

        try:
            self.log.info(f'Pushing index image "{index_image.url_tag}".')
            self.docker_api.push(index_image)
            return index_image

        except DockerError as e:
            err_msg = f"failed to push {index_image}: {e}."
            self.log.error(err_msg)
            raise IndexBuilderError(err_msg)
