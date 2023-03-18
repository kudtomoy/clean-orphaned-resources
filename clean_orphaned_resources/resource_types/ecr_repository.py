from logging import getLogger
from functools import lru_cache

import boto3

from clean_orphaned_resources.resource_types.base import (
    get_account_id,
    ResourceTypeBase,
    handle_boto3_exceptions,
)


logger = getLogger(__name__)


class EcrRepository(ResourceTypeBase):
    RESOURCE_TYPE = "AWS::ECR::Repository"

    @staticmethod
    @handle_boto3_exceptions("")
    def get_tags(client, arn: str) -> str:
        response = client.list_tags_for_resource(resourceArn=arn)
        return ",".join([f"{tag['Key']}={tag['Value']}" for tag in response["tags"]])

    @staticmethod
    @handle_boto3_exceptions([])
    def list_resource_identifiers(region: str) -> list[tuple[str, str]]:
        client = boto3.client("ecr", region_name=region)
        paginator = client.get_paginator("describe_repositories")

        identifiers = []

        for page in paginator.paginate():
            for repo in page["repositories"]:
                name = repo["repositoryName"]
                arn = f"arn:aws:ecr:{region}:{get_account_id()}:repository/{name}"
                tags = EcrRepository.get_tags(client, arn)
                identifiers.append((name, tags))

        return identifiers

    @staticmethod
    @handle_boto3_exceptions()
    def delete_resource(region: str, identifier: str) -> None:
        client = boto3.client("ecr", region_name=region)

        images = client.list_images(repositoryName=identifier)

        if images.get("imageIds"):
            client.batch_delete_image(
                repositoryName=identifier, imageIds=images["imageIds"]
            )

        client.delete_repository(repositoryName=identifier)
