"""Persistent, idempotent escalation actions for the local demo.

SQLite persistence is suitable for a single-instance demo. For multi-instance
production deployment, replace this store with a shared transactional database.
"""
import sqlite3
from datetime import datetime, timezone

from src.config import STORAGE_DIR

DB_PATH = STORAGE_DIR / "escalations.sqlite3"


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(DB_PATH), timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS escalations (
            escalation_id TEXT PRIMARY KEY,
            ticket_id TEXT NOT NULL UNIQUE,
            reason TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            idempotency_key TEXT NOT NULL UNIQUE
        )
        """
    )
    return connection


def create_escalation(ticket_id, reason, idempotency_key=None):
    """Create at most one escalation per ticket; retries return its record."""
    normalized_ticket = str(ticket_id).strip().upper()
    if not normalized_ticket:
        raise ValueError("A valid ticket ID is required.")

    request_key = str(idempotency_key or "ticket:" + normalized_ticket)
    escalation_id = "ESC-" + normalized_ticket
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    connection = _connect()
    try:
        with connection:
            # Acquire the write reservation before checking uniqueness.
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT * FROM escalations WHERE ticket_id = ? OR idempotency_key = ?",
                (normalized_ticket, request_key),
            ).fetchone()

            if existing:
                result = dict(existing)
                result["already_exists"] = True
                return result

            connection.execute(
                """
                INSERT INTO escalations
                (escalation_id, ticket_id, reason, status, created_at, idempotency_key)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    escalation_id,
                    normalized_ticket,
                    str(reason),
                    "Escalation created",
                    created_at,
                    request_key,
                ),
            )
            result = dict(connection.execute(
                "SELECT * FROM escalations WHERE ticket_id = ?",
                (normalized_ticket,),
            ).fetchone())
            result["already_exists"] = False
            return result
    finally:
        connection.close()


def list_escalations():
    """Return persisted escalation records for diagnostics."""
    connection = _connect()
    try:
        rows = connection.execute(
            "SELECT * FROM escalations ORDER BY created_at DESC"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()
