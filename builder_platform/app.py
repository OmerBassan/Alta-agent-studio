# -*- coding: utf-8 -*-
"""Platform API: the FastAPI app fronting the AI Builder (Day 2 PM / Day 3).

Endpoints (file upload still lands later, per the plan's cut-line order):

  POST /api/chat   {session_id, message} -> SSE stream of builder turn events
                    (text chunks, tool-call markers, a final result event).
                    Creates the BuilderSession on first use; reuses it after.
  POST /api/call   {session_id} -> spawns the voice runtime for that session's
                    generated agent, points the Vapi assistant at this machine's
                    tunnel, and returns {public_key, assistant_id} for the
                    browser to open a web call. Refuses unless the agent's
                    selftest PASSed.
  GET  /api/agent   {session_id} -> the session's generated-project status
                    (none yet / instantiated / selftest verdict) for the
                    config-display card.
  DELETE /api/session/{session_id} -> disconnect + drop a session (used by
                    the UI's "start over" action).
  GET  /health

One process, one in-memory session registry — the plan's subprocess-per-agent
model applies to the SPOKEN runtime (runtime.py/vapi_adapter.py), not to the
builder: builder sessions are cheap SDK client connections, not compiled
graphs, so they live in this process.
"""

from __future__ import annotations

import asyncio
import io
import json
import logging
import os
import re
import time
import zipfile
from pathlib import Path
from typing import AsyncIterator, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response, StreamingResponse
from pydantic import BaseModel, Field

import env_bootstrap  # noqa: F401 — loads repo-root .env into os.environ on import
import runtime_supervisor
import tunnel
import vapi_control
from builder import (
    WORKSPACES_DIR,
    GENERATED_AGENTS_DIR,
    BuilderSession,
    _MARKER_NAME,
    discover_project,
    has_persisted_pass,
)
from storage import StorageManager

app = FastAPI(title="Alta builder platform")

