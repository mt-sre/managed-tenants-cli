from managedtenants.core.addons_loader.addon import Addon


def instantiate_addon(args):
    return Addon(path=args[0], environment=args[1])


def load_addons(path, environment, addon_name):
    addons_to_load = []
    for item in sorted(path.iterdir()):
        if addon_name is not None:
            if item.name != addon_name:
                continue
        envs_path = item / "metadata"
        for env_path in sorted(envs_path.iterdir()):
            # Filtering out the other environments
            if env_path.name != environment:
                continue
            addons_to_load.append((item, environment))

    if not addons_to_load:
        return []

    # force list to not lazily evaluate the returned iterator of map()
    return list(map(instantiate_addon, addons_to_load))
