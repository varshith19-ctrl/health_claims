"""
Test Suite 2 — ML Model Validation.
Checks that the model loads, predicts correctly, SHAP works,
and model performance meets minimum thresholds.
"""
import pytest
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import MODEL_DIR, GOLD_DIR


# ── Model File Tests ────────────────────────────────────────────────

class TestModelFiles:
    """Verify trained model artifacts exist on disk."""

    def test_xgboost_model_exists(self):
        assert (MODEL_DIR / "xgboost.pkl").exists(), "XGBoost model file missing"

    def test_feature_columns_exist(self):
        assert (MODEL_DIR / "feature_columns.pkl").exists(), "Feature columns file missing"

    def test_logistic_regression_exists(self):
        assert (MODEL_DIR / "logistic_regression.pkl").exists(), "Logistic Regression model missing"


# ── Model Loading & SHAP Tests ──────────────────────────────────────

class TestModelLoading:
    """Verify model loads and SHAP explainer initializes without error."""

    def test_model_loads(self):
        model = joblib.load(MODEL_DIR / "xgboost.pkl")
        assert model is not None, "Model loaded as None"

    def test_feature_columns_load(self):
        cols = joblib.load(MODEL_DIR / "feature_columns.pkl")
        assert isinstance(cols, list), "Feature columns should be a list"
        assert len(cols) == 5, f"Expected 5 feature columns, got {len(cols)}"

    def test_shap_explainer_initializes(self):
        import shap
        model = joblib.load(MODEL_DIR / "xgboost.pkl")
        explainer = shap.TreeExplainer(model)
        assert explainer is not None, "SHAP explainer failed to initialize"


# ── Prediction Tests ────────────────────────────────────────────────

class TestPrediction:
    """Verify predict_claim returns valid, complete output."""

    SAMPLE_FEATURES = {
        "billed_vs_avg_ratio": 1.5,
        "severity_score": 2,
        "provider_claim_count": 50,
        "patient_claim_frequency": 3,
        "specialty_risk": 1,
    }

    def test_prediction_runs_without_error(self):
        from ml.predict import predict_claim
        result = predict_claim(self.SAMPLE_FEATURES)
        assert result is not None

    def test_prediction_has_required_keys(self):
        from ml.predict import predict_claim
        result = predict_claim(self.SAMPLE_FEATURES)
        required_keys = ["prediction", "probability", "risk_level", "reasons", "feature_contributions"]
        for key in required_keys:
            assert key in result, f"Missing key in prediction output: {key}"

    def test_probability_in_valid_range(self):
        from ml.predict import predict_claim
        result = predict_claim(self.SAMPLE_FEATURES)
        assert 0.0 <= result["probability"] <= 1.0, f"Probability out of range: {result['probability']}"

    def test_risk_level_is_valid(self):
        from ml.predict import predict_claim
        result = predict_claim(self.SAMPLE_FEATURES)
        assert result["risk_level"] in ("HIGH", "MEDIUM", "LOW"), f"Invalid risk level: {result['risk_level']}"

    def test_feature_contributions_sum_roughly_100(self):
        from ml.predict import predict_claim
        result = predict_claim(self.SAMPLE_FEATURES)
        total = sum(result["feature_contributions"].values())
        assert 95 <= total <= 105, f"Feature contributions should sum to ~100%, got {total}%"

    def test_no_missing_features_in_output(self):
        from ml.predict import predict_claim
        result = predict_claim(self.SAMPLE_FEATURES)
        assert len(result["feature_contributions"]) == 5, "Expected 5 feature contributions"


# ── Model Performance Tests ─────────────────────────────────────────

class TestModelPerformance:
    """Verify model accuracy meets minimum production thresholds."""

    def test_accuracy_above_threshold(self):
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score

        model = joblib.load(MODEL_DIR / "xgboost.pkl")
        feature_cols = joblib.load(MODEL_DIR / "feature_columns.pkl")

        df = pd.read_parquet(GOLD_DIR / "gold_claim_features.parquet")
        X = df[feature_cols]
        y = df["claim_status"]
        _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        assert accuracy >= 0.75, f"Model accuracy too low: {accuracy:.4f} (min 0.75)"

    def test_roc_auc_above_threshold(self):
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import roc_auc_score

        model = joblib.load(MODEL_DIR / "xgboost.pkl")
        feature_cols = joblib.load(MODEL_DIR / "feature_columns.pkl")

        df = pd.read_parquet(GOLD_DIR / "gold_claim_features.parquet")
        X = df[feature_cols]
        y = df["claim_status"]
        _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

        y_proba = model.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, y_proba)
        assert auc >= 0.80, f"ROC-AUC too low: {auc:.4f} (min 0.80)"
