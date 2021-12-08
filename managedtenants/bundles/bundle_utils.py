#!/usr/bin/env python
import re
import subprocess
from pathlib import Path

import semver
from sretoolbox.container import Image
from sretoolbox.utils.logger import get_text_logger

from managedtenants.bundles.binary_deps import OPERATOR_SDK
from managedtenants.bundles.exceptions import BundleUtilsError
from managedtenants.bundles.utils import (
    ensure_quay_repo,
    get_subdirs,
    load_yaml,
    push_image,
)
from managedtenants.utils.general_utils import run


class BundleUtils:
    def __init__(
        self,
        addon_dir,
        dry_run,
        quay_token=None,
        docker_conf_path=None,
        logger=None,
    ):
        # pylint: disable=R0913
        err = self._validate_dir_structure(addon_dir)
        if err:
            raise BundleUtilsError(err)
        self.addon_dir = addon_dir
        self.dry_run = dry_run
        self.quay_token = quay_token
        self.docker_conf = docker_conf_path
        if logger:
            self.logger = logger
        else:
            self.logger = get_text_logger("managedtenants-bundles")

    def validate_local_bundles(self):
        """
        Validates the all the bundles present locally under
        the given addon directory.
        """
        bundles = self._get_all_bundles()
        invalid_bundles = [
            bundle
            for bundle in bundles
            if not self._operator_sdk_validate(bundle)
        ]
        if not invalid_bundles:
            return ""

        err_prefix = "OperatorSDK failed to validate the following bundles: \n"
        err_msg = err_prefix + "\n".join(invalid_bundles)
        return err_msg

    def get_latest_version(self):
        """
        Returns the latest bundle in the given addon directory
        """
        main_addon_path = self.addon_dir.joinpath("main")
        return max([item.name for item in get_subdirs(main_addon_path)])

    def get_all_operator_names(self):
        all_bundles = self._get_all_bundles()
        operator_names = []
        for bundle in all_bundles:
            operator_name = self.get_operator_name_from_bundle(bundle)
            if operator_name:
                operator_names.append(operator_name)

        return operator_names

    @staticmethod
    def get_operator_name_from_bundle(bundle_dir):
        manifests_dir = Path(bundle_dir) / "manifests"
        csv_file_pattern = r".+\.(csv|clusterserviceversion)\..+$"
        for file in manifests_dir.iterdir():
            if re.search(csv_file_pattern, file.name):
                contents = load_yaml(file)
                if contents:
                    return contents.get("metadata", {}).get("name")
        return None

    def build_push_bundle_images_with_deps(
        self,
        quay_org_path,
        versions,
        hash_string,
        docker_file_path,
        create_quay_repo,
    ):
        # pylint: disable=R0913
        """
        Builds and pushes bundle images in the given addon directory.
        :param quay_org_path: Quay org to which images should be pushed.
        :param versions: A list versions to consider
        :param hash_string: A string to be used in the created
        image tag.
        :param docker_file_path: Path to the dockerfile to be
        used to create the bundle image.
        :create_quay_repo: A boolean flag to indicate whether to create
        quay repos for the bundles. If set to `false`, repos are
        expected to be created before-hand.
        :return: A list of pushed bundle images
        """
        all_inner_addons = get_subdirs(path=self.addon_dir)
        self.logger.info(f"quay org: {quay_org_path}")
        addon_images = []
        for inner_addon in all_inner_addons:
            addon_images.extend(
                self._build_push_bundle_images(
                    addon=inner_addon,
                    quay_org_path=quay_org_path,
                    versions=versions,
                    hash_string=hash_string,
                    dockerfile_path=docker_file_path,
                    create_quay_repo=create_quay_repo,
                )
            )
        return addon_images

    def validate_bundle_image(self, image):
        """
        Validates the passed image using operator-sdk binary
        """
        self.logger.info('Validating bundle image "%s"', image.url_tag)

        cmd = [
            "bundle",
            "validate",
            image.url_tag,
        ]

        if not self.dry_run:
            try:
                OPERATOR_SDK.run(*cmd)
            except subprocess.CalledProcessError as e:
                self.logger.error(
                    "Failed to validate bundle image. operator-sdk output:"
                )
                self.logger.error(e.stdout.decode())
                # reraise the error to stop execution
                raise e

        return image

    def _build_push_bundle_images(
        self,
        addon,
        quay_org_path,
        hash_string,
        dockerfile_path,
        create_quay_repo,
        versions=None,
    ):
        # pylint: disable=R0913
        """
        :param addon: A Posix directory path
        :param main_addon: A boolean to indicate if the passed addon
        is the "main" addon.
        :param quay_org_path: Quay org to which images should be pushed.
        :param versions: A list versions to consider
        :param hash_string: A string to be used in the created image tag.
        :param docker_file_path: Path to the dockerfile to be used to create
        the bundle image.
        :return: A list of pushed bundle images
        """
        images = []
        main_addon = self._is_main_addon(addon)
        # The main addon lives inside the "main" directory, so
        # we look at its parents name to get the addon name.
        # (sblaisdo) MTSRE-225: prepend deps /w addon_id to avoid quay
        # collisions
        addon_id = addon.parent.name
        addon_name = addon_id if main_addon else f"{addon_id}-{addon.name}"

        for bundle in filter(self._version_parsable, get_subdirs(addon)):
            if main_addon and versions and bundle.name not in versions:
                self.logger.info(
                    f"skipping version {bundle.name} for main operator"
                )
                continue
            bundle_image = self._build_push_bundle_image(
                bundle=bundle,
                quay_org_path=quay_org_path,
                hash_string=hash_string,
                docker_file_path=dockerfile_path,
                addon_name=addon_name,
                create_quay_repo=create_quay_repo,
            )
            images.append(
                self.validate_bundle_image(
                    image=bundle_image,
                )
            )
        return images

    def _build_push_bundle_image(
        self,
        bundle,
        quay_org_path,
        hash_string,
        docker_file_path,
        addon_name,
        create_quay_repo,
    ):
        # pylint: disable=R0913
        repo_name = f"{addon_name}-bundle"
        if not ensure_quay_repo(
            dry_run=self.dry_run,
            org_path=quay_org_path,
            repo_name=repo_name,
            quay_token=self.quay_token,
            create_quay_repo=create_quay_repo,
        ):
            raise BundleUtilsError(
                f"Failed to create/find quay repo:{repo_name} for the addon:"
                f" {addon_name}"
            )
        image = Image(
            str(quay_org_path / f"{repo_name}:{bundle.name}-{hash_string}")
        )
        if not self.dry_run and image:
            self.logger.info('Image exists "%s"', image.url_tag)
            return image

        self.logger.info('Building bundle image "%s"', image.url_tag)

        dockerfile = Path(docker_file_path)
        cmd = [
            "docker",
            "build",
            "-f",
            str(dockerfile),
            "-t",
            image.url_tag,
            str(bundle),
        ]

        run(cmd=cmd, logger=self.logger)

        return push_image(
            dry_run=self.dry_run,
            image=image,
            logger=self.logger,
            docker_conf_path=self.docker_conf,
        )

    def _get_all_bundles(self):
        """
        Gets all the bundles under the top-level addon-directory.
        (Both the main addon's bundles and the dependent addon's bundles)
        """
        addon_bundles = [
            list(get_subdirs(inner_addon))
            for inner_addon in get_subdirs(self.addon_dir)
        ]

        # Flatten
        result = [
            bundle for inner_list in addon_bundles for bundle in inner_list
        ]
        return map(str, result)

    def _validate_dir_structure(self, addon_dir):
        main_addon_path, deps_paths = self._get_addon_and_deps_path(addon_dir)
        invalid_bundle_version_paths = []

        # validate main addon subdirs
        if main_addon_path.exists() and main_addon_path.is_dir():
            invalid_main_bundles = [
                bundle
                for bundle in get_subdirs(main_addon_path)
                if not self._version_parsable(bundle)
            ]
            invalid_bundle_version_paths.extend(invalid_main_bundles)
        else:
            return (
                "Main addon directory not present for the addon:"
                f" {addon_dir.name}"
            )

        # Validate the dependency addon subdirs
        for dep_addon_path in deps_paths:
            invalid_dep_bundles = [
                bundle
                for bundle in get_subdirs(dep_addon_path)
                if not self._version_parsable(bundle)
            ]
            invalid_bundle_version_paths.extend(invalid_dep_bundles)

        # Convert paths to strings
        invalid_bundle_version_paths = list(
            map(str, invalid_bundle_version_paths)
        )
        if invalid_bundle_version_paths:
            err_prefix = (
                "Unable to parse the version number in the followingbundles: \n"
            )
            err_msg = err_prefix + "\n".join(invalid_bundle_version_paths)
            return err_msg

        return ""

    @staticmethod
    def _get_addon_and_deps_path(addon):
        main_addon_path = addon.joinpath("main")
        # Everything in the addon directory except the main addon
        # is considered as a "dependent" addon.
        deps_paths = (
            path
            for path in get_subdirs(addon)
            if str(path) != str(main_addon_path)
        )
        return (main_addon_path, deps_paths)

    @staticmethod
    def _version_parsable(path_name):
        try:
            semver.VersionInfo.parse(path_name.name)
            return True
        except ValueError:
            return False

    @staticmethod
    def _is_main_addon(inner_addon):
        return inner_addon.name == "main"

    @staticmethod
    def _operator_sdk_validate(bundle_path):
        cmd = [
            "bundle",
            "validate",
            str(bundle_path),
        ]
        try:
            OPERATOR_SDK.run(*cmd)
            return True
        except subprocess.CalledProcessError:
            return False
