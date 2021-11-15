
from managedtenants.utils.quay_api import QuayApi
import subprocess


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


def quay_repo_exists(dry_run, org, repo_name, quay_token):
    """
    Checks if the required quay repository exists.
    :return: true if repo exists
    :rtype: bool
    """
    if dry_run:
        return True
    quay_api = QuayApi(organization=org, token=quay_token)
    return quay_api.repo_exists(repo_name)


def push_image(dry_run, image, logger=None, docker_conf_path=None):
    # return early if we are in dry-run mode
    if dry_run:
        return image

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
