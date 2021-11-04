from managedtenants.core.addons_loader.addon import Addon
from managedtenants.utils.git import ChangeDetector


def instantiate_addon(args):
    return Addon(path=args[0], environment=args[1])


def load_addons(path, environment, addon_name, args):
    addons_to_load = []

    for candidate in get_candidates(path, args):
        if addon_name is not None:
            if candidate.name != addon_name:
                continue
        envs_path = candidate / "metadata"
        for env_path in sorted(envs_path.iterdir()):
            # Filtering out the other environments
            if env_path.name != environment:
                continue
            addons_to_load.append((candidate, environment))

    if not addons_to_load:
        return []

    # force list to not lazily evaluate the returned iterator of map()
    return list(map(instantiate_addon, addons_to_load))


def get_candidates(path, args):
    """
    Filter potential addon candidates to be loaded or acted upon.
    """
    if args.only_changed:
        cd = ChangeDetector(addons_dir=path, dry_run=args.dry_run)
        return sorted(cd.get_changed_addons())

    return sorted(path.iterdir())
