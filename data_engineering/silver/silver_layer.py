"""
Silver Layer — Cleans bronze data, handles nulls, removes duplicates,
standardises formats, joins reference tables. Output is trusted, analysis-ready data.
"""
import pandas as pd
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from monitoring.logger import get_logger
from config.settings import BRONZE_DIR, SILVER_DIR

log = get_logger("silver.silver_layer")


def _load_bronze(name: str) -> pd.DataFrame:
    path = BRONZE_DIR / f"bronze_{name}_raw.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Bronze table missing: {path}")
    return pd.read_parquet(path)


def _clean_claims(df: pd.DataFrame) -> pd.DataFrame:
    initial = len(df)
    df = df.drop_duplicates(subset=["claim_id"])
    log.info("Claims: removed %d duplicates", initial - len(df))

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["billed_amount"] = pd.to_numeric(df["billed_amount"], errors="coerce")
    df["claim_status"] = df["claim_status"].fillna(0).astype(int)

    df["diagnosis_code"] = df["diagnosis_code"].fillna("UNKNOWN")
    df["procedure_code"] = df["procedure_code"].fillna("UNKNOWN")

    median_amount = df["billed_amount"].median()
    df["billed_amount"] = df["billed_amount"].fillna(median_amount)

    df = df.drop(columns=["_ingested_at", "_source_file"], errors="ignore")
    return df


def _clean_providers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset=["provider_id"])
    df["location"] = df["location"].fillna("Unknown")
    df["specialty"] = df["specialty"].fillna("General")
    df = df.drop(columns=["_ingested_at", "_source_file"], errors="ignore")
    return df


def _clean_diagnosis(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset=["diagnosis_code"])
    df = df.drop(columns=["_ingested_at", "_source_file"], errors="ignore")
    return df


def _clean_cost(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset=["procedure_code"])
    df["average_cost"] = pd.to_numeric(df["average_cost"], errors="coerce")
    df["expected_cost"] = pd.to_numeric(df["expected_cost"], errors="coerce")
    df = df.drop(columns=["_ingested_at", "_source_file"], errors="ignore")
    return df


def build_silver() -> dict[str, pd.DataFrame]:
    log.info("=== Silver Layer: Starting ===")
    results = {}

    try:
        claims = _clean_claims(_load_bronze("claims"))
        providers = _clean_providers(_load_bronze("providers"))
        diagnosis = _clean_diagnosis(_load_bronze("diagnosis"))
        cost = _clean_cost(_load_bronze("cost"))
    except FileNotFoundError as exc:
        log.error("Bronze data missing: %s", exc)
        raise

    claims = claims.merge(providers, on="provider_id", how="left")
    claims = claims.merge(diagnosis, on="diagnosis_code", how="left")
    claims = claims.merge(cost, on="procedure_code", how="left")
    log.info("Silver claims joined: %d rows, %d columns", len(claims), len(claims.columns))

    tables = {
        "claims": claims,
        "providers": providers,
        "diagnosis": diagnosis,
        "cost": cost,
    }

    for name, df in tables.items():
        out = SILVER_DIR / f"silver_{name}.parquet"
        df.to_parquet(out, index=False)
        results[name] = df
        log.info("Silver %s: %d rows -> %s", name, len(df), out.name)

    log.info("=== Silver Layer: Complete ===")
    return results


if __name__ == "__main__":
    tables = build_silver()
    for name, df in tables.items():
        print(f"silver_{name}: {len(df)} rows")
