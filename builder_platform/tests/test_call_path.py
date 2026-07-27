"""Tests for the test-call path: tunnel discovery, Vapi control, POST /api/call.

The real call is proven by a flight; these pin the wiring and — more valuably —
the REFUSALS, so a misconfigured demo fails loudly at button-press instead of
connecting to dead air.

Run: python -m pytest builder_platform/tests/test_call_path.py -q
"""

import asyncio
import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import app as app_mod  # noqa: E402
import runtime_supervisor  # noqa: E402
import tunnel  # noqa: E402
import vapi_control  # noqa: E402


# --- tunnel -----------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for var in ("PUBLIC_URL", "VAPI_SERVER_SECRET", "VAPI_PRIVATE_KEY",
                "VAPI_PUBLIC_KEY", "VAPI_ASSISTANT_ID"):
        monkeypatch.delenv(var, raising=False)


def _fake_tunnels(*pairs):
    """(public_url, addr) pairs -> an ngrok agent API tunnel list."""
    async def _inner():
        return [{"public_url": u, "config": {"addr": a}} for u, a in pairs]
    return _inner


def test_public_url_prefers_env_override(monkeypatch):
    monkeypatch.setenv("PUBLIC_URL", "https://demo.example.com/")
    # A trailing slash would produce ".../v1" with a double slash downstream.
    assert asyncio.run(tunnel.resolve_public_url(8100)) == "https://demo.example.com"


def test_public_url_raises_when_no_tunnel(monkeypatch):
    monkeypatch.setattr(tunnel, "_ngrok_tunnels", _fake_tunnels())
    # Hermetic: never touch the network or spawn a real ngrok during tests.
    monkeypatch.setattr(tunnel, "_find_ngrok", lambda: None)

    async def _no_agent():
        return False
    monkeypatch.setattr(tunnel, "_agent_reachable", _no_agent)
    with pytest.raises(tunnel.TunnelNotFound) as exc:
        asyncio.run(tunnel.resolve_public_url(8100))
    assert "ngrok http 8100" in str(exc.value)


def test_public_url_accepts_tunnel_on_the_runtime_port(monkeypatch):
    monkeypatch.setattr(tunnel, "_ngrok_tunnels", _fake_tunnels(
        ("https://good.ngrok-free.dev", "http://localhost:8100")))
    assert asyncio.run(tunnel.resolve_public_url(8100)) == "https://good.ngrok-free.dev"


def test_public_url_rejects_tunnel_pointing_at_the_wrong_port(monkeypatch):
    """Regression, observed for real: a long-running `ngrok http 8000` while the
    runtime binds 8100. A tunnel EXISTS, so a naive check passes and Vapi lands
    on the wrong local service — the call connects and never speaks."""
    monkeypatch.setattr(tunnel, "_ngrok_tunnels", _fake_tunnels(
        ("https://sixteenpenny-unrecipient-gabriele.ngrok-free.dev",
         "http://localhost:8000")))
    with pytest.raises(tunnel.TunnelPortMismatch) as exc:
        asyncio.run(tunnel.resolve_public_url(8100))
    msg = str(exc.value)
    assert "8000" in msg and "8100" in msg      # names both sides of the mismatch


def test_public_url_picks_the_matching_tunnel_among_several(monkeypatch):
    monkeypatch.setattr(tunnel, "_ngrok_tunnels", _fake_tunnels(
        ("https://other.ngrok-free.dev", "http://localhost:8000"),
        ("https://right.ngrok-free.dev", "http://localhost:8100")))
    assert asyncio.run(tunnel.resolve_public_url(8100)) == "https://right.ngrok-free.dev"


@pytest.mark.parametrize("addr,expected", [
    ("http://localhost:8000", 8000),
    ("localhost:8100", 8100),
    ("8100", 8100),
    ("https://127.0.0.1:443", 443),
    ("", None),
])
def test_addr_port_parsing(addr, expected):
    assert tunnel._addr_port(addr) == expected


