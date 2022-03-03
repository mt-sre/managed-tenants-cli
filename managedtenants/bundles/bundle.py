import subprocess
from pathlib import Path

import semver
import yaml
from sretoolbox.binaries import OperatorSDK

from managedtenants.bundles.csv import CSV
from managedtenants.bundles.exceptions import BundleError, CSVError

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
    def __init__(
        self,
        addon_name,
        path,
        operator_name,
        version,
        image=None,
        single_bundle=False,
    ):
        self.addon_name = addon_name
        self.path = Path(path)
        self.operator_name = operator_name
        self.version = version
        self.image = image
        self.single_bundle = single_bundle
        self.annotations = self._parse_metadata_annotations()
        self.csv = self._parse_csv()
        self.validate()

    def _parse_metadata_annotations(self):
        annotations_file = self.path / "metadata" / "annotations.yaml"
        with open(annotations_file, "r", encoding="utf-8") as f:
            try:
                data = yaml.load(f, Loader=yaml.CSafeLoader)

            except FileNotFoundError as e:
                raise BundleError(f"{self}: {annotations_file} not found: {e}")

            except yaml.YAMLError as e:
                raise BundleError(
                    f"{self}: failed to parse {annotations_file}: {e}."
                )

        annotations = data.get("annotations", None)
        if annotations is None:
            raise BundleError(
                f"{self}: failed to extract annotations from"
                f" {annotations_file}."
            )

        # avoid unmarshaling ints, floats and bools
        return {k: str(v) for k, v in annotations.items()}

    def _parse_csv(self):
        try:
            return CSV(
                manifests_dir=self.path / "manifests",
                operator_name=self.operator_name,
            )
        except CSVError as e:
            raise BundleError(f"{self} failed to parse CSV: {e}.")

    def validate(self):
        self._validate_semver()
        self._validate_operator_sdk()

        if self.single_bundle:
            self._validate_single_bundle_pattern()

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

    def _validate_single_bundle_pattern(self):
        # 1. enforce the `olm.skipRange` annotation
        # expected value == '>=0.0.1 <{bundle_version}'
        skip_range = self.csv.get_olm_skip_range_annotation()
        if skip_range is None:
            raise BundleError(
                f"{self}: missing `olm.skipRange` annotation in CSV for."
            )

        expected = f">=0.0.1 <{self.version}"
        if skip_range.replace(" ", "") != expected.replace(" ", ""):
            raise BundleError(
                f"{self}: invalid format for `olm.skipRange`, expected"
                f" {expected} but got {skip_range}."
            )

        # 2. make sure `spec.replaces` and `spec.skips` are unset.
        # (single-bundle-per-operator pattern)
        if not self.csv.is_replaces_unset() or not self.csv.is_skips_unset():
            raise BundleError(
                f"{self}: please do not provide `spec.replaces` "
                " (single-bundle-per-operator pattern)."
            )

    def _is_main_bundle(self):
        """
        A bundle is a main bundle if it is part of the main addon operator.
        """
        return self.operator_name == self.addon_name

    def bundle_repo_name(self):
        if self._is_main_bundle():
            return f"{self.addon_name}-bundle"

        # Prepend dependency bundles /w addon_name to avoid quay collisions.
        return f"{self.addon_name}-{self.operator_name}-bundle"

    def index_repo_name(self):
        return f"{self.addon_name}-index"

    def __str__(self):
        image = self.image.url_tag if self.image is not None else "unset"
        return (
            f"Bundle(addon_name={self.addon_name},"
            f" operator_name={self.operator_name}, version={self.version},"
            f" path={self.path},"
            f" image={image})"
        )
