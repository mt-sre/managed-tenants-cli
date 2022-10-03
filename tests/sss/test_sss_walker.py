import hypothesis.strategies as hypothesis_strategies
from hypothesis import given

import tests.testutils.strategies as custom_strategies
from managedtenants.core.addons_loader.sss import Sss


@given(hypothesis_strategies.data())
def test_sss_deploy(data):
    env = data.draw(custom_strategies.environment())
    addon = data.draw(custom_strategies.addon(env))
    # Set every field so that we render the template fully
    addon.metadata["namespaces"] = data.draw(
        hypothesis_strategies.lists(
            custom_strategies.namespace(), min_size=2, max_size=5, unique=True
        )
    )

    # Rerender template
    addon.sss = Sss(addon=addon)
    walker = addon.sss.walker()
    resources = walker["sss_deploy"]["spec"]["resources"]

    assert len(resources["Namespace"]) == len(addon.metadata["namespaces"])
    for ns, _ in resources["Namespace"]:
        assert ns in addon.metadata["namespaces"]

    # Validate CatalogSource, OperatorGroup, Subscription
    for kind, name in [
        (
            "CatalogSource",
            f"addon-{addon.metadata['id']}-catalog",
        ),
        (
            "OperatorGroup",
            "redhat-layered-product-og",
        ),
        (
            "Subscription",
            f"addon-{addon.metadata['id']}",
        ),
    ]:
        assert len(resources[kind]) == 1
        assert name == resources[kind][0][0]


@given(hypothesis_strategies.data())
def test_sss_delete(data):
    env = data.draw(custom_strategies.environment())
    addon = data.draw(custom_strategies.addon(env))
    target_ns = data.draw(custom_strategies.namespace())
    addon.metadata["targetNamespace"] = target_ns

    # Rerender template
    addon.sss = Sss(addon=addon)
    walker = addon.sss.walker()
    resources = walker["sss_delete"]["spec"]["resources"]

    assert len(resources["Namespace"]) == 1
    assert target_ns == resources["Namespace"][0][0]

    assert len(resources["ConfigMap"]) == 1
    assert target_ns == resources["ConfigMap"][0][1]["metadata"]["namespace"]


# TODO
# @given(hypothesis_strategies.data())
# def test_pagerduty(data):
#     pass