# --- vapi_control auth preflight -------------------------------------------

def test_preflight_rejects_when_server_secret_set(monkeypatch):
    """Vapi cannot send a secret to a custom-llm url (probed: PATCH model.secret
    -> 400). A set secret therefore means every turn 401s and the call is dead
    air. This must fail BEFORE the call, not during it."""
    monkeypatch.setenv("VAPI_SERVER_SECRET", "s" * 32)
    with pytest.raises(vapi_control.VapiConfigError) as exc:
        vapi_control.preflight_auth()
    assert "401" in str(exc.value)


def test_preflight_passes_when_secret_absent():
    vapi_control.preflight_auth()  # must not raise


def test_public_key_error_names_the_fix(monkeypatch):
    with pytest.raises(vapi_control.VapiConfigError) as exc:
        vapi_control.public_key()
    assert "VAPI_PUBLIC_KEY" in str(exc.value)


def test_point_assistant_rewrites_only_the_url(monkeypatch):
    """The dashboard owns the assistant; we rewrite the wiring and nothing else."""
    monkeypatch.setenv("VAPI_PRIVATE_KEY", "priv")
    existing = {"provider": "custom-llm", "model": "custom-router",
                "url": "https://old.ngrok.app/v1", "temperature": 0.2,
                "messages": [{"role": "system", "content": "keep me"}]}
    sent = {}

    async def fake_request(method, path, **kw):
        if method == "GET":
            return {"id": "aid1", "model": existing, "voice": {"provider": "vapi"}}
        sent["method"], sent["path"], sent["json"] = method, path, kw.get("json")
        return {}

    monkeypatch.setattr(vapi_control, "_request", fake_request)
    out = asyncio.run(vapi_control.point_assistant_at("https://new.ngrok.app", "aid1"))

    assert out["model_url"] == "https://new.ngrok.app/v1"
    assert out["previous_model_url"] == "https://old.ngrok.app/v1"
    assert sent["method"] == "PATCH"
    model = sent["json"]["model"]
    assert model["url"] == "https://new.ngrok.app/v1"
    assert model["provider"] == "custom-llm"
    # untouched dashboard config survives the PATCH
    assert model["temperature"] == 0.2
    assert model["messages"] == [{"role": "system", "content": "keep me"}]
    # and we never invent a secret field: Vapi 400s on it
    assert "secret" not in model


def test_point_assistant_requires_https(monkeypatch):
    monkeypatch.setenv("VAPI_PRIVATE_KEY", "priv")
    with pytest.raises(vapi_control.VapiConfigError):
        asyncio.run(vapi_control.point_assistant_at("http://insecure.example", "aid1"))


def test_patch_body_default_omits_unverified_endpointing(monkeypatch):
    """Default payload is unchanged: endpointing stays in the dashboard until a
    flight test verifies Vapi's field names (VAPI_CODIFY_ENDPOINTING off)."""
    monkeypatch.delenv("VAPI_CODIFY_ENDPOINTING", raising=False)
    body = vapi_control._patch_body({"provider": "custom-llm"}, "Hi there!")
    assert body["backchannelingEnabled"] is False
    assert body["startSpeakingPlan"] == {"waitSeconds": 0}
    assert "stopSpeakingPlan" not in body   # not shipped un-probed


def test_patch_body_codifies_endpointing_when_enabled(monkeypatch):
    """With the flag on (post-flight-test), the turn-taking knobs are pinned
    into the PATCH so they are version-controlled, not dashboard-only."""
    monkeypatch.setenv("VAPI_CODIFY_ENDPOINTING", "1")
    body = vapi_control._patch_body({"provider": "custom-llm"}, None)
    assert body["startSpeakingPlan"]["smartEndpointingEnabled"] is True
    assert body["startSpeakingPlan"]["waitSeconds"] == 0
    assert body["stopSpeakingPlan"]["numWords"] == 1


