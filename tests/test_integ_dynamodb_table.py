import os
import sys
import io

import boto3
import pytest

from clean_orphaned_resources.app import CleanOrphanedResources


class TestIntegDynamoDBTable:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.app = CleanOrphanedResources()

    def test_list_and_destroy(self, capfd):
        region = os.environ.get("TEST_AWS_REGION", "ap-southeast-1")
        directly_created_name = "directly_created_table"
        cloudformation_created_name = "cloudformation_created_table"
        stack_name = "dynamodb-table-test-stack"

        # Create a DynamoDB table directly
        dynamodb_client = boto3.client("dynamodb", region_name=region)
        dynamodb_client.create_table(
            TableName=directly_created_name,
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
            Tags=[{"Key": "CreatedBy", "Value": "TestUser"}],
        )

        # Create a DynamoDB table through CloudFormation
        cf_client = boto3.client("cloudformation", region_name=region)

        template_body = f"""
        Resources:
          DynamoDBTable:
            Type: AWS::DynamoDB::Table
            Properties:
              TableName: {cloudformation_created_name}
              AttributeDefinitions:
                - AttributeName: id
                  AttributeType: S
              KeySchema:
                - AttributeName: id
                  KeyType: HASH
              ProvisionedThroughput:
                ReadCapacityUnits: 1
                WriteCapacityUnits: 1
        """
        cf_client.create_stack(StackName=stack_name, TemplateBody=template_body)
        waiter = cf_client.get_waiter("stack_create_complete")
        waiter.wait(StackName=stack_name)

        try:
            # Call list method
            self.app.list(region=region)

            # Check if the output contains the directly created DynamoDB table
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

            # Check if the directly created DynamoDB table has been deleted or is in the process of being deleted
            try:
                table_description = dynamodb_client.describe_table(
                    TableName=directly_created_name
                )["Table"]
                assert table_description["TableStatus"] in ["DELETING"]
            except dynamodb_client.exceptions.ResourceNotFoundException:
                pass

        finally:
            # Clean up remaining resources
            try:
                cf_client.delete_stack(StackName=stack_name)
                waiter = cf_client.get_waiter("stack_delete_complete")
                waiter.wait(StackName=stack_name)
            except cf_client.exceptions.ValidationError:
                pass

            # Delete the directly created table if it still exists
            try:
                table_description = dynamodb_client.describe_table(
                    TableName=directly_created_name
                )["Table"]
                if table_description["TableStatus"] not in ["DELETING"]:
                    dynamodb_client.delete_table(TableName=directly_created_name)
            except dynamodb_client.exceptions.ResourceNotFoundException:
                pass
