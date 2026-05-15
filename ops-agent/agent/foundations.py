import anthropic
import json
from tools.metrics import query_prometheus, PROMETHEUS_TOOL

client = anthropic.Anthropic()

SYSTEM_PROMPT = """
You are an SRE ops agent. When investigating an alert:
1. Always query Prometheus metrics first for the affected service
2. Reason over the returned data
3. Return a structured RCA in this exact JSON format:

{
    "probable_cause": "string",
    "confidence": "high | medium | low",
    "recommended_action": "string",
    "needs_more_data": boolean
}

Return only the JSON. No markdown, no explanation.
"""


def run_tool(tool_name: str, tool_input: dict) -> str:
    """Execute the tool the LLM requested and return result as string."""
    if tool_name == "query_prometheus":
        result = query_prometheus(**tool_input)
        return json.dumps(result)
    raise ValueError(f"Unknown tool: {tool_name}")


def investigate_alert(alert_name: str, service: str, severity: str) -> dict:
    messages = [
        {
            "role": "user",
            "content": (
                f"Investigate this alert:\n"
                f"Alert: {alert_name}\n"
                f"Service: {service}\n"
                f"Severity: {severity}\n"
                f"Query the metrics for this service then provide your RCA."
            )
        }
    ]

    # Agentic loop — keeps running until LLM stops calling tools
    while True:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=[PROMETHEUS_TOOL],
            messages=messages
        )

        # LLM wants to call a tool
        if response.stop_reason == "tool_use":
            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]

            # Append full assistant response first
            messages.append({"role": "assistant", "content": response.content})

            # Execute ALL tool calls and collect results
            tool_results = []
            for tool_use_block in tool_use_blocks:
                print(f"[tool call] {tool_use_block.name}({tool_use_block.input})")
                tool_result = run_tool(tool_use_block.name, tool_use_block.input)
                print(f"[tool result] {tool_result}\n")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use_block.id,
                    "content": tool_result
                })

            # Return all results in a single user message
            messages.append({"role": "user", "content": tool_results})

        # LLM is done — extract final response
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
    result = investigate_alert(
        alert_name="HighErrorRate",
        service="payments-api",
        severity="critical"
    )
    print(json.dumps(result, indent=2))