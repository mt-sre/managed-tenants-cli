import logging
import sys

from managedtenants.core import tasks_loader
from managedtenants.core.status import Status

APP_LOG = logging.getLogger("app")


def run(tasks_factory):
    status = Status.ALL_OK

    for task in tasks_factory:
        try:
            APP_LOG.info("%s...", task.name)
            task.run()
            APP_LOG.info("%s OK", task.name)

        except tasks_loader.exceptions.TaskSkip as details:
            APP_LOG.warning("%s SKIP: %s", task.name, details)

        except tasks_loader.exceptions.TaskFail as details:
            APP_LOG.error("%s FAIL: %s", task.name, details)
            status |= Status.TASK_ERROR
            sys.exit(status)

        except AssertionError as details:
            APP_LOG.error("%s ASSERTION_ERROR: %s", task.name, details)
            status |= Status.ASSERTION_ERROR
            sys.exit(status)

        except Exception:  # pylint: disable=broad-except
            APP_LOG.exception("%s ERROR", task.name)
            status |= Status.TASK_ERROR
            sys.exit(status)
