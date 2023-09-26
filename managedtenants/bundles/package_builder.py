import logging
import subprocess

from sretoolbox.binaries import KubectlPackage
from sretoolbox.container import Image
from sretoolbox.utils.logger import get_text_logger

from managedtenants.bundles.exceptions import DockerError
from managedtenants.utils.git import get_short_hash


class PackageBuilderError(Exception):
    pass


class PackageBuilder:
    def __init__(
        self,
        docker_api,
        dry_run=False,
        debug=False,
        build_with="digest",
    ):
        self.dry_run = dry_run
        self.docker_api = docker_api
        self.build_with = build_with
        self.kubectl_package = KubectlPackage(
            version="1.9.0", download_path="/tmp"
        )
        self.log = get_text_logger(
            "managedtenants-package-builder",
            level=logging.DEBUG if debug else logging.INFO,
        )

    def build_and_push(self, addon_package):
        package_image = self._build(addon_package)
        return self._push(package_image=package_image)

    def _build(self, addon_package, hash_string=get_short_hash()):
        package_image = Image(
            f"{self.docker_api.registry}/"
            f"{addon_package.image_name}:{hash_string}"
        )

        addon_package.image = package_image

        command = [
            "validate",
            f"{addon_package.path.resolve()}",
        ]
        self.log.info(f'Validating package image "{package_image.url_tag}"')
        try:
            self.kubectl_package.run(*command)
        except subprocess.CalledProcessError as exp:
            self.log.error(exp.output.decode())
            raise

        self.log.info(
            f'Building package image "{package_image.url_tag}": {command}'
        )
        _ = self.docker_api.build_package(addon_package)
        return package_image

    def _push(self, package_image):
        if self.dry_run:
            return package_image

        try:
            self.log.info(f'Pushing package image "{package_image.url_tag}".')
            self.docker_api.push(package_image)
            return package_image

        except DockerError as e:
            err_msg = f"failed to push {package_image}: {e}."
            self.log.error(err_msg)
            raise PackageBuilderError(err_msg)
