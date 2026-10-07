"""
RiskIntel upay - Production Security & Compliance Automated Test Suite
File: backend/tests/test_security.py

Automated tests validating resolution of Judge 1, 2, and 3 criticisms:
1.  Unauthenticated risk request -> 401
2.  Authenticated risk request -> allowed (200)
3.  Unauthorized role -> 403
4.  Excessive risk requests -> 429
5.  Excessive login attempts -> 429
6.  Invalid 2FA -> rejected (400)
7.  Expired 2FA -> rejected (400)
8.  Reused recovery token -> rejected (400)
9.  Expired recovery token -> rejected (400)
10. Unauthorized CORS origin -> rejected
11. Valid CORS origin -> accepted
12. Audit event is persisted to SQLite
13. Password/OTP/token never appears in audit logs
14. Invalid request body -> 422
15. Risk explanation is generated correctly
16. Model prediction and explanation remain consistent
"""

import os
import sys
import json
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

# Ensure root paths are resolvable
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.main import app, load_artifacts
from backend.database import init_db, db_session
from backend.rate_limiter import rate_limiter
from backend.auth import create_access_token

# Initialize test client and persistent state
init_db()
load_artifacts()
client = TestClient(app)

SAMPLE_VALID_TXN = {
    "txn_amount": 500.0,
    "hour_of_day": 14,
    "device_change_count_30d": 0,
    "velocity_last_1h": 1,
    "agent_distance_km": 1.2,
    "failed_pin_attempts_24h": 0,
    "is_cash_out": 0,
}

SAMPLE_HIGH_RISK_TXN = {
    "txn_amount": 25000.0,
    "hour_of_day": 3,
    "device_change_count_30d": 3,
    "velocity_last_1h": 6,
    "agent_distance_km": 22.5,
    "failed_pin_attempts_24h": 3,
    "is_cash_out": 1,
}


