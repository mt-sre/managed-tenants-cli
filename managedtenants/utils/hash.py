from functools import lru_cache
from hashlib import sha256

from checksumdir import dirhash


@lru_cache(maxsize=None)
def hash_sha256(items):
    """
    Joins the items and hashes them using sha256.

    :param items: The string items to be hashed.
    :return: Hexdigest.
    """
    value = "-".join(items)
    sha256_hash = sha256()
    sha256_hash.update(value.encode())
    return sha256_hash.hexdigest()


@lru_cache(maxsize=None)
def hash_dir_sha256(path):
    """
    Hashes a directory content using sha256.

    :param path: The directory path.
    :return: Hexdigest.
    """
    return dirhash(path, "sha256")
