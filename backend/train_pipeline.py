"""
RiskIntel upay - Track 01: Trust & Risk Intelligence
File: backend/train_pipeline.py

Comprehensive ML Validation & Training Pipeline for MFS Transaction Risk:
- Generates 12,000 synthetic transactions matching Bangladeshi upay patterns
- Enforces strict 3-way stratified partition: Train (70%), Validation (15%), Test (15%)
- Evaluates on clean, held-out test data never touched during training
- Computes PR-AUC, ROC-AUC, Precision, Recall, F1, and Confusion Matrix
- Conducts granular threshold analysis comparing False Positive Rate (FPR) vs. False Negative Rate (FNR)
- Fits and exports LightGBM classifier and SHAP TreeExplainer artifacts
- Persists machine-readable validation metrics to models/model_metrics.json
"""

import json
import logging
import os
import sys
from typing import Dict, Any, Tuple

import joblib
import numpy as np
import pandas as pd
import shap
from lightgbm import LGBMClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    precision_recall_curve,
    auc,
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score,
)
from sklearn.model_selection import train_test_split

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("RiskIntel-TrainPipeline")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

MODEL_FILE_PATH = os.path.join(MODELS_DIR, "fraud_model.pkl")
EXPLAINER_FILE_PATH = os.path.join(MODELS_DIR, "shap_explainer.pkl")
METRICS_FILE_PATH = os.path.join(MODELS_DIR, "model_metrics.json")
DATASET_FILE_PATH = os.path.join(DATA_DIR, "synthetic_upay_txns.csv")

