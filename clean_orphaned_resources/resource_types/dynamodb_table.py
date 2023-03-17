from logging import getLogger

import boto3


RESOURCE_TYPE = "AWS::DynamoDB::Table"
logger = getLogger(__name__)


def list_resource_names(region: str) -> list[str]:
    client = boto3.client("dynamodb", region_name=region)
    response = client.list_tables()
    names = response.get("TableNames", [])
    return names


def delete_resources(region: str, resource_names: list[str]) -> None:
    client = boto3.client("dynamodb", region_name=region)

    for name in resource_names:
        client.delete_table(TableName=name)
