from pathlib import Path

import pytest

from managedtenants.utils.git import ChangeDetector

ROOT = Path("/addons")


@pytest.mark.parametrize(
    "data",
    [
        {
            "parents": set(
                [
                    ROOT / "addon-one",
                    ROOT / "addon-two",
                    ROOT / "addon-three",
                ]
            ),
            "children": set(
                [
                    ROOT / "addon-one/some/file",
                    ROOT / "addon-one/another/file",
                ]
            ),
            "expected": set([ROOT / "addon-one"]),
        },
        {
            "parents": set(
                [
                    ROOT / "addon-one",
                    ROOT / "addon-two",
                    ROOT / "addon-three",
                ]
            ),
            "children": set(
                [
                    ROOT / "addon-one/some/file",
                    ROOT / "addon-two/another/file",
                    ROOT / "addon-three/yippy",
                ]
            ),
            "expected": set(
                [
                    ROOT / "addon-one",
                    ROOT / "addon-two",
                    ROOT / "addon-three",
                ]
            ),
        },
        {
            "parents": set(
                [
                    ROOT / "addon-one",
                    ROOT / "addon-two",
                    ROOT / "addon-three",
                ]
            ),
            "children": set(
                [
                    ROOT / "addon-four/some/file",
                    ROOT / "addon-five/another/file",
                    ROOT / "addon-six/yippy",
                ]
            ),
            "expected": set(),
        },
    ],
)
def test_change_detector_intersect(data):
    cd = ChangeDetector(addons_dir="unused")
    got = cd._intersect(data["parents"], data["children"])

    assert len(got) == len(data["expected"])
    for e in data["expected"]:
        assert e in got
