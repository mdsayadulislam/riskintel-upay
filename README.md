# RiskIntel upay — Trust & Risk Intelligence Engine

> **Track 01: Trust & Risk Intelligence**  
> *AI DEV FEST 2026 Submission*  
> Developed for **upay (UCB Fintech Ltd.)** — Next-Generation Mobile Financial Services (MFS) Fraud Detection & XAI Governance.

---

## 1. Project Overview

### The MFS Fraud Challenge in Bangladesh
Bangladesh's Mobile Financial Services (MFS) ecosystem processes billions of Bangladeshi Taka (BDT) daily across more than 200 million registered accounts. As digital adoption surges, sophisticated threat actors increasingly exploit behavioral and structural vulnerabilities:
- **Account Takeover (ATO) Attacks:** Unauthorized access gained via SIM swapping, social engineering phishing, and credential stuffing, followed by rapid device re-registration.
- **Midnight Velocity Drains:** High-frequency transaction bursts coordinated between 01:00 AM and 04:00 AM while account holders sleep, delaying victim notifications and manual bank freeze protocols.
- **Mule Agent Cash-Out Liquidation:** Rapid liquidation of illicit funds via remote agent points or rogue cash-out locations before anti-money laundering (AML) circuit breakers can activate.

### The RiskIntel Solution
**RiskIntel upay** is an enterprise-grade AI risk scoring and local explainability engine designed specifically for the high-throughput, low-latency requirements of upay. By unifying ultra-fast tree-based gradient boosting (**LightGBM**) with game-theoretic local explainability (**SHAP TreeExplainer**), RiskIntel computes calibrated fraud probability scores ($0 - 100$) in sub-$15\text{ms}$ latency and generates actionable, grounded analyst narratives that prevent black-box algorithmic discrimination.

```
                           +------------------------------------------+
                           |  upay Core MFS Transaction Stream (JSON) |
                           +--------------------+---------------------+
                                                |
                                                v
                           +------------------------------------------+
                           |     FastAPI Edge Inference Gateway       |
                           |   /api/v1/assess-risk (Pydantic Schema)  |
                           +--------------------+---------------------+
                                                |
                       +------------------------+------------------------+
                       |                                                 |
                       v                                                 v
         +----------------------------+                   +----------------------------+
         |     LightGBM Classifier    |                   |     SHAP TreeExplainer     |
         | Calibrated Fraud Log-Odds  |                   |  Local Feature Attribution |
         +-------------+--------------+                   +--------------+-------------+
                       |                                                 |
                       +------------------------+------------------------+
                                                |
                                                v
                           +------------------------------------------+
                           |       Deterministic Policy Engine        |
                           |   Score-Based Risk Tiering & Narrative   |
                           +--------------------+---------------------+
                                                |
                     +--------------------------+--------------------------+
                     |                          |                          |
                     v                          v                          v
             [Score < 40]               [Score 40 - 74]             [Score >= 75]
               APPROVE                    STEP_UP_2FA              BLOCK_IMMEDIATELY
             (Low Risk)                  (Medium Risk)                (High Risk)
```

---

## 2. Core Features

- **Dynamic Risk Scoring Engine (0–100 Gauge Scale):** Continuously scores transaction risk using a trained LightGBM binary classifier ($n=100$) with probabilistic calibration.
- **Local Explainability via SHAP TreeExplainer:** Deconstructs each individual prediction into exact mathematical contribution values (log-odds impact) for every feature, isolating the Top 3 local risk drivers.
- **Real-Time Dual-View Transaction Simulator:** Interactive analyst console featuring granular controls for all 7 critical transaction vectors alongside 1-click test archetypes.
- **Policy-Driven Action Governance:**
  - `APPROVE` ($\text{Score} < 40$): Low risk baseline; frictionless transaction completion.
  - `STEP_UP_2FA` ($40 \le \text{Score} < 75$): Medium risk; prompts user for biometric or SMS OTP challenge.
  - `BLOCK_IMMEDIATELY` ($\text{Score} \ge 75$): High risk anomaly; transaction halted and flagged for audit.
- **Grounded AI Investigation Narrative:** Auto-generates structured, context-specific 3-sentence briefings for fraud analysts, eliminating opaque decisions and ensuring end-to-end operational transparency.

---

