import boto3

ec2 = boto3.client("ec2", region_name="us-east-1")

response = ec2.run_instances(
    ImageId="ami-0c02fb55956c7d316",  # Amazon Linux 2 — us-east-1
    InstanceType="t2.micro",
    MinCount=1,
    MaxCount=1,
    TagSpecifications=[
        {
            "ResourceType": "instance",
            "Tags": [
                {"Key": "Name", "Value": "devops-test-1"},
                {"Key": "Environment", "Value": "dev"}
            ]
        }
    ]
)

instance_id = response["Instances"][0]["InstanceId"]
print(f"Launched instance: {instance_id}")