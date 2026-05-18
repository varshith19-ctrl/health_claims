"""
Storage Backend — Unified interface for reading/writing data.
Switches between local filesystem and AWS S3 based on STORAGE_BACKEND env var.

Usage:
    from storage.storage_backend import storage
    df = storage.read_parquet("data/silver/silver_claims.parquet")
    storage.write_parquet(df, "data/silver/silver_claims.parquet")
"""
import io
import json
import pickle
import pandas as pd
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from monitoring.logger import get_logger

log = get_logger("storage.backend")


class LocalBackend:
    """Reads/writes from the local filesystem (development mode)."""

    def __init__(self, base_dir: Path):
        self.base = base_dir

    def _resolve(self, key: str) -> Path:
        return self.base / key

    def read_parquet(self, key: str) -> pd.DataFrame:
        return pd.read_parquet(self._resolve(key))

    def write_parquet(self, df: pd.DataFrame, key: str) -> None:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(path, index=False)

    def read_csv(self, key: str) -> pd.DataFrame:
        return pd.read_csv(self._resolve(key))

    def read_json(self, key: str) -> dict | list:
        return json.loads(self._resolve(key).read_text(encoding="utf-8"))

    def write_json(self, data, key: str) -> None:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    def read_pickle(self, key: str):
        import joblib
        return joblib.load(self._resolve(key))

    def write_pickle(self, obj, key: str) -> None:
        import joblib
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(obj, path)

    def read_bytes(self, key: str) -> bytes:
        return self._resolve(key).read_bytes()

    def write_bytes(self, data: bytes, key: str) -> None:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def file_exists(self, key: str) -> bool:
        return self._resolve(key).exists()

    def abs_path(self, key: str) -> Path:
        """Return the absolute local path (needed for FAISS, fitz, etc.)."""
        return self._resolve(key)


class S3Backend:
    """Reads/writes from AWS S3 (production mode). Uses local cache for heavy files."""

    def __init__(self, base_dir: Path):
        self.cache_dir = base_dir / ".s3_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, key: str) -> Path:
        safe = key.replace("/", "__").replace("\\", "__")
        return self.cache_dir / safe

    def read_parquet(self, key: str) -> pd.DataFrame:
        from storage.s3_client import download_bytes
        data = download_bytes(key)
        return pd.read_parquet(io.BytesIO(data))

    def write_parquet(self, df: pd.DataFrame, key: str) -> None:
        buf = io.BytesIO()
        df.to_parquet(buf, index=False)
        from storage.s3_client import upload_bytes
        upload_bytes(buf.getvalue(), key)

    def read_csv(self, key: str) -> pd.DataFrame:
        from storage.s3_client import download_bytes
        data = download_bytes(key)
        return pd.read_csv(io.BytesIO(data))

    def read_json(self, key: str) -> dict | list:
        from storage.s3_client import download_bytes
        return json.loads(download_bytes(key).decode("utf-8"))

    def write_json(self, data, key: str) -> None:
        from storage.s3_client import upload_bytes
        upload_bytes(json.dumps(data, indent=2, default=str).encode("utf-8"), key)

    def read_pickle(self, key: str):
        """Downloads pickle from S3, caches locally, loads with joblib."""
        import joblib
        cached = self._cache_path(key)
        if not cached.exists():
            from storage.s3_client import download_file
            download_file(key, cached)
        return joblib.load(cached)

    def write_pickle(self, obj, key: str) -> None:
        import joblib
        cached = self._cache_path(key)
        joblib.dump(obj, cached)
        from storage.s3_client import upload_file
        upload_file(cached, key)

    def read_bytes(self, key: str) -> bytes:
        from storage.s3_client import download_bytes
        return download_bytes(key)

    def write_bytes(self, data: bytes, key: str) -> None:
        from storage.s3_client import upload_bytes
        upload_bytes(data, key)

    def file_exists(self, key: str) -> bool:
        from storage.s3_client import file_exists
        return file_exists(key)

    def abs_path(self, key: str) -> Path:
        """Download to local cache and return path (for libs that need a file path)."""
        cached = self._cache_path(key)
        if not cached.exists():
            from storage.s3_client import download_file
            download_file(key, cached)
        return cached


def _create_backend():
    from config.settings import STORAGE_BACKEND, BASE_DIR
    if STORAGE_BACKEND == "s3":
        log.info("Using S3 storage backend")
        return S3Backend(BASE_DIR)
    else:
        log.info("Using local storage backend")
        return LocalBackend(BASE_DIR)


# Module-level singleton — import this everywhere
storage = _create_backend()
