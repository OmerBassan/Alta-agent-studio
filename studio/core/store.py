"""The episode store — durable product data, not operational logs (FR73).

SQLite behind a small API, at the Spine's documented fallback floor for
durability: every record carries a tenant (AD-17); the journal is append-only
and every agent request, Core decision and inbound message is a step in it
(AD-2, AD-12); an external effect is keyed by a Core-issued idempotency key
under ``UNIQUE (tenant, episode_id, idempotency_key)``, and its evidence row is
written in the same transaction as its outcome (AD-6, AD-10). The engine is an
infrastructure choice behind this API (``m-arch`` 48); moving to PostgreSQL is
an implementation change here, not a change to the Core.

The Core is the only writer (AD-13). Step order is recorded because it is what
happened; nothing reads it as permission for what may happen next (AD-12).

Every query is scoped by tenant. A lookup that crosses tenants is *rejected*
by the caller, never answered with an empty result (AD-17) — which is why the
provenance lookup deliberately does not filter by tenant: the Core must see
the foreign reference in order to refuse it.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterator, Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS tenant_flags (
  tenant TEXT PRIMARY KEY,
  agent_suspended INTEGER NOT NULL DEFAULT 0,
  effects_suspended INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL,
  updated_by TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS episodes (
  tenant TEXT NOT NULL,
  episode_id TEXT NOT NULL,
  conversation_key TEXT NOT NULL,
  spec_version TEXT NOT NULL,
  compiler_version TEXT NOT NULL,
  lifecycle TEXT NOT NULL CHECK (lifecycle IN ('active', 'pending', 'closed')),
  awaiting TEXT,
  deadline TEXT,
  close_reason TEXT CHECK (close_reason IS NULL OR close_reason IN ('resolved','escalated','halted','suspended')),
  active_goal TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (tenant, episode_id)
);
CREATE INDEX IF NOT EXISTS episodes_by_conversation ON episodes (tenant, conversation_key, lifecycle);
CREATE TABLE IF NOT EXISTS inbound (
  tenant TEXT NOT NULL,
  message_id TEXT NOT NULL,
  episode_id TEXT NOT NULL,
  received_at TEXT NOT NULL,
  PRIMARY KEY (tenant, message_id)
);
CREATE TABLE IF NOT EXISTS steps (
  tenant TEXT NOT NULL,
  episode_id TEXT NOT NULL,
  seq INTEGER NOT NULL,
  at TEXT NOT NULL,
  actor TEXT NOT NULL CHECK (actor IN ('requester', 'agent', 'core', 'operator')),
  kind TEXT NOT NULL,
  payload TEXT NOT NULL,
  PRIMARY KEY (tenant, episode_id, seq)
);
CREATE TABLE IF NOT EXISTS facts (
  tenant TEXT NOT NULL,
  episode_id TEXT NOT NULL,
  name TEXT NOT NULL,
  value TEXT NOT NULL,
  step_seq INTEGER NOT NULL,
  PRIMARY KEY (tenant, episode_id, name)
);
CREATE TABLE IF NOT EXISTS goals (
  tenant TEXT NOT NULL,
  episode_id TEXT NOT NULL,
  goal_id TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state IN ('active', 'parked', 'resolved')),
  updated_seq INTEGER NOT NULL,
  PRIMARY KEY (tenant, episode_id, goal_id)
);
CREATE TABLE IF NOT EXISTS provenance (
  ref TEXT PRIMARY KEY,
  tenant TEXT NOT NULL,
  episode_id TEXT NOT NULL,
  item_id TEXT NOT NULL,
  source_id TEXT NOT NULL,
  source_version TEXT NOT NULL,
  locator TEXT NOT NULL,
  issued_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS provenance_by_episode ON provenance (tenant, episode_id);
CREATE TABLE IF NOT EXISTS offers (
  offer_id TEXT PRIMARY KEY,
  tenant TEXT NOT NULL,
  episode_id TEXT NOT NULL,
  gate TEXT NOT NULL CHECK (gate IN ('confirmation', 'operator_approval')),
  capability TEXT NOT NULL,
  digest TEXT NOT NULL,
  spec_version TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state IN ('offered', 'granted', 'declined', 'consumed', 'expired')),
  offered_seq INTEGER NOT NULL,
  decided_by TEXT,
  decided_at TEXT
);
CREATE TABLE IF NOT EXISTS effects (
  tenant TEXT NOT NULL,
  episode_id TEXT NOT NULL,
  idempotency_key TEXT NOT NULL,
  capability TEXT NOT NULL,
  arguments TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state IN ('started', 'verified', 'unverified', 'failed')),
  reference TEXT,
  evidence_id TEXT,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  UNIQUE (tenant, episode_id, idempotency_key)
);
CREATE TABLE IF NOT EXISTS evidence (
  evidence_id TEXT PRIMARY KEY,
  tenant TEXT NOT NULL,
  episode_id TEXT NOT NULL,
  kind TEXT NOT NULL,
  payload TEXT NOT NULL,
  step_seq INTEGER NOT NULL,
  at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS evidence_by_episode ON evidence (tenant, episode_id);
CREATE TABLE IF NOT EXISTS denials (
  tenant TEXT NOT NULL,
  episode_id TEXT NOT NULL,
  step_seq INTEGER NOT NULL,
  classification TEXT NOT NULL CHECK (classification IN ('spec_defect', 'business_refusal', 'platform_error')),
  reason TEXT NOT NULL,
  detail TEXT NOT NULL,
  spec_version TEXT NOT NULL,
  at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS resolutions (
  tenant TEXT NOT NULL,
  episode_id TEXT NOT NULL,
  goal_id TEXT NOT NULL,
  served INTEGER NOT NULL,
  authority TEXT NOT NULL,
  evidence TEXT NOT NULL,
  payload TEXT NOT NULL,
  at TEXT NOT NULL,
  PRIMARY KEY (tenant, episode_id, goal_id)
);
CREATE TABLE IF NOT EXISTS waivers (
  tenant TEXT NOT NULL,
  episode_id TEXT NOT NULL,
  goal_id TEXT NOT NULL,
  obligation TEXT NOT NULL,
  authority TEXT NOT NULL,
  waived_by TEXT NOT NULL,
  at TEXT NOT NULL,
  PRIMARY KEY (tenant, episode_id, goal_id, obligation)
);
CREATE TABLE IF NOT EXISTS outbox (
  tenant TEXT NOT NULL,
  episode_id TEXT NOT NULL,
  seq INTEGER NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('reply', 'terminal_notice', 'escalation', 'halt_notice')),
  destination TEXT NOT NULL,
  body TEXT NOT NULL,
  created_at TEXT NOT NULL,
  delivered_at TEXT,
  PRIMARY KEY (tenant, episode_id, seq)
);
CREATE TABLE IF NOT EXISTS model_calls (
  tenant TEXT NOT NULL,
  episode_id TEXT NOT NULL,
  step_seq INTEGER NOT NULL,
  model TEXT NOT NULL,
  ok INTEGER NOT NULL,
  path TEXT NOT NULL,
  input_tokens INTEGER,
  output_tokens INTEGER,
  latency_ms REAL NOT NULL,
  error TEXT
);
CREATE TABLE IF NOT EXISTS late_results (
  tenant TEXT NOT NULL,
  episode_id TEXT NOT NULL,
  payload TEXT NOT NULL,
  at TEXT NOT NULL
);
"""

