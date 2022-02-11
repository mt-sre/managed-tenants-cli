import logging
import os
import sys
from pathlib import Path

import urllib3
import yaml
from gitlab.exceptions import GitlabError
from sretoolbox.utils.logger import get_text_logger

from managedtenants.bundles.addon_bundles import AddonBundles
from managedtenants.bundles.bundle_builder import BundleBuilder
from managedtenants.bundles.docker_api import DockerAPI
from managedtenants.bundles.index_builder import IndexBuilder
from managedtenants.utils.git import ChangeDetector, get_short_hash
from managedtenants.utils.gitlab_client import GitLab
from managedtenants.utils.quay_api import QuayAPI

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

GITLAB_URL = os.environ.get("GITLAB_SERVER")
GITLAB_TOKEN = os.environ.get("GITLAB_TOKEN")
GITLAB_PROJECT = os.environ.get("GITLAB_PROJECT")
DOCKER_CONF = os.environ.get("DOCKER_CONF")
LOG = get_text_logger("app")


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


# TODO: remove this function once flow has been verified with condition on L688
# pylint: disable=R1710
def post_managed_tenants_mr_metadata(
    dry_run,
    addon,
    addon_env,
    version,
    index_image,
):
    """
    TODO
    :param dry_run:
    :param addon:
    :param addon_env:
    :param version:
    :param index_image:
    :return:
    """

    if dry_run:
        return None

    gl = GitLab(url=GITLAB_URL, token=GITLAB_TOKEN, project=GITLAB_PROJECT)
    version_name = f"{addon.name}-{version}"

    addon_metadata_path = f"addons/{addon.name}/metadata/{addon_env}/addon.yaml"

    if gl.mr_exists(title=version_name):
        LOG.info("MR with the same name already exists. Aborting MR creation.")
        return None

    main_branch = "main"
    branch = f"{addon.name}-{get_short_hash()}"
    LOG.info("Creating branch %s", branch)

    gl.create_branch(new_branch=branch, source_branch=main_branch)

    try:
        raw_file = gl.project.files.get(
            file_path=addon_metadata_path, ref=main_branch
        )
    except GitlabError:
        exit_with_error(
            f"File {addon_metadata_path} does not exist in the managed-tenants"
            " repository. Please create it."
        )

    addon_metadata = yaml.load(raw_file.decode(), Loader=yaml.CSafeLoader)

    addon_metadata["indexImage"] = index_image.url_digest

    content_metadata = yaml.dump(addon_metadata, Dumper=yaml.CSafeDumper)

    commit_message = f"Updating metadata for {version_name}:{addon_env}"
    gl.update_file(
        branch_name=branch,
        file_path=addon_metadata_path,
        commit_message=commit_message,
        content=content_metadata,
    )

    if not gl.project.repository_compare(from_=main_branch, to=branch)["diffs"]:
        gl.delete_branch(branch=branch)
        LOG.info(
            "No changes when compared to %s. Aborting MR creation.", main_branch
        )
        return None

    gitlab_data = {
        "source_branch": branch,
        "target_branch": main_branch,
        "title": version_name,
        "remove_source_branch": True,
        "labels": [],
    }

    LOG.info("Posting MR to Managed Tenants")
    if not dry_run:
        return gl.project.mergerequests.create(gitlab_data)


# pylint: disable=R1710
def post_managed_tenants_mr(
    dry_run,
    addon,
    addon_env,
    version,
    index_image,
):
    """
    TODO
    :param dry_run:
    :param addon:
    :param addon_env:
    :param version:
    :param index_image:
    :return:
    """

    if dry_run:
        return None

    gl = GitLab(url=GITLAB_URL, token=GITLAB_TOKEN, project=GITLAB_PROJECT)
    version_name = f"{addon.name}-{version}"
    addon_version = f"{addon.name}.v{version}"

    addon_image_set = {
        "name": addon_version,
        "indexImage": index_image.url_digest,
        "relatedImages": [],
    }

    config_path = f"addons/{addon.name}/main/config.yaml"

    try:
        with open(config_path, "r", encoding="utf-8") as stream:
            try:
                config = yaml.safe_load(stream)
                ocm_config = config.get("ocm", {})

                # Populate OCM data in ImageSet
                for key in ocm_config:

                    # Ensure that we're not allowing any other keys
                    if key in [
                        "addOnParameters",
                        "subOperators",
                        "addOnRequirements",
                    ]:
                        val = ocm_config.get(key, {})
                        if val:
                            addon_image_set[key] = val

            except IOError as e:
                LOG.error(f"failed to read config file for {addon.name}: {e}")
    except FileNotFoundError as e:
        LOG.info(f"No config file present: {e}")

    addon_image_sets_path = (
        f"addons/{addon.name}/addonimagesets/{addon_env}/{addon_version}.yaml"
    )

    if gl.mr_exists(title=version_name):
        LOG.info("MR with the same name already exists. Aborting MR creation.")
        return None

    main_branch = "main"
    branch = f"{addon.name}-{get_short_hash()}"
    LOG.info("Creating branch %s", branch)

    gl.create_branch(new_branch=branch, source_branch=main_branch)

    image_set_content = yaml.dump(addon_image_set, Dumper=yaml.CSafeDumper)

    # Check if ImageSet file does not already exist
    if not gl.file_exists(
        file_path=addon_image_sets_path, target_branch=main_branch
    ):
        commit_message = f"Creating AddonImageSet for {addon.name}"
        gl.create_file(
            branch_name=branch,
            file_path=addon_image_sets_path,
            commit_message=commit_message,
            content=image_set_content,
        )
    else:
        commit_message = f"Updating AddonImageSet for {addon.name}"
        gl.update_file(
            branch_name=branch,
            file_path=addon_image_sets_path,
            commit_message=commit_message,
            content=image_set_content,
        )

    if not gl.project.repository_compare(from_=main_branch, to=branch)["diffs"]:
        gl.delete_branch(branch=branch)
        LOG.info(
            "No changes when compared to %s. Aborting MR creation.", main_branch
        )
        return None

    gitlab_data = {
        "source_branch": branch,
        "target_branch": main_branch,
        "title": version_name,
        "remove_source_branch": True,
        "labels": [],
    }

    LOG.info("Posting MR to Managed Tenants")
    if not dry_run:
        return gl.project.mergerequests.create(gitlab_data)


