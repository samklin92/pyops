import boto3

ec2 = boto3.client("ec2", region_name="us-east-1")

response = ec2.describe_instances()

for reservation in response["Reservations"]:
    for instance in reservation["Instances"]:
        instance_id = instance["InstanceId"]
        instance_type = instance["InstanceType"]
        state = instance["State"]["Name"]
        region = "us-east-1"

        # Get Name tag if it exists
        name = "unnamed"
        for tag in instance.get("Tags", []):
            if tag["Key"] == "Name":
                name = tag["Value"]

        print(f"{instance_id} | {instance_type} | {state} | {name}")