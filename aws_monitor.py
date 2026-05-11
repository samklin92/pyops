import boto3
import logging
import os
import sys
from datetime import datetime, timezone, timedelta
from infra import load_config, EC2Instance, InfraMonitor, S3Reporter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("aws_monitor.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

BUCKET_NAME = "devops-monitor-109804294707"

def get_cpu_utilization(instance_id, region):
    cloudwatch = boto3.client("cloudwatch", region_name=region)
    response = cloudwatch.get_metric_statistics(
        Namespace="AWS/EC2",
        MetricName="CPUUtilization",
        Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
        StartTime=datetime.now(timezone.utc) - timedelta(minutes=10),
        EndTime=datetime.now(timezone.utc),
        Period=300,
        Statistics=["Average"]
    )
    datapoints = response.get("Datapoints", [])
    if not datapoints:
        return 0.0
    latest = sorted(datapoints, key=lambda x: x["Timestamp"])[-1]
    return round(latest["Average"], 2)


def fetch_ec2_instances(region="us-east-1"):
    ec2 = boto3.client("ec2", region_name=region)
    response = ec2.describe_instances()
    instances = []

    for reservation in response["Reservations"]:
        for inst in reservation["Instances"]:
            if inst["State"]["Name"] == "terminated":
                continue
            cpu = get_cpu_utilization(inst["InstanceId"], region)
            instances.append(EC2Instance(
                instance_id=inst["InstanceId"],
                instance_type=inst["InstanceType"],
                region=region,
                running=inst["State"]["Name"] == "running",
                cpu=cpu
            ))
    return instances


def generate_report(monitor):
    lines = []
    lines.append(f"Monitor Report — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    lines.append(f"Environment: {monitor.environment} | Region: {monitor.region}")
    lines.append("-" * 50)

    up = down = alerts = 0

    for instance in monitor.instances:
        status = instance.status()
        health = "OK" if instance.is_healthy(monitor.alert_threshold) else "ALERT"
        lines.append(instance.summarise(monitor.alert_threshold))

        if instance.running:
            up += 1
        else:
            down += 1
        if health == "ALERT":
            alerts += 1

    lines.append("-" * 50)
    lines.append(f"Total: {up} UP | {down} DOWN | {alerts} ALERT")
    return "\n".join(lines)


if __name__ == "__main__":
    region = os.getenv("AWS_REGION", "us-east-1")
    config = load_config("config.json")
    monitor = InfraMonitor(config)

    instances = fetch_ec2_instances(region=region)

    if not instances:
        logging.warning("No instances found in region")
        sys.exit(0)

    for instance in instances:
        monitor.add_instance(instance)

    monitor.run()
    monitor.summary()

    # Generate and upload report to S3
    report_content = generate_report(monitor)
    reporter = S3Reporter(bucket_name=BUCKET_NAME, region=region)
    reporter.upload(report_content)

    # List all reports in bucket
    reports = reporter.list_reports()
    logging.info(f"Total reports in S3: {len(reports)}")


def get_cpu_utilization(instance_id, region):

    cloudwatch = boto3.client(
        "cloudwatch",
        region_name=region
    )

    response = cloudwatch.get_metric_statistics(
        Namespace="AWS/EC2",
        MetricName="CPUUtilization",
        Dimensions=[
            {
                "Name": "InstanceId",
                "Value": instance_id
            }
        ],
        StartTime=datetime.now(timezone.utc)
        - timedelta(minutes=10),
        EndTime=datetime.now(timezone.utc),
        Period=300,
        Statistics=["Average"]
    )

    datapoints = response.get("Datapoints", [])

    if not datapoints:
        return 0.0

    latest = sorted(
        datapoints,
        key=lambda x: x["Timestamp"]
    )[-1]

    return round(latest["Average"], 2)


def fetch_ec2_instances(region="us-east-1"):

    ec2 = boto3.client(
        "ec2",
        region_name=region
    )

    response = ec2.describe_instances()

    instances = []

    for reservation in response["Reservations"]:

        for inst in reservation["Instances"]:

            # Skip terminated instances
            if inst["State"]["Name"] == "terminated":
                continue

            name = "unnamed"

            for tag in inst.get("Tags", []):

                if tag["Key"] == "Name":
                    name = tag["Value"]

            cpu = get_cpu_utilization(
                inst["InstanceId"],
                region
            )

            instances.append(
                EC2Instance(
                    instance_id=inst["InstanceId"],
                    instance_type=inst["InstanceType"],
                    region=region,
                    running=(
                        inst["State"]["Name"]
                        == "running"
                    ),
                    cpu=cpu
                )
            )

    return instances