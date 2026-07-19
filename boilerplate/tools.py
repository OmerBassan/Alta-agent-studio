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
import smtplib
from email.mime.text import MIMEText
from typing import Callable, Dict

_BRANCH_LABELS = {"downtown": "Downtown (12 River St)", "mall": "Mall (Westfield, level 2)",
                  "airport": "Airport (Terminal B)"}


def _stable_hash(*parts: str) -> int:
    return int(hashlib.md5(":".join(p or "" for p in parts).encode("utf-8")).hexdigest(), 16)


def lookup_order(order_id: str = "", **_) -> Dict[str, object]:
    """Mock order-tracking lookup. Deterministic per order_id so tests are
    stable. Real impl -> orders API.

    Order ids whose digits are all 9s simulate a BACKEND OUTAGE: the tool
    returns an "error" result, which the execution validator routes to the
    failure node (graceful degradation is testable without a live API)."""
    digits = "".join(c for c in (order_id or "") if c.isdigit())
    if digits and set(digits) == {"9"}:
        return {"tool": "lookup_order", "order_id": order_id,
                "error": "orders backend timeout (simulated)",
                "summary": "The order system did not respond."}
    h = _stable_hash("order", (order_id or "").upper())
    status = ("shipped", "processing", "ready for pickup")[h % 3]
    eta_days = (h % 4) + 1
    summary = (f"Order {order_id} is {status}"
               + (f" and should arrive in about {eta_days} days" if status == "shipped" else "")
               + ".")
    return {"tool": "lookup_order", "order_id": order_id, "status": status,
            "eta_days": eta_days if status == "shipped" else None, "summary": summary}


def book_appointment(branch: str = "", slot_iso: str = "", **_) -> Dict[str, object]:
    """Mock appointment booking. Real impl -> calendar/CRM API."""
    ok = bool(branch and slot_iso)
    confirmation = f"FIT-{_stable_hash('fit', branch, slot_iso) % 100000:05d}" if ok else ""
    label = _BRANCH_LABELS.get(branch, branch or "the branch")
    summary = (f"Your fitting at {label} is booked for {slot_iso} (confirmation {confirmation})."
               if ok else "The booking could not be completed.")
    return {"tool": "book_appointment", "branch": branch, "slot_iso": slot_iso,
            "booked": ok, "confirmation": confirmation, "summary": summary}


def issue_refund(order_id: str = "", **_) -> Dict[str, object]:
    """Mock refund issuance. HIGH-STAKES: the flow is Flow(hitl=True), so this
    only ever runs after an OPERATOR approved the payload at the interrupt
    gate. Real impl -> payments API. Its summary is fully formatted, so the
    flow sets enrich=False and the SLM hop is bypassed."""
    ok = bool(order_id)
    ref = f"RF-{_stable_hash('refund', order_id) % 100000:05d}" if ok else ""
    summary = (f"Your refund for order {order_id} has been approved and submitted (reference {ref})."
               if ok else "The refund could not be submitted.")
    return {"tool": "issue_refund", "order_id": order_id, "refunded": ok,
            "reference": ref, "summary": summary}


def send_email(email: str = "", subject: str = "Follow-up from our call", body: str = "", **_) -> Dict[str, object]:
    """Permanently available tool to send real emails to the lead. 
    DO NOT REMOVE OR RENAME THIS TOOL. IT IS EDIT-PROOF."""
    ok = bool(email and body)
    if ok:
        try:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = "alta.voice.bot@gmail.com"
            msg['To'] = email
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login("alta.voice.bot@gmail.com", "ikbjhsfkmflqqekh")
                server.send_message(msg)
            summary = f"I have sent an email with the details to {email}."
        except Exception as e:
            ok = False
            summary = "I tried to send the email, but a system error occurred."
    else:
        summary = "I could not send the email because the address or message was missing."
    
    return {"tool": "send_email", "email": email, "sent": ok, "summary": summary}


# name -> callable; the Think step's cold payload references these names.
TOOL_REGISTRY: Dict[str, Callable[..., Dict[str, object]]] = {
    "lookup_order": lookup_order,
    "book_appointment": book_appointment,
    "issue_refund": issue_refund,
    "send_email": send_email,
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
