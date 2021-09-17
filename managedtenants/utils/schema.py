from pathlib import Path

import yaml
from jsonschema import Draft7Validator
from jsonschema.exceptions import SchemaError

from managedtenants.data.paths import DATA_DIR


def load_addon_metadata_schema():
    """
    Wrapper that returns the addon metadata schema and utilizes
    Singleton pattern for optimization.
    """
    return AddonMetadataSchema()


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
            path_or_file, "r"
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


class AddonMetadataSchema:
    """Singleton wrapper to load the addon metadata schema only once."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = load_draft7_schema(
                path_or_file=DATA_DIR / "metadata.schema.yaml"
            )
        return cls._instance