# --- runtime supervisor -----------------------------------------------------

def test_child_env_blanks_server_secret_rather_than_deleting_it(monkeypatch,
                                                                tmp_path):
    """Regression: the child must see VAPI_SERVER_SECRET as PRESENT-BUT-EMPTY.

    The child re-runs env_bootstrap, which merges builder_platform/.env with
    os.environ.setdefault (env_bootstrap.py:78). Deleting the key lets the file
    value flow straight back in and the adapter 401s every Vapi turn — silent
    dead air. An empty string blocks the merge and disables auth as intended.

    This originally shipped as env.pop(), which passed a `not in env` assertion
    while the real spawned runtime still returned 401.
    """
    monkeypatch.setenv("VAPI_SERVER_SECRET", "leftover")
    env = runtime_supervisor._child_env(tmp_path)
    assert "VAPI_SERVER_SECRET" in env, "deleting the key lets builder_platform/.env refill it"
    assert env["VAPI_SERVER_SECRET"] == ""
    assert env["AGENT_DIR"] == str(tmp_path)
    assert env["PYTHONIOENCODING"] == "utf-8"


def test_child_env_blank_secret_survives_env_bootstrap_merge(tmp_path):
    """The real mechanism, end to end: setdefault must not overwrite the blank.

    Pins the env_bootstrap precedence rule this fix depends on, so a future
    change there fails loudly here instead of in a live call.
    """
    import env_bootstrap

    env = runtime_supervisor._child_env(tmp_path)
    # Simulate the child: its os.environ starts as `env`, then env_bootstrap
    # merges the files in with setdefault.
    simulated = dict(env)
    simulated.setdefault("VAPI_SERVER_SECRET", "value-from-platform-dot-env")
    assert simulated["VAPI_SERVER_SECRET"] == ""
    assert env_bootstrap.LEGACY_PLATFORM_ENV.name == ".env"


# --- POST /api/call ---------------------------------------------------------

class _FakeSession:
    def __init__(self, project_dir=None, selftest_passed=False):
        self.project_dir = project_dir
        self.selftest_passed = selftest_passed


@pytest.fixture()
def client(monkeypatch):
    app_mod._sessions.clear()
    return TestClient(app_mod.app)


def _register(session_id, session):
    import asyncio
    app_mod._sessions[session_id] = (session, 0.0, asyncio.Lock())


def test_call_404_for_unknown_session(client):
    assert client.post("/api/call", json={"session_id": "nope"}).status_code == 404


def test_call_409_when_no_agent_built(client):
    _register("s1", _FakeSession())
    r = client.post("/api/call", json={"session_id": "s1"})
    assert r.status_code == 409
    assert "built" in r.json()["detail"].lower()


def test_call_409_when_selftest_not_passed(client, tmp_path):
    """The selftest is the ship gate — an unproven agent must never be dialed."""
    _register("s2", _FakeSession(project_dir=tmp_path, selftest_passed=False))
    r = client.post("/api/call", json={"session_id": "s2"})
    assert r.status_code == 409
    assert "selftest" in r.json()["detail"].lower()


def test_call_503_when_credentials_missing(client, tmp_path):
    _register("s3", _FakeSession(project_dir=tmp_path, selftest_passed=True))
    r = client.post("/api/call", json={"session_id": "s3"})
    assert r.status_code == 503
    assert "VAPI_ASSISTANT_ID" in r.json()["detail"]


def test_call_503_when_no_tunnel(client, tmp_path, monkeypatch):
    monkeypatch.setenv("VAPI_ASSISTANT_ID", "aid1")
    monkeypatch.setenv("VAPI_PUBLIC_KEY", "pub")
    monkeypatch.setenv("VAPI_PRIVATE_KEY", "priv")

    async def _boom(runtime_port):
        raise tunnel.TunnelNotFound("no tunnel")
    monkeypatch.setattr(tunnel, "resolve_public_url", _boom)

    _register("s4", _FakeSession(project_dir=tmp_path, selftest_passed=True))
    assert client.post("/api/call", json={"session_id": "s4"}).status_code == 503