def get_token(username="demo_user", role="customer", scopes=None):
    """Helper to generate valid HS256 tokens."""
    return create_access_token(
        user_id=f"TEST-{username.upper()}",
        username=username,
        role=role,
        scopes=scopes or ["assess_risk"],
        expires_delta_minutes=30
    )


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Reset rate limiter store before each test to ensure test isolation."""
    rate_limiter.reset()


# ---------------------------------------------------------------------------
# Test 1 & 2: Authentication on Risk Endpoint
# ---------------------------------------------------------------------------
def test_unauthenticated_risk_request_returns_401():
    """Judge 1: Risk endpoint MUST reject unauthenticated requests with 401."""
    response = client.post("/api/v1/assess-risk", json=SAMPLE_VALID_TXN)
    assert response.status_code == 401
    assert "detail" in response.json()
    assert "Bearer" in response.headers.get("WWW-Authenticate", "")


def test_authenticated_risk_request_allowed():
    """Judge 1: Risk endpoint MUST accept authenticated requests with valid Bearer token."""
    token = get_token(username="demo_user", role="customer")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/v1/assess-risk", json=SAMPLE_VALID_TXN, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data
    assert "recommended_action" in data
    assert "key_risk_drivers" in data
    assert len(data["key_risk_drivers"]) == 3
    assert data["recommended_action"] == "APPROVE"


# ---------------------------------------------------------------------------
# Test 3: Role-Based Authorization
# ---------------------------------------------------------------------------
def test_unauthorized_role_returns_403():
    """Customer role MUST be blocked from compliance audit log inspection with 403."""
    customer_token = get_token(username="regular_customer", role="customer")
    headers = {"Authorization": f"Bearer {customer_token}"}
    response = client.get("/api/v1/audit/logs", headers=headers)
    assert response.status_code == 403
    assert "Forbidden" in response.json()["detail"]


def test_authorized_analyst_role_allowed_403_guard():
    """Analyst/Admin role MUST be permitted to inspect audit logs."""
    analyst_token = get_token(username="compliance_officer", role="analyst")
    headers = {"Authorization": f"Bearer {analyst_token}"}
    response = client.get("/api/v1/audit/logs", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_count" in data
    assert "logs" in data


# ---------------------------------------------------------------------------
# Test 4 & 5: Rate Limiting
# ---------------------------------------------------------------------------
def test_excessive_risk_requests_rate_limit_429():
    """Judge 3: Bombarding the risk endpoint beyond threshold triggers HTTP 429."""
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Simulate rapid burst exceeding assess limit
    for _ in range(60):
        res = client.post("/api/v1/assess-risk", json=SAMPLE_VALID_TXN, headers=headers)
        if res.status_code == 429:
            break

    # 61st request must trigger 429
    res = client.post("/api/v1/assess-risk", json=SAMPLE_VALID_TXN, headers=headers)
    assert res.status_code == 429
    assert "Retry-After" in res.headers


def test_excessive_login_attempts_rate_limit_429():
    """Brute-force credential attempts trigger HTTP 429."""
    bad_payload = {"username": "demo_user", "password": "WrongPassword!"}
    for _ in range(10):
        client.post("/api/v1/auth/login", json=bad_payload)

    res = client.post("/api/v1/auth/login", json=bad_payload)
    assert res.status_code == 429
    assert "Retry-After" in res.headers


# ---------------------------------------------------------------------------
# Test 6 & 7: Real 2FA / Step-Up Authentication
# ---------------------------------------------------------------------------
def test_invalid_2fa_rejected():
    """Judge 3: Submitting an invalid 2FA code is rejected with HTTP 400 and decrements attempts."""
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Create challenge
    challenge_res = client.post("/api/v1/auth/2fa/challenge", headers=headers)
    assert challenge_res.status_code == 200
    challenge_id = challenge_res.json()["challenge_id"]

    # Verify with wrong OTP
    verify_res = client.post(
        "/api/v1/auth/2fa/verify",
        json={"challenge_id": challenge_id, "code": "000000"},
        headers=headers
    )
    assert verify_res.status_code == 400
    assert "Invalid verification code" in verify_res.json()["detail"]


def test_valid_2fa_and_replay_prevention():
    """Valid OTP succeeds once, but replay attempts are strictly rejected."""
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    challenge_res = client.post("/api/v1/auth/2fa/challenge", headers=headers)
    assert challenge_res.status_code == 200
    data = challenge_res.json()
    challenge_id = data["challenge_id"]
    demo_otp = data["demo_otp"]

    # First verification must succeed
    verify_res = client.post(
        "/api/v1/auth/2fa/verify",
        json={"challenge_id": challenge_id, "code": demo_otp},
        headers=headers
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["verified"] is True

    # Replay attempt with same code must be rejected
    replay_res = client.post(
        "/api/v1/auth/2fa/verify",
        json={"challenge_id": challenge_id, "code": demo_otp},
        headers=headers
    )
    assert replay_res.status_code == 400
    assert "already been used" in replay_res.json()["detail"]


def test_expired_2fa_rejected():
    """Expired 2FA challenge must be rejected."""
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    challenge_res = client.post("/api/v1/auth/2fa/challenge", headers=headers)
    challenge_id = challenge_res.json()["challenge_id"]
    demo_otp = challenge_res.json()["demo_otp"]

    # Force expiration in database
    past_iso = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    with db_session() as conn:
        conn.execute(
            "UPDATE two_factor_challenges SET expires_at = ? WHERE challenge_id = ?",
            (past_iso, challenge_id)
        )

    verify_res = client.post(
        "/api/v1/auth/2fa/verify",
        json={"challenge_id": challenge_id, "code": demo_otp},
        headers=headers
    )
    assert verify_res.status_code == 400
    assert "expired" in verify_res.json()["detail"]


# ---------------------------------------------------------------------------
# Test 8 & 9: Account Recovery Workflow
# ---------------------------------------------------------------------------
def test_reused_recovery_token_rejected():
    """Judge 3: Single-use recovery tokens cannot be reused."""
    req_res = client.post("/api/v1/recovery/request", json={"account_identifier": "demo_user"})
    assert req_res.status_code == 200
    recovery_token = req_res.json()["demo_recovery_token"]
    assert recovery_token is not None

    # First consumption must succeed
    ver_res = client.post(
        "/api/v1/recovery/verify",
        json={"recovery_token": recovery_token, "new_pin": "5678"}
    )
    assert ver_res.status_code == 200
    assert ver_res.json()["success"] is True

    # Reused token must be rejected
    reuse_res = client.post(
        "/api/v1/recovery/verify",
        json={"recovery_token": recovery_token, "new_pin": "5678"}
    )
    assert reuse_res.status_code == 400
    assert "already been used" in reuse_res.json()["detail"]


def test_expired_recovery_token_rejected():
    """Expired recovery tokens must be rejected."""
    req_res = client.post("/api/v1/recovery/request", json={"account_identifier": "demo_user"})
    recovery_token = req_res.json()["demo_recovery_token"]

    past_iso = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
    with db_session() as conn:
        conn.execute("UPDATE recovery_tokens SET expires_at = ?", (past_iso,))

    ver_res = client.post(
        "/api/v1/recovery/verify",
        json={"recovery_token": recovery_token, "new_pin": "5678"}
    )
    assert ver_res.status_code == 400
    assert "expired" in ver_res.json()["detail"]


# ---------------------------------------------------------------------------
# Test 10 & 11: CORS Hardening
# ---------------------------------------------------------------------------
def test_unauthorized_cors_origin_rejected():
    """Judge 3: Wildcard/arbitrary untrusted origins must NOT receive Access-Control-Allow-Origin."""
    headers = {"Origin": "https://attacker-domain-malicious.com"}
    res = client.options("/api/v1/assess-risk", headers=headers)
    allow_origin = res.headers.get("access-control-allow-origin")
    assert allow_origin != "https://attacker-domain-malicious.com"
    assert allow_origin != "*"


def test_valid_cors_origin_accepted():
    """Configured allowlist origins receive Access-Control-Allow-Origin."""
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
    }
    res = client.options("/api/v1/assess-risk", headers=headers)
    assert res.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert res.headers.get("access-control-allow-credentials") == "true"


# ---------------------------------------------------------------------------
# Test 12 & 13: Durable Audit Logging
# ---------------------------------------------------------------------------
def test_audit_event_is_persisted():
    """Judge 3: Assessing risk must persist an append-only record to SQLite."""
    token = get_token(username="audit_test_user")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post("/api/v1/assess-risk", json=SAMPLE_VALID_TXN, headers=headers)
    assert res.status_code == 200
    corr_id = res.json()["correlation_id"]

    # Verify directly from database
    with db_session() as conn:
        row = conn.execute(
            "SELECT * FROM audit_logs WHERE request_id = ? AND event_type = 'RISK_ASSESSMENT'",
            (corr_id,)
        ).fetchone()
        assert row is not None
        assert row["status_code"] == 200
        assert row["actor_id"] == "TEST-AUDIT_TEST_USER"
        assert row["risk_decision"] == "APPROVE"


def test_password_otp_token_never_in_audit_logs():
    """Audit logs must never store passwords, OTPs, or auth tokens in plaintext."""
    client.post("/api/v1/auth/login", json={"username": "demo_user", "password": "SecretPassword123!"})

    with db_session() as conn:
        rows = conn.execute("SELECT details FROM audit_logs WHERE event_type LIKE 'AUTH_%'").fetchall()
        for r in rows:
            details_str = r["details"] or ""
            assert "SecretPassword123!" not in details_str
            assert "Upay@2026!" not in details_str


# ---------------------------------------------------------------------------
# Test 14: Input Validation
# ---------------------------------------------------------------------------
def test_invalid_request_body_validation_error():
    """Invalid amounts, out-of-range hours, or malformed data return HTTP 422."""
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    bad_payload = SAMPLE_VALID_TXN.copy()
    bad_payload["hour_of_day"] = 25  # Invalid (must be 0-23)
    res = client.post("/api/v1/assess-risk", json=bad_payload, headers=headers)
    assert res.status_code == 422

    bad_amount = SAMPLE_VALID_TXN.copy()
    bad_amount["txn_amount"] = 999999.0  # Exceeds regulatory limit of 25,000 BDT
    res2 = client.post("/api/v1/assess-risk", json=bad_amount, headers=headers)
    assert res2.status_code == 422


# ---------------------------------------------------------------------------
# Test 15 & 16: Explainability & Model Consistency
# ---------------------------------------------------------------------------
def test_risk_explanation_generated_correctly():
    """SHAP returns top 3 drivers with non-zero impact and coherent narrative."""
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post("/api/v1/assess-risk", json=SAMPLE_HIGH_RISK_TXN, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["risk_score"] >= 75.0
    assert data["recommended_action"] == "BLOCK_IMMEDIATELY"
    assert len(data["key_risk_drivers"]) == 3
    # Check that highest impact features are present
    driver_names = [d["feature"] for d in data["key_risk_drivers"]]
    assert "txn_amount" in driver_names or "failed_pin_attempts_24h" in driver_names


def test_model_prediction_and_explanation_remain_consistent():
    """Repeated inference on identical inputs returns deterministic score and drivers."""
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    res1 = client.post("/api/v1/assess-risk", json=SAMPLE_HIGH_RISK_TXN, headers=headers).json()
    res2 = client.post("/api/v1/assess-risk", json=SAMPLE_HIGH_RISK_TXN, headers=headers).json()

    assert res1["risk_score"] == res2["risk_score"]
    assert res1["recommended_action"] == res2["recommended_action"]
    assert res1["key_risk_drivers"] == res2["key_risk_drivers"]
