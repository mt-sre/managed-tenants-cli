import argparse
import logging
import sys
from pathlib import Path

from sretoolbox.utils.logger import get_text_logger

from managedtenants import PostTask, PreTask, Task
from managedtenants.bundles.ci import MtbundlesCLI
from managedtenants.core import runner
from managedtenants.core.addons_loader import load_addons
from managedtenants.core.addons_loader.exceptions import AddonsLoaderError
from managedtenants.core.status import Status
from managedtenants.core.tasks_loader import load_tasks
from managedtenants.core.version import VERSION
from managedtenants.data.environments import ENVIRONMENTS

APP_LOG = get_text_logger("name")


class Cli:
    def __init__(self):
        parser = argparse.ArgumentParser(prog="managedtenants")

        parser.add_argument(
            "-v",
            "--version",
            action="version",
            version=f"managedtenants v{VERSION}",
        )
        parser.add_argument(
            "--environment",
            choices=ENVIRONMENTS,
            default="stage",
            help="Target environment",
        )
        parser.add_argument(
            "--addon-name", default=None, help="Load only a given addon"
        )
        parser.add_argument(
            "--addons-dir",
            type=self._validate_addons_dir,
            required=True,
            help='[path] "path" for the addons directory',
        )
        parser.add_argument(
            "--ocm-api", help="Override the environments OCM API"
        )
        parser.add_argument(
            "--ocm-api-insecure",
            action="store_true",
            default=False,
            help="Allow Insecure connection to OCM API",
        )
        parser.add_argument(
            "--only-changed",
            action="store_true",
            default=False,
            help=(
                "Modifies the addons_loader to only consider addons with"
                " changed files"
            ),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Flag to specify a non-invasive execution",
        )
        parser.add_argument(
            "--debug",
            action="store_true",
            default=False,
            help="Enable the debug messages",
        )

        subcommands = parser.add_subparsers(
            title="subcommands", help="subcommand help", dest="subcommand"
        )

        subcommands.add_parser("load", help="Loads the addons inventory")

        run_parser = subcommands.add_parser("run", help="Runs the tasks")
        run_parser.add_argument(
            "tasks_reference",
            type=self._validate_tasks_reference,
            help=(
                '[path:search] "path" for the directory '
                'or file and "search" string to filter '
                "tasks"
            ),
        )

        bundles_parser = subcommands.add_parser(
            "bundles", help="Build addon bundles"
        )
        bundles_parser.add_argument(
            "--quay-org",
            default="osd-addons",
            help="Quay org to push images to.",
        )
        bundles_parser.add_argument(
            "--force-push",
            action="store_true",
            default=False,
            help="Force push an existing image.",
        )

        self.args = parser.parse_args()

        self.search = None
        self.tasks_path = None

        self.status = Status.ALL_OK

    @staticmethod
    def _validate_addons_dir(value):
        addons_path = Path(value)
        if addons_path.is_dir():
            return value
        raise argparse.ArgumentTypeError(
            f"The addons dir path: {addons_path} is invalid. Please provide a"
            " valid addons_dir using '--addons-dir'."
        )

    @staticmethod
    def _validate_tasks_reference(value):
        if ":" in value:
            path = value.split(":", 1)[0]
        else:
            path = value
        tasks_path = Path(path)
        if tasks_path.is_dir() or tasks_path.is_file():
            return value
        raise argparse.ArgumentTypeError(f"not found: {path}")

    def run(self):
        if self.args.subcommand == "load":
            self._load_addons()

        elif self.args.subcommand == "run":
            if ":" in self.args.tasks_reference:
                path, self.search = self.args.tasks_reference.split(":", 1)
            else:
                path = self.args.tasks_reference
            self.tasks_path = Path(path)

            # init task logger /w appropriate log_level
            log_level = logging.INFO if self.args.debug else logging.WARN
            _ = get_text_logger(name="task", level=log_level)
            self._run()

        elif self.args.subcommand == "bundles":
            self._build_bundles()

    def _load_addons(self):
        addons_path = Path(self.args.addons_dir)
        addon_name = self.args.addon_name
        try:
            APP_LOG.info("Loading %s...", self.args.environment)
            addons_factory = load_addons(
                path=addons_path,
                environment=self.args.environment,
                addon_name=addon_name,
                args=self.args,
            )
            APP_LOG.info("Loading %s OK", self.args.environment)
            return addons_factory
        except AddonsLoaderError as details:
            APP_LOG.error("[%s] %s", type(details).__name__, details)
            self.status |= Status.ADDONS_LOAD_ERROR
        except Exception:  # pylint: disable=broad-except
            APP_LOG.exception("[ERROR]")
            self.status |= Status.ADDONS_LOAD_ERROR
        sys.exit(self.status)

    def _run(self):
        addons_factory = self._load_addons()
        tasks_factory = load_tasks(
            addons_factory=addons_factory,
            args=self.args,
            tasks_path=self.tasks_path,
            task_type=PreTask,
            search=self.search,
        )
        if tasks_factory:
            APP_LOG.info("== PRETASKS ".ljust(80, "="))
            runner.run(tasks_factory=tasks_factory)

        tasks_factory = load_tasks(
            addons_factory=addons_factory,
            args=self.args,
            tasks_path=self.tasks_path,
            task_type=Task,
            search=self.search,
        )
        if tasks_factory:
            APP_LOG.info("== TASKS ".ljust(80, "="))
            runner.run(tasks_factory=tasks_factory)

        tasks_factory = load_tasks(
            addons_factory=addons_factory,
            args=self.args,
            tasks_path=self.tasks_path,
            task_type=PostTask,
            search=self.search,
        )
        if tasks_factory:
            APP_LOG.info("== POSTTASKS ".ljust(80, "="))
            runner.run(tasks_factory=tasks_factory)

    def _build_bundles(self):
        cli = MtbundlesCLI(args=self.args)
        cli.run()


def main():
    cli = Cli()
    cli.run()


if __name__ == "__main__":
    main()
