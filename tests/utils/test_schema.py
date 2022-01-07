from io import StringIO

import pytest
from jsonschema.exceptions import SchemaError

from managedtenants.data.paths import SCHEMAS_DIR
from managedtenants.utils.schema import (
    SchemaLoader,
    load_draft7_schema,
    load_schema,
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
            "path_or_file": SCHEMAS_DIR / "metadata.schema.yaml",
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


@pytest.mark.parametrize(
    "schema_name",
    ["metadata", "imageset", "mtbundles"],
)
def test_schemas_are_singletons(schema_name):
    assert id(load_schema(schema_name)) == id(load_schema(schema_name))
