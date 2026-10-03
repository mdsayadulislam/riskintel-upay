# RiskIntel upay — Trust & Risk Intelligence Engine

[![Track](https://img.shields.io/badge/Track%2001-Trust%20%26%20Risk%20Intelligence-FFC800?style=for-the-badge&labelColor=063254)](https://github.com/si4795/riskintel-upay)
[![Hackathon](https://img.shields.io/badge/UCB%20Fintech%20Ltd.-AI%20DEV%20FEST%202026-063254?style=for-the-badge&labelColor=FFC800)](https://github.com/si4795/riskintel-upay)
[![Latency](https://img.shields.io/badge/Inference%20Latency-sub--20ms-10B981?style=for-the-badge&labelColor=063254)](https://github.com/si4795/riskintel-upay)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge&labelColor=063254)](LICENSE)

> **Official Submission for AI DEV FEST 2026 — Track 01: Trust & Risk Intelligence**  
> *Developed for upay (UCB Fintech Ltd., Bangladesh)*

---

## 1. Executive Overview

Mobile Financial Services (MFS) in Bangladesh process over 150 million transactions daily. High transaction volumes combined with rapid fund turnover make MFS platforms prime targets for Account Takeovers (ATO), SIM-swap velocity bursts, brute-force PIN assaults, and midnight mule cash-outs. 

**RiskIntel upay** is an ultra-low-latency (<20ms) fraud risk assessment engine and consumer transaction simulator tailored specifically for the upay ecosystem. The platform couples an optimized gradient-boosted decision forest (**LightGBM**) with local Explainable AI (**SHAP TreeExplainer**) and a real-time policy engine, enabling automated transaction triage across three operational tiers:
- **`APPROVE`** — Frictionless instant processing for verified baseline transactions.
- **`STEP_UP_2FA`** — Targeted multi-factor authentication challenge for borderline anomalies.
- **`BLOCK_IMMEDIATELY`** — Instant pre-settlement halt for critical cyber and takeover patterns, complete with self-service identity recovery.

---

## 2. ASCII Architecture Diagram

```
+-----------------------------------------------------------------------------------+
|                        RiskIntel upay - Fullstack Topology                        |
+-----------------------------------------------------------------------------------+
                                          |
                [ Consumer Client / Evaluator Dashboard ]
                Next.js 14 App Router | React | Tailwind CSS
                Authentic upay Mobile Handset + Real-Time Telemetry Inspector
                                          |
                                          | HTTP POST (JSON Payload)
                                          | sub-20ms roundtrip
                                          v
+-----------------------------------------------------------------------------------+
|                   FastAPI High-Performance Gateway (:8000)                        |
|                                                                                   |
|  - Input Validation via Pydantic v2 Schemas (TransactionPayload)                 |
|  - CORS Cross-Origin Handler & Health Probes (/health)                            |
|  - Cold-Start Singleton Loading (fraud_model.pkl, shap_explainer.pkl)             |
+-----------------------------------------------------------------------------------+
                                          |
                   +----------------------+----------------------+
                   |                                             |
                   v                                             v
+------------------------------------+       +------------------------------------+
|     LightGBM Classifier Engine     |       |     SHAP TreeExplainer Engine      |
|  - 100 Gradient-Boosted Trees      |       |  - Local Feature Attribution       |
|  - Class 1 Calibrated Probability  |       |  - Directional Impact Drivers (+/-)|
|  - Output: Risk Index (0.0 - 100.0)|       |  - Output: Top 3 Critical Features |
+------------------------------------+       +------------------------------------+
                   \                                             /
                    \                                           /
                     +--------------------+--------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                     Automated Policy & Governance Engine                          |
|                                                                                   |
|  - Score >= 75.0  --> BLOCK_IMMEDIATELY (Red Alert + Self-Service Unblock Recourse)|
|  - Score >= 40.0  --> STEP_UP_2FA       (Amber Challenge + 6-digit Mock OTP)      |
|  - Score <  40.0  --> APPROVE           (Green Instant Settlement + Balance Decr) |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                        Client Response & UI Presentation                          |
|  - SVG Clamped Circular Risk Gauge (0-100)                                        |
|  - Localized Bengali Investigation Narrative Briefing                             |
|  - Color-Coded SHAP Attribution Visual Bars                                       |
|  - Persistent Session State (LocalStorage Hydration)                              |
+-----------------------------------------------------------------------------------+
```

---

## 3. Regulatory Limits & MFS Policy Compliance

RiskIntel upay strictly enforces the transaction limits set by Bangladesh Bank for Mobile Financial Services:

| Policy Metric | P2P Send Money (ব্যক্তিগত লেনদেন) | Agent Cash-Out (এজেন্ট ক্যাশ-আউট) | Enforcement Mechanism |
| :--- | :--- | :--- | :--- |
| **Minimum per Txn** | ৳১০.০০ | ৳৫০.০০ | Client UI Guard + Backend Schema |
| **Maximum per Txn** | ৳২৫,০০০.০০ | ৳২৫,০০০.০০ | Strict Validation Warning |
| **Daily Aggregate Cap** | ৳২৫,০০০.০০ (৫ বার) | ৳২৫,০০০.০০ (৫ বার) | Dynamic Form Blocker |
| **Monthly Aggregate Cap** | ৳২,০০,০০০.০০ (৫০ বার) | ৳১,৫০,০০০.০০ (২০ বার) | Ledger Rule Check |
| **Demo Initial Balance** | ৳৩৫,০০০.০০ | ৳৩৫,০০০.০০ | Dynamic Balance with ↻ +৳২০k Top-up |

---

## 4. Evaluator Test Scenarios & Expected AI Decisions

The top Evaluator Sandbox Toolbar provides 1-click test scenarios that instantly synchronize the mobile handset inputs and background telemetry:

| Scenario Preset | Txn Parameters | Telemetry State | Expected Risk Score | Decision Action | Primary SHAP Drivers |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Normal P2P** | Amount: ৳500<br>Channel: P2P Send Money (0) | Hour: 14:00 (Daytime)<br>Velocity: 1 txn/hr<br>Device Changes: 0<br>Failed PINs: 0<br>Distance: 1.2 km | **0.05 / 100** | **`APPROVE`**<br>(Green Success) | `txn_amount` (-0.61)<br>`is_cash_out` (-0.40)<br>`device_change_count_30d` (-0.34) |
| **2. ATO Attack** | Amount: ৳25,000<br>Channel: Cash-Out (1) | Hour: 03:00 (Midnight Spike)<br>Velocity: 6 txns/hr<br>Device Changes: 2 (SIM Swap)<br>Failed PINs: 3<br>Distance: 18.5 km | **99.80 / 100** | **`BLOCK_IMMEDIATELY`**<br>(Red Halt + Recovery) | `txn_amount` (+3.07)<br>`failed_pin_attempts_24h` (+2.76)<br>`device_change_count_30d` (+2.15) |
| **3. Midnight Cashout** | Amount: ৳18,000<br>Channel: Cash-Out (1) | Hour: 02:00 (Midnight Anomaly)<br>Velocity: 4 txns/hr<br>Device Changes: 1<br>Failed PINs: 1<br>Distance: 8.0 km | **99.12 / 100** | **`BLOCK_IMMEDIATELY`**<br>(Red Halt + Recovery) | `txn_amount` (+3.08)<br>`failed_pin_attempts_24h` (+2.74)<br>`hour_of_day` (+2.45) |

---

## 5. Technology Stack Breakdown

### Backend & Machine Learning
- **Python 3.10+** — Runtime environment.
- **FastAPI** — High-throughput asynchronous REST gateway.
- **Uvicorn** — Lightning-fast ASGI web server implementation.
- **LightGBM (`LGBMClassifier`)** — Gradient-boosted decision tree algorithm trained on 12,000 synthetic MFS transactions.
- **SHAP (`TreeExplainer`)** — Game-theoretic local feature attribution calculating exact Shapley values.
- **Pydantic v2** — Strict request/response payload typing and boundary validation.
- **Joblib** — Serialization and persistence of trained model and explainer artifacts.
- **Pandas & NumPy** — High-performance vector transformations.

### Frontend Dashboard & Simulator
- **Next.js 14 (App Router)** — React-based server and client rendering architecture.
- **TypeScript** — Compile-time type safety across data pipelines.
- **Tailwind CSS** — Custom design system matching official upay brand guidelines:
  - Radiant Yellow: `#FFC800`
  - Deep Corporate Blue: `#063254`
  - Soft Neutral Canvas: `#F4F6F8`
- **Lucide React** — Crisp fintech and telemetry iconography.
- **LocalStorage API** — Automatic state hydration and cross-refresh persistence.

---

## 6. Step-by-Step Installation & Run Guide

### Prerequisites
- Python 3.10 or higher installed.
- Node.js 18.x or higher and npm installed.
- Git installed.

### Step 1: Clone the Repository
```bash
git clone https://github.com/si4795/riskintel-upay.git
cd riskintel-upay
```

### Step 2: Backend Setup & ML Pipeline Execution
```bash
# 1. Create and activate a Python virtual environment
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux / macOS:
# source venv/bin/activate

# 2. Upgrade pip and install backend dependencies
pip install --upgrade pip
pip install fastapi uvicorn lightgbm shap scikit-learn pandas numpy joblib pydantic

# 3. Train the model and generate serialized artifacts
python backend/train_pipeline.py
```
*Expected training output:*
- `models/fraud_model.pkl` generated.
- `models/shap_explainer.pkl` generated.
- `data/synthetic_upay_txns.csv` generated (12,000 rows).
- Validation ROC-AUC score: `>0.98`.

### Step 3: Launch FastAPI Gateway
```bash
python backend/main.py
```
*The API gateway runs at `http://127.0.0.1:8000`. Interactive documentation is available at `http://127.0.0.1:8000/docs`.*

### Step 4: Frontend Dashboard Setup & Launch
Open a second terminal window:
```bash
cd frontend

# Install Node dependencies
npm install

# Start the Next.js development server
npm run dev
```
*The interactive dashboard will be accessible at `http://localhost:3000`.*

---

## 7. Local Explainability & SHAP Attribution Design

Black-box machine learning models are unacceptable in regulated financial services. RiskIntel upay solves this by embedding SHAP TreeExplainer directly into the scoring loop:

$$\phi_i(x) = \sum_{S \subseteq F \setminus \{i\}} \frac{|S|!(|F| - |S| - 1)!}{|F|!} \left[ f_x(S \cup \{i\}) - f_x(S) \right]$$

1. **Local Attribution**: Every scored transaction returns the exact numerical contribution ($\phi_i$) for each of the 7 features.
2. **Directional Impact**:
   - **Positive Impact ($\phi_i > 0$)**: Pushes the transaction towards fraud (highlighted in red/amber bars).
   - **Negative Impact ($\phi_i < 0$)**: Anchors the transaction towards legitimate behavior (highlighted in green/teal bars).
3. **Auditable Narrative**: The top 3 absolute drivers are dynamically synthesized into human-readable compliance narratives for audit trails and operations teams.

---

## 8. In-App Mobile Simulator & Self-Service Unblock Workflow

Unlike generic developer consoles, RiskIntel upay simulates the actual mobile application handset experience for upay customers:
- **Balance & Top-Up**: Starts with ৳35,000.00. Evaluators can tap **+৳২০,০০০** to replenish funds at any time.
- **Dynamic Deduction**: Approving a transaction or completing identity verification deducts funds immediately across the app interface.
- **Quick Amount Chips**: `+৳500`, `+৳2,000`, `+৳10,000`, `+৳25,000` clamp within balance and regulatory daily caps; `↺` restores default ৳500.
- **Self-Service Recovery**: When a transaction is blocked (`BLOCK_IMMEDIATELY`), users are not stranded with a dead-end message. They can tap **"ওটিপি ও বায়োমেট্রিক দিয়ে তাৎক্ষণিক আনলক করুন"**, verify a 6-digit mock OTP (`123456`), clear failed PIN counts, and execute their urgent transfer safely.

---

## 9. Responsible AI & Ethical Governance

- **Zero Real PII Storage**: All training data (12,000 records) is synthetically generated using statistical distributions mirroring legitimate MFS behavior and known fraud topologies. No customer NID, phone numbers, or account pins are stored.
- **Explainability by Default**: Every automated decision is backed by mathematical feature attribution, eliminating black-box bias.
- **Human-in-the-Loop Safeguards**: Borderline transactions (scores 40.0–74.9) trigger step-up multi-factor verification rather than outright cancellation, preventing legitimate customer lockout.

---

## 10. Contributors & License

- **Developer**: Md. Suaib (si4795)
- **Track**: Track 01 — Trust & Risk Intelligence
- **Event**: AI DEV FEST 2026, UCB Fintech Ltd.
- **License**: MIT Open Source License
