import pytest
from infra.instance import EC2Instance


# Test fixtures — reusable test objects
@pytest.fixture
def healthy_instance():
    return EC2Instance("i-0abc123", "t3.micro", "us-east-1", True, 45)

@pytest.fixture
def alert_instance():
    return EC2Instance("i-0def456", "t3.large", "us-west-2", True, 82)

@pytest.fixture
def down_instance():
    return EC2Instance("i-0ghi789", "t3.medium", "eu-west-1", False, 91)


# Tests
def test_status_up(healthy_instance):
    assert healthy_instance.status() == "[UP]"

def test_status_down(down_instance):
    assert down_instance.status() == "[DOWN]"

def test_is_healthy_below_threshold(healthy_instance):
    assert healthy_instance.is_healthy(75) == True

def test_is_healthy_above_threshold(alert_instance):
    assert alert_instance.is_healthy(75) == False

def test_summarise_healthy(healthy_instance):
    result = healthy_instance.summarise(75)
    assert "[UP]" in result
    assert "OK" in result
    assert "i-0abc123" in result

def test_summarise_alert(alert_instance):
    result = alert_instance.summarise(75)
    assert "[UP]" in result
    assert "ALERT" in result

def test_summarise_down(down_instance):
    result = down_instance.summarise(75)
    assert "[DOWN]" in result