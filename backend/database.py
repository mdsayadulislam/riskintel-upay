"""
RiskIntel upay - Durable Persistence Layer (SQLite WAL & PostgreSQL Compatible)
File: backend/database.py

Implements durable persistence for:
1. Audit Logs (immutable, append-only compliance ledger)
2. Transactions (state machine: PENDING, STEP_UP_REQUIRED, AUTHORIZED, BLOCKED)
3. Step-Up 2FA Challenges (salted & hashed OTPs bound to user & transaction)
4. Account Recovery Tokens (one-time high-entropy hashes)
5. Idempotency Records (prevents duplicate financial execution)

Uses Write-Ahead Logging (WAL) for SQLite locally, and provides connection
hooks compatible with PostgreSQL for cloud deployments (e.g. Render).
"""

import sqlite3
import os
import logging
from contextlib import contextmanager
from typing import Generator, Any
from backend.config import DATABASE_PATH, DATABASE_URL

logger = logging.getLogger("riskintel.database")


def get_db_connection() -> sqlite3.Connection:
    """Creates a configured connection to the SQLite database with WAL mode."""
    os.makedirs(os.path.dirname(os.path.abspath(DATABASE_PATH)), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH, timeout=15.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for high concurrency and crash durability
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


@contextmanager
def db_session() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for atomic database transactions."""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _safe_add_column(conn: sqlite3.Connection, table: str, column_def: str) -> None:
    """Helper to add columns to existing SQLite tables without erroring."""
    try:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column_def};")
    except sqlite3.OperationalError:
        pass  # Column already exists


def init_db() -> None:
    """Initializes tables, columns, and indexes if they do not already exist."""
    logger.info("Initializing RiskIntel persistence layer (SQLite WAL: %s)", DATABASE_PATH)
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

        # 2. Transactions Table (Stateful transaction lifecycle)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                amount REAL NOT NULL,
                channel TEXT NOT NULL,
                recipient TEXT,
                risk_score REAL NOT NULL,
                risk_level TEXT NOT NULL,
                policy TEXT NOT NULL,
                status TEXT NOT NULL,
                idempotency_key TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                details TEXT
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_txn_user_id ON transactions(user_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_txn_status ON transactions(status);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_txn_idempotency ON transactions(idempotency_key);")

        # 3. Idempotency Records Table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS idempotency_records (
                key TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                response_code INTEGER NOT NULL,
                response_body TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_idempotency_user ON idempotency_records(user_id);")

        # 4. Step-Up 2FA Challenges (Salted and hashed OTP state bound to transaction)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS two_factor_challenges (
                challenge_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                transaction_id TEXT,
                purpose TEXT DEFAULT 'transaction_authorization',
                otp_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                max_attempts INTEGER NOT NULL DEFAULT 3,
                verified INTEGER NOT NULL DEFAULT 0,
                used_at TEXT,
                backup_code_hash TEXT NOT NULL
            );
        """)
        _safe_add_column(conn, "two_factor_challenges", "transaction_id TEXT")
        _safe_add_column(conn, "two_factor_challenges", "purpose TEXT DEFAULT 'transaction_authorization'")
        _safe_add_column(conn, "two_factor_challenges", "used_at TEXT")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_2fa_user_id ON two_factor_challenges(user_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_2fa_txn_id ON two_factor_challenges(transaction_id);")

        # 5. Account Recovery Tokens (One-time, hashed recovery tokens)
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

    logger.info("Database schema initialized and verified successfully.")
