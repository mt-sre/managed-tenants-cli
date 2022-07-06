import random

import hypothesis.strategies as hypothesis_strategies
import pytest
from hypothesis import given

import tests.testutils.strategies as custom_strategies
from managedtenants.core.addons_loader.sss import Sss


@given(data=hypothesis_strategies.data())
def test_namespace_and_servicemonitor_v1(data):
    env = data.draw(custom_strategies.environment())
    addon = data.draw(custom_strategies.addon(env))
    addon.metadata["monitoring"] = {
        "portName": data.draw(custom_strategies.k8s_name()),
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

    # validate endpoint.0
    endpoint = sm["spec"]["endpoints"][0]
    assert endpoint["port"] == addon.metadata["monitoring"]["portName"]
    assert (
        endpoint["bearerTokenFile"]
        == "/var/run/secrets/kubernetes.io/serviceaccount/token"
    )

    for matchName in addon.metadata["monitoring"]["matchNames"]:
        series_name = f"""{{__name__="{matchName}"}}"""
        assert series_name in endpoint["params"]["match[]"]

    # validate selectors
    assert (
        addon.metadata["monitoring"]["namespace"]
        == sm["spec"]["namespaceSelector"]["matchNames"][0]
    )

    for k, v in addon.metadata["monitoring"]["matchLabels"].items():
        assert sm["spec"]["selector"]["matchLabels"][k] == v
