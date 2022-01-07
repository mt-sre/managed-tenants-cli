from pathlib import Path

import yaml
from jsonschema import Draft7Validator
from jsonschema.exceptions import SchemaError

from managedtenants.data.paths import SCHEMAS_DIR


def load_schema(name):
    """
    Load schema from a recognized name.

    Acceptable names: metadata, imageset and mtbundles.
    """
    valid_schema_names = ("metadata", "imageset", "mtbundles")
    if name not in valid_schema_names:
        raise ValueError(
            f"Invalid schema name '{name}' provided. Please use a valid schema"
            f" name: {','.join(valid_schema_names)}"
        )
    return SchemaLoader(name)


# Accept path or file for easier testing
def load_draft7_schema(path_or_file):
    """
    Loads and validates a Draft7 schema:
        https://json-schema.org/specification-links.html

    :param path_or_file: Absolute path or file to jsonschema.
    :type path_or_file: Union[PosixPath, IO]

    :raises SchemaError: If jsonschema can't be validated as Draft7

    :return: Python object representing the jsonschema
    :rtype: Dict
    """
    if isinstance(path_or_file, Path):
        f = file_to_close = open(  # pylint: disable=consider-using-with
            path_or_file, "r", encoding="utf8"
        )
    else:
        f = path_or_file
        file_to_close = None
    try:
        schema = yaml.load(f.read(), Loader=yaml.CSafeLoader)
        Draft7Validator.check_schema(schema)
        return schema
    except Exception as e:
        raise SchemaError("Error reading addon metadata schema") from e
    finally:
        if file_to_close:
            file_to_close.close()


class SchemaLoader:
    """Singleton wrapper to load schemas only once."""

    _instances = {}
    _SUPPORTED_SCHEMAS = ["metadata", "imageset", "mtbundles"]

    def __new__(cls, schema_type):
        if schema_type in cls._SUPPORTED_SCHEMAS:
            if cls._instances.get(schema_type) is None:
                cls._instances[schema_type] = load_draft7_schema(
                    path_or_file=SCHEMAS_DIR / f"{schema_type}.schema.yaml"
                )
        else:
            raise SchemaError(f"{schema_type} schema is not supported")

        return cls._instances[schema_type]
