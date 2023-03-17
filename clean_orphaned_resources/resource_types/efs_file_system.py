from logging import getLogger

import boto3

from clean_orphaned_resources.resource_types.base import (
    ResourceTypeBase,
    handle_boto3_exceptions,
)


logger = getLogger(__name__)


class EfsFileSystem(ResourceTypeBase):
    RESOURCE_TYPE = "AWS::EFS::FileSystem"

    @staticmethod
    @handle_boto3_exceptions("")
    def get_tags(client, file_system_id: str) -> str:
        response = client.describe_tags(FileSystemId=file_system_id)
        tags = response.get("Tags", [])
        return ",".join([f"{tag['Key']}={tag['Value']}" for tag in tags])

    @staticmethod
    @handle_boto3_exceptions([])
    def list_resource_identifiers(region: str) -> list[tuple[str, str]]:
        client = boto3.client("efs", region_name=region)
        response = client.describe_file_systems()
        file_systems = response.get("FileSystems", [])

        identifiers = []
        for fs in file_systems:
            fs_id = fs.get("FileSystemId")
            tags = EfsFileSystem.get_tags(client, fs_id)
            identifiers.append((fs_id, tags))
        return identifiers

    @staticmethod
    @handle_boto3_exceptions()
    def delete_resource(region: str, identifier: str) -> None:
        client = boto3.client("efs", region_name=region)
        client.delete_file_system(FileSystemId=identifier)
