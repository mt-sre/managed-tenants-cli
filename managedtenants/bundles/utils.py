import subprocess

from managedtenants.bundles.exceptions import BundleUtilsError
from managedtenants.utils.quay_api import QuayApi


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


def quay_repo_exists(dry_run, org_path, repo_name, quay_token):
    """
    Checks if the required quay repository exists.
    :return: true if repo exists
    :rtype: bool
    """
    if dry_run:
        return True
    org = quay_org_from_path(org_path)
    quay_api = QuayApi(organization=org, token=quay_token)
    return quay_api.repo_exists(repo_name)


def quay_repo_create(org, repo_name, quay_token):
    """
    Creates the passed repo under the passed org in quay.
    :return: true if repo exists
    :rtype: bool
    """
    quay_api = QuayApi(organization=org, token=quay_token)
    if quay_api.repo_exists(repo_name):
        return True
    return quay_api.repo_create(repo_name)


def push_image(dry_run, image, logger=None, docker_conf_path=None):
    # return early if we are in dry-run mode
    if dry_run:
        return image

    size = check_image_size(image.url_tag)
    if (size is None) and logger:
        logger.error("Failed to check the image size!")

    if size == 0:
        raise BundleUtilsError("Received a zero byte image!")
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


def quay_org_from_path(quay_org_path, base_path="quay.io/"):
    # "quay.io/osd-addons/" -> osd-addons
    # "quay.io/osd-addons" -> osd-addons
    split_res = quay_org_path.split(base_path)
    if split_res:
        return split_res[-1].strip("/")
    raise BundleUtilsError(
        f"Unable to parse:{quay_org_path}."
        "Tried extracting quay org from quay org path"
    )
