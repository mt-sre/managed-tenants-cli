import subprocess

from sretoolbox.container import Image
from sretoolbox.utils.logger import get_text_logger

from managedtenants.bundles.binary_deps import MTCLI, OPM
from managedtenants.bundles.exceptions import BundleUtilsError
from managedtenants.bundles.utils import ensure_quay_repo, push_image


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

    def build_push_index_image(
        self, bundle_images, quay_org_path, hash_string, create_quay_repo
    ):
        """
        Returns an index image which points to the passed bundle_images.
        :param quay_org_path: Quay org to which images should be pushed.
        :param hash_string: A string to be used in the created image's tag.
        :param bundle_images: A list of bundle images to be added
        to the index image.
        :create_quay_repo: A boolean flag to indicate whether to create
        a quay repo for the index image. If set to `false`, the repo is
        expected to be created before-hand.
        :return: An Index image that has been pushed to the passed quay_org.
        """
        dry_run = self.dry_run
        addon = self.addon_dir
        repo_name = f"{addon.name}-index"
        if not ensure_quay_repo(
            dry_run=self.dry_run,
            org_path=quay_org_path,
            repo_name=repo_name,
            quay_token=self.quay_token,
            create_quay_repo=create_quay_repo,
        ):
            raise BundleUtilsError(
                f"Failed to create/find quay repo:{repo_name} for the addon:"
                f" {addon.name}"
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


def list_bundles(index_image_url, logger=None):
    cmd = ["list-bundles", index_image_url]
    try:
        res = MTCLI.run(*cmd).rstrip()
        return [i for i in res.split("\n") if i != ""]
    except subprocess.CalledProcessError:
        if logger:
            logger.info(f"Failed to extract bundles from {index_image_url}")
        return None
