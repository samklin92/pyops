import boto3

ec2 = boto3.client("ec2", region_name="us-east-1")

instance_id = "i-004d5cc32c15cf16d"

response = ec2.terminate_instances(InstanceIds=[instance_id])

state = response["TerminatingInstances"][0]["CurrentState"]["Name"]
print(f"Instance {instance_id} state: {state}")