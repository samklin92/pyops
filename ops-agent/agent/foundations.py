import anthropic
import json
from tools.metrics import query_prometheus, PROMETHEUS_TOOL
from tools.rag_search import search_runbooks, build_qdrant_client, RAG_SEARCH_TOOL

client = anthropic.Anthropic()

# Build RAG index once at startup
print("Building RAG index...")
qdrant_client = build_qdrant_client()
print("RAG index ready.\n")

SYSTEM_PROMPT = """
You are an SRE ops agent investigating infrastructure alerts.

When an alert comes in:
1. Query Prometheus metrics for the affected service to understand current state
2. Search runbooks for known issues matching the symptoms
3. Correlate metrics with runbook findings
4. Return a structured RCA

Always respond in this exact JSON format:
{
    "probable_cause": "string",
    "confidence": "high | medium | low",
    "recommended_action": "string",
    "runbook_reference": "string — which runbook section applies",
    "needs_more_data": boolean
}

Return only the JSON. No markdown, no explanation.
"""


def run_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "query_prometheus":
        result = query_prometheus(**tool_input)
        return json.dumps(result)

    if tool_name == "search_runbooks":
        results = search_runbooks(
            query=tool_input["query"],
            qdrant_client=qdrant_client,
            top_k=tool_input.get("top_k", 3)
        )
        return json.dumps(results)

    raise ValueError(f"Unknown tool: {tool_name}")


def investigate_alert(alert_name: str, service: str, severity: str) -> dict:
    messages = [
        {
            "role": "user",
            "content": (
                f"Investigate this alert:\n"
                f"Alert: {alert_name}\n"
                f"Service: {service}\n"
                f"Severity: {severity}\n\n"
                f"Query metrics for this service, search runbooks for matching issues, "
                f"then provide your RCA."
            )
        }
    ]

    while True:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=[PROMETHEUS_TOOL, RAG_SEARCH_TOOL],
            messages=messages
        )

        if response.stop_reason == "tool_use":
            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in tool_use_blocks:
                print(f"[tool call] {block.name}({block.input})")
                result = run_tool(block.name, block.input)
                print(f"[tool result] {result[:200]}...\n" if len(result) > 200 else f"[tool result] {result}\n")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result
                })

            messages.append({"role": "user", "content": tool_results})

        elif response.stop_reason == "end_turn":
            final_text = next(
                (b.text for b in response.content if hasattr(b, "text")), ""
            ).strip()

            if final_text.startswith("```"):
                final_text = final_text.split("```")[1]
                if final_text.startswith("json"):
                    final_text = final_text[4:]

            return json.loads(final_text.strip())


if __name__ == "__main__":
    # Test three different alert scenarios
    alerts = [
        ("HighErrorRate", "payments-api", "critical"),
        ("UnhealthyHosts", "auth-service", "warning"),
        ("HighLatency", "inventory-api", "critical"),
    ]

    for alert_name, service, severity in alerts:
        print(f"{'='*60}")
        print(f"Alert: {alert_name} | Service: {service} | Severity: {severity}")
        print(f"{'='*60}")
        result = investigate_alert(alert_name, service, severity)
        print(json.dumps(result, indent=2))
        print()