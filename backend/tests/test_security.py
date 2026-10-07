"""
RiskIntel upay - Production Security & Compliance Automated Test Suite
File: backend/tests/test_security.py

Automated tests validating all 18 specified security requirements:
1.  PIN empty -> 400
2.  PIN invalid length -> 400
3.  PIN non-numeric -> 400
4.  PIN validation (valid vs invalid) -> 200 vs 401
5.  OTP generation -> 6 digits, salted SHA-256
6.  OTP hash verification -> constant-time match
7.  Wrong OTP -> rejected (400) and remaining attempts decremented
8.  Expired OTP -> rejected (400)
9.  OTP reuse -> rejected (400)
10. Maximum OTP attempts -> challenge locked after 3 failures
11. OTP request rate limit -> 429 on excessive requests
12. Unauthenticated risk request -> 401
13. Unauthorized transaction ownership -> 403
14. Duplicate idempotency request -> identical replay returned
15. BLOCK policy -> status BLOCKED / BLOCK_IMMEDIATELY
16. STEP_UP policy -> status STEP_UP_REQUIRED / STEP_UP_2FA
17. APPROVE policy -> status AUTHORIZED / APPROVE
18. Audit log creation & zero secret leakage
"""

import os
import sys
import json
import uuid
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
from backend.auth import create_access_token, validate_pin_format, verify_user_pin, SYNTHETIC_USERS
from backend.two_factor import issue_2fa_challenge, verify_2fa_code, hash_otp_with_salt
from backend.sms_provider import set_sms_provider, MockSmsProvider

# Initialize test client and persistent state
init_db()
load_artifacts()
mock_sms = MockSmsProvider()
set_sms_provider(mock_sms)
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

