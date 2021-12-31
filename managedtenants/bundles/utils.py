import subprocess

import semver
import yaml

from managedtenants.bundles.exceptions import BundleBuilderError
from managedtenants.utils.general_utils import parse_version_from_imageset_name


def run(cmd, logger=None):
    """
    Calls subprocess.run with select options.
    """
    if logger:
        logger.info("Running %s", cmd)
    return subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False
    )


def get_subdirs(path):
    """
    Returns all the sub-directories under `path`.
    """
    return (item for item in path.iterdir() if item.is_dir())


def push_image(dry_run, image, logger=None, docker_conf_path=None):
    # return early if we are in dry-run mode
    if dry_run:
        return image

    size = check_image_size(image.url_tag)
    if (size is None) and logger:
        logger.error("Failed to check the image size!")

    if size == 0:
        raise BundleBuilderError("Received a zero byte image!")
    if logger:
        logger.info('Pushing image "%s"', image.url_tag)

    cmd = ["docker"]

    if docker_conf_path is not None:
        cmd.extend(["--config", docker_conf_path])

    cmd.extend(
        [
            "push",
            image.url_tag,
        ]
    )

    result = run(cmd=cmd, logger=logger)
    if result.returncode:
        if logger:
            logger.error(result.stdout.decode())

    return image


def check_image_size(image_url_tag):
    cmd = ["docker", "image", "inspect", image_url_tag, "--format='{{.Size}}'"]
    result = run(cmd=cmd)
    if not result.returncode:
        return int(result.stdout.decode().strip("'\n"))
    return None


def load_yaml(path):
    try:
        with open(path, "r", encoding="utf8") as file_obj:
            data = yaml.load(file_obj.read(), Loader=yaml.SafeLoader)
            return data
    except yaml.YAMLError:
        return None


def parse_version(version_str):
    """Returns the image version from the name.
    Ex: mock-operator.v1.0.0 -> 1.0.0"""
    try:
        result = semver.VersionInfo.parse(version_str)
        return result
    except ValueError:
        return None


def present(items, store):
    return all(bool(store.get(item)) for item in items)


def csvs_older(older_versions, current):
    current_version = parse_version_from_imageset_name(
        current["metadata"]["name"]
    )
    older_versions = list(map(parse_version_from_imageset_name, older_versions))
    return all(version < current_version for version in older_versions)
