# infra_monitor.py

import json
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Enable DEBUG logs
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("monitor.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Load configuration with error handling
try:
    with open("config.json", "r") as config_file:
        config = json.load(config_file)

    environment = config["environment"]
    region = config["region"]
    alert_threshold = config["alert_threshold"]

    logging.info(
        f"Configuration loaded successfully "
        f"(Environment: {environment}, Region: {region})"
    )

except FileNotFoundError:
    logging.error("config.json file not found.")
    sys.exit(1)

except json.JSONDecodeError:
    logging.error("Invalid JSON format in config.json.")
    sys.exit(1)

except KeyError as missing_key:
    logging.error(f"Missing required config key: {missing_key}")
    sys.exit(1)

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

# Process instances
for instance in ec2_instances:

    # DEBUG log showing raw instance data
    logging.debug(f"Raw instance data: {instance}")

    instance_id = instance["id"]
    instance_type = instance["type"]
    instance_region = instance["region"]
    cpu = instance["cpu"]
    running = instance["running"]

    # Log ERROR if instance is DOWN
    if not running:
        logging.error(
            f"[DOWN] {instance_id} | "
            f"{instance_type} | "
            f"{instance_region} | "
            f"CPU: {cpu}%"
        )

    # Log WARNING if CPU exceeds threshold
    elif cpu > alert_threshold:
        logging.warning(
            f"[ALERT] {instance_id} | "
            f"{instance_type} | "
            f"{instance_region} | "
            f"CPU: {cpu}% exceeds threshold "
            f"({alert_threshold}%)"
        )

    # Log INFO for healthy instances
    else:
        logging.info(
            f"[HEALTHY] {instance_id} | "
            f"{instance_type} | "
            f"{instance_region} | "
            f"CPU: {cpu}%"
        )

# Infrastructure summary
up = sum(1 for i in ec2_instances if i["running"])
down = sum(1 for i in ec2_instances if not i["running"])
alerts = sum(
    1 for i in ec2_instances
    if i["cpu"] > alert_threshold
)

# Log CRITICAL if more than half are DOWN
if down > len(ec2_instances) / 2:
    logging.critical(
        "CRITICAL: More than half of the instances are DOWN!"
    )

# Final summary log
logging.info(
    f"Script complete — "
    f"{up} UP | "
    f"{down} DOWN | "
    f"{alerts} ALERT"
)