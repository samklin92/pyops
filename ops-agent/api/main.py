import sys
import json
import logging
import os
import httpx
from pathlib import Path
from fastapi import FastAPI, Request, BackgroundTasks
from pydantic import BaseModel

# Add agent directory to path
sys.path.append(str(Path(__file__).parent.parent / "agent"))

from foundations import investigate_alert

# Use fastembed in container, sentence-transformers locally
try:
    from tools.rag_search_container import build_qdrant_client
except ImportError:
    from tools.rag_search import build_qdrant_client

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("opsAgent")

app = FastAPI(title="opsAgent", version="1.0.0")

# Build RAG index once at startup
logger.info("Building RAG index...")
qdrant_client = build_qdrant_client()
logger.info("RAG index ready.")

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


# --- Slack Notification ---

async def notify_slack(alert_name: str, service: str, severity: str, rca: dict):
    """Post RCA result to Slack #alerts channel."""
    if not SLACK_WEBHOOK_URL:
        logger.warning("SLACK_WEBHOOK_URL not set — skipping notification")
        return

    confidence_emoji = {
        "high": "🔴",
        "medium": "🟡",
        "low": "🟢"
    }.get(rca.get("confidence", "medium"), "🟡")

    needs_more = "⚠️ Yes" if rca.get("needs_more_data") else "✅ No"

    message = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚨 opsAgent RCA — {alert_name}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Service:*\n{service}"},
                    {"type": "mrkdwn", "text": f"*Severity:*\n{severity.upper()}"},
                    {"type": "mrkdwn", "text": f"*Confidence:*\n{confidence_emoji} {rca.get('confidence', 'unknown').upper()}"},
                    {"type": "mrkdwn", "text": f"*Needs More Data:*\n{needs_more}"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🔍 Probable Cause:*\n{rca.get('probable_cause', 'N/A')}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🛠️ Recommended Action:*\n{rca.get('recommended_action', 'N/A')}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*📖 Runbook:*\n{rca.get('runbook_reference', 'N/A')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*🔀 Deployment Correlation:*\n{rca.get('deployment_correlation', 'none found')}"
                    }
                ]
            },
            {
                "type": "divider"
            }
        ]
    }

    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.post(SLACK_WEBHOOK_URL, json=message)
        if response.status_code == 200:
            logger.info(f"Slack notification sent for {alert_name}")
        else:
            logger.error(f"Slack notification failed: {response.status_code} {response.text}")


# --- Request/Response Models ---

class AlertPayload(BaseModel):
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


# --- Endpoints ---

@app.get("/health")
def health():
    return {"status": "healthy", "service": "opsAgent"}


@app.post("/investigate", response_model=RCAResponse)
async def investigate(payload: AlertPayload, background_tasks: BackgroundTasks):
    logger.info(f"Investigating alert: {payload.alert_name} | {payload.service} | {payload.severity}")

    result = investigate_alert(
        alert_name=payload.alert_name,
        service=payload.service,
        severity=payload.severity,
        qdrant_client=qdrant_client
    )

    logger.info(f"RCA complete: {result.get('probable_cause', '')[:80]}")

    background_tasks.add_task(
        notify_slack,
        alert_name=payload.alert_name,
        service=payload.service,
        severity=payload.severity,
        rca=result
    )

    return result


@app.post("/webhook/sns")
async def sns_webhook(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    msg_type = body.get("Type", "")

    if msg_type == "SubscriptionConfirmation":
        logger.info(f"SNS subscription confirmation URL: {body.get('SubscribeURL')}")
        return {"status": "confirm this URL to activate webhook"}

    if msg_type == "Notification":
        raw_message = body.get("Message", "{}")

        try:
            message = json.loads(raw_message)
        except json.JSONDecodeError:
            message = {"detail": raw_message}

        alarm_name = message.get("AlarmName", "UnknownAlarm")
        new_state = message.get("NewStateValue", "ALARM")

        parts = alarm_name.split("-")
        service = parts[0].lower() if parts else "unknown"
        severity = "critical" if new_state == "ALARM" else "warning"

        logger.info(f"SNS alarm received: {alarm_name} | service: {service} | state: {new_state}")

        background_tasks.add_task(
            run_investigation,
            alert_name=alarm_name,
            service=service,
            severity=severity
        )

        return {"status": "investigation started", "alert": alarm_name}

    return {"status": "unhandled message type", "type": msg_type}


async def run_investigation(alert_name: str, service: str, severity: str):
    try:
        result = investigate_alert(
            alert_name=alert_name,
            service=service,
            severity=severity,
            qdrant_client=qdrant_client
        )
        logger.info(f"Background RCA complete for {alert_name}")
        await notify_slack(alert_name, service, severity, result)
    except Exception as e:
        logger.error(f"Investigation failed for {alert_name}: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)