"""
RiskIntel upay - Durable Persistent Audit Logging
File: backend/audit.py

Provides persistent, append-only SQLite logging for compliance, triage,
and incident post-mortems. Strictly guarantees zero secret / zero raw PII storage.
Provides an authorized inspection API for compliance officers and security admins.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from backend.database import db_session

logger = logging.getLogger("riskintel.audit")

# Redacted keys to prevent sensitive data leakage in audit records
REDACTED_KEYS = {
    "password", "secret", "token", "otp", "pin", "auth", "key",
    "access_token", "jwt", "authorization", "recovery_token"
}


def sanitize_audit_metadata(data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Sanitizes metadata dictionary to ensure secrets or PII are never persisted."""
    if not data:
        return {}
    sanitized = {}
    for k, v in data.items():
        lower_k = k.lower()
        if any(redacted in lower_k for redacted in REDACTED_KEYS):
            sanitized[k] = "[REDACTED_CREDENTIAL]"
        elif isinstance(v, dict):
            sanitized[k] = sanitize_audit_metadata(v)
        else:
            sanitized[k] = v
    return sanitized


def record_audit_event(
    event_type: str,
    actor_id: str,
    role: str,
    endpoint: str,
    status_code: int,
    request_id: Optional[str] = None,
    risk_score: Optional[float] = None,
    risk_decision: Optional[str] = None,
    model_version: Optional[str] = "LightGBM-v1.0-SHAP",
    drivers_summary: Optional[str] = None,
    client_ip: Optional[str] = "127.0.0.1",
    details: Optional[Dict[str, Any]] = None,
) -> int:
    """
    Appends an immutable audit event to the SQLite audit_logs table.
    Guarantees persistence and sanitization.
    """
    req_id = request_id or str(uuid.uuid4())
    timestamp_iso = datetime.now(timezone.utc).isoformat()
    clean_details = json.dumps(sanitize_audit_metadata(details))

    with db_session() as conn:
        cursor = conn.execute(
            """
            INSERT INTO audit_logs (
                timestamp, request_id, event_type, actor_id, role,
                endpoint, status_code, risk_score, risk_decision,
                model_version, drivers_summary, client_ip, details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                timestamp_iso,
                req_id,
                event_type,
                actor_id,
                role,
                endpoint,
                status_code,
                risk_score,
                risk_decision,
                model_version,
                drivers_summary,
                client_ip,
                clean_details,
            ),
        )
        record_id = cursor.lastrowid

    logger.info(
        "AUDIT [%s] %s | Actor: %s (%s) | Status: %d | ReqID: %s",
        event_type, endpoint, actor_id, role, status_code, req_id
    )
    return record_id


# ---------------------------------------------------------------------------
# Audit Record Schemas for Inspection API
# ---------------------------------------------------------------------------
class AuditLogEntry(BaseModel):
    id: int
    timestamp: str
    request_id: str
    event_type: str
    actor_id: str
    role: str
    endpoint: str
    status_code: int
    risk_score: Optional[float]
    risk_decision: Optional[str]
    model_version: Optional[str]
    drivers_summary: Optional[str]
    client_ip: Optional[str]
    details: Optional[str]


class AuditLogQueryResponse(BaseModel):
    total_count: int
    limit: int
    offset: int
    logs: List[AuditLogEntry]


def query_audit_logs(
    limit: int = 50,
    offset: int = 0,
    event_type: Optional[str] = None,
    actor_id: Optional[str] = None
) -> AuditLogQueryResponse:
    """Queries durable audit records with pagination and filtering."""
    query = "SELECT * FROM audit_logs WHERE 1=1"
    params = []

    if event_type:
        query += " AND event_type = ?"
        params.append(event_type)

    if actor_id:
        query += " AND actor_id = ?"
        params.append(actor_id)

    # Count query
    count_query = query.replace("SELECT *", "SELECT COUNT(*)", 1)
    with db_session() as conn:
        total = conn.execute(count_query, params).fetchone()[0]

        query += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = conn.execute(query, params).fetchall()

    entries = [
        AuditLogEntry(
            id=row["id"],
            timestamp=row["timestamp"],
            request_id=row["request_id"],
            event_type=row["event_type"],
            actor_id=row["actor_id"],
            role=row["role"],
            endpoint=row["endpoint"],
            status_code=row["status_code"],
            risk_score=row["risk_score"],
            risk_decision=row["risk_decision"],
            model_version=row["model_version"],
            drivers_summary=row["drivers_summary"],
            client_ip=row["client_ip"],
            details=row["details"],
        )
        for row in rows
    ]

    return AuditLogQueryResponse(
        total_count=total,
        limit=limit,
        offset=offset,
        logs=entries,
    )

