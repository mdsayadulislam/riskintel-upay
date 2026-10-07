# RiskIntel upay — Security Gap Report & Architecture Audit

**Project:** RiskIntel upay (AI DEV FEST 2026 — Track 01: Trust & Risk Intelligence)  
**Date:** October 2026  
**Auditor:** Senior AI/ML + Cybersecurity Engineer & Full-Stack Architect  
**Evaluation Context:** Addressing official Judge Feedback (Judges 1, 2, and 3).

---

## Executive Summary

An exhaustive technical audit was conducted across the frontend (Next.js 14), backend (FastAPI), machine learning pipeline (LightGBM + SHAP), data layer, and network configuration. The codebase has strong human/customer safety foundations (synthetic data, no real PII, SHAP local explainability, step-up 2FA design), but exhibits critical gaps in production security, persistent controls, and rigorous ML validation that directly substantiate the judges' feedback:

1. **Judge 1:** *"No authentication on the risk endpoint"* — Confirmed. `/api/v1/assess-risk` accepts unauthenticated POST requests from any client.
2. **Judge 2:** *"Real-world security and fraud-model validation remain outstanding"* — Confirmed. 2FA and recovery flows are simulated in client JavaScript; model validation lacks threshold analysis (FPR vs. FNR tradeoffs), PR-AUC, and confusion matrix auditing.
3. **Judge 3:** *"Production security is weak because the API lacks authentication/rate limiting, CORS is permissive, recovery/2FA are simulated, and the claimed audit/compliance controls are not implemented as durable backend controls"* — Confirmed. CORS allows `*` with credentials enabled, rate limiting does not exist, and audit logs are ephemeral console printouts rather than durable database records.

---

## Detailed Gap Analysis

### Gap 1: Unauthenticated Fraud / Risk Scoring Endpoint

- **Current Problem:** The risk evaluation endpoint (`POST /api/v1/assess-risk`) is completely public without authentication or identity validation.
- **Risk:** Malicious actors or unauthorized clients can bombard the inference engine, scrape the proprietary LightGBM model decisions and SHAP attribution vectors, reverse-engineer risk thresholds, or exhaust compute resources.
- **Existing Implementation:** `backend/main.py` defines `assess_risk(txn: TransactionPayload)` without any FastAPI `Security`, `Depends`, or Bearer token checks.
- **Missing Implementation:** Short-lived JWT/token authentication, role-based authorization (e.g., `analyst`, `service_agent`, `customer`), server-side identity resolution (deriving caller identity rather than trusting client-supplied identifiers), and returning `401 Unauthorized` / `403 Forbidden`.
- **Proposed Fix:**
  - Implement a cryptographic authentication service with JWT token verification (HS256).
  - Add auth dependency injection to `/api/v1/assess-risk` and sensitive endpoints.
  - Provide synthetic/demo test accounts with clear role distinctions (`user`, `analyst`, `admin`).
- **Files That Need Modification:** `backend/main.py`, `backend/auth.py` (new), `frontend/app/page.tsx`.

---

### Gap 2: Missing Server-Side Rate Limiting

- **Current Problem:** There is zero rate limiting on the API gateway.
- **Risk:** Brute-force attacks against authentication, OTP spamming, credential stuffing, and Denial of Service (DoS) against compute-heavy ML/SHAP inference.
- **Existing Implementation:** None. Requests are processed synchronously as received.
- **Missing Implementation:** Configurable rate limiting middleware enforcing per-IP and per-token sliding-window limits, returning `HTTP 429 Too Many Requests` with a `Retry-After` header.
- **Proposed Fix:**
  - Implement high-performance in-memory sliding-window token bucket rate limiter (production-ready for single-instance, swappable for Redis in multi-instance clusters).
  - Configure route-specific thresholds via environment variables (`RATE_LIMIT_ASSESS_PER_MIN`, `RATE_LIMIT_AUTH_PER_MIN`, etc.).
- **Files That Need Modification:** `backend/main.py`, `backend/rate_limiter.py` (new), `backend/.env.example` (new).

---

### Gap 3: Permissive CORS Configuration

