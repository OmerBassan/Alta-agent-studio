# -*- coding: utf-8 -*-
"""Public URL discovery for the voice runtime.

Vapi must reach the adapter over the public internet, so the locally-bound
runtime needs a tunnel. We do NOT manage the ngrok process: the binary is not
guaranteed to be on PATH, and supervising a second long-lived subprocess buys
nothing over the operator's own `ngrok http <port>` (which is how every proven
flight call to date was run).

Resolution order:
  1. PUBLIC_URL env  — explicit operator override (any tunnel: ngrok, cloudflared,
     a real host). Wins outright; never probed.
  2. ngrok's local agent API (http://127.0.0.1:4040/api/tunnels) — if the
     operator already has `ngrok http <port>` running, adopt its https tunnel.

Both are advisory: a caller that gets TunnelNotFound should report the fix to
the operator, never guess a URL.
"""

from __future__ import annotations

import asyncio
import glob
import logging
import os
import shutil
import subprocess
import time
from urllib.parse import urlparse

import httpx

logger = logging.getLogger("alta.tunnel")

NGROK_AGENT_API = os.environ.get("NGROK_AGENT_API", "http://127.0.0.1:4040/api/tunnels")
NGROK_AGENT_ROOT = NGROK_AGENT_API.rsplit("/api/", 1)[0]  # http://127.0.0.1:4040
_PROBE_TIMEOUT_S = 2.0
_SPAWN_WAIT_S = float(os.environ.get("NGROK_SPAWN_WAIT_S", "15"))

# An ngrok process WE started, tracked so app shutdown can kill it — a lingering
# agent trips the free tier's one-session limit on the next launch
# (ERR_NGROK_108). The spawn decision is serialized by a per-loop lock so two
# concurrent callers (startup warm-up + a fast first /api/call) can never race
# into a double spawn.
_spawned_proc: "subprocess.Popen | None" = None
_spawn_lock: "asyncio.Lock | None" = None
_spawn_lock_loop = None


def _get_spawn_lock() -> asyncio.Lock:
    """One lock bound to the CURRENT running loop. Created lazily (and re-created
    if the loop changed) so a module-level lock can't leak across the separate
    event loops that `asyncio.run(...)` spins up per test."""
    global _spawn_lock, _spawn_lock_loop
    loop = asyncio.get_running_loop()
    if _spawn_lock is None or _spawn_lock_loop is not loop:
        _spawn_lock = asyncio.Lock()
        _spawn_lock_loop = loop
    return _spawn_lock


class TunnelNotFound(RuntimeError):
    """No public URL could be resolved — the operator must start a tunnel."""


class TunnelPortMismatch(RuntimeError):
    """A tunnel is up but forwards somewhere other than the voice runtime.

    Its own failure class because it is the plausible-looking disaster: a tunnel
    EXISTS, so a naive check passes, but Vapi's traffic lands on the wrong local
    port and the call dies with no error anywhere. Observed for real: a
    long-running `ngrok http 8000` while the runtime binds 8100.
    """


def _from_env() -> str | None:
    url = os.environ.get("PUBLIC_URL", "").strip().rstrip("/")
    return url or None


def _find_ngrok() -> str | None:
    """Locate the ngrok binary even when it isn't visible on THIS process's
    PATH. A fresh Windows PATH entry (e.g. from a winget install) only reaches
    processes started AFTER the change — a long-running server terminal keeps
    its stale PATH — so a bare "ngrok" lookup can silently fail on a machine
    that genuinely has it installed. Falls back to the standard winget install
    location before giving up."""
    found = shutil.which("ngrok")
    if found:
        return found
    winget_glob = os.path.join(
        os.path.expanduser("~"), "AppData", "Local", "Microsoft", "WinGet",
        "Packages", "Ngrok.Ngrok_*", "ngrok.exe")
    matches = glob.glob(winget_glob)
    return matches[0] if matches else None


def _addr_port(addr: str) -> int | None:
    """Port out of an ngrok tunnel's config.addr ('http://localhost:8000', or
    bare forms like '8000' / 'localhost:8000')."""
    addr = (addr or "").strip()
    if not addr:
        return None
    if addr.isdigit():
        return int(addr)
    parsed = urlparse(addr if "//" in addr else f"//{addr}")
    return parsed.port


async def _ngrok_tunnels() -> list[dict]:
    """Raw tunnel list from the local ngrok agent; [] when no agent is running.

    A closed port is the normal case (operator uses PUBLIC_URL, or hasn't started
    ngrok), so connection errors resolve to [] rather than raising — the caller
    turns "nothing found" into one actionable message.
    """
    try:
        async with httpx.AsyncClient(timeout=_PROBE_TIMEOUT_S) as client:
            resp = await client.get(NGROK_AGENT_API)
            resp.raise_for_status()
            payload = resp.json()
    except (httpx.HTTPError, ValueError):
        return []
    tunnels = payload.get("tunnels")
    return [t for t in tunnels if isinstance(t, dict)] if isinstance(tunnels, list) else []


def _match_https_tunnel(tunnels: list[dict], runtime_port: int) -> str | None:
    """The https tunnel forwarding to runtime_port, or None."""
    for t in tunnels:
        if str(t.get("public_url", "")).startswith("https://") and \
                _addr_port(str((t.get("config") or {}).get("addr", ""))) == runtime_port:
            return str(t["public_url"]).rstrip("/")
    return None


