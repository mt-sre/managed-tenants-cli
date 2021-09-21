import hypothesis.strategies as hypothesis_strategies
import pytest
from hypothesis import given

import tests.testutils.strategies as custom_strategies
from managedtenants.core.addons_loader.sss import Sss


@given(data=hypothesis_strategies.data())
@pytest.mark.parametrize(
    "has_value",
    [
        True,
        False,
    ],
)
def test_common_labels_and_annotations(has_value, data):
    env = data.draw(custom_strategies.environment())
    addon = data.draw(custom_strategies.addon(env))

    if has_value:
        addon.metadata["commonLabels"] = data.draw(custom_strategies.labels())
        addon.metadata["commonAnnotations"] = data.draw(
            custom_strategies.labels()
        )
    else:
        addon.metadata.pop("commonLabels", None)
        addon.metadata.pop("commonAnnotations", None)

    # Rerender selectorsyncset.yaml.j2
    addon.sss = Sss(addon=addon)
    walker = addon.sss.walker()

    # Validate labels on CatalogSource
    r = walker["sss_deploy"]["spec"]["resources"]["CatalogSource"][0][1]
    if has_value:
        for k, v in r["metadata"]["annotations"].items():
            assert addon.metadata["commonAnnotations"][k] == v
        for k, v in r["metadata"]["labels"].items():
            assert addon.metadata["commonLabels"][k] == v
    else:
        # field should be undefined
        for field in ["annotations", "labels"]:
            with pytest.raises(KeyError):
                _ = r["metadata"][field]


@given(data=hypothesis_strategies.data())
def test_namespace_labels_and_annotations_priority_over_common(data):
    env = data.draw(custom_strategies.environment())
    addon = data.draw(custom_strategies.addon(env))
    duplicate_key, common_val, ns_val = data.draw(
        hypothesis_strategies.lists(
            custom_strategies.k8s_name(), min_size=3, max_size=3, unique=True
        )
    )
    addon.metadata["namespaces"] = data.draw(
        hypothesis_strategies.lists(
            custom_strategies.namespace(), min_size=2, max_size=2, unique=True
        )
    )

    addon.metadata["namespaceLabels"].update({duplicate_key: ns_val})
    addon.metadata["namespaceAnnotations"].update({duplicate_key: ns_val})
    addon.metadata["commonLabels"] = {duplicate_key: common_val}
    addon.metadata["commonAnnotations"] = {duplicate_key: common_val}

    # Rerender selectorsyncset.yaml.j2
    addon.sss = Sss(addon=addon)
    walker = addon.sss.walker()

    for _, ns in walker["sss_deploy"]["spec"]["resources"]["Namespace"]:
        assert ns["metadata"]["labels"][duplicate_key] == ns_val
        assert ns["metadata"]["annotations"][duplicate_key] == ns_val
