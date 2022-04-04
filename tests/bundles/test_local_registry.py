from managedtenants.bundles.registry import LocalDockerRegistry


def test_run_and_teardown_local_docker_registry():
    registry = LocalDockerRegistry()

    registry.run()
    assert registry.exists()

    registry.teardown()
    assert not registry.exists()
