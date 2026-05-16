"""
Test Suite 1 — Data Pipeline Validation.
Checks that all layers of the Medallion Architecture (Bronze, Silver, Gold)
have been processed correctly and contain valid data.
"""
import pytest
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import BRONZE_DIR, SILVER_DIR, GOLD_DIR


# ── Bronze Layer Tests ──────────────────────────────────────────────

class TestBronzeLayer:
    """Verify raw data was ingested into Bronze parquet files."""

    EXPECTED_FILES = [
        "bronze_claims_raw.parquet",
        "bronze_providers_raw.parquet",
        "bronze_diagnosis_raw.parquet",
        "bronze_cost_raw.parquet",
    ]

    @pytest.mark.parametrize("filename", EXPECTED_FILES)
    def test_bronze_file_exists(self, filename):
        path = BRONZE_DIR / filename
        assert path.exists(), f"Missing bronze file: {filename}"

    @pytest.mark.parametrize("filename", EXPECTED_FILES)
    def test_bronze_file_not_empty(self, filename):
        df = pd.read_parquet(BRONZE_DIR / filename)
        assert len(df) > 0, f"Bronze file is empty: {filename}"


# ── Silver Layer Tests ──────────────────────────────────────────────

class TestSilverLayer:
    """Verify cleaned/enriched data exists in Silver layer."""

    EXPECTED_FILES = [
        "silver_claims.parquet",
        "silver_providers.parquet",
        "silver_diagnosis.parquet",
        "silver_cost.parquet",
    ]

    @pytest.mark.parametrize("filename", EXPECTED_FILES)
    def test_silver_file_exists(self, filename):
        path = SILVER_DIR / filename
        assert path.exists(), f"Missing silver file: {filename}"

    @pytest.mark.parametrize("filename", EXPECTED_FILES)
    def test_silver_file_not_empty(self, filename):
        df = pd.read_parquet(SILVER_DIR / filename)
        assert len(df) > 0, f"Silver file is empty: {filename}"


# ── Gold Layer Tests ────────────────────────────────────────────────

class TestGoldLayer:
    """Verify Gold feature table is complete and valid for ML training."""

    FEATURE_COLS = [
        "billed_vs_avg_ratio",
        "severity_score",
        "provider_claim_count",
        "patient_claim_frequency",
        "specialty_risk",
    ]
    TARGET_COL = "claim_status"

    def test_gold_file_exists(self):
        path = GOLD_DIR / "gold_claim_features.parquet"
        assert path.exists(), "Gold feature file missing"

    def test_gold_row_count(self):
        df = pd.read_parquet(GOLD_DIR / "gold_claim_features.parquet")
        assert len(df) >= 100, f"Gold table too small: {len(df)} rows (expected >= 100)"

    def test_gold_has_all_feature_columns(self):
        df = pd.read_parquet(GOLD_DIR / "gold_claim_features.parquet")
        for col in self.FEATURE_COLS:
            assert col in df.columns, f"Missing feature column: {col}"

    def test_gold_has_target_column(self):
        df = pd.read_parquet(GOLD_DIR / "gold_claim_features.parquet")
        assert self.TARGET_COL in df.columns, f"Missing target column: {self.TARGET_COL}"

    def test_gold_no_nulls_in_features(self):
        df = pd.read_parquet(GOLD_DIR / "gold_claim_features.parquet")
        for col in self.FEATURE_COLS:
            null_count = df[col].isnull().sum()
            assert null_count == 0, f"Feature '{col}' has {null_count} null values"