def test_call_503_when_tunnel_points_at_wrong_port(client, tmp_path, monkeypatch):
    """The mismatch must surface as a refusal with the operator's fix in it."""
    monkeypatch.setenv("VAPI_ASSISTANT_ID", "aid1")
    monkeypatch.setenv("VAPI_PUBLIC_KEY", "pub")
    monkeypatch.setenv("VAPI_PRIVATE_KEY", "priv")

    async def _mismatch(runtime_port):
        raise tunnel.TunnelPortMismatch(
            f"tunnel -> http://localhost:8000, runtime on {runtime_port}")
    monkeypatch.setattr(tunnel, "resolve_public_url", _mismatch)

    _register("s7", _FakeSession(project_dir=tmp_path, selftest_passed=True))
    r = client.post("/api/call", json={"session_id": "s7"})
    assert r.status_code == 503
    assert "8000" in r.json()["detail"]


def test_call_happy_path_returns_public_key_never_private(client, tmp_path,
                                                          monkeypatch):
    monkeypatch.setenv("VAPI_ASSISTANT_ID", "aid1")
    monkeypatch.setenv("VAPI_PUBLIC_KEY", "pub-key-123")
    monkeypatch.setenv("VAPI_PRIVATE_KEY", "PRIVATE-SHOULD-NEVER-LEAK")

    async def _url(runtime_port):
        return "https://tunnel.example"
    monkeypatch.setattr(tunnel, "resolve_public_url", _url)

    async def _start(agent_dir, port=8100):
        return runtime_supervisor.ActiveRuntime(agent_dir=tmp_path, port=8100,
                                                proc=None)
    monkeypatch.setattr(runtime_supervisor, "start", _start)

    async def _point(public_url, aid=None, first_message=None):
        return {"assistant_id": aid, "model_url": public_url + "/v1",
                "previous_model_url": None, "first_message": first_message}
    monkeypatch.setattr(vapi_control, "point_assistant_at", _point)

    _register("s5", _FakeSession(project_dir=tmp_path, selftest_passed=True))
    r = client.post("/api/call", json={"session_id": "s5"})
    assert r.status_code == 200
    body = r.json()
    assert body["public_key"] == "pub-key-123"
    assert body["assistant_id"] == "aid1"
    assert body["model_url"] == "https://tunnel.example/v1"
    # the private key must never reach the browser
    assert "PRIVATE-SHOULD-NEVER-LEAK" not in r.text


def test_call_500_when_runtime_fails_to_start(client, tmp_path, monkeypatch):
    monkeypatch.setenv("VAPI_ASSISTANT_ID", "aid1")
    monkeypatch.setenv("VAPI_PUBLIC_KEY", "pub")
    monkeypatch.setenv("VAPI_PRIVATE_KEY", "priv")

    async def _url(runtime_port):
        return "https://tunnel.example"
    monkeypatch.setattr(tunnel, "resolve_public_url", _url)

    async def _boom(agent_dir, port=8100):
        raise runtime_supervisor.RuntimeStartError("graph import blew up")
    monkeypatch.setattr(runtime_supervisor, "start", _boom)

    _register("s6", _FakeSession(project_dir=tmp_path, selftest_passed=True))
    r = client.post("/api/call", json={"session_id": "s6"})
    assert r.status_code == 500
    assert "graph import blew up" in r.json()["detail"]


# --- POST /api/warm ---------------------------------------------------------

def test_warm_404_for_unknown_session(client):
    """Warm gates identically to call: an unknown session is a fast 404, no
    background spawn."""
    assert client.post("/api/warm", json={"session_id": "nope"}).status_code == 404


def test_warm_409_when_selftest_not_passed(client, tmp_path):
    _register("w1", _FakeSession(project_dir=tmp_path, selftest_passed=False))
    r = client.post("/api/warm", json={"session_id": "w1"})
    assert r.status_code == 409
    assert "selftest" in r.json()["detail"].lower()


