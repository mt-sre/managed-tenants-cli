import imp  # pylint: disable=deprecated-module
import inspect
import sys

from managedtenants.core.tasks_loader.post_task import PostTask
from managedtenants.core.tasks_loader.pre_task import PreTask


def discover_tasks(tasks):
    if tasks.is_file() and tasks.suffix == ".py":
        return [tasks]
    return sorted((item for item in tasks.iterdir() if item.suffix == ".py"))


def load_tasks(addons_factory, args, tasks_path, task_type, search):
    sys.path.insert(0, str(tasks_path))

    tasks_factory = []
    for task_file in discover_tasks(tasks_path):
        filename, filepath, fileinfo = imp.find_module(
            task_file.stem, [str(task_file.parent)]
        )
        task_module = imp.load_module(
            task_file.stem, filename, filepath, fileinfo
        )
        for _, obj in inspect.getmembers(task_module):
            if not inspect.isclass(obj):
                continue

            if obj.__name__ == task_type.__name__:
                continue

            if not issubclass(obj, task_type):
                continue

            if task_type in [PreTask, PostTask]:
                instance = obj(addons=addons_factory, args=args, path=task_file)
                if search is None:
                    tasks_factory.append(instance)
                else:
                    if search in instance.name:
                        tasks_factory.append(instance)
                continue

            for addon in addons_factory:
                instance = obj(
                    addons=addons_factory,
                    addon=addon,
                    args=args,
                    path=task_file,
                )
                if search is None:
                    tasks_factory.append(instance)
                else:
                    if search in instance.name:
                        tasks_factory.append(instance)

    if str(tasks_path) in sys.path:
        sys.path.remove(str(tasks_path))

    return tasks_factory
