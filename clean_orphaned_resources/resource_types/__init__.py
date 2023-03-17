from clean_orphaned_resources.resource_types import cloudwatch_log_group
from clean_orphaned_resources.resource_types import ecr_repository
from clean_orphaned_resources.resource_types import kms_key
from clean_orphaned_resources.resource_types import s3_bucket


imports = [cloudwatch_log_group, ecr_repository, kms_key, s3_bucket]

modules = {}
for module in imports:
    modules[module.RESOURCE_TYPE] = module
