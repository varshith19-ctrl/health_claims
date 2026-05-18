"""
ML Training — Trains Logistic Regression and XGBoost models
for claim denial prediction.
"""
import joblib
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from monitoring.logger import get_logger
from config.settings import TEST_SPLIT_RATIO, RANDOM_STATE
from ml.evaluate import evaluate_model
from storage.storage_backend import storage

log = get_logger("ml.train")

FEATURE_COLS = [
    "billed_vs_avg_ratio",
    "severity_score", "provider_claim_count",
    "patient_claim_frequency", "specialty_risk",
]
TARGET_COL = "claim_status"


def load_training_data():
    gold_key = "data/gold/gold_claim_features.parquet"
    if not storage.file_exists(gold_key):
        raise FileNotFoundError(f"Gold features missing: {gold_key}")

    df = storage.read_parquet(gold_key)
    X = df[FEATURE_COLS]
    y = df[TARGET_COL]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SPLIT_RATIO,
        random_state=RANDOM_STATE, stratify=y,
    )
    log.info("Train: %d, Test: %d, Denial rate: %.2f%%", len(X_train), len(X_test), y.mean() * 100)
    return X_train, X_test, y_train, y_test


def train_logistic_regression(X_train, y_train):
    log.info("Training Logistic Regression...")
    model = LogisticRegression(max_iter=1000, random_state=RANDOM_STATE)
    model.fit(X_train, y_train)
    storage.write_pickle(model, "ml/models/logistic_regression.pkl")
    log.info("Logistic Regression saved to storage")
    return model


def train_xgboost(X_train, y_train):
    log.info("Training XGBoost...")
    model = XGBClassifier(
        n_estimators=200, max_depth=5, learning_rate=0.1,
        random_state=RANDOM_STATE, eval_metric="logloss",
        use_label_encoder=False,
    )
    model.fit(X_train, y_train)
    storage.write_pickle(model, "ml/models/xgboost.pkl")
    log.info("XGBoost saved to storage")
    return model


def train_all():
    log.info("=== ML Training: Start ===")
    X_train, X_test, y_train, y_test = load_training_data()

    lr_model = train_logistic_regression(X_train, y_train)
    evaluate_model(lr_model, X_test, y_test, "Logistic Regression")

    xgb_model = train_xgboost(X_train, y_train)
    evaluate_model(xgb_model, X_test, y_test, "XGBoost")

    storage.write_pickle(FEATURE_COLS, "ml/models/feature_columns.pkl")
    log.info("=== ML Training: Complete ===")
    return lr_model, xgb_model


if __name__ == "__main__":
    train_all()
