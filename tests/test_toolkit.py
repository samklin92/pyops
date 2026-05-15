import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone


# ── EC2Toolkit ────────────────────────────────────────────

class TestEC2Toolkit:

    @patch("toolkit.ec2.boto3")
    def test_list_instances_returns_list(self, mock_boto3):
        from toolkit.ec2 import EC2Toolkit
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.describe_instances.return_value = {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-0abc123",
                            "InstanceType": "t2.micro",
                            "State": {"Name": "running"},
                            "LaunchTime": datetime(2026, 5, 13, tzinfo=timezone.utc),
                            "Tags": [{"Key": "Name", "Value": "web-server"}]
                        }
                    ]
                }
            ]
        }
        toolkit = EC2Toolkit()
        result = toolkit.list_instances()
        assert len(result) == 1
        assert result[0]["id"] == "i-0abc123"
        assert result[0]["name"] == "web-server"

    @patch("toolkit.ec2.boto3")
    def test_list_instances_skips_terminated(self, mock_boto3):
        from toolkit.ec2 import EC2Toolkit
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.describe_instances.return_value = {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-terminated",
                            "InstanceType": "t2.micro",
                            "State": {"Name": "terminated"},
                            "LaunchTime": datetime(2026, 5, 13, tzinfo=timezone.utc),
                            "Tags": []
                        }
                    ]
                }
            ]
        }
        toolkit = EC2Toolkit()
        result = toolkit.list_instances()
        assert len(result) == 0

    @patch("toolkit.ec2.boto3")
    def test_stop_instance_returns_action(self, mock_boto3):
        from toolkit.ec2 import EC2Toolkit
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        toolkit = EC2Toolkit()
        result = toolkit.stop_instance("i-0abc123")
        assert result["action"] == "stop"
        assert result["status"] == "initiated"
        mock_client.stop_instances.assert_called_once_with(InstanceIds=["i-0abc123"])

    @patch("toolkit.ec2.boto3")
    def test_start_instance_returns_action(self, mock_boto3):
        from toolkit.ec2 import EC2Toolkit
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        toolkit = EC2Toolkit()
        result = toolkit.start_instance("i-0abc123")
        assert result["action"] == "start"
        assert result["status"] == "initiated"
        mock_client.start_instances.assert_called_once_with(InstanceIds=["i-0abc123"])

    @patch("toolkit.ec2.boto3")
    def test_list_running_filters_by_state(self, mock_boto3):
        from toolkit.ec2 import EC2Toolkit
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.describe_instances.return_value = {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-running",
                            "InstanceType": "t2.micro",
                            "State": {"Name": "running"},
                            "LaunchTime": datetime(2026, 5, 13, tzinfo=timezone.utc),
                            "Tags": []
                        },
                        {
                            "InstanceId": "i-stopped",
                            "InstanceType": "t2.micro",
                            "State": {"Name": "stopped"},
                            "LaunchTime": datetime(2026, 5, 13, tzinfo=timezone.utc),
                            "Tags": []
                        }
                    ]
                }
            ]
        }
        toolkit = EC2Toolkit()
        result = toolkit.list_running()
        assert len(result) == 1
        assert result[0]["id"] == "i-running"


# ── S3Toolkit ─────────────────────────────────────────────

class TestS3Toolkit:

    @patch("toolkit.s3.boto3")
    def test_upload_returns_key(self, mock_boto3):
        from toolkit.s3 import S3Toolkit
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        toolkit = S3Toolkit(bucket_name="test-bucket")
        result = toolkit.upload("report content", key="reports/test.txt")
        assert result["key"] == "reports/test.txt"
        assert result["bucket"] == "test-bucket"
        mock_client.put_object.assert_called_once()

    @patch("toolkit.s3.boto3")
    def test_upload_autogenerates_key(self, mock_boto3):
        from toolkit.s3 import S3Toolkit
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        toolkit = S3Toolkit(bucket_name="test-bucket")
        result = toolkit.upload("report content")
        assert "reports/report-" in result["key"]

    @patch("toolkit.s3.boto3")
    def test_download_returns_content(self, mock_boto3):
        from toolkit.s3 import S3Toolkit
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.get_object.return_value = {
            "Body": MagicMock(read=lambda: b"report content")
        }
        toolkit = S3Toolkit(bucket_name="test-bucket")
        result = toolkit.download("reports/test.txt")
        assert result == "report content"

    @patch("toolkit.s3.boto3")
    def test_list_objects_returns_list(self, mock_boto3):
        from toolkit.s3 import S3Toolkit
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.list_objects_v2.return_value = {
            "Contents": [
                {
                    "Key": "reports/test.txt",
                    "Size": 1024,
                    "LastModified": datetime(2026, 5, 13, tzinfo=timezone.utc)
                }
            ]
        }
        toolkit = S3Toolkit(bucket_name="test-bucket")
        result = toolkit.list_objects()
        assert len(result) == 1
        assert result[0]["key"] == "reports/test.txt"
        assert result[0]["size_kb"] == 1.0

    @patch("toolkit.s3.boto3")
    def test_delete_returns_confirmation(self, mock_boto3):
        from toolkit.s3 import S3Toolkit
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        toolkit = S3Toolkit(bucket_name="test-bucket")
        result = toolkit.delete("reports/test.txt")
        assert result["action"] == "deleted"
        assert result["key"] == "reports/test.txt"
        mock_client.delete_object.assert_called_once()

    @patch("toolkit.s3.boto3")
    def test_latest_object_returns_most_recent(self, mock_boto3):
        from toolkit.s3 import S3Toolkit
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.list_objects_v2.return_value = {
            "Contents": [
                {
                    "Key": "reports/old.txt",
                    "Size": 512,
                    "LastModified": datetime(2026, 5, 1, tzinfo=timezone.utc)
                },
                {
                    "Key": "reports/new.txt",
                    "Size": 1024,
                    "LastModified": datetime(2026, 5, 13, tzinfo=timezone.utc)
                }
            ]
        }
        toolkit = S3Toolkit(bucket_name="test-bucket")
        result = toolkit.latest_object()
        assert result["key"] == "reports/new.txt"


