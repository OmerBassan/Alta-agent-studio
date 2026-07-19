"""builder_platform/app.py regression tests: the HTTP surface around BuilderSession,
using a fake session (no SDK connection, no LLM) so these run offline and fast.

The property under test: /api/chat creates-then-reuses a session per
session_id, streams valid SSE, and never lets a crashed builder turn hang the
stream; /api/agent reflects session state; DELETE actually closes it.
"""

import asyncio
import json
import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import app as app_module  # noqa: E402


class FakeSession:
    """Same public surface as BuilderSession.send/start/close, no SDK/LLM."""

    instances: list["FakeSession"] = []

    def __init__(self, session_id: str, db=None) -> None:
        if session_id == "":
            raise ValueError("empty session_id")
        self.session_id = session_id
        self.project_dir = None
        self.selftest_passed = False
        self.started = False
        self.closed = False
        self.sent: list[str] = []
        self.raise_on_send = False
        self.interrupted = 0
        FakeSession.instances.append(self)

    async def start(self) -> None:
        self.started = True

    async def send(self, message: str):
        self.sent.append(message)
        if self.raise_on_send:
            raise RuntimeError("boom mid-turn")
        yield {"type": "text", "text": f"echo: {message}"}
        yield {"type": "result", "is_error": False,
               "project_dir": None, "selftest_passed": False}

    async def interrupt(self) -> None:
        self.interrupted += 1

    async def close(self) -> None:
        self.closed = True


@pytest.fixture(autouse=True)
def _patch_session(monkeypatch):
    FakeSession.instances.clear()
    monkeypatch.setattr(app_module, "BuilderSession", FakeSession)
    # Auth-independent baseline: chat tests exercise the chat contract, not
    # the consent gate (which has its own tests below).
    monkeypatch.setattr(app_module, "_auth_mode", "api_key")
    app_module._sessions.clear()
    app_module._msg_counts.clear()
    yield
    app_module._sessions.clear()
    app_module._msg_counts.clear()


@pytest.fixture
def client():
    return TestClient(app_module.app)


def _parse_sse(body: str) -> list[dict]:
    events = []
    for line in body.splitlines():
        if line.startswith("data: ") and line != "data: [DONE]":
            events.append(json.loads(line[len("data: "):]))
    return events


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_chat_creates_session_and_streams_events(client):
    resp = client.post("/api/chat", json={"session_id": "s1", "message": "hi"})
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    assert events[0] == {"type": "text", "text": "echo: hi"}
    assert events[-1]["type"] == "result"
    assert resp.text.rstrip().endswith("data: [DONE]")
    assert len(FakeSession.instances) == 1
    assert FakeSession.instances[0].started


def test_chat_reuses_session_across_calls(client):
    client.post("/api/chat", json={"session_id": "s1", "message": "hi"})
    client.post("/api/chat", json={"session_id": "s1", "message": "again"})
    assert len(FakeSession.instances) == 1
    assert FakeSession.instances[0].sent == ["hi", "again"]


def test_chat_different_sessions_are_isolated(client):
    client.post("/api/chat", json={"session_id": "a", "message": "1"})
    client.post("/api/chat", json={"session_id": "b", "message": "2"})
    assert len(FakeSession.instances) == 2


def test_chat_crash_mid_turn_still_terminates_stream(client):
    client.post("/api/chat", json={"session_id": "s1", "message": "prime"})
    FakeSession.instances[0].raise_on_send = True
    resp = client.post("/api/chat", json={"session_id": "s1", "message": "boom"})
    assert resp.status_code == 200
    events = _parse_sse(resp.text)
    assert events and events[-1]["type"] == "error"
    assert resp.text.rstrip().endswith("data: [DONE]")  # never hangs the stream


# --- hard stop (server-side interrupt) ---------------------------------------

def test_stop_interrupts_active_session(client):
    client.post("/api/chat", json={"session_id": "s1", "message": "hi"})
    r = client.post("/api/chat/stop", json={"session_id": "s1"})
    assert r.json() == {"stopped": True}
    assert FakeSession.instances[0].interrupted == 1


def test_stop_unknown_session_is_typed_result_not_500(client):
    r = client.post("/api/chat/stop", json={"session_id": "ghost"})
    assert r.status_code == 200
    assert r.json()["stopped"] is False


def test_logout_interrupts_before_closing(client, tmp_path, monkeypatch):
    monkeypatch.setattr(app_module.env_bootstrap, "ROOT_ENV", tmp_path / ".env")
    client.post("/api/chat", json={"session_id": "s1", "message": "hi"})
    sess = FakeSession.instances[0]
    client.post("/api/auth/logout")
    # the "stop eating my tokens NOW" path preempts the turn, then closes.
    assert sess.interrupted == 1 and sess.closed


# --- code-enforced narration guard -------------------------------------------

