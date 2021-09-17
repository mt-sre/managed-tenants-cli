import logging
from abc import ABC, abstractmethod

from managedtenants.core.tasks_loader.environment import Environment
from managedtenants.core.tasks_loader.exceptions import TaskFail, TaskSkip


class Task(ABC):
    def __init__(self, addons, addon, args, path):
        self.addons = addons
        self.addon = addon

        self.environment = Environment(environment=args.environment, args=args)
        self.dry_run = args.dry_run

        self.path = path

        self.log = logging.getLogger("task")

    @abstractmethod
    def run(self):
        pass

    @property
    def name(self):
        return (
            f"{self.path}:"
            f"{self.__class__.__name__}:"
            f"{self.addon.name}:"
            f"{self.environment.name}"
        )

    @staticmethod
    def fail(message=""):
        raise TaskFail(message)

    @staticmethod
    def skip(message=""):
        raise TaskSkip(message)