# Backend event log: one INFO line for the major lifecycle moments (new session,
# agent built/re-proven, call started). Level is env-overridable; basicConfig is
# a no-op if the host already configured logging, so it never fights a parent.
logging.basicConfig(
    level=os.environ.get("ALTA_LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("alta")

_STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(os.path.join(_STATIC_DIR, "index.html"))

# session_id -> (BuilderSession, last_used_epoch, lock). The lock serializes
# concurrent requests on ONE session (the SDK client is not safe for two
# in-flight queries) without blocking other sessions.
_sessions: dict[str, tuple[BuilderSession, float, asyncio.Lock]] = {}

SESSION_IDLE_TTL_S = int(os.environ.get("BUILDER_SESSION_IDLE_TTL_S", str(2 * 60 * 60)))

# Persistent session/agent history (SQLite, stdlib-only). Bookkeeping layer:
# the DISK pass marker remains the authoritative call gate (see _probe_disk).
# init at import, not in a startup event: idempotent, and guarantees tables
# exist even when the app is exercised without a lifespan (TestClient).
_db = StorageManager()
_db.init_db()


def _db_safe(op, *args) -> None:
    """Bookkeeping writes must never fail a user request."""
    try:
        op(*args)
    except Exception as exc:
        print(f"[app] storage {getattr(op, '__name__', op)!s} failed: {exc!r}",
              flush=True)


# --- recruiter auth: informed consent + disconnect ---------------------------
# The builder bills the OPERATOR's Anthropic credential (API key or the
# machine's Claude subscription login). Nothing runs until a mode is chosen —
# writer: /api/auth/setup and the startup auto-resolve below; readers:
# /api/auth/status and the /api/chat gate; cleared by /api/auth/logout.
_auth_mode: Optional[str] = None            # "api_key" | "subscription" | None
if env_bootstrap.anthropic_key_status()[0]:
    # A usable key already in .env/os.environ = the operator configured it by
    # hand; auto-resolve, but the UI still shows a persistent "powered by your
    # API key — Disconnect" pill so nothing is hidden.
    _auth_mode = "api_key"

# Per-session message budget: a recruiter must never watch the builder run a
# shared demo dry. Writer: _chat_events (increments); lifecycle: process
# memory, cleared with the session.
_MSG_CAP = int(os.environ.get("BUILDER_SESSION_MSG_CAP", "30"))
_msg_counts: dict[str, int] = {}

_KEY_RE = re.compile(r"^sk-ant-[A-Za-z0-9_\-]{20,200}$")


def _rewrite_env_key(env_path: Path, key: str, value: Optional[str]) -> None:
    """Set (value=str) or comment out (value=None) ONE key line in a .env,
    preserving every other line. Creates the file if missing."""
    lines: list[str] = []
    if env_path.is_file():
        lines = env_path.read_text(encoding="utf-8").splitlines()
    out, done = [], False
    for line in lines:
        stripped = line.strip()
        is_key = stripped.startswith(f"{key}=")
        is_commented_key = stripped.lstrip("# ").startswith(f"{key}=")
        if is_key or (value is not None and is_commented_key and not done):
            if done:
                continue                      # drop duplicate lines for the key
            out.append(f"{key}={value}" if value is not None else f"# {key}= (disconnected via platform)")
            done = True
        else:
            out.append(line)
    if not done and value is not None:
        out.append(f"{key}={value}")
    env_path.write_text("\n".join(out) + "\n", encoding="utf-8")


class AuthSetupRequest(BaseModel):
    mode: str = Field(pattern="^(api_key|subscription)$")
    api_key: Optional[str] = None
    openai_key: Optional[str] = None    # generated agent's brain; optional


@app.get("/api/auth/status")
async def auth_status():
    usable, detail = env_bootstrap.anthropic_key_status()
    return {"configured": _auth_mode is not None, "mode": _auth_mode,
            "key_present": usable, "detail": detail,
            "openai_key_set": bool(os.environ.get("OPENAI_API_KEY"))}


@app.post("/api/auth/setup")
async def auth_setup(req: AuthSetupRequest):
    global _auth_mode
    if req.mode == "api_key":
        key = (req.api_key or "").strip()
        if not _KEY_RE.fullmatch(key):
            raise HTTPException(
                status_code=400,
                detail="That doesn't look like an Anthropic API key "
                       "(they start with sk-ant-).")
        _rewrite_env_key(env_bootstrap.ROOT_ENV, "ANTHROPIC_API_KEY", key)
        os.environ["ANTHROPIC_API_KEY"] = key
    else:
        # Subscription: consent only — with no key set, the SDK uses the
        # machine's own Claude CLI login (builder.py forwards nothing).
        os.environ.pop("ANTHROPIC_API_KEY", None)
    openai_key = (req.openai_key or "").strip()
    if openai_key:
        if re.search(r"\s", openai_key):
            raise HTTPException(
                status_code=400,
                detail="That OpenAI key contains whitespace — check the paste.")
        # Root .env is the single source: env_bootstrap loads it here, and
        # _child_env inherits os.environ into the voice runtime — no per-agent
        # credential entry needed.
        _rewrite_env_key(env_bootstrap.ROOT_ENV, "OPENAI_API_KEY", openai_key)
        os.environ["OPENAI_API_KEY"] = openai_key
    _auth_mode = req.mode
    return {"configured": True, "mode": _auth_mode}


@app.post("/api/auth/logout")
async def auth_logout():
    """The 'it's eating my tokens, disconnect NOW' path: drop every builder
    session, forget the key, return the UI to the setup card."""
    global _auth_mode
    for sid in list(_sessions):
        entry = _sessions.pop(sid, None)
        if entry is None:
            continue
        session, _, lock = entry
        # Preempt FIRST, before waiting on the lock: a turn mid-flight holds the
        # lock, so `async with lock` alone would block the "stop eating my
        # tokens NOW" path until that turn finished. interrupt() ends the turn,
        # which frees the lock so the close below can proceed promptly.
        try:
            await session.interrupt()
        except Exception as exc:
            print(f"[app] logout interrupt failed for {sid}: {exc!r}", flush=True)
        async with lock:
            await session.close()
        _db_safe(_db.close_session, sid)
    os.environ.pop("ANTHROPIC_API_KEY", None)
    _rewrite_env_key(env_bootstrap.ROOT_ENV, "ANTHROPIC_API_KEY", None)
    _auth_mode = None
    _msg_counts.clear()
    return {"configured": False, "mode": None}


def _marker_bytes(project_dir: Optional[Path]) -> bytes:
    """Raw selftest pass-marker (surface hash inside) — b'' when absent."""
    if project_dir is None:
        return b""
    try:
        return (Path(project_dir) / _MARKER_NAME).read_bytes()
    except OSError:
        return b""


def _friendly_error(exc: Exception) -> str:
    """A chat-stream error the recruiter can act on; raw detail goes to logs."""
    text = repr(exc).lower()
    if "401" in text or "authentication" in text or "invalid x-api-key" in text:
        return ("Your Anthropic API key was rejected — click Disconnect "
                "(top right) and enter it again in setup.")
    return (f"The builder hit an unexpected error ({type(exc).__name__}). "
            "Try sending that message again.")


def _probe_disk(session_id: str) -> tuple[Optional[Path], bool]:
    """Ground-truth fallback when a session isn't in memory (server restart,
    or the user switched to a pre-existing session id): the workspace dir and
    its surface-hash pass marker. Works for agents built before the DB layer
    was wired — those have no DB row, but their files and marker are on disk.
    """
    # Same safety regex BuilderSession enforces — a raw query-param session_id
    # must never become a path segment unvalidated (traversal).
    if not re.fullmatch(r"[A-Za-z0-9_\-]{1,64}", session_id):
        return None, False
    project = discover_project(WORKSPACES_DIR / session_id)
    if project is None:
        # Pre-built/shipped agents (e.g. the demo) sit one level flatter: the
        # named dir under Generated_Agents/ IS the project (config.py directly
        # inside). The regex above already forbids path separators, so this can
        # only ever be a direct child — no traversal. Lets a reviewer set the
        # session id to the agent's folder name and call it with no build.
        candidate = GENERATED_AGENTS_DIR / session_id
        if (candidate / "config.py").is_file():
            project = candidate
    if project is None:
        return None, False
    return project, has_persisted_pass(project)


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1, max_length=8000)


async def _get_or_create_session(session_id: str) -> tuple[BuilderSession, asyncio.Lock]:
    entry = _sessions.get(session_id)
    if entry is not None:
        session, _, lock = entry
        _sessions[session_id] = (session, time.time(), lock)
        _db_safe(_db.touch_session, session_id)
        return session, lock
    try:
        session = BuilderSession(session_id, db=_db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _db_safe(_db.create_session, session_id)  # idempotent upsert
    lock = asyncio.Lock()
    async with lock:
        await session.start()
    _sessions[session_id] = (session, time.time(), lock)
    logger.info("new builder session started: %s", session_id)
    return session, lock


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event)}\n\n"


