#!/usr/bin/env python3
import argparse
import json
import logging
import os
import sys

from infra import load_config
from toolkit import EC2Toolkit, S3Toolkit, IAMToolkit, MonitorToolkit

logging.basicConfig(level=logging.WARNING, format="%(levelname)s | %(message)s")

config = load_config("config.json")
REGION = os.getenv("AWS_REGION", config["region"])
BUCKET = config["s3_bucket"]

ec2 = EC2Toolkit(region=REGION)
s3 = S3Toolkit(bucket_name=BUCKET, region=REGION)
iam = IAMToolkit()
monitor = MonitorToolkit(region=REGION)


def print_json(data):
    print(json.dumps(data, indent=2, default=str))


def cmd_ec2_list(args):
    instances = ec2.list_instances(state=args.state)
    if not instances:
        print("No instances found.")
        return
    print_json(instances)


def cmd_ec2_stop(args):
    result = ec2.stop_instance(args.instance_id)
    print_json(result)


def cmd_ec2_start(args):
    result = ec2.start_instance(args.instance_id)
    print_json(result)


def cmd_ec2_state(args):
    result = ec2.get_instance_state(args.instance_id)
    print_json(result)


def cmd_s3_list(args):
    objects = s3.list_objects(prefix=args.prefix)
    if not objects:
        print("No objects found.")
        return
    print_json(objects)


def cmd_s3_upload(args):
    with open(args.file, "r") as f:
        content = f.read()
    result = s3.upload(content, key=args.key)
    print_json(result)


def cmd_s3_download(args):
    content = s3.download(args.key)
    print(content)


def cmd_s3_delete(args):
    result = s3.delete(args.key)
    print_json(result)


def cmd_iam_users(args):
    users = iam.list_users()
    print_json(users)


def cmd_iam_roles(args):
    roles = iam.list_roles()
    print_json(roles)


def cmd_iam_policies(args):
    policies = iam.list_attached_policies(args.role)
    print_json(policies)


def cmd_monitor_cpu(args):
    result = monitor.get_ec2_cpu(args.instance_id, minutes=args.minutes)
    print_json(result)


def cmd_monitor_alarms(args):
    alarms = monitor.list_alarms(state=args.state)
    if not alarms:
        print("No alarms found.")
        return
    print_json(alarms)


def cmd_monitor_firing(args):
    alarms = monitor.alarms_in_alarm()
    if not alarms:
        print("All alarms OK.")
        return
    print_json(alarms)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="pyops",
        description="PyOps CLI — AWS infrastructure automation toolkit"
    )
    subparsers = parser.add_subparsers(dest="service", required=True)

    # EC2
    ec2_parser = subparsers.add_parser("ec2", help="EC2 operations")
    ec2_sub = ec2_parser.add_subparsers(dest="command", required=True)

    ec2_list = ec2_sub.add_parser("list", help="List EC2 instances")
    ec2_list.add_argument("--state", choices=["running", "stopped", "pending"], help="Filter by state")
    ec2_list.set_defaults(func=cmd_ec2_list)

    ec2_stop = ec2_sub.add_parser("stop", help="Stop an EC2 instance")
    ec2_stop.add_argument("instance_id", help="Instance ID to stop")
    ec2_stop.set_defaults(func=cmd_ec2_stop)

    ec2_start = ec2_sub.add_parser("start", help="Start an EC2 instance")
    ec2_start.add_argument("instance_id", help="Instance ID to start")
    ec2_start.set_defaults(func=cmd_ec2_start)

    ec2_state = ec2_sub.add_parser("state", help="Get instance state")
    ec2_state.add_argument("instance_id", help="Instance ID")
    ec2_state.set_defaults(func=cmd_ec2_state)

    # S3
    s3_parser = subparsers.add_parser("s3", help="S3 operations")
    s3_sub = s3_parser.add_subparsers(dest="command", required=True)

    s3_list = s3_sub.add_parser("list", help="List S3 objects")
    s3_list.add_argument("--prefix", default="", help="Filter by prefix")
    s3_list.set_defaults(func=cmd_s3_list)

    s3_upload = s3_sub.add_parser("upload", help="Upload a file to S3")
    s3_upload.add_argument("file", help="Local file path to upload")
    s3_upload.add_argument("--key", default=None, help="S3 key (auto-generated if not provided)")
    s3_upload.set_defaults(func=cmd_s3_upload)

    s3_download = s3_sub.add_parser("download", help="Download an S3 object")
    s3_download.add_argument("key", help="S3 object key")
    s3_download.set_defaults(func=cmd_s3_download)

    s3_delete = s3_sub.add_parser("delete", help="Delete an S3 object")
    s3_delete.add_argument("key", help="S3 object key to delete")
    s3_delete.set_defaults(func=cmd_s3_delete)

    # IAM
    iam_parser = subparsers.add_parser("iam", help="IAM operations")
    iam_sub = iam_parser.add_subparsers(dest="command", required=True)

    iam_sub.add_parser("users", help="List IAM users").set_defaults(func=cmd_iam_users)
    iam_sub.add_parser("roles", help="List IAM roles").set_defaults(func=cmd_iam_roles)

    iam_policies = iam_sub.add_parser("policies", help="List policies attached to a role")
    iam_policies.add_argument("role", help="Role name")
    iam_policies.set_defaults(func=cmd_iam_policies)

    # Monitor
    mon_parser = subparsers.add_parser("monitor", help="CloudWatch operations")
    mon_sub = mon_parser.add_subparsers(dest="command", required=True)

    mon_cpu = mon_sub.add_parser("cpu", help="Get EC2 CPU utilization")
    mon_cpu.add_argument("instance_id", help="Instance ID")
    mon_cpu.add_argument("--minutes", type=int, default=10, help="Lookback window in minutes")
    mon_cpu.set_defaults(func=cmd_monitor_cpu)

    mon_alarms = mon_sub.add_parser("alarms", help="List CloudWatch alarms")
    mon_alarms.add_argument("--state", choices=["OK", "ALARM", "INSUFFICIENT_DATA"], help="Filter by state")
    mon_alarms.set_defaults(func=cmd_monitor_alarms)

    mon_sub.add_parser("firing", help="List alarms in ALARM state").set_defaults(func=cmd_monitor_firing)

    return parser


def main():
    parser = build_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stdout)
        sys.stdout.flush()
        sys.exit(0)
    args = parser.parse_args()
    try:
        args.func(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.stderr.flush()
        sys.exit(1)


if __name__ == "__main__":
    main()