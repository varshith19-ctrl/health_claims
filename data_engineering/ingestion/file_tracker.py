"""
Delta Live Table-inspired checkpoint tracker.
Tracks which files have been ingested so re-runs only process new/modified files.
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from monitoring.logger import get_logger
from storage.storage_backend import storage

log = get_logger("ingestion.file_tracker")

CHECKPOINT_KEY = "data/checkpoints/ingestion_checkpoint.json"


def _file_hash(path: Path) -> str:
    h = hashlib.md5()
    h.update(path.read_bytes())
    return h.hexdigest()


def load_checkpoint() -> dict:
    if storage.file_exists(CHECKPOINT_KEY):
        try:
            return storage.read_json(CHECKPOINT_KEY)
        except Exception as exc:
            log.warning("Corrupt checkpoint, resetting: %s", exc)
    return {}


def save_checkpoint(state: dict) -> None:
    storage.write_json(state, CHECKPOINT_KEY)
    log.info("Checkpoint saved with %d entries", len(state))


def get_new_files(file_paths: list[Path]) -> list[Path]:
    state = load_checkpoint()
    new_files = []
    for fp in file_paths:
        key = str(fp.resolve())
        current_hash = _file_hash(fp)
        prev = state.get(key)
        if prev is None or prev.get("hash") != current_hash:
            new_files.append(fp)
            log.info("New/modified file detected: %s", fp.name)
        else:
            log.debug("Skipping already-processed file: %s", fp.name)
    return new_files


def mark_processed(file_paths: list[Path]) -> None:
    state = load_checkpoint()
    for fp in file_paths:
        state[str(fp.resolve())] = {
            "hash": _file_hash(fp),
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }
    save_checkpoint(state)
