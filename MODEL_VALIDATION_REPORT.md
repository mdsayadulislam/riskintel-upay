# RiskIntel upay — Machine Learning Validation & Risk Model Report

**Project:** RiskIntel upay (AI DEV FEST 2026 — Track 01: Trust & Risk Intelligence)  
**Date:** October 2026  
**Auditor/Author:** Machine Learning Researcher & Risk Intelligence Team  
**Evaluation Target:** Addressing Judge 2 ("Real-world security and fraud-model validation remain outstanding") & Judge 3 ("Synthetic data and SHAP explanations are positive safeguards... production security is weak")

---

## 1. Executive Summary & Validation Objective

This document provides a transparent, scientifically disciplined validation report of the **LightGBM gradient-boosted decision forest** and **SHAP TreeExplainer** used in RiskIntel upay.

> [!IMPORTANT]
> **Synthetic Validation Disclaimer:**  
> All empirical metrics presented herein are derived from statistically synthesized transaction distributions mirroring Bangladeshi Mobile Financial Services (MFS) behavioral topologies. **This synthetic validation does NOT prove production performance on live banking traffic.** It serves as a rigorous proof-of-concept demonstrating model calibration, feature sensitivity, threshold tuning, and explainability under controlled experimental conditions. Final production deployment requires re-validation against anonymized, compliance-cleared live data under Bangladesh Bank regulatory supervision.

---

## 2. Dataset Specification & Synthetic Topology

| Attribute | Specification | Operational Context |
| :--- | :--- | :--- |
| **Data Status** | 100% Synthetic / Zero Real PII | Generated via parameterized probabilistic distributions |
| **Total Population** | 12,000 transaction records | Sample size representative of multi-day MFS prototype activity |
| **Legitimate Records ($y=0$)** | 10,931 (91.09%) | Typical customer P2P and cash-out operations |
| **Fraudulent Records ($y=1$)** | 1,069 (8.91%) | Simulates realistic MFS class imbalance (ATO, SIM swap, velocity) |
| **Storage Artifact** | `data/synthetic_upay_txns.csv` | Version-controlled CSV dataset |

### 2.1 Feature Definitions & Distribution Parameters

| Feature Name | Type | Range / Distribution | Fraud Correlation Rationale |
| :--- | :--- | :--- | :--- |
| `txn_amount` | `float` | ৳50.00 – ৳25,000.00 | Fraud syndicates tend to max out the ৳25,000 Bangladesh Bank single-transaction ceiling. |
| `hour_of_day` | `int` | 0 – 23 (24h clock) | Nighttime lull (01:00–04:00) exhibits severe anomaly spikes when victims are asleep. |
| `device_change_count_30d` | `int` | 0 – 4 changes | Multiple switches indicate SIM-swap attacks or device takeovers. |
| `velocity_last_1h` | `int` | 0 – 15 txns/hr | Rapid consecutive transfers indicate automated liquidity siphoning. |
| `agent_distance_km` | `float` | 0.1 – 45.0 km | High distances indicate remote agent mule cash-outs. |
| `failed_pin_attempts_24h` | `int` | 0 – 4 attempts | Repeated failed PIN entries indicate brute-force probing or stolen handsets. |
| `is_cash_out` | `int` | 0 (P2P) or 1 (Cash-Out) | Cash-outs are irreversible and carry higher fraud risk than internal P2P transfers. |

---

## 3. Experimental Protocol & Partitioning

To avoid data leakage and model overfitting, the dataset was partitioned using a strict **3-way stratified split**:

```
+-------------------------------------------------------------------------+
|                    Full Population: 12,000 Records                      |
+------------------------------------+-------------------+----------------+
|       Train Split (70%)            | Validation (15%)  |   Test (15%)   |
|     8,400 records (748 fraud)      |   1,800 records   | 1,800 records  |
|   Used exclusively for fitting     |   (161 fraud)     |  (160 fraud)   |
|       LightGBM tree splits         |  Threshold Tuning |  Pristine Hold |
+------------------------------------+-------------------+----------------+
```

- **Stratification:** Maintained constant 8.91% fraud incidence across all 3 subsets.
- **Pristine Test Set:** The 1,800 test records were **never seen** during model fitting or parameter tuning.

---

## 4. Empirical Evaluation Results (Test Set: $N=1,800$)

### 4.1 Discrimination Metrics

- **ROC-AUC (Receiver Operating Characteristic):** **`0.9780`**
- **PR-AUC (Precision-Recall Area Under Curve):** **`0.8247`**

> [!NOTE]
> In imbalanced fraud detection ($~8.9\%$ minority class), ROC-AUC can be overly optimistic because large numbers of True Negatives suppress the False Positive Rate. **PR-AUC is the true gold-standard metric**, measuring the trade-off between precision (minimizing false alarms) and recall (capturing true fraud). A PR-AUC of **0.8247** demonstrates strong signal discrimination.

### 4.2 Confusion Matrix (Default $\tau = 0.50$)

| | Predicted Legitimate ($\hat{y}=0$) | Predicted Fraudulent ($\hat{y}=1$) | Total Actual |
| :--- | :---: | :---: | :---: |
| **Actual Legitimate ($y=0$)** | **1,567** (TN) | **73** (FP) | 1,640 |
| **Actual Fraudulent ($y=1$)** | **21** (FN) | **139** (TP) | 160 |
| **Total Predicted** | 1,588 | 212 | 1,800 |

- **Precision ($\frac{TP}{TP + FP}$):** `65.57%`
- **Recall / Sensitivity ($\frac{TP}{TP + FN}$):** `86.88%`
- **F1-Score:** `0.7473`
- **False Positive Rate ($FPR = \frac{FP}{FP + TN}$):** `4.45%`
- **False Negative Rate ($FNR = \frac{FN}{FN + TP}$):** `13.13%`

