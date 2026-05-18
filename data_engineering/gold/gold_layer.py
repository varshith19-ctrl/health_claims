"""
Gold Layer — Feature engineering for ML training.
Creates business-logic features from Silver data.
"""
import pandas as pd
import numpy as np
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from monitoring.logger import get_logger
from storage.storage_backend import storage

log = get_logger("gold.gold_layer")


def build_gold() -> pd.DataFrame:
    log.info("=== Gold Layer: Starting feature engineering ===")

    silver_key = "data/silver/silver_claims.parquet"
    if not storage.file_exists(silver_key):
        raise FileNotFoundError(f"Silver claims missing: {silver_key}")

    df = storage.read_parquet(silver_key)

    # Cost features
    df["billed_vs_avg_ratio"] = np.where(
        df["average_cost"] > 0,
        df["billed_amount"] / df["average_cost"],
        1.0,
    )

    # original missing fields logic removed as validation handles it.

    # Severity score
    severity_map = {"High": 3, "Low": 1}
    df["severity_score"] = df["severity"].map(severity_map).fillna(2)

    # Provider claim count (legitimate — uses only claim volume, NOT the target)
    provider_counts = df.groupby("provider_id")["claim_id"].transform("count")
    df["provider_claim_count"] = provider_counts

    # Patient claim frequency
    patient_counts = df.groupby("patient_id")["claim_id"].transform("count")
    df["patient_claim_frequency"] = patient_counts

    # Specialty encoding
    specialty_risk = {
        "Cardiology": 3, "Neurology": 3, "Orthopedic": 2, "General": 1,
    }
    df["specialty_risk"] = df["specialty"].map(specialty_risk).fillna(1)

    feature_cols = [
        "claim_id", "billed_vs_avg_ratio",
        "severity_score", "provider_claim_count",
        "patient_claim_frequency", "specialty_risk",
        "claim_status",
    ]
    gold = df[feature_cols].copy()

    gold_key = "data/gold/gold_claim_features.parquet"
    storage.write_parquet(gold, gold_key)
    log.info("Gold features: %d rows, %d features -> %s", len(gold), len(feature_cols) - 2, gold_key)
    log.info("=== Gold Layer: Complete ===")
    return gold


if __name__ == "__main__":
    gold = build_gold()
    print(f"Gold features: {len(gold)} rows")
    print(gold.head())