FEATURE_COLUMNS = [
    "txn_amount",
    "hour_of_day",
    "device_change_count_30d",
    "velocity_last_1h",
    "agent_distance_km",
    "failed_pin_attempts_24h",
    "is_cash_out",
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
      'is_fraud' (binary 0/1) correlates with:
        * High transaction amounts (>15,000 BDT)
        * Midnight velocity spikes (hours 1 to 4)
        * Multiple device changes (>=2)
        * Repeated failed PIN attempts (>=2)
    """
    logger.info("Generating %d synthetic upay transaction records (random_state=%d)...", n_samples, random_state)
    np.random.seed(random_state)

    # 1. Transaction Amount (BDT)
    base_amount = np.random.exponential(scale=3200.0, size=n_samples) + 60.0
    large_transfer_mask = np.random.rand(n_samples) < 0.14
    base_amount[large_transfer_mask] += np.random.uniform(13000.0, 21000.0, size=np.sum(large_transfer_mask))
    txn_amount = np.round(np.clip(base_amount, 50.0, 25000.0), 2)

    # 2. Hour of Day (0-23)
    hour_distribution = np.array([
        0.015, 0.008, 0.005, 0.005, 0.008, 0.015, 0.025, 0.040,  # 00:00 - 07:00
        0.060, 0.070, 0.075, 0.070, 0.065, 0.060, 0.065, 0.070,  # 08:00 - 15:00
        0.075, 0.080, 0.075, 0.060, 0.045, 0.035, 0.025, 0.019   # 16:00 - 23:00
    ])
    hour_distribution = hour_distribution / np.sum(hour_distribution)
    hour_of_day = np.random.choice(np.arange(24), size=n_samples, p=hour_distribution)

    # 3. Device Change Count in Last 30 Days (0, 1, 2, 3, 4)
    device_change_probs = np.array([0.76, 0.17, 0.045, 0.020, 0.005])
    device_change_probs = device_change_probs / np.sum(device_change_probs)
    device_change_count_30d = np.random.choice([0, 1, 2, 3, 4], size=n_samples, p=device_change_probs)

    # 4. Velocity in Last 1 Hour
    velocity_last_1h = np.random.poisson(lam=1.1, size=n_samples)
    velocity_last_1h = np.clip(velocity_last_1h, 0, 15)

    # 5. Agent Distance in Kilometers
    agent_dist = np.random.gamma(shape=2.0, scale=2.5, size=n_samples)
    agent_distance_km = np.round(np.clip(agent_dist, 0.1, 45.0), 2)

    # 6. Failed PIN Attempts in Last 24 Hours
    pin_fail_probs = np.array([0.84, 0.11, 0.035, 0.012, 0.003])
    pin_fail_probs = pin_fail_probs / np.sum(pin_fail_probs)
    failed_pin_attempts_24h = np.random.choice([0, 1, 2, 3, 4], size=n_samples, p=pin_fail_probs)

    # 7. Cash-out Flag (Binary 0 or 1)
    is_cash_out = np.random.choice([0, 1], size=n_samples, p=[0.62, 0.38])

    # Target Correlation & Fraud Signal Synthesis
    midnight_window = (hour_of_day >= 1) & (hour_of_day <= 4)
    midnight_velocity_spike = midnight_window & (velocity_last_1h >= 3)
    high_amount_condition = (txn_amount > 15000.0)
    multiple_device_condition = (device_change_count_30d >= 2)
    repeated_pin_condition = (failed_pin_attempts_24h >= 2)

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
    logger.info("Dataset generated. Total: %d, Fraudulent: %d (%.2f%%)", n_samples, fraud_total, fraud_pct)
    return df


def perform_threshold_sweep(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    thresholds: list = [0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.75, 0.80, 0.90]
) -> list:
    """Evaluates Precision, Recall, F1, FPR, and FNR across multiple decision thresholds."""
    results = []
    total_negatives = int(np.sum(y_true == 0))
    total_positives = int(np.sum(y_true == 1))

    for thresh in thresholds:
        y_pred = (y_prob >= thresh).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

        precision = precision_score(y_true, y_pred, zero_division=0)
        recall = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        fpr = fp / total_negatives if total_negatives > 0 else 0.0
        fnr = fn / total_positives if total_positives > 0 else 0.0

        results.append({
            "threshold": round(thresh, 2),
            "precision": round(float(precision), 4),
            "recall": round(float(recall), 4),
            "f1_score": round(float(f1), 4),
            "false_positive_rate": round(float(fpr), 4),
            "false_negative_rate": round(float(fnr), 4),
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp),
        })
    return results


def run_pipeline() -> Dict[str, Any]:
    """
    Executes end-to-end ML validation and model persistence:
    1. Generates 12,000 synthetic records
    2. Performs stratified 70/15/15 split
    3. Fits LightGBM on train split only
    4. Evaluates on validation and pristine test split
    5. Computes PR-AUC, ROC-AUC, and threshold analysis
    6. Fits SHAP TreeExplainer
    7. Persists artifacts and machine-readable metrics JSON
    """
    logger.info("=== Starting RiskIntel upay ML Validation Pipeline ===")

    # Step 1: Generate dataset
    df = generate_synthetic_upay_data(n_samples=12000, random_state=42)
    df.to_csv(DATASET_FILE_PATH, index=False)
    logger.info("Dataset saved to %s", DATASET_FILE_PATH)

    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    # Step 2: Stratified 70% Train, 15% Validation, 15% Test Split
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, random_state=42, stratify=y
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=42, stratify=y_temp
    )

    logger.info(
        "Partitions created -> Train: %s (Fraud: %d) | Val: %s (Fraud: %d) | Test: %s (Fraud: %d)",
        X_train.shape, int(y_train.sum()),
        X_val.shape, int(y_val.sum()),
        X_test.shape, int(y_test.sum()),
    )

    # Step 3: Train LightGBM Classifier on Train partition only
    logger.info("Training LightGBM Classifier on 70% training split...")
    clf = LGBMClassifier(
        n_estimators=100,
        random_state=42,
        objective="binary",
        learning_rate=0.08,
        num_leaves=31,
        class_weight="balanced",
        verbose=-1,
    )
    clf.fit(X_train, y_train)

    # Step 4: Evaluate on Clean Held-Out Test Set
    y_test_prob = clf.predict_proba(X_test)[:, 1]
    y_test_pred_default = (y_test_prob >= 0.50).astype(int)

    # Compute ROC-AUC and PR-AUC
    roc_auc = float(roc_auc_score(y_test, y_test_prob))
    precisions, recalls, _ = precision_recall_curve(y_test, y_test_prob)
    pr_auc = float(auc(recalls, precisions))

    # Confusion Matrix at default 0.50 threshold
    tn, fp, fn, tp = confusion_matrix(y_test, y_test_pred_default).ravel()
    total_pos = int(y_test.sum())
    total_neg = len(y_test) - total_pos

    fpr_default = float(fp / total_neg)
    fnr_default = float(fn / total_pos)

    # Detailed Threshold Analysis
    threshold_analysis = perform_threshold_sweep(y_test.to_numpy(), y_test_prob)

    report_dict = classification_report(y_test, y_test_pred_default, output_dict=True, digits=4)

    logger.info("=== TEST SET EVALUATION RESULTS ===")
    logger.info("ROC-AUC Score: %.4f | PR-AUC Score: %.4f", roc_auc, pr_auc)
    logger.info("Default Threshold (0.50) -> Precision: %.4f | Recall: %.4f | F1: %.4f",
                report_dict["1"]["precision"], report_dict["1"]["recall"], report_dict["1"]["f1-score"])
    logger.info("Confusion Matrix -> TN: %d, FP: %d, FN: %d, TP: %d", tn, fp, fn, tp)
    logger.info("False Positive Rate (FPR): %.4f | False Negative Rate (FNR): %.4f", fpr_default, fnr_default)

    # Step 5: Fit SHAP TreeExplainer
    logger.info("Fitting SHAP TreeExplainer on trained model...")
    explainer = shap.TreeExplainer(clf)

    # Step 6: Persist Model, Explainer, and Metrics
    logger.info("Saving trained model to: %s", MODEL_FILE_PATH)
    joblib.dump(clf, MODEL_FILE_PATH)

    logger.info("Saving SHAP explainer to: %s", EXPLAINER_FILE_PATH)
    joblib.dump(explainer, EXPLAINER_FILE_PATH)

    metrics_payload = {
        "dataset_metadata": {
            "source": "Synthetic Bangladeshi upay MFS Telemetry Generator",
            "total_records": 12000,
            "features": FEATURE_COLUMNS,
            "class_distribution": {
                "legitimate": int((df["is_fraud"] == 0).sum()),
                "fraudulent": int((df["is_fraud"] == 1).sum()),
                "fraud_rate_percent": round(float((df["is_fraud"].mean()) * 100), 2),
            },
            "partitions": {
                "train_records": len(X_train),
                "val_records": len(X_val),
                "test_records": len(X_test),
            }
        },
        "test_performance": {
            "roc_auc": round(roc_auc, 4),
            "pr_auc": round(pr_auc, 4),
            "default_threshold_0_50": {
                "precision": round(report_dict["1"]["precision"], 4),
                "recall": round(report_dict["1"]["recall"], 4),
                "f1_score": round(report_dict["1"]["f1-score"], 4),
                "false_positive_rate": round(fpr_default, 4),
                "false_negative_rate": round(fnr_default, 4),
                "confusion_matrix": {
                    "true_negatives": int(tn),
                    "false_positives": int(fp),
                    "false_negatives": int(fn),
                    "true_positives": int(tp),
                }
            },
            "governance_thresholds": {
                "step_up_2fa_threshold_0_40": next(t for t in threshold_analysis if t["threshold"] == 0.40),
                "block_or_hold_threshold_0_75": next(t for t in threshold_analysis if t["threshold"] == 0.75),
            },
            "threshold_sweep": threshold_analysis,
        }
    }

    with open(METRICS_FILE_PATH, "w") as f:
        json.dump(metrics_payload, f, indent=2)
    logger.info("Saved validation metrics to: %s", METRICS_FILE_PATH)

    logger.info("=== Pipeline Completed Successfully ===")
    return metrics_payload


if __name__ == "__main__":
    run_pipeline()
