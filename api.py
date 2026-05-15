import logging
import os
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from infra import load_config
from toolkit import EC2Toolkit, S3Toolkit, MonitorToolkit
from agent import run_agent

logger = logging.getLogger(__name__)

app = FastAPI(title="Infra Monitor API", version="1.0.0")

config = load_config("config.json")
BUCKET_NAME = config["s3_bucket"]
REGION = os.getenv("AWS_REGION", config["region"])

executor = ThreadPoolExecutor(max_workers=2)

ec2 = EC2Toolkit(region=REGION)
s3 = S3Toolkit(bucket_name=BUCKET_NAME, region=REGION)
monitor = MonitorToolkit(region=REGION)


# ── Health ───────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/")
def root():
    return {"message": "Infra Monitor API is running"}


# ── Instances ────────────────────────────────────────────

@app.get("/instances")
def list_instances():
    instances = ec2.list_instances()
    if not instances:
        raise HTTPException(status_code=404, detail="No instances found")
    return {"region": REGION, "count": len(instances), "instances": instances}


@app.get("/instances/running")
def list_running_instances():
    instances = ec2.list_running()
    if not instances:
        raise HTTPException(status_code=404, detail="No running instances found")
    return {"region": REGION, "count": len(instances), "instances": instances}


@app.get("/instances/{instance_id}")
def get_instance(instance_id: str):
    try:
        instance = ec2.get_instance_state(instance_id)
        return instance
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Instance not found: {str(e)}")


@app.post("/instances/{instance_id}/stop")
def stop_instance(instance_id: str):
    try:
        result = ec2.stop_instance(instance_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop instance: {str(e)}")


@app.post("/instances/{instance_id}/start")
def start_instance(instance_id: str):
    try:
        result = ec2.start_instance(instance_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start instance: {str(e)}")


# ── Reports ──────────────────────────────────────────────

@app.get("/reports")
def list_reports():
    reports = s3.list_objects(prefix="reports/")
    if not reports:
        raise HTTPException(status_code=404, detail="No reports found")
    return {"count": len(reports), "reports": reports}


@app.get("/reports/latest")
def latest_report():
    report = s3.latest_object(prefix="reports/")
    if not report:
        raise HTTPException(status_code=404, detail="No reports found")
    content = s3.download(report["key"])
    return {"key": report["key"], "content": content}


# ── Alarms ───────────────────────────────────────────────

@app.get("/alarms")
def list_alarms():
    alarms = monitor.list_alarms()
    if not alarms:
        raise HTTPException(status_code=404, detail="No alarms found")
    return {"count": len(alarms), "alarms": alarms}


@app.get("/alarms/firing")
def firing_alarms():
    alarms = monitor.alarms_in_alarm()
    return {"count": len(alarms), "alarms": alarms}


# ── Agent ────────────────────────────────────────────────

class AgentQuery(BaseModel):
    question: str


@app.post("/agent/query")
async def agent_query(payload: AgentQuery):
    try:
        loop = __import__("asyncio").get_event_loop()
        result = await loop.run_in_executor(executor, run_agent, payload.question)
        return {"question": payload.question, "answer": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))