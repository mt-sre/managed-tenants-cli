import pytest

from managedtenants.bundles.utils import check_image_size
from tests.testutils.addon_helpers import create_zero_size_docker_image


def test_check_image_size():
    zero_size_image = create_zero_size_docker_image()
    if zero_size_image is None:
        pytest.fail("Failed to create a zero size docker image!")
    else:
        result = check_image_size(zero_size_image.url_tag)
        assert result == 0
