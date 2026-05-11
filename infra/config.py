import json
import logging
import sys


def load_config(path="config.json"):
    try:
        with open(path, "r") as config_file:
            config = json.load(config_file)

        logging.info(
            f"Configuration loaded successfully "
            f"(Environment: {config['environment']}, "
            f"Region: {config['region']})"
        )
        return config

    except FileNotFoundError:
        logging.error(f"Config file not found: {path}")
        sys.exit(1)

    except json.JSONDecodeError:
        logging.error(f"Invalid JSON format in: {path}")
        sys.exit(1)

    except KeyError as missing_key:
        logging.error(f"Missing required config key: {missing_key}")
        sys.exit(1)