import logging
from infra.instance import EC2Instance


class InfraMonitor:

    def __init__(self, config):
        self.instances = []
        self.alert_threshold = config["alert_threshold"]
        self.environment = config["environment"]
        self.region = config["region"]

    def add_instance(self, instance):
        self.instances.append(instance)

    def run(self):
        for instance in self.instances:

            logging.debug(
                f"Raw instance values: "
                f"id={instance.id}, "
                f"type={instance.type}, "
                f"region={instance.region}, "
                f"running={instance.running}, "
                f"cpu={instance.cpu}"
            )

            if not instance.running:
                logging.error(
                    instance.summarise(self.alert_threshold)
                )
            elif not instance.is_healthy(self.alert_threshold):
                logging.warning(
                    instance.summarise(self.alert_threshold)
                )
            else:
                logging.info(
                    instance.summarise(self.alert_threshold)
                )

    def summary(self):
        up = sum(1 for i in self.instances if i.running)
        down = sum(1 for i in self.instances if not i.running)
        alerts = sum(
            1 for i in self.instances
            if i.cpu > self.alert_threshold
        )

        if down > len(self.instances) / 2:
            logging.critical(
                "CRITICAL: More than half of the instances are DOWN!"
            )

        logging.info(
            f"Script complete — "
            f"{up} UP | {down} DOWN | {alerts} ALERT"
        )