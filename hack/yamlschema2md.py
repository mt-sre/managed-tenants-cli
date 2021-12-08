import argparse

import jsonschema2md
import yaml


def main(schema, output):
    with open(schema, "r", encoding="utf8") as yaml_in, open(
        output, "w", encoding="utf8"
    ) as md_out:
        yaml_obj = yaml.load(yaml_in, Loader=yaml.CSafeLoader)
        md_lines = jsonschema2md.Parser().parse_schema(yaml_obj)
        md_out.write("\n".join(md_lines))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="yamlschema2md")
    parser.add_argument(
        "-s", "--schema", required=True, help="Path to YAML schema."
    )
    parser.add_argument(
        "-o", "--output", required=True, help="Markdown output path."
    )
    args = parser.parse_args()

    main(args.schema, args.output)
