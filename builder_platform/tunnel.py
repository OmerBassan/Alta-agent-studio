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

import os
from urllib.parse import urlparse

import httpx

NGROK_AGENT_API = os.environ.get("NGROK_AGENT_API", "http://127.0.0.1:4040/api/tunnels")
_PROBE_TIMEOUT_S = 2.0


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


async def resolve_public_url(runtime_port: int) -> str:
    """The base https URL Vapi should call, verified to reach `runtime_port`.

    PUBLIC_URL is trusted blindly (the operator may front the runtime with any
    proxy we cannot introspect). A discovered ngrok tunnel is NOT trusted: we
    confirm it forwards to the runtime's port, because a tunnel pointing at the
    wrong port is worse than no tunnel — it fails silently.
    """
    url = _from_env()
    if url:
        return url

    tunnels = await _ngrok_tunnels()
    https = [t for t in tunnels
             if str(t.get("public_url", "")).startswith("https://")]
    for tunnel in https:
        if _addr_port(str((tunnel.get("config") or {}).get("addr", ""))) == runtime_port:
            return str(tunnel["public_url"]).rstrip("/")

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

    raise TunnelNotFound(
        f"No public URL for the voice runtime. Either start a tunnel "
        f"(`ngrok http {runtime_port}`) so Vapi can reach this machine, or set "
        f"PUBLIC_URL in builder_platform/.env to an https URL that forwards to port "
        f"{runtime_port}.")
