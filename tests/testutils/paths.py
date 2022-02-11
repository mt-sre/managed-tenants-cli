from pathlib import Path

TEST_ROOT = (Path(__file__) / ".." / "..").resolve()

TEST_OPERATOR_PATH = TEST_ROOT / "testdata" / "addons" / "test-operator"

CHECK_TASKS_DIR = (TEST_ROOT / ".." / "tasks" / "check").resolve()

DEPLOY_TASKS_DIR = (TEST_ROOT / ".." / "tasks" / "deploy").resolve()

REFERENCE_ADDON = TEST_ROOT / "testdata" / "addons" / "reference-addon"
