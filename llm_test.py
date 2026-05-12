import anthropic

client = anthropic.Anthropic()

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
            "content": """Analyse this infrastructure status:
- i-0abc123 | t3.micro | us-east-1 | CPU: 82% | ALERT
- i-0def456 | t3.large | us-west-2 | CPU: 45% | OK
- i-0ghi789 | t3.medium | eu-west-1 | CPU: 91% | ALERT
- i-0jkl012 | t3.small | ap-southeast-1 | CPU: 60% | OK"""
        }
    ]
)

print(message.content[0].text)