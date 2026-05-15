import anthropic
import json

client = anthropic.Anthropic()

SYSTEM_PROMPT = """
You are an SRE ops agent. You will be given alert context and must return a structured RCA.

Always respond in this exact JSON format:
{
    "probable_cause": "string",
    "confidence": "high | medium | low",
    "recommended_action": "string",
    "needs_more_data": boolean
}
"""

def investigate_alert(alert_context: dict) -> dict:
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Investigate this alert:\n{json.dumps(alert_context, indent=2)}"
            }
        ]
    )
    
    response_text = message.content[0].text
    
    # Strip markdown code fences if present
    response_text = response_text.strip()
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
    
    return json.loads(response_text.strip())

if __name__ == "__main__":
    # Simulated alert — replace with real Prometheus alert structure later
    test_alert = {
        "alert_name": "HighErrorRate",
        "service": "payments-api",
        "severity": "critical",
        "metric": "http_error_rate",
        "value": "18.4%",
        "threshold": "5%",
        "duration": "10 minutes",
        "recent_changes": "Deployed v2.3.1 at 14:32 UTC"
    }
    
    result = investigate_alert(test_alert)
    print(json.dumps(result, indent=2))