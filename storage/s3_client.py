"""
S3 Client — Low-level boto3 wrapper for AWS S3 operations.
All S3 interactions go through this module.
"""
import io
import boto3
from botocore.exceptions import ClientError
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from monitoring.logger import get_logger

log = get_logger("storage.s3_client")

_client = None


def _get_client():
    """Returns a cached boto3 S3 client, initialised from environment variables."""
    global _client
    if _client is None:
        from config.settings import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
        _client = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION,
        )
        log.info("S3 client initialised (region=%s)", AWS_REGION)
    return _client


def _bucket():
    from config.settings import S3_BUCKET_NAME
    return S3_BUCKET_NAME


def upload_bytes(data: bytes, key: str) -> None:
    """Upload raw bytes to S3."""
    _get_client().put_object(Bucket=_bucket(), Key=key, Body=data)
    log.info("S3 upload: %s (%d bytes)", key, len(data))


def download_bytes(key: str) -> bytes:
    """Download raw bytes from S3."""
    resp = _get_client().get_object(Bucket=_bucket(), Key=key)
    data = resp["Body"].read()
    log.info("S3 download: %s (%d bytes)", key, len(data))
    return data


def upload_file(local_path: Path, key: str) -> None:
    """Upload a local file to S3."""
    _get_client().upload_file(str(local_path), _bucket(), key)
    log.info("S3 upload file: %s -> %s", local_path.name, key)


def download_file(key: str, local_path: Path) -> None:
    """Download an S3 object to a local file."""
    local_path.parent.mkdir(parents=True, exist_ok=True)
    _get_client().download_file(_bucket(), key, str(local_path))
    log.info("S3 download file: %s -> %s", key, local_path.name)


def file_exists(key: str) -> bool:
    """Check if a key exists in the S3 bucket."""
    try:
        _get_client().head_object(Bucket=_bucket(), Key=key)
        return True
    except ClientError:
        return False


def list_keys(prefix: str) -> list[str]:
    """List all keys under a prefix."""
    resp = _get_client().list_objects_v2(Bucket=_bucket(), Prefix=prefix)
    return [obj["Key"] for obj in resp.get("Contents", [])]


def delete_key(key: str) -> None:
    """Delete a single key from S3."""
    _get_client().delete_object(Bucket=_bucket(), Key=key)
    log.info("S3 delete: %s", key)
