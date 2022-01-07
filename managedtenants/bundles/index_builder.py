import subprocess

from sretoolbox.container import Image
from sretoolbox.utils.logger import get_text_logger

from managedtenants.bundles.binary_deps import MTCLI, OPM
from managedtenants.bundles.exceptions import IndexBuilderError
from managedtenants.bundles.utils import push_image


class IndexBuilder:
    def __init__(
        self,
        addon_dir,
        dry_run,
        quay_api=None,
        docker_conf_path=None,
    ):
        if quay_api is None:
            raise IndexBuilderError("Please provide a valid quay_api object.")
        self.addon_dir = addon_dir
        self.dry_run = dry_run
        self.quay_api = quay_api
        self.docker_conf = docker_conf_path
        self.logger = get_text_logger("managedtenants-catalog-builder")

    def build_push_index_image(
        self, bundle_images, hash_string, ensure_quay_repo=True
    ):
        """
        Returns an index image which points to the passed bundle_images.
        :param hash_string: A string to be used in the created image's tag.
        :param bundle_images: A list of bundle images to be added
        to the index image.
        :return: An Index image that has been pushed.
        """
        dry_run = self.dry_run
        addon = self.addon_dir
        repo_name = f"{addon.name}-index"
        if ensure_quay_repo and not self.quay_api.ensure_repo(
            repo_name, dry_run=self.dry_run
        ):
            raise IndexBuilderError(
                f"Failed to create/find quay repo:{repo_name} for the addon:"
                f" {addon.name}"
            )

        image = Image(f"{self.quay_api.org}/{repo_name}:{hash_string}")

        if not dry_run and image:
            self.logger.info('Image exists "%s"', image.url_tag)
            return image

        self.logger.info(
            'Building index image "%s" with %s', image.url_tag, bundle_images
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

        if not dry_run:
            try:
                OPM.run(*cmd)
            except subprocess.CalledProcessError as e:
                self.logger.error(
                    "Failed to build and push index image. opm output:"
                )
                self.logger.error(e.stdout.decode())
                # reraise the error to stop execution
                raise e

        return push_image(
            dry_run=dry_run,
            image=image,
            docker_conf_path=self.docker_conf,
            logger=self.logger,
        )


def list_bundles(index_image_url, logger=None):
    cmd = ["list-bundles", index_image_url]
    try:
        res = MTCLI.run(*cmd).rstrip()
        return [i for i in res.split("\n") if i != ""]
    except subprocess.CalledProcessError:
        if logger:
            logger.info(f"Failed to extract bundles from {index_image_url}")
        return None
