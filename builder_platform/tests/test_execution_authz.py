# -*- coding: utf-8 -*-
"""Execution-time authorization (C2 + C3), proven against boilerplate/'s engine.

tool_exec must refuse a gated tool BEFORE it runs unless a platform-owned,
one-time authorization record exists for every gate the flow's declared
action properties require, bound to (conversation, agent, configuration
fingerprint, flow, tool, canonical args). The records live in the
AuthorizationLedger, outside AgentState, so nothing a node returns or a
caller injects into state can mint one.

Adversarial cases (each executed the tool before this change):
  1. a payload modified after the yes / during the operator suspension;
  2. an operator approval replayed onto a later request;
  3. an approval or confirmation reused from another conversation;
  4. a forged approval: pre-set tool_action_pending/cold_payload or
     pending_confirmation with no platform record behind it.
"""

import asyncio
import dataclasses
import os
import sys

import pytest

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_BASE_URL"] = ""

BOILERPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "boilerplate")
sys.path.insert(0, os.path.abspath(BOILERPLATE_DIR))

import config  # noqa: E402
import nodes  # noqa: E402
import tools  # noqa: E402
from graph import TURN_RESET, build_pipeline  # noqa: E402
from langchain_core.messages import HumanMessage  # noqa: E402
from langgraph.types import Command  # noqa: E402

BOOK = "I'd like to book a fitting at the Downtown branch tomorrow at 3pm"
REFUND = "I want a refund for order AC-12345"


# ── harness ──────────────────────────────────────────────────────────────────
@pytest.fixture
def calls(monkeypatch):
    """Record every real execution of the two gated demo tools."""
    seen = []
    for name in ("book_appointment", "issue_refund"):
        real = tools.TOOL_REGISTRY[name]

        def wrapped(*, _real=real, _name=name, **args):
            seen.append((_name, dict(args)))
            return _real(**args)
        monkeypatch.setitem(tools.TOOL_REGISTRY, name, wrapped)
    return seen


@pytest.fixture
def both_gated(monkeypatch):
    """book_fitting declared state_changing AND liability -> confirm + hitl."""
    flow = dataclasses.replace(config.FLOWS["book_fitting"],
                               properties=frozenset({"state_changing", "liability"}))
    monkeypatch.setitem(config.FLOWS, "book_fitting", flow)
    monkeypatch.setitem(nodes.FLOW_BY_TOOL, flow.tool, flow)
    return flow


def _cfg(thread):
    return {"configurable": {"thread_id": thread}}


def _turn(graph, thread, msg, **inject):
    payload = dict(TURN_RESET)
    payload["user_message"] = msg
    payload["recent_messages"] = [HumanMessage(content=msg)]
    payload.update(inject)
    return asyncio.run(graph.ainvoke(payload, config=_cfg(thread)))


def _pending_interrupt(graph, thread):
    snap = asyncio.run(graph.aget_state(_cfg(thread)))
    return snap.interrupts[0].value if snap.interrupts else None


def _decision_for(graph, thread, approved=True):
    """What a legitimate operator console sends: approve THIS offer."""
    return {"approved": approved, "offer_id": _pending_interrupt(graph, thread).get("offer_id")}


def _resume(graph, thread, decision):
    return asyncio.run(graph.ainvoke(Command(resume=decision), config=_cfg(thread)))


def _nodes(state):
    return [e["node"] for e in state.get("trace") or []]


# ── the intended path: both gates, confirmation first ────────────────────────
def test_both_gates_confirm_then_operator_then_execute(both_gated, calls):
    g = build_pipeline()
    st = _turn(g, "t", BOOK)
    assert st.get("pending_confirmation"), "turn 1 must ask the user first"
    assert not st.get("__interrupt__") and not calls

    st = _turn(g, "t", "yes")
    assert st.get("__interrupt__"), "after yes the operator gate must suspend"
    assert not calls, "nothing runs before the operator approves"
    offered = _pending_interrupt(g, "t")["args"]

    st = _resume(g, "t", _decision_for(g, "t"))
    assert calls == [("book_appointment", offered)]
    assert _nodes(st)[-5:-2] == ["hitl_gate", "tool_exec", "execution_validator"]
    assert not st.get("refusal")


