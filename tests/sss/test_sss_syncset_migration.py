import pytest
from jsonschema.exceptions import ValidationError

from tests.testutils.addon_helpers import (  # noqa: F401
    addon_with_syncset_migration_step_1,
    addon_with_syncset_migration_step_2,
    addon_with_syncset_migration_step_3,
    addon_with_syncset_migration_step_4,
    addon_with_syncset_migration_step_5,
    addon_with_syncset_migration_step_rollback_ocm,
    addon_with_syncset_migration_step_rollback_reset_addon_migration,
    addon_with_syncset_migration_step_rollback_selectorsyncset,
    addon_with_wrong_syncset_migration_step,
)


@pytest.mark.parametrize(
    "addon_str",
    [
        "addon_with_syncset_migration_step_1",
        "addon_with_syncset_migration_step_2",
        "addon_with_syncset_migration_step_3",
        "addon_with_syncset_migration_step_4",
        "addon_with_syncset_migration_step_5",
        "addon_with_syncset_migration_step_rollback_ocm",
        "addon_with_syncset_migration_step_rollback_selectorsyncset",
        "addon_with_syncset_migration_step_rollback_reset_addon_migration",
        "addon_with_wrong_syncset_migration_step",
    ],
)
def test_sss_syncset_migration(addon_str, request):
    if addon_str == "addon_with_wrong_syncset_migration_step":
        with pytest.raises(ValidationError):
            addon = request.getfixturevalue(addon_str)
    else:
        addon = request.getfixturevalue(addon_str)

        sss_walker = addon.sss.walker()

        resource_apply_mode = sss_walker["sss_deploy"]["spec"][
            "resourceApplyMode"
        ]
        if addon_str in [
            "addon_with_syncset_migration_step_1",
            "addon_with_syncset_migration_step_rollback_selectorsyncset",
            "addon_with_syncset_migration_step_rollback_reset_addon_migration",
        ]:
            assert resource_apply_mode == "Sync"
        else:
            assert resource_apply_mode == "Upsert"

        cluster_dep_label_selectors_obj = sss_walker["sss_deploy"]["spec"][
            "clusterDeploymentSelector"
        ]["matchLabels"]
        if addon_str in [
            "addon_with_syncset_migration_step_1",
            "addon_with_syncset_migration_step_2",
            "addon_with_syncset_migration_step_rollback_selectorsyncset",
            "addon_with_syncset_migration_step_rollback_reset_addon_migration",
        ]:
            assert (
                cluster_dep_label_selectors_obj[addon.metadata["label"]]
                == "true"
            )
        else:
            assert (
                cluster_dep_label_selectors_obj[addon.metadata["label"]]
                == "migrated"
            )
