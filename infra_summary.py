# infra_summary.py

# List of EC2 instances
ec2_instances = [
    {
        "id": "i-0a12b34c56d78e90",
        "type": "t2.micro",
        "region": "us-east-1",
        "running": True
    },
    {
        "id": "i-1b23c45d67e89f01",
        "type": "t3.medium",
        "region": "eu-west-1",
        "running": False
    },
    {
        "id": "i-2c34d56e78f90g12",
        "type": "m5.large",
        "region": "ap-southeast-1",
        "running": True
    },
    {
        "id": "i-3d45e67f89g01h23",
        "type": "c5.xlarge",
        "region": "us-west-2",
        "running": False
    }
]

# Function to summarize an EC2 instance
def summarise_instance(instance):
    status = "[UP]" if instance["running"] else "[DOWN]"

    return (
        f"{status} "
        f"{instance['id']} | "
        f"{instance['type']} | "
        f"{instance['region']}"
    )

# Counters
up_count = 0
down_count = 0

# Loop through the instances and print summaries
for instance in ec2_instances:
    print(summarise_instance(instance))

    if instance["running"]:
        up_count += 1
    else:
        down_count += 1

# Print final counts
print("\nInfrastructure Status Summary")
print(f"UP instances: {up_count}")
print(f"DOWN instances: {down_count}")