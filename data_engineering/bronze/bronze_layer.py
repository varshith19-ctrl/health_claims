"""
Bronze Layer — Ingests raw CSV files into Bronze (Parquet).
Mirrors Databricks DLT: raw data stored as-is with metadata columns.
No cleaning happens here.
"""
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from monitoring.logger import get_logger
from config.settings import RAW_FILES, BRONZE_DIR
from data_engineering.ingestion.file_tracker import get_new_files, mark_processed

log = get_logger("bronze.bronze_layer")

SCHEMA = {
    "claims": {
        "claim_id": "str", "patient_id": "str", "provider_id": "str",
        "diagnosis_code": "str", "procedure_code": "str",
        "billed_amount": "float64", "date": "str", "claim_status": "int64",
    },
    "providers": {
        "provider_id": "str", "doctor_name": "str",
        "specialty": "str", "location": "str",
    },
    "diagnosis": {
        "diagnosis_code": "str", "category": "str", "severity": "str",
    },
    "cost": {
        "procedure_code": "str", "average_cost": "float64",
        "expected_cost": "float64", "region": "str",
    },
}


def _enforce_schema(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    schema = SCHEMA.get(table_name, {})
    for col, dtype in schema.items():
        if col in df.columns:
            try:
                df[col] = df[col].astype(dtype)
            except (ValueError, TypeError):
                log.warning("Could not cast %s.%s to %s", table_name, col, dtype)
    return df


def ingest_to_bronze() -> dict[str, pd.DataFrame]:
    log.info("=== Bronze Layer: Starting ingestion ===")
    results = {}

    all_files = [fp for fp in RAW_FILES.values() if fp.exists()]
    new_files = get_new_files(all_files)

    if not new_files:
        log.info("No new files to process. Loading existing bronze data.")
        for name, fp in RAW_FILES.items():
            bronze_path = BRONZE_DIR / f"bronze_{name}_raw.parquet"
            if bronze_path.exists():
                results[name] = pd.read_parquet(bronze_path)
        return results

    processed = []
    for name, fp in RAW_FILES.items():
        if fp not in new_files:
            bronze_path = BRONZE_DIR / f"bronze_{name}_raw.parquet"
            if bronze_path.exists():
                results[name] = pd.read_parquet(bronze_path)
            continue

        try:
            log.info("Ingesting %s from %s", name, fp.name)
            df = pd.read_csv(fp)
            df = _enforce_schema(df, name)
            df["_ingested_at"] = datetime.now(timezone.utc).isoformat()
            df["_source_file"] = fp.name

            out_path = BRONZE_DIR / f"bronze_{name}_raw.parquet"
            df.to_parquet(out_path, index=False)
            results[name] = df
            processed.append(fp)
            log.info("Bronze %s: %d rows written to %s", name, len(df), out_path.name)
        except Exception as exc:
            log.error("Failed to ingest %s: %s", name, exc)
            raise

    if processed:
        mark_processed(processed)

    log.info("=== Bronze Layer: Complete (%d tables) ===", len(results))
    return results


if __name__ == "__main__":
    tables = ingest_to_bronze()
    for name, df in tables.items():
        print(f"bronze_{name}_raw: {len(df)} rows, {list(df.columns)}")