# --- code-enforced narration guard -------------------------------------------
# The builder is INSTRUCTED never to narrate internal work, but a model's
# adherence is probabilistic — and a non-technical client watching "Let me edit
# selftest.py" believes the agent is rewriting its own source (it cannot: writes
# are sandboxed). Per anti-pattern #9, an invariant that MUST hold is enforced in
# code, not left to the prompt. This drops any assistant text carrying an
# unmistakable internal marker before it reaches the browser. Patterns are tight
# so spoken-style client prose ("Tell me about your plans") never matches; the
# guided-question block (alta:ask) is always exempt.
_PY_FILE_RE = re.compile(r"\b[\w-]+\.py\b")
_CODE_IDENT_RE = re.compile(r"\b[A-Z][A-Z0-9]*_[A-Z0-9_]+\b")  # HOOK_CHECKS, PAUSED_RESUME_TEXT
_INTERNAL_LEADIN_RE = re.compile(
    r"\b(let me|now i'?ll|i'?ll now|now let'?s|let'?s|i'?m going to|i will)\b[^.?!]*\b"
    r"(check|look|view|read|updat|edit|writ|fix|run|see|examin|rewrit|inspect|"
    r"scan|refactor|rework|open|instantiat|generat|verif)",
    re.IGNORECASE)
