import logging
import sqlite3
import subprocess
import tempfile

from sretoolbox.container import Image
from sretoolbox.utils.logger import get_text_logger

from managedtenants.bundles.binary_deps import OPM
from managedtenants.bundles.exceptions import DockerError, IndexBuilderError
from managedtenants.utils.git import get_short_hash


class IndexBuilder:
    def __init__(
        self,
        docker_api,
        dry_run=False,
        debug=False,
    ):
        self.dry_run = dry_run
        self.docker_api = docker_api
        self.log = get_text_logger(
            "managedtenants-index-builder",
            level=logging.DEBUG if debug else logging.INFO,
        )

    def build_and_push(
        self, bundles, hash_string=get_short_hash(), skip_validation=False
    ):
        """
        Build and push an index image. The base image is named binary-image by
        opm and is later used to generate a final dockerfile using this
        template:
        https://github.com/operator-framework/operator-registry/blob/5566e4b6832a7fc08c12d3c79fc0a0b8c6a2e7aa/alpha/action/generate_dockerfile.go#L42-L63

        :params bundles: List of Bundle to be added to the index image.
        :return: An Index image that has been pushed.
        """

        index_image = self._build(bundles, hash_string, skip_validation)
        return self._push(index_image)

    # pylint: disable=unused-argument
    def _build(self, bundles, hash_string, skip_validation=False):
        if len(bundles) == 0:
            raise IndexBuilderError("invalid empty bundles list")

        # all bundles for a given addon produce the same index_repo
        index_image = Image(
            f"{self.docker_api.registry}/"
            f"{bundles[0].index_repo_name()}:{hash_string}"
        )
        self.log.info(f'Building index image "{index_image.url_tag}".')
        self.log.debug(
            f"Index image contains {len(bundles)} bundles: {bundles}."
        )

        # pylint: disable=line-too-long
        cmd = [
            "index",
            "--container-tool",
            "docker",
            "add",
            "--binary-image",
            # Custom base image based on UBI, OPM 1.19.5
            # https://github.com/mt-sre/containers/tree/main/opm-ubi
            "quay.io/mtsre/opm-ubi@sha256:471dc5652a045103d75bafd24072926fbd7a520bd613cee896f2ce1602316eac",  # noqa: 501
            "--permissive",
            "--bundles",
            ",".join([bundle.image.url_digest for bundle in bundles]),
            "--tag",
            index_image.url_tag,
        ]
        self.log.debug(f"OPM build command: opm {' '.join(cmd)}")

        try:
            OPM.run(cmd)

            # (sblaisdo) the index image is always broken on --dry-run as opm
            #            tooling requires bundles to be hosted on a registry
            # if not skip_validation:
            #     self._validate_sql_catalog(index_image.url_tag, len(bundles))
            return index_image

        except subprocess.CalledProcessError as e:
            raise IndexBuilderError(
                f"Failed to build index image {index_image.url_tag} with opm"
                f" version {OPM.version}: {e.stdout.decode()}."
            )

        except DockerError as e:
            raise IndexBuilderError(f"Built invalid index_image: {e}")

    def _push(self, index_image):
        # skip pushing on dry_run
        if self.dry_run:
            return index_image

        try:
            self.log.info(f'Pushing index image "{index_image.url_tag}".')
            self.docker_api.push(index_image)
            return index_image

        except DockerError as e:
            err_msg = f"failed to push {index_image}: {e}."
            self.log.error(err_msg)
            raise IndexBuilderError(err_msg)

    def _validate_sql_catalog(self, tag, n_bundles):
        """
        Validates an sql based index_image. Makes sure it contains bundles.
        """
        db_name = "/database/index.db"
        try:
            in_memory_db = self.docker_api.extract_file_from_container(
                tag, db_name
            )

        except DockerError as e:
            err_msg = f"failed to validate {tag}, got {e}."
            self.log.error(err_msg)
            raise IndexBuilderError(err_msg)

        try:
            with SQLCatalog(in_memory_db) as catalog:
                bundles = catalog.get_bundles()
                self.log.debug(bundles)

                if len(bundles) != n_bundles:
                    err_msg = (
                        f"expected {db_name} to contain {n_bundles} bundles"
                        f" but found {len(bundles)}."
                    )
                    self.log.error(err_msg)
                    raise IndexBuilderError(err_msg)

                self.log.debug(f"Found {len(bundles)} bundles:")
                for bundle in bundles:
                    self.log.debug(bundle)

        except sqlite3.Error as e:
            err_msg = (
                "failed to query bundles from '/database/index.db' inside of ",
                f"{tag}, got {e}.",
            )
            self.log.error(err_msg)
            raise IndexBuilderError(err_msg)


# (sblaisdo) OPM 1.19.5 uses a busybox distroless container. It does not have
# sqlite3 or a package manager so it's easier to simply create a temp container
# and validate the index.db on the host.
class SQLCatalog:
    """
    Abstract an SQL catalog.
    """

    def __init__(self, in_memory_db):
        """
        Initialize a database connection from an in_memory_db fileobj.
        """
        # sqlite3 module only works with path-like object and does not support
        # fileobj so we unfortunately have to do some temp I/O gymnastics
        try:
            with tempfile.NamedTemporaryFile() as tmp:
                tmp.write(in_memory_db.read())
                self.db = sqlite3.connect(tmp.name)
                self.cursor = self.db.cursor()

        except sqlite3.Error as e:
            raise e

    def get_bundles(self):
        try:
            self.cursor.execute("SELECT * from properties;")
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            raise e

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.db.close()
