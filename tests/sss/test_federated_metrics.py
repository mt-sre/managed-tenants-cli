import hypothesis.strategies as hypothesis_strategies
import pytest
from hypothesis import given

import tests.testutils.strategies as custom_strategies
from managedtenants.core.addon_manager import AddonManager
from managedtenants.core.addons_loader.sss import Sss


@given(data=hypothesis_strategies.data())
def test_namespace_and_servicemonitor_v1(data):
    env = data.draw(custom_strategies.environment())
    addon = data.draw(custom_strategies.addon(env))
    addon.metadata["monitoring"] = {
        "namespace": data.draw(custom_strategies.namespace()),
        "matchNames": data.draw(
            hypothesis_strategies.lists(custom_strategies.k8s_name())
        ),
        "matchLabels": data.draw(custom_strategies.labels()),
    }

    # Rerender selectorsyncset.yaml.j2
    addon.sss = Sss(addon=addon)
    walker = addon.sss.walker()

    expected_ns_name = f"redhat-monitoring-{addon.metadata['id']}"

    # validate namespace
    found = False
    for ns, _ in walker["sss_deploy"]["spec"]["resources"]["Namespace"]:
        if ns == expected_ns_name:
            found = True
            break
    assert found

    # validate servicemonitor
    _, sm = walker["sss_deploy"]["spec"]["resources"]["ServiceMonitor"][0]
    assert sm["metadata"]["namespace"] == expected_ns_name

    assert (
        addon.metadata["monitoring"]["namespace"]
        == sm["spec"]["namespaceSelector"]["matchNames"][0]
    )

    for matchName in addon.metadata["monitoring"]["matchNames"]:
        series_name = f"""'{{__name__="{matchName}"}}'"""
        assert series_name in sm["spec"]["endpoints"][0]["params"]["match[]"]

    for k, v in addon.metadata["monitoring"]["matchLabels"].items():
        assert sm["spec"]["selector"]["matchLabels"][k] == v


# For v2, the namespace and ServiceMonitor should be created and managed
# by the addon-operator.
@given(data=hypothesis_strategies.data())
def test_namespace_and_servicemonitor_v2(data):
    env = data.draw(custom_strategies.environment())
    addon = data.draw(custom_strategies.addon(env))
    addon.metadata["monitoring"] = {
        "matchNames": data.draw(
            hypothesis_strategies.lists(custom_strategies.k8s_name())
        ),
        "matchLabels": data.draw(custom_strategies.labels()),
    }
    addon.manager = AddonManager.ADDON_OPERATOR
    addon.metadata["indexImage"] = custom_strategies.quay_image(
        addon.metadata["id"]
    )

    # Rerender selectorsyncset.yaml.j2
    addon.sss = Sss(addon=addon)
    walker = addon.sss.walker()

    expected_ns_name = f"redhat-monitoring-{addon.metadata['id']}"

    # validate namespace does not exist
    found = False
    for ns, _ in walker["sss_deploy"]["spec"]["resources"]["Namespace"]:
        if ns == expected_ns_name:
            found = True
            break
    assert not found

    # validate servicemonitor does not exist
    with pytest.raises(IndexError):
        _ = walker["sss_deploy"]["spec"]["resources"]["ServiceMonitor"][0]
