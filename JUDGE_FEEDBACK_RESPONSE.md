# Judge Feedback Resolution: RiskIntel upay

**Event:** AI DEV FEST 2026 — Track 01: Trust & Risk Intelligence  
**Team:** Loading_211  
**Project:** RiskIntel upay (Trust & Risk Intelligence Engine for upay MFS)  
**Date:** October 2026  
**Status:** All Critical Criticisms Resolved, Verified & Tested

---

## Overview of Resolutions

This document provides explicit, evidence-backed answers to the evaluation feedback provided by Hackathon Judges 1, 2, and 3. Every single criticism has been solved with production-grade backend controls, persistent database durability, real cryptographic algorithms, and automated unit/integration tests.

| Feedback Source | Criticism | Remediation Summary | Automated Test Status |
| :--- | :--- | :--- | :---: |
| **Judge 1** | *"No authentication on the risk endpoint"* | Implemented JWT (HS256) Bearer token authentication + RBAC; unauthenticated requests return HTTP 401. | `PASSED` |
| **Judge 2** | *"Real-world security and fraud-model validation remain outstanding"* | Built stratified 3-way partition (70/15/15), PR-AUC (0.8247), ROC-AUC (0.9780), confusion matrix, threshold trade-off analysis (FPR vs. FNR), and honest production roadmap. | `PASSED` |
| **Judge 3** | *"API lacks authentication / rate limiting"* | Added sliding-window rate limiter per IP/token with HTTP 429 & Retry-After headers across all routes. | `PASSED` |
| **Judge 3** | *"CORS is permissive"* | Removed wildcard `*`; enforced strict domain allowlist loaded from environment variables (`ALLOWED_ORIGINS`). | `PASSED` |
| **Judge 3** | *"Recovery / 2FA are simulated"* | Replaced frontend mock delays with server-side salted SHA-256 OTP challenges, attempt counters (max 3), replay prevention, and single-use recovery tokens. | `PASSED` |
| **Judge 3** | *"Claimed audit/compliance controls not durable"* | Migrated from ephemeral stdout logs to persistent SQLite WAL append-only `audit_logs` table with zero PII/secret leakage and role-protected query API. | `PASSED` |

---

## Issue 1: No Authentication on Risk Endpoint

### Problem
In the initial prototype, `POST /api/v1/assess-risk` was completely unauthenticated. Any anonymous client or attacker could issue unlimited HTTP POST requests, scrape model probabilities, and reverse-engineer proprietary decision rules.

### Fix
- Implemented cryptographic JWT (HS256) authentication in `backend/auth.py` and guarded `/api/v1/assess-risk` using FastAPI dependency injection (`get_current_user`).
- Derived the caller's identity (`user_id`, `role`, `scopes`) strictly from the server-validated JWT payload. Client-supplied `user_id` is never trusted.
- Enforced role-based authorization (`require_role`): unauthenticated requests return `HTTP 401 Unauthorized` with `WWW-Authenticate: Bearer`; authenticated users lacking required role (e.g., customer attempting to view audit logs) return `HTTP 403 Forbidden`.
- Integrated synthetic demo credentials for evaluation:
  - `demo_user` (Role: `customer`, Password: `Upay@2026!`)
  - `compliance_officer` (Role: `analyst`, Password: `Analyst@2026!`)
  - `security_admin` (Role: `admin`, Password: `Admin@2026!`)

