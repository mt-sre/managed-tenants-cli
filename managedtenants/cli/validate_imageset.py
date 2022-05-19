import sys

import jsonschema
import yaml

from managedtenants.data.paths import SCHEMAS_DIR
from managedtenants.utils.schema import load_schema


def main():
    try:
        data = yaml.safe_load(sys.stdin)
    except yaml.YAMLError as exc:
        print(f"Invalid yaml: {exc}")
        sys.exit(1)

    try:
        jsonschema.validate(
            instance=data,
            schema=load_schema("imageset"),
            resolver=jsonschema.RefResolver(
                base_uri=f"file://{SCHEMAS_DIR}/",
                referrer="imageset.schema.yaml",
            ),
        )
    except (jsonschema.SchemaError, jsonschema.ValidationError) as exc:
        print(f"Schema validation failed {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
