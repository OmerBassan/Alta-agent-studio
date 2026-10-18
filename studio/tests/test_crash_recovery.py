"""Story 1.11: an in-flight episode survives a crash mid-turn.

A child process runs one turn of a booking and is killed with ``os._exit`` right
after its Nth committed journal write (no cleanup, no rollback beyond SQLite's
own). A fresh process — new store and Core objects on the same database file,
nothing carried in memory — then continues the conversation. The system of
record is a file, shared by both processes, so a write that landed before the
crash is visible after it.

Run directly, this module is the child: ``python test_crash_recovery.py
<db> <calendar> <crash_after_commit> <crash_in_adapter> <message_id> <text>``.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))

from studio.agent.deterministic import DeterministicAgent  # noqa: E402
from studio.core import Core, EpisodeStore, InboundMessage, SpecRegistry  # noqa: E402
from studio.extensions.simulated import SimulatedCalendar  # noqa: E402
from studio.spec import compile_specification, load_specification  # noqa: E402

DENTAL = ROOT / "studio" / "businesses" / "dental" / "specification.toml"
TENANT = "bright-smile-dental"
CONVERSATION = "crash-c1"
FIRST = "Hi, I'd like to book a check-up on Monday at 9am. My name is Ada Lovelace, ada@example.com"
TODAY = date(2026, 10, 13)
CRASHED = 97  # a distinctive exit code: an ordinary failure in the child exits 1, never this


class FileCalendar:
    """The simulated calendar, persisted to a JSON file between processes."""

    name = "calendar"

    def __init__(self, path: Path, crash_in_adapter: bool = False):
        self.path, self.crash_in_adapter = path, crash_in_adapter

    def _load(self) -> SimulatedCalendar:
        cal = SimulatedCalendar()
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))
            cal.bookings = {tuple(k.split("|", 1)): v for k, v in data["bookings"].items()}
            cal.executions = Counter({tuple(k.split("|", 1)): v for k, v in data["executions"].items()})
        return cal

    def _save(self, cal: SimulatedCalendar) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"bookings": {"|".join(k): v for k, v in cal.bookings.items()},
                                   "executions": {"|".join(k): v for k, v in cal.executions.items()}}),
                       encoding="utf-8")
        os.replace(tmp, self.path)

    def read(self, *a):
        return self._load().read(*a)

    def effect(self, *a):
        cal = self._load()
        result = cal.effect(*a)
        self._save(cal)
        if self.crash_in_adapter:  # the write landed; the process dies before the Core records it
            os._exit(CRASHED)
        return result

    def read_back(self, *a):
        return self._load().read_back(*a)

    def executions(self) -> int:
        return sum(self._load().executions.values())


class _CrashingConnection:
    """Delegates to the real connection; dies right after the Nth COMMIT."""

    def __init__(self, conn, crash_after: int):
        self._conn, self._left = conn, crash_after

    def execute(self, sql, *params):
        cursor = self._conn.execute(sql, *params)
        if sql.strip().upper() == "COMMIT":
            self._left -= 1
            if self._left == 0:
                os._exit(CRASHED)
        return cursor

    def __getattr__(self, name):
        return getattr(self._conn, name)


def _core(db: Path, calendar: FileCalendar) -> tuple[Core, EpisodeStore]:
    registry = SpecRegistry()
    registry.register(compile_specification(load_specification(DENTAL)))
    store = EpisodeStore(db, clock=lambda: datetime(2026, 10, 13, 9, 0, tzinfo=timezone.utc))
    return Core(registry, store, DeterministicAgent(today=lambda: TODAY), {"calendar": calendar}), store


def send(db: Path, cal: Path, message_id: str, text: str, crash_after: int = 0, crash_in_adapter: bool = False):
    core, store = _core(db, FileCalendar(cal, crash_in_adapter))
    if crash_after:
        store._db = _CrashingConnection(store._db, crash_after)
    try:
        return asyncio.run(core.handle(InboundMessage(tenant=TENANT, conversation_key=CONVERSATION,
                                                      message_id=message_id, text=text)))
    finally:
        store.close()


def _child(db, cal, crash_after, crash_in_adapter, message_id, text) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, __file__, str(db), str(cal), str(crash_after), str(int(crash_in_adapter)),
                           message_id, text], capture_output=True, text=True, cwd=ROOT)


def _record(db: Path) -> dict:
    store = EpisodeStore(db)
    try:
        episodes = store.episodes(TENANT)
        steps = [(e.episode_id, s["seq"]) for e in episodes for s in store.steps(TENANT, e.episode_id)]
        evidence = [ev for e in episodes for ev in store.evidence(TENANT, e.episode_id)]
        started = [r for e in episodes for r in store.started_effects(TENANT, e.episode_id)]
        last_steps = {e.episode_id: store.steps(TENANT, e.episode_id)[-1] for e in episodes}
        verified_at = [ev["step_seq"] for ev in evidence if ev["kind"] == "effect_verified"]
        verified_keys = Counter(ev["payload"].get("idempotency_key") for ev in evidence if ev["kind"] == "effect_verified")
        egress_at = [s["seq"] for e in episodes for s in store.steps(TENANT, e.episode_id) if s["kind"] == "egress"]
        effects = store._all("SELECT * FROM effects")
        return {"lifecycles": [e.lifecycle for e in episodes], "close_reasons": [e.close_reason for e in episodes], "steps": steps, "started": started,
                "verified": sum(1 for ev in evidence if ev["kind"] == "effect_verified"),
                "evidence_kinds": [ev["kind"] for ev in evidence], "last_steps": last_steps,
                "effects": len(effects), "verified_keys": verified_keys,
                "reply_pending": bool(verified_at) and not any(q > max(verified_at) for q in egress_at)}
    finally:
        store.close()


def _fresh(tmp_path: Path, name: str) -> tuple[Path, Path]:
    folder = tmp_path / name
    folder.mkdir()
    db, cal = folder / "episodes.db", folder / "calendar.json"
    out = send(db, cal, "m1", FIRST)  # turn 1, no crash: the agent proposes the booking for confirmation
    assert out.lifecycle == "active"
    return db, cal


def _commits_in_second_turn(tmp_path: Path) -> int:
    db, cal = _fresh(tmp_path, "count")
    core, store = _core(db, FileCalendar(cal))
    counter = {"n": 0}

    class Counting(_CrashingConnection):
        def execute(self, sql, *params):
            if sql.strip().upper() == "COMMIT":
                counter["n"] += 1
            return self._conn.execute(sql, *params)

    store._db = Counting(store._db, 0)
    asyncio.run(core.handle(InboundMessage(tenant=TENANT, conversation_key=CONVERSATION, message_id="m2",
                                           text="yes")))
    store.close()
    assert FileCalendar(cal).executions() == 1, "the uninterrupted second turn must book exactly once"
    return counter["n"]


def _settled(db: Path, cal: Path) -> bool:
    rec = _record(db)
    booked = FileCalendar(cal).executions() == 1 and rec["verified"] == 1
    handed_over = FileCalendar(cal).executions() == 0 and "escalated" in rec["close_reasons"]
    return booked or handed_over


def _continue_until_settled(db: Path, cal: Path) -> None:
    """The requester keeps answering 'yes' in a new process until the case is settled: booked exactly once, or —
    when the interrupted booking could not be confirmed — handed to a person. It must never land twice."""
    for i in range(3):
        send(db, cal, f"m-after-{i}", "yes")
        assert FileCalendar(cal).executions() <= 1, "an effect was executed again after the crash"
        if _settled(db, cal):
            return
    raise AssertionError("three more 'yes' turns neither booked nor handed the case over")


def _assert_consistent(db: Path, cal: Path, where: str) -> None:
    rec = _record(db)
    assert rec["started"] == [], f"{where}: an orphan effect remains"
    assert len(rec["steps"]) == len(set(rec["steps"])), f"{where}: a duplicate step"
    assert all(lc in ("active", "pending", "closed") for lc in rec["lifecycles"]), where
    assert FileCalendar(cal).executions() <= 1, f"{where}: executions {FileCalendar(cal).executions()}"
    assert rec["verified"] == FileCalendar(cal).executions(),         f"{where}: {rec['verified']} effect_verified for {FileCalendar(cal).executions()} executions"
    assert all(n == 1 for n in rec["verified_keys"].values()), f"{where}: one effect verified twice"
    assert _settled(db, cal), f"{where}: neither booked nor handed over"


def test_a_crash_at_every_journal_boundary_of_a_turn_is_recoverable(tmp_path):
    total = _commits_in_second_turn(tmp_path)
    assert total >= 5, f"the booking turn makes only {total} commits; the boundaries are not being exercised"
    seen = Counter()
    for n in range(1, total + 1):
        db, cal = _fresh(tmp_path, f"crash-{n}")
        child = _child(db, cal, n, False, "m2", "yes")
        assert child.returncode == CRASHED, f"commit {n}: the child did not crash ({child.returncode}): {child.stderr[-400:]}"
        before = _record(db)
        # A decision journaled but not yet authorized (no effect row): it is never acted on (AC 2).
        for last in before["last_steps"].values():
            if last["kind"] == "decision" and (last["payload"]["request"] or {}).get("kind") == "effect" \
                    and before["effects"] == 0:
                seen["decision_unauthorised"] += 1
                assert FileCalendar(cal).executions() == 0, f"commit {n}: an unauthorised decision was acted on"
        # An effect executed and evidenced, its reply not yet journaled (AC 1).
        if before["verified"] == 1 and before["reply_pending"]:
            seen["effect_evidenced"] += 1
        _continue_until_settled(db, cal)
        _assert_consistent(db, cal, f"crash after commit {n} of {total}")
    assert seen["decision_unauthorised"] >= 1, "no boundary left a decision journaled but unauthorised"
    assert seen["effect_evidenced"] >= 1, "no boundary left an effect evidenced before its reply"


def test_a_crash_after_the_system_wrote_but_before_the_core_recorded_it(tmp_path):
    db, cal = _fresh(tmp_path, "adapter")
    child = _child(db, cal, 0, True, "m2", "yes")
    assert child.returncode == CRASHED, child.stderr[-400:]
    rec = _record(db)
    assert len(rec["started"]) == 1 and FileCalendar(cal).executions() == 1  # the orphan the story is about
    send(db, cal, "m3", "hello?")
    rec = _record(db)
    assert rec["started"] == [] and rec["verified"] == 1
    assert FileCalendar(cal).executions() == 1, "reconciliation executed the effect again"
    _continue_until_settled(db, cal)
    _assert_consistent(db, cal, "crash inside the adapter call")


if __name__ == "__main__":
    _db, _cal, _after, _in_adapter, _mid, _text = sys.argv[1:7]
    send(Path(_db), Path(_cal), _mid, _text, crash_after=int(_after), crash_in_adapter=_in_adapter == "1")
    sys.exit(0)