def test_confirm_only_and_hitl_only_happy_paths(calls):
    g = build_pipeline()
    _turn(g, "c", BOOK)
    _turn(g, "c", "yes")
    assert [c[0] for c in calls] == ["book_appointment"]

    st = _turn(g, "h", REFUND)
    assert st.get("__interrupt__") and len(calls) == 1
    _resume(g, "h", _decision_for(g, "h"))
    assert calls[-1] == ("issue_refund", {"order_id": "AC-12345"})


def test_operator_denial_is_a_business_refusal(calls):
    g = build_pipeline()
    _turn(g, "d", REFUND)
    st = _resume(g, "d", _decision_for(g, "d", approved=False))
    assert not calls
    assert st["refusal"]["kind"] == "business_refusal"
    assert st["final_response"] == config.HITL_DENIED_TEXT


# ── 1. modified payload ──────────────────────────────────────────────────────
def test_payload_modified_between_question_and_yes_is_refused(calls):
    g = build_pipeline()
    _turn(g, "m1", BOOK)
    confirm = dict(_state(g, "m1")["pending_confirmation"])
    confirm["args"] = {**confirm["args"], "branch": "airport"}
    asyncio.run(g.aupdate_state(_cfg("m1"), {"pending_confirmation": confirm}))
    st = _turn(g, "m1", "yes")
    assert not calls, "a payload the user never heard was executed"
    assert st["refusal"]["kind"] == "platform_error"


def test_payload_modified_during_operator_suspension_is_refused(calls):
    g = build_pipeline()
    _turn(g, "m2", REFUND)
    shown = _decision_for(g, "m2")   # the operator approves what they were shown
    asyncio.run(g.aupdate_state(_cfg("m2"), {
        "cold_payload": {"tool": "issue_refund", "args": {"order_id": "AC-99999"}}}))
    st = _resume(g, "m2", shown)
    assert not calls, "the operator approved AC-12345; AC-99999 must not run"
    assert st["refusal"]["kind"] == "platform_error"


def test_operator_approving_a_payload_the_user_never_confirmed_is_refused(both_gated, calls):
    g = build_pipeline()
    _turn(g, "m3", BOOK)
    confirm = dict(_state(g, "m3")["pending_confirmation"])
    confirm["args"] = {**confirm["args"], "branch": "airport"}
    asyncio.run(g.aupdate_state(_cfg("m3"), {"pending_confirmation": confirm}))
    _turn(g, "m3", "yes")
    assert _pending_interrupt(g, "m3")["args"]["branch"] == "airport"
    # The operator is shown the TAMPERED payload and genuinely approves it;
    # the user confirmed the original, so the run must still be refused.
    st = _resume(g, "m3", _decision_for(g, "m3"))
    assert not calls
    assert st["refusal"] == {"kind": "platform_error", "gate": "confirm",
                             "tool": "book_appointment",
                             "reason": "authorization is for a different payload"}


# ── 2. replayed approval ─────────────────────────────────────────────────────
def test_replayed_operator_approval_is_refused(calls):
    g = build_pipeline()
    _turn(g, "r", REFUND)
    first = _decision_for(g, "r")
    _resume(g, "r", first)
    assert len(calls) == 1

    st = _turn(g, "r", REFUND)
    assert st.get("__interrupt__"), "a second refund must ask the operator again"
    st = _resume(g, "r", first)        # the old approval, replayed verbatim
    assert len(calls) == 1, "one approval authorized two refunds"
    assert st["refusal"]["kind"] == "platform_error"


def test_consumed_authorization_cannot_execute_again(calls):
    g = build_pipeline()
    _turn(g, "r2", BOOK)
    _turn(g, "r2", "yes")
    executed = calls[-1][1]
    st = _turn(g, "r2", "hello", tool_action_pending=True,
               cold_payload={"tool": "book_appointment", "args": executed})
    assert len(calls) == 1
    assert st["refusal"]["kind"] == "platform_error"


