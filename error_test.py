import json

try:
    with open("config.json", "r") as f:
        config = json.load(f)
    print(config["environment"])

except FileNotFoundError:
    print("ERROR: config.json not found")

except json.JSONDecodeError:
    print("ERROR: config.json is not valid JSON")

except KeyError as e:
    print(f"ERROR: Missing key in config — {e}")