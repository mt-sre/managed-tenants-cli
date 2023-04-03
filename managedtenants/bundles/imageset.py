import jsonschema
import yaml

from managedtenants.bundles.exceptions import ImageSetError
from managedtenants.data.paths import SCHEMAS_DIR
from managedtenants.utils.schema import load_schema


class ImageSet:
    # pylint:disable=too-many-arguments
    def __init__(
        self,
        addon_name,
        env,
        version,
        index_image,
        package_image,
        ocm_config,
        related_images=None,
    ):
        self.name = f"{addon_name}.v{version}"
        self.env = env
        self.version = version
        self.path = f"addons/{addon_name}/addonimagesets/{env}/{self.name}.yaml"
        self.index_image = index_image
        self.package_image = package_image
        self.ocm_config = ocm_config
        # has to be of type array
        self.related_images = (
            related_images if related_images is not None else []
        )

    def to_yaml(self):
        """
        Convert the imageset to a valid schema instance and dump as yaml.
        """
        try:
            data = self._to_schema_instance()
            return yaml.dump(data, Dumper=yaml.CSafeDumper)

        except jsonschema.exceptions.SchemaError as e:
            raise ImageSetError(
                f"imageset.schema.yaml schema error: {e.message}"
            )
        except jsonschema.exceptions.ValidationError as e:
            raise ImageSetError(f"{self} validation error: {e.message}")

        except yaml.YAMLError as e:
            raise ImageSetError(f"{self} error writing yaml: {e}")

    def _to_schema_instance(self):
        try:
            instance = {
                "name": self.name,
                "indexImage": self.index_image.url_digest,
                "relatedImages": self.related_images,
                **self.ocm_config,
            }

            if self.package_image is not None:
                instance["packageImage"] = self.package_image.url_digest

            jsonschema.validate(
                instance=instance,
                schema=load_schema("imageset"),
                resolver=jsonschema.RefResolver(
                    base_uri=f"file://{SCHEMAS_DIR}/",
                    referrer="imageset.schema.yaml",
                ),
            )
            return instance

        except jsonschema.exceptions.SchemaError as e:
            raise ImageSetError(
                f"imageset.schema.yaml schema error: {e.message}"
            )
        except jsonschema.exceptions.ValidationError as e:
            raise ImageSetError(f"{self} validation error: {e.message}")

    def __str__(self):
        return (
            f"ImageSet(name={self.name}, env={self.env},"
            f" version={self.version}, path={self.path},"
            f" index_image={self.index_image},"
            f" package_image={self.package_image},"
            f" ocm_config={self.ocm_config})"
            f" related_images={self.related_images})"
        )
