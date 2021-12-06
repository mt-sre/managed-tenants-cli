import subprocess

import semver


def parse_version_from_imageset_name(name):
    """Returns the image version from the name.
    Ex: mock-operator.v1.0.0 -> 1.0.0"""
    version_str = name.split(".v")[-1]
    try:
        result = semver.VersionInfo.parse(version_str)
        return result
    except ValueError:
        return None


def run(cmd, logger=None):
    """
    Calls subprocess.run with select options.
    """
    if logger:
        logger.info("Running %s", cmd)
    return subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False
    )
