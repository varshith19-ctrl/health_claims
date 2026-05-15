"""
ML Prediction — Runs inference with SHAP explanations.
Returns top 2 features as percentages of contribution.
"""
import joblib
import shap
import numpy as np
import pandas as pd
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from monitoring.logger import get_logger
from config.settings import MODEL_DIR

log = get_logger("ml.predict")

FEATURE_DISPLAY_NAMES = {
    "billed_vs_avg_ratio": "Billed vs Regional Average",
    "severity_score": "Diagnosis Severity",
    "provider_claim_count": "Provider Claim Volume",
    "patient_claim_frequency": "Patient Claim Frequency",
    "specialty_risk": "Specialty Risk Level",
}

_model = None
_explainer = None
_feature_cols = None


def _load_model():
    """
    Loads the trained XGBoost model, feature columns, and initializes the SHAP explainer.
    Caches these in memory to avoid reloading on every prediction request.
    """
    global _model, _explainer, _feature_cols
    if _model is not None:
        return

    model_path = MODEL_DIR / "xgboost.pkl"
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")

    _model = joblib.load(model_path)
    _feature_cols = joblib.load(MODEL_DIR / "feature_columns.pkl")
    _explainer = shap.TreeExplainer(_model)
    log.info("Model and SHAP explainer loaded")


def predict_claim(features: dict) -> dict:
    """
    Predicts the denial probability for a given claim and generates SHAP-based feature explanations.
    
    Args:
        features (dict): A dictionary of engineered features.
        
    Returns:
        dict: A dictionary containing the prediction (0 or 1), probability, risk level,
              feature contributions (%), top 2 features, and human-readable reasons.
    """
    _load_model()

    df = pd.DataFrame([features])[_feature_cols]
    
    # Get the probability of the positive class (denial)
    probability = float(_model.predict_proba(df)[:, 1][0])
    prediction = int(probability >= 0.5)
    
    # Categorize risk based on probability thresholds
    risk_level = "HIGH" if probability >= 0.7 else "MEDIUM" if probability >= 0.4 else "LOW"

    # Generate SHAP values for the given features
    shap_values = _explainer.shap_values(df)
    shap_row = shap_values[0] if isinstance(shap_values, list) else shap_values[0]

    # Calculate absolute contributions to convert them into percentages
    abs_shap = np.abs(shap_row)
    total = abs_shap.sum()
    percentages = (abs_shap / total * 100) if total > 0 else abs_shap

    feature_contributions = {}
    for i, col in enumerate(_feature_cols):
        display_name = FEATURE_DISPLAY_NAMES.get(col, col)
        feature_contributions[display_name] = round(float(percentages[i]), 1)

    sorted_features = sorted(feature_contributions.items(), key=lambda x: x[1], reverse=True)
    top_2 = sorted_features[:2]

    # Format the top contributing features into readable reasons
    reasons = []
    for feat_name, pct in top_2:
        reasons.append(f"{feat_name} ({pct}% contribution)")

    # Compute a 0–100 risk score for direct numerical display
    risk_score = round(probability * 100, 1)

    result = {
        "prediction": prediction,
        "probability": round(probability, 4),
        "risk_level": risk_level,
        "risk_score": risk_score,
        "feature_contributions": feature_contributions,
        "top_2_features": [{"feature": f, "percentage": p} for f, p in top_2],
        "reasons": reasons,
    }
    log.info("Prediction: %s (%.2f%%), Risk: %s", "DENIED" if prediction else "ACCEPTED", probability * 100, risk_level)
    return result
