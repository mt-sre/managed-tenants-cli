import pytest
from managedtenants.data.paths import DATA_DIR


@pytest.mark.parametrize(
    "case",
    [
        {"dir": DATA_DIR, "expected": "data"},
    ],
)
def test_directories(case):
    assert case["dir"].is_dir()
    assert case["dir"].stem == case["expected"]