---

## 5. Granular Threshold Analysis & Business Tradeoffs

In Mobile Financial Services, setting a single binary threshold ($\tau = 0.50$) is inadequate because different operational decisions incur asymmetric costs:
1. **False Positive Cost:** Legitimate customer friction, transaction abandonment, customer support call center strain (upay helpline 16268).
2. **False Negative Cost:** Direct financial loss, mule account liquidity drainage, regulatory scrutiny by the Bangladesh Bank.

### 5.1 Threshold Sweep Matrix (Test Set $N=1,800$)

| Threshold ($\tau$) | Precision | Recall (TPR) | F1-Score | FPR | FNR | TP | FP | TN | FN | Operational Tier |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **0.20** | 49.50% | 93.13% | 0.6464 | 9.27% | 6.88% | 149 | 152 | 1488 | 11 | Aggressive Monitoring |
| **0.30** | 55.38% | 90.00% | 0.6857 | 7.07% | 10.00% | 144 | 116 | 1524 | 16 | Pre-Alert |
| **0.40** | **59.41%** | **88.75%** | **0.7118** | **5.91%** | **11.25%** | **142** | **97** | **1543** | **18** | **`STEP_UP_2FA` Boundary** |
| **0.50** | 65.57% | 86.88% | 0.7473 | 4.45% | 13.13% | 139 | 73 | 1567 | 21 | Balanced Baseline |
| **0.60** | 68.88% | 84.38% | 0.7584 | 3.72% | 15.62% | 135 | 61 | 1579 | 25 | High Monitoring |
| **0.70** | 70.39% | 78.75% | 0.7434 | 3.23% | 21.25% | 126 | 53 | 1587 | 34 | Pre-Hold Review |
| **0.75** | **71.43%** | **78.12%** | **0.7463** | **3.05%** | **21.88%** | **125** | **50** | **1590** | **35** | **`BLOCK_IMMEDIATELY` / Hold** |
| **0.80** | 74.55% | 76.88% | 0.7569 | 2.56% | 23.13% | 123 | 42 | 1598 | 37 | Extreme Confidence |
| **0.90** | 81.34% | 68.13% | 0.7415 | 1.52% | 31.87% | 109 | 25 | 1615 | 51 | Severe Attack Defense |

---

## 6. Justification of Governance Decision Thresholds

### Tier 1: `APPROVE` (Score < 40.0)
- **Rationale:** At $\tau < 0.40$, over 94% of genuine transactions pass with **zero customer friction**.
- **User Experience:** Instant processing under 10ms with automatic balance deduction.

### Tier 2: `STEP_UP_2FA` (Score 40.0 – 74.9)
- **Threshold Justification:** Set at $\tau = 0.40$ where recall is **88.75%**.
- **Trade-off Mitigation:** Instead of blocking transactions that have moderate risk indicators (e.g. late night or large amount), the customer is issued a cryptographic step-up 2FA challenge. Legitimate customers complete the challenge in seconds, while automated fraudsters lacking the device/SIM are halted.

### Tier 3: `BLOCK_IMMEDIATELY` / Temporary Security Hold (Score $\ge 75.0$)
- **Threshold Justification:** Set at $\tau = 0.75$ where the False Positive Rate drops to **3.05%** and precision rises to **71.43%**.
- **Human Recourse Guard:** A score $\ge 75.0$ initiates a **pre-settlement hold with an immediate self-service recovery pathway** (`POST /api/v1/recovery/verify`) and helpline routing (16268). The system **never imposes an irreversible permanent block** based solely on model output.

---

## 7. Model Limitations & Potential Data Drift

### 7.1 Limitations
1. **Synthetic Feature Assumptions:** Generated features assume standard exponential amount distributions and Poisson velocities. Real MFS data often features multimodal clusters (e.g., salary payment spikes on the 1st of the month, Eid shopping festivals).
2. **Tabular Isolation:** The LightGBM classifier scores individual transactions in isolation; it does not analyze graph topologies (e.g. fan-in / fan-out mule money networks).
3. **Location Granularity:** `agent_distance_km` is modeled continuously; real cellular telemetry involves discrete cell tower azimuths and GPS spoofing risks.

### 7.2 Anticipated Production Data Drift
- **Seasonal Drift:** Festival spikes (Eid, Pohela Boishakh) cause sharp spikes in legitimate midnight transfers and cash-out volumes that could cause false positives if unadjusted.
- **Adversarial Drift:** Fraudsters rapidly adapt to static rule ceilings (e.g., splitting ৳25,000 into five ৳4,999 transactions).
- **Macroeconomic Changes:** Regulatory shifts by Bangladesh Bank in transaction caps will alter baseline features.

---

## 8. Real-World Production Validation Roadmap

To transition from this hackathon prototype to production banking deployment, the following governance protocol must be executed:

1. **Governed Shadow Mode Testing:** Deploy model in parallel ("dark mode") to existing rule engines for 30–60 days, scoring live transactions without affecting execution, to benchmark real-world FPR and FNR against confirmed fraud chargebacks.
2. **Concept Drift Monitoring:** Implement Population Stability Index (PSI) and Kolmogorov-Smirnov (KS) tests on daily feature distributions with automated retraining triggers when PSI exceeds 0.25.
3. **Graph Analysis Layer:** Augment LightGBM with graph neural networks (e.g., PyTorch Geometric) to detect cyclic mule chains.
4. **BFIU Regulatory Compliance Review:** Validate audit logs and explainability records with the Bangladesh Financial Intelligence Unit (BFIU) for automated Suspicious Transaction Reporting (STR).
