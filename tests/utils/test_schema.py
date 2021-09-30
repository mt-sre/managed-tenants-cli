from io import StringIO

import pytest
from jsonschema.exceptions import SchemaError

from managedtenants.data.paths import DATA_DIR
from managedtenants.utils.schema import (
    SchemaLoader,
    load_addon_metadata_schema,
    load_draft7_schema,
)

invalid_type_value = """
---
"$schema": "http://json-schema.org/draft-07/schema#"
type: invalid
"""


@pytest.mark.parametrize(
    "case",
    [
        {"path_or_file": invalid_type_value, "raises": True},
        {
            "path_or_file": DATA_DIR / "metadata.schema.yaml",
            "raises": False,
        },
    ],
)
def test_load_draft7_schema(case):
    if case["raises"]:
        with pytest.raises(SchemaError):
            _ = load_draft7_schema(path_or_file=StringIO(case["path_or_file"]))
    else:
        assert isinstance(
            load_draft7_schema(path_or_file=case["path_or_file"]), dict
        )


def test_load_addon_metadata_schema():
    assert isinstance(load_addon_metadata_schema(), dict)


def test_singleton_AddonMetadataSchema():
    assert id(SchemaLoader("metadata")) == id(SchemaLoader("metadata"))


def test_singleton_AddonImageSetSchema():
    assert id(SchemaLoader("imageset")) == id(SchemaLoader("imageset"))
