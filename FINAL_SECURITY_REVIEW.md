# RiskIntel upay — Final Security Review & Verification Report

**Event:** AI DEV FEST 2026 — Track 01: Trust & Risk Intelligence  
**Date:** October 2026  
**Auditor:** Senior AI/ML + Cybersecurity Engineer & Production Full-Stack Developer  
**Status:** Verification Complete — 18/18 Automated Security Tests Passing

---

## 1. Summary of Changes & Problem Resolution

An end-to-end security remediation was implemented across the RiskIntel upay codebase, resolving every judge feedback point without fabricating capabilities or introducing fake UI badges:

1. **Authentication on Risk Endpoint (Judge 1):**  
   - Implemented standard JWT (HS256) Bearer token authentication in `backend/auth.py`.
   - Protected `POST /api/v1/assess-risk` via dependency injection (`get_current_user`). Unauthenticated calls return `HTTP 401 Unauthorized` with `WWW-Authenticate: Bearer`.
   - Derives caller identity from the server-validated token rather than client-supplied inputs.
2. **Server-Side Rate Limiting (Judge 3):**  
   - Built a sliding-window rate limiter in `backend/rate_limiter.py` protecting login, 2FA, recovery, and risk scoring.
   - Enforces configurable limits via environment variables and returns `HTTP 429 Too Many Requests` with `Retry-After`.
3. **Hardened CORS (Judge 3):**  
   - Eliminated wildcard `*` origins on authenticated endpoints.
   - Enforced strict origin allowlist from `ALLOWED_ORIGINS` environment variable in `backend/config.py`.
4. **Real 2FA & Step-Up Authentication (Judges 2 & 3):**  
   - Replaced client-side simulated `setTimeout()` with cryptographic server-side challenge issuance (`backend/two_factor.py`).
   - Generates 6-digit CSPRNG OTP, unique salt, and stores salted SHA-256 hashes in SQLite with 5-minute TTL.
   - Enforces 3-attempt maximum, replay prevention (`verified = 1`), and issues single-use emergency backup recovery codes.
5. **Real Account Recovery Workflow (Judges 2 & 3):**  
   - Implemented server-side recovery token issuance (`backend/recovery.py`) with 15-minute TTL.
   - Integrated anti-enumeration defenses (constant generic response).
   - Enforces atomic token consumption to prevent token reuse.
6. **Durable Persistent Audit Logging (Judge 3):**  
   - Implemented SQLite Write-Ahead Logging (WAL) persistent storage in `backend/database.py`.
   - Appends immutable audit records with timestamp, correlation request ID, event type, actor ID, status code, risk score, decision action, model version, and top SHAP drivers.
   - Integrated automated credential sanitizer guaranteeing zero passwords, OTPs, or auth keys in database.
   - Provided authorized query API (`GET /api/v1/audit/logs`) restricted to `analyst` and `admin` roles (returns 403 otherwise).
7. **Rigorous Fraud Model Validation (Judge 2):**  
   - Upgraded `backend/train_pipeline.py` with clean 3-way stratified partition: 70% Train, 15% Validation, 15% Pristine Test.
   - Evaluated on clean test set: **ROC-AUC = 0.9780**, **PR-AUC = 0.8247**, Confusion Matrix (TN=1567, FP=73, FN=21, TP=139).
   - Conducted full threshold sweep ($\tau \in [0.20, 0.90]$) analyzing False Positive Rate (customer friction) vs. False Negative Rate (fraud loss).
   - Published `models/model_metrics.json` and `MODEL_VALIDATION_REPORT.md`.
8. **Defensive HTTP Security Headers:**  
   - Implemented ASGI middleware in `backend/security_headers.py` injecting `nosniff`, `DENY`, `strict-origin-when-cross-origin`, and CSP.
