from logging import getLogger

import boto3


RESOURCE_TYPE = "AWS::Logs::LogGroup"
logger = getLogger(__name__)


def list_resource_names(region: str) -> list[str]:
    client = boto3.client("logs", region_name=region)
    response = client.describe_log_groups()
    names = []

    while response:
        for log_group in response["logGroups"]:
            names.append(log_group["logGroupName"])

        if "nextToken" in response:
            response = client.describe_log_groups(nextToken=response["nextToken"])
        else:
            response = None

    return names


def delete_resources(region: str, resource_names: list[str]) -> None:
    client = boto3.client("logs", region_name=region)

    for name in resource_names:
        log_streams = client.describe_log_streams(logGroupName=name)

        for log_stream in log_streams.get("logStreams", []):
            client.delete_log_stream(
                logGroupName=name, logStreamName=log_stream["logStreamName"]
            )

        client.delete_log_group(logGroupName=name)
