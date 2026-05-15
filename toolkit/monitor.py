import boto3
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


class MonitorToolkit:

    def __init__(self, region="us-east-1"):
        self.region = region
        self.cloudwatch = boto3.client("cloudwatch", region_name=region)

    def get_ec2_cpu(self, instance_id, minutes=10):
        """Get average CPU utilization for an EC2 instance."""
        response = self.cloudwatch.get_metric_statistics(
            Namespace="AWS/EC2",
            MetricName="CPUUtilization",
            Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
            StartTime=datetime.now(timezone.utc) - timedelta(minutes=minutes),
            EndTime=datetime.now(timezone.utc),
            Period=minutes * 60,
            Statistics=["Average"]
        )
        datapoints = response.get("Datapoints", [])
        if not datapoints:
            return {"instance_id": instance_id, "cpu": 0.0, "datapoints": 0}
        latest = sorted(datapoints, key=lambda x: x["Timestamp"])[-1]
        return {
            "instance_id": instance_id,
            "cpu": round(latest["Average"], 2),
            "datapoints": len(datapoints)
        }

    def list_alarms(self, state=None):
        """List CloudWatch alarms, optionally filtered by state."""
        params = {}
        if state:
            params["StateValue"] = state
        response = self.cloudwatch.describe_alarms(**params)
        alarms = [
            {
                "name": a["AlarmName"],
                "state": a["StateValue"],
                "metric": a["MetricName"],
                "threshold": a["Threshold"],
                "updated": a["StateUpdatedTimestamp"].isoformat()
            }
            for a in response["MetricAlarms"]
        ]
        logger.info(f"Found {len(alarms)} alarms")
        return alarms

    def alarms_in_alarm(self):
        """Return only alarms currently in ALARM state."""
        return self.list_alarms(state="ALARM")