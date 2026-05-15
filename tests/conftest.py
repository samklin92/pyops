import pytest
from unittest.mock import MagicMock, patch
import sys

# Mock heavy dependencies before any imports
sys.modules["chromadb"] = MagicMock()
sys.modules["chromadb.config"] = MagicMock()
sys.modules["chromadb.Client"] = MagicMock()
sys.modules["langchain"] = MagicMock()
sys.modules["langchain_community"] = MagicMock()
sys.modules["langchain_community.vectorstores"] = MagicMock()
sys.modules["langchain_community.embeddings"] = MagicMock()
sys.modules["langchain_openai"] = MagicMock()
sys.modules["langchain_anthropic"] = MagicMock()
sys.modules["langchain.agents"] = MagicMock()
sys.modules["langchain.tools"] = MagicMock()


# ── Shared fixtures ───────────────────────────────────────

@pytest.fixture
def mock_ec2_instance():
    return {
        "id": "i-0abc123def456",
        "name": "test-instance",
        "type": "t2.micro",
        "state": "running",
        "region": "us-east-1",
        "launch_time": "2026-05-13T12:00:00+00:00"
    }


@pytest.fixture
def mock_report():
    return {
        "key": "reports/report-2026-05-13.txt",
        "size_kb": 2.4,
        "last_modified": "2026-05-13T12:00:00+00:00"
    }


@pytest.fixture
def mock_alarm():
    return {
        "name": "pyops-cpu-high",
        "state": "OK",
        "metric": "CPUUtilization",
        "threshold": 80.0,
        "updated": "2026-05-13T12:00:00+00:00"
    }