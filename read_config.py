import json
import os

with open("config.json", "r") as f:
    config = json.load(f)

print(config["environment"])
print(config["region"])
print(config["alert_threshold"])

# Reading an environment variable
environment = os.environ.get("APP_ENV", "development")
print(f"Running in: {environment}")