- **Current Problem:** `backend/main.py` configures `CORSMiddleware` with `allow_origins=["*"]` and `allow_credentials=True`.
- **Risk:** Allowing wildcard origins with credentials violates browser security specifications and exposes authenticated sessions to cross-site request forgery (CSRF) and credential exfiltration.
- **Existing Implementation:**
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```
- **Missing Implementation:** Origin allowlist parsed strictly from environment variables (`ALLOWED_ORIGINS`), blocking arbitrary origins while permitting development localhost and configured production domains.
- **Proposed Fix:**
  - Parse `ALLOWED_ORIGINS` environment variable into an explicit list.
  - Reject unauthorized origins with appropriate CORS headers.
  - Document production domain configuration.
- **Files That Need Modification:** `backend/main.py`, `backend/config.py` (new), `backend/.env.example`.

---

### Gap 4: Simulated 2FA / Step-Up Authentication

- **Current Problem:** Step-up 2FA is purely a frontend UI simulation with hardcoded OTP (`841920`) and `setTimeout()` client-side delay.
- **Risk:** Attackers can bypass step-up authentication simply by modifying frontend state or issuing direct API calls. No real security challenge is executed.
- **Existing Implementation:** `frontend/app/page.tsx` line 888–895 uses `setVerifyingOtp(true)` followed by client-side timeout to mark `otpVerified = true`.
- **Missing Implementation:**
  - Server-side challenge issuance (`POST /api/v1/auth/2fa/challenge`).
  - Secure time-bound OTP generation (cryptographically secure pseudorandom numbers or TOTP).
  - Secure hashing of OTP secrets (never plaintext in DB).
  - Attempt rate limiting and replay prevention.
  - Server-side verification endpoint (`POST /api/v1/auth/2fa/verify`).
  - Single-use emergency recovery codes.
- **Proposed Fix:**
  - Build backend 2FA management module with challenge generation, SHA-256 OTP hashing with salt, 5-minute TTL, maximum 3 verification attempts, and single-use emergency backup codes.
  - Integrate frontend modal to submit real verification calls to backend.
- **Files That Need Modification:** `backend/main.py`, `backend/two_factor.py` (new), `frontend/app/page.tsx`.

---

### Gap 5: Simulated Account Recovery Workflow

- **Current Problem:** Account unblocking/recovery in `frontend/app/page.tsx` is completely simulated using hardcoded code `123456` and `setTimeout()`.
- **Risk:** Account lockout recovery lacks server-side authorization and auditability. Malicious actors could exploit client-side unblocking to reset security locks.
- **Existing Implementation:** `frontend/app/page.tsx` lines 898–906 simulates identity unblock and resets `failed_pin_attempts_24h: 0`.
- **Missing Implementation:**
  - Real backend recovery token generation with expiration.
  - One-time consumption enforcement.
  - Protection against account enumeration.
  - Secure session invalidation and lockout clearance on the backend.
- **Proposed Fix:**
  - Implement `/api/v1/recovery/request` and `/api/v1/recovery/verify` endpoints.
  - Issue cryptographically secure single-use recovery tokens with 15-minute expiration.
  - Enforce atomic consumption to prevent token reuse.
- **Files That Need Modification:** `backend/main.py`, `backend/recovery.py` (new), `frontend/app/page.tsx`.

---

### Gap 6: Claimed Audit / Compliance Controls Not Durable

- **Current Problem:** The project claims regulatory audit compliance with Bangladesh Bank MFS guidelines, but audit logs are merely transient `logger.info()` console statements.
- **Risk:** In an actual incident or regulatory audit, zero durable evidence exists. Tampering cannot be detected, and historical risk assessments cannot be reconstructed.
- **Existing Implementation:** Python standard library `logging.getLogger("riskintel.api")` logging to console stdout.
- **Missing Implementation:**
  - Persistent, append-only audit database schema.
  - Recording actor ID, correlation/request ID, timestamp, endpoint, decision, risk score, model version, and SHAP top drivers.
  - Zero PII / zero secret logging guarantee (passwords, tokens, and raw OTPs excluded).
  - Authorized audit query API (`GET /api/v1/audit/logs`) with role protection.
- **Proposed Fix:**
  - Implement SQLite/SQLAlchemy durable audit log storage with append-only semantics.
  - Create structured audit record schema.
  - Expose authenticated inspection endpoint for auditors/security analysts.
- **Files That Need Modification:** `backend/main.py`, `backend/audit.py` (new), `backend/database.py` (new).

---

### Gap 7: Fraud / Risk ML Model Validation Deficiencies

- **Current Problem:** `backend/train_pipeline.py` prints a basic classification report and ROC-AUC on a 20% test split, then refits on all 12,000 samples without generating durable evaluation artifacts, threshold analysis, PR-AUC, or confusion matrices.
- **Risk:** Overstating model reliability without empirical threshold justification or awareness of the false positive vs. false negative trade-off in financial fraud.
- **Existing Implementation:** Basic `train_test_split` with standard classification report.
- **Missing Implementation:**
  - Precision-Recall AUC (PR-AUC) which is crucial for imbalanced fraud data.
  - Explicit threshold sweep across candidate cutoffs (e.g. 0.30, 0.40, 0.50, 0.70, 0.75).
  - False Positive Rate (FPR) vs. False Negative Rate (FNR) tradeoff documentation.
  - Exported confusion matrix and validation artifact.
  - Formal `MODEL_VALIDATION_REPORT.md` documenting synthetic data origin, limitations, data drift, and production testing protocol.
- **Proposed Fix:**
  - Enhance `train_pipeline.py` with comprehensive threshold analysis, confusion matrices, PR-AUC, and calibration curves.
  - Generate comprehensive `MODEL_VALIDATION_REPORT.md`.
- **Files That Need Modification:** `backend/train_pipeline.py`, `MODEL_VALIDATION_REPORT.md` (new).

---

### Gap 8: Missing Production Security Headers

- **Current Problem:** FastAPI application does not emit standard HTTP security headers.
- **Risk:** Susceptibility to clickjacking, MIME-type sniffing, cross-site scripting (XSS), and data leakage.
- **Existing Implementation:** None.
- **Missing Implementation:**
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Content-Security-Policy` appropriate for API endpoints
  - `Strict-Transport-Security` for HTTPS