async def _agent_reachable() -> bool:
    """True if an ngrok agent is answering on :4040 AT ALL (even with zero
    tunnels). Used to AVOID spawning a second agent — the free tier allows one
    session, so a second `ngrok http` just dies with ERR_NGROK_108."""
    try:
        async with httpx.AsyncClient(timeout=_PROBE_TIMEOUT_S) as client:
            resp = await client.get(NGROK_AGENT_ROOT)
            return resp.status_code < 500
    except httpx.HTTPError:
        return False


async def _spawn_ngrok_and_wait(ngrok_exe: str, runtime_port: int) -> str:
    """Start ONE ngrok agent and POLL until it forwards to runtime_port, or fail
    with the REAL reason. Replaces the old fire-and-sleep-2.5s, which timed out
    on a slow bind and swallowed ngrok's own error to DEVNULL. Caller holds the
    spawn lock, so only one spawn is ever in flight."""
    global _spawned_proc
    logger.info("no ngrok tunnel for port %s — starting %s", runtime_port, ngrok_exe)
    proc = subprocess.Popen(
        [ngrok_exe, "http", str(runtime_port)],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    _spawned_proc = proc
    deadline = time.monotonic() + _SPAWN_WAIT_S
    while time.monotonic() < deadline:
        await asyncio.sleep(1.0)
        if proc.poll() is not None:               # ngrok died — surface WHY
            err = (proc.stderr.read() if proc.stderr else "").strip()
            raise TunnelNotFound(
                f"ngrok exited on startup: {err[:300] or 'no error output'}. "
                f"Most often a leftover ngrok session (the free tier allows ONE "
                f"— close any other ngrok window/process and retry) or a missing "
                f"authtoken (run `ngrok config add-authtoken <token>` once).")
        url = _match_https_tunnel(await _ngrok_tunnels(), runtime_port)
        if url:
            logger.info("ngrok tunnel ready: %s -> %s", url, runtime_port)
            return url
    raise TunnelNotFound(
        f"ngrok started but exposed no tunnel to port {runtime_port} within "
        f"{_SPAWN_WAIT_S:.0f}s. Retry the call (it may just be slow to bind), or "
        f"set PUBLIC_URL in builder_platform/.env.")


async def resolve_public_url(runtime_port: int) -> str:
    """The base https URL Vapi should call, verified to reach `runtime_port`.

    Order: PUBLIC_URL override -> adopt a matching running ngrok tunnel ->
    (serialized) auto-start ONE ngrok and poll until it binds. Never spawns a
    second agent while one is already running (the free tier's one-session
    limit); a tunnel on the WRONG port raises TunnelPortMismatch (silent-dead-air
    trap), never adopted blindly.
    """
    url = _from_env()
    if url:
        return url

    # Fast path: a matching tunnel is already up (the common warm case).
    url = _match_https_tunnel(await _ngrok_tunnels(), runtime_port)
    if url:
        return url

    # Serialize the decide-and-spawn so two callers can't double-spawn (108).
    async with _get_spawn_lock():
        tunnels = await _ngrok_tunnels()
        url = _match_https_tunnel(tunnels, runtime_port)   # re-check after the wait
        if url:
            return url

        https = [t for t in tunnels
                 if str(t.get("public_url", "")).startswith("https://")]
        if https:
            found = ", ".join(
                f"{t['public_url']} -> {(t.get('config') or {}).get('addr')}"
                for t in https)
            raise TunnelPortMismatch(
                f"An ngrok tunnel is running, but none of them forward to the voice "
                f"runtime on port {runtime_port}. Found: {found}. Vapi would reach "
                f"the wrong local service and the call would connect but never "
                f"speak. Restart ngrok against the runtime port "
                f"(`ngrok http {runtime_port}`), or set RUNTIME_PORT in "
                f"builder_platform/.env to the port your tunnel already forwards to.")

        # An agent is up but exposes no tunnels: DON'T spawn a second (108).
        if await _agent_reachable():
            raise TunnelNotFound(
                f"An ngrok agent is running but exposes no tunnel to port "
                f"{runtime_port}. Point it at the runtime (`ngrok http "
                f"{runtime_port}`) or set PUBLIC_URL. (Not auto-starting a second "
                f"agent — the free tier allows only one session.)")

        ngrok_exe = _find_ngrok()
        if ngrok_exe is None:
            raise TunnelNotFound(
                f"No public URL for the voice runtime and ngrok is not installed. "
                f"Start a tunnel (`ngrok http {runtime_port}`) so Vapi can reach "
                f"this machine, or set PUBLIC_URL in builder_platform/.env to an "
                f"https URL that forwards to port {runtime_port}.")
        return await _spawn_ngrok_and_wait(ngrok_exe, runtime_port)


def shutdown_tunnel() -> None:
    """Best-effort kill of an ngrok WE spawned, so a lingering agent can't block
    the next launch with ERR_NGROK_108. Safe to call when nothing was spawned."""
    global _spawned_proc
    proc, _spawned_proc = _spawned_proc, None
    if proc is not None and proc.poll() is None:
        try:
            proc.terminate()
        except Exception:
            pass
