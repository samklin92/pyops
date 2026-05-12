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


def analyse_infra(monitor):
    client = anthropic.Anthropic()
    summary = build_infra_summary(monitor)

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system="""You are an expert DevOps engineer and AWS specialist.
When given infrastructure data, you analyse it and respond with:
1. A clear status summary
2. Any risks or concerns
3. Specific recommended actions
Keep responses concise and actionable.""",
        messages=[
            {
                "role": "user",
                "content": f"Analyse this infrastructure status:\n{summary}"
            }
        ]
    )

    return message.content[0].text


if __name__ == "__main__":
    config = load_config("config.json")
    monitor = InfraMonitor(config)

    # Add test instances
    monitor.add_instance(EC2Instance("i-0abc123", "t3.micro", "us-east-1", True, 82))
    monitor.add_instance(EC2Instance("i-0def456", "t3.large", "us-west-2", True, 45))
    monitor.add_instance(EC2Instance("i-0ghi789", "t3.medium", "eu-west-1", False, 91))
    monitor.add_instance(EC2Instance("i-0jkl012", "t3.small", "ap-southeast-1", True, 60))

    print("=== Infrastructure Analysis ===\n")
    analysis = analyse_infra(monitor)
    print(analysis)