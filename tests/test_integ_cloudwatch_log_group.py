import os
import sys
import io

import boto3
import pytest

from clean_orphaned_resources.app import CleanOrphanedResources


class TestIntegCloudWatchLogGroup:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.app = CleanOrphanedResources()

    def test_list_and_destroy(self, capfd):
        region = os.environ.get("TEST_AWS_REGION", "ap-southeast-1")
        directly_created_name = "directly_created_log_group"
        cloudformation_created_name = "cloudformation_created_log_group"
        stack_name = "cloudwatch-log-test-stack"

        # Create a log group directly
        logs_client = boto3.client("logs", region_name=region)
        logs_client.create_log_group(logGroupName=directly_created_name)
        logs_client.tag_log_group(
            logGroupName=directly_created_name, tags={"CreatedBy": "TestUser"}
        )

        # Create a log group through CloudFormation
        cf_client = boto3.client("cloudformation", region_name=region)

        template_body = f"""
        Resources:
          LogGroup:
            Type: AWS::Logs::LogGroup
            Properties:
              LogGroupName: {cloudformation_created_name}
        """
        cf_client.create_stack(StackName=stack_name, TemplateBody=template_body)
        waiter = cf_client.get_waiter("stack_create_complete")
        waiter.wait(StackName=stack_name)

        try:
            # Call list method
            self.app.list(region=region)

            # Check if the output contains the directly created log group
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

            # Check if the directly created log group has been deleted
            response = logs_client.describe_log_groups(
                logGroupNamePrefix=directly_created_name
            )
            assert len(response["logGroups"]) == 0

        finally:
            # Clean up remaining resources
            try:
                cf_client.delete_stack(StackName=stack_name)
                waiter = cf_client.get_waiter("stack_delete_complete")
                waiter.wait(StackName=stack_name)
            except cf_client.exceptions.ValidationError:
                pass

            # Delete the directly created log group if it still exists
            try:
                logs_client.describe_log_groups(
                    logGroupNamePrefix=directly_created_name
                )
                logs_client.delete_log_group(logGroupName=directly_created_name)
            except logs_client.exceptions.ResourceNotFoundException:
                pass