# ── 3. cross-conversation reuse ──────────────────────────────────────────────
def test_operator_approval_from_another_conversation_is_refused(calls):
    g = build_pipeline()
    _turn(g, "x-a", REFUND)
    _turn(g, "x-b", REFUND)
    st = _resume(g, "x-b", _decision_for(g, "x-a"))
    assert not calls, "conversation A's approval authorized conversation B"
    assert st["refusal"]["kind"] == "platform_error"


def test_confirmation_from_another_conversation_is_refused(both_gated, calls):
    g = build_pipeline()
    _turn(g, "y-a", BOOK)
    _turn(g, "y-a", "yes")                      # A confirmed; A's payload:
    payload = dict(_state(g, "y-a")["cold_payload"])
    _turn(g, "y-b", "hello", tool_action_pending=True, cold_payload=payload)
    _resume(g, "y-b", _decision_for(g, "y-b"))  # B's operator approves B's offer
    assert not calls, "B executed on the strength of A's confirmation"


# ── 4. forged approval ───────────────────────────────────────────────────────
def test_forged_ready_payload_is_refused(calls):
    g = build_pipeline()
    st = _turn(g, "f1", "hello", tool_action_pending=True, cold_payload={
        "tool": "book_appointment",
        "args": {"branch": "downtown", "slot_iso": "2026-01-01T15:00:00"}})
    assert not calls, "a pre-set tool_action_pending executed with no confirmation"
    assert st["refusal"]["kind"] == "platform_error"


def test_forged_pending_confirmation_is_refused(calls):
    g = build_pipeline()
    st = _turn(g, "f2", "yes", pending_confirmation={
        "intent": "book_fitting", "tool": "book_appointment",
        "args": {"branch": "airport", "slot_iso": "2026-01-01T15:00:00"}})
    assert not calls, "a 'yes' to a question the platform never asked executed"
    assert st["refusal"]["kind"] == "platform_error"


def test_bare_boolean_operator_approval_is_refused(calls):
    """An approval must name the offer it approves; a bare True does not."""
    g = build_pipeline()
    _turn(g, "f3", REFUND)
    _resume(g, "f3", {"approved": True})
    assert not calls


# ── action properties -> gates, and the structural preflight ────────────────
def test_property_set_maps_to_gates():
    import authz
    assert authz.required_gates(frozenset()) == frozenset()
    assert authz.required_gates({"state_changing"}) == {"confirm"}
    assert authz.required_gates({"liability"}) == {"hitl"}
    assert authz.required_gates({"state_changing", "liability"}) == {"confirm", "hitl"}


def test_shipped_flows_pass_preflight():
    import authz
    authz.preflight_flows(config.FLOWS)


@pytest.mark.parametrize("bad, why", [
    ({"properties": "liability"}, "set"),               # a str is iterable chars
    ({"properties": ["liability"]}, "set"),
    ({"properties": frozenset({"liabilty"})}, "unknown"),
])
def test_preflight_rejects_misdeclared_flow(bad, why):
    import authz
    flows = dict(config.FLOWS)
    flows["request_refund"] = dataclasses.replace(flows["request_refund"], **bad)
    with pytest.raises(authz.FlowDeclarationError, match=why):
        authz.preflight_flows(flows)


def test_preflight_rejects_gated_tool_shared_by_two_flows():
    import authz
    flows = dict(config.FLOWS)
    flows["refund_again"] = dataclasses.replace(flows["request_refund"],
                                                properties=frozenset())
    with pytest.raises(authz.FlowDeclarationError, match="issue_refund"):
        authz.preflight_flows(flows)


def test_build_pipeline_refuses_to_start_on_a_misdeclared_flow(monkeypatch):
    import authz
    bad = dataclasses.replace(config.FLOWS["request_refund"], properties=frozenset({"money"}))
    monkeypatch.setitem(config.FLOWS, "request_refund", bad)
    with pytest.raises(authz.FlowDeclarationError):
        build_pipeline()


