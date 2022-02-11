import subprocess
from pathlib import Path

import semver
import yaml
from sretoolbox.binaries import OperatorSDK

from managedtenants.bundles.exceptions import BundleError

_OPERATOR_SDK = OperatorSDK(version="1.4.2", download_path="/tmp")


class Bundle:
    """
    Represent a bundle.

    :param addon_name: name of the addon owning the bundle
    :param path: path to bundle (e.g.: reference-addon/main/0.1.0/)
    :param operator_name: name of the operator owning the bundle
    :param version: bundle's semver
    :raise BundleError: if it is invalid.
    """

    # pylint: disable=too-many-arguments
    def __init__(self, addon_name, path, operator_name, version, image=None):
        self.addon_name = addon_name
        self.path = Path(path)
        self.operator_name = operator_name
        self.version = version
        self.annotations = self._parse_metadata_annotations()
        self.image = image
        self.validate()

    def validate(self):
        self._validate_semver()
        self._validate_operator_sdk()

    def is_main_bundle(self):
        """
        A bundle is a main bundle if it is part of the main addon operator.
        """
        return self.operator_name == self.addon_name

    def bundle_repo_name(self):
        if self.is_main_bundle():
            return f"{self.addon_name}-bundle"

        # Prepend dependency bundles /w addon_name to avoid quay collisions.
        return f"{self.addon_name}-{self.operator_name}-bundle"

    def index_repo_name(self):
        return f"{self.addon_name}-index"

    def _validate_semver(self):
        if not semver.VersionInfo.isvalid(self.version):
            raise BundleError(f"invalid semver for {self}")

    def _validate_operator_sdk(self):
        cmd = [
            "bundle",
            "validate",
            str(self.path),
        ]
        try:
            _OPERATOR_SDK.run(*cmd)
        except subprocess.CalledProcessError as e:
            raise BundleError(
                f"Failed to validate {self} with operator_sdk version"
                f" {_OPERATOR_SDK.version}: {e.stdout.decode()}."
            )

    def _parse_metadata_annotations(self):
        annotations_file = self.path / "metadata" / "annotations.yaml"
        with open(annotations_file, "r", encoding="utf-8") as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise BundleError(
                    f"{self}: failed to parse {annotations_file}, got {e}."
                )

        annotations = data.get("annotations", None)
        if annotations is None:
            raise BundleError(
                f"{self}: failed to extract annotations from"
                f" {annotations_file}."
            )

        # avoid unmarshaling ints, floats and bools
        return {k: str(v) for k, v in annotations.items()}

    def __str__(self):
        image = self.image.url_tag if self.image is not None else "unset"
        return (
            f"Bundle(addon_name={self.addon_name},"
            f" operator_name={self.operator_name}, version={self.version},"
            f" path={self.path},"
            f" image={image})"
        )
