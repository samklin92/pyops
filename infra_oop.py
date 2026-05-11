# infra_oop.py

import json
import logging
import sys


class EC2Instance:

    def __init__(self, instance_id, instance_type,
                 region, running, cpu):

        self.id = instance_id
        self.type = instance_type
        self.region = region
        self.running = running
        self.cpu = cpu

    def status(self):
        return "[UP]" if self.running else "[DOWN]"

    def is_healthy(self, alert_threshold):
        return self.cpu <= alert_threshold

    def summarise(self, alert_threshold):

        health = (
            "OK"
            if self.is_healthy(alert_threshold)
            else "ALERT"
        )

        return (
            f"{self.status()} "
            f"{self.id} | "
            f"{self.type} | "
            f"{self.region} | "
            f"CPU: {self.cpu}% | "
            f"{health}"
        )


class InfraMonitor:

    def __init__(self):

        self.instances = []

        # Configure logging
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s | %(levelname)s | %(message)s",
            handlers=[
                logging.FileHandler("monitor.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )

        # Load config.json
        try:
            with open("config.json", "r") as config_file:
                config = json.load(config_file)

            self.environment = config["environment"]
            self.region = config["region"]
            self.alert_threshold = config["alert_threshold"]

            logging.info(
                f"Configuration loaded successfully "
                f"(Environment: {self.environment}, "
                f"Region: {self.region})"
            )

        except FileNotFoundError:
            logging.error("config.json file not found.")
            sys.exit(1)

        except json.JSONDecodeError:
            logging.error("Invalid JSON format in config.json.")
            sys.exit(1)

        except KeyError as missing_key:
            logging.error(
                f"Missing required config key: {missing_key}"
            )
            sys.exit(1)

    def add_instance(self, instance):
        self.instances.append(instance)

    def run(self):

        for instance in self.instances:

            # DEBUG log for raw object data
            logging.debug(
                f"Raw instance values: "
                f"id={instance.id}, "
                f"type={instance.type}, "
                f"region={instance.region}, "
                f"running={instance.running}, "
                f"cpu={instance.cpu}"
            )

            # ERROR for DOWN instances
            if not instance.running:

                logging.error(
                    instance.summarise(self.alert_threshold)
                )

            # WARNING for high CPU usage
            elif not instance.is_healthy(
                self.alert_threshold
            ):

                logging.warning(
                    instance.summarise(self.alert_threshold)
                )

            # INFO for healthy instances
            else:

                logging.info(
                    instance.summarise(self.alert_threshold)
                )

    def summary(self):

        up = sum(
            1 for i in self.instances
            if i.running
        )

        down = sum(
            1 for i in self.instances
            if not i.running
        )

        alerts = sum(
            1 for i in self.instances
            if i.cpu > self.alert_threshold
        )

        # CRITICAL if more than half are DOWN
        if down > len(self.instances) / 2:

            logging.critical(
                "CRITICAL: More than half "
                "of the instances are DOWN!"
            )

        logging.info(
            f"Script complete — "
            f"{up} UP | "
            f"{down} DOWN | "
            f"{alerts} ALERT"
        )


if __name__ == "__main__":

    monitor = InfraMonitor()

    # Add instances
    monitor.add_instance(
        EC2Instance(
            "i-0abc123",
            "t3.micro",
            "us-east-1",
            True,
            82
        )
    )

    monitor.add_instance(
        EC2Instance(
            "i-0def456",
            "t3.large",
            "us-west-2",
            True,
            45
        )
    )

    monitor.add_instance(
        EC2Instance(
            "i-0ghi789",
            "t3.medium",
            "eu-west-1",
            False,
            91
        )
    )

    monitor.add_instance(
        EC2Instance(
            "i-0jkl012",
            "t3.small",
            "ap-southeast-1",
            True,
            60
        )
    )

    monitor.run()
    monitor.summary()