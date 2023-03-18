import os
import sys
import io

import boto3
import pytest

from clean_orphaned_resources.app import CleanOrphanedResources


class TestIntegEFSFilesystem:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.app = CleanOrphanedResources()

    def test_list_and_destroy(self, capfd):
        region = os.environ.get("TEST_AWS_REGION", "ap-southeast-1")
        directly_created_name = "directly-created-filesystem"
        cloudformation_created_name = "cloudformation-created-filesystem"
        stack_name = "efs-filesystem-test-stack"

        # Create an EFS filesystem directly
        efs_client = boto3.client("efs", region_name=region)
        directly_created_filesystem = efs_client.create_file_system(
            CreationToken=directly_created_name
        )
        efs_client.create_tags(
            FileSystemId=directly_created_filesystem["FileSystemId"],
            Tags=[
                {"Key": "Name", "Value": directly_created_name},
                {"Key": "CreatedBy", "Value": "TestUser"},
            ],
        )

        # Create an EFS filesystem through CloudFormation
        cf_client = boto3.client("cloudformation", region_name=region)

        template_body = f"""
        Resources:
          EFSFileSystem:
            Type: AWS::EFS::FileSystem
            Properties:
              FileSystemTags:
                - Key: Name
                  Value: {cloudformation_created_name}
        """
        cf_client.create_stack(StackName=stack_name, TemplateBody=template_body)
        waiter = cf_client.get_waiter("stack_create_complete")
        waiter.wait(StackName=stack_name)

        try:
            # Call list method
            self.app.list(region=region)

            # Check if the output contains the directly created EFS filesystem
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

            # Check if the directly created EFS filesystem has been deleted or is in the process of being deleted
            try:
                file_system_description = efs_client.describe_file_systems(
                    FileSystemId=directly_created_filesystem["FileSystemId"]
                )["FileSystems"][0]
                assert file_system_description["LifeCycleState"] in [
                    "deleted",
                    "deleting",
                ]
            except efs_client.exceptions.FileSystemNotFound:
                pass

        finally:
            # Clean up remaining resources
            try:
                cf_client.delete_stack(StackName=stack_name)
                waiter = cf_client.get_waiter("stack_delete_complete")
                waiter.wait(StackName=stack_name)
            except cf_client.exceptions.ValidationError:
                pass

            # Delete the directly created EFS filesystem if it still exists
            try:
                efs_client.describe_file_systems(
                    FileSystemId=directly_created_filesystem["FileSystemId"]
                )
                efs_client.delete_file_system(
                    FileSystemId=directly_created_filesystem["FileSystemId"]
                )
            except efs_client.exceptions.FileSystemNotFound:
                pass
