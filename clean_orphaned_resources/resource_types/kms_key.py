from logging import getLogger

import boto3


RESOURCE_TYPE = "AWS::KMS::Key"
logger = getLogger(__name__)


def list_resource_names(region: str) -> list[str]:
    client = boto3.client("kms", region_name=region)
    response = client.list_keys()
    names = []

    while response:
        for key in response["Keys"]:
            names.append(key["KeyId"])

        if "NextMarker" in response:
            response = client.list_keys(Marker=response["NextMarker"])
        else:
            response = None

    return names


def delete_resources(region: str, resource_names: list[str]) -> None:
    client = boto3.client("kms", region_name=region)

    for name in resource_names:
        key_metadata = client.describe_key(KeyId=name)["KeyMetadata"]
        key_state = key_metadata["KeyState"]

        if key_state not in ("PendingDeletion", "Invalid"):
            client.disable_key(KeyId=name)

        client.schedule_key_deletion(KeyId=name, PendingWindowInDays=7)
