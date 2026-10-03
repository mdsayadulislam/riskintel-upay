# Project Report: RiskIntel upay — Trust & Risk Intelligence Engine

> **Document Type:** Master Project Reference & Technical Report  
> **Target Audience:** Hackathon Evaluators, Technical Reviewers, Solution Architects & Academic Committees  
> **Event:** AI DEV FEST 2026 — Track 01: Trust & Risk Intelligence  
> **Organization:** Developed for upay (UCB Fintech Ltd., Bangladesh)  
> **Team:** Loading_211  
> **Generated:** October 2026  
> **Version:** 1.0.0 (Production Release)

---

## Table of Contents
1. [Executive Summary & Metadata](#1-executive-summary--metadata)
2. [Problem Statement & Financial Domain Context](#2-problem-statement--financial-domain-context)
3. [System Architecture & Data Flow](#3-system-architecture--data-flow)
4. [Machine Learning Pipeline & Synthetic Data Modeling](#4-machine-learning-pipeline--synthetic-data-modeling)
5. [Explainable AI (XAI) & Local Attribution Engine](#5-explainable-ai-xai--local-attribution-engine)
6. [Regulatory Compliance & Bangladesh Bank MFS Framework](#6-regulatory-compliance--bangladesh-bank-mfs-framework)
7. [Frontend UI/UX: Authentic upay Handset & Evaluator Console](#7-frontend-uiux-authentic-upay-handset--evaluator-console)
8. [Interactive Decision Modals & Self-Service Unblock Flow](#8-interactive-decision-modals--self-service-unblock-flow)
9. [API Gateway & Data Schema Specifications](#9-api-gateway--data-schema-specifications)
10. [Evaluator Test Matrix & Benchmark Scenarios](#10-evaluator-test-matrix--benchmark-scenarios)
11. [Installation, Run & Deployment Guide](#11-installation-run--deployment-guide)
12. [Security, Privacy & Responsible AI Governance](#12-security-privacy--responsible-ai-governance)
13. [Future Roadmap & Production Scaling](#13-future-roadmap--production-scaling)

---

## 1. Executive Summary & Metadata

### 1.1 Project Overview
**RiskIntel upay** is an ultra-low-latency (<20ms), explainable fraud prevention engine and interactive consumer transaction simulator designed specifically for the **upay** Mobile Financial Services (MFS) ecosystem (UCB Fintech Ltd., a subsidiary of United Commercial Bank PLC).

The platform bridges cutting-edge machine learning (**LightGBM decision forests**) with game-theoretic local explainability (**SHAP TreeExplainer**) and a policy-driven decision gateway. Evaluators and risk analysts can test real-time mobile transactions inside a high-fidelity upay mobile app mockup while observing sub-millisecond AI inference, dynamic risk scoring, feature impact bars, and regulatory policy execution.

### 1.2 Team Information
- **Team Name:** `Loading_211`
- **Track:** Track 01: Trust & Risk Intelligence
- **Event:** AI DEV FEST 2026
- **Members:**
  1. **Md. Suaib Islam** ([@si4795](https://github.com/si4795)) — Lead Full-Stack Architect & AI Engineer
  2. **Md. Sayadul Islam** — Machine Learning Researcher & Data Modeler
  3. **Md. Elias Ahmed** — Frontend UX Engineer & QA Specialist

### 1.3 Deployment Links & Artifacts
- **GitHub Repository:** [https://github.com/si4795/riskintel-upay](https://github.com/si4795/riskintel-upay)
- **Interactive Web Simulator (Vercel):** [https://riskintel-upay.vercel.app](https://riskintel-upay.vercel.app)
- **FastAPI Backend & Swagger Docs (Render):** [https://riskintel-upay.onrender.com/docs](https://riskintel-upay.onrender.com/docs)
- **License:** MIT Open Source License

---

## 2. Problem Statement & Financial Domain Context

### 2.1 The Bangladeshi MFS Landscape
Mobile Financial Services in Bangladesh represent the financial lifeblood of over 120 million registered citizens, executing more than **150 million transactions daily**. The speed of digital transfers and instant cash-out mechanisms make MFS platforms prime targets for sophisticated fraud syndicates.

### 2.2 Primary Fraud Attack Vectors
1. **Account Takeover (ATO) & SIM Swap Attacks:** Attackers unlawfully re-issue a victim's SIM card, install the MFS application on a fresh device, and attempt rapid fund draining.
2. **Brute-Force PIN Probing:** Automated bots or malicious actors repeatedly test 4-digit PIN permutations within short 24-hour windows.
3. **Midnight Mule Cash-Outs:** Fraudulent operators transfer stolen balances during early morning hours (01:00 AM – 04:00 AM) to remote cash-out points to bypass human oversight.
4. **Velocity Bursts:** Splitting large illicit sums into consecutive bursts of smaller transfers within a 60-minute window to evade static daily threshold alerts.

### 2.3 The Core Technical Bottleneck
Traditional rules-based fraud engines rely on static `IF-ELSE` condition matrices. They suffer from:
- **High False Positive Rates (FPR):** Legitimate users making emergency late-night medical payments or festival shopping transfers get wrongfully blocked.
- **High Latency:** Complex SQL joins across relational tables introduce 300–800ms delays, degrading mobile app responsiveness.
- **Zero Transparency (Black-Box Problem):** Deep neural networks or rigid rules cannot provide real-time regulatory explanations required by the Bangladesh Bank Guidelines on MFS.

**RiskIntel upay** resolves this bottleneck by combining sub-10ms gradient boosted inference with on-the-fly local SHAP attribution.

---

## 3. System Architecture & Data Flow

### 3.1 Architectural Diagram
```
+-----------------------------------------------------------------------------------+
|                        RiskIntel upay - Fullstack Topology                        |
+-----------------------------------------------------------------------------------+
                                          |
                 [ Consumer Client / Evaluator Dashboard ]
                 Next.js 14 App Router | React 18 | TypeScript | Tailwind CSS
                 Authentic upay Handset + Evaluator Sandbox + Telemetry Sliders
                                          |
                                          | HTTP POST (JSON Payload)
                                          | sub-20ms roundtrip
                                          v
+-----------------------------------------------------------------------------------+
|                   FastAPI High-Performance Gateway (:8000)                        |
|                                                                                   |
|  - Input Validation via Pydantic v2 Schemas (TransactionPayload)                 |
|  - CORS Cross-Origin Middleware (allow_origins=["*"])                             |
|  - In-Memory Artifact Singletons (fraud_model.pkl, shap_explainer.pkl)            |
|  - Sub-millisecond Execution Profiler (perf_counter)                              |
+-----------------------------------------------------------------------------------+
                                          |
                   +----------------------+----------------------+
                   |                                             |
                   v                                             v
+------------------------------------+       +------------------------------------+
|     LightGBM Classifier Engine     |       |     SHAP TreeExplainer Engine      |
|  - 100 Gradient-Boosted Trees      |       |  - Game-Theoretic Feature Values   |
|  - Fast Leaf-Wise Tree Splitting   |       |  - Local Attribution Vectors       |
|  - Output: Calibrated Probability  |       |  - Output: Top 3 Critical Drivers  |
+------------------------------------+       +------------------------------------+
                   \                                             /
                    \                                           /
                     +--------------------+--------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                     Automated Policy & Governance Engine                          |
|                                                                                   |
|  - Risk Score >= 75.0  --> BLOCK_IMMEDIATELY (Pre-settlement halt + Self-Recovery)|
|  - Risk Score >= 40.0  --> STEP_UP_2FA       (Secondary OTP / Biometric Challenge)|
|  - Risk Score <  40.0  --> APPROVE           (Instant Settlement & Balance Decr)  |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                        Client Response & UI Presentation                          |
|  - Clamped Circular SVG Risk Gauge (0 - 100)                                      |
|  - Bengali Compliance Narrative Briefing                                          |
|  - Color-Coded Directional SHAP Feature Impact Bars                               |
|  - Client State Synchronization (LocalStorage Hydration)                          |
+-----------------------------------------------------------------------------------+
```

### 3.2 End-to-End Data Lifecycle
1. **User Action:** The evaluator configures transaction details (Amount, Channel, PIN) and telemetry parameters (Hour, Velocity, Device Changes, Failed PINs, Agent Distance) via quick presets or sliders.
2. **Payload Dispatch:** The frontend sends an HTTP `POST` request to `/api/v1/assess-risk` containing the 7 core feature parameters.
3. **Pydantic Validation:** FastAPI validates data boundaries (e.g. `hour_of_day` $\in [0, 23]$, amounts $\ge 0$).
4. **Vector Inference:** In-memory LightGBM predicts fraud probability ($P(\text{fraud})$) in $<5\text{ms}$.
5. **SHAP Decomposition:** `TreeExplainer` decomposes the log-odds prediction into local Shapley values for all 7 features in $<8\text{ms}$.
6. **Policy Evaluation:** The score ($P(\text{fraud}) \times 100$) is mapped to `APPROVE`, `STEP_UP_2FA`, or `BLOCK_IMMEDIATELY`.
7. **Client Feedback:** Next.js renders the animated gauge, displays SHAP bars, updates the balance, and triggers the corresponding in-app modal.

---

## 4. Machine Learning Pipeline & Synthetic Data Modeling

### 4.1 Feature Dictionary
The model processes 7 real-time telemetry inputs reflecting behavioral, temporal, spatial, and device-level risk indicators:

| Feature Name | Type | Unit / Range | Real-World MFS Significance |
| :--- | :--- | :--- | :--- |
| `txn_amount` | `float` | ৳10.00 – ৳28,000.00 | Higher amounts correlate strongly with liquidity draining during account takeovers. |
| `hour_of_day` | `int` | 0 – 23 (24h clock) | Nighttime transactions (01:00 – 04:00) represent significant anomaly spikes. |
| `device_change_count_30d` | `int` | 0 – 4 | Frequent device switching indicates SIM swapping or stolen credentials. |
| `velocity_last_1h` | `int` | 0 – 15 | High transfer frequency within 60 minutes indicates rapid mule account dispersion. |
| `agent_distance_km` | `float` | 0.1 – 45.0 km | Distance from user's typical geo-centroid to the current agent counter. |
| `failed_pin_attempts_24h` | `int` | 0 – 4 | Repeated incorrect PIN entries indicate credential stuffing or guessing. |
| `is_cash_out` | `int` | Binary (0: P2P, 1: Cash-Out) | Cash-out carries irreversible physical cash extraction risk compared to traceable P2P transfers. |

### 4.2 Synthetic Dataset Generation (`data/synthetic_upay_txns.csv`)
Because banking privacy regulations strictly forbid the publication of real customer PII and transaction records, the training pipeline (`backend/train_pipeline.py`) synthesizes **12,000 realistic transactions** using calibrated statistical distributions:
- **Transaction Amount:** Exponential distribution ($\lambda = 3200$) with a heavy-tail spike ($14\%$ chance of high-value transfer between ৳13,000 and ৳21,000), clipped to ৳28,000.
- **Hour of Day:** Realistic diurnal distribution with $82\%$ volume between 08:00 and 22:00, and a sharp drop during 01:00–04:00.
- **Device Changes:** Discrete probability vector: $76\%$ (0 changes), $17\%$ (1 change), $4.5\%$ (2 changes), $2\%$ (3 changes), $0.5\%$ (4 changes).
- **Velocity:** Poisson distribution with $\lambda = 1.1$.
- **PIN Failures:** Geometric decay: $84\%$ (0), $11\%$ (1), $3.5\%$ (2), $1.2\%$ (3), $0.3\%$ (4).
- **Fraud Synthesis Logic:** Calibrated multivariate latent log-odds function modeling synergistic attack patterns (e.g. midnight spike + velocity burst + multiple device switches).

### 4.3 Model Selection & Training Hyperparameters
We selected **LightGBM (Light Gradient Boosting Machine)** for its superior execution speed, low memory footprint, and native leaf-wise tree growth:
```python
clf = LGBMClassifier(
    n_estimators=100,
    learning_rate=0.08,
    num_leaves=31,
    objective="binary",
    random_state=42,
    verbose=-1
)
```

### 4.4 Model Performance Metrics
Evaluated on an 80/20 stratified train-test split:
- **ROC-AUC Score:** `> 0.985` (exceptional class separation between legitimate and anomalous transfers).
- **Inference Latency:** `< 8.0 ms` on standard CPU hardware.
- **Model Artifact Size:** `~320 KB` (highly portable for edge and containerized deployments).

---

## 5. Explainable AI (XAI) & Local Attribution Engine

### 5.1 Game-Theoretic Shapley Formulations
In regulated banking, black-box decisions violate consumer protection standards. RiskIntel upay uses **SHAP (SHapley Additive exPlanations)** based on cooperative game theory:

$$\phi_i(x) = \sum_{S \subseteq F \setminus \{i\}} \frac{|S|!(|F| - |S| - 1)!}{|F|!} \left[ f_x(S \cup \{i\}) - f_x(S) \right]$$

Where:
- $F$ is the complete set of all 7 transaction features.
- $S$ is a subset of features excluding feature $i$.
- $\phi_i(x)$ is the exact marginal attribution contribution of feature $i$ to the final prediction.

### 5.2 Directional Impact & Audit Trail
Every API response returns the top 3 driving features ranked by absolute magnitude $|\phi_i|$:
- **Positive SHAP Impact ($\phi_i > 0$):** Indicates an anomalous factor driving the score *upward* toward fraud (e.g. repeated PIN failures, unusual amount). Rendered as an alert red bar.
- **Negative SHAP Impact ($\phi_i < 0$):** Indicates a stabilizing baseline factor driving the score *downward* toward legitimate status (e.g. zero device changes, normal daytime hour). Rendered as a reassuring emerald bar.

### 5.3 Automated Localized Compliance Narrative
The API automatically synthesizes the mathematical drivers into clear Bengali and English audit narratives:
- **Approved Example:** *"Transaction conforms to expected baseline behavior. Low anomaly probability across biometric and velocity signals."*
- **Blocked Example:** *"Critical risk detected. Severe deviation driven by txn_amount, failed_pin_attempts_24h, device_change_count_30d. Transaction halted immediately; step-up verification or manual triage required."*

---

## 6. Regulatory Compliance & Bangladesh Bank MFS Framework

The application strictly implements the regulatory transaction limits defined by the **Bangladesh Bank Guidelines for Mobile Financial Services**:

| Policy Parameter | P2P Send Money (ব্যক্তিগত লেনদেন) | Agent Cash-Out (এজেন্ট ক্যাশ-আউট) | System Enforcement Point |
| :--- | :--- | :--- | :--- |
| **Minimum Transaction Amount** | **৳১০.০০** | **৳৫০.০০** | Real-time input boundary validation |
| **Maximum Single Transaction** | **৳২৫,০০০.০০** | **৳২৫,০০০.০০** | Form constraint & Bengali alert |
| **Daily Transaction Limit** | **৳২৫,০০০.০০** (সর্বোচ্চ ৫ বার) | **৳২৫,০০০.০০** (সর্বোচ্চ ৫ বার) | Aggregate ledger cap validation |
| **Monthly Transaction Limit** | **৳২,০০,০০০.০০** (সর্বোচ্চ ৫০ বার) | **৳১,৫০,০০০.০০** (সর্বোচ্চ ২০ বার) | Monthly quota tracking |
| **Base Evaluator Balance** | **৳৩৫,০০০.০০** | **৳৩৫,০০০.০০** | Dynamic demo balance |
| **Balance Top-Up Mechanism** | **↻ +৳২০,০০০.০০** | **↻ +৳২০,০০০.০০** | 1-click sandbox fund replenishment |

### 6.1 Real-Time Input Validation Logic
- **Exceeding Single Limit ($> ৳25,000$):** `"দৈনিক লেনদেন সীমা অতিক্রম করেছে (সর্বোচ্চ ৳২৫,০০০)"`
- **Insufficient Account Balance ($> \text{Balance}$):** `"অপর্যাপ্ত অ্যাকাউন্ট ব্যালেন্স! আপনার বর্তমান ব্যালেন্স ৳১২,৫৪০.০০"`
- **Below Minimum Boundary ($< ৳10$ or $< ৳50$):** `"সর্বনিম্ন লেনদেনের পরিমাণ ৳১০ / ৳৫০"`

---

## 7. Frontend UI/UX: Authentic upay Handset & Evaluator Console

The user interface is split into a **dual-console layout** engineered with Next.js 14 and Tailwind CSS:

### 7.1 Authentic upay Mobile Handset (Left Screen)
Designed to match the real-world upay consumer Android/iOS experience:
- **Header:** Signature upay Radiant Yellow (`#FFC800`), verified user identity ("Homanur Bagum"), balance pill with toggle eye icon (`৳৩৫,০০০.০০`), and 1-click top-up button (`↻ +৳২০,০০০`).
- **Channel Switcher:** Symmetrical segmented control toggling between **"সেন্ড মানি (P2P)"** and **"ক্যাশ আউট (Agent)"** with smooth transition styles.
- **Recipient Card:** Displays verified recipient avatar, phone number (`01812-345678`) or agent point code (`#88219`), with green "সক্রিয়" badge.
- **Amount Input & Quick Chips:** Large monetary input with currency symbol (৳), plus quick addition chips (`+৳500`, `+৳2,000`, `+৳10,000`, `+৳25,000`) and a reset button (`↺`).
- **4-Digit MFS PIN Field:** Authentic masked PIN input (`type="password"`, `maxLength={4}`, `tracking-widest`, centered text), restricted strictly to numeric digits, with helper warning if $< 4$ digits are present.
- **Action Button:** Responsive submission button displaying dynamic labels (`"টাকা পাঠান / নিশ্চিত করুন"` or `"ক্যাশ আউট নিশ্চিত করুন"`).
- **Navigation Bar:** Genuine bottom tab bar featuring Home, Activity, Notifications, Profile, and a central floating yellow **"বাংলা QR"** button.

### 7.2 Evaluator Sandbox Toolbar (Top Bar)
Provides 1-click evaluation presets that simultaneously configure phone inputs, update telemetry sliders, and trigger instant AI risk evaluation:
1. **Normal P2P (৳500):** Baseline legitimate daytime transaction.
2. **ATO Attack (৳25,000):** Midnight high-velocity SIM swap cash-out attack.
3. **Midnight Cashout (৳18,000):** Odd-hour large-sum withdrawal anomaly.

### 7.3 Risk Intelligence Console & Telemetry Drawer (Right Screen)
- **Circular SVG Risk Gauge:** Smoothly animated SVG arc measuring calibrated risk from $0.0$ to $100.0$ with color-coded operational zones (Green: Low, Amber: Medium, Red: Critical).
- **Policy Decision Badge:** Prominent display of `APPROVE`, `STEP_UP_2FA`, or `BLOCK_IMMEDIATELY`.
- **SHAP Feature Impact Breakdown:** Visual bar charts detailing the top 3 drivers with numerical attribution scores.
- **Interactive Telemetry Sliders:** Real-time range sliders allowing manual tweaking of Hour of Day, Hourly Velocity, Device Changes, Failed PINs, and Agent Distance.
- **Service Telemetry Indicator:** Displays FastAPI connection status (Live vs Local Simulation Fallback) and real-time inference roundtrip latency in milliseconds.

---

## 8. Interactive Decision Modals & Self-Service Unblock Flow

When a transaction is submitted or a preset is evaluated, the handset dynamically launches an authentic in-app modal tailored to the AI decision:

### 8.1 Scenario A: Low Risk (`APPROVE`)
- **Visual:** Emerald success checkmark with celebratory animation.
- **Details:** Confirms transaction completion, transaction ID (`TXN-98214-UPAY`), channel, and recipient.
- **Financial Effect:** Immediately deducts the transaction amount from the active balance and persists the updated balance to `localStorage`.

### 8.2 Scenario B: Moderate Risk (`STEP_UP_2FA`)
- **Visual:** Amber shield challenge modal.
- **Behavior:** Prevents immediate fund transfer. Prompts the customer for a 6-digit one-time passcode (mock OTP: `123456`).
- **Resolution:** Upon entering the valid OTP, the challenge resolves to approval, deducts the funds, and completes the transfer without customer lockout.

### 8.3 Scenario C: Critical Risk (`BLOCK_IMMEDIATELY`) & Self-Service Unblock
- **Visual:** Urgent red security alert notifying the user of detected cyber anomalies.
- **The Self-Service Innovation:** Rather than presenting an operational dead-end ("Contact Helpline"), the modal empowers legitimate victims to recover their account instantly:
  1. User taps **"ওটিপি ও বায়োমেট্রিক দিয়ে তাৎক্ষণিক আনলক করুন"** (Instant Self-Service Unlock).
  2. The system sends a simulated secure challenge.
  3. User enters the 6-digit identity recovery token (`123456`).
  4. The engine resets the `failed_pin_attempts_24h` counter, clears the security freeze, deducts the approved transaction, and restores full account access immediately.

---

## 9. API Gateway & Data Schema Specifications

### 9.1 Root Metadata Endpoint
- **URL:** `GET /`
- **Response:**
```json
{
  "service": "RiskIntel upay",
  "track": "Track 01: Trust & Risk Intelligence",
  "organization": "UCB Fintech Ltd.",
  "health": "/health",
  "docs": "/docs",
  "endpoint": "/api/v1/assess-risk"
}
```

### 9.2 Health Probe Endpoint
- **URL:** `GET /health`
- **Response:**
```json
{
  "status": "healthy",
  "service": "RiskIntel upay Engine",
  "artifacts_loaded": "True"
}
```

### 9.3 Risk Assessment Endpoint
- **URL:** `POST /api/v1/assess-risk`
- **Request Headers:** `Content-Type: application/json`
- **Request Body (Pydantic Schema):**
```json
{
  "txn_amount": 25000.0,
  "hour_of_day": 3,
  "device_change_count_30d": 2,
  "velocity_last_1h": 6,
  "agent_distance_km": 18.5,
  "failed_pin_attempts_24h": 3,
  "is_cash_out": 1
}
```
- **Response Body (200 OK):**
```json
{
  "risk_score": 99.8,
  "risk_level": "HIGH",
  "recommended_action": "BLOCK_IMMEDIATELY",
  "key_risk_drivers": [
    {
      "feature": "txn_amount",
      "impact": 3.0721
    },
    {
      "feature": "failed_pin_attempts_24h",
      "impact": 2.7614
    },
    {
      "feature": "device_change_count_30d",
      "impact": 2.1548
    }
  ],
  "narrative": "Critical risk detected. Severe deviation driven by txn_amount, failed_pin_attempts_24h, device_change_count_30d. Transaction halted immediately; step-up verification or manual triage required.",
  "inference_time_ms": 7.16
}
```

---

## 10. Evaluator Test Matrix & Benchmark Scenarios

| Scenario Preset | Input Parameters | Simulated Telemetry Context | Expected Risk Score | AI Policy Action | Primary SHAP Drivers | Expected UX Feedback |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Normal P2P** | Amount: ৳500<br>Channel: P2P (0)<br>PIN: `1234` | Hour: 14:00<br>Velocity: 1<br>Devices: 0<br>PIN Fails: 0<br>Dist: 1.2 km | **0.05 / 100**<br>(Low Risk) | **`APPROVE`** | `txn_amount` (-0.61)<br>`is_cash_out` (-0.40)<br>`device_change_count_30d` (-0.34) | Green Success Modal with instant balance deduction to ৳34,500.00. |
| **2. ATO Attack** | Amount: ৳25,000<br>Channel: Cash-Out (1)<br>PIN: `1234` | Hour: 03:00<br>Velocity: 6<br>Devices: 2<br>PIN Fails: 3<br>Dist: 18.5 km | **99.80 / 100**<br>(Critical) | **`BLOCK_IMMEDIATELY`** | `txn_amount` (+3.07)<br>`failed_pin_attempts_24h` (+2.76)<br>`device_change_count_30d` (+2.15) | Red Halt Modal with 1-click self-service OTP/Biometric recovery recourse. |
| **3. Midnight Cashout** | Amount: ৳18,000<br>Channel: Cash-Out (1)<br>PIN: `1234` | Hour: 02:00<br>Velocity: 4<br>Devices: 1<br>PIN Fails: 1<br>Dist: 8.0 km | **99.12 / 100**<br>(Critical) | **`BLOCK_IMMEDIATELY`** | `txn_amount` (+3.08)<br>`failed_pin_attempts_24h` (+2.74)<br>`hour_of_day` (+2.45) | Red Alert Modal requiring identity verification before fund release. |

---

## 11. Installation, Run & Deployment Guide

### 11.1 Prerequisites
- **Python:** Version 3.10 or higher.
- **Node.js:** Version 18.x or higher with `npm`.
- **Git:** Installed and configured.

### 11.2 Local Setup
```bash
# 1. Clone the repository
git clone https://github.com/si4795/riskintel-upay.git
cd riskintel-upay

# 2. Setup Python environment and install dependencies
python -m venv venv
.\venv\Scripts\Activate.ps1    # On Windows PowerShell
# source venv/bin/activate     # On Linux / macOS

pip install --upgrade pip
pip install fastapi uvicorn lightgbm shap scikit-learn pandas numpy joblib pydantic

# 3. Train the model and generate serial artifacts
python backend/train_pipeline.py

# 4. Launch FastAPI backend gateway
python backend/main.py
# Running on http://127.0.0.1:8000 (Docs at /docs)
```

In a separate terminal window:
```bash
# 5. Launch Next.js frontend simulator
cd frontend
npm install
npm run dev
# Accessible at http://localhost:3000
```

### 11.3 Production Deployment
- **Frontend (Vercel):** Connect the GitHub repository, select `frontend` as Root Directory, and configure:
  ```env
  NEXT_PUBLIC_API_URL=https://riskintel-upay.onrender.com
  ```
- **Backend (Render / Railway / AWS):** Build command: `pip install -r requirements.txt && python backend/train_pipeline.py`, Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`.

---

## 12. Security, Privacy & Responsible AI Governance

1. **Zero Real PII Transmission:** The system never accepts, transmits, or stores National ID numbers, bank card numbers, or real user PINs. All features are behavioral aggregations and statistical representations.
2. **CORS Security:** Backend configured with Starlette CORSMiddleware to permit secure cross-domain API invocation from Vercel deployments.
3. **No Black-Box Automated Lockout:** Critical block decisions provide an immediate customer unblock pathway via step-up 2FA, preventing denial of legitimate funds.
4. **State Persistence without Cookie Leaks:** Handset state is isolated strictly to browser `localStorage` under domain sandboxing.

---

## 13. Future Roadmap & Production Scaling

- [ ] **Graph Neural Network (GNN) Layer:** Incorporating PyTorch Geometric to map dynamic transaction graphs and expose organized mule distribution rings.
- [ ] **Cell-Tower & IP Velocity Correlation:** Analyzing cellular base station switching speeds to detect automated SIM-farm operations.
- [ ] **Automated STR/CTR Generation:** Auto-drafting Suspicious Transaction Reports (STR) in Bangladesh Financial Intelligence Unit (BFIU) standardized XML format.
- [ ] **Offline Edge Scoring:** Compiling LightGBM models into ONNX/WebAssembly format to perform zero-network pre-flight inference directly inside the mobile client.

---

> **Report Maintained By:** Team Loading_211  
> **Contact:** [GitHub Repository Issues](https://github.com/si4795/riskintel-upay/issues)
