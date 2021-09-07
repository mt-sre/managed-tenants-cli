from copy import deepcopy
from string import ascii_letters, ascii_lowercase, digits, punctuation

from hypothesis import strategies as st
from hypothesis_jsonschema import from_schema
from managedtenants.core.addons_loader import Addon
from managedtenants.data.environments import ENVIRONMENTS
from managedtenants.utils.schema import load_addon_metadata_schema
from tests.testutils.paths import TEST_OPERATOR_PATH


def text(min_size=2, max_size=10, alphabet=None, **kwargs):
    """Returns printable characters."""
    default = ascii_letters + digits + punctuation + " "
    return st.text(
        min_size=min_size,
        max_size=max_size,
        alphabet=default if alphabet is None else alphabet,
        **kwargs,
    )


def k8s_name(**kwargs):
    """Returns a kubernetes friendly resource name."""
    return text(alphabet=ascii_letters + "-", **kwargs)


def namespace(**kwargs):
    """Namespace need to match '^redhat-.*$'."""

    def callback(ns):
        return f"redhat-{ns}".lower()

    return st.builds(callback, text(alphabet=ascii_letters + "-", **kwargs))


def labels(min_size=1, max_size=5, **kwargs):
    label_alphabet = ascii_lowercase + digits + "-" + "." + "/"

    return st.dictionaries(
        keys=text(alphabet=label_alphabet),
        values=text(alphabet=label_alphabet),
        min_size=min_size,
        max_size=max_size,
        **kwargs,
    )


def environment(**kwargs):
    return st.sampled_from(list(ENVIRONMENTS.keys()), **kwargs)


def addon(env):
    return AddonStrategy(env)


#
# Helpers to build addon strategy
#
def build_addon_strategy_for_env(env):
    """
    Returns a custom hypothesis strategy to draw Addon from.
    All addons are drawn from the same environment.

    addon_id can't start with a number otherwise it breaks indexing when
    present as a dictionary key.
    """

    def callback(env, labels, annotations, metadata):
        """Callback used to patch addon metadata before injection in tests."""
        addon = MockAddon(env)

        # jsonschema object.items does not respect pattern field
        metadata["namespaceAnnotations"] = annotations
        metadata["namespaceLabels"] = labels

        # TODO - when a pattern ends with '$' hypothesis adds a '\n', which
        # breaks jinja2 templating. Using this solution as temporary fix.
        fields_to_rstrip = [
            "name",
            "testHarness",
            "label",
            "ocmQuotaName",
            "quayRepo",
            "addonOwner",
            "id",
        ]
        for f in fields_to_rstrip:
            metadata[f] = metadata[f].rstrip()

        addon.metadata = metadata
        return addon

    return st.builds(
        callback,
        env=st.just(env),
        labels=labels(),
        annotations=labels(),
        metadata=from_schema(
            get_fast_schema(),
            # we define a custom format for non-unicode generation, this is
            # because we use `yaml.load_safe(...)` which breaks on non-printable
            # UTF-8. This format name must not override built-in jsonschema
            # format names:
            # https://json-schema.org/understanding-json-schema/reference/string.html#built-in-formats
            custom_formats={
                "printable": text(),
            },
        ),
    )


def get_fast_schema():
    """Only generate required fields for fast testing."""
    schema = load_addon_metadata_schema()
    fast_schema = deepcopy(schema)

    all_fields = set(fast_schema.get("properties").keys())
    required_fields = set(fast_schema.get("required"))
    optional_fields = all_fields - required_fields
    for f in optional_fields:
        fast_schema["properties"].pop(f, None)

    return fast_schema


class AddonStrategy:
    """Singleton wrapper for addon hypothesis strategy."""

    _instances = {env: None for env in ENVIRONMENTS}

    def __new__(cls, env):
        if env not in ENVIRONMENTS:
            raise TypeError("Invalid environment.")

        if cls._instances[env] is None:
            cls._instances[env] = build_addon_strategy_for_env(env)
        return cls._instances[env]


class MockAddon:
    """
    Singleton wrapper for the mock addon.
    Always returns a deepcopy so we start from a fresh addon.
    """

    _instances = {env: None for env in ENVIRONMENTS}

    def __new__(cls, env):
        if env not in ENVIRONMENTS:
            raise TypeError("Invalid environment.")

        if cls._instances[env] is None:
            cls._instances[env] = Addon(TEST_OPERATOR_PATH, env)
        return deepcopy(cls._instances[env])
