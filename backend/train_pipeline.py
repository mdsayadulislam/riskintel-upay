"""
RiskIntel upay - Track 01: Trust & Risk Intelligence
File: backend/train_pipeline.py

This script generates synthetic MFS (Mobile Financial Services) transaction data
tailored to Bangladeshi upay usage patterns, trains a high-performance LightGBM
Classifier for fraud detection, fits a SHAP TreeExplainer for local explainability,
and saves the artifacts to disk with robust path handling.
"""

import os
import sys
import logging
import joblib
import numpy as np
import pandas as pd
import shap
from lightgbm import LGBMClassifier
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("RiskIntel-TrainPipeline")

# Robust directory and path resolution
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

MODEL_FILE_PATH = os.path.join(MODELS_DIR, "fraud_model.pkl")
EXPLAINER_FILE_PATH = os.path.join(MODELS_DIR, "shap_explainer.pkl")
DATASET_FILE_PATH = os.path.join(DATA_DIR, "synthetic_upay_txns.csv")

FEATURE_COLUMNS = [
    "txn_amount",
    "hour_of_day",
    "device_change_count_30d",
    "velocity_last_1h",
    "agent_distance_km",
    "failed_pin_attempts_24h",
    "is_cash_out"
]
TARGET_COLUMN = "is_fraud"


def generate_synthetic_upay_data(n_samples: int = 12000, random_state: int = 42) -> pd.DataFrame:
    """
    Generate 12,000 synthetic MFS transaction rows simulating realistic upay behavior.
    Features:
      - txn_amount (float, in BDT)
      - hour_of_day (int, 0-23)
      - device_change_count_30d (int)
      - velocity_last_1h (int)
      - agent_distance_km (float)
      - failed_pin_attempts_24h (int)
      - is_cash_out (int 0 or 1)

    Synthetic Target Logic:
      'is_fraud' (binary 0/1) is heavily correlated with:
        * High transaction amounts (>15,000 BDT)
        * Midnight velocity spikes (hours 1 to 4)
        * Multiple device changes (>=2)
        * Repeated failed PIN attempts (>=2)
    """
    logger.info("Generating %d synthetic upay transaction records (random_state=%d)...", n_samples, random_state)
    np.random.seed(random_state)

    # 1. Transaction Amount (BDT)
    # Typical MFS transactions: small-medium transfers with right-skewed tail up to daily ceiling
    base_amount = np.random.exponential(scale=3200.0, size=n_samples) + 60.0
    large_transfer_mask = np.random.rand(n_samples) < 0.14
    base_amount[large_transfer_mask] += np.random.uniform(13000.0, 21000.0, size=np.sum(large_transfer_mask))
    txn_amount = np.round(np.clip(base_amount, 50.0, 28000.0), 2)

    # 2. Hour of Day (0-23)
    # Daytime concentration (08:00 to 22:00); sharp lull during midnight hours (01:00 to 04:00)
    hour_distribution = np.array([
        0.015, 0.008, 0.005, 0.005, 0.008, 0.015, 0.025, 0.040,  # 00:00 - 07:00
        0.060, 0.070, 0.075, 0.070, 0.065, 0.060, 0.065, 0.070,  # 08:00 - 15:00
        0.075, 0.080, 0.075, 0.060, 0.045, 0.035, 0.025, 0.019   # 16:00 - 23:00
    ])
    hour_distribution = hour_distribution / np.sum(hour_distribution)
    hour_of_day = np.random.choice(np.arange(24), size=n_samples, p=hour_distribution)

    # 3. Device Change Count in Last 30 Days (0, 1, 2, 3, 4)
    # Mostly 0 or 1 for genuine users; multiple changes indicate device takeover / SIM swap
    device_change_probs = np.array([0.76, 0.17, 0.045, 0.020, 0.005])
    device_change_probs = device_change_probs / np.sum(device_change_probs)
    device_change_count_30d = np.random.choice([0, 1, 2, 3, 4], size=n_samples, p=device_change_probs)

    # 4. Velocity in Last 1 Hour (Number of transactions)
    velocity_last_1h = np.random.poisson(lam=1.1, size=n_samples)
    velocity_last_1h = np.clip(velocity_last_1h, 0, 15)

    # 5. Agent Distance in Kilometers
    # Typically 0.2 km - 6 km; outliers represent remote agent points
    agent_dist = np.random.gamma(shape=2.0, scale=2.5, size=n_samples)
    agent_distance_km = np.round(np.clip(agent_dist, 0.1, 45.0), 2)

    # 6. Failed PIN Attempts in Last 24 Hours (0, 1, 2, 3, 4)
    # Legitimate users almost always enter correctly (0 or 1); repeated failures (>=2) indicate brute force
    pin_fail_probs = np.array([0.84, 0.11, 0.035, 0.012, 0.003])
    pin_fail_probs = pin_fail_probs / np.sum(pin_fail_probs)
    failed_pin_attempts_24h = np.random.choice([0, 1, 2, 3, 4], size=n_samples, p=pin_fail_probs)

    # 7. Cash-out Flag (Binary 0 or 1)
    is_cash_out = np.random.choice([0, 1], size=n_samples, p=[0.62, 0.38])

    # ----------------------------------------------------
    # Target Correlation & Fraud Signal Synthesis
    # ----------------------------------------------------
    midnight_window = (hour_of_day >= 1) & (hour_of_day <= 4)
    midnight_velocity_spike = midnight_window & (velocity_last_1h >= 3)
    high_amount_condition = (txn_amount > 15000.0)
    multiple_device_condition = (device_change_count_30d >= 2)
    repeated_pin_condition = (failed_pin_attempts_24h >= 2)

    # Calibrated latent log-odds function
    fraud_latent = (
        -4.25
        + 3.20 * high_amount_condition
        + 2.60 * midnight_window
        + 2.50 * midnight_velocity_spike
        + 2.75 * multiple_device_condition
        + 3.10 * repeated_pin_condition
        + 1.25 * (is_cash_out == 1)
        + 1.15 * (velocity_last_1h >= 4)
        + 0.04 * agent_distance_km
        + np.random.normal(loc=0.0, scale=0.6, size=n_samples)
    )

    fraud_probability = 1.0 / (1.0 + np.exp(-fraud_latent))
    is_fraud = (fraud_probability > 0.5).astype(int)

    df = pd.DataFrame({
        "txn_amount": txn_amount,
        "hour_of_day": hour_of_day.astype(int),
        "device_change_count_30d": device_change_count_30d.astype(int),
        "velocity_last_1h": velocity_last_1h.astype(int),
        "agent_distance_km": agent_distance_km,
        "failed_pin_attempts_24h": failed_pin_attempts_24h.astype(int),
        "is_cash_out": is_cash_out.astype(int),
        "is_fraud": is_fraud.astype(int),
    })

    fraud_total = int(df["is_fraud"].sum())
    fraud_pct = (fraud_total / n_samples) * 100.0
    logger.info("Dataset generated successfully. Total: %d, Fraud: %d (%.2f%%)", n_samples, fraud_total, fraud_pct)
    return df


