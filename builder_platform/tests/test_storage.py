"""
Alta Builder Platform -- Storage Layer Tests
Collected by the suite:  python -m pytest builder_platform/tests/
Uses :memory: SQLite -- no files created, no cleanup needed.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from storage.db_manager import StorageManager


def _fresh_db() -> StorageManager:
    db = StorageManager(":memory:")
    db.init_db()
    return db


def test_init_db_idempotent():
    db = _fresh_db()
    db.init_db()


def test_create_session():
    db = _fresh_db()
    s = db.create_session("web_abc123")
    assert s["session_id"] == "web_abc123"
    assert s["active"] == 1


def test_create_session_idempotent():
    db = _fresh_db()
    s1 = db.create_session("web_abc123")
    s2 = db.create_session("web_abc123")
    assert s1["session_id"] == s2["session_id"]
    assert s2["last_active"] >= s1["last_active"]


def test_get_session():
    db = _fresh_db()
    assert db.get_session("nonexistent") is None
    db.create_session("web_xyz")
    assert db.get_session("web_xyz")["session_id"] == "web_xyz"


def test_close_session():
    db = _fresh_db()
    db.create_session("web_close")
    assert db.get_session("web_close")["active"] == 1
    db.close_session("web_close")
    assert db.get_session("web_close")["active"] == 0


def test_register_and_get_agent():
    db = _fresh_db()
    db.create_session("web_agent")
    aid = db.register_agent("web_agent", "TestBot", "/tmp/TestBot", "prompt")
    assert isinstance(aid, int)
    agent = db.get_agent(aid)
    assert agent["agent_name"] == "TestBot"
    assert agent["selftest_status"] == "pending"


def test_update_selftest():
    db = _fresh_db()
    db.create_session("web_st")
    aid = db.register_agent("web_st", "Bot", "/tmp/Bot", None)
    db.update_selftest(aid, "passed")
    assert db.get_agent(aid)["selftest_status"] == "passed"
    try:
        db.update_selftest(aid, "exploded")
        assert False, "Should have raised"
    except ValueError:
        pass


def test_latest_agent():
    db = _fresh_db()
    db.create_session("web_lat")
    assert db.latest_agent("web_lat") is None
    db.register_agent("web_lat", "First", "/a", None)
    db.register_agent("web_lat", "Second", "/b", None)
    assert db.latest_agent("web_lat")["agent_name"] == "Second"


def test_list_agents_newest_first():
    db = _fresh_db()
    db.create_session("web_list")
    db.register_agent("web_list", "A", "/a", None)
    db.register_agent("web_list", "B", "/b", None)
    agents = db.list_agents("web_list")
    assert len(agents) == 2
    assert agents[0]["agent_name"] == "B"
