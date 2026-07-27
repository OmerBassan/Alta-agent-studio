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
import logging
import os
import re
import smtplib
from email.mime.text import MIMEText
from typing import Callable, Dict

logger = logging.getLogger(__name__)

# SMTP config lives in the environment, NEVER in source (no hardcoded secrets).
# A real deployment sets these in .env; with no credentials the tool runs in
# MOCK mode (no network) so the agent and its selftest run credential-free —
# mock-first, exactly like every other tool. The live send carries an explicit
# timeout so a hung mail server returns a typed failure instead of hanging the
# turn (a blocking socket with no timeout is the classic dead-air trap).
_SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
_SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
_SMTP_USER = os.getenv("SMTP_USER", "")
_SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
_SMTP_FROM = os.getenv("SMTP_FROM", "") or _SMTP_USER
_SMTP_TIMEOUT_S = float(os.getenv("SMTP_TIMEOUT_S", "10"))

# Canonical email pattern — used at the SMTP boundary to pull a clean address
# out of a raw slot value. Voice STT frequently appends trailing punctuation
# ("name@site.com?") or surrounding words; sending that verbatim makes Gmail
# reject the recipient and the whole follow-up silently fails.
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")

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
    DO NOT REMOVE OR RENAME THIS TOOL. IT IS EDIT-PROOF.

    Boundary sanitation: the recipient is extracted with _EMAIL_RE, so a raw
    slot value carrying trailing punctuation or stray words ("name@site.com?")
    still yields a deliverable address. A value with no valid address fails
    gracefully here instead of throwing at the SMTP layer.

    Credentials come from the environment (SMTP_USER/SMTP_PASSWORD/…), never
    from source. With no credentials set the tool runs in MOCK mode — it does
    NOT touch the network and reports a mock send — so the agent and its
    selftest run credential-free. The live SMTP call carries an explicit
    timeout; a hung server returns a typed failure, never dead air."""
    m = _EMAIL_RE.search(email or "")
    clean = m.group(0) if m else ""
    if not (clean and body):
        return {"tool": "send_email", "email": clean or email, "sent": False,
                "summary": "I could not send the email because the address or message was missing."}

    if not (_SMTP_USER and _SMTP_PASSWORD):
        # MOCK send: no credentials configured -> never touch the network.
        return {"tool": "send_email", "email": clean, "sent": True, "mock": True,
                "summary": f"I have sent an email with the details to {clean}."}

    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = _SMTP_FROM
        msg['To'] = clean
        with smtplib.SMTP_SSL(_SMTP_HOST, _SMTP_PORT, timeout=_SMTP_TIMEOUT_S) as server:
            server.login(_SMTP_USER, _SMTP_PASSWORD)
            server.send_message(msg)
        return {"tool": "send_email", "email": clean, "sent": True,
                "summary": f"I have sent an email with the details to {clean}."}
    except (smtplib.SMTPException, OSError) as exc:
        logger.warning("send_email to %s failed: %s", clean, exc)
        return {"tool": "send_email", "email": clean, "sent": False,
                "summary": "I tried to send the email, but a system error occurred."}


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
