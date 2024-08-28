# Copyright 2024 sed-i
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

import ops
import ops.testing
import pytest

from charm import K6K8SCharm


@pytest.fixture
def harness():
    harness = ops.testing.Harness(K6K8SCharm)
    harness.begin()
    yield harness
    harness.cleanup()


def test_pebble_ready(harness: ops.testing.Harness[K6K8SCharm]):
    # Simulate the container coming up and emission of pebble-ready event
    harness.container_pebble_ready("some-container")
    # Ensure we set an ActiveStatus with no message
    assert harness.model.unit.status == ops.ActiveStatus()
