"""
One-time migration script — uploads all local data to S3.
Run this once to seed the S3 bucket with existing data.

Usage:
    python scripts/upload_to_s3.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import BASE_DIR, S3_BUCKET_NAME, AWS_REGION
from storage.s3_client import upload_file, _get_client, _bucket
from monitoring.logger import get_logger

log = get_logger("scripts.upload_to_s3")

# Mapping: local directory -> S3 prefix
UPLOAD_MAP = [
    ("raw_data",           "raw_data/"),
    ("data/bronze",        "data/bronze/"),
    ("data/silver",        "data/silver/"),
    ("data/gold",          "data/gold/"),
    ("data/vector_store",  "data/vector_store/"),
    ("data/checkpoints",   "data/checkpoints/"),
    ("ml/models",          "ml/models/"),
]


def ensure_bucket_exists():
    """Create the S3 bucket if it doesn't already exist."""
    client = _get_client()
    try:
        client.head_bucket(Bucket=_bucket())
        log.info("Bucket '%s' already exists", _bucket())
    except Exception:
        log.info("Creating bucket '%s' in region '%s'", _bucket(), AWS_REGION)
        if AWS_REGION == "us-east-1":
            client.create_bucket(Bucket=_bucket())
        else:
            client.create_bucket(
                Bucket=_bucket(),
                CreateBucketConfiguration={"LocationConstraint": AWS_REGION},
            )
        log.info("Bucket created successfully")


def upload_directory(local_dir: Path, s3_prefix: str):
    """Upload all files in a local directory to S3 under the given prefix."""
    if not local_dir.exists():
        log.warning("Skipping %s — directory does not exist", local_dir)
        return 0

    count = 0
    for file_path in local_dir.rglob("*"):
        if file_path.is_file():
            relative = file_path.relative_to(local_dir)
            s3_key = s3_prefix + str(relative).replace("\\", "/")
            upload_file(file_path, s3_key)
            count += 1
    return count


def main():
    log.info("=" * 60)
    log.info("S3 Migration — Uploading local data to s3://%s", S3_BUCKET_NAME)
    log.info("=" * 60)

    ensure_bucket_exists()

    total = 0
    for local_rel, s3_prefix in UPLOAD_MAP:
        local_dir = BASE_DIR / local_rel
        log.info("--- %s -> s3://%s/%s ---", local_rel, S3_BUCKET_NAME, s3_prefix)
        count = upload_directory(local_dir, s3_prefix)
        total += count
        log.info("    Uploaded %d files", count)

    log.info("=" * 60)
    log.info("Migration complete: %d total files uploaded to S3", total)
    log.info("=" * 60)


if __name__ == "__main__":
    main()