### Evidence
- File: [`backend/auth.py`](file:///d:/riskintel-upay/backend/auth.py#L190-L240)
- File: [`backend/main.py`](file:///d:/riskintel-upay/backend/main.py#L425-L445)

### Test
- `test_unauthenticated_risk_request_returns_401`: Verifies unauthenticated request returns `401`.
- `test_authenticated_risk_request_allowed`: Verifies valid Bearer token returns `200 OK`.
- `test_unauthorized_role_returns_403`: Verifies role-based access denial returns `403`.

---

## Issue 2: Missing Rate Limiting

### Problem
The API gateway lacked request throttling. An attacker could flood the inference engine with denial-of-service requests or brute-force user passwords and 2FA OTP codes without restriction.

### Fix
- Built a thread-safe sliding-window rate limiter in `backend/rate_limiter.py`.
- Enforces configurable per-minute limits via environment variables:
  - Risk Assessment: `RATE_LIMIT_ASSESS_PER_MIN=60`
  - Authentication Login: `RATE_LIMIT_AUTH_PER_MIN=10`
  - 2FA Verification: `RATE_LIMIT_2FA_PER_MIN=10`
  - Account Recovery: `RATE_LIMIT_RECOVERY_PER_MIN=5`
- Returns `HTTP 429 Too Many Requests` with a mandatory `Retry-After: <seconds>` header.
- Designed as an in-memory sliding window that can be swapped directly for Redis in multi-instance clusters.

### Evidence
- File: [`backend/rate_limiter.py`](file:///d:/riskintel-upay/backend/rate_limiter.py#L18-L100)
- File: [`backend/config.py`](file:///d:/riskintel-upay/backend/config.py#L27-L35)

### Test
- `test_excessive_risk_requests_rate_limit_429`: Verifies 61st request within 60s returns `429` with `Retry-After`.
- `test_excessive_login_attempts_rate_limit_429`: Verifies credential brute force returns `429`.

---

## Issue 3: Permissive CORS

### Problem
The backend previously applied `allow_origins=["*"]` while enabling `allow_credentials=True`. This permissive wildcard violates browser security standards and exposes authenticated sessions to Cross-Origin Request Forgery (CSRF) and credential exfiltration.

### Fix
- Removed the wildcard `*`.
- Configured a strict origin allowlist in `backend/config.py` read from the `ALLOWED_ORIGINS` environment variable.
- In production, only explicitly allowed domains (e.g. `https://riskintel-upay.vercel.app`) and local development origins receive CORS response headers.
- Untrusted origins are blocked without `Access-Control-Allow-Origin` headers.

### Evidence
- File: [`backend/main.py`](file:///d:/riskintel-upay/backend/main.py#L115-L125)
- File: [`backend/config.py`](file:///d:/riskintel-upay/backend/config.py#L22-L26)

### Test
- `test_unauthorized_cors_origin_rejected`: Verifies `https://attacker-domain-malicious.com` receives no wildcard or reflected origin header.
- `test_valid_cors_origin_accepted`: Verifies `http://localhost:3000` receives allowed origin and credential headers.

---

## Issue 4: Simulated 2FA / Account Recovery

### Problem
In the original submission, both 2FA and account recovery were client-side visual simulations in `frontend/app/page.tsx` using `setTimeout()` and hardcoded codes (`841920` and `123456`). No backend security challenge was actually executed.

### Fix
1. **Real Cryptographic 2FA (`backend/two_factor.py`):**
   - Challenge generation (`POST /api/v1/auth/2fa/challenge`): Generates a 6-digit CSPRNG OTP, generates a unique salt, hashes the OTP with SHA-256, and stores the challenge in SQLite with a 5-minute TTL.
   - Generates an emergency single-use backup recovery code (e.g. `UPAY-A4F1-99B2`) also hashed with SHA-256.
   - Verification (`POST /api/v1/auth/2fa/verify`): Validates code against salted hash with constant-time comparison, enforces a 3-attempt maximum, marks challenge as consumed (`verified = 1`) to prevent replay attacks, and logs the event in the audit trail.
2. **Real Account Recovery (`backend/recovery.py`):**
   - Request (`POST /api/v1/recovery/request`): Generates a high-entropy URL-safe cryptographic token (32 bytes), hashes it with SHA-256, and stores with a 15-minute TTL.
   - Anti-Enumeration Defense: Returns an identical generic confirmation message whether or not the account exists, preventing user enumeration attacks.
   - Verification (`POST /api/v1/recovery/verify`): Verifies token hash, checks expiration, atomically sets `used = 1` to guarantee single-use consumption, resets security hold, and logs the event.

### Evidence
- File: [`backend/two_factor.py`](file:///d:/riskintel-upay/backend/two_factor.py#L50-L150)
- File: [`backend/recovery.py`](file:///d:/riskintel-upay/backend/recovery.py#L40-L120)

### Test
- `test_invalid_2fa_rejected`: Rejects wrong OTP with `400` and decrements attempts.
- `test_valid_2fa_and_replay_prevention`: First verification succeeds; second attempt with same OTP is rejected.
- `test_expired_2fa_rejected`: Rejects expired challenge.
- `test_reused_recovery_token_rejected`: Verifies recovery token once, then rejects reuse attempt.
- `test_expired_recovery_token_rejected`: Rejects expired recovery token.

---

## Issue 5: Missing Durable Audit Controls

### Problem
Audit logging was previously implemented solely as Python `logger.info()` console statements. If the application server restarted, crashed, or was deployed in a container, all audit trails vanished. There was no persistent compliance record for Bangladesh Bank inspection.

### Fix
- Built a durable SQLite persistence engine in `backend/database.py` with **Write-Ahead Logging (WAL)** enabled for crash resilience and concurrency.
- Created an append-only `audit_logs` table storing:
  - Timestamp (ISO 8601 UTC)
  - Correlation Request ID (`X-Request-ID`)
  - Event Type (`RISK_ASSESSMENT`, `STEP_UP_2FA_VERIFIED`, `RECOVERY_VERIFIED`, etc.)
  - Actor ID & Role (derived from JWT)
  - Endpoint & HTTP Status
  - Calibrated Risk Score & Decision Action
  - Model Version & Top SHAP Risk Drivers
  - Client IP
- **Zero PII & Zero Secret Guarantee:** Automated sanitizer scrubs passwords, tokens, raw OTPs, and authorization keys prior to database insertion.
- Created an authorized compliance inspection API (`GET /api/v1/audit/logs`) restricted to `analyst` and `admin` roles with pagination and filtering.

### Evidence
- File: [`backend/database.py`](file:///d:/riskintel-upay/backend/database.py#L38-L90)
- File: [`backend/audit.py`](file:///d:/riskintel-upay/backend/audit.py#L25-L160)

### Test
- `test_audit_event_is_persisted`: Verifies transaction scoring persists an immutable row to SQLite.
- `test_password_otp_token_never_in_audit_logs`: Verifies sensitive credentials are never stored in audit logs.
- `test_unauthorized_role_returns_403`: Verifies regular customer cannot access audit log API.

---

## Issue 6: Fraud Model Validation

### Problem
The initial pipeline reported basic classification accuracy and refit on the full dataset without publishing held-out test artifacts, threshold sweep analysis, PR-AUC, or confusion matrices.

### Fix
- Enhanced `backend/train_pipeline.py` with a **strict 3-way stratified partition**:
  - Training Partition (70% = 8,400 records)
  - Validation Partition (15% = 1,800 records)
  - Clean Test Partition (15% = 1,800 records, never touched during fitting)
- Evaluated on clean test set:
  - **ROC-AUC:** `0.9780`
  - **PR-AUC (Precision-Recall Area Under Curve):** `0.8247`
  - **Confusion Matrix at $\tau = 0.50$:** TN: 1,567, FP: 73, FN: 21, TP: 139
- Conducted a full **Threshold Sweep ($\tau \in [0.20, 0.90]$)** analyzing the trade-off between False Positive Rate (customer friction) and False Negative Rate (fraud loss).
- Published machine-readable validation artifact: `models/model_metrics.json`.
- Published comprehensive documentation: `MODEL_VALIDATION_REPORT.md`.
- Stated explicitly that synthetic benchmark validation does not prove production readiness on live banking traffic without governed shadow-mode testing.

### Evidence
- File: [`backend/train_pipeline.py`](file:///d:/riskintel-upay/backend/train_pipeline.py#L170-L300)
- File: [`models/model_metrics.json`](file:///d:/riskintel-upay/models/model_metrics.json)
- File: [`MODEL_VALIDATION_REPORT.md`](file:///d:/riskintel-upay/MODEL_VALIDATION_REPORT.md)

### Test
- `test_risk_explanation_generated_correctly`: Verifies SHAP drivers match expected model weights.
- `test_model_prediction_and_explanation_remain_consistent`: Verifies deterministic, reproducible scoring.

---

## Responsible AI & Ethical Governance

In strict accordance with AI DEV FEST 2026 ethical guidelines and Bangladesh Bank Mobile Financial Services regulations:

1. **Synthetic Data & Zero Real PII:**
   All 12,000 transaction records are synthetically generated using statistical distributions mirroring legitimate MFS behavior. No real NID numbers, bank cards, or biometric data are collected, processed, or stored.
2. **Local Explainable AI (SHAP TreeExplainer):**
   Every risk prediction is decomposed into exact local Shapley values ($\phi_i$). Evaluators and compliance officers can inspect the direction and magnitude of all 7 features.
3. **No Autonomous Irreversible Blocking:**
   - Low Risk (<40.0): `APPROVE` (frictionless transfer)
   - Medium Risk (40.0–74.9): `STEP_UP_2FA` (secondary OTP/biometric verification)
   - High Risk ($\ge 75.0$): `BLOCK_IMMEDIATELY` (pre-settlement halt with an immediate, self-service identity recovery pathway and helpline 16268 escalation)
   - Customer control is preserved; legitimate funds are never permanently locked out by an autonomous AI model.
4. **Deterministic ML Over LLM Hallucination:**
   Risk scoring is computed exclusively by deterministic gradient-boosted decision trees. No LLM has autonomous authority to score or block financial transactions.
