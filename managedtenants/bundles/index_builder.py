import logging
import subprocess

from sretoolbox.container import Image
from sretoolbox.utils.logger import get_text_logger

from managedtenants.bundles.binary_deps import MTCLI, OPM
from managedtenants.bundles.docker_api import DockerAPI
from managedtenants.bundles.exceptions import IndexBuilderError


class IndexBuilder:
    def __init__(
        self,
        addon_dir,
        docker_api=None,
        dry_run=False,
        debug=False,
    ):
        self.addon_dir = addon_dir
        self.dry_run = dry_run
        self.docker_api = (
            docker_api if docker_api is not None else DockerAPI(debug=debug)
        )
        self.log = get_text_logger(
            "managedtenants-index-builder",
            level=logging.DEBUG if debug else logging.INFO,
        )

    def build_push_index_image(self, bundle_images, hash_string):
        """
        Build and push an index image.

        :param hash_string: A string to be used in the created image's tag.
        :param bundle_images: A list of bundle images to be added
        to the index image.
        :return: An Index image that has been pushed.
        """
        registry = self.docker_api.registry
        repo_name = f"{self.addon_dir.name}-index"
        image = Image(f"{registry}/{repo_name}:{hash_string}")

        self.log.info(
            f'Building index image "{image.url_tag}" with "{bundle_images}".'
        )
        cmd = [
            "index",
            "--container-tool",
            "docker",
            "add",
            "--permissive",
            "--bundles",
            ",".join([item.url_tag for item in bundle_images]),
            "--tag",
            image.url_tag,
        ]

        try:
            OPM.run(*cmd)
        except subprocess.CalledProcessError as e:
            raise IndexBuilderError(
                f"Failed to build index image: {e.stdout.decode()}."
            )

        if not self.dry_run:
            self.log.info(f'Pushing index image "{image.url_tag}".')
            self.docker_api.push(image)

        return image

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
