import os
import sys
import io

import boto3
import pytest

from clean_orphaned_resources.app import CleanOrphanedResources
from clean_orphaned_resources.resource_types.base import get_account_id


class TestIntegECRRepository:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.app = CleanOrphanedResources()

    def test_list_and_destroy(self, capfd):
        region = os.environ.get("TEST_AWS_REGION", "ap-southeast-1")
        directly_created_name = "directly-created-repository"
        cloudformation_created_name = "cloudformation-created-repository"
        stack_name = "ecr-repository-test-stack"

        # Create an ECR repository directly
        ecr_client = boto3.client("ecr", region_name=region)
        ecr_client.create_repository(repositoryName=directly_created_name)
        ecr_client.tag_resource(
            resourceArn=f"arn:aws:ecr:{region}:{get_account_id()}:repository/{directly_created_name}",
            tags=[{"Key": "CreatedBy", "Value": "TestUser"}],
        )

        # Create an ECR repository through CloudFormation
        cf_client = boto3.client("cloudformation", region_name=region)

        template_body = f"""
        Resources:
          ECRRepository:
            Type: AWS::ECR::Repository
            Properties:
              RepositoryName: {cloudformation_created_name}
        """
        cf_client.create_stack(StackName=stack_name, TemplateBody=template_body)
        waiter = cf_client.get_waiter("stack_create_complete")
        waiter.wait(StackName=stack_name)

        try:
            # Call list method
            self.app.list(region=region)

            # Check if the output contains the directly created ECR repository
            captured = capfd.readouterr()
            assert directly_created_name in captured.out
            assert "CreatedBy=TestUser" in captured.out
            assert cloudformation_created_name not in captured.out

            # Call destroy method
            selected_line = next(
                line
                for line in captured.out.splitlines()
                if directly_created_name in line
            )
            sys.stdin = io.StringIO(selected_line)
            self.app.destroy()

            # Check if the directly created ECR repository has been deleted
            try:
                ecr_client.describe_repositories(
                    repositoryNames=[directly_created_name]
                )
            except ecr_client.exceptions.RepositoryNotFoundException:
                pass
            else:
                assert False, f"{directly_created_name} should have been deleted"

        finally:
            # Clean up remaining resources
            try:
                cf_client.delete_stack(StackName=stack_name)
                waiter = cf_client.get_waiter("stack_delete_complete")
                waiter.wait(StackName=stack_name)
            except cf_client.exceptions.ValidationError:
                pass

            # Delete the directly created ECR repository if it still exists
            try:
                ecr_client.describe_repositories(
                    repositoryNames=[directly_created_name]
                )
                ecr_client.delete_repository(
                    repositoryName=directly_created_name, force=True
                )
            except ecr_client.exceptions.RepositoryNotFoundException:
                pass
