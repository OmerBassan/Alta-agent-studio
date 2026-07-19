"""Deterministic tool layer (the 'Act' in Think→Act).            [CUSTOMIZE]

The reasoning tier decides WHICH tool and WITH WHAT args (a cold structured
payload); it never executes side-effects itself. These functions are the only
place a real API/DB call would live — mock-first so the agent runs with zero
credentials. A real deployment swaps the bodies and keeps the signatures.

Contract for every tool:
  - args are the flow's slots (see config.FLOWS)
  - return a small structured dict (never prose) INCLUDING a "summary" field:
    one plain-English sentence used verbatim by mock mode and as grounding by
    the ENRICH tier in live mode.
Register each tool in TOOL_REGISTRY at the bottom.
"""

from __future__ import annotations

import hashlib
from typing import Callable, Dict


def _stable_hash(*parts: str) -> int:
    return int(hashlib.md5(":".join(p or "" for p in parts).encode("utf-8")).hexdigest(), 16)


def submit_lead_profile(monthly_volume: str = "", drink_mix: str = "", current_supplier: str = "",
                        contract_renewal: str = "", buyer_character: str = "", **_) -> Dict[str, object]:
    """Log the qualified lead profile and route it to the sales team (a single
    write covers both — the CRM/inbox notification IS the write). Real impl ->
    CRM write + sales-inbox email.

    A monthly_volume whose digits are all 9s (4+ digits) simulates a BACKEND
    OUTAGE: the tool returns an "error" result, which the execution validator
    routes to the failure node (graceful degradation, testable without a live
    CRM)."""
    digits = "".join(c for c in (monthly_volume or "") if c.isdigit())
    if digits and set(digits) == {"9"} and len(digits) >= 4:
        return {"tool": "submit_lead_profile",
                "error": "lead system timeout (simulated)",
                "summary": "The lead system did not respond."}
    ref = f"LD-{_stable_hash('lead', current_supplier, monthly_volume, drink_mix) % 100000:05d}"
    summary = (f"Logged: about {monthly_volume} guests a month, mostly {drink_mix}, currently through "
               f"{current_supplier or 'their current supplier'}, looking at {buyer_character}. "
               f"Sent to our sales team (reference {ref}).")
    return {"tool": "submit_lead_profile", "lead_reference": ref, "monthly_volume": monthly_volume,
            "drink_mix": drink_mix, "buyer_character": buyer_character, "summary": summary}


def flag_for_team(request_details: str = "", **_) -> Dict[str, object]:
    """Log a request the agent can't resolve itself (discount ask, delivery
    complaint, custom recipe, technical question) for the sales team to follow
    up on directly. Real impl -> CRM ticket + sales-inbox email."""
    ref = f"FR-{_stable_hash('flag', request_details) % 100000:05d}"
    summary = f"Got it — logged for our sales team to follow up on directly (reference {ref})."
    return {"tool": "flag_for_team", "flag_reference": ref, "request_details": request_details,
            "summary": summary}


# name -> callable; the Think step's cold payload references these names.
TOOL_REGISTRY: Dict[str, Callable[..., Dict[str, object]]] = {
    "submit_lead_profile": submit_lead_profile,
    "flag_for_team": flag_for_team,
}

# Compaction retrieval (engine, not domain): pages back the full items behind
# a crushed result's sentinel ref. Registered always; give it a Flow only if
# the domain's tools return big lists AND the ANSWER tier needs to page them.
from compaction import retrieve_full_result  # noqa: E402

TOOL_REGISTRY["retrieve_full_result"] = retrieve_full_result


# ── MCP integration (optional, additive) ────────────────────────────────────
async def register_mcp_tools(session, tool_names: list[str] | None = None) -> list[str]:
    """Wrap tools exposed by an MCP server into TOOL_REGISTRY, preserving the
    cold-payload contract (kwargs in -> structured dict WITH a "summary" out).

    `session` is a connected `mcp.ClientSession` (pip install mcp). Await this
    once at startup, then reference the tool names from config.FLOWS exactly
    like local tools — the graph cannot tell the difference, which is the
    point: MCP swaps the transport, never the architecture (schema enforcement
    stays with Flow slots + validators; execution stays behind the registry).
    Local Python tools remain the default; nothing here runs in mock mode or
    without `mcp` installed. The wrappers are async — tool_exec_node awaits
    coroutine tools transparently.

    Returns the list of registered tool names."""
    import json

    def _wrap(name: str) -> Callable[..., object]:
        async def _call(**kwargs) -> Dict[str, object]:
            result = await session.call_tool(name, arguments=kwargs)
            # Normalize MCP content blocks into the registry's dict contract.
            text = "".join(getattr(c, "text", "") for c in getattr(result, "content", []) or [])
            try:
                payload = json.loads(text) if text.strip().startswith("{") else {"raw": text}
            except ValueError:
                payload = {"raw": text}
            payload.setdefault("tool", name)
            payload.setdefault("summary", text.strip()[:200] or f"{name} completed.")
            if getattr(result, "isError", False):
                payload.setdefault("error", payload.get("raw", "MCP tool error"))
            return payload
        return _call

    available = await session.list_tools()
    registered = []
    for tool in available.tools:
        if tool_names and tool.name not in tool_names:
            continue
        TOOL_REGISTRY[tool.name] = _wrap(tool.name)
        registered.append(tool.name)
    return registered