## 3. Technology Stack

| Layer | Technologies | Purpose |
| :--- | :--- | :--- |
| **Machine Learning** | LightGBM, SHAP, Scikit-Learn, Joblib, NumPy, Pandas | Synthetic dataset generation, gradient boosted decision trees, TreeSHAP explainer, metric evaluation |
| **Backend API** | FastAPI, Uvicorn, Pydantic v2 | High-concurrency async REST API, strict schema validation, dynamic model path resolution |
| **Frontend Dashboard** | Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Lucide Icons | Dual-column responsive triage console, animated SVG gauge, SHAP bar charts, real-time telemetry |

---

## 4. Prerequisites & Requirements

- **Operating System:** Windows 10/11, macOS, or Linux
- **Python:** Python 3.10+ (tested on Python 3.14)
- **Node.js:** Node.js 18.x or 20.x+ (tested on Node v22.14.0) with `npm`
- **Memory & Storage:** 4 GB RAM minimum; 500 MB free disk space

---

## 5. Step-by-Step Local Installation & Setup

Open **Windows Command Prompt (`cmd.exe`)** or **PowerShell** and execute the following commands:

```cmd
:: 1. Clone the repository and enter the root workspace
git clone https://github.com/your-username/riskintel-upay.git
cd riskintel-upay

:: 2. Setup Python Virtual Environment and Install Backend Dependencies
python -m venv venv
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

:: 3. Train the Model and Generate Artifacts
:: (Generates 12,000 synthetic upay rows, trains LightGBM, fits SHAP, and saves models)
python backend/train_pipeline.py

:: 4. Install Frontend Dependencies
cd frontend
npm install
cd ..
```

---

## 6. Environment Variables Configuration

### Backend Configuration
The backend is engineered with zero-configuration sensible defaults. Optionally create `backend/.env` for custom network bindings:

```env
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development
CORS_ORIGINS=["*"]
```

### Frontend Configuration
Create `frontend/.env.local` (optional, defaults to local FastAPI URL):

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1/assess-risk
NEXT_PUBLIC_HEALTH_URL=http://localhost:8000/health
```

---

## 7. Run and Build Commands

### Step 1: Start the Backend Server (Terminal 1)
From the project root:
```cmd
call venv\Scripts\activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
*The FastAPI backend will start at `http://localhost:8000`. Access interactive API documentation at `http://localhost:8000/docs`.*

### Step 2: Start the Frontend Dashboard (Terminal 2)
From the project root:
```cmd
cd frontend
npm run dev
```
*The Next.js dashboard will be accessible at `http://localhost:3000`.*

### Optional: Frontend Production Build
To verify production optimization and static bundle size:
```cmd
cd frontend
npm run build
npm run start
```

---

## 8. Live Deployment URLs

| Service | Platform | URL Placeholder | Status |
| :--- | :--- | :--- | :--- |
| **Frontend Web App** | Vercel | `https://riskintel-upay.vercel.app` | Ready for Deployment |
| **Backend REST API** | Render / Railway | `https://riskintel-upay-api.onrender.com` | Ready for Deployment |
| **Interactive API Docs** | Swagger UI | `https://riskintel-upay-api.onrender.com/docs` | Ready for Deployment |

---

## 9. Testing Instructions & Scenario Verification

RiskIntel includes 3 pre-configured scenario presets in the web interface and CLI for immediate evaluation.

### Preset A: Scenario 1 — "Normal P2P" (Legitimate Everyday User)
- **Vectors:** Amount: ৳500 | Hour: 14:00 | Velocity: 1 | Failed PINs: 0 | Device Changes: 0 | Cash-Out: 0 (P2P)
- **Expected Outcome:**
  - **Risk Score:** $< 40.0$ (typically $\approx 0.03$)
  - **Verdict:** `APPROVE` (Emerald Green)
  - **Narrative:** *"Transaction conforms to expected baseline behavior. Low fraud probability across velocity and biometric markers."*

```bash
curl -X POST http://localhost:8000/api/v1/assess-risk \
  -H "Content-Type: application/json" \
  -d '{"txn_amount":500,"hour_of_day":14,"device_change_count_30d":0,"velocity_last_1h":1,"agent_distance_km":1.2,"failed_pin_attempts_24h":0,"is_cash_out":0}'
```