def test_narration_guard_drops_internal_markers():
    leaks = [
        "selftest.py has hardcoded HOOK_CHECKS referencing the old flows.",
        "Let me view the full file to rewrite these sections.",
        "Now I'll update prompts.py for the sales voice.",
        "I'll edit config.py and rerun the boilerplate.",
        "This is a much bigger rewrite of selftest.py's demo scenarios.",
    ]
    for t in leaks:
        assert app_module.is_internal_narration(t), t


def test_narration_guard_keeps_client_prose_and_ask_block():
    keep = [
        "Got it — tell me about the internet provider and who it calls.",
        "Your agent is built and tested — press Start call to try it.",
        "We're SOC 2 Type II certified, so your data is safe.",
        "Let me know your top objection and I'll handle it.",
        '```alta:ask\n{"phase":"mission","kind":"approve"}\n```',
    ]
    for t in keep:
        assert not app_module.is_internal_narration(t), t


def test_narration_guard_filters_the_chat_stream(client, monkeypatch):
    async def leaky_send(self, message):
        yield {"type": "text", "text": "Now I'll edit prompts.py."}   # dropped
        yield {"type": "text", "text": "All set — your agent is ready."}  # kept
        yield {"type": "result", "is_error": False,
               "project_dir": None, "selftest_passed": False}
    monkeypatch.setattr(FakeSession, "send", leaky_send)
    resp = client.post("/api/chat", json={"session_id": "s1", "message": "go"})
    texts = [e["text"] for e in _parse_sse(resp.text) if e["type"] == "text"]
    assert texts == ["All set — your agent is ready."]


def test_agent_status_unknown_session(client):
    body = client.get("/api/agent", params={"session_id": "nope"}).json()
    assert body == {"exists": False, "project_dir": None, "selftest_passed": False}


def test_agent_status_reflects_session(client):
    client.post("/api/chat", json={"session_id": "s1", "message": "hi"})
    FakeSession.instances[0].project_dir = "/tmp/AgentX"
    FakeSession.instances[0].selftest_passed = True
    body = client.get("/api/agent", params={"session_id": "s1"}).json()
    assert body == {"exists": True, "project_dir": "/tmp/AgentX", "selftest_passed": True}


def test_delete_session_closes_and_removes(client):
    client.post("/api/chat", json={"session_id": "s1", "message": "hi"})
    resp = client.delete("/api/session/s1")
    assert resp.json() == {"closed": True}
    assert FakeSession.instances[0].closed
    assert client.delete("/api/session/s1").json() == {"closed": False}
    # gone from the registry -> agent status reports unknown again
    body = client.get("/api/agent", params={"session_id": "s1"}).json()
    assert body["exists"] is False


def test_bad_session_id_returns_400(client):
    resp = client.post("/api/chat", json={"session_id": "", "message": "hi"})
    assert resp.status_code == 422 or resp.status_code == 400


def test_probe_disk_resolves_prebuilt_generated_agent(tmp_path, monkeypatch):
    """A shipped agent under Generated_Agents/ (config.py directly inside, one
    level flatter than a workspace) is reachable by folder name, with its
    pass-marker honored — the path that lets a reviewer call the demo agent
    without running a build."""
    import builder as builder_module

    agent = tmp_path / "DemoAgent"
    agent.mkdir()
    for name in ("config.py", "tools.py", "prompts.py", "selftest.py"):
        (agent / name).write_text("# stub\n", encoding="utf-8")
    builder_module._write_pass_marker(agent)  # valid surface-hash marker

    monkeypatch.setattr(app_module, "GENERATED_AGENTS_DIR", tmp_path)
    assert app_module._probe_disk("DemoAgent") == (agent, True)
    # a name with no matching dir stays a clean miss, not a crash
    assert app_module._probe_disk("NoSuchAgent") == (None, False)


# --- recruiter auth: consent gate, setup, logout -----------------------------

def test_chat_refuses_until_auth_configured(client, monkeypatch):
    """Informed consent: with no auth mode chosen, /api/chat must not create a
    session or touch the SDK — the operator's tokens are theirs."""
    monkeypatch.setattr(app_module, "_auth_mode", None)
    resp = client.post("/api/chat", json={"session_id": "s1", "message": "hi"})
    events = _parse_sse(resp.text)
    assert events and events[0]["type"] == "error"
    assert "powered" in events[0]["detail"].lower()
    assert len(FakeSession.instances) == 0


def test_auth_setup_rejects_malformed_key(client, tmp_path, monkeypatch):
    monkeypatch.setattr(app_module.env_bootstrap, "ROOT_ENV", tmp_path / ".env")
    r = client.post("/api/auth/setup", json={"mode": "api_key", "api_key": "not-a-key"})
    assert r.status_code == 400
    assert not (tmp_path / ".env").exists()


