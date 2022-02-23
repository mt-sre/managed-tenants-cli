import os
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


def read_env_or_fail(env_var_name):
    res = os.environ.get(env_var_name)
    if res == "":
        raise ValueError(f"Please set {env_var_name} env var.")
    return res
