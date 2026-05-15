import boto3
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


class EC2Toolkit:

    def __init__(self, region="us-east-1"):
        self.region = region
        self.client = boto3.client("ec2", region_name=region)

    def list_instances(self, state=None):
        """List all instances, optionally filtered by state."""
        response = self.client.describe_instances()
        instances = []

        for reservation in response["Reservations"]:
            for inst in reservation["Instances"]:
                current_state = inst["State"]["Name"]
                if current_state == "terminated":
                    continue
                if state and current_state != state:
                    continue

                name = next(
                    (tag["Value"] for tag in inst.get("Tags", []) if tag["Key"] == "Name"),
                    "unnamed"
                )

                instances.append({
                    "id": inst["InstanceId"],
                    "name": name,
                    "type": inst["InstanceType"],
                    "state": current_state,
                    "region": self.region,
                    "launch_time": inst["LaunchTime"].isoformat()
                })

        logger.info(f"Found {len(instances)} instances in {self.region}")
        return instances

    def stop_instance(self, instance_id):
        """Stop a running EC2 instance."""
        try:
            self.client.stop_instances(InstanceIds=[instance_id])
            logger.info(f"Stop initiated for {instance_id}")
            return {"instance_id": instance_id, "action": "stop", "status": "initiated"}
        except Exception as e:
            logger.error(f"Failed to stop {instance_id}: {e}")
            raise

    def start_instance(self, instance_id):
        """Start a stopped EC2 instance."""
        try:
            self.client.start_instances(InstanceIds=[instance_id])
            logger.info(f"Start initiated for {instance_id}")
            return {"instance_id": instance_id, "action": "start", "status": "initiated"}
        except Exception as e:
            logger.error(f"Failed to start {instance_id}: {e}")
            raise

    def get_instance_state(self, instance_id):
        """Get current state of a specific instance."""
        response = self.client.describe_instances(InstanceIds=[instance_id])
        inst = response["Reservations"][0]["Instances"][0]
        return {
            "instance_id": instance_id,
            "state": inst["State"]["Name"],
            "type": inst["InstanceType"]
        }

    def list_running(self):
        """Shortcut — return only running instances."""
        return self.list_instances(state="running")

    def list_stopped(self):
        """Shortcut — return only stopped instances."""
        return self.list_instances(state="stopped")