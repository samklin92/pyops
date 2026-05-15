import boto3
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class S3Toolkit:

    def __init__(self, bucket_name, region="us-east-1"):
        self.bucket_name = bucket_name
        self.region = region
        self.client = boto3.client("s3", region_name=region)

    def upload(self, content, key=None):
        """Upload string content to S3 with an auto-generated key if not provided."""
        if not key:
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
            key = f"reports/report-{timestamp}.txt"

        self.client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=content.encode("utf-8")
        )
        logger.info(f"Uploaded to s3://{self.bucket_name}/{key}")
        return {"bucket": self.bucket_name, "key": key}

    def download(self, key):
        """Download and return content of an S3 object as a string."""
        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=key)
            content = response["Body"].read().decode("utf-8")
            logger.info(f"Downloaded s3://{self.bucket_name}/{key}")
            return content
        except Exception as e:
            logger.error(f"Failed to download {key}: {e}")
            raise

    def list_objects(self, prefix=""):
        """List objects in the bucket, optionally filtered by prefix."""
        response = self.client.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=prefix
        )
        objects = [
            {
                "key": obj["Key"],
                "size_kb": round(obj["Size"] / 1024, 2),
                "last_modified": obj["LastModified"].isoformat()
            }
            for obj in response.get("Contents", [])
        ]
        logger.info(f"Found {len(objects)} objects in {self.bucket_name}/{prefix}")
        return objects

    def delete(self, key):
        """Delete an object from S3."""
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=key)
            logger.info(f"Deleted s3://{self.bucket_name}/{key}")
            return {"bucket": self.bucket_name, "key": key, "action": "deleted"}
        except Exception as e:
            logger.error(f"Failed to delete {key}: {e}")
            raise

    def latest_object(self, prefix=""):
        """Return the most recently modified object in the bucket."""
        objects = self.list_objects(prefix=prefix)
        if not objects:
            return None
        return sorted(objects, key=lambda x: x["last_modified"])[-1]