# ── IAMToolkit ────────────────────────────────────────────

class TestIAMToolkit:

    @patch("toolkit.iam.boto3")
    def test_list_users_returns_list(self, mock_boto3):
        from toolkit.iam import IAMToolkit
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.list_users.return_value = {
            "Users": [
                {
                    "UserName": "devops-admin",
                    "UserId": "AIDAEXAMPLE",
                    "CreateDate": datetime(2026, 1, 1, tzinfo=timezone.utc),
                    "Arn": "arn:aws:iam::123456789:user/devops-admin"
                }
            ]
        }
        toolkit = IAMToolkit()
        result = toolkit.list_users()
        assert len(result) == 1
        assert result[0]["username"] == "devops-admin"

    @patch("toolkit.iam.boto3")
    def test_list_roles_returns_list(self, mock_boto3):
        from toolkit.iam import IAMToolkit
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.list_roles.return_value = {
            "Roles": [
                {
                    "RoleName": "ecsTaskExecutionRole",
                    "RoleId": "AROAEXAMPLE",
                    "CreateDate": datetime(2026, 1, 1, tzinfo=timezone.utc),
                    "Arn": "arn:aws:iam::123456789:role/ecsTaskExecutionRole"
                }
            ]
        }
        toolkit = IAMToolkit()
        result = toolkit.list_roles()
        assert len(result) == 1
        assert result[0]["name"] == "ecsTaskExecutionRole"

    @patch("toolkit.iam.boto3")
    def test_list_attached_policies(self, mock_boto3):
        from toolkit.iam import IAMToolkit
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.list_attached_role_policies.return_value = {
            "AttachedPolicies": [
                {
                    "PolicyName": "AmazonECSTaskExecutionRolePolicy",
                    "PolicyArn": "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
                }
            ]
        }
        toolkit = IAMToolkit()
        result = toolkit.list_attached_policies("ecsTaskExecutionRole")
        assert len(result) == 1
        assert result[0]["name"] == "AmazonECSTaskExecutionRolePolicy"


# ── MonitorToolkit ────────────────────────────────────────

