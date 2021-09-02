class AddonsLoaderError(Exception):
    """
    Used when some error happens during the addons loading process.
    """


class AddonLoadError(AddonsLoaderError):
    pass


class BundleLoadError(AddonsLoaderError):
    pass


class ManifestLoadError(AddonsLoaderError):
    pass


class SssLoadError(AddonsLoaderError):
    pass
