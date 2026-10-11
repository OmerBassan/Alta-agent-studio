# -*- coding: utf-8 -*-
"""Outcome verification (C4), proven against boilerplate/'s engine.

A tool's own report is not evidence. After a tool runs, execution_validator
reads the effect back from the system the tool wrote to (tools.VERIFIERS) and
classifies the outcome:

  verified    tool ok AND the read-back matches        -> success path
  unchecked   read-only flow with no verifier, tool ok -> success path
  failed      tool returned an error AND the read-back proves nothing landed
              -> FAILURE_TEXT ("nothing was changed" is now backed), retryable
  unverified  anything else after an effect was attempted (timeout, crash,
              dropped write, unreadable or mismatched read-back, no verifier)
              -> UNVERIFIED_TEXT: no success claim, no "nothing changed"
                 claim, no retry invitation, handoff_requested set

The simulated backend in tools.py injects failures via SIMULATED_FAILURE.
"""

import asyncio
import os
import sys

import pytest

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_BASE_URL"] = ""

BOILERPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "boilerplate")
sys.path.insert(0, os.path.abspath(BOILERPLATE_DIR))

import authz  # noqa: E402
import config  # noqa: E402
import nodes  # noqa: E402
import tools  # noqa: E402
from graph import TURN_RESET, build_pipeline  # noqa: E402
from langchain_core.messages import HumanMessage  # noqa: E402
from langgraph.types import Command  # noqa: E402

BOOK = "I'd like to book a fitting at the Downtown branch tomorrow at 3pm"
REFUND = "I want a refund for order AC-12345"


@pytest.fixture(autouse=True)
def clean_backend(monkeypatch):
    monkeypatch.delenv("SIMULATED_FAILURE", raising=False)
    tools.BACKEND.reset()
    yield
    tools.BACKEND.reset()


def _cfg(thread):
    return {"configurable": {"thread_id": thread}}


def _turn(graph, thread, msg):
    payload = dict(TURN_RESET)
    payload["user_message"] = msg
    payload["recent_messages"] = [HumanMessage(content=msg)]
    return asyncio.run(graph.ainvoke(payload, config=_cfg(thread)))


def _book(thread, failure=None, monkeypatch=None):
    g = build_pipeline()
    _turn(g, thread, BOOK)
    if failure:
        monkeypatch.setenv("SIMULATED_FAILURE", failure)
    return _turn(g, thread, "yes")


def _entry(state, node):
    hits = [e for e in state.get("trace") or [] if e["node"] == node]
    assert hits, f"no {node} entry in trace: {[e['node'] for e in state.get('trace') or []]}"
    return hits[-1]


def _assert_no_success_claim(state):
    reply = state["final_response"].lower()
    assert "booked" not in reply and "confirmation" not in reply, reply
    assert "confirmation" not in (state.get("session_facts") or {}), \
        "an unverified confirmation number was cached as a fact"
    assert not nodes._flow_complete("book_fitting", state), \
        "an unverified booking counts as a completed flow"


# ── the healthy path ─────────────────────────────────────────────────────────
def test_verified_success_carries_read_back_evidence():
    st = _book("ok")
    v = _entry(st, "execution_validator")
    assert v["outcome"] == "verified" and v["verified"] is True
    conf = st["tool_result"]["confirmation"]
    assert conf in v["evidence"], v
    assert "booked" in st["final_response"].lower()
    assert st["session_facts"]["confirmation"] == conf
    assert nodes._flow_complete("book_fitting", st)


def test_read_only_flow_without_verifier_is_unchecked():
    g = build_pipeline()
    st = _turn(g, "ro", "where is my order AC-12345")
    v = _entry(st, "execution_validator")
    assert v["outcome"] == "unchecked" and v["verified"] is None


def test_refund_after_operator_approval_is_verified():
    g = build_pipeline()
    _turn(g, "rf", REFUND)
    offer = asyncio.run(g.aget_state(_cfg("rf"))).interrupts[0].value["offer_id"]
    st = asyncio.run(g.ainvoke(Command(resume={"approved": True, "offer_id": offer}),
                               config=_cfg("rf")))
    assert _entry(st, "execution_validator")["outcome"] == "verified"


# ── the tool says OK, the system disagrees ───────────────────────────────────
def test_tool_reports_ok_but_write_never_landed(monkeypatch):
    st = _book("drop", "drop_write", monkeypatch)
    assert _entry(st, "tool_exec")["ok"] is True, "precondition: the tool claimed success"
    v = _entry(st, "execution_validator")
    assert v["outcome"] == "unverified" and v["verified"] is False
    assert config.UNVERIFIED_TEXT in st["final_response"]
    _assert_no_success_claim(st)
    assert st.get("handoff_requested") is True, "the reply promises a person will check"
    assert st.get("pending_intent") is None, "an unknown-state effect must not invite a retry"


def test_read_back_unavailable_is_unverified(monkeypatch):
    st = _book("rbd", "readback_down", monkeypatch)
    assert _entry(st, "execution_validator")["outcome"] == "unverified"
    _assert_no_success_claim(st)


def test_tool_timeout_is_typed_and_never_success(monkeypatch):
    monkeypatch.setattr(config, "TOOL_TIMEOUT_S", 0.05, raising=False)
    monkeypatch.setenv("SIMULATED_DELAY_S", "0.4")
    st = _book("to", "timeout", monkeypatch)
    t = _entry(st, "tool_exec")
    assert t["ok"] is False and "timed out" in t["error"]
    assert st["tool_result"]["tool_status"] == "timeout"
    v = _entry(st, "execution_validator")
    # A timed-out call may still land: absence on read-back proves nothing.
    assert v["outcome"] == "unverified"
    assert config.UNVERIFIED_TEXT in st["final_response"]
    _assert_no_success_claim(st)


def test_rejected_write_is_failed_and_retryable(monkeypatch):
    st = _book("rej", "reject", monkeypatch)
    v = _entry(st, "execution_validator")
    assert v["outcome"] == "failed", v
    assert config.FAILURE_TEXT in st["final_response"]
    _assert_no_success_claim(st)
    assert st.get("pending_intent") == "book_fitting", "a proven no-op stays retryable"


def test_gated_flow_without_a_verifier_is_unverified_at_runtime(monkeypatch):
    monkeypatch.delitem(tools.VERIFIERS, "book_appointment")
    st = _book("nov")
    assert _entry(st, "tool_exec")["ok"] is True
    assert _entry(st, "execution_validator")["outcome"] == "unverified"
    _assert_no_success_claim(st)


def test_read_back_mismatch_is_not_verified():
    args = {"branch": "downtown", "slot_iso": "2026-01-01T15:00:00"}
    first = tools.book_appointment(**args)
    status, _ = tools.VERIFIERS["book_appointment"](args, {**first, "confirmation": "FIT-99999"})
    assert status == "mismatch"


# ── the structural gate ──────────────────────────────────────────────────────
def test_preflight_requires_a_verifier_for_every_gated_flow(monkeypatch):
    assert authz.verification_gaps(config.FLOWS, tools.VERIFIERS) == []
    monkeypatch.delitem(tools.VERIFIERS, "issue_refund")
    gaps = authz.verification_gaps(config.FLOWS, tools.VERIFIERS)
    assert len(gaps) == 1 and "issue_refund" in gaps[0]


def test_selftest_structural_preflight_fails_without_a_verifier(monkeypatch):
    import selftest
    assert not [f for f in selftest.structural_preflight() if "verif" in f]
    monkeypatch.delitem(tools.VERIFIERS, "book_appointment")
    assert [f for f in selftest.structural_preflight() if "book_appointment" in f]