def run_pipeline() -> None:
    """
    Executes the end-to-end ML training pipeline:
    1. Generates synthetic data.
    2. Saves dataset to data/synthetic_upay_txns.csv.
    3. Trains LightGBM Classifier (100 estimators, random_state=42).
    4. Evaluates performance on stratified test split.
    5. Fits and exports SHAP TreeExplainer.
    6. Persists artifacts to models/ directory.
    """
    logger.info("=== Starting RiskIntel upay ML Training Pipeline ===")

    # Step 1: Generate synthetic dataset
    df = generate_synthetic_upay_data(n_samples=12000, random_state=42)

    # Step 2: Save dataset to disk
    logger.info("Saving synthetic transactions dataset to: %s", DATASET_FILE_PATH)
    df.to_csv(DATASET_FILE_PATH, index=False)
    logger.info("Dataset saved successfully (%d rows, %d columns).", len(df), len(df.columns))

    # Step 3: Train / Validation Split
    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    logger.info("Train set shape: %s | Test set shape: %s", X_train.shape, X_test.shape)

    # Step 4: Model Training (LightGBM Classifier)
    logger.info("Training LightGBM Classifier (n_estimators=100, random_state=42)...")
    clf = LGBMClassifier(
        n_estimators=100,
        random_state=42,
        objective="binary",
        learning_rate=0.08,
        num_leaves=31,
        verbose=-1
    )
    clf.fit(X_train, y_train)

    # Step 5: Evaluation
    y_test_pred = clf.predict(X_test)
    y_test_prob = clf.predict_proba(X_test)[:, 1]
    auc_score = roc_auc_score(y_test, y_test_prob)

    logger.info("=== Model Performance on Test Split ===")
    logger.info("ROC-AUC Score: %.4f", auc_score)
    report = classification_report(y_test, y_test_pred, digits=4)
    print("\n" + "=" * 60)
    print("RiskIntel upay - Evaluation Classification Report:")
    print("=" * 60)
    print(report)
    print("=" * 60 + "\n")

    # Step 6: Refit on full dataset for maximum production fidelity
    logger.info("Fitting final LightGBM model on full 12,000 dataset...")
    full_model = LGBMClassifier(
        n_estimators=100,
        random_state=42,
        objective="binary",
        learning_rate=0.08,
        num_leaves=31,
        verbose=-1
    )
    full_model.fit(X, y)

    # Step 7: Initialize SHAP TreeExplainer
    logger.info("Initializing SHAP TreeExplainer on trained model...")
    explainer = shap.TreeExplainer(full_model)

    # Step 8: Save Model and SHAP Explainer
    logger.info("Persisting fraud model to: %s", MODEL_FILE_PATH)
    joblib.dump(full_model, MODEL_FILE_PATH)

    logger.info("Persisting SHAP explainer to: %s", EXPLAINER_FILE_PATH)
    joblib.dump(explainer, EXPLAINER_FILE_PATH)

    # Step 9: Verify Artifacts on disk
    assert os.path.exists(MODEL_FILE_PATH), f"Missing model file at {MODEL_FILE_PATH}"
    assert os.path.exists(EXPLAINER_FILE_PATH), f"Missing explainer file at {EXPLAINER_FILE_PATH}"
    assert os.path.exists(DATASET_FILE_PATH), f"Missing dataset file at {DATASET_FILE_PATH}"

    logger.info("Verification passed: all artifacts successfully created on disk!")
    logger.info("  - Model:     %s (%d bytes)", MODEL_FILE_PATH, os.path.getsize(MODEL_FILE_PATH))
    logger.info("  - Explainer: %s (%d bytes)", EXPLAINER_FILE_PATH, os.path.getsize(EXPLAINER_FILE_PATH))
    logger.info("  - Dataset:   %s (%d bytes)", DATASET_FILE_PATH, os.path.getsize(DATASET_FILE_PATH))
    logger.info("=== Training Pipeline Completed Successfully ===")


if __name__ == "__main__":
    run_pipeline()
