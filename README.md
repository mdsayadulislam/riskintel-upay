# RiskIntel upay — Trust & Risk Intelligence Engine

[![Track](https://img.shields.io/badge/Track%2001-Trust%20%26%20Risk%20Intelligence-FFC800?style=for-the-badge&labelColor=063254)](https://github.com/mdsayadulislam/riskintel-upay)
[![Hackathon](https://img.shields.io/badge/UCB%20Fintech%20Ltd.-AI%20DEV%20FEST%202026-063254?style=for-the-badge&labelColor=FFC800)](https://github.com/mdsayadulislam/riskintel-upay)
[![Security Status](https://img.shields.io/badge/Production%20Security-Hardened%20%26%20Tested-10B981?style=for-the-badge&labelColor=063254)](JUDGE_FEEDBACK_RESPONSE.md)
[![Inference Latency](https://img.shields.io/badge/Inference%20Latency-sub--15ms-10B981?style=for-the-badge&labelColor=063254)](https://github.com/mdsayadulislam/riskintel-upay)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge&labelColor=063254)](LICENSE)

> **Official Submission for AI DEV FEST 2026 — Track 01: Trust & Risk Intelligence**  
> _Developed for upay (UCB Fintech Ltd., Bangladesh) by Team Loading_211_

---

## Quick Navigation & Technical Reports

- **[Judge Feedback Resolution (`JUDGE_FEEDBACK_RESPONSE.md`)](JUDGE_FEEDBACK_RESPONSE.md)** — Detailed response addressing all judge feedback with test proofs.
- **[Security Gap Audit Report (`SECURITY_GAP_REPORT.md`)](SECURITY_GAP_REPORT.md)** — Baseline security assessment and gap analysis.
- **[ML Model Validation Report (`MODEL_VALIDATION_REPORT.md`)](MODEL_VALIDATION_REPORT.md)** — Comprehensive validation report with ROC-AUC, PR-AUC, confusion matrices, and threshold trade-offs.
- **[Final Security Review (`FINAL_SECURITY_REVIEW.md`)](FINAL_SECURITY_REVIEW.md)** — Complete verification, audit checklist, and deployment review.

---

## 1. Executive Overview

Mobile Financial Services (MFS) in Bangladesh process over **150 million transactions daily**. The speed of digital transfers and instant cash-out mechanisms make MFS platforms prime targets for Account Takeovers (ATO), SIM-swap velocity bursts, brute-force PIN probing, and midnight mule cash-outs.

**RiskIntel upay** is an ultra-low-latency (<15ms), explainable fraud prevention engine and interactive consumer transaction simulator tailored specifically for the upay ecosystem. The platform couples an optimized gradient-boosted decision forest (**LightGBM**) with local Explainable AI (**SHAP TreeExplainer**), a real-time governance policy engine, and production-grade security:

- **`APPROVE` (Score < 40.0):** Frictionless instant processing for verified baseline transactions.
- **`STEP_UP_2FA` (Score 40.0 – 74.9):** Targeted multi-factor authentication challenge for borderline anomalies.
- **`BLOCK_IMMEDIATELY` (Score $\ge$ 75.0):** Pre-settlement security halt with an immediate self-service identity recovery pathway and helpline escalation.

---

## 2. Fullstack Architecture & Security Topology

```
+-----------------------------------------------------------------------------------+
|                        RiskIntel upay - Fullstack Topology                        |
+-----------------------------------------------------------------------------------+
                                          |
                [ Consumer Client / Evaluator Dashboard ]
                Next.js 14 App Router | React 18 | TypeScript | Tailwind CSS
                Authentic upay Mobile Handset + Real-Time Telemetry Inspector
                                          |
                                          | HTTP POST (JSON Payload + Bearer JWT)
                                          | sub-15ms roundtrip
                                          v
+-----------------------------------------------------------------------------------+
|               FastAPI High-Performance Gateway (:8000) - HARDENED                |
|                                                                                   |
|  - Security Headers (CSP, nosniff, frame-ancestors, HSTS)                         |
|  - Restrictive CORS Allowlist (No Wildcards for Authenticated APIs)               |
|  - Sliding-Window Rate Limiting (60 req/min with HTTP 429 & Retry-After)         |
|  - JWT Bearer Authentication (HS256) & Role-Based Access Control (RBAC)           |
|  - Pydantic v2 Boundary Validation (le=৳25,000 BB MFS Limit, Enum Bounds)         |
+-----------------------------------------------------------------------------------+
                                          |
                    +---------------------+---------------------+
                    |                                           |
                    v                                           v
+------------------------------------+     +------------------------------------+
|     LightGBM Classifier Engine     |     |     SHAP TreeExplainer Engine      |
|  - 100 Gradient-Boosted Trees      |     |  - Local Feature Attribution       |
|  - Class 1 Calibrated Probability  |     |  - Directional Impact Drivers (+/-)|
|  - Output: Risk Index (0.0 - 100.0)|     |  - Output: Top 3 Critical Features |
+------------------------------------+     +------------------------------------+
                    \                                           /
                     \                                         /
                      +-------------------+-------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                     Automated Policy & Governance Engine                          |
|                                                                                   |
|  - Score >= 75.0  --> BLOCK_IMMEDIATELY (Pre-settlement halt + Single-Use Recovery)|
|  - Score >= 40.0  --> STEP_UP_2FA       (Salted SHA-256 OTP + 5m TTL)             |
|  - Score <  40.0  --> APPROVE           (Instant Settlement & Balance Decr)       |
+-----------------------------------------------------------------------------------+
                                          |
                    +---------------------+---------------------+
                    |                                           |
                    v                                           v
+------------------------------------+     +------------------------------------+
|     Durable SQLite Audit Ledger    |     |     Live Client Feedback & UI      |
|  - Write-Ahead Logging (WAL Mode)  |     |  - SVG Clamped Circular Risk Gauge |
|  - Immutable Append-Only Schema    |     |  - Bengali Compliance Narrative    |
|  - Zero Secret / Zero PII Scrubbing|     |  - Color-Coded SHAP Visual Bars    |
|  - Authorized Inspection API       |     |  - Live Security Controls Status   |
+------------------------------------+     +------------------------------------+
```

---

## 3. Production Security Implementations (Addressing Judge Criticisms)

### 3.1 Authentication & Role-Based Authorization
- **Endpoint Protection:** The risk evaluation endpoint (`POST /api/v1/assess-risk`) strictly requires authentication. Unauthenticated requests return `HTTP 401 Unauthorized` with `WWW-Authenticate: Bearer`.
- **Identity Derivation:** The authenticated user identity is derived strictly from the verified JWT payload; client-supplied identifiers are never trusted.
- **RBAC Enforcement:** Compliance endpoints (such as `GET /api/v1/audit/logs`) require `analyst` or `admin` roles, returning `HTTP 403 Forbidden` for standard customer accounts.
- **Demo Credentials:**
  - Standard Customer: `demo_user` / `Upay@2026!` (Role: `customer`)
  - Compliance Officer: `compliance_officer` / `Analyst@2026!` (Role: `analyst`)
  - Security Administrator: `security_admin` / `Admin@2026!` (Role: `admin`)

### 3.2 Server-Side Sliding-Window Rate Limiting
- Configurable per-route rate limits enforced at the gateway:
  - Risk Assessment: `60 requests / minute`
  - Authentication Login: `10 requests / minute`
  - 2FA Challenge & Verification: `10 requests / minute`
  - Account Recovery: `5 requests / minute`
- Exceeding limits returns `HTTP 429 Too Many Requests` with a compliant `Retry-After: <seconds>` header.

### 3.3 Restrictive CORS Allowlist
- Removed wildcard `*` origins.
- Uses strict allowlist configured via `ALLOWED_ORIGINS` environment variable (e.g., `http://localhost:3000,https://riskintel-upay.vercel.app`).
- Rejects untrusted origins without CORS response headers.

### 3.4 Cryptographic Step-Up 2FA & Single-Use Recovery
- **Real 2FA Engine:** Replaced client-side simulation with server-side challenge issuance. Generates a 6-digit CSPRNG OTP, unique salt, and stores salted SHA-256 hashes in SQLite with a 5-minute TTL. Enforces a 3-attempt maximum and replay prevention.
- **Real Account Recovery:** Issues high-entropy single-use recovery tokens (SHA-256 hashed at rest) with a 15-minute TTL. Features **anti-enumeration defenses** (identical generic message returned regardless of account existence) and atomic token consumption.

### 3.5 Persistent SQLite Audit Logging
- Durable append-only storage configured with **Write-Ahead Logging (WAL)**.
- Records timestamp, request correlation ID (`X-Request-ID`), event type, actor ID, endpoint, status code, risk score, decision action, model version, and top SHAP drivers.
- **Zero PII / Zero Secret Guarantee:** Passwords, OTPs, recovery tokens, and authorization keys are automatically redacted prior to insertion.
- Authorized query endpoint: `GET /api/v1/audit/logs` (requires `analyst` or `admin` role).

### 3.6 Defensive HTTP Security Headers
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Content-Security-Policy: default-src 'self'; frame-ancestors 'none';`
- `Cache-Control: no-store, no-cache` on sensitive API endpoints.

---

## 4. Machine Learning & Local Explainability (SHAP)

### 4.1 Feature Dictionary
The model processes 7 real-time telemetry inputs reflecting behavioral, temporal, spatial, and device-level risk indicators:

| Feature Name | Type | Range / Distribution | Real-World MFS Significance |
| :--- | :--- | :--- | :--- |
| `txn_amount` | `float` | ৳10.00 – ৳25,000.00 | Fraudsters maximize transfers near the ৳25,000 Bangladesh Bank ceiling. |
| `hour_of_day` | `int` | 0 – 23 (24h clock) | Anomaly spikes occur during midnight hours (01:00 – 04:00) when victims sleep. |
| `device_change_count_30d` | `int` | 0 – 4 switches | Multiple device switches indicate SIM swap or device takeover attacks. |
| `velocity_last_1h` | `int` | 0 – 15 txns/hr | High frequency indicates automated liquidity draining. |
| `agent_distance_km` | `float` | 0.1 – 45.0 km | High distance indicates remote mule cash-out points. |
| `failed_pin_attempts_24h` | `int` | 0 – 4 attempts | Repeated failures indicate brute-force PIN probing. |
| `is_cash_out` | `int` | 0 (P2P) or 1 (Cash-Out) | Agent cash-outs are irreversible and carry higher fraud risk. |

### 4.2 Local XAI Decomposition (SHAP TreeExplainer)
Every scored transaction returns the exact numerical Shapley contribution ($\phi_i$) for each feature:
- **Positive Impact ($\phi_i > 0$):** Pushes transaction towards fraud (amber/red bars).
- **Negative Impact ($\phi_i < 0$):** Anchors transaction towards legitimate baseline (green/teal bars).
- Top 3 absolute drivers are synthesized dynamically into compliance narratives.

---

## 5. Machine Learning Validation Summary

Derived from the held-out test partition ($N=1,800$, clean test split):

- **Dataset Size:** 12,000 synthetic transaction records (8.91% fraud incidence).
- **Stratified Partition:** 70% Train (8,400) / 15% Validation (1,800) / 15% Pristine Test (1,800).
- **ROC-AUC Score:** **`0.9780`**
- **PR-AUC Score (Precision-Recall):** **`0.8247`**
- **Confusion Matrix at $\tau = 0.50$:** TN: 1,567 | FP: 73 | FN: 21 | TP: 139
- **Precision:** `65.57%` | **Recall:** `86.88%` | **F1-Score:** `0.7473`
- **FPR:** `4.45%` | **FNR:** `13.13%`

### Threshold Tradeoff Summary:
- **$\tau = 0.40$ (`STEP_UP_2FA`):** Recall is `88.75%` with an FPR of `5.91%`. Catches fraud early while subjecting only 5.9% of legitimate users to a mild step-up challenge.
- **$\tau = 0.75$ (`BLOCK_IMMEDIATELY` / Hold):** Precision rises to `71.43%` and FPR drops to `3.05%`, minimizing false accusations before initiating pre-settlement hold with recovery recourse.

_For full scientific analysis, see [`MODEL_VALIDATION_REPORT.md`](MODEL_VALIDATION_REPORT.md)._

---

## 6. Installation & Execution Guide

### Prerequisites
- Python 3.10+ installed.
- Node.js 18.x+ and npm installed.

### Step 1: Clone Repository
```bash
git clone https://github.com/mdsayadulislam/riskintel-upay.git
cd riskintel-upay
```

### Step 2: Backend Setup & ML Pipeline Execution
```bash
# 1. Create and activate Python virtual environment
python -m venv backend/venv

# Windows (PowerShell):
.\backend\venv\Scripts\Activate.ps1
# Linux / macOS:
# source backend/venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Train LightGBM model, fit SHAP explainer, and generate validation report
python backend/train_pipeline.py
```

### Step 3: Run Automated Security Test Suite
```bash
pytest backend/tests/test_security.py -v
```
_Expected output: `18 passed in ~7s` verifying authentication, rate limiting, CORS, 2FA, recovery, audit logs, and XAI consistency._

### Step 4: Launch FastAPI Gateway
```bash
python backend/main.py
```
_The API gateway runs at `http://127.0.0.1:8000`. Interactive OpenAPI documentation is available at `http://127.0.0.1:8000/docs`._

### Step 5: Frontend Simulator Setup & Launch
Open a second terminal:
```bash
cd frontend
npm install
npm run dev
```
_The interactive dashboard will be accessible at `http://localhost:3000`._

---

## 7. Environment Variables Reference

Copy `.env.example` in `backend/` to `.env` and configure:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `RISKINTEL_ENV` | `development` | Environment mode (`development`, `staging`, `production`) |
| `JWT_SECRET_KEY` | _(dev default)_ | Cryptographic secret for signing JWTs (**Must change in production**) |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Token expiration window |
| `ALLOWED_ORIGINS` | `http://localhost:3000,...` | Comma-separated list of allowed CORS origins |
| `RATE_LIMIT_ASSESS_PER_MIN` | `60` | Request ceiling for risk scoring endpoint |
| `RATE_LIMIT_AUTH_PER_MIN` | `10` | Request ceiling for authentication login |
| `DATABASE_PATH` | `data/riskintel_audit.db` | SQLite persistent database path |
| `TWO_FACTOR_EXPIRY_SECONDS` | `300` | Step-up 2FA OTP time-to-live |
| `RECOVERY_TOKEN_EXPIRY_SECONDS` | `900` | Account recovery token time-to-live |

---

## 8. Hackathon Prototype vs. Production Deployment

| Dimension | Hackathon Prototype (Implemented) | Production Deployment Requirements |
| :--- | :--- | :--- |
| **Data Scope** | 12,000 synthetic transaction records | Historical banking data lakes (petabyte scale, multi-year) |
| **PII Handling** | Zero real PII; synthetic identifiers | Full HSM encryption, NID tokenization, ISO 27001 / PCI-DSS compliance |
| **Rate Limiter** | Thread-safe sliding window in-memory | Distributed Redis cluster with Sentinel / Redis Cluster |
| **Audit Ledger** | SQLite with Write-Ahead Logging (WAL) | Distributed PostgreSQL / Amazon Aurora with WORM compliance storage |
| **Model Serving** | Single-process FastAPI + Uvicorn | Kubernetes (EKS / GKE) horizontal pod autoscaling with Triton / TorchServe |
| **Model Validation** | Clean 70/15/15 synthetic split | 60-day parallel shadow-mode testing on live traffic with BFIU regulatory oversight |

---

## 9. Team & Contributors

- **Team Name:** Loading_211
- **Track:** Track 01 — Trust & Risk Intelligence
- **Event:** AI DEV FEST 2026
- **Members:**
  1. **Md. Suaib Islam** ([@si4795](https://github.com/si4795)) — Lead Full-Stack Architect & Security Engineer
  2. **Md. Sayadul Islam** — Machine Learning Researcher & Data Modeler
  3. **Md. Elias Ahmed** — Frontend UX Engineer & QA Specialist
- **License:** MIT Open Source License
