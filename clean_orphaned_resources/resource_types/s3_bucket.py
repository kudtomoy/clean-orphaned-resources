from logging import getLogger

import boto3
import botocore.exceptions

from clean_orphaned_resources.resource_types.base import (
    ResourceTypeBase,
    handle_boto3_exceptions,
)


logger = getLogger(__name__)


class S3Bucket(ResourceTypeBase):
    RESOURCE_TYPE = "AWS::S3::Bucket"

    @staticmethod
    @handle_boto3_exceptions("")
    def get_tags(client, name: str) -> str:
        response = client.get_bucket_tagging(Bucket=name)
        return ",".join([f"{tag['Key']}={tag['Value']}" for tag in response["TagSet"]])

    @staticmethod
    @handle_boto3_exceptions([])
    def list_resource_identifiers(region: str) -> list[tuple[str, str]]:
        client = boto3.client("s3", region_name=region)
        response = client.list_buckets()
        identifiers = []

        for bucket in response["Buckets"]:
            bucket_name = bucket["Name"]
            try:
                bucket_location_response = client.get_bucket_location(
                    Bucket=bucket_name
                )
                bucket_region = bucket_location_response["LocationConstraint"]

                if bucket_region == region or (
                    bucket_region is None and region == "us-east-1"
                ):
                    tags = S3Bucket.get_tags(client, bucket_name)
                    identifiers.append((bucket_name, tags))

            except botocore.exceptions.ClientError as e:
                if e.response["Error"]["Code"] == "NoSuchBucket":
                    logger.info(f"Bucket '{bucket_name}' not found, skipping.")
                else:
                    raise e

        return identifiers

    @staticmethod
    @handle_boto3_exceptions()
    def delete_resource(region: str, identifier: str) -> None:
        client = boto3.client("s3", region_name=region)

        versioning = client.get_bucket_versioning(Bucket=identifier)

        if versioning.get("Status") == "Enabled":
            object_versions = client.list_object_versions(Bucket=identifier)

            for version in object_versions.get("Versions", []):
                client.delete_object(
                    Bucket=identifier,
                    Key=version["Key"],
                    VersionId=version["VersionId"],
                )

            for marker in object_versions.get("DeleteMarkers", []):
                client.delete_object(
                    Bucket=identifier, Key=marker["Key"], VersionId=marker["VersionId"]
                )

        objects = client.list_objects_v2(Bucket=identifier)

        for obj in objects.get("Contents", []):
            client.delete_object(Bucket=identifier, Key=obj["Key"])

        client.delete_bucket(Bucket=identifier)
