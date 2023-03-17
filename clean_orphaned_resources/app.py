from collections import defaultdict
import logging
import sys

import fire
import boto3
import botocore.exceptions

from clean_orphaned_resources import resource_types


protected_resource_keywords = ["do-not-delete"]

logger = logging.getLogger(__name__)
logging.basicConfig()
logger.setLevel(logging.INFO)


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
    region: str, resource_type: str, resource_name: str
) -> None:
    print(f"{region},{resource_type},{resource_name}")


def parse_orphaned_resource(text: str) -> (str, str, str):
    region, resource_type, resource_name = text.split(",")
    return region, resource_type, resource_name


def is_protected(name: str) -> bool:
    for keyword in protected_resource_keywords:
        if keyword in name:
            return True
    return False


def list_orphaned_resources() -> None:
    for region in get_regions():
        logger.info(f"Fetching resources in {region} region...")
        stack_resources = get_stack_resources(region)

        for resource_type in resource_types.modules.values():
            for name in resource_type.list_resource_names(region):
                if (
                    not is_protected(name)
                    and name not in stack_resources[resource_type.RESOURCE_TYPE]
                ):
                    print_orphaned_resource(region, resource_type.RESOURCE_TYPE, name)


def destroy_orphaned_resources() -> None:
    lines = sys.stdin.readlines()

    for line in lines:
        region, resource_type, resource_name = parse_orphaned_resource(line.strip())
        try:
            logger.info(f"Deleting {resource_name} ({resource_type})...")
            modules.modules[resource_type].delete_resources(region, [resource_name])
        except botocore.exceptions.ClientError as e:
            logger.warning(e)


class CleanOrphanedResources:
    def list(self):
        """
        Lists the candidate resources to be deleted after an AWS CDK 'destroy' operation.

        Usage: app.py list
        """
        list_orphaned_resources()

    def destroy(self):
        """
        Deletes the candidate resources after they are passed through standard input.

        Usage: app.py destroy
        """
        destroy_orphaned_resources()


def main():
    fire.Fire(CleanOrphanedResources)


if __name__ == "__main__":
    main()
