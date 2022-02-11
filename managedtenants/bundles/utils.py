import subprocess

import yaml


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


def load_yaml(path):
    try:
        with open(path, "r", encoding="utf8") as file_obj:
            data = yaml.load(file_obj.read(), Loader=yaml.CSafeLoader)
            return data
    except yaml.YAMLError:
        return None
