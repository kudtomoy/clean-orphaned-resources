from collections import defaultdict
import logging
import sys

import fire
import boto3
import botocore.exceptions

from clean_orphaned_resources import resource_types


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def get_regions() -> list[str]:
    ec2_client = boto3.client("ec2")
    regions = ec2_client.describe_regions()
    region_names = [region["RegionName"] for region in regions["Regions"]]
    return region_names


def get_stack_resources(region: str) -> dict[str, dict[str, dict[str, str]]]:
    """
    Return a nested dict like: {"AWS::S3::Bucket": {"SampleBucket": {...}}}
    """
    resources = defaultdict(lambda: defaultdict(dict))

    cfn_client = boto3.client("cloudformation", region_name=region)
    paginator = cfn_client.get_paginator("list_stacks")
    target_statuses = [
        "CREATE_COMPLETE",
        "UPDATE_COMPLETE",
        "ROLLBACK_COMPLETE",
        "UPDATE_ROLLBACK_COMPLETE",
    ]

    for page in paginator.paginate():
        for stack in page["StackSummaries"]:
            if stack["StackStatus"] in target_statuses:
                stack_name = stack["StackName"]
                stack_resources = cfn_client.describe_stack_resources(
                    StackName=stack_name
                )

                for stack_resource in stack_resources["StackResources"]:
                    if "PhysicalResourceId" in stack_resource:
                        resources[stack_resource["ResourceType"]][
                            stack_resource["PhysicalResourceId"]
                        ] = {"resource_status": stack_resource["ResourceStatus"]}
    return resources


def print_orphaned_resource(
    region: str, resource_type: str, resource_name: str, tags: str
) -> None:
    print(f"{region},{resource_type},{resource_name},{tags}")


def parse_orphaned_resource(text: str) -> (str, str, str, str):
    if "#" in text:
        text = text.split("#", 1)[0]

    parts = text.split(",")
    region = parts[0]
    resource_type = parts[1]
    resource_name = parts[2]

    tags = ""
    if len(parts) > 3:
        tags = parts[3]

    return region, resource_type, resource_name, tags


def list_orphaned_resources() -> None:
    for region in get_regions():
        logger.info(f"Fetching resources in {region} region...")
        stack_resources = get_stack_resources(region)

        for resource_type in resource_types.classes.values():
            for name, tags in resource_type.list_resource_identifiers(region):
                if name not in stack_resources[resource_type.RESOURCE_TYPE]:
                    print_orphaned_resource(
                        region, resource_type.RESOURCE_TYPE, name, tags
                    )


def destroy_orphaned_resources() -> None:
    lines = sys.stdin.readlines()

    for line in lines:
        region, resource_type, resource_name, tags = parse_orphaned_resource(
            line.strip()
        )
        try:
            logger.info(f"Deleting {resource_name} ({resource_type})...")
            resource_types.classes[resource_type].delete_resource(region, resource_name)
        except botocore.exceptions.ClientError as e:
            logger.warning(e)


class CleanOrphanedResources:
    def list(self):
        """
        Lists the candidate resources to be deleted after an AWS CDK 'destroy' operation.

        Usage: clean-orphaned-resources list
        """
        list_orphaned_resources()

    def destroy(self):
        """
        Deletes the candidate resources after they are passed through standard input.

        Usage: clean-orphaned-resources destroy
        """
        destroy_orphaned_resources()


def main():
    fire.Fire(CleanOrphanedResources)


if __name__ == "__main__":
    main()