9. **Transparent UI & Live Security Status (Judge Feedback):**  
   - Connected `frontend/app/page.tsx` to real backend endpoints: automatic demo JWT authentication, real 2FA challenge/verification, real recovery token verification.
   - Added live Security & Production Controls Status Panel querying `/api/v1/security/status`.
   - Added interactive Responsible Risk Decision Pipeline visualizer.

---

## 2. Inventory of Modified & Created Files

### Modified Files:
- [`backend/main.py`](file:///d:/riskintel-upay/backend/main.py) — Integrated authentication, CORS allowlist, rate limiting, security headers, 2FA/recovery routes, audit logging, and security status endpoint.
- [`backend/train_pipeline.py`](file:///d:/riskintel-upay/backend/train_pipeline.py) — 3-way stratified split, PR-AUC, confusion matrix, threshold sweep, and metrics export.
- [`frontend/app/page.tsx`](file:///d:/riskintel-upay/frontend/app/page.tsx) — Real backend JWT authentication, real 2FA challenge/verify, real recovery API, security status panel, and decision flow visualizer.
- [`README.md`](file:///d:/riskintel-upay/README.md) — Comprehensive technical architecture, installation guide, security documentation, and model validation summary.

### Newly Created Files:
- [`backend/config.py`](file:///d:/riskintel-upay/backend/config.py) — Environment variables loader, secrets management, CORS allowlist, rate limit configuration.
- [`backend/.env.example`](file:///d:/riskintel-upay/backend/.env.example) — Production environment variable template.
- [`backend/database.py`](file:///d:/riskintel-upay/backend/database.py) — Durable SQLite schema with Write-Ahead Logging (WAL).
- [`backend/auth.py`](file:///d:/riskintel-upay/backend/auth.py) — Cryptographic JWT engine, PBKDF2-HMAC-SHA256 password hashing, RBAC guards.
- [`backend/rate_limiter.py`](file:///d:/riskintel-upay/backend/rate_limiter.py) — Sliding-window rate limiting with HTTP 429 and Retry-After.
- [`backend/two_factor.py`](file:///d:/riskintel-upay/backend/two_factor.py) — Cryptographic 2FA challenge, salted SHA-256 hashing, replay prevention.
- [`backend/recovery.py`](file:///d:/riskintel-upay/backend/recovery.py) — Single-use account recovery tokens with anti-enumeration protection.
- [`backend/audit.py`](file:///d:/riskintel-upay/backend/audit.py) — Append-only audit logger, zero-PII sanitizer, authorized query API.
- [`backend/security_headers.py`](file:///d:/riskintel-upay/backend/security_headers.py) — Starlette ASGI security headers middleware.
- [`backend/tests/test_security.py`](file:///d:/riskintel-upay/backend/tests/test_security.py) — Automated test suite covering 18 test cases.
- [`models/model_metrics.json`](file:///d:/riskintel-upay/models/model_metrics.json) — Machine-readable evaluation metrics artifact.
- [`SECURITY_GAP_REPORT.md`](file:///d:/riskintel-upay/SECURITY_GAP_REPORT.md) — Initial codebase security audit.
- [`MODEL_VALIDATION_REPORT.md`](file:///d:/riskintel-upay/MODEL_VALIDATION_REPORT.md) — Comprehensive machine learning validation report.
- [`JUDGE_FEEDBACK_RESPONSE.md`](file:///d:/riskintel-upay/JUDGE_FEEDBACK_RESPONSE.md) — Point-by-point response to judge feedback with evidence.
- [`FINAL_SECURITY_REVIEW.md`](file:///d:/riskintel-upay/FINAL_SECURITY_REVIEW.md) — This final review and verification report.

---

## 3. Automated Test Execution Results

**Test Runner:** `pytest backend/tests/test_security.py -v`  
**Execution Environment:** Windows Python 3.14.4 virtual environment  
**Execution Timestamp:** October 2026  
**Result:** **18 Passed, 0 Failed (100% Pass Rate)**

| # | Test Name | Target Requirement | Status |
| :---: | :--- | :--- | :---: |
| 1 | `test_unauthenticated_risk_request_returns_401` | Risk endpoint rejects unauthenticated request with 401 | **PASSED** |
| 2 | `test_authenticated_risk_request_allowed` | Authenticated request with Bearer JWT returns 200 OK | **PASSED** |
| 3 | `test_unauthorized_role_returns_403` | Unauthorized role (customer) blocked from audit logs with 403 | **PASSED** |
| 4 | `test_authorized_analyst_role_allowed_403_guard` | Authorized analyst role permitted to inspect audit logs | **PASSED** |
| 5 | `test_excessive_risk_requests_rate_limit_429` | Exceeding 60 req/min on risk endpoint returns 429 & Retry-After | **PASSED** |
| 6 | `test_excessive_login_attempts_rate_limit_429` | Brute force login attempts return 429 & Retry-After | **PASSED** |
| 7 | `test_invalid_2fa_rejected` | Submitting invalid OTP returns 400 Bad Request | **PASSED** |
| 8 | `test_valid_2fa_and_replay_prevention` | Valid OTP succeeds; replay attempt strictly rejected | **PASSED** |
| 9 | `test_expired_2fa_rejected` | Expired 2FA challenge is rejected | **PASSED** |
| 10 | `test_reused_recovery_token_rejected` | Single-use recovery token cannot be reused | **PASSED** |
| 11 | `test_expired_recovery_token_rejected` | Expired recovery token is rejected | **PASSED** |
| 12 | `test_unauthorized_cors_origin_rejected` | Untrusted origin denied CORS header | **PASSED** |
| 13 | `test_valid_cors_origin_accepted` | Whitelisted origin receives CORS allow header | **PASSED** |
| 14 | `test_audit_event_is_persisted` | Assessment event persisted to SQLite audit_logs table | **PASSED** |
| 15 | `test_password_otp_token_never_in_audit_logs` | Passwords, OTPs, and tokens scrubbed from audit details | **PASSED** |
| 16 | `test_invalid_request_body_validation_error` | Out-of-bounds amount (>৳25k) or hour returns 422 | **PASSED** |
| 17 | `test_risk_explanation_generated_correctly` | Top 3 SHAP drivers and narrative generated accurately | **PASSED** |
| 18 | `test_model_prediction_and_explanation_remain_consistent`| Identical payloads return deterministic score and explanation | **PASSED** |

---

## 4. Known Limitations & Remaining Production Risks

1. **In-Memory Rate Limiting Scope:**  
   The current rate limiter uses an in-memory sliding window. While thread-safe and optimal for single-instance containers, multi-instance horizontal scaling requires configuring a shared Redis instance. The codebase is architected with a modular interface allowing clean substitution with `redis-py`.
2. **Synthetic Data Domain Gap:**  
   While synthetic transactions mirror realistic statistical distributions (exponential amounts, Poisson velocity, midnight clustering), real MFS traffic contains unpredictable macroeconomic anomalies (e.g. Eid festivals, national holidays, banking downtime).
3. **Single-Node SQLite Storage:**  
   SQLite with WAL mode provides durability, atomic transactions, and high read concurrency for hackathon demonstration. A production banking cluster processing 150M daily transactions requires a distributed relational database (e.g., PostgreSQL with partitioning and WORM compliance).

---

## 5. Future Validation & Deployment Requirements

1. **Dark/Shadow-Mode Pilot:** Run the LightGBM scoring engine in shadow mode alongside upay's existing rules engine for 30–60 days without affecting live fund execution.
2. **Chargeback Benchmarking:** Compare false positives and false negatives against confirmed fraud chargebacks and police/BFIU reports.
3. **Population Stability Index (PSI):** Establish automated drift monitoring to trigger model retraining when feature drift exceeds 0.25.
4. **Hardware Security Module (HSM):** Transition JWT and token signing keys to bank-grade Cloud HSM / KMS.