_INTERNAL_TERM_RE = re.compile(
    r"\b(selftest|boilerplate|hook[_ ]?checks|hardcoded|codebase|engine file|"
    r"domain-specific|config key|the full file)\b", re.IGNORECASE)


def is_internal_narration(text: str) -> bool:
    """True if this assistant text leaks HOW the builder works (file names,
    code identifiers, work narration) and must not reach the client."""
    t = (text or "").strip()
    if not t or "alta:ask" in t:      # never drop the guided-question block
        return False
    return bool(
        _PY_FILE_RE.search(t)
        or _CODE_IDENT_RE.search(t)
        or _INTERNAL_LEADIN_RE.search(t)
        or _INTERNAL_TERM_RE.search(t)
    )


async def _chat_events(session_id: str, message: str) -> AsyncIterator[str]:
    if _auth_mode is None:
        # Informed consent first: the builder burns the OPERATOR's tokens.
        yield _sse({"type": "error",
                    "detail": "Choose how the builder is powered first — open "
                              "the setup card (API key or Claude subscription)."})
        yield "data: [DONE]\n\n"
        return
    used = _msg_counts.get(session_id, 0)
    if used >= _MSG_CAP:
        # Budget guard: refuse BEFORE the SDK sees the message — a capped
        # session must cost zero tokens.
        yield _sse({"type": "text",
                    "text": "This session reached its message limit — switch "
                            "to a fresh session id (top right) to continue."})
        yield _sse({"type": "result", "is_error": False})
        yield "data: [DONE]\n\n"
        return
    _msg_counts[session_id] = used + 1
    try:
        session, lock = await _get_or_create_session(session_id)
    except HTTPException as exc:
        yield _sse({"type": "error", "detail": exc.detail})
        return
    async with lock:
        marker_before = _marker_bytes(session.project_dir)
        try:
            async for event in session.send(message):
                # Code-enforced narration guard: never stream internal-work text
                # to the client (see is_internal_narration). Tool events carry no
                # client-facing text; the UI shows progress via the stepper only.
                if (event.get("type") == "text"
                        and is_internal_narration(event.get("text", ""))):
                    continue
                yield _sse(event)
        except Exception as exc:  # a crashed builder turn must still close the
                                  # stream cleanly for the chat UI, not hang it
            print(f"[app] builder turn failed for {session_id}: {exc!r}",
                  flush=True)
            yield _sse({"type": "error", "detail": _friendly_error(exc)})
    # Edit-loop staleness guard: the pass marker embeds the surface hash, so
    # changed marker bytes mean the agent was rewritten AND re-proven this
    # turn. A warm runtime for that project is now serving stale code — stop
    # it here; the next /api/call respawns it on the edited files.
    if _marker_bytes(session.project_dir) != marker_before:
        logger.info("agent built/re-proven: session=%s dir=%s",
                    session_id, session.project_dir)
        active = runtime_supervisor.status()
        if (active["running"] and session.project_dir is not None
                and Path(active["agent_dir"]).resolve()
                == Path(session.project_dir).resolve()):
            await runtime_supervisor.stop()
    yield "data: [DONE]\n\n"


@app.post("/api/chat")
async def chat(req: ChatRequest):
    return StreamingResponse(
        _chat_events(req.session_id, req.message),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


class StopRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=64)


@app.post("/api/chat/stop")
async def stop_chat(req: StopRequest):
    """Hard-stop the session's in-flight builder turn NOW.

    Deliberately does NOT acquire the session lock: the running turn holds it,
    so waiting for it would be the exact deadlock we are fixing. interrupt()
    is designed to be called concurrently with a receive loop — it signals the
    SDK to end the turn, which releases the lock on its own."""
    entry = _sessions.get(req.session_id)
    if entry is None:
        return {"stopped": False, "reason": "no active session"}
    session, _, _ = entry
    try:
        await session.interrupt()
    except Exception as exc:  # a failed interrupt is a typed result, never a 500
        print(f"[app] interrupt failed for {req.session_id}: {exc!r}", flush=True)
        return {"stopped": False, "reason": repr(exc)}
    return {"stopped": True}