---

### Preset B: Scenario 2 — "Account Takeover (ATO) Attack"
- **Vectors:** Amount: ৳25,000 | Hour: 03:00 (Midnight) | Velocity: 6 | Failed PINs: 3 | Device Changes: 2 | Cash-Out: 1
- **Expected Outcome:**
  - **Risk Score:** $\ge 75.0$ (typically $\ge 99.0$)
  - **Verdict:** `BLOCK_IMMEDIATELY` (Crimson Red)
  - **Top SHAP Drivers:** `txn_amount`, `failed_pin_attempts_24h`, `device_change_count_30d`
  - **Narrative:** *"Critical risk detected. Significant anomaly driven by txn_amount, failed_pin_attempts_24h, device_change_count_30d. Transaction halted; step-up audit mandated for upay operations."*

```bash
curl -X POST http://localhost:8000/api/v1/assess-risk \
  -H "Content-Type: application/json" \
  -d '{"txn_amount":25000,"hour_of_day":3,"device_change_count_30d":2,"velocity_last_1h":6,"agent_distance_km":18.5,"failed_pin_attempts_24h":3,"is_cash_out":1}'
```

---

### Preset C: Scenario 3 — "Midnight Cash-out Anomaly"
- **Vectors:** Amount: ৳18,000 | Hour: 02:00 | Velocity: 4 | Failed PINs: 1 | Device Changes: 1 | Cash-Out: 1
- **Expected Outcome:**
  - **Risk Score:** $40.0 \le \text{Score} < 75.0$ (typically $\approx 69.3$)
  - **Verdict:** `STEP_UP_2FA` (Amber Yellow)
  - **Top SHAP Drivers:** `txn_amount`, `is_cash_out`, `hour_of_day`
  - **Narrative:** *"Moderate risk variance identified due to elevated txn_amount, is_cash_out, hour_of_day. Prompt user for biometric or SMS OTP challenge."*

```bash
curl -X POST http://localhost:8000/api/v1/assess-risk \
  -H "Content-Type: application/json" \
  -d '{"txn_amount":18000,"hour_of_day":2,"device_change_count_30d":1,"velocity_last_1h":4,"agent_distance_km":8.0,"failed_pin_attempts_24h":1,"is_cash_out":1}'
```

---

## 10. Responsible AI, Bias & Compliance

RiskIntel upay has been architected to adhere strictly to the **Trust & Risk Intelligence** mandate of AI DEV FEST 2026 and national regulatory frameworks:

1. **Zero Synthetic Personally Identifiable Information (PII):**
   - The engine processes exclusively anonymized behavioral, temporal, and spatial telemetry (`txn_amount`, `hour_of_day`, `velocity_last_1h`, etc.).
   - No National ID (NID) numbers, biometric raw templates, phone numbers (MSISDN), or demographic identifiers are stored, ingested, or used for model training.

2. **Explainability-First Architecture (Preventing Black-Box Harm):**
   - Traditional deep neural networks create opaque decisions that harm consumer trust. RiskIntel integrates **SHAP (Shapley Additive Explanations)** directly into every inference request.
   - For every flagged transaction, the engine computes exact Shapley values showing which feature increased or decreased risk, empowering compliance analysts to justify decisions.

3. **Human-in-the-Loop Analyst Governance:**
   - Transactions with moderate risk ($40 \le \text{Score} < 75$) are not outright blocked; rather, a stepped-up challenge (`STEP_UP_2FA`) is triggered, protecting consumer inclusion while preventing fraudulent loss.
   - High-risk halts (`BLOCK_IMMEDIATELY`) provide full audit logs ready for review by human fraud investigation teams.

4. **Regulatory Alignment with Bangladesh Bank Guidelines:**
   - Adheres to the **Bangladesh Bank Guidelines for Mobile Financial Services (MFS)** and the **National Payment Systems Regulatory Framework**.
   - Preserves deterministic audit trails that satisfy AML/CFT (Anti-Money Laundering and Combating the Financing of Terrorism) inspection requirements.

---

## License & Attribution
Developed for the **AI DEV FEST 2026** Hackathon (Track 01: Trust & Risk Intelligence).  
*Proprietary concept designed for evaluation and demonstration with upay (UCB Fintech Ltd.).*
