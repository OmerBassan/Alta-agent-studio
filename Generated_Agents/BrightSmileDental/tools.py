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

Every tool with a real-world effect (any gated flow) also registers a
read-back in VERIFIERS: verify(args, result) -> (status, detail), status one
of "present" (the system holds exactly this effect), "absent" (it holds
nothing for these args) or "mismatch" (it holds something else). The engine
never takes a tool's own "booked: True" as evidence — only the read-back.
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import smtplib
import threading
import time
from email.mime.text import MIMEText
from typing import Callable, Dict, Optional, Tuple

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


class SimulatedBackend:
    """The mock system of record the effect tools write to and the verifiers
    read back from — what a calendar or payments API is in a real deployment.

    Writer: the effect tools; reader: VERIFIERS; one lock guards both. Ids are
    issued per write (never derived from the args), so a dropped write cannot
    be mistaken for an earlier identical one. In-memory and process-local;
    reset() clears it (tests, a fresh sandbox run).

    Failure injection, read at call time from the environment:
      SIMULATED_FAILURE=drop_write     the tool reports success, nothing is stored
      SIMULATED_FAILURE=reject         the system refuses; the tool returns an error
      SIMULATED_FAILURE=timeout        the write hangs SIMULATED_DELAY_S seconds
      SIMULATED_FAILURE=readback_down  every read-back raises
    SIMULATED_FAILURE_TOOLS (comma list) limits injection to those tools."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._records: Dict[Tuple[str, Tuple], Dict[str, object]] = {}
        self._seq = 0

    def reset(self) -> None:
        with self._lock:
            self._records.clear()
            self._seq = 0

    @staticmethod
    def _failure(tool: str) -> str:
        mode = os.getenv("SIMULATED_FAILURE", "").strip()
        scope = [t.strip() for t in os.getenv("SIMULATED_FAILURE_TOOLS", "").split(",") if t.strip()]
        return mode if mode and (not scope or tool in scope) else ""

    def write(self, tool: str, key: Tuple, record: Dict[str, object], prefix: str) -> Optional[str]:
        """Store `record` under (tool, key) and return the issued id; None when
        the system rejected the write. Under drop_write the id is returned but
        nothing is stored — the lie the read-back exists to catch."""
        mode = self._failure(tool)
        if mode == "reject":
            return None
        if mode == "timeout":
            # Deterministic for tests: the hung write never lands.
            time.sleep(float(os.getenv("SIMULATED_DELAY_S", "30")))
            return None
        with self._lock:
            self._seq += 1
            issued = f"{prefix}-{self._seq:05d}"
            if mode != "drop_write":
                self._records[(tool, key)] = {**record, "id": issued}
        return issued

    def read(self, tool: str, key: Tuple) -> Optional[Dict[str, object]]:
        if self._failure(tool) == "readback_down":
            raise ConnectionError(f"{tool} read-back unavailable (simulated)")
        with self._lock:
            rec = self._records.get((tool, key))
            return dict(rec) if rec else None


BACKEND = SimulatedBackend()


def _read_back(tool: str, key: Tuple, issued: str) -> Tuple[str, str]:
    rec = BACKEND.read(tool, key)
    if rec is None:
        return "absent", f"no {tool} record for {key}"
    if not issued or rec["id"] != issued:
        return "mismatch", f"{tool} record for {key} is {rec['id']}, the tool reported {issued or 'none'}"
    return "present", f"{tool} record {rec['id']} found for {key}"


def _stable_hash(*parts: str) -> int:
    return int(hashlib.md5(":".join(p or "" for p in parts).encode("utf-8")).hexdigest(), 16)


def book_dental_visit(visit_type: str = "", slot_iso: str = "", **_) -> Dict[str, object]:
    """Book a visit in the simulated practice calendar. Real impl -> the
    practice-management system; verify_dental_visit reads that same calendar."""
    confirmation = (BACKEND.write("book_dental_visit", (visit_type, slot_iso),
                                  {"visit_type": visit_type, "slot_iso": slot_iso}, "BSD")
                    if visit_type and slot_iso else None)
    if not confirmation:
        return {"tool": "book_dental_visit", "visit_type": visit_type, "slot_iso": slot_iso,
                "booked": False, "error": "practice calendar rejected the booking",
                "summary": "The visit could not be booked."}
    summary = f"Your {visit_type} visit is booked for {slot_iso} (confirmation {confirmation})."
    return {"tool": "book_dental_visit", "visit_type": visit_type, "slot_iso": slot_iso,
            "booked": True, "confirmation": confirmation, "summary": summary}


def verify_dental_visit(args: dict, result: dict) -> Tuple[str, str]:
    return _read_back("book_dental_visit", (args.get("visit_type", ""), args.get("slot_iso", "")),
                      str(result.get("confirmation") or ""))


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
    # No refund or billing tool exists here BY DESIGN: this agent has no
    # authority over money, so no payload can ever name one (tool_exec
    # refuses an unregistered tool as "no such tool").
    "book_dental_visit": book_dental_visit,
    "send_email": send_email,
}

# tool name -> read-back. Required for every tool a gated flow runs (the
# selftest's structural preflight fails without one); optional otherwise.
VERIFIERS: Dict[str, Callable[[dict, dict], Tuple[str, str]]] = {
    "book_dental_visit": verify_dental_visit,
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
