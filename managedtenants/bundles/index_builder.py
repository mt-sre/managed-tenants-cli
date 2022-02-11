import logging
import subprocess

from sretoolbox.container import Image
from sretoolbox.utils.logger import get_text_logger

from managedtenants.bundles.binary_deps import MTCLI, OPM
from managedtenants.bundles.docker_api import DockerAPI
from managedtenants.bundles.exceptions import DockerError, IndexBuilderError


class IndexBuilder:
    def __init__(
        self,
        docker_api=None,
        dry_run=False,
        debug=False,
    ):
        self.dry_run = dry_run
        self.docker_api = (
            docker_api if docker_api is not None else DockerAPI(debug=debug)
        )
        self.log = get_text_logger(
            "managedtenants-index-builder",
            level=logging.DEBUG if debug else logging.INFO,
        )

    def build_and_push(self, bundles, hash_string):
        """
        Build and push an index image.

        :params bundles: List of Bundle to be added to the index image.
        :param hash_string: A string to be used in the created image's tag.
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
            return index_image

        except subprocess.CalledProcessError as e:
            raise IndexBuilderError(
                f"Failed to build index image {index_image.url_tag}:"
                f" {e.stdout.decode()}."
            )

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

    # TODO (sblaisdo) - golang library does not trust self-signed certs
    # find a way to test this functionality with the local testing registry
    # before releasing in the wild
    def _list_bundles(self, index_image_url):
        cmd = ["list-bundles", index_image_url]
        try:
            res = MTCLI.run(*cmd).rstrip()
            return list(res.split("\n")) if res != "" else []

        except subprocess.CalledProcessError as e:
            self.log.error(
                f"Failed to extract bundles from {index_image_url}. mtcli"
                " output:"
            )
            self.log.error(e.stdout.decode())
            raise e
