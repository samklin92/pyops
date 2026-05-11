# infra_report.py

import json
import os

# Read configuration from config.json
with open("config.json", "r") as config_file:
    config = json.load(config_file)

environment = config["environment"]
region = config["region"]
alert_threshold = config["alert_threshold"]

# Read OPERATOR environment variable
operator = os.getenv("OPERATOR", "unknown")

# EC2 instances list
ec2_instances = [
    {
        "id": "i-0abc123",
        "type": "t3.micro",
        "region": "us-east-1",
        "running": True,
        "cpu": 82
    },
    {
        "id": "i-0def456",
        "type": "t3.large",
        "region": "us-west-2",
        "running": True,
        "cpu": 45
    },
    {
        "id": "i-0ghi789",
        "type": "t3.medium",
        "region": "eu-west-1",
        "running": False,
        "cpu": 91
    },
    {
        "id": "i-0jkl012",
        "type": "t3.small",
        "region": "ap-southeast-1",
        "running": True,
        "cpu": 60
    }
]

# Counters
up_count = 0
down_count = 0
alert_count = 0

# Create report
with open("report.txt", "w") as report:

    report.write(f"Operator: {operator}\n")
    report.write(
        f"Environment: {environment} | Region: {region}\n"
    )
    report.write("------------------------------------\n")

    # Process instances
    for instance in ec2_instances:

        status = "[UP]" if instance["running"] else "[DOWN]"

        health = (
            "ALERT"
            if instance["cpu"] > alert_threshold
            else "OK"
        )

        # Count UP/DOWN states
        if instance["running"]:
            up_count += 1
        else:
            down_count += 1

        # Count ALERT states
        if health == "ALERT":
            alert_count += 1

        # Write instance details
        report.write(
            f"{status:<7}"
            f"{instance['id']} | "
            f"{instance['type']} | "
            f"{instance['region']} | "
            f"CPU: {instance['cpu']}% | "
            f"{health}\n"
        )

    report.write("------------------------------------\n")
    report.write(
        f"Total: {up_count} UP | {down_count} DOWN\n"
    )
    report.write(
        f"Instances in ALERT state: {alert_count}\n"
    )

print("Report generated successfully: report.txt")