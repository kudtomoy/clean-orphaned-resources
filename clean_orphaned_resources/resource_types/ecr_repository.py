from logging import getLogger

import boto3


RESOURCE_TYPE = "AWS::ECR::Repository"
logger = getLogger(__name__)


def list_resource_names(region: str) -> list[str]:
    client = boto3.client("ecr", region_name=region)
    paginator = client.get_paginator("describe_repositories")

    names = []

    for page in paginator.paginate():
        for repo in page["repositories"]:
            names.append(repo["repositoryName"])

    return names


def delete_resources(region: str, resource_names: list[str]) -> None:
    client = boto3.client("ecr", region_name=region)

    for name in resource_names:
        images = client.list_images(repositoryName=name)

        if images.get("imageIds"):
            client.batch_delete_image(repositoryName=name, imageIds=images["imageIds"])

        client.delete_repository(repositoryName=name)