@dataclasses.dataclass(frozen=True)
class _PreDay2Flow:
    """The Flow shape an agent's config.py had before `properties` existed —
    Flow lives in each agent's own config.py, so old agents still carry it."""
    tool: str
    slots: tuple
    slot_prompts: dict = dataclasses.field(default_factory=dict)
    confirm: bool = False
    confirm_template: str = ""
    validators: dict = dataclasses.field(default_factory=dict)
    enrich: bool = True
    hitl: bool = False
    cache_keys: tuple = ()


def test_flow_without_properties_field_still_starts_and_is_gated(monkeypatch, calls):
    shipped = config.FLOWS["book_fitting"]
    old = _PreDay2Flow(tool=shipped.tool, slots=shipped.slots, slot_prompts=shipped.slot_prompts,
                       confirm=True, confirm_template=shipped.confirm_template,
                       cache_keys=shipped.cache_keys)
    monkeypatch.setitem(config.FLOWS, "book_fitting", old)
    monkeypatch.setitem(nodes.FLOW_BY_TOOL, old.tool, old)
    g = build_pipeline()                      # must not raise AttributeError
    st = _turn(g, "old1", "hello", tool_action_pending=True, cold_payload={
        "tool": "book_appointment",
        "args": {"branch": "downtown", "slot_iso": "2026-01-01T15:00:00"}})
    assert not calls and st["refusal"]["kind"] == "platform_error"
    _turn(g, "old2", BOOK)
    _turn(g, "old2", "yes")
    assert [c[0] for c in calls] == ["book_appointment"]


# ── the ledger itself: binding, one-time use, expiry ─────────────────────────
def _ledger(**kw):
    import authz
    return authz.AuthorizationLedger(agent_id=kw.pop("agent", "acme"),
                                     fingerprint=kw.pop("fp", "f" * 64), **kw)


def test_ledger_binds_agent_and_configuration_fingerprint():
    a, b = _ledger(fp="1" * 64), _ledger(fp="2" * 64)
    bind_a = a.binding("t", "request_refund", "issue_refund", {"order_id": "AC-1"})
    bind_b = b.binding("t", "request_refund", "issue_refund", {"order_id": "AC-1"})
    assert bind_a.digest != bind_b.digest
    oid = a.offer("hitl", bind_a)
    assert a.grant("hitl", "t", oid) is None
    # A record minted under one effective configuration is not valid under
    # another, even for a byte-identical payload in the same conversation.
    refusal = a.consume(frozenset({"hitl"}), bind_b)
    assert refusal is not None and refusal.kind == "platform_error"
    assert _ledger(agent="other").binding("t", "request_refund", "issue_refund",
                                          {"order_id": "AC-1"}).digest != bind_a.digest


def test_ledger_args_are_canonicalized():
    led = _ledger()
    one = led.binding("t", "f", "tool", {"a": "1", "b": "2"})
    two = led.binding("t", "f", "tool", {"b": "2", "a": "1"})
    assert one.digest == two.digest


def test_ledger_consume_is_one_time_and_all_or_nothing():
    led = _ledger()
    bind = led.binding("t", "f", "tool", {"x": "1"})
    led.offer("confirm", bind)
    assert led.grant("confirm", "t") is None
    assert led.consume(frozenset({"confirm", "hitl"}), bind) is not None   # hitl missing
    assert led.consume(frozenset({"confirm"}), bind) is not None, \
        "a failed attempt must burn the grant, not leave it for a retry"
    led.offer("confirm", bind)
    led.grant("confirm", "t")
    assert led.consume(frozenset({"confirm"}), bind) is None
    assert led.consume(frozenset({"confirm"}), bind) is not None


def test_ledger_records_expire():
    now = [1000.0]
    led = _ledger(ttl_s=60, clock=lambda: now[0])
    bind = led.binding("t", "f", "tool", {})
    oid = led.offer("hitl", bind)
    now[0] += 61
    assert led.grant("hitl", "t", oid) is not None
    assert led.consume(frozenset({"hitl"}), bind) is not None


def _state(graph, thread):
    return asyncio.run(graph.aget_state(_cfg(thread))).values
