import argparse

from managedtenants.data.environments import ENVIRONMENTS
from managedtenants.data.paths import ADDONS_DIR
from tests.testutils.paths import CHECK_TASKS_DIR


def default_cli_args(env, **kwargs):
    if env not in ENVIRONMENTS.keys():
        raise TypeError(
            f"Invalid environent {env}. Must be one of"
            f" {list(ENVIRONMENTS.keys())}"
        )
    defaults = {
        "addon_name": None,
        "addons_dir": ADDONS_DIR,
        "dry_run": False,
        "debug": False,
        "environment": env,
        "ocm_api": ENVIRONMENTS[env]["ocm_api"],
        "ocm_api_insecure": False,
        "task_reference": CHECK_TASKS_DIR,
    }
    # Override with custom args provided
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)
