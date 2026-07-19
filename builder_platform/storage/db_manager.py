"""
Alta Builder Platform — Local SQLite Storage Manager
=====================================================
Zero-dependency persistence layer (stdlib sqlite3 only).

Usage::

    from builder_platform.storage.db_manager import StorageManager

    db = StorageManager()          # defaults to alta_builder.db next to this file
    db.init_db()                   # idempotent — safe to call on every startup

    db.create_session("web_k3x9m2q7")
    agent_id = db.register_agent(
        session_id="web_k3x9m2q7",
        agent_name="DentalBooker",
        project_path="/abs/path/to/Generated_Agents/DentalBooker_20260716",
        system_prompt="You are a dental appointment booking agent...",
    )
    db.update_selftest(agent_id, "passed")
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

_HERE = Path(__file__).resolve().parent
_DEFAULT_DB = _HERE / "alta_builder.db"
_SCHEMA_SQL = _HERE / "schema.sql"


class StorageManager:
    """Thin, synchronous wrapper around a local SQLite database.

    Uses a single shared connection (opened lazily on first use).
    Thread-safety is handled by SQLite's WAL mode; for multi-threaded
    servers, create one ``StorageManager`` per thread or protect calls
    with a lock.
    """

    def __init__(self, db_path: Path | str = _DEFAULT_DB) -> None:
        self._db_path = Path(db_path) if str(db_path) != ":memory:" else db_path
        self._conn: Optional[sqlite3.Connection] = None

    # ── connection helper ────────────────────────────────────────────

    def _get_conn(self) -> sqlite3.Connection:
        """Return the shared connection, opening it on first call."""
        if self._conn is None:
            self._conn = sqlite3.connect(
                str(self._db_path),
                timeout=5.0,
                isolation_level="DEFERRED",
            )
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
        return self._conn

    @contextmanager
    def _cursor(self):
        """Yield a cursor inside a transaction; commit on success, rollback on error."""
        conn = self._get_conn()
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def close(self) -> None:
        """Close the underlying connection (safe to call multiple times)."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    # ── bootstrap ────────────────────────────────────────────────────

    def init_db(self) -> None:
        """Create the database file and tables if they don't already exist.

        Idempotent — safe to call on every server startup.
        """
        schema = _SCHEMA_SQL.read_text(encoding="utf-8")
        with self._cursor() as cur:
            cur.executescript(schema)

    # ── sessions ─────────────────────────────────────────────────────

    def create_session(self, session_id: str) -> Dict[str, Any]:
        """Insert a new session row.  Returns the created row as a dict.

        If the session_id already exists the call is a no-op and returns
        the existing row (idempotent — the frontend may re-send the same
        id on page reload).
        """
        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO sessions (session_id)
                VALUES (?)
                ON CONFLICT(session_id) DO UPDATE
                    SET last_active = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                """,
                (session_id,),
            )
            cur.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
            return dict(cur.fetchone())

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Return the session row or ``None``."""
        with self._cursor() as cur:
            cur.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def touch_session(self, session_id: str) -> None:
        """Bump ``last_active`` to now."""
        with self._cursor() as cur:
            cur.execute(
                """
                UPDATE sessions
                   SET last_active = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                 WHERE session_id = ?
                """,
                (session_id,),
            )

    def close_session(self, session_id: str) -> None:
        """Mark a session as inactive."""
        with self._cursor() as cur:
            cur.execute(
                "UPDATE sessions SET active = 0 WHERE session_id = ?",
                (session_id,),
            )

    # ── built agents ─────────────────────────────────────────────────

    def register_agent(
        self,
        session_id: str,
        agent_name: str,
        project_path: str,
        system_prompt: Optional[str] = None,
    ) -> int:
        """Register a newly generated agent.  Returns the new row id."""
        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO built_agents
                    (session_id, agent_name, project_path, system_prompt)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, agent_name, project_path, system_prompt),
            )
            return cur.lastrowid  # type: ignore[return-value]

    def update_selftest(self, agent_id: int, status: str) -> None:
        """Update the selftest status of a built agent.

        Parameters
        ----------
        agent_id : int
            The ``built_agents.id`` returned by :meth:`register_agent`.
        status : str
            One of ``"pending"``, ``"running"``, ``"passed"``, ``"failed"``.
        """
        allowed = {"pending", "running", "passed", "failed"}
        if status not in allowed:
            raise ValueError(f"status must be one of {allowed}, got {status!r}")
        with self._cursor() as cur:
            cur.execute(
                """
                UPDATE built_agents
                   SET selftest_status = ?,
                       updated_at      = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                 WHERE id = ?
                """,
                (status, agent_id),
            )

    def get_agent(self, agent_id: int) -> Optional[Dict[str, Any]]:
        """Return a single agent row or ``None``."""
        with self._cursor() as cur:
            cur.execute("SELECT * FROM built_agents WHERE id = ?", (agent_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def list_agents(self, session_id: str) -> List[Dict[str, Any]]:
        """Return all agents built within a session, newest first."""
        with self._cursor() as cur:
            cur.execute(
                "SELECT * FROM built_agents WHERE session_id = ? ORDER BY id DESC",
                (session_id,),
            )
            return [dict(r) for r in cur.fetchall()]

    def latest_agent(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Return the most recently built agent for a session, or ``None``."""
        with self._cursor() as cur:
            cur.execute(
                """
                SELECT * FROM built_agents
                 WHERE session_id = ?
                 ORDER BY id DESC
                 LIMIT 1
                """,
                (session_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None
