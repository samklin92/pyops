import boto3
import logging
from datetime import datetime, timezone


class S3Reporter:

    def __init__(self, bucket_name, region="us-east-1"):

        self.bucket_name = bucket_name
        self.region = region

        self.s3 = boto3.client(
            "s3",
            region_name=region
        )

    def upload(self, content, key=None):

        if key is None:

            timestamp = datetime.now(
                timezone.utc
            ).strftime("%Y-%m-%dT%H-%M-%S")

            key = (
                f"reports/monitor-{timestamp}.txt"
            )

        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=content.encode("utf-8")
        )

        logging.info(
            f"Report uploaded to "
            f"s3://{self.bucket_name}/{key}"
        )

        return key

    def list_reports(self):

        response = self.s3.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix="reports/"
        )

        if "Contents" not in response:
            return []

        return [
            {
                "key": obj["Key"],
                "size": obj["Size"],
                "last_modified": obj["LastModified"]
            }
            for obj in response["Contents"]
        ]

    def download(self, key):

        response = self.s3.get_object(
            Bucket=self.bucket_name,
            Key=key
        )

        content = response["Body"].read()

        decoded_content = content.decode("utf-8")

        logging.info(
            f"Downloaded file from "
            f"s3://{self.bucket_name}/{key}"
        )

        return decoded_content