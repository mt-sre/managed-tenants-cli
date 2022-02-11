#!/usr/bin/env python
import logging
import re
import subprocess
from pathlib import Path

import semver
from sretoolbox.container import Image
from sretoolbox.utils.logger import get_text_logger

from managedtenants.bundles.binary_deps import OPERATOR_SDK
from managedtenants.bundles.docker_api import DockerAPI
from managedtenants.bundles.exceptions import BundleBuilderError
from managedtenants.bundles.utils import get_subdirs, load_yaml


class BundleBuilder:
    """
    Build and push bundle images.

    :param addon_dir: Path to the addon bundle.
    :param docker_api: DockerAPI object to be used to build and push.
    :param dry_run: If True, skips pushing images.
    :param debug: Enable debug logging.
    """

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
            "managedtenants-bundle-builder",
            level=logging.DEBUG if debug else logging.INFO,
        )
        self._validate_dir_structure()

    def build_push_bundle_images_with_deps(
        self,
        versions,
        hash_string,
    ):
        """
        Builds and pushes bundle images in the given addon directory.

        :param versions: A list versions to consider
        :param hash_string: A string to be used in the created image tag.

        :return: A list of pushed bundle images
        """
        all_inner_addons = get_subdirs(path=self.addon_dir)
        addon_images = []
        for inner_addon in all_inner_addons:
            addon_images.extend(
                self._build_push_bundle_images(
                    addon=inner_addon,
                    versions=versions,
                    hash_string=hash_string,
                )
            )
        return addon_images

    def _build_push_bundle_images(
        self,
        addon,
        hash_string,
        versions=None,
    ):
        """
        :param addon: A Posix directory path
        :param versions: A list versions to consider
        :param hash_string: A string to be used in the created image tag.

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
                self.log.info(
                    f"skipping version {bundle.name} for main operator"
                )
                continue
            bundle_image = self._build_push_bundle_image(
                bundle=bundle,
                hash_string=hash_string,
                addon_name=addon_name,
            )
            images.append(bundle_image)
        return images

    def _build_push_bundle_image(
        self,
        bundle,
        addon_name,
        hash_string,
    ):
        registry = self.docker_api.registry
        repo_name = f"{addon_name}-bundle"
        image = Image(f"{registry}/{repo_name}:{bundle.name}-{hash_string}")

        self.log.info(f'Building bundle image "{image.url_tag}".')
        _ = self.docker_api.build_bundle(path=bundle, tag=image.url_tag)

        # don't push images on dry_run
        if not self.dry_run:
            self.log.info(f'Pushing bundle image "{image.url_tag}".')
            self.docker_api.push(image)

        return image

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
        return max(
            [item.name for item in get_subdirs(main_addon_path)],
            key=semver.VersionInfo.parse,
        )

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

    def _validate_dir_structure(self):
        """
        Validates dir structure for self.addon_dir.

        :raises BundleBuilderError:
        """
        main_addon_path, deps_paths = self._get_addon_and_deps_path()
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
            raise BundleBuilderError(
                "Main addon directory not present for the addon:"
                f" {self.addon_dir.name}"
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
            raise BundleBuilderError(
                err_prefix + "\n".join(invalid_bundle_version_paths)
            )

    def _get_addon_and_deps_path(self):
        main_addon_path = self.addon_dir.joinpath("main")
        # Everything in the addon directory except the main addon
        # is considered as a "dependent" addon.
        deps_paths = (
            path
            for path in get_subdirs(self.addon_dir)
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
        except subprocess.CalledProcessError as e:
            raise BundleBuilderError(
                f"Failed to validate bundle path '{bundle_path}', got"
                f" {e.stdout.decode()}."
            )