def test_auth_setup_and_logout_roundtrip(client, tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    monkeypatch.setattr(app_module.env_bootstrap, "ROOT_ENV", env_file)
    # register env-var restoration with monkeypatch before setup mutates it
    monkeypatch.setenv("ANTHROPIC_API_KEY", os.environ.get("ANTHROPIC_API_KEY", "x"))
    key = "sk-ant-" + "a" * 30

    r = client.post("/api/auth/setup", json={"mode": "api_key", "api_key": key})
    assert r.json() == {"configured": True, "mode": "api_key"}
    assert f"ANTHROPIC_API_KEY={key}" in env_file.read_text(encoding="utf-8")
    assert client.get("/api/auth/status").json()["configured"] is True

    r = client.post("/api/auth/logout")
    assert r.json() == {"configured": False, "mode": None}
    # the key line is commented out, not silently kept
    text = env_file.read_text(encoding="utf-8")
    assert f"ANTHROPIC_API_KEY={key}" not in text
    assert "disconnected" in text
    assert client.get("/api/auth/status").json()["configured"] is False


def test_message_cap_refuses_without_touching_sdk(client, monkeypatch):
    monkeypatch.setattr(app_module, "_MSG_CAP", 2)
    for _ in range(2):
        client.post("/api/chat", json={"session_id": "s1", "message": "hi"})
    resp = client.post("/api/chat", json={"session_id": "s1", "message": "over"})
    events = _parse_sse(resp.text)
    assert "limit" in events[0]["text"].lower()
    assert FakeSession.instances[0].sent == ["hi", "hi"]  # 3rd never reached the SDK


# --- agent credentials panel + zip download ----------------------------------

def _project_on_disk(tmp_path, monkeypatch, sid="envsess"):
    """A built agent on disk only (no live session) — exercises the same
    disk-fallback path a restarted server uses."""
    ws = tmp_path / "ws"
    project = ws / sid / "Agent_20260101_000000"
    project.mkdir(parents=True)
    (project / "config.py").write_text("OPENER = 'hi'\n", encoding="utf-8")
    (project / ".env.example").write_text(
        "OPENAI_API_KEY=\nGMAIL_TOKEN_PATH=\n", encoding="utf-8")
    monkeypatch.setattr(app_module, "WORKSPACES_DIR", ws)
    return project


def test_agent_env_get_masks_values(client, tmp_path, monkeypatch):
    project = _project_on_disk(tmp_path, monkeypatch)
    (project / ".env").write_text(
        "OPENAI_API_KEY=sk-live-abcdef123456\n", encoding="utf-8")
    body = client.get("/api/agent/env", params={"session_id": "envsess"}).json()
    keys = {k["key"]: k for k in body["keys"]}
    assert set(keys) == {"OPENAI_API_KEY", "GMAIL_TOKEN_PATH"}
    assert keys["OPENAI_API_KEY"]["set"] is True
    assert keys["OPENAI_API_KEY"]["masked"] == "…3456"
    assert keys["GMAIL_TOKEN_PATH"]["set"] is False
    assert "sk-live-abcdef123456" not in json.dumps(body)  # raw value never leaves


def test_agent_env_post_rejects_unknown_key(client, tmp_path, monkeypatch):
    _project_on_disk(tmp_path, monkeypatch)
    r = client.post("/api/agent/env", json={
        "session_id": "envsess", "values": {"EVIL_KEY": "x"}})
    assert r.status_code == 400
    assert "EVIL_KEY" in r.json()["detail"]


def test_agent_env_post_writes_allowlisted_key(client, tmp_path, monkeypatch):
    project = _project_on_disk(tmp_path, monkeypatch)
    r = client.post("/api/agent/env", json={
        "session_id": "envsess", "values": {"OPENAI_API_KEY": "sk-new-123"}})
    assert r.status_code == 200
    assert "OPENAI_API_KEY=sk-new-123" in (project / ".env").read_text(encoding="utf-8")


def test_agent_download_returns_zip_with_env(client, tmp_path, monkeypatch):
    import io
    import zipfile
    project = _project_on_disk(tmp_path, monkeypatch)
    (project / ".env").write_text("OPENAI_API_KEY=sk-x\n", encoding="utf-8")
    r = client.get("/api/agent/download", params={"session_id": "envsess"})
    assert r.status_code == 200
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    names = zf.namelist()
    assert any(n.endswith("config.py") for n in names)
    assert any(n.endswith(".env") for n in names)   # the takeaway includes creds


def test_agent_env_404_when_no_project(client, tmp_path, monkeypatch):
    monkeypatch.setattr(app_module, "WORKSPACES_DIR", tmp_path / "empty")
    assert client.get("/api/agent/env",
                      params={"session_id": "ghost"}).status_code == 404
