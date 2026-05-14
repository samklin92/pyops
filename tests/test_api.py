import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from api import app

client = TestClient(app)


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

MOCK_INSTANCES = [
    {
        "id": "i-0abc123",
        "type": "t2.micro",
        "region": "us-east-1",
        "running": True,
        "cpu": 12.5,
        "status": "[UP]"
    }
]


def test_instances_returns_200():
    with patch("api.fetch_ec2_instances", return_value=MOCK_INSTANCES):
        response = client.get("/instances")
        assert response.status_code == 200


def test_instances_schema():
    with patch("api.fetch_ec2_instances", return_value=MOCK_INSTANCES):
        response = client.get("/instances")
        data = response.json()
        assert "count" in data
        assert "instances" in data
        assert data["count"] == 1


def test_instances_returns_404_when_empty():
    with patch("api.fetch_ec2_instances", return_value=[]):
        response = client.get("/instances")
        assert response.status_code == 404


# ── Reports ──────────────────────────────────────────────

MOCK_REPORTS = [
    {"key": "report-2026-05-13.txt", "last_modified": "2026-05-13T12:00:00"}
]


def test_reports_returns_200():
    with patch("api.S3Reporter") as MockReporter:
        MockReporter.return_value.list_reports.return_value = MOCK_REPORTS
        response = client.get("/reports")
        assert response.status_code == 200


def test_reports_schema():
    with patch("api.S3Reporter") as MockReporter:
        MockReporter.return_value.list_reports.return_value = MOCK_REPORTS
        response = client.get("/reports")
        data = response.json()
        assert "count" in data
        assert data["count"] == 1


def test_reports_returns_404_when_empty():
    with patch("api.S3Reporter") as MockReporter:
        MockReporter.return_value.list_reports.return_value = []
        response = client.get("/reports")
        assert response.status_code == 404


# ── Latest report ────────────────────────────────────────

def test_latest_report_returns_200():
    with patch("api.S3Reporter") as MockReporter:
        MockReporter.return_value.list_reports.return_value = MOCK_REPORTS
        MockReporter.return_value.download.return_value = "report content"
        response = client.get("/reports/latest")
        assert response.status_code == 200


def test_latest_report_schema():
    with patch("api.S3Reporter") as MockReporter:
        MockReporter.return_value.list_reports.return_value = MOCK_REPORTS
        MockReporter.return_value.download.return_value = "report content"
        response = client.get("/reports/latest")
        data = response.json()
        assert "key" in data
        assert "content" in data


def test_latest_report_404_when_empty():
    with patch("api.S3Reporter") as MockReporter:
        MockReporter.return_value.list_reports.return_value = []
        response = client.get("/reports/latest")
        assert response.status_code == 404


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