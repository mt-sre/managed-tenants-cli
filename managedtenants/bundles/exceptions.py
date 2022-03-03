class BundleBuilderError(Exception):
    pass


class IndexBuilderError(Exception):
    pass


class DockerError(Exception):
    pass


class AddonBundlesError(Exception):
    pass


class BundleError(Exception):
    pass


class CSVError(Exception):
    pass


class ImageSetError(Exception):
    pass


class ImageSetCreatorError(Exception):
    pass


class MtbundlesCLIError(Exception):
    pass


class QuayAPIError(Exception):
    """Used when there are errors with the Quay API."""

    def __init__(self, message, response):
        super().__init__(message)
        self.response = response
