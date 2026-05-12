import json
import anthropic
from infra import load_config, EC2Instance, InfraMonitor


def build_infra_summary(monitor):
    lines = []
    for instance in monitor.instances:
        health = "OK" if instance.is_healthy(monitor.alert_threshold) else "ALERT"
        lines.append(
            f"- {instance.id} | {instance.type} | "
            f"{instance.region} | CPU: {instance.cpu}% | {health}"
        )
    return "\n".join(lines)


def analyse_infra_structured(monitor):
    client = anthropic.Anthropic()
    summary = build_infra_summary(monitor)

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system="""You are an expert DevOps engineer and AWS specialist.
Analyse the infrastructure data provided and respond ONLY with a JSON object.
No markdown, no explanation, no code blocks — raw JSON only.

The JSON must follow this exact structure:
{
  "overall_status": "OK|WARNING|CRITICAL",
  "total_instances": <number>,
  "alerts": <number>,
  "instances": [
    {
      "id": "<instance_id>",
      "status": "OK|WARNING|CRITICAL",
      "cpu": <number>,
      "recommendation": "<action to take>"
    }
  ],
  "priority_action": "<most urgent action>",
  "summary": "<one sentence summary>"
}""",
        messages=[
            {
                "role": "user",
                "content": f"Analyse this infrastructure:\n{summary}"
            }
        ]
    )

    raw = message.content[0].text

    # Strip markdown code fences if present
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        result = json.loads(raw)
        return result
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")
        print(f"Raw response: {raw}")
        return None


if __name__ == "__main__":
    config = load_config("config.json")
    monitor = InfraMonitor(config)

    monitor.add_instance(EC2Instance("i-0abc123", "t3.micro", "us-east-1", True, 82))
    monitor.add_instance(EC2Instance("i-0def456", "t3.large", "us-west-2", True, 45))
    monitor.add_instance(EC2Instance("i-0ghi789", "t3.medium", "eu-west-1", False, 91))
    monitor.add_instance(EC2Instance("i-0jkl012", "t3.small", "ap-southeast-1", True, 60))

    result = analyse_infra_structured(monitor)

    if result:
        print(json.dumps(result, indent=2))
        print("\n=== Automated Actions ===\n")

        if result["overall_status"] == "CRITICAL":
            print(f"CRITICAL ALERT — {result['summary']}")
            print(f"Priority: {result['priority_action']}")

        for instance in result["instances"]:
            if instance["status"] == "CRITICAL":
                print(f"\n[ACTION REQUIRED] {instance['id']}")
                print(f"  CPU: {instance['cpu']}%")
                print(f"  Recommendation: {instance['recommendation']}")
            elif instance["status"] == "WARNING":
                print(f"\n[WARNING] {instance['id']}")
                print(f"  CPU: {instance['cpu']}%")
                print(f"  Recommendation: {instance['recommendation']}")