logger = logging.getLogger("studio.store")

EPISODE_TABLES = ("episodes", "inbound", "steps", "facts", "goals", "provenance", "offers", "effects", "evidence",
                  "denials", "resolutions", "waivers", "outbox", "model_calls", "late_results")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_instant(text: str) -> datetime:
    """An ISO 8601 date-time, as an aware UTC datetime. A naive value is read
    as UTC. A date without a time of day is refused: whether "2026-10-20" means
    its start or its end is a guess, and a deadline is never guessed. Raises
    ``ValueError`` on anything else."""
    if not isinstance(text, str) or len(text.strip()) <= 10:
        raise ValueError(f"{text!r} is not an ISO 8601 date-time")
    value = datetime.fromisoformat(text.strip())
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    try:
        return value.astimezone(timezone.utc)
    except OverflowError as exc:  # e.g. 0001-01-01T00:00:00+01:00 has no UTC equivalent
        raise ValueError(f"{text!r} is outside the representable range") from exc


def _dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


@dataclass(frozen=True)
class Episode:
    tenant: str
    episode_id: str
    conversation_key: str
    spec_version: str
    compiler_version: str
    lifecycle: str
    awaiting: Optional[str]
    deadline: Optional[str]
    close_reason: Optional[str]
    active_goal: Optional[str]
    created_at: str


