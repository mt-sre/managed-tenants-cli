import logging
import os
from pathlib import Path

import urllib3
from sretoolbox.utils.logger import get_text_logger

from managedtenants.bundles.addon_bundles import AddonBundles
from managedtenants.bundles.bundle_builder import BundleBuilder
from managedtenants.bundles.docker_api import DockerAPI
from managedtenants.bundles.exceptions import MtbundlesCLIError
from managedtenants.bundles.imageset_creator import ImageSetCreator
from managedtenants.bundles.index_builder import IndexBuilder
from managedtenants.utils.git import ChangeDetector

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class MtbundlesCLI:
    def __init__(self, args):
        self.args = args
        self.addons_dir = Path(args.addons_dir)
        self.log = get_text_logger(
            "mtbundles",
            level=logging.DEBUG if args.debug else logging.INFO,
        )
        self.docker_api = self._init_docker_api()
        self.bundle_builder = self._init_bundle_builder()
        self.index_builder = self._init_index_builder()
        self.imageset_creator = self._init_imageset_creator()

    def run(self):
        target_addons = self._get_target_addons()
        n = len(target_addons)

        for i, addon_dir in enumerate(target_addons):
            self.log.info(
                f"==> Building bundles for {addon_dir.name} ({i+1}/{n})..."
            )
            addon_bundles = AddonBundles(
                addon_dir,
                debug=self.args.debug,
                single_bundle=self.args.single_bundle,
            )
            bundles = addon_bundles.get_all_bundles()

            self.bundle_builder.build_and_push_all(bundles)
            index_image = self.index_builder.build_and_push(bundles)

            if self.args.enable_gitlab:
                self.imageset_creator.create(
                    addon_bundles,
                    index_image,
                    # TODO: enable once flow is verified with condition L688
                    with_imagesets=addon_dir.name == "reference-addon",
                )

    def _get_target_addons(self):
        """
        Returns a list of targeted addons. 3 use cases:
            1. single addon
            2. all addons that have a changed file (using git diff)
            3. all addons
        """
        if self.args.addon_name is not None:
            addon = get_single_addon(self.addons_dir, self.args.addon_name)
            if not addon:
                err_msg = (
                    f"Invalid addon name provided: {self.args.addon_name}."
                )
                self.log.error(err_msg)
                raise MtbundlesCLIError(err_msg)
            self.log.info(f"Targeting single addon {addon.name}...")
            return [addon]

        # TODO: (sblaisdo) deprecate the changed_addons workflow?
        if self.args.only_changed:
            self.log.info("Targeting changed addons as reported by git...")
            return ChangeDetector(
                addons_dir=self.addons_dir, dry_run=self.args.dry_run
            ).get_changed_addons()

        self.log.info(f"Targeting all addons in {self.addons_dir}.")
        return list(self.addons_dir.iterdir())

    def _init_docker_api(self):
        return DockerAPI(
            registry=f"quay.io/{self.args.quay_org}",
            quay_org=self.args.quay_org,
            dockercfg_path=os.environ.get("DOCKER_CONF"),
            debug=self.args.debug,
            force_push=self.args.force_push,
        )

    def _init_bundle_builder(self):
        return BundleBuilder(
            docker_api=self.docker_api,
            dry_run=self.args.dry_run,
            debug=self.args.debug,
        )

    def _init_index_builder(self):
        return IndexBuilder(
            docker_api=self.docker_api,
            dry_run=self.args.dry_run,
            debug=self.args.debug,
        )

    def _init_imageset_creator(self):
        # Only initialize if --enable-gitlab flag is provided.
        # Requires GITLAB_TOKEN, GITLAB_SERVER and GITLAB_PROJECT env vars.
        return (
            ImageSetCreator(debug=self.args.debug)
            if self.args.enable_gitlab
            else None
        )


def get_single_addon(addons_dir, addon_name):
    """
    :param addon_name: Name of Addon
    :return: The changed addon path
    """
    target_addon = None
    for addon in addons_dir.iterdir():
        if addon.name == addon_name:
            target_addon = addon
            break
    return target_addon
