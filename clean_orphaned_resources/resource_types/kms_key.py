from logging import getLogger

import boto3

from clean_orphaned_resources.resource_types.base import (
    ResourceTypeBase,
    handle_boto3_exceptions,
)


logger = getLogger(__name__)


class KmsKey(ResourceTypeBase):
    RESOURCE_TYPE = "AWS::KMS::Key"

    @staticmethod
    @handle_boto3_exceptions("")
    def get_tags(client, key_id: str) -> str:
        response = client.list_resource_tags(KeyId=key_id)
        return ",".join(
            [f"{tag['TagKey']}={tag['TagValue']}" for tag in response["Tags"]]
        )

    @staticmethod
    @handle_boto3_exceptions([])
    def list_resource_identifiers(region: str) -> list[tuple[str, str]]:
        client = boto3.client("kms", region_name=region)
        response = client.list_keys()
        identifiers = []

        while response:
            for key in response["Keys"]:
                key_id = key["KeyId"]
                key_metadata = client.describe_key(KeyId=key_id)
                if (
                    key_metadata["KeyMetadata"]["KeyManager"] == "CUSTOMER"
                    and key_metadata["KeyMetadata"]["KeyState"] == "Enabled"
                ):
                    tags = KmsKey.get_tags(client, key_id)
                    identifiers.append((key_id, tags))

            if "NextMarker" in response:
                response = client.list_keys(Marker=response["NextMarker"])
            else:
                response = None

        return identifiers

    @staticmethod
    @handle_boto3_exceptions()
    def delete_resource(region: str, identifier: str) -> None:
        client = boto3.client("kms", region_name=region)

        key_metadata = client.describe_key(KeyId=identifier)["KeyMetadata"]
        if key_metadata["KeyState"] not in ("PendingDeletion", "Invalid"):
            client.disable_key(KeyId=identifier)

        client.schedule_key_deletion(KeyId=identifier, PendingWindowInDays=7)
