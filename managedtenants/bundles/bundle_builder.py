#!/usr/bin/env python
import logging

from sretoolbox.container import Image
from sretoolbox.utils.logger import get_text_logger

from managedtenants.bundles.docker_api import DockerAPI
from managedtenants.bundles.exceptions import BundleBuilderError, DockerError
from managedtenants.utils.git import get_short_hash


class BundleBuilder:
    """
    Build and push bundle images.

    :param docker_api: DockerAPI object to be used to build and push.
    :param dry_run: If True, skips pushing images.
    :param debug: Enable debug logging.
    """

    def __init__(
        self,
        docker_api=None,
        dry_run=False,
        debug=False,
    ):

        self.dry_run = dry_run
        self.docker_api = (
            docker_api if docker_api is not None else DockerAPI(debug=debug)
        )
        self.log = get_text_logger(
            "managedtenants-bundle-builder",
            level=logging.DEBUG if debug else logging.INFO,
        )

    def build_and_push_all(self, bundles, hash_string=get_short_hash()):
        """
        Builds all the bundles. Also sets the bundle.image field.
        """
        self._build_all(bundles, hash_string)
        self._push_all(bundles)

    def _build_all(self, bundles, hash_string):
        try:
            for bundle in bundles:
                image = Image(
                    f"{self.docker_api.registry}/"
                    f"{bundle.bundle_repo_name()}:"
                    f"{bundle.version}-{hash_string}"
                )
                bundle.image = image

                self.log.info(f"Building {bundle}.")
                _ = self.docker_api.build_bundle(bundle)

        except DockerError as e:
            err_msg = f"failed to build {bundle}: {e}."
            self.log.error(err_msg)
            raise BundleBuilderError(err_msg)

    def _push_all(self, bundles):
        # don't push images on dry_run
        if self.dry_run:
            return

        try:
            # Optimization - only ensure repo once for an operator dir
            seen = set()
            for bundle in bundles:
                self.log.info(f"Pushing {bundle}.")
                repo = bundle.bundle_repo_name()
                self.docker_api.push(bundle.image, ensure_repo=repo not in seen)
                seen.add(repo)

        except DockerError as e:
            err_msg = f"failed to push {bundle}: {e}"
            self.log.error(err_msg)
            raise BundleBuilderError(err_msg)
