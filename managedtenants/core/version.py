import pkg_resources

try:
    VERSION = pkg_resources.get_distribution("managedtenants_cli").version
except pkg_resources.DistributionNotFound:
    VERSION = "unknown.unknown"
