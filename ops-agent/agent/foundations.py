import anthropic
import json

# Use fastembed in container, sentence-transformers locally
try:
    from tools.rag_search_container import search_runbooks, build_qdrant_client, RAG_SEARCH_TOOL
    print("Using fastembed for embeddings")
except ImportError:
    from tools.rag_search import search_runbooks, build_qdrant_client, RAG_SEARCH_TOOL
    print("Using sentence-transformers for embeddings")

from tools.metrics import query_prometheus, PROMETHEUS_TOOL
from tools.git_context import get_recent_changes, GIT_CONTEXT_TOOL

client = anthropic.Anthropic()

SYSTEM_PROMPT = """
You are an SRE ops agent investigating infrastructure alerts.

When an alert comes in:
1. Query Prometheus metrics for the affected service
2. Search runbooks for known issues matching the symptoms
3. Check recent git changes for the affected service for deployment correlation
4. Correlate all three sources and return a structured RCA

Always respond in this exact JSON format:
{
    "probable_cause": "string",
    "confidence": "high | medium | low",
    "recommended_action": "string",
    "runbook_reference": "string — which runbook section applies",
    "deployment_correlation": "string — any recent changes that may be related or 'none found'",
    "needs_more_data": boolean
}

Return only the JSON. No markdown, no explanation.
"""


def run_tool(tool_name: str, tool_input: dict, qdrant_client) -> str:
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

    if tool_name == "get_recent_changes":
        result = get_recent_changes(**tool_input)
        return json.dumps(result)

    raise ValueError(f"Unknown tool: {tool_name}")


def investigate_alert(
    alert_name: str,
    service: str,
    severity: str,
    qdrant_client=None
) -> dict:
    if qdrant_client is None:
        qdrant_client = build_qdrant_client()

    messages = [
        {
            "role": "user",
            "content": (
                f"Investigate this alert:\n"
                f"Alert: {alert_name}\n"
                f"Service: {service}\n"
                f"Severity: {severity}\n\n"
                f"Query metrics, search runbooks, check recent git changes, "
                f"then provide your RCA."
            )
        }
    ]

    while True:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=[PROMETHEUS_TOOL, RAG_SEARCH_TOOL, GIT_CONTEXT_TOOL],
            messages=messages
        )

        if response.stop_reason == "tool_use":
            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in tool_use_blocks:
                print(f"[tool call] {block.name}({block.input})")
                result = run_tool(block.name, block.input, qdrant_client)
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
    print("Building RAG index...")
    qdra