class TestMonitorToolkit:

    @patch("toolkit.monitor.boto3")
    def test_get_ec2_cpu_returns_metric(self, mock_boto3):
        from toolkit.monitor import MonitorToolkit
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.get_metric_statistics.return_value = {
            "Datapoints": [
                {
                    "Average": 45.5,
                    "Timestamp": datetime(2026, 5, 13, 12, 0, tzinfo=timezone.utc)
                }
            ]
        }
        toolkit = MonitorToolkit()
        result = toolkit.get_ec2_cpu("i-0abc123")
        assert result["cpu"] == 45.5
        assert result["instance_id"] == "i-0abc123"

    @patch("toolkit.monitor.boto3")
    def test_get_ec2_cpu_no_datapoints(self, mock_boto3):
        from toolkit.monitor import MonitorToolkit
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.get_metric_statistics.return_value = {"Datapoints": []}
        toolkit = MonitorToolkit()
        result = toolkit.get_ec2_cpu("i-0abc123")
        assert result["cpu"] == 0.0
        assert result["datapoints"] == 0

    @patch("toolkit.monitor.boto3")
    def test_list_alarms_returns_list(self, mock_boto3):
        from toolkit.monitor import MonitorToolkit
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.describe_alarms.return_value = {
            "MetricAlarms": [
                {
                    "AlarmName": "pyops-cpu-high",
                    "StateValue": "OK",
                    "MetricName": "CPUUtilization",
                    "Threshold": 80.0,
                    "StateUpdatedTimestamp": datetime(2026, 5, 13, tzinfo=timezone.utc)
                }
            ]
        }
        toolkit = MonitorToolkit()
        result = toolkit.list_alarms()
        assert len(result) == 1
        assert result[0]["name"] == "pyops-cpu-high"
        assert result[0]["state"] == "OK"

    @patch("toolkit.monitor.boto3")
    def test_alarms_in_alarm_filters_state(self, mock_boto3):
        from toolkit.monitor import MonitorToolkit
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.describe_alarms.return_value = {"MetricAlarms": []}
        toolkit = MonitorToolkit()
        result = toolkit.alarms_in_alarm()
        mock_client.describe_alarms.assert_called_with(StateValue="ALARM")
        assert result == []

        # ── EC2Toolkit error handling ─────────────────────────────

    @patch("toolkit.ec2.boto3")
    def test_stop_instance_raises_on_error(self, mock_boto3):
        from toolkit.ec2 import EC2Toolkit
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.stop_instances.side_effect = Exception("AWS error")
        toolkit = EC2Toolkit()
        with pytest.raises(Exception, match="AWS error"):
            toolkit.stop_instance("i-0abc123")

    @patch("toolkit.ec2.boto3")
    def test_start_instance_raises_on_error(self, mock_boto3):
        from toolkit.ec2 import EC2Toolkit
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.start_instances.side_effect = Exception("AWS error")
        toolkit = EC2Toolkit()
        with pytest.raises(Exception, match="AWS error"):
            toolkit.start_instance("i-0abc123")

    @patch("toolkit.ec2.boto3")
    def test_get_instance_state_returns_state(self, mock_boto3):
        from toolkit.ec2 import EC2Toolkit
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"State": {"Name": "running"}, "InstanceType": "t2.micro"}]}]
        }
        toolkit = EC2Toolkit()
        result = toolkit.get_instance_state("i-0abc123")
        assert result["state"] == "running"
        assert result["instance_id"] == "i-0abc123"


# ── S3Toolkit error handling ──────────────────────────────

    @patch("toolkit.s3.boto3")
    def test_download_raises_on_error(self, mock_boto3):
        from toolkit.s3 import S3Toolkit
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.get_object.side_effect = Exception("S3 error")
        toolkit = S3Toolkit(bucket_name="test-bucket")
        with pytest.raises(Exception, match="S3 error"):
            toolkit.download("reports/missing.txt")

    @patch("toolkit.s3.boto3")
    def test_delete_raises_on_error(self, mock_boto3):
        from toolkit.s3 import S3Toolkit
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.delete_object.side_effect = Exception("S3 error")
        toolkit = S3Toolkit(bucket_name="test-bucket")
        with pytest.raises(Exception, match="S3 error"):
            toolkit.delete("reports/missing.txt")

    @patch("toolkit.s3.boto3")
    def test_latest_object_returns_none_when_empty(self, mock_boto3):
        from toolkit.s3 import S3Toolkit
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.list_objects_v2.return_value = {"Contents": []}
        toolkit = S3Toolkit(bucket_name="test-bucket")
        result = toolkit.latest_object()
        assert result is None


# ── IAMToolkit — get_user ─────────────────────────────────

    @patch("toolkit.iam.boto3")
    def test_get_user_returns_user(self, mock_boto3):
        from toolkit.iam import IAMToolkit
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.get_user.return_value = {
            "User": {
                "UserName": "devops-admin",
                "UserId": "AIDAEXAMPLE",
                "CreateDate": datetime(2026, 1, 1, tzinfo=timezone.utc),
                "Arn": "arn:aws:iam::123456789:user/devops-admin"
            }
        }
        toolkit = IAMToolkit()
        result = toolkit.get_user("devops-admin")
        assert result["username"] == "devops-admin"

    @patch("toolkit.iam.boto3")
    def test_get_user_raises_on_error(self, mock_boto3):
        from toolkit.iam import IAMToolkit
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.get_user.side_effect = Exception("User not found")
        toolkit = IAMToolkit()
        with pytest.raises(Exception, match="User not found"):
            toolkit.get_user("nonexistent")


# ── API agent exception path ──────────────────────────────

    def test_agent_query_handles_exception(self):
        with patch("api.run_agent", side_effect=Exception("Agent failed")):
            from fastapi.testclient import TestClient
            from api import app
            client = TestClient(app)
            response = client.post("/agent/query", json={"question": "test"})
            assert response.status_code == 500