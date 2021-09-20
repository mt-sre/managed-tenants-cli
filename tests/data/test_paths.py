import pytest

from managedtenants.data.paths import ADDONS_DIR, DATA_DIR


@pytest.mark.parametrize(
    "case",
    [
        {"dir": ADDONS_DIR, "expected": "addons"},
        {"dir": DATA_DIR, "expected": "data"},
    ],
)
def test_directories(case):
    assert case["dir"].is_dir()
    assert case["dir"].stem == case["expected"]
