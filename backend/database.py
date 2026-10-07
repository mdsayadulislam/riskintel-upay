"""
RiskIntel upay - Durable SQLite Persistence Layer
File: backend/database.py

Implements durable, append-only SQLite storage for audit logs,
two-factor authentication challenges, and account recovery records.
Uses Write-Ahead Logging (WAL) for concurrency and crash-durability.
"""

import sqlite3
import os
import logging
from contextlib import contextmanager
from typing import Generator
from backend.config import DATABASE_PATH

logger = logging.getLogger("riskintel.database")


def get_db_connection() -> sqlite3.Connection:
    """Creates a configured connection to the SQLite database with WAL mode."""
    os.makedirs(os.path.dirname(os.path.abspath(DATABASE_PATH)), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH, timeout=10.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for high concurrency and crash durability
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


@contextmanager
def db_session() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for database transactions."""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Initializes tables and indexes if they do not already exist."""
    logger.info("Initializing RiskIntel SQLite database at: %s", DATABASE_PATH)
    with db_session() as conn:
        # 1. Audit Logs (Durable, append-only compliance ledger)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                request_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                actor_id TEXT NOT NULL,
                role TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                status_code INTEGER NOT NULL,
                risk_score REAL,
                risk_decision TEXT,
                model_version TEXT,
                drivers_summary TEXT,
                client_ip TEXT,
                details TEXT
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_logs(event_type);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_actor_id ON audit_logs(actor_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_request_id ON audit_logs(request_id);")

        # 2. Step-Up 2FA Challenges (Salted and hashed OTP state)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS two_factor_challenges (
                challenge_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                otp_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                max_attempts INTEGER NOT NULL DEFAULT 3,
                verified INTEGER NOT NULL DEFAULT 0,
                backup_code_hash TEXT NOT NULL
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_2fa_user_id ON two_factor_challenges(user_id);")

        # 3. Account Recovery Tokens (One-time, hashed recovery tokens)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS recovery_tokens (
                token_hash TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                used INTEGER NOT NULL DEFAULT 0,
                used_at TEXT
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_recovery_user_id ON recovery_tokens(user_id);")

    logger.info("Database schema initialized successfully.")

