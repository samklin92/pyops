import json
import boto3
import anthropic
from datetime import datetime, timedelta, timezone
from infra import load_config
from infra.reporter import S3Reporter
from rag_pipeline import load_runbooks, index_runbooks, search_runbooks

# Load and index runbooks at startup
docs = load_runbooks()
index_runbooks(docs)

# Tool definitions
tools = [
    {
        "name": "get_ec2_instances",
        "description": "Fetches real EC2 instance data from AWS including instance ID, type, region, and running state.",
        "input_schema": {
            "type": "object",
            "properties": {
                "region": {
                    "type": "string",
                    "description": "AWS region to query, e.g. us-east-1"
                }
            },
            "required": ["region"]
        }
    },
    {
        "name": "get_cloudwatch_cpu",
        "description": "Fetches real CPU utilization for a specific EC2 instance from CloudWatch over the last 10 minutes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "instance_id": {
                    "type": "string",
                    "description": "The EC2 instance ID to query"
                },
                "region": {
                    "type": "string",
                    "description": "AWS region, e.g. us-east-1"
                }
            },
            "required": ["instance_id", "region"]
        }
    },
    {
        "name": "analyse_instance",
        "description": "Analyses a specific EC2 instance and returns health status and recommended action based on CPU utilization.",
        "input_schema": {
            "type": "object",
            "properties": {
                "instance_id": {
                    "type": "string",
                    "description": "The EC2 instance ID to analyse"
                },
                "cpu": {
                    "type": "number",
                    "description": "Current CPU utilization percentage"
                },
                "threshold": {
                    "type": "number",
                    "description": "Alert threshold percentage"
                }
            },
            "required": ["instance_id", "cpu", "threshold"]
        }
    },
    {
        "name": "search_runbooks",
        "description": "Searches the operations runbook knowledge base for relevant procedures and recommendations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant runbooks"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "save_report",
        "description": "Saves the final infrastructure analysis report to S3 for audit and record keeping.",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The report content to save"
                },
                "bucket": {
                    "type": "string",
                    "description": "S3 bucket name to save the report to"
                }
            },
            "required": ["content", "bucket"]
        }
    }
]


def get_ec2_instances(region="us-east-1"):
    """Fetch real EC2 instances from AWS."""
    try:
        ec2 = boto3.client("ec2", region_name=region)
        response = ec2.describe_instances()
        instances = []

        for reservation in response["Reservations"]:
            for inst in reservation["Instances"]:
                if inst["State"]["Name"] == "terminated":
                    continue
                instances.append({
                    "id": inst["InstanceId"],
                    "type": inst["InstanceType"],
                    "region": region,
                    "running": inst["State"]["Name"] == "running",
                    "state": inst["State"]["Name"]
                })

        if not instances:
            return {"instances": [], "message": "No instances found in region"}

        return {"instances": instances, "count": len(instances)}

    except Exception as e:
        return {"error": str(e)}


def get_cloudwatch_cpu(instance_id, region="us-east-1"):
    """Fetch real CPU utilization from CloudWatch."""
    try:
        cw = boto3.client("cloudwatch", region_name=region)
        response = cw.get_metric_statistics(
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
            return {
                "instance_id": instance_id,
                "cpu": None,
                "message": "No CloudWatch data available — instance may be new or stopped"
            }

        latest = sorted(datapoints, key=lambda x: x["Timestamp"])[-1]
        return {
            "instance_id": instance_id,
            "cpu": round(latest["Average"], 2),
            "timestamp": latest["Timestamp"].isoformat()
        }

    except Exception as e:
        return {"error": str(e)}


def analyse_instance(instance_id, cpu, threshold=75):
    """Analyse a single instance health."""
    if cpu is None:
        return {
            "instance_id": instance_id,
            "status": "UNKNOWN",
            "recommended_action": "No CPU data available — verify CloudWatch agent is running"
        }

    if cpu > 90:
        status = "CRITICAL"
        action = "Immediate scaling required"
    elif cpu > threshold:
        status = "WARNING"
        action = "Monitor closely and prepare to scale"
    else:
        status = "OK"
        action = "No action required"

    return {
        "instance_id": instance_id,
        "cpu": cpu,
        "threshold": threshold,
        "status": status,
        "recommended_action": action
    }


def save_report(content, bucket):
    """Save report to S3 using S3Reporter."""
    try:
        reporter = S3Reporter(bucket_name=bucket)
        key = reporter.upload(content)
        return {
            "success": True,
            "s3_key": key,
            "bucket": bucket
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def execute_tool(tool_name, tool_input):
    """Route tool calls to the correct function."""
    if tool_name == "get_ec2_instances":
        return get_ec2_instances(tool_input.get("region", "us-east-1"))

    elif tool_name == "get_cloudwatch_cpu":
        return get_cloudwatch_cpu(
            tool_input["instance_id"],
            tool_input.get("region", "us-east-1")
        )

    elif tool_name == "analyse_instance":
        return analyse_instance(
            tool_input["instance_id"],
            tool_input["cpu"],
            tool_input.get("threshold", 75)
        )

    elif tool_name == "search_runbooks":
        results = search_runbooks(tool_input["query"])
        return {"runbooks": results}

    elif tool_name == "save_report":
        return save_report(
            tool_input["content"],
            tool_input["bucket"]
        )

    else:
        return {"error": f"Unknown tool: {tool_name}"}


def run_agent(instruction):
    """Run the AI agent with tool calling."""
    client = anthropic.Anthropic()
    config = load_config("config.json")

    print(f"\n{'='*50}")
    print(f"Agent Instruction: {instruction}")
    print(f"{'='*50}\n")

    messages = [{"role": "user", "content": instruction}]

    system_prompt = """You are an expert DevOps AI agent with access to tools.
When given an infrastructure analysis task:
1. Use get_ec2_instances to fetch current AWS instance data
2. For each running instance, use get_cloudwatch_cpu to fetch real CPU metrics
3. Use analyse_instance to assess health status for each instance with CPU data
4. Use search_runbooks to find relevant procedures for any issues found
5. Use save_report to persist the final report to S3 using bucket: pyops-infra-reports-109804294707
6. Provide a final structured recommendation

Always use the tools — do not make assumptions about infrastructure state."""

    # Agent loop
    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system_prompt,
            tools=tools,
            messages=messages
        )

        print(f"Agent step — stop reason: {response.stop_reason}")

        if response.stop_reason == "tool_use":
            messages.append({
                "role": "assistant",
                "content": response.content
            })

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  → Calling tool: {block.name}")
                    print(f"    Input: {json.dumps(block.input, indent=2)}")

                    result = execute_tool(block.name, block.input)
                    print(f"    Result: {json.dumps(result, indent=2)[:200]}...")

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result)
                    })

            messages.append({
                "role": "user",
                "content": tool_results
            })

        elif response.stop_reason == "end_turn":
            final_response = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_response += block.text

            print(f"\n{'='*50}")
            print("AGENT FINAL RESPONSE:")
            print(f"{'='*50}\n")
            print(final_response)
            return final_response

        else:
            print(f"Unexpected stop reason: {response.stop_reason}")
            break


if __name__ == "__main__":
    run_agent(
        "Analyse the current AWS infrastructure in us-east-1 and provide "
        "a prioritised remediation plan based on our runbooks."
    )