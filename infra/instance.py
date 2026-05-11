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

    def is_healthy(self, threshold):
        return self.cpu <= threshold

    def summarise(self, threshold):
        health = "OK" if self.is_healthy(threshold) else "ALERT"
        return (
            f"{self.status()} "
            f"{self.id} | "
            f"{self.type} | "
            f"{self.region} | "
            f"CPU: {self.cpu}% | "
            f"{health}"
        )