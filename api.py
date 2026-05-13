import boto3
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from infra import load_config, S3Reporter
from agent import run_agent

app = FastAPI(title="Infra Monitor API", version="1.0.0")

config = load_config("config.json")
BUCKET_NAME = config["s3_bucket"]
REGION = os.getenv("AWS_REGION", config["region"])

executor = ThreadPoolExecutor(max_workers=2)


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


def fetch_ec2_instances(region):
    ec2 = boto3.client("ec2", region_name=region)
    response = ec2.describe_instances()
    instances = []
    for reservation in response["Reservations"]:
        for inst in reservation["Instances"]:
            if inst["State"]["Name"] == "terminated":
                continue
            cpu = get_cpu_utilization(inst["InstanceId"], region)
            instances.append({
                "id": inst["InstanceId"],
                "type": inst["InstanceType"],
                "region": region,
                "running": inst["State"]["Name"] == "running",
                "cpu": cpu,
                "status": "[UP]" if inst["State"]["Name"] == "running" else "[DOWN]"
            })
    return instances


@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/")
def root():
    return {"message": "Infra Monitor API is running"}


@app.get("/instances")
def list_instances():
    instances = fetch_ec2_instances(REGION)
    if not instances:
        raise HTTPException(status_code=404, detail="No instances found")
    return {"region": REGION, "count": len(instances), "instances": instances}


@app.get("/reports")
def list_reports():
    reporter = S3Reporter(bucket_name=BUCKET_NAME, region=REGION)
    reports = reporter.list_reports()
    if not reports:
        raise HTTPException(status_code=404, detail="No reports found")
    return {"count": len(reports), "reports": reports}


@app.get("/reports/latest")
def latest_report():
    reporter = S3Reporter(bucket_name=BUCKET_NAME, region=REGION)
    reports = reporter.list_reports()
    if not reports:
        raise HTTPException(status_code=404, detail="No reports found")
    latest = sorted(reports, key=lambda x: x["last_modified"])[-1]
    content = reporter.download(latest["key"])
    return {"key": latest["key"], "content": content}


class AgentQuery(BaseModel):
    question: str


@app.post("/agent/query")
async def agent_query(payload: AgentQuery):
    """Run the AI agent with a natural language infrastructure question."""
    try:
        loop = __import__("asyncio").get_event_loop()
        result = await loop.run_in_executor(
            executor,
            run_agent,
            payload.question
        )
        return {"question": payload.question, "answer": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))