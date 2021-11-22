import pytest

from tests.testutils.addon_helpers import (
    addon_with_deadmanssnitch,
)  # noqa: F401


@pytest.mark.parametrize(
    "addon_str",
    [
        "addon_with_deadmanssnitch",
    ],
)
def test_deadmansnitch(addon_str, request):
    addon = request.getfixturevalue(addon_str)
    expected_data = {
        "metadata": {
            "name": f"addon-{addon.metadata['id']}",
        },
        "spec": {
            "clusterDeploymentSelector": {
                "matchExpressions": [
                    {
                        "key": f"api.openshift.com/addon-{addon.metadata['id']}",
                        "operator": "In",
                        "values": ["true"],
                    }
                ]
            },
            "snitchNamePostFix": addon.metadata['deadmanssnitch']['snitchNamePostFix'],
            "tags": addon.metadata['deadmanssnitch']['tags'],
            "targetSecretRef": {
                "name": f"{addon.metadata['id']}-deadmanssnitch",
                "namespace": addon.metadata['targetNamespace'],
            },
        },
    }
    
    sss_walker = addon.sss.walker()
    deadmanssnitch_obj = sss_walker["dms"]
    assert deadmanssnitch_obj is not None
    assert deadmanssnitch_obj.get("metadata") is not None
    assert deadmanssnitch_obj.get("spec")is not None

    metadata, spec = deadmanssnitch_obj.get("metadata"), deadmanssnitch_obj.get("spec")
    assert metadata.get("name") == "addon-test-operator"
    assert spec.get("clusterDeploymentSelector") == expected_data["spec"]["clusterDeploymentSelector"]
    assert spec.get("snitchNamePostFix") == expected_data["spec"]["snitchNamePostFix"]
    assert spec.get("tags") == expected_data["spec"]["tags"]
    assert spec.get("targetSecretRef") == expected_data["spec"]["targetSecretRef"]
