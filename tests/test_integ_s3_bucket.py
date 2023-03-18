import os
import sys
import io
import random
import string

import boto3
import botocore.exceptions
import pytest

from clean_orphaned_resources.app import CleanOrphanedResources


class TestIntegS3Bucket:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.app = CleanOrphanedResources()

    def test_list_and_destroy(self, capfd):
        region = os.environ.get("TEST_AWS_REGION", "ap-southeast-1")
        random_string = "".join(random.choices(string.ascii_lowercase, k=8))
        directly_created_name = "directly-created-bucket-" + random_string
        cloudformation_created_name = "cloudformation-created-bucket-" + random_string
        stack_name = "s3-bucket-test-stack"

        # Create an S3 bucket directly
        s3_client = boto3.client("s3", region_name=region)
        s3_client.create_bucket(
            Bucket=directly_created_name,
            CreateBucketConfiguration={"LocationConstraint": region},
        )
        s3_client.put_bucket_tagging(
            Bucket=directly_created_name,
            Tagging={"TagSet": [{"Key": "CreatedBy", "Value": "TestUser"}]},
        )

        # Create an S3 bucket through CloudFormation
        cf_client = boto3.client("cloudformation", region_name=region)

        template_body = f"""
        Resources:
          S3Bucket:
            Type: AWS::S3::Bucket
            Properties:
              BucketName: {cloudformation_created_name}
        """
        cf_client.create_stack(StackName=stack_name, TemplateBody=template_body)
        waiter = cf_client.get_waiter("stack_create_complete")
        waiter.wait(StackName=stack_name)

        try:
            # Call list method
            self.app.list(region=region)

            # Check if the output contains the directly created S3 bucket
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

            # Check if the directly created S3 bucket has been deleted
            try:
                s3_client.head_bucket(Bucket=directly_created_name)
                assert False, "Bucket should be deleted"
            except (
                s3_client.exceptions.NoSuchBucket,
                botocore.exceptions.ClientError,
            ) as e:
                if (
                    isinstance(e, botocore.exceptions.ClientError)
                    and e.response["Error"]["Code"] == "404"
                ):
                    pass
                else:
                    raise e

        finally:
            # Clean up remaining resources
            try:
                cf_client.delete_stack(StackName=stack_name)
                waiter = cf_client.get_waiter("stack_delete_complete")
                waiter.wait(StackName=stack_name)
            except cf_client.exceptions.ValidationError:
                pass

            # Delete the directly created bucket if it still exists
            try:
                s3_client.head_bucket(Bucket=directly_created_name)
                s3_client.delete_bucket(Bucket=directly_created_name)
            except (
                s3_client.exceptions.NoSuchBucket,
                botocore.exceptions.ClientError,
            ) as e:
                if (
                    isinstance(e, botocore.exceptions.ClientError)
                    and e.response["Error"]["Code"] == "404"
                ):
                    pass
                else:
                    raise e
