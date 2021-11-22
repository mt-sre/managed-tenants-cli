import subprocess

from sretoolbox.container import Image
from sretoolbox.utils.logger import get_text_logger

from managedtenants.bundles.binary_deps import OPM
from managedtenants.bundles.exceptions import BundleUtilsError
from managedtenants.bundles.utils import push_image, quay_repo_exists


class IndexImageBuilder:
    def __init__(
        self,
        addon_dir,
        dry_run,
        quay_token=None,
        docker_conf_path=None,
        logger=None,
    ):
        # pylint: disable=R0913
        self.addon_dir = addon_dir
        self.dry_run = dry_run
        self.quay_token = quay_token
        self.docker_conf = docker_conf_path
        if logger:
            self.logger = logger
        else:
            self.logger = get_text_logger("managedtenants-indeximage-builder")

    def build_push_index_image(self, bundle_images, quay_org_path, hash_string):
        """
        Returns an index image which points to the passed bundle_images.
        :param quay_org_path: Quay org to which images should be pushed.
        :param hash_string: A string to be used in the created image's tag.
        :param bundle_images: A list of bundle images to be added
        to the index image.
        :return: An Index image that has been pushed to the passed quay_org.
        """
        dry_run = self.dry_run
        addon = self.addon_dir
        repo_name = f"{addon.name}-index"
        if not quay_repo_exists(
            dry_run=self.dry_run,
            org_path=quay_org_path,
            repo_name=repo_name,
            quay_token=self.quay_token,
        ):
            raise BundleUtilsError(
                f"Quay repo:{repo_name} for the addon:               "
                f" {addon.name} doesnt exist!"
            )

        image = Image(str(quay_org_path / f"{repo_name}:{hash_string}"))

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
