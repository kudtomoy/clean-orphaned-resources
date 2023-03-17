from clean_orphaned_resources.resource_types import cloudwatch_log_group
from clean_orphaned_resources.resource_types import dynamodb_table
from clean_orphaned_resources.resource_types import ecr_repository
from clean_orphaned_resources.resource_types import efs_file_system
from clean_orphaned_resources.resource_types import kms_key
from clean_orphaned_resources.resource_types import s3_bucket


_import_classes = [
    cloudwatch_log_group.CloudWatchLogs,
    dynamodb_table.DynamoDbTable,
    ecr_repository.EcrRepository,
    efs_file_system.EfsFileSystem,
    kms_key.KmsKey,
    s3_bucket.S3Bucket,
]

classes = {}
for _class in _import_classes:
    classes[_class.RESOURCE_TYPE] = _class