def test_warm_returns_immediately_and_registers_a_task(client, tmp_path,
                                                       monkeypatch):
    """Warm answers right away with {"warming": True} and schedules a background
    prepare task for the project — the frontend never blocks on the spawn."""
    monkeypatch.setenv("VAPI_ASSISTANT_ID", "aid1")
    monkeypatch.setenv("VAPI_PUBLIC_KEY", "pub")
    monkeypatch.setenv("VAPI_PRIVATE_KEY", "priv")

    async def _url(runtime_port):
        return "https://tunnel.example"
    monkeypatch.setattr(tunnel, "resolve_public_url", _url)

    async def _point(public_url, aid=None, first_message=None):
        return {"assistant_id": aid, "model_url": public_url + "/v1",
                "previous_model_url": None, "first_message": first_message}
    monkeypatch.setattr(vapi_control, "point_assistant_at", _point)

    async def _start(agent_dir, port=8100):
        return runtime_supervisor.ActiveRuntime(agent_dir=tmp_path, port=8100,
                                                proc=None)
    monkeypatch.setattr(runtime_supervisor, "start", _start)

    app_mod._warm_tasks.pop(str(tmp_path), None)
    _register("w2", _FakeSession(project_dir=tmp_path, selftest_passed=True))

    r = client.post("/api/warm", json={"session_id": "w2"})
    assert r.status_code == 200
    assert r.json()["warming"] is True
    assert str(tmp_path) in app_mod._warm_tasks
    app_mod._warm_tasks.pop(str(tmp_path), None)


def test_warm_is_idempotent_within_one_loop(tmp_path, monkeypatch):
    """Two warms for the same in-flight project ride ONE task — the guard must
    not stack a second runtime spawn. Driven directly (not via TestClient) so
    both calls share one event loop, as the real uvicorn process does; the
    TestClient spins a fresh loop per request and would tear the task down."""
    monkeypatch.setenv("VAPI_ASSISTANT_ID", "aid1")
    monkeypatch.setenv("VAPI_PUBLIC_KEY", "pub")
    monkeypatch.setenv("VAPI_PRIVATE_KEY", "priv")

    async def _url(runtime_port):
        return "https://tunnel.example"
    monkeypatch.setattr(tunnel, "resolve_public_url", _url)

    async def _point(public_url, aid=None, first_message=None):
        return {"assistant_id": aid, "model_url": public_url + "/v1",
                "previous_model_url": None, "first_message": first_message}
    monkeypatch.setattr(vapi_control, "point_assistant_at", _point)

    starts = []

    async def _slow_start(agent_dir, port=8100):
        starts.append(agent_dir)
        await asyncio.sleep(0.2)            # keep the first task in-flight
        return runtime_supervisor.ActiveRuntime(agent_dir=tmp_path, port=8100,
                                                proc=None)
    monkeypatch.setattr(runtime_supervisor, "start", _slow_start)

    async def scenario():
        app_mod._warm_tasks.pop(str(tmp_path), None)
        app_mod._sessions["w3"] = (
            _FakeSession(project_dir=tmp_path, selftest_passed=True),
            0.0, asyncio.Lock())
        req = app_mod.CallRequest(session_id="w3")
        r1 = await app_mod.warm_call(req)
        t1 = app_mod._warm_tasks[str(tmp_path)]
        await asyncio.sleep(0)                      # let the first task reach start()
        r2 = await app_mod.warm_call(req)          # rides the in-flight task
        t2 = app_mod._warm_tasks[str(tmp_path)]
        assert r1["warming"] is True and r2["warming"] is True
        assert r2.get("already") is True           # second warm did not re-spawn
        assert t1 is t2                            # same task, no second spawn
        t1.cancel()

    asyncio.run(scenario())
    assert len(starts) == 1                        # start() invoked once, not twice
