# -*- coding: utf-8 -*-
"""Supervises the voice runtime subprocess (one generated agent at a time).

Why a subprocess and not an import: every generated agent defines top-level
modules named `config`, `graph`, `tools`. Importing a second agent into this
process would collide on those names and silently serve the FIRST agent's brain
forever. The process boundary is the isolation — regenerating an agent kills and
respawns, never re-imports. (CLAUDE.md: subprocess-per-agent.)

Single-active-agent is deliberate technical debt for the demo: one runtime port,
one agent. Building a port pool would buy nothing a reviewer can see.

State: `_active` holds the one running child. Written by start()/stop(), read by
status(); cleared by stop() and on process death. Lifecycle is bounded by the
app's shutdown hook.
"""

from __future__ import annotations

import ast
import asyncio
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import httpx

PLATFORM_DIR = Path(__file__).resolve().parent
RUNTIME_HOST = "127.0.0.1"  # child binds here; health check must match
RUNTIME_PORT = int(os.environ.get("RUNTIME_PORT", "8100"))
_HEALTH_TIMEOUT_S = float(os.environ.get("RUNTIME_HEALTH_TIMEOUT_S", "90"))
_POLL_INTERVAL_S = 0.5
_STOP_GRACE_S = 10


class RuntimeStartError(RuntimeError):
    """The runtime failed to come up; carries the child's output tail."""


def opener_from_config(agent_dir: Path | str) -> str | None:
    """The agent's OPENER string literal, statically parsed — or None.

    Serves the cached-opener path: /api/call PATCHes this text into the Vapi
    assistant's firstMessage so the agent's first words play at pickup with
    zero model calls. Parsed via ast, NEVER imported (agent modules collide on
    names, and import runs arbitrary code).

    None on ANY doubt — missing file, syntax error, OPENER absent, not a plain
    string literal (f-string/concat), or empty/whitespace-only. Whitespace is
    explicitly rejected: a " " firstMessage silently wedges Vapi's TTS queue
    (logged trap, cost a day). On None the caller leaves the assistant's
    firstMessage exactly as dashboard-configured.
    """
    config_path = Path(agent_dir) / "config.py"
    try:
        tree = ast.parse(config_path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, ValueError):
        return None
    for node in tree.body:
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets = [node.target]
        if not any(isinstance(t, ast.Name) and t.id == "OPENER" for t in targets):
            continue
        value = node.value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            text = value.value.strip()
            return text or None
        return None      # OPENER exists but isn't a plain literal — refuse
    return None


@dataclass
class ActiveRuntime:
    agent_dir: Path
    port: int
    proc: subprocess.Popen

    @property
    def alive(self) -> bool:
        return self.proc.poll() is None


_active: ActiveRuntime | None = None


def status() -> dict:
    if _active is None:
        return {"running": False, "agent_dir": None, "port": None}
    return {"running": _active.alive,
            "agent_dir": str(_active.agent_dir),
            "port": _active.port}


def _child_env(agent_dir: Path) -> dict[str, str]:
    env = dict(os.environ)
    env["AGENT_DIR"] = str(agent_dir)
    env["BRAIN_MODE"] = os.environ.get("BRAIN_MODE", "live")
    env["PYTHONIOENCODING"] = "utf-8"      # child prints agent prose; console is cp1255
    env["PYTHONUNBUFFERED"] = "1"          # so a crash tail is readable immediately
    # Vapi cannot send a secret to a custom-llm url, so a set secret makes the
    # adapter 401 every turn (see vapi_control.preflight_auth).
    #
    # This MUST be an empty string, not a pop(). The child re-runs env_bootstrap,
    # which merges builder_platform/.env via os.environ.setdefault (env_bootstrap.py:78):
    # a DELETED key gets refilled from the file, while a key that is present-but-
    # empty blocks the file value. Popping it here looked correct and was inert —
    # the child 401'd anyway. Verified by spawning the real runtime.
    env["VAPI_SERVER_SECRET"] = ""
    return env


async def _await_health(port: int, proc: subprocess.Popen) -> None:
    """Poll /health until the agent's graph finishes its (heavy) first load.

    Bounded by _HEALTH_TIMEOUT_S, and short-circuits if the child dies — waiting
    the full timeout on a process that already crashed is pure dead air.
    """
    deadline = asyncio.get_event_loop().time() + _HEALTH_TIMEOUT_S
    url = f"http://{RUNTIME_HOST}:{port}/health"
    async with httpx.AsyncClient(timeout=2.0) as client:
        while asyncio.get_event_loop().time() < deadline:
            if proc.poll() is not None:
                raise RuntimeStartError(
                    f"runtime exited with code {proc.returncode} during startup:\n"
                    f"{_drain(proc)}")
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return
            except httpx.HTTPError:
                pass
            await asyncio.sleep(_POLL_INTERVAL_S)
    raise RuntimeStartError(
        f"runtime did not answer {url} within {_HEALTH_TIMEOUT_S:.0f}s")


def _drain(proc: subprocess.Popen, limit: int = 2000) -> str:
    try:
        out = proc.stdout.read() if proc.stdout else ""
    except (ValueError, OSError):
        out = ""
    return (out or "")[-limit:]


async def start(agent_dir: Path | str, port: int = RUNTIME_PORT) -> ActiveRuntime:
    """Spawn the adapter+runtime for `agent_dir`, replacing any active one.

    Idempotent for the same directory: a live runtime already serving this agent
    is reused rather than restarted (a restart would drop in-flight calls and
    cost the graph's slow first load again).
    """
    global _active
    agent_dir = Path(agent_dir).resolve()
    if not agent_dir.is_dir():
        raise RuntimeStartError(f"agent dir does not exist: {agent_dir}")

    if _active is not None and _active.alive and _active.agent_dir == agent_dir:
        return _active
    await stop()

    proc = subprocess.Popen(
        [sys.executable, "-X", "utf8", "-m", "uvicorn", "vapi_adapter:app",
         "--host", RUNTIME_HOST, "--port", str(port), "--log-level", "warning"],
        cwd=str(PLATFORM_DIR), env=_child_env(agent_dir),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace",
    )
    try:
        await _await_health(port, proc)
    except RuntimeStartError:
        _kill(proc)
        raise
    _active = ActiveRuntime(agent_dir=agent_dir, port=port, proc=proc)
    return _active


def _kill(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=_STOP_GRACE_S)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=_STOP_GRACE_S)


async def stop() -> None:
    global _active
    if _active is None:
        return
    await asyncio.to_thread(_kill, _active.proc)
    _active = None
