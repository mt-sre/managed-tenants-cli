import signal
import subprocess
from contextlib import contextmanager
from time import sleep

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


@contextmanager
def timeout(duration):
    def timeout_handler(sig, frame):
        raise TimeoutError(f"Timed out after {duration} seconds")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(duration)
    try:
        yield
    finally:
        signal.alarm(0)


def try_with_timeout_until(
    predicate_func, poll_interval=2, timeout_duration=15, max_tries=10
):
    """
    Invokes `predicate_func` until it returns true, in which case the
    function returns True.
    If predicate_func doesnt evaluate to true before `timeout_duration`,
    a TimeoutError exception is raised.
    The function also returns false after trying `max_tries` number of times.
    """
    with timeout(timeout_duration):
        for _ in range(0, max_tries):
            if predicate_func():
                return True
            sleep(poll_interval)
        return False
