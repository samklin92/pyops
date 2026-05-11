import pytest
from infra.instance import EC2Instance
from infra.monitor import InfraMonitor


@pytest.fixture
def config():
    return {
        "environment": "production",
        "region": "us-east-1",
        "alert_threshold": 75
    }

@pytest.fixture
def monitor(config):
    return InfraMonitor(config)

@pytest.fixture
def populated_monitor(monitor):
    monitor.add_instance(EC2Instance("i-0abc123", "t3.micro", "us-east-1", True, 45))
    monitor.add_instance(EC2Instance("i-0def456", "t3.large", "us-west-2", True, 82))
    monitor.add_instance(EC2Instance("i-0ghi789", "t3.medium", "eu-west-1", False, 91))
    return monitor


# Tests
def test_monitor_initialises(monitor):
    assert monitor.alert_threshold == 75
    assert monitor.environment == "production"
    assert monitor.instances == []

def test_add_instance(monitor):
    instance = EC2Instance("i-0abc123", "t3.micro", "us-east-1", True, 45)
    monitor.add_instance(instance)
    assert len(monitor.instances) == 1

def test_add_multiple_instances(populated_monitor):
    assert len(populated_monitor.instances) == 3

def test_up_count(populated_monitor):
    up = sum(1 for i in populated_monitor.instances if i.running)
    assert up == 2

def test_down_count(populated_monitor):
    down = sum(1 for i in populated_monitor.instances if not i.running)
    assert down == 1

def test_alert_count(populated_monitor):
    alerts = sum(
        1 for i in populated_monitor.instances
        if i.cpu > populated_monitor.alert_threshold
    )
    assert alerts == 2