class EpisodeStore:
    def __init__(self, path: str | Path = ":memory:", clock: Callable[[], datetime] = utc_now):
        self._db = sqlite3.connect(str(path), isolation_level=None, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA foreign_keys = ON")
        if str(path) != ":memory:":
            self._db.execute("PRAGMA journal_mode = WAL")
        self._db.executescript(SCHEMA)
        self._lock = threading.RLock()
        self._depth = 0
        self._clock = clock

    # --- transactions -------------------------------------------------------------

    def now(self) -> str:
        return self._clock().astimezone(timezone.utc).isoformat()

    @contextmanager
    def transaction(self) -> Iterator[None]:
        """All writes inside one block commit together or not at all. Nested
        blocks join the outer transaction."""
        with self._lock:
            outer = self._depth == 0
            if outer:
                self._db.execute("BEGIN IMMEDIATE")
            self._depth += 1
            try:
                yield
            except BaseException:
                self._depth -= 1
                if outer:
                    self._db.execute("ROLLBACK")
                raise
            self._depth -= 1
            if outer:
                self._db.execute("COMMIT")

    def _exec(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        with self.transaction():
            return self._db.execute(sql, params)

    def _all(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        with self._lock:
            return list(self._db.execute(sql, params))

    def _one(self, sql: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        with self._lock:
            return self._db.execute(sql, params).fetchone()

    # --- tenant flags (FR110) -------------------------------------------------------

    def flags(self, tenant: str) -> tuple[bool, bool]:
        row = self._one("SELECT agent_suspended, effects_suspended FROM tenant_flags WHERE tenant = ?", (tenant,))
        return (bool(row["agent_suspended"]), bool(row["effects_suspended"])) if row else (False, False)

    def set_flags(self, tenant: str, *, agent_suspended: bool, effects_suspended: bool, by: str) -> None:
        self._exec(
            "INSERT INTO tenant_flags (tenant, agent_suspended, effects_suspended, updated_at, updated_by) "
            "VALUES (?, ?, ?, ?, ?) ON CONFLICT(tenant) DO UPDATE SET agent_suspended = excluded.agent_suspended, "
            "effects_suspended = excluded.effects_suspended, updated_at = excluded.updated_at, "
            "updated_by = excluded.updated_by",
            (tenant, int(agent_suspended), int(effects_suspended), self.now(), by))

    # --- episodes ---------------------------------------------------------------------

    def _episode(self, row: Optional[sqlite3.Row]) -> Optional[Episode]:
        if row is None:
            return None
        return Episode(**{k: row[k] for k in Episode.__dataclass_fields__})

    def open_episode(self, tenant: str, conversation_key: str) -> Optional[Episode]:
        return self._episode(self._one(
            "SELECT * FROM episodes WHERE tenant = ? AND conversation_key = ? AND lifecycle != 'closed' "
            "ORDER BY created_at DESC LIMIT 1", (tenant, conversation_key)))

    def get_episode(self, tenant: str, episode_id: str) -> Optional[Episode]:
        return self._episode(self._one("SELECT * FROM episodes WHERE tenant = ? AND episode_id = ?",
                                       (tenant, episode_id)))

    def episodes(self, tenant: str) -> list[Episode]:
        return [self._episode(r) for r in self._all(
            "SELECT * FROM episodes WHERE tenant = ? ORDER BY created_at", (tenant,))]

    def due_pending(self, now: str) -> list[Episode]:
        """Pending episodes, across every tenant, whose deadline is at or before
        ``now``. Deadlines are compared as parsed instants, never as strings.
        The Core validates a deadline before it is stored; a row that still
        cannot be parsed is logged and skipped, never treated as due."""
        cutoff = parse_instant(now)
        due = []
        for row in self._all("SELECT * FROM episodes WHERE lifecycle = 'pending' AND deadline IS NOT NULL "
                             "ORDER BY created_at"):
            try:
                deadline = parse_instant(row["deadline"])
            except ValueError:
                logger.warning("episode %s/%s has an unreadable deadline %r", row["tenant"], row["episode_id"],
                               row["deadline"])
                continue
            if deadline <= cutoff:
                due.append(self._episode(row))
        return due

    def create_episode(self, tenant: str, conversation_key: str, spec_version: str, compiler_version: str) -> Episode:
        episode_id = "ep_" + uuid.uuid4().hex[:16]
        now = self.now()
        self._exec("INSERT INTO episodes (tenant, episode_id, conversation_key, spec_version, compiler_version, "
                   "lifecycle, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 'active', ?, ?)",
                   (tenant, episode_id, conversation_key, spec_version, compiler_version, now, now))
        return self.get_episode(tenant, episode_id)

    def set_lifecycle(self, tenant: str, episode_id: str, lifecycle: str, *, awaiting: Optional[str] = None,
                      deadline: Optional[str] = None, close_reason: Optional[str] = None) -> None:
        self._exec("UPDATE episodes SET lifecycle = ?, awaiting = ?, deadline = ?, close_reason = ?, updated_at = ? "
                   "WHERE tenant = ? AND episode_id = ?",
                   (lifecycle, awaiting, deadline, close_reason, self.now(), tenant, episode_id))

    # --- inbound dedupe (FR87) ---------------------------------------------------------

    def seen_message(self, tenant: str, message_id: str) -> Optional[str]:
        row = self._one("SELECT episode_id FROM inbound WHERE tenant = ? AND message_id = ?", (tenant, message_id))
        return row["episode_id"] if row else None

    def record_inbound(self, tenant: str, message_id: str, episode_id: str) -> None:
        self._exec("INSERT INTO inbound (tenant, message_id, episode_id, received_at) VALUES (?, ?, ?, ?)",
                   (tenant, message_id, episode_id, self.now()))

    # --- journal ------------------------------------------------------------------------

    def append_step(self, tenant: str, episode_id: str, actor: str, kind: str, payload: Any) -> int:
        with self.transaction():
            row = self._db.execute("SELECT COALESCE(MAX(seq), 0) + 1 AS n FROM steps WHERE tenant = ? AND episode_id = ?",
                                   (tenant, episode_id)).fetchone()
            seq = int(row["n"])
            self._db.execute("INSERT INTO steps (tenant, episode_id, seq, at, actor, kind, payload) "
                             "VALUES (?, ?, ?, ?, ?, ?, ?)", (tenant, episode_id, seq, self.now(), actor, kind,
                                                              _dump(payload)))
        return seq

    def steps(self, tenant: str, episode_id: str) -> list[dict]:
        return [{**dict(r), "payload": json.loads(r["payload"])} for r in self._all(
            "SELECT * FROM steps WHERE tenant = ? AND episode_id = ? ORDER BY seq", (tenant, episode_id))]

    # --- facts and goals (AD-19) ---------------------------------------------------------

    def set_fact(self, tenant: str, episode_id: str, name: str, value: Any, step_seq: int) -> None:
        self._exec("INSERT INTO facts (tenant, episode_id, name, value, step_seq) VALUES (?, ?, ?, ?, ?) "
                   "ON CONFLICT(tenant, episode_id, name) DO UPDATE SET value = excluded.value, "
                   "step_seq = excluded.step_seq", (tenant, episode_id, name, _dump(value), step_seq))

    def facts(self, tenant: str, episode_id: str) -> dict[str, Any]:
        return {r["name"]: json.loads(r["value"]) for r in self._all(
            "SELECT name, value FROM facts WHERE tenant = ? AND episode_id = ?", (tenant, episode_id))}

    def set_active_goal(self, tenant: str, episode_id: str, goal_id: str, step_seq: int) -> None:
        """Make ``goal_id`` the one active goal; the previous active goal is parked
        explicitly (FR50). The Core records the Agent's choice; it never makes it."""
        with self.transaction():
            self._db.execute("UPDATE goals SET state = 'parked', updated_seq = ? WHERE tenant = ? AND episode_id = ? "
                             "AND state = 'active' AND goal_id != ?", (step_seq, tenant, episode_id, goal_id))
            self._db.execute("INSERT INTO goals (tenant, episode_id, goal_id, state, updated_seq) "
                             "VALUES (?, ?, ?, 'active', ?) ON CONFLICT(tenant, episode_id, goal_id) "
                             "DO UPDATE SET state = 'active', updated_seq = excluded.updated_seq",
                             (tenant, episode_id, goal_id, step_seq))
            self._db.execute("UPDATE episodes SET active_goal = ?, updated_at = ? WHERE tenant = ? AND episode_id = ?",
                             (goal_id, self.now(), tenant, episode_id))

    def mark_goal_resolved(self, tenant: str, episode_id: str, goal_id: str, step_seq: int) -> None:
        self._exec("INSERT INTO goals (tenant, episode_id, goal_id, state, updated_seq) VALUES (?, ?, ?, 'resolved', ?) "
                   "ON CONFLICT(tenant, episode_id, goal_id) DO UPDATE SET state = 'resolved', "
                   "updated_seq = excluded.updated_seq", (tenant, episode_id, goal_id, step_seq))

    def goals(self, tenant: str, episode_id: str) -> dict[str, str]:
        return {r["goal_id"]: r["state"] for r in self._all(
            "SELECT goal_id, state FROM goals WHERE tenant = ? AND episode_id = ?", (tenant, episode_id))}

    # --- provenance (AD-7) -------------------------------------------------------------

    def issue_reference(self, tenant: str, episode_id: str, item_id: str, source_id: str, source_version: str,
                        locator: str) -> str:
        ref = "ref_" + uuid.uuid4().hex[:12]
        self._exec("INSERT INTO provenance (ref, tenant, episode_id, item_id, source_id, source_version, locator, "
                   "issued_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                   (ref, tenant, episode_id, item_id, source_id, source_version, locator, self.now()))
        return ref

    def references(self, tenant: str, episode_id: str) -> list[dict]:
        return [dict(r) for r in self._all("SELECT * FROM provenance WHERE tenant = ? AND episode_id = ? ORDER BY ref",
                                           (tenant, episode_id))]

    def lookup_reference(self, ref: str) -> Optional[dict]:
        """Deliberately unscoped: the caller must see a foreign reference in order
        to reject it (AD-17), rather than receive a silent miss."""
        row = self._one("SELECT * FROM provenance WHERE ref = ?", (ref,))
        return dict(row) if row else None

    # --- gates: confirmation and operator approval (AD-2, FR53, FR16) ---------------------

    def create_offer(self, tenant: str, episode_id: str, gate: str, capability: str, digest: str,
                     spec_version: str, step_seq: int) -> str:
        existing = self._one("SELECT offer_id FROM offers WHERE tenant = ? AND episode_id = ? AND gate = ? AND "
                             "digest = ? AND state = 'offered'", (tenant, episode_id, gate, digest))
        if existing:
            return existing["offer_id"]
        offer_id = "of_" + uuid.uuid4().hex[:12]
        self._exec("INSERT INTO offers (offer_id, tenant, episode_id, gate, capability, digest, spec_version, state, "
                   "offered_seq) VALUES (?, ?, ?, ?, ?, ?, ?, 'offered', ?)",
                   (offer_id, tenant, episode_id, gate, capability, digest, spec_version, step_seq))
        return offer_id

    def offers(self, tenant: str, episode_id: str, gate: Optional[str] = None) -> list[dict]:
        sql = "SELECT * FROM offers WHERE tenant = ? AND episode_id = ?"
        params: tuple = (tenant, episode_id)
        if gate:
            sql += " AND gate = ?"
            params += (gate,)
        return [dict(r) for r in self._all(sql + " ORDER BY offered_seq", params)]

    def get_offer(self, offer_id: str) -> Optional[dict]:
        row = self._one("SELECT * FROM offers WHERE offer_id = ?", (offer_id,))
        return dict(row) if row else None

    def decide_offer(self, offer_id: str, state: str, decided_by: str) -> None:
        self._exec("UPDATE offers SET state = ?, decided_by = ?, decided_at = ? WHERE offer_id = ?",
                   (state, decided_by, self.now(), offer_id))

    # --- effects and evidence (AD-6, AD-10) ---------------------------------------------

    def get_effect(self, tenant: str, episode_id: str, key: str) -> Optional[dict]:
        row = self._one("SELECT * FROM effects WHERE tenant = ? AND episode_id = ? AND idempotency_key = ?",
                        (tenant, episode_id, key))
        return dict(row) if row else None

    def start_effect(self, tenant: str, episode_id: str, key: str, capability: str, arguments: dict) -> None:
        self._exec("INSERT INTO effects (tenant, episode_id, idempotency_key, capability, arguments, state, started_at) "
                   "VALUES (?, ?, ?, ?, ?, 'started', ?)",
                   (tenant, episode_id, key, capability, _dump(arguments), self.now()))

    def finish_effect(self, tenant: str, episode_id: str, key: str, state: str, reference: Optional[str],
                      evidence_kind: str, evidence_payload: dict, step_seq: int) -> str:
        """Record an effect's outcome and its evidence in one transaction, so
        the evidence and the effect it describes can never diverge."""
        with self.transaction():
            evidence_id = self.add_evidence(tenant, episode_id, evidence_kind, evidence_payload, step_seq)
            self._db.execute("UPDATE effects SET state = ?, reference = ?, evidence_id = ?, finished_at = ? "
                             "WHERE tenant = ? AND episode_id = ? AND idempotency_key = ?",
                             (state, reference, evidence_id, self.now(), tenant, episode_id, key))
        return evidence_id

    def add_evidence(self, tenant: str, episode_id: str, kind: str, payload: dict, step_seq: int) -> str:
        evidence_id = "ev_" + uuid.uuid4().hex[:12]
        self._exec("INSERT INTO evidence (evidence_id, tenant, episode_id, kind, payload, step_seq, at) "
                   "VALUES (?, ?, ?, ?, ?, ?, ?)", (evidence_id, tenant, episode_id, kind, _dump(payload), step_seq,
                                                   self.now()))
        return evidence_id

    def get_evidence(self, evidence_id: str) -> Optional[dict]:
        row = self._one("SELECT * FROM evidence WHERE evidence_id = ?", (evidence_id,))
        return {**dict(row), "payload": json.loads(row["payload"])} if row else None

    def evidence(self, tenant: str, episode_id: str) -> list[dict]:
        return [{**dict(r), "payload": json.loads(r["payload"])} for r in self._all(
            "SELECT * FROM evidence WHERE tenant = ? AND episode_id = ? ORDER BY step_seq, at", (tenant, episode_id))]

    # --- denials, resolutions, waivers --------------------------------------------------

    def add_denial(self, tenant: str, episode_id: str, step_seq: int, classification: str, reason: str, detail: str,
                   spec_version: str) -> None:
        self._exec("INSERT INTO denials (tenant, episode_id, step_seq, classification, reason, detail, spec_version, at) "
                   "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                   (tenant, episode_id, step_seq, classification, reason, detail, spec_version, self.now()))

    def denials(self, tenant: str, episode_id: Optional[str] = None) -> list[dict]:
        if episode_id:
            return [dict(r) for r in self._all("SELECT * FROM denials WHERE tenant = ? AND episode_id = ? "
                                               "ORDER BY step_seq", (tenant, episode_id))]
        return [dict(r) for r in self._all("SELECT * FROM denials WHERE tenant = ? ORDER BY at", (tenant,))]

    def set_resolution(self, tenant: str, episode_id: str, goal_id: str, served: bool, authority: str,
                       evidence: list[str], payload: dict) -> None:
        self._exec("INSERT INTO resolutions (tenant, episode_id, goal_id, served, authority, evidence, payload, at) "
                   "VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(tenant, episode_id, goal_id) DO UPDATE SET "
                   "served = excluded.served, authority = excluded.authority, evidence = excluded.evidence, "
                   "payload = excluded.payload, at = excluded.at",
                   (tenant, episode_id, goal_id, int(served), authority, _dump(evidence), _dump(payload), self.now()))

    def resolutions(self, tenant: str, episode_id: str) -> list[dict]:
        return [{**dict(r), "evidence": json.loads(r["evidence"]), "payload": json.loads(r["payload"])}
                for r in self._all("SELECT * FROM resolutions WHERE tenant = ? AND episode_id = ?",
                                   (tenant, episode_id))]

    def add_waiver(self, tenant: str, episode_id: str, goal_id: str, obligation: str, authority: str, by: str) -> None:
        self._exec("INSERT OR REPLACE INTO waivers (tenant, episode_id, goal_id, obligation, authority, waived_by, at) "
                   "VALUES (?, ?, ?, ?, ?, ?, ?)", (tenant, episode_id, goal_id, obligation, authority, by, self.now()))

    def waivers(self, tenant: str, episode_id: str) -> dict[str, set[str]]:
        out: dict[str, set[str]] = {}
        for r in self._all("SELECT goal_id, obligation FROM waivers WHERE tenant = ? AND episode_id = ?",
                           (tenant, episode_id)):
            out.setdefault(r["goal_id"], set()).add(r["obligation"])
        return out

    # --- outbox, model calls, late results -------------------------------------------------

    def add_outbox(self, tenant: str, episode_id: str, kind: str, destination: str, body: str) -> None:
        with self.transaction():
            row = self._db.execute("SELECT COALESCE(MAX(seq), 0) + 1 AS n FROM outbox WHERE tenant = ? AND episode_id = ?",
                                   (tenant, episode_id)).fetchone()
            self._db.execute("INSERT INTO outbox (tenant, episode_id, seq, kind, destination, body, created_at) "
                             "VALUES (?, ?, ?, ?, ?, ?, ?)",
                             (tenant, episode_id, int(row["n"]), kind, destination, body, self.now()))

    def outbox(self, tenant: str, episode_id: Optional[str] = None) -> list[dict]:
        if episode_id:
            return [dict(r) for r in self._all("SELECT * FROM outbox WHERE tenant = ? AND episode_id = ? ORDER BY seq",
                                               (tenant, episode_id))]
        return [dict(r) for r in self._all("SELECT * FROM outbox WHERE tenant = ? ORDER BY created_at, seq", (tenant,))]

    def add_model_call(self, tenant: str, episode_id: str, step_seq: int, call: dict) -> None:
        self._exec("INSERT INTO model_calls (tenant, episode_id, step_seq, model, ok, path, input_tokens, output_tokens, "
                   "latency_ms, error) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   (tenant, episode_id, step_seq, call["model"], int(call["ok"]), call["path"],
                    call.get("input_tokens"), call.get("output_tokens"), call.get("latency_ms", 0.0),
                    call.get("error")))

    def model_calls(self, tenant: str, episode_id: str) -> list[dict]:
        return [dict(r) for r in self._all("SELECT * FROM model_calls WHERE tenant = ? AND episode_id = ? "
                                           "ORDER BY step_seq", (tenant, episode_id))]

    def add_late_result(self, tenant: str, episode_id: str, payload: dict) -> None:
        self._exec("INSERT INTO late_results (tenant, episode_id, payload, at) VALUES (?, ?, ?, ?)",
                   (tenant, episode_id, _dump(payload), self.now()))

    def late_results(self, tenant: str, episode_id: str) -> list[dict]:
        return [{**dict(r), "payload": json.loads(r["payload"])} for r in self._all(
            "SELECT * FROM late_results WHERE tenant = ? AND episode_id = ?", (tenant, episode_id))]

    # --- data lifecycle (AD-25, FR75) ------------------------------------------------------

    def purge(self, tenant: str, *, episode_id: Optional[str] = None, older_than_days: Optional[int] = None) -> int:
        """Remove episodes and everything recorded about them, by tenant, by
        episode, or by age — without reshaping any table. The retention policy
        and the executor that calls this are deferred (AD-25)."""
        if episode_id is None and older_than_days is None:
            raise ValueError("purge needs an episode or an age; purging a whole tenant is done one age at a time")
        with self.transaction():
            if episode_id is not None:
                ids = [episode_id]
            else:
                cutoff = (self._clock() - timedelta(days=older_than_days)).astimezone(timezone.utc).isoformat()
                ids = [r["episode_id"] for r in self._db.execute(
                    "SELECT episode_id FROM episodes WHERE tenant = ? AND updated_at < ?", (tenant, cutoff))]
            for eid in ids:
                for table in EPISODE_TABLES:
                    self._db.execute(f"DELETE FROM {table} WHERE tenant = ? AND episode_id = ?", (tenant, eid))
        return len(ids)

    def close(self) -> None:
        self._db.close()
