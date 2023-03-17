from logging import getLogger

import boto3
import botocore.exceptions


RESOURCE_TYPE = "AWS::S3::Bucket"
logger = getLogger(__name__)


def list_resource_names(region: str) -> list[str]:
    client = boto3.client("s3", region_name=region)
    response = client.list_buckets()
    names = []

    for bucket in response["Buckets"]:
        try:
            bucket_location_response = client.get_bucket_location(Bucket=bucket["Name"])
            bucket_region = bucket_location_response["LocationConstraint"]

            if bucket_region == region or (
                bucket_region is None and region == "us-east-1"
            ):
                names.append(bucket["Name"])

        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchBucket":
                logger.info(f"Bucket '{bucket['Name']}' not found, skipping.")
            else:
                logger.info(f"Error occurred for bucket '{bucket['Name']}': {e}")

    return names


def delete_resources(region: str, resource_names: list[str]) -> None:
    client = boto3.client("s3", region_name=region)

    for name in resource_names:
        versioning = client.get_bucket_versioning(Bucket=name)

        if versioning.get("Status") == "Enabled":
            object_versions = client.list_object_versions(Bucket=name)

            for version in object_versions.get("Versions", []):
                client.delete_object(
                    Bucket=name, Key=version["Key"], VersionId=version["VersionId"]
                )

            for marker in object_versions.get("DeleteMarkers", []):
                client.delete_object(
                    Bucket=name, Key=marker["Key"], VersionId=marker["VersionId"]
                )

        objects = client.list_objects_v2(Bucket=name)

        for obj in objects.get("Contents", []):
            client.delete_object(Bucket=name, Key=obj["Key"])

        client.delete_bucket(Bucket=name)
