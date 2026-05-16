import sys
import json
import logging
from pathlib import Path
from fastapi import FastAPI, Request, BackgroundTasks
from pydantic import BaseModel

# Add agent directory to path
sys.path.append(str(Path(__file__).parent.parent / "agent"))

from foundations import investigate_alert
from tools.rag_search import build_qdrant_client

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("opsAgent")

app = FastAPI(title="opsAgent", version="1.0.0")

# Build RAG index once at startup
logger.info("Building RAG index...")
qdrant_client = build_qdrant_client()
logger.info("RAG index ready.")


# --- Request/Response Models ---

class AlertPayload(BaseModel):
    """Direct alert payload for manual queries."""
    alert_name: str
    service: str
    severity: str


class RCAResponse(BaseModel):
    probable_cause: str
    confidence: str
    recommended_action: str
    runbook_reference: str
    deployment_correlation: str
    needs_more_data: bool


class SNSNotification(BaseModel):
    """AWS SNS webhook payload structure."""
    Type: str
    TopicArn: str = ""
    Subject: str = ""
    Message: str = ""
    SubscribeURL: str = ""


# --- Endpoints ---

@app.get("/health")
def health():
    """ALB health check endpoint."""
    return {"status": "healthy", "service": "opsAgent"}


@app.post("/investigate", response_model=RCAResponse)
async def investigate(payload: AlertPayload):
    """
    Direct investigation endpoint.
    Accepts alert name, service, and severity — returns structured RCA.
    """
    logger.info(f"Investigating alert: {payload.alert_name} | {payload.service} | {payload.severity}")

    result = investigate_alert(
        alert_name=payload.alert_name,
        service=payload.service,
        severity=payload.severity
    )

    logger.info(f"RCA complete: {result.get('probable_cause', '')[:80]}")
    return result


@app.post("/webhook/sns")
async def sns_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    AWS SNS webhook endpoint.
    Handles CloudWatch Alarm → SNS → opsAgent notification flow.
    """
    body = await request.json()
    msg_type = body.get("Type", "")

    # SNS subscription confirmation
    if msg_type == "SubscriptionConfirmation":
        logger.info(f"SNS subscription confirmation URL: {body.get('SubscribeURL')}")
        return {"status": "confirm this URL to activate webhook"}

    # Handle actual alarm notification
    if msg_type == "Notification":
        raw_message = body.get("Message", "{}")

        try:
            message = json.loads(raw_message)
        except json.JSONDecodeError:
            message = {"detail": raw_message}

        # Parse CloudWatch alarm structure
        alarm_name = message.get("AlarmName", "UnknownAlarm")
        alarm_desc = message.get("AlarmDescription", "")
        new_state = message.get("NewStateValue", "ALARM")

        # Extract service name from alarm name or description
        # Convention: alarm name format is "ServiceName-AlertType"
        parts = alarm_name.split("-")
        service = parts[0].lower() if parts else "unknown"
        severity = "critical" if new_state == "ALARM" else "warning"

        logger.info(f"SNS alarm received: {alarm_name} | service: {service} | state: {new_state}")

        # Run investigation in background so SNS gets fast 200 response
        background_tasks.add_task(
            run_investigation,
            alert_name=alarm_name,
            service=service,
            severity=severity
        )

        return {"status": "investigation started", "alert": alarm_name}

    return {"status": "unhandled message type", "type": msg_type}


async def run_investigation(alert_name: str, service: str, severity: str):
    """Background task — runs agent investigation and logs result."""
    try:
        result = investigate_alert(
            alert_name=alert_name,
            service=service,
            severity=severity
        )
        logger.info(f"Background RCA complete for {alert_name}:")
        logger.info(json.dumps(result, indent=2))
        # Week 11: replace logger with Slack notification here
    except Exception as e:
        logger.error(f"Investigation failed for {alert_name}: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)