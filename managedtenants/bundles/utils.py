import subprocess

import yaml

from managedtenants.bundles.exceptions import BundleBuilderError


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