@app.get("/api/agent")
async def agent_status(session_id: str):
    entry = _sessions.get(session_id)
    if entry is None:
        # Not in memory (restart / switched to a pre-existing session id):
        # answer from disk so a proven agent shows as ready without requiring
        # a chat turn first.
        project, passed = _probe_disk(session_id)
        return {
            "exists": project is not None,
            "project_dir": str(project) if project else None,
            "selftest_passed": passed,
        }
    session, _, _ = entry
    return {
        "exists": session.project_dir is not None,
        "project_dir": str(session.project_dir) if session.project_dir else None,
        "selftest_passed": session.selftest_passed,
    }


# --- agent credentials + takeaway --------------------------------------------
# "The agent is dead without credentials": the generated agent's .env
# (OPENAI_API_KEY, integration keys) is populated through the UI, and the
# whole agent can be downloaded as a zip WITH those credentials inside.

def _resolve_project(session_id: str) -> Path:
    """The session's project dir, in-memory first, disk fallback — 404 if none."""
    entry = _sessions.get(session_id)
    if entry is not None and entry[0].project_dir is not None:
        return Path(entry[0].project_dir)
    project, _ = _probe_disk(session_id)
    if project is None:
        raise HTTPException(status_code=404,
                            detail="No built agent found for this session.")
    return project


def _env_allowlist(project: Path) -> list[str]:
    """Keys the panel may show/set = keys declared in the project's
    .env.example. Arbitrary keys are never exposed or accepted."""
    example = project / ".env.example"
    keys: list[str] = []
    if example.is_file():
        for line in example.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if s and not s.startswith("#") and "=" in s:
                keys.append(s.split("=", 1)[0].strip())
    return keys


def _mask(value: str) -> str:
    v = value.strip()
    if not v:
        return ""
    return f"…{v[-4:]}" if len(v) > 8 else "•••"


@app.get("/api/agent/env")
async def agent_env(session_id: str):
    project = _resolve_project(session_id)
    keys = _env_allowlist(project)
    current: dict[str, str] = {}
    env_file = project / ".env"
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if s and not s.startswith("#") and "=" in s:
                k, v = s.split("=", 1)
                current[k.strip()] = v.strip()
    return {"project": project.name,
            "keys": [{"key": k, "set": bool(current.get(k, "").strip()),
                      "masked": _mask(current.get(k, ""))} for k in keys]}


class AgentEnvRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=64)
    values: dict[str, str] = Field(min_length=1)


@app.post("/api/agent/env")
async def set_agent_env(req: AgentEnvRequest):
    project = _resolve_project(req.session_id)
    allow = set(_env_allowlist(project))
    bad = [k for k in req.values if k not in allow]
    if bad:
        raise HTTPException(
            status_code=400,
            detail=f"Not settable for this agent: {', '.join(sorted(bad))} — "
                   f"only keys from its .env.example are accepted.")
    env_file = project / ".env"
    for key, value in req.values.items():
        _rewrite_env_key(env_file, key, value.strip())
    # The voice runtime keeps a warm process per agent; it inherits env at
    # spawn. Stop it so the NEXT call restarts with the new credentials.
    restarted = False
    active = runtime_supervisor.status()
    if active.get("running") and active.get("agent_dir") == str(project):
        await runtime_supervisor.stop()
        restarted = True
    return {"saved": sorted(req.values), "runtime_stopped": restarted,
            "note": "The next test call starts the runtime with the new values."}


@app.get("/api/agent/download")
async def download_agent(session_id: str):
    """The takeaway zip — INCLUDES .env, so it carries the operator's
    credentials; the UI says so next to the button."""
    project = _resolve_project(session_id)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(project.rglob("*")):
            if path.is_dir():
                continue
            rel = path.relative_to(project)
            if "__pycache__" in rel.parts or rel.suffix == ".pyc":
                continue
            zf.write(path, arcname=str(Path(project.name) / rel))
    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition":
                 f'attachment; filename="{project.name}.zip"'})


@app.delete("/api/session/{session_id}")
async def end_session(session_id: str):
    entry = _sessions.pop(session_id, None)
    if entry is None:
        return {"closed": False}
    session, _, lock = entry
    async with lock:
        await session.close()
    _db_safe(_db.close_session, session_id)
    _msg_counts.pop(session_id, None)
    return {"closed": True}


class CallRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=64)


@app.post("/api/call")
async def start_call(req: CallRequest):
    """Make the session's generated agent reachable by Vapi, and hand the
    browser what it needs to open a web call.

    Order matters: every cheap, deterministic check runs BEFORE the expensive
    runtime spawn, so a misconfiguration costs a fast 4xx instead of a 90-second
    graph load followed by failure.

      1. the agent exists and its selftest PASSed  (never dial an unproven agent)
      2. credentials + auth alignment              (vapi_control preflight)
      3. a public URL resolves                     (tunnel)
      4. spawn/reuse the runtime subprocess        (slow: graph first load)
      5. point the Vapi assistant at that tunnel

    The browser then calls vapi.start(assistant_id) with the PUBLIC key; the
    private key never leaves this process.
    """
    entry = _sessions.get(req.session_id)
    if entry is not None:
        session, _, _ = entry
        project_dir, selftest_passed = session.project_dir, session.selftest_passed
    else:
        # No live builder session (restart / pre-existing session id): the
        # call path only needs the project path and a trusted PASS, and the
        # disk marker provides both — no need to force a chat turn first.
        project_dir, selftest_passed = _probe_disk(req.session_id)
        if project_dir is None:
            raise HTTPException(
                status_code=404,
                detail="No builder session or built agent found for this "
                       "session id.")
    if project_dir is None:
        raise HTTPException(
            status_code=409,
            detail="No agent has been built in this session yet.")
    if not selftest_passed:
        raise HTTPException(
            status_code=409,
            detail="This agent has not passed its selftest — it is not "
                   "callable yet.")

    try:
        vapi_control.preflight_auth()
        assistant = vapi_control.assistant_id()
        pub_key = vapi_control.public_key()
        vapi_control._private_key()          # fail here, not after the spawn
    except vapi_control.VapiConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    try:
        # Verified against the port the runtime will actually bind — a tunnel
        # pointing at the wrong port passes a naive "is ngrok up?" check and
        # then fails as silent dead air.
        public_url = await tunnel.resolve_public_url(runtime_supervisor.RUNTIME_PORT)
    except (tunnel.TunnelNotFound, tunnel.TunnelPortMismatch) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    try:
        active = await runtime_supervisor.start(project_dir)
    except runtime_supervisor.RuntimeStartError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"The voice runtime failed to start: {exc}") from exc

    logger.info("call started: session=%s agent=%s port=%s brain=%s",
                req.session_id, active.agent_dir, active.port,
                "live" if os.environ.get("OPENAI_API_KEY", "").strip() else "mock")

    # Cached opener: the agent's static OPENER becomes Vapi's firstMessage, so
    # the first words play at pickup with zero model calls. None (missing or
    # non-literal) leaves the dashboard's firstMessage untouched.
    first_message = runtime_supervisor.opener_from_config(project_dir)

    try:
        wiring = await vapi_control.point_assistant_at(
            public_url, assistant, first_message=first_message)
    except (vapi_control.VapiConfigError, vapi_control.VapiAPIError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {
        "public_key": pub_key,
        "assistant_id": wiring["assistant_id"],
        "model_url": wiring["model_url"],
        "public_url": public_url,
        "agent_dir": str(active.agent_dir),
        "runtime_port": active.port,
        "first_message": wiring["first_message"],
        # Deadlock visibility: a blank OPENAI_API_KEY means the agent answers
        # from deterministic keyword matching — the operator must SEE that
        # before demoing, not discover it on the call.
        "brain": "live" if os.environ.get("OPENAI_API_KEY", "").strip() else "mock",
    }


@app.get("/health")
async def health():
    return {"status": "ok", "active_sessions": len(_sessions),
            "runtime": runtime_supervisor.status()}


@app.on_event("shutdown")
async def _close_all_sessions() -> None:
    for session, _, lock in list(_sessions.values()):
        async with lock:
            await session.close()
    _sessions.clear()
    await runtime_supervisor.stop()
