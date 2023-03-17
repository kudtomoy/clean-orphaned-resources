from logging import getLogger

import boto3

from clean_orphaned_resources.resource_types.base import (
    ResourceTypeBase,
    handle_boto3_exceptions,
)


logger = getLogger(__name__)


class DynamoDbTable(ResourceTypeBase):
    RESOURCE_TYPE = "AWS::DynamoDB::Table"

    @staticmethod
    @handle_boto3_exceptions("")
    def get_tags(client, name: str) -> str:
        response = client.list_tags_of_resource(ResourceArn=name)
        return ",".join([f"{tag['Key']}={tag['Value']}" for tag in response["Tags"]])

    @staticmethod
    @handle_boto3_exceptions([])
    def list_resource_identifiers(region: str) -> list[tuple[str, str]]:
        client = boto3.client("dynamodb", region_name=region)
        response = client.list_tables()
        identifiers = []

        for name in response.get("TableNames", []):
            tags = DynamoDbTable.get_tags(client, name)
            identifiers.append((name, tags))

        return identifiers

    @staticmethod
    @handle_boto3_exceptions()
    def delete_resource(region: str, identifier: str) -> None:
        client = boto3.client("dynamodb", region_name=region)
        client.delete_table(TableName=identifier)
