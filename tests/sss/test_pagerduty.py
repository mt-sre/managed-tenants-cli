import pytest

from tests.testutils.addon_helpers import addon_with_pagerduty  # noqa: F401


@pytest.mark.parametrize(
    "addon_str",
    [
        "addon_with_pagerduty",
    ],
)
def test_pagerduty(addon_str, request):
    addon = request.getfixturevalue(addon_str)
    expected_data = {
        "metadata": {
            "name": f"addon-{addon.metadata['id']}",
        },
        "spec": {
            "servicePrefix": addon.metadata["id"],
            "acknowledgeTimeout": addon.metadata["pagerduty"][
                "acknowledgeTimeout"
            ],
            "resolveTimeout": addon.metadata["pagerduty"]["acknowledgeTimeout"],
            "escalationPolicy": addon.metadata["pagerduty"]["escalationPolicy"],
            "clusterDeploymentSelector": {
                "matchLabels": {
                    f"api.openshift.com/addon-{addon.metadata['id']}": "true"
                }
            },
            "targetSecretRef": {
                "name": addon.metadata["pagerduty"]["secretName"],
                "namespace": addon.metadata["pagerduty"]["secretNamespace"],
            },
        },
    }

    sss_walker = addon.sss.walker()
    pagerduty_obj = sss_walker["pdi"]
    assert pagerduty_obj is not None
    assert pagerduty_obj.get("metadata") is not None
    assert pagerduty_obj.get("spec") is not None

    metadata, spec = pagerduty_obj.get("metadata"), pagerduty_obj.get("spec")
    assert metadata.get("name") == "addon-test-operator"
    assert spec.get("servicePrefix") == expected_data["spec"]["servicePrefix"]
    assert (
        spec.get("acknowledgeTimeout")
        == expected_data["spec"]["acknowledgeTimeout"]
    )
    assert spec.get("resolveTimeout") == expected_data["spec"]["resolveTimeout"]
    assert (
        spec.get("escalationPolicy")
        == expected_data["spec"]["escalationPolicy"]
    )
    assert (
        spec.get("clusterDeploymentSelector")
        == expected_data["spec"]["clusterDeploymentSelector"]
    )
    assert (
        spec.get("targetSecretRef") == expected_data["spec"]["targetSecretRef"]
    )
