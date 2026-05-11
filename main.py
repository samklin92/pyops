import logging
import sys
from infra.config import load_config
from infra.instance import EC2Instance
from infra.monitor import InfraMonitor

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("monitor.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

if __name__ == "__main__":

    config = load_config("config.json")
    monitor = InfraMonitor(config)

    monitor.add_instance(EC2Instance("i-0abc123", "t3.micro", "us-east-1", True, 82))
    monitor.add_instance(EC2Instance("i-0def456", "t3.large", "us-west-2", True, 45))
    monitor.add_instance(EC2Instance("i-0ghi789", "t3.medium", "eu-west-1", False, 91))
    monitor.add_instance(EC2Instance("i-0jkl012", "t3.small", "ap-southeast-1", True, 60))

    monitor.run()
    monitor.summary()