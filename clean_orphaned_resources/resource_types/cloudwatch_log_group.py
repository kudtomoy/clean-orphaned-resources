from logging import getLogger

import boto3

from clean_orphaned_resources.resource_types.base import (
    ResourceTypeBase,
    handle_boto3_exceptions,
)


logger = getLogger(__name__)


class CloudWatchLogs(ResourceTypeBase):
    RESOURCE_TYPE = "AWS::Logs::LogGroup"

    @staticmethod
    @handle_boto3_exceptions("")
    def get_tags(client, name: str) -> str:
        response = client.list_tags_log_group(logGroupName=name)
        return ",".join([f"{key}={value}" for key, value in response["tags"].items()])

    @staticmethod
    @handle_boto3_exceptions([])
    def list_resource_identifiers(region: str) -> list[tuple[str, str]]:
        client = boto3.client("logs", region_name=region)
        response = client.describe_log_groups()
        identifiers = []

        while response:
            for log_group in response["logGroups"]:
                tags = CloudWatchLogs.get_tags(client, log_group["logGroupName"])
                identifiers.append((log_group["logGroupName"], tags))

            if "nextToken" in response:
                response = client.describe_log_groups(nextToken=response["nextToken"])
            else:
                response = None

        return identifiers

    @staticmethod
    @handle_boto3_exceptions()
    def delete_resource(region: str, identifier: str) -> None:
        client = boto3.client("logs", region_name=region)

        log_streams = client.describe_log_streams(logGroupName=identifier)

        for log_stream in log_streams.get("logStreams", []):
            client.delete_log_stream(
                logGroupName=identifier, logStreamName=log_stream["logStreamName"]
            )

        client.delete_log_group(logGroupName=identifier)
