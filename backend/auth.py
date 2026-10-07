"""
RiskIntel upay - Authentication & Role-Based Authorization
File: backend/auth.py

Provides cryptographic JWT (HS256) handling, password hashing via PBKDF2-HMAC-SHA256,
synthetic demo credential verification, and FastAPI dependency guards.
Strictly returns HTTP 401 for unauthenticated calls and HTTP 403 for unauthorized roles.
"""

import base64
import hashlib
import hmac
import json
import logging
import secrets
import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.config import JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

logger = logging.getLogger("riskintel.auth")
security_bearer = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Password Hashing Utilities (PBKDF2-HMAC-SHA256)
# ---------------------------------------------------------------------------
def hash_password(password: str, salt: Optional[str] = None) -> str:
    """Hashes a password using PBKDF2-HMAC-SHA256 with 600,000 iterations."""
    if salt is None:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        600000
    )
    return f"pbkdf2_sha256${salt}${dk.hex()}"


def verify_password(plain_password: str, hashed_value: str) -> bool:
    """Verifies a plain password against stored PBKDF2 hash using constant-time comparison."""
    try:
        algorithm, salt, expected_hash = hashed_value.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        candidate = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            600000
        ).hex()
        return hmac.compare_digest(candidate, expected_hash)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Synthetic Demo Accounts (Clearly marked for Hackathon Evaluation)
# ---------------------------------------------------------------------------
# Pre-computed PBKDF2 hashes for demo accounts
SYNTHETIC_USERS: Dict[str, Dict[str, Any]] = {
    "demo_user": {
        "username": "demo_user",
        "user_id": "SYNTH-UPAY-USER-001",
        "full_name": "Rahim Ahmed (Synthetic Demo User)",
        "password_hash": hash_password("Upay@2026!", salt="demo_salt_user_001"),
        "role": "customer",
        "scopes": ["assess_risk", "step_up_2fa", "recover_account"],
        "is_synthetic": True,
    },
    "compliance_officer": {
        "username": "compliance_officer",
        "user_id": "SYNTH-UPAY-ANALYST-101",
        "full_name": "Farhana Sultana (Compliance Analyst)",
        "password_hash": hash_password("Analyst@2026!", salt="demo_salt_analyst_101"),
        "role": "analyst",
        "scopes": ["assess_risk", "step_up_2fa", "view_audit_logs"],
        "is_synthetic": True,
    },
    "security_admin": {
        "username": "security_admin",
        "user_id": "SYNTH-UPAY-ADMIN-999",
        "full_name": "Tariq Hasan (Chief Information Security Officer)",
        "password_hash": hash_password("Admin@2026!", salt="demo_salt_admin_999"),
        "role": "admin",
        "scopes": ["assess_risk", "step_up_2fa", "view_audit_logs", "manage_security"],
        "is_synthetic": True,
    },
}


# ---------------------------------------------------------------------------
# Cryptographic JWT (HS256) Engine
# ---------------------------------------------------------------------------
def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(encoded: str) -> bytes:
    padding = 4 - (len(encoded) % 4)
    if padding != 4:
        encoded += "=" * padding
    return base64.urlsafe_b64decode(encoded.encode("ascii"))


def create_access_token(
    user_id: str,
    username: str,
    role: str,
    scopes: List[str],
    expires_delta_minutes: Optional[int] = None
) -> str:
    """Issues a cryptographically signed HS256 JWT."""
    now = int(time.time())
    ttl = (expires_delta_minutes or ACCESS_TOKEN_EXPIRE_MINUTES) * 60
    exp = now + ttl

    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "scopes": scopes,
        "iat": now,
        "exp": exp,
        "iss": "riskintel-upay-engine",
    }

    header_bytes = json.dumps(header, separators=(",", ":")).encode("utf-8")
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")

    signing_input = f"{_b64url_encode(header_bytes)}.{_b64url_encode(payload_bytes)}"
    signature = hmac.new(
        JWT_SECRET_KEY.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256
    ).digest()

    return f"{signing_input}.{_b64url_encode(signature)}"


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decodes and cryptographically verifies an HS256 JWT.
    Raises HTTPException(401) on signature mismatch, malformed payload, or expiration.
    """
    parts = token.split(".")
    if len(parts) != 3:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    header_b64, payload_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}"

    expected_sig = hmac.new(
        JWT_SECRET_KEY.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256
    ).digest()

    try:
        actual_sig = _b64url_decode(sig_b64)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token signature encoding.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not hmac.compare_digest(actual_sig, expected_sig):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token cryptographic signature.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to decode token claims payload.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    now = int(time.time())
    if payload.get("exp", 0) < now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired. Please re-authenticate.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


# ---------------------------------------------------------------------------
# Schemas & FastAPI Dependencies
# ---------------------------------------------------------------------------
class AuthenticatedUser(BaseModel):
    user_id: str
    username: str
    role: str
    scopes: List[str] = Field(default_factory=list)


class LoginRequest(BaseModel):
    username: str = Field(..., description="Synthetic username (e.g. demo_user, compliance_officer, security_admin)")
    password: str = Field(..., description="Account password")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in_seconds: int
    user_id: str
    role: str
    username: str
    message: str


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer)
) -> AuthenticatedUser:
    """
    Enforces authentication on protected endpoints.
    Rejects requests without valid Bearer token with HTTP 401.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    return AuthenticatedUser(
        user_id=payload["sub"],
        username=payload.get("username", "anonymous"),
        role=payload.get("role", "customer"),
        scopes=payload.get("scopes", []),
    )


def require_role(allowed_roles: List[str]):
    """
    Enforces role-based authorization.
    Returns HTTP 403 Forbidden if authenticated user lacks one of the required roles.
    """
    def role_checker(current_user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if current_user.role not in allowed_roles:
            logger.warning(
                "Access forbidden: User %s (role: %s) requested endpoint requiring roles: %s",
                current_user.user_id,
                current_user.role,
                allowed_roles
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Insufficient privileges. Required roles: {allowed_roles}, your role: {current_user.role}.",
            )
        return current_user

    return role_checker

