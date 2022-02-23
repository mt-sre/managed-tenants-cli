import logging

import yaml
from gitlab.exceptions import GitlabCreateError, GitlabError
from sretoolbox.utils.logger import get_text_logger

from managedtenants.bundles.exceptions import ImageSetCreatorError
from managedtenants.bundles.utils import read_env_or_fail
from managedtenants.utils.gitlab_client import GitLab


class ImageSetCreator:
    """
    Open merge requests to managed-tenants for imagesets.

    Also supports legacy index_image only addons.

    :param main_branch: Override target main branch. Default 'main'.
    :param debug: Enable verbose logging.
    """

    def __init__(self, main_branch="main", debug=False):
        self.main_branch = main_branch
        self.log = get_text_logger(
            "managedtenants-mr-poster",
            level=logging.DEBUG if debug else logging.INFO,
        )
        self.gl = self._init_gitlab_client()

    def _init_gitlab_client(self):
        try:
            return GitLab(
                url=read_env_or_fail("GITLAB_SERVER"),
                token=read_env_or_fail("GITLAB_TOKEN"),
                project=read_env_or_fail("GITLAB_PROJECT"),
            )
        except ValueError as e:
            self.log.error(e)
            raise ImageSetCreatorError(e)

    def create(self, addon_bundles, index_image, with_imagesets=False):
        """
        Post a merge request to managed-tenants for all addons and all envs
        found in the config.yaml file.

        :param addon_bundles: AddonBundles for addon.
        :param index_image: Built and Pushed index_image for addon.
        :param with_imagesets: Enable/Disable imageset feature.
        """
        new_branch = addon_bundles.get_unique_name()
        if self.gl.mr_exists(title=new_branch):
            self.log.info(
                f"Merge request {new_branch} already exists for"
                f" {addon_bundles}. Skipping."
            )
            return

        self._ensure_branch(new_branch)

        if with_imagesets:
            imagesets = addon_bundles.get_all_imagesets(index_image)
            self._update_imagesets(new_branch, imagesets)
        else:
            metadata_paths = addon_bundles.get_all_metadata_paths()
            self._update_index_image(new_branch, metadata_paths, index_image)

        self.log.info(f"Posting merge request {new_branch} to managed-tenants.")
        self._post_mr(new_branch)

    def _ensure_branch(self, new_branch):
        # Make branch creation more reliable because when an MR is closed, the
        # underlying branch is not automatically deleted.
        try:
            self.log.info(
                f"Ensuring git branch {new_branch} in managed-tenants."
            )
            self.gl.create_branch(
                new_branch=new_branch, source_branch=self.main_branch
            )
        except GitlabCreateError:
            self.log.info(f"Branch {new_branch} already exists, deleting.")
            self.gl.delete_branch(new_branch)
            self.gl.create_branch(
                new_branch=new_branch, source_branch=self.main_branch
            )

    def _update_imagesets(self, new_branch, imagesets):
        for imageset in imagesets:
            self.log.info(f"Adding {imageset} to {new_branch}.")
            if not self.gl.file_exists(
                file_path=imageset.path, target_branch=self.main_branch
            ):
                self.gl.create_file(
                    branch_name=new_branch,
                    file_path=imageset.path,
                    commit_message=(
                        f"Creating {imageset.name} for {imageset.env}."
                    ),
                    content=imageset.to_yaml(),
                )
            else:
                self.gl.update_file(
                    branch_name=new_branch,
                    file_path=imageset.path,
                    commit_message=(
                        f"Updating {imageset.name} for {imageset.env}"
                    ),
                    content=imageset.to_yaml(),
                )

    def _update_index_image(self, new_branch, metadata_paths, index_image):
        for path in metadata_paths:
            try:
                f = self.gl.project.files.get(
                    file_path=path, ref=self.main_branch
                )
                metadata = yaml.load(f.decode(), Loader=yaml.CSafeLoader)
                metadata["indexImage"] = index_image.url_digest

                self.gl.update_file(
                    branch_name=new_branch,
                    file_path=path,
                    commit_message=f"Updating index_image in {path}.",
                    content=yaml.dump(metadata, Dumper=yaml.CSafeDumper),
                )

            except GitlabError as e:
                err_msg = f"{path} does not exist in managed-tenants repo: {e}"
                self.log.error(err_msg)
                raise ImageSetCreatorError(err_msg)

            except yaml.YAMLError as e:
                err_msg = f"error reading or writing to {path}: {e}."
                self.log.error(err_msg)
                raise ImageSetCreatorError(err_msg)

    def _post_mr(self, new_branch):
        if not self.gl.project.repository_compare(
            from_=self.main_branch, to=new_branch
        )["diffs"]:
            self.log.info(
                f"Empty diff when comparing {self.main_branch} and"
                f" {new_branch}. Aborting MR creation."
            )
            self.gl.delete_branch(branch=new_branch)

        self.gl.project.mergerequests.create(
            {
                "source_branch": new_branch,
                "target_branch": self.main_branch,
                "title": new_branch,
                "remove_source_branch": True,
                "labels": [],
            }
        )
