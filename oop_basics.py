class EC2Instance:

    def __init__(self, id, type, region, cpu, running):
        self.id = id
        self.type = type
        self.region = region
        self.cpu = cpu
        self.running = running

    def status(self):
        return "[UP]" if self.running else "[DOWN]"

    def is_healthy(self, threshold=75):
        return self.cpu <= threshold

    def summarise(self, threshold=75):
        health = "OK" if self.is_healthy(threshold) else "ALERT"
        return f"{self.status()} {self.id} | {self.type} | {self.region} | CPU: {self.cpu}% | {health}"

    def cpu_status(self, threshold=75):
        if self.cpu > threshold:
            return f"WARNING: CPU at {self.cpu}% exceeds {threshold}%"
        return f"OK: CPU at {self.cpu}%"

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "region": self.region,
            "cpu": self.cpu,
            "running": self.running,
            "status": self.status()
        }


# Create instances
instance1 = EC2Instance("i-0abc123", "t3.micro", "us-east-1", 82, True)
instance2 = EC2Instance("i-0def456", "t3.large", "us-west-2", 45, True)
instance3 = EC2Instance("i-0ghi789", "t3.medium", "eu-west-1", 91, False)

# Summarise
print(instance1.summarise())
print(instance2.summarise())
print(instance3.summarise())

# CPU status
print(instance1.cpu_status())
print(instance2.cpu_status())

# Convert to dict
import json
print(json.dumps(instance1.to_dict(), indent=2))

class InfraMonitor:

    def __init__(self, threshold=75):
        self.instances = []
        self.threshold = threshold

    def add_instance(self, instance):
        self.instances.append(instance)

    def report(self):
        for instance in self.instances:
            print(instance.summarise(self.threshold))

    def summary(self):
        up = sum(1 for i in self.instances if i.running)
        down = sum(1 for i in self.instances if not i.running)
        alerts = sum(1 for i in self.instances if not i.is_healthy(self.threshold))
        print(f"\nTotal: {up} UP | {down} DOWN | {alerts} ALERT")


# Use the manager
monitor = InfraMonitor(threshold=75)
monitor.add_instance(instance1)
monitor.add_instance(instance2)
monitor.add_instance(instance3)

monitor.report()
monitor.summary()