- **Proposed Fix:**
  - Add ASGI security headers middleware to FastAPI.
- **Files That Need Modification:** `backend/main.py`, `backend/security_headers.py` (new).

---

### Gap 9: Lack of Unified Environment Configuration & Secrets Management

- **Current Problem:** Secrets (JWT keys, allowed origins, rate limits) are either hardcoded or missing from environment configuration.
- **Risk:** Compromise of production secrets if checked into source control or run with default settings.
- **Existing Implementation:** No `.env` or `.env.example` in backend; hardcoded paths in `main.py`.
- **Missing Implementation:**
  - Pydantic `BaseSettings` or python-dotenv configuration loader.
  - `backend/.env.example` with clear documentation.
- **Proposed Fix:**
  - Create `backend/config.py` loading all secrets, CORS domains, rate limits, and model paths from environment variables.
  - Provide complete `.env.example`.
- **Files That Need Modification:** `backend/config.py` (new), `backend/.env.example` (new), `backend/main.py`.

---

## Action Plan & Remediation Roadmap

| Step | Objective | Module / Artifact | Target Result |
| :--- | :--- | :--- | :--- |
| **1** | Audit Documentation | `SECURITY_GAP_REPORT.md` | Formal baseline audit addressing Judge 1, 2, 3 |
| **2** | Backend Auth & RBAC | `backend/auth.py` | JWT authentication + 401/403 guards on risk scoring |
| **3** | Rate Limiting | `backend/rate_limiter.py` | Sliding-window limiter with 429 & Retry-After |
| **4** | Hardened CORS | `backend/config.py` | Strict allowlist, credentials validation |
| **5** | Real 2FA / Step-Up | `backend/two_factor.py` | Cryptographic OTP, salt-hashing, 5m TTL, recovery codes |
| **6** | Durable Recovery | `backend/recovery.py` | One-time recovery tokens, no account enumeration |
| **7** | Persistent Audit Log | `backend/audit.py`, `database.py` | SQLite/SQLAlchemy append-only audit trail + query API |
| **8** | ML Validation Pipeline | `backend/train_pipeline.py` | PR-AUC, threshold sweep, confusion matrix |
| **9** | Model Validation Doc | `MODEL_VALIDATION_REPORT.md` | Honest analysis of synthetic data vs. real-world MFS |
| **10** | Security Headers & Input | `backend/security_headers.py` | Nosniff, frame-ancestors, CSP, strict validation |
| **11** | Automated Security Tests | `backend/tests/test_security.py` | 16+ automated unit & integration security tests |
| **12** | Frontend Security Integration | `frontend/app/page.tsx` | Real auth token, real 2FA challenge, security status banner |
| **13** | Documentation Updates | `README.md`, `JUDGE_FEEDBACK_RESPONSE.md` | Complete alignment with hackathon criteria |
| **14** | Final Verification | `FINAL_SECURITY_REVIEW.md` | Verification of all passing tests and demo runbook |