def exit_with_error(msg):
    LOG.error(msg)
    sys.exit(1)


def get_addon_environments(addon):
    """
    Returns a list of all environments that the managed-tenants
    metadata PRs must be made to.

    :param addon:
    :return:
    """
    path = f"addons/{addon.name}/main/config.yaml"
    try:
        with open(path, "r", encoding="utf-8") as addon_config:
            config = yaml.safe_load(addon_config)
            environments = config.get("environments", ["stage"])
            for environment in environments:
                if environment == "production":
                    exit_with_error(
                        "Pull Requests can not be raised by CI to managed"
                        " tenants production metadata"
                    )
                if environment not in ["stage", "integration"]:
                    exit_with_error(
                        "Invalid environment specified in config file. Valid"
                        " values are stage or integration"
                    )
    except IOError:
        LOG.info(
            f"No valid config file found for {addon.name}. Defaulting to"
            " 'stage'"
        )
        environments = ["stage"]
    return environments


class MtbundlesCLI:
    def __init__(self, args):
        self.args = args
        self.addons_dir = Path(args.addons_dir)
        self.quay_org = args.quay_org
        self.docker_api = self._docker_api()
        self.bundle_builder = self._bundle_builder()
        self.index_builder = self._index_builder()
        self.log = get_text_logger(
            "mtbundles",
            level=logging.DEBUG if args.debug else logging.INFO,
        )

    def run(self):
        target_addons = self._get_target_addons()

        for addon_dir in target_addons:
            addon_bundles = AddonBundles(addon_dir)
            bundles = addon_bundles.get_all_bundles()

            self.bundle_builder.build_and_push_all(bundles, get_short_hash())
            index_image = self.index_builder.build_and_push(
                bundles, get_short_hash()
            )

            if not self.args.dry_run:
                latest_version = addon_bundles.get_latest_version()
                environments = get_addon_environments(addon_dir)
                for env in environments:
                    if addon_dir.name == "reference-addon":
                        post_managed_tenants_mr(
                            dry_run=self.args.dry_run,
                            addon=addon_dir,
                            addon_env=env,
                            version=latest_version,
                            index_image=index_image,
                        )
                    else:
                        post_managed_tenants_mr_metadata(
                            dry_run=self.args.dry_run,
                            addon=addon_dir,
                            addon_env=env,
                            version=latest_version,
                            index_image=index_image,
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
                exit_with_error(
                    f"Invalid addon name provided: {self.args.addon_name}."
                )
            self.log.info(f"Targeting single addon {addon.name}...")
            return [addon]

        # TODO: (sblaisdo) deprecate the changed_addons workflow once the
        # tooling is more stable, and supports concurrently building+deploying
        # index/bundle images.
        if self.args.only_changed:
            self.log.info("Targeting changed addons as reported by git...")
            return ChangeDetector(
                addons_dir=self.addons_dir, dry_run=self.args.dry_run
            ).get_changed_addons()

        self.log.info(f"Targeting all addons in {self.addons_dir}.")
        return list(self.addons_dir.iterdir())

    def _docker_api(self):
        return DockerAPI(
            quay_api=QuayAPI(org=self.args.quay_org),
            dockercfg_path=DOCKER_CONF,
            debug=self.args.debug,
            force_push=self.args.force_push,
        )

    def _bundle_builder(self):
        return BundleBuilder(
            docker_api=self.docker_api,
            dry_run=self.args.dry_run,
            debug=self.args.debug,
        )

    def _index_builder(self):
        return IndexBuilder(
            docker_api=self.docker_api,
            dry_run=self.args.dry_run,
            debug=self.args.debug,
        )
