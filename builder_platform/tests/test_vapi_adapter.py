"""Regression tests for the Vapi SSE contract (report §6.1).

Run: python -m pytest builder_platform/tests/test_vapi_adapter.py -q
"""

import json
import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import vapi_adapter  # noqa: E402


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.delenv("VAPI_SERVER_SECRET", raising=False)
    # SSE-contract tests exercise the wire format, not the brain.
    monkeypatch.setenv("BRAIN_MODE", "skeleton")
    return TestClient(vapi_adapter.app)


def _stream_body(client) -> str:
    resp = client.post(
        "/v1/chat/completions",
        json={"stream": True, "messages": [{"role": "user", "content": "hi"}],
              "call": {"id": "call_test"}},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    return resp.text


def test_every_event_has_two_trailing_newlines(client):
    body = _stream_body(client)
    # Splitting on the required delimiter must reconstruct the whole body:
    # any event missing \n\n would leave a "data:" fragment inside a part.
    parts = body.split("\n\n")
    assert parts[-1] == ""  # body itself ends with the delimiter
    for part in parts[:-1]:
        assert part.startswith("data: "), f"malformed event: {part[:60]!r}"
        assert "\ndata:" not in part, f"missing \\n\\n between events: {part[:60]!r}"


def test_chunk_schema_and_terminators(client):
    body = _stream_body(client)
    events = [p for p in body.split("\n\n") if p]
    assert events[-1] == "data: [DONE]"

    json_events = [json.loads(e[len("data: "):]) for e in events[:-1]]
    for ev in json_events:
        assert ev["object"] == "chat.completion.chunk"
        choice = ev["choices"][0]
        assert choice["index"] == 0
        assert "delta" in choice

    # Second-to-last event is the stop chunk with an empty delta.
    stop = json_events[-1]
    assert stop["choices"][0]["finish_reason"] == "stop"
    assert stop["choices"][0]["delta"] == {}

    # All content chunks precede the stop chunk and carry text.
    content = "".join(
        ev["choices"][0]["delta"].get("content", "") for ev in json_events[:-1]
    )
    assert content.strip()


def test_auth_enforced_when_secret_set(monkeypatch):
    monkeypatch.setenv("VAPI_SERVER_SECRET", "topsecret")
    monkeypatch.setenv("BRAIN_MODE", "skeleton")
    client = TestClient(vapi_adapter.app)
    payload = {"messages": []}
    assert client.post("/v1/chat/completions", json=payload).status_code == 401
    assert client.post("/v1/chat/completions", json=payload,
                       headers={"x-vapi-secret": "wrong"}).status_code == 401
    assert client.post("/v1/chat/completions", json=payload,
                       headers={"x-vapi-secret": "topsecret"}).status_code == 200


def test_brain_stream_failure_still_terminates_sse(client, monkeypatch):
    """A brain that raises mid-stream must still produce a spoken apology, a
    stop chunk, and [DONE] — an unterminated stream freezes Vapi silently."""
    monkeypatch.setenv("BRAIN_MODE", "live")

    async def _exploding_segments(body):
        yield "First bit. "
        raise RuntimeError("brain crashed mid-turn")

    monkeypatch.setattr(vapi_adapter, "_brain_segments", _exploding_segments)
    body = _stream_body(client)
    events = [p for p in body.split("\n\n") if p]
    assert events[-1] == "data: [DONE]"
    json_events = [json.loads(e[len("data: "):]) for e in events[:-1]]
    assert json_events[-1]["choices"][0]["finish_reason"] == "stop"
    content = "".join(ev["choices"][0]["delta"].get("content", "")
                      for ev in json_events[:-1])
    assert "First bit." in content
    assert "Sorry" in content  # the apology chunk, not dead air


def test_non_streaming_fallback(client):
    resp = client.post("/v1/chat/completions", json={"messages": []})
    assert resp.status_code == 200
    data = resp.json()
    assert data["object"] == "chat.completion"
    assert data["choices"][0]["message"]["content"]
    assert data["choices"][0]["finish_reason"] == "stop"
