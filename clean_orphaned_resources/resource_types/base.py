from functools import wraps
from logging import getLogger
from functools import lru_cache

import boto3
import botocore.exceptions


logger = getLogger(__name__)


@lru_cache()
def get_account_id() -> str:
    sts = boto3.client("sts")
    identity = sts.get_caller_identity()
    return identity["Account"]


def handle_boto3_exceptions(default_return_value=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except botocore.exceptions.ClientError as e:
                logger.warning(f"{func.__qualname__}: {e}")
                return default_return_value

        return wrapper

    return decorator


class ResourceTypeBase:
    RESOURCE_TYPE: str

    @staticmethod
    def list_resource_identifiers(region: str) -> list[tuple[str, str]]:
        raise NotImplementedError

    @staticmethod
    def delete_resource(region: str, identifier: str) -> None:
        raise NotImplementedError