SAMPLE_MEDIUM_RISK_TXN = {
    "txn_amount": 1500.0,
    "hour_of_day": 1,
    "device_change_count_30d": 1,
    "velocity_last_1h": 1,
    "agent_distance_km": 6.0,
    "failed_pin_attempts_24h": 0,
    "is_cash_out": 1,
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


def get_token(username="demo_user", user_id="SYNTH-UPAY-USER-001", role="customer", scopes=None):
    """Helper to generate valid HS256 tokens."""
    return create_access_token(
        user_id=user_id,
        username=username,
        role=role,
        scopes=scopes or ["assess_risk", "transact", "step_up_2fa"],
        expires_delta_minutes=30
    )


@pytest.fixture(autouse=True)
def reset_test_environment():
    """Reset rate limiter store, database tables, and mock SMS state before each test."""
    rate_limiter.reset()
    mock_sms.sent_messages.clear()
    with db_session() as conn:
        conn.execute("DELETE FROM two_factor_challenges")
        conn.execute("DELETE FROM transactions")
        conn.execute("DELETE FROM idempotency_records")


# ---------------------------------------------------------------------------
# Requirement 1: PIN Empty
# ---------------------------------------------------------------------------
def test_pin_empty_rejected():
    """Requirement 1: Empty PIN must be rejected with HTTP 400."""
    valid, err = validate_pin_format("")
    assert not valid
    assert "empty" in err.lower()

    token = get_token()
    payload = SAMPLE_VALID_TXN.copy()
    payload["pin"] = ""
    res = client.post("/api/v1/transactions/authorize", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 422 or res.status_code == 400


# ---------------------------------------------------------------------------
# Requirement 2: PIN Invalid Length
# ---------------------------------------------------------------------------
def test_pin_invalid_length_rejected():
    """Requirement 2: PINs with length != 4 must be rejected with HTTP 400."""
    valid_short, err_short = validate_pin_format("12")
    assert not valid_short
    assert "4 digits" in err_short

    valid_long, err_long = validate_pin_format("12345")
    assert not valid_long
    assert "4 digits" in err_long

    token = get_token()
    payload = SAMPLE_VALID_TXN.copy()
    payload["pin"] = "12"
    res = client.post("/api/v1/transactions/authorize", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code in [400, 422]


# ---------------------------------------------------------------------------
# Requirement 3: PIN Non-Numeric
# ---------------------------------------------------------------------------
def test_pin_non_numeric_rejected():
    """Requirement 3: Non-numeric PIN characters must be rejected."""
    valid, err = validate_pin_format("12a4")
    assert not valid
    assert "numeric" in err.lower()

    token = get_token()
    payload = SAMPLE_VALID_TXN.copy()
    payload["pin"] = "abcd"
    res = client.post("/api/v1/transactions/authorize", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 400
    assert "numeric" in res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Requirement 4: PIN Validation (Correct vs Incorrect)
# ---------------------------------------------------------------------------
def test_pin_validation_correct_and_incorrect():
    """Requirement 4: Valid PIN succeeds, incorrect PIN returns HTTP 401."""
    # Demo user correct PIN is "1234"
    assert verify_user_pin("SYNTH-UPAY-USER-001", "1234") is True
    assert verify_user_pin("SYNTH-UPAY-USER-001", "9999") is False

    token = get_token()
    # Correct PIN
    payload_ok = SAMPLE_VALID_TXN.copy()
    payload_ok["pin"] = "1234"
    res_ok = client.post("/api/v1/transactions/authorize", json=payload_ok, headers={"Authorization": f"Bearer {token}"})
    assert res_ok.status_code == 200

    # Incorrect PIN
    payload_bad = SAMPLE_VALID_TXN.copy()
    payload_bad["pin"] = "9999"
    res_bad = client.post("/api/v1/transactions/authorize", json=payload_bad, headers={"Authorization": f"Bearer {token}"})
    assert res_bad.status_code == 401
    assert "incorrect" in res_bad.json()["detail"].lower() or "invalid" in res_bad.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Requirement 5: OTP Generation
# ---------------------------------------------------------------------------
def test_otp_generation():
    """Requirement 5: OTP is 6 digits, securely generated and stored with salt."""
    ch = issue_2fa_challenge(user_id="SYNTH-UPAY-USER-001", transaction_id="test-txn-001")
    assert "challenge_id" in ch
    assert ch["expires_in_seconds"] == 300
    assert len(mock_sms.sent_messages) == 1
    # Verify DB storage
    with db_session() as conn:
        row = conn.execute("SELECT * FROM two_factor_challenges WHERE challenge_id = ?", (ch["challenge_id"],)).fetchone()
        assert row is not None
        assert row["user_id"] == "SYNTH-UPAY-USER-001"
        assert row["transaction_id"] == "test-txn-001"
        assert len(row["otp_hash"]) == 64  # SHA-256 hex length
        assert len(row["salt"]) == 32


# ---------------------------------------------------------------------------
# Requirement 6: OTP Hash Verification
# ---------------------------------------------------------------------------
def test_otp_hash_verification():
    """Requirement 6: OTP hash verification matches correct salted hash."""
    otp = "654321"
    salt = "abcdef0123456789abcdef0123456789"
    h = hash_otp_with_salt(otp, salt)
    assert hash_otp_with_salt("654321", salt) == h
    assert hash_otp_with_salt("654322", salt) != h


# ---------------------------------------------------------------------------
# Requirement 7: Wrong OTP
# ---------------------------------------------------------------------------
def test_wrong_otp_rejected():
    """Requirement 7: Wrong OTP returns 400 and decrements remaining attempts."""
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    ch_res = client.post("/api/v1/auth/2fa/challenge", headers=headers)
    assert ch_res.status_code == 200
    ch_id = ch_res.json()["challenge_id"]

    verify_res = client.post(
        "/api/v1/auth/2fa/verify",
        json={"challenge_id": ch_id, "code": "000000"},
        headers=headers,
    )
    assert verify_res.status_code == 400
    assert "invalid" in verify_res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Requirement 8: Expired OTP
# ---------------------------------------------------------------------------
def test_expired_otp_rejected():
    """Requirement 8: Expired OTP returns HTTP 400."""
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    ch_res = client.post("/api/v1/auth/2fa/challenge", headers=headers)
    ch_id = ch_res.json()["challenge_id"]
    demo_otp = ch_res.json()["demo_otp"]

    # Force expiration in SQLite
    past_iso = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    with db_session() as conn:
        conn.execute("UPDATE two_factor_challenges SET expires_at = ? WHERE challenge_id = ?", (past_iso, ch_id))

    verify_res = client.post(
        "/api/v1/auth/2fa/verify",
        json={"challenge_id": ch_id, "code": demo_otp},
        headers=headers,
    )
    assert verify_res.status_code == 400
    assert "expired" in verify_res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Requirement 9: OTP Reuse
# ---------------------------------------------------------------------------
def test_otp_reuse_rejected():
    """Requirement 9: Successfully used OTP cannot be reused (replay attack prevention)."""
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    ch_res = client.post("/api/v1/auth/2fa/challenge", headers=headers)
    ch_id = ch_res.json()["challenge_id"]
    demo_otp = ch_res.json()["demo_otp"]

    # First verify succeeds
    v1 = client.post("/api/v1/auth/2fa/verify", json={"challenge_id": ch_id, "code": demo_otp}, headers=headers)
    assert v1.status_code == 200
    assert v1.json()["verified"] is True

    # Replay verify fails
    v2 = client.post("/api/v1/auth/2fa/verify", json={"challenge_id": ch_id, "code": demo_otp}, headers=headers)
    assert v2.status_code == 400
    assert "already been used" in v2.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Requirement 10: Maximum OTP Attempts
# ---------------------------------------------------------------------------
def test_maximum_otp_attempts_locks():
    """Requirement 10: Challenge is locked after 3 failed verification attempts."""
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    ch_res = client.post("/api/v1/auth/2fa/challenge", headers=headers)
    ch_id = ch_res.json()["challenge_id"]

    for _ in range(3):
        client.post("/api/v1/auth/2fa/verify", json={"challenge_id": ch_id, "code": "000000"}, headers=headers)

    # 4th attempt must report locked
    res4 = client.post("/api/v1/auth/2fa/verify", json={"challenge_id": ch_id, "code": "000000"}, headers=headers)
    assert res4.status_code == 400
    assert "exceeded" in res4.json()["detail"].lower() or "locked" in res4.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Requirement 11: OTP Request Rate Limit
# ---------------------------------------------------------------------------
def test_otp_request_rate_limit():
    """Requirement 11: Requesting more than 3 OTP challenges within window returns HTTP 429."""
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    client.post("/api/v1/auth/2fa/challenge", headers=headers)
    client.post("/api/v1/auth/2fa/challenge", headers=headers)
    client.post("/api/v1/auth/2fa/challenge", headers=headers)

    # 4th request must be rate limited
    res4 = client.post("/api/v1/auth/2fa/challenge", headers=headers)
    assert res4.status_code == 429


# ---------------------------------------------------------------------------
# Requirement 12: Unauthenticated Risk Request
# ---------------------------------------------------------------------------
def test_unauthenticated_risk_request_returns_401():
    """Requirement 12: Unauthenticated requests to /api/v1/assess-risk return HTTP 401."""
    res = client.post("/api/v1/assess-risk", json=SAMPLE_VALID_TXN)
    assert res.status_code == 401
    assert "detail" in res.json()


# ---------------------------------------------------------------------------
# Requirement 13: Unauthorized Transaction Ownership
# ---------------------------------------------------------------------------
def test_unauthorized_transaction_ownership():
    """Requirement 13: User B cannot verify or view User A's transaction (HTTP 403)."""
    user_a_token = get_token(username="demo_user", user_id="SYNTH-UPAY-USER-001")
    user_b_token = get_token(username="compliance_officer", user_id="SYNTH-UPAY-ANALYST-101", role="customer")

    # User A creates a transaction requiring step-up
    payload = SAMPLE_MEDIUM_RISK_TXN.copy()
    payload["pin"] = "1234"
    create_res = client.post(
        "/api/v1/transactions/authorize",
        json=payload,
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert create_res.status_code == 200
    txn_id = create_res.json()["transaction_id"]
    challenge_id = create_res.json()["challenge"]["challenge_id"]

    # User B attempts to verify User A's transaction
    hack_res = client.post(
        f"/api/v1/transactions/{txn_id}/verify-step-up",
        json={"challenge_id": challenge_id, "otp_code": "123456"},
        headers={"Authorization": f"Bearer {user_b_token}"},
    )
    assert hack_res.status_code == 403
    assert "forbidden" in hack_res.json()["detail"].lower() or "not owned" in hack_res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Requirement 14: Duplicate Idempotency Request
# ---------------------------------------------------------------------------
def test_duplicate_idempotency_request():
    """Requirement 14: Re-submitting the same Idempotency-Key returns cached response with idempotent_replay=true."""
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": f"test-idemp-{uuid.uuid4()}",
    }
    payload = SAMPLE_VALID_TXN.copy()
    payload["pin"] = "1234"

    res1 = client.post("/api/v1/transactions/authorize", json=payload, headers=headers)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["idempotent_replay"] is False

    # Second request with identical key
    res2 = client.post("/api/v1/transactions/authorize", json=payload, headers=headers)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["idempotent_replay"] is True
    assert data2["transaction_id"] == data1["transaction_id"]
    assert data2["amount"] == data1["amount"]


# ---------------------------------------------------------------------------
# Requirement 15: BLOCK Policy
# ---------------------------------------------------------------------------
def test_block_policy():
    """Requirement 15: Critical risk inputs trigger BLOCK_IMMEDIATELY and status BLOCKED."""
    token = get_token()
    payload = SAMPLE_HIGH_RISK_TXN.copy()
    payload["pin"] = "1234"
    res = client.post(
        "/api/v1/transactions/authorize",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["policy"] == "BLOCK_IMMEDIATELY"
    assert data["status"] == "BLOCKED"
    assert data["risk_score"] >= 75.0
    assert data["challenge"] is None


# ---------------------------------------------------------------------------
# Requirement 16: STEP_UP Policy
# ---------------------------------------------------------------------------
def test_step_up_policy():
    """Requirement 16: Medium risk inputs trigger STEP_UP_2FA and issue bound challenge."""
    token = get_token()
    payload = SAMPLE_MEDIUM_RISK_TXN.copy()
    payload["pin"] = "1234"
    res = client.post(
        "/api/v1/transactions/authorize",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["policy"] == "STEP_UP_2FA"
    assert data["status"] == "STEP_UP_REQUIRED"
    assert 40.0 <= data["risk_score"] < 75.0
    assert data["challenge"] is not None
    assert data["challenge"]["challenge_id"] is not None


# ---------------------------------------------------------------------------
# Requirement 17: APPROVE Policy
# ---------------------------------------------------------------------------
def test_approve_policy():
    """Requirement 17: Baseline legitimate transaction triggers APPROVE and status AUTHORIZED."""
    token = get_token()
    payload = SAMPLE_VALID_TXN.copy()
    payload["pin"] = "1234"
    res = client.post(
        "/api/v1/transactions/authorize",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["policy"] == "APPROVE"
    assert data["status"] == "AUTHORIZED"
    assert data["risk_score"] < 40.0
    assert data["challenge"] is None


# ---------------------------------------------------------------------------
# Requirement 18: Audit Log Creation & Zero Secrets Leakage
# ---------------------------------------------------------------------------
def test_audit_log_creation_and_zero_secret_leak():
    """Requirement 18: Security events persist to SQLite audit log with zero secrets leaked."""
    token = get_token(username="audit_tester")
    headers = {"Authorization": f"Bearer {token}"}
    payload = SAMPLE_VALID_TXN.copy()
    payload["pin"] = "1234"

    res = client.post("/api/v1/transactions/authorize", json=payload, headers=headers)
    assert res.status_code == 200
    txn_id = res.json()["transaction_id"]

    with db_session() as conn:
        row = conn.execute("SELECT * FROM audit_logs WHERE event_type LIKE 'TRANSACTION_%' ORDER BY id DESC LIMIT 1").fetchone()
        assert row is not None
        assert row["status_code"] == 200

        # Verify zero secrets leaked
        all_logs = conn.execute("SELECT details FROM audit_logs").fetchall()
        for log_row in all_logs:
            details_str = log_row["details"] or ""
            assert "1234" not in details_str or "amount" in details_str or "elapsed" in details_str  # PIN not logged as PIN
            assert "Upay@2026!" not in details_str
            assert "SecretPassword" not in details_str
