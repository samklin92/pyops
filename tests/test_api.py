import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

with patch("agent.run_agent", MagicMock()):
    from api import app

client = TestClient(app)

MOCK_INSTANCES = [
    {
        "id": "i-0abc123",
        "name": "web-server",
        "type": "t2.micro",
        "state": "running",
        "region": "us-east-1",
        "launch_time": "2026-05-13T12:00:00+00:00"
    }
]

MOCK_REPORTS = [
    {"key": "reports/report-2026-05-13.txt", "size_kb": 2.4, "last_modified": "2026-05-13T12:00:00+00:00"}
]

MOCK_ALARMS = [
    {"name": "pyops-cpu-high", "state": "OK", "metric": "CPUUtilization", "threshold": 80.0, "updated": "2026-05-13T12:00:00+00:00"}
]


# ── Root and health ──────────────────────────────────────

def test_root_returns_200():
    response = client.get("/")
    assert response.status_code == 200


def test_root_message():
    response = client.get("/")
    assert response.json()["message"] == "Infra Monitor API is running"


def test_health_returns_200():
    response = client.get("/health")
    assert response.status_code == 200


def test_health_schema():
    response = client.get("/health")
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


# ── Instances ────────────────────────────────────────────

def test_instances_returns_200():
    with patch("api.ec2.list_instances", return_value=MOCK_INSTANCES):
        response = client.get("/instances")
        assert response.status_code == 200


def test_instances_schema():
    with patch("api.ec2.list_instances", return_value=MOCK_INSTANCES):
        response = client.get("/instances")
        data = response.json()
        assert "count" in data
        assert "instances" in data
        assert data["count"] == 1


def test_instances_returns_404_when_empty():
    with patch("api.ec2.list_instances", return_value=[]):
        response = client.get("/instances")
        assert response.status_code == 404


def test_running_instances_returns_200():
    with patch("api.ec2.list_running", return_value=MOCK_INSTANCES):
        response = client.get("/instances/running")
        assert response.status_code == 200


def test_running_instances_returns_404_when_empty():
    with patch("api.ec2.list_running", return_value=[]):
        response = client.get("/instances/running")
        assert response.status_code == 404


def test_get_instance_returns_200():
    with patch("api.ec2.get_instance_state", return_value={"instance_id": "i-0abc123", "state": "running", "type": "t2.micro"}):
        response = client.get("/instances/i-0abc123")
        assert response.status_code == 200


def test_get_instance_returns_404_on_error():
    with patch("api.ec2.get_instance_state", side_effect=Exception("Not found")):
        response = client.get("/instances/i-invalid")
        assert response.status_code == 404


def test_stop_instance_returns_200():
    with patch("api.ec2.stop_instance", return_value={"instance_id": "i-0abc123", "action": "stop", "status": "initiated"}):
        response = client.post("/instances/i-0abc123/stop")
        assert response.status_code == 200


def test_start_instance_returns_200():
    with patch("api.ec2.start_instance", return_value={"instance_id": "i-0abc123", "action": "start", "status": "initiated"}):
        response = client.post("/instances/i-0abc123/start")
        assert response.status_code == 200


# ── Reports ──────────────────────────────────────────────

def test_reports_returns_200():
    with patch("api.s3.list_objects", return_value=MOCK_REPORTS):
        response = client.get("/reports")
        assert response.status_code == 200


def test_reports_returns_404_when_empty():
    with patch("api.s3.list_objects", return_value=[]):
        response = client.get("/reports")
        assert response.status_code == 404


def test_latest_report_returns_200():
    with patch("api.s3.latest_object", return_value=MOCK_REPORTS[0]):
        with patch("api.s3.download", return_value="report content"):
            response = client.get("/reports/latest")
            assert response.status_code == 200


def test_latest_report_404_when_empty():
    with patch("api.s3.latest_object", return_value=None):
        response = client.get("/reports/latest")
        assert response.status_code == 404


# ── Alarms ───────────────────────────────────────────────

def test_alarms_returns_200():
    with patch("api.monitor.list_alarms", return_value=MOCK_ALARMS):
        response = client.get("/alarms")
        assert response.status_code == 200


def test_alarms_returns_404_when_empty():
    with patch("api.monitor.list_alarms", return_value=[]):
        response = client.get("/alarms")
        assert response.status_code == 404


def test_firing_alarms_returns_200():
    with patch("api.monitor.alarms_in_alarm", return_value=[]):
        response = client.get("/alarms/firing")
        assert response.status_code == 200


# ── Agent ────────────────────────────────────────────────

def test_agent_query_returns_200():
    with patch("api.run_agent", return_value="2 instances running"):
        response = client.post("/agent/query", json={"question": "How many instances are running?"})
        assert response.status_code == 200


def test_agent_query_schema():
    with patch("api.run_agent", return_value="2 instances running"):
        response = client.post("/agent/query", json={"question": "How many instances are running?"})
        data = response.json()
        assert "question" in data
        assert "answer" in data


def test_agent_query_missing_payload():
    response = client.post("/agent/query", json={})
    assert response.status_code == 422


def test_agent_query_handles_exception():
    with patch("api.run_agent", side_effect=Exception("Agent failed")):
        response = client.post("/agent/query", json={"question": "test"})
        assert response.status_code == 500