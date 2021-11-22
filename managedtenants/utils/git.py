import os
from pathlib import Path

from sretoolbox.utils.logger import get_text_logger

from managedtenants.utils.general_utils import run


class ChangeDetector:
    def __init__(self, addons_dir, dry_run=True):
        self.dry_run = dry_run
        self.addons_dir = addons_dir
        self.log = get_text_logger("app")

    def get_changed_addons(self):
        """
        Get the list of all changed addons.
        """
        addons_dir = Path(self.addons_dir).resolve()
        all_addons = set(addons_dir.iterdir())
        changed_files = self._get_changed_files()
        return self._intersect(parents=all_addons, children=changed_files)

    @staticmethod
    def _intersect(parents, children):
        """
        Abstraction to find all parents that have at least a child path listed
        in children.

        :param parents: set of parent directories
        :param children: set of child paths
        """
        res = set()
        for child in children:
            match = set(child.parents).intersection(parents)

            # If match is already in res this is a no-op
            res.update(match)

        return res

    def _get_changed_files(self):
        """
        Detect changed files within managed-tenants and managed-tenants-bundles.

        Remote name has to be origin and principal branch called main, which is
        the case for both repositories.
        """
        if self.dry_run:
            # pr_check
            commit_range = "remotes/origin/main...HEAD"
        else:
            # build_deploy
            # From https://plugins.jenkins.io/git/
            git_previous_commit = os.environ["GIT_PREVIOUS_COMMIT"]
            git_commit = os.environ["GIT_COMMIT"]
            commit_range = f"{git_previous_commit}...{git_commit}"

        changed_files = set()
        cmd = [
            "git",
            "diff",
            "--name-only",
            f"{commit_range}",
        ]
        result = run(cmd, self.log).stdout.decode().strip()
        for diff in result.splitlines():
            changed_files.add(Path(diff).resolve())
        return changed_files


def get_short_hash(size=7):
    """
    TODO
    :param size:
    :return:
    """
    cmd = ["git", "rev-parse", f"--short={size}", "HEAD"]
    return run(cmd=cmd).stdout.decode().strip()
