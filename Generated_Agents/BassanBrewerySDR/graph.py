"""Same-turn multi-model pipeline graph (v3). Generic — routing adapts to config.

    START
      -> intent_detect            (INTENT tier; hierarchical category->intent;
                                   deterministic gates FIRST: a pending yes/no
                                   confirmation, then the FAST ROUTER — a
                                   mid-slot-fill message that deterministically
                                   fills a missing slot skips the model call
                                   and routes straight to think)
      -> [route by intent]
           confirmed action (yes at a gate) -> tool_exec (Act) directly
                                               (or hitl_gate for a liability
                                               flow: confirm first, then the
                                               operator)
           SYSTEM intents (help/restart/
                           human_handoff)   -> system   -> validator
           chitchat                         -> validator
           config.RETRIEVAL_INTENTS: agentic_retrieval (RAG SUBGRAPH, private
                                     state) -> knowledge -> validator
           other config.KNOWLEDGE_INTENTS: knowledge -> validator
           goodbye  -> closing              -> validator
           compound_request (multi-action utterance) -> planner (ANSWER tier,
                ONCE: emits plan_steps) -> plan_step (deterministic controller)
                -> think ... tool ... -> plan_step -> ... until done/paused
           any config.FLOWS intent: think (ANSWER tier)
                -> need_info?               -> validator
                -> state_changing ready?    -> ask yes/no      -> validator
                -> liability ready?         -> hitl_gate: interrupt() —
                                               OPERATOR approves/denies
                -> ready?                   -> tool_exec (Act: authz-checked
                                               BEFORE the tool, breaker-guarded)
                     -> execution_validator (Layer 2.5, deterministic)
                          failure           -> failure -> validator
                          ok, enrich=False  -> validator   (SLM BYPASS)
                          ok, enrich=True   -> enrichment (ENRICH/SLM)
                                            -> validator
      -> validator (RESPONSE validator, exit filter) -> END

Execution-time authorization (authz.py): routing is NOT the gate. tool_exec
refuses a gated tool unless the AuthorizationLedger build_pipeline creates
holds a granted, one-time record for every gate the flow's properties
require, bound to this conversation, agent, configuration fingerprint, flow,
tool and canonical args. The ledger is outside AgentState; nodes reach it only
through the _traced wrapper, which also forwards the conversation's thread_id.

A knowledge/chitchat detour NEVER clears a pending flow or confirmation — the
reply carries a deterministic resume line instead (nodes._resume_suffix).
A second tool FLOW interrupting a pending one is PARKED in the depth-1
interrupt archive (paused_flow: intent + collected slots) instead of being
clobbered; the interrupting flow's completion appends a one-shot resume offer,
and a matching slot answer or re-entry by name restores the parked flow
deterministically (never a blind re-pend; never a stack).

Every path reaches END within a single invocation, so a question is answered
in the SAME turn it's asked (an open hitl_gate interrupt is the ONE sanctioned
suspension: the Shell surfaces it and resumes with Command(resume=...)).
Turn-taking is the Shell's job (the host frontend — voice/SSE runtime, test
harness — re-invokes from START per user message, resetting TURN_RESET fields).
The checkpointer persists pending_* slots across turns for multi-turn
slot-filling; pass a durable checkpointer (e.g. sqlite) for cross-restart
session resume. That is NOT enough for a gated action: confirm/hitl records
live in the in-process AuthorizationLedger, so a restart between a yes or an
approval and its execution refuses the run (fail closed) — see authz.py.

Loops: the agentic_retrieval node encapsulates one loop (a compiled RAG
subgraph with a private state namespace, bounded by config.RAG_MAX_ITERATIONS).
The parent graph stays loop-free with ONE sanctioned exception: the plan-step
walk (plan_step -> think -> ... -> plan_step). It is deterministic (no model
decides whether to continue), monotonic (current_step_index only increases),
and doubly bounded (MAX_PLAN_STEPS at creation, MAX_TOOL_CALLS_PER_TURN at
execution). Budget note: each plan step costs ~5 graph super-steps; the
LangGraph default recursion_limit (25) fits MAX_PLAN_STEPS=3 — raise both
together if a client needs longer plans.
"""

from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any, Callable, Literal

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

import authz
import config
from episode_trace import config_fingerprint
from llm_client import close_call_log, open_call_log
from schemas import AgentState
from nodes import (
    intent_detect_node, knowledge_node, agentic_retrieval_node, chitchat_node,
    closing_node, system_node, think_node, hitl_gate_node, tool_exec_node,
    execution_validator_node, failure_node, enrichment_node, validator_node,
    planner_node, plan_step_node, FLOW_BY_TOOL, _plan_active,
)


def route_by_intent(state: AgentState) -> Literal[
        "knowledge", "retrieval", "chitchat", "closing", "system",
        "think", "tool_exec", "hitl_gate", "planner"]:
    # A resolved confirmation gate (user said yes) carries a ready payload from
    # intent_detect — execute it directly, no second Think pass. A Flow.hitl
    # payload still has to pass the operator gate first. Either way tool_exec
    # re-checks authorization itself; this edge only picks the next human.
    if state.get("tool_action_pending") and state.get("cold_payload"):
        flow = FLOW_BY_TOOL.get(state["cold_payload"].get("tool", ""))
        if flow is not None and "hitl" in authz.flow_gates(flow):
            return "hitl_gate"
        return "tool_exec"
    intent = state.get("intent", "chitchat")
    if intent == "compound_request":
        return "planner"
    if intent in config.SYSTEM_INTENTS:
        return "system"
    if intent in config.RETRIEVAL_INTENTS:
        return "retrieval"
    if intent in config.KNOWLEDGE_INTENTS:
        return "knowledge"
    if intent == "goodbye":
        return "closing"
    if intent in config.FLOWS:
        return "think"
    return "chitchat"


def route_after_planner(state: AgentState) -> Literal["plan_step", "validator"]:
    """A valid plan enters the step walk; an empty plan (every action was
    outside the catalog) already carries a deterministic decline reply."""
    return "plan_step" if _plan_active(state) else "validator"


def route_after_plan_step(state: AgentState) -> Literal["think", "validator"]:
    """The controller either dispatched a step (its action is now the intent ->
    think) or produced a terminal reply (finished / paused / aborted)."""
    plan = state.get("plan_steps") or []
    idx = state.get("current_step_index", 0)
    # "running" is set ONLY by a dispatch; pause/finish/abort all leave the
    # current step non-running (or clear the plan), so status is the routing
    # truth — never draft_response, which may carry a previous step's text.
    if idx < len(plan) and plan[idx].get("status") == "running":
        return "think"
    return "validator"


def route_after_think(state: AgentState) -> Literal["tool_exec", "hitl_gate", "plan_step", "validator"]:
    """Think -> Act only if the reasoning tier produced a ready tool call; a
    liability payload detours through the operator gate; otherwise (need_info,
    confirm question) the reply goes straight to the exit — via the plan
    controller first when a plan is active, so the pause is book-kept."""
    if state.get("awaiting_human"):
        return "hitl_gate"
    if state.get("tool_action_pending"):
        return "tool_exec"
    return "plan_step" if _plan_active(state) else "validator"


def route_after_hitl(state: AgentState) -> Literal["tool_exec", "validator"]:
    """Operator approved -> Act; denied -> the deterministic denial reply
    (hitl_gate itself aborts and reports an active plan on denial)."""
    return "tool_exec" if state.get("tool_action_pending") else "validator"


def route_after_execution(state: AgentState) -> Literal["failure", "enrichment", "plan_step", "validator"]:
    """Layer 2.5 verdict: failure -> graceful degradation; healthy result ->
    ENRICH tier, or straight to the exit when Flow.enrich=False (SLM bypass) —
    the bypass detours through the plan controller when a plan is active."""
    if state.get("execution_error"):
        return "failure"
    if state.get("needs_enrichment"):
        return "enrichment"
    return "plan_step" if _plan_active(state) else "validator"


def route_to_exit(state: AgentState) -> Literal["plan_step", "validator"]:
    """failure/enrichment normally exit; with a plan active they return to the
    controller so the step outcome is recorded (advance or abort)."""
    return "plan_step" if _plan_active(state) else "validator"


# Transient per-turn fields — every Shell (text CLI, voice/SSE runtime, any
# future frontend) resets these at the start of a turn so nothing leaks between
# turns. Lives HERE in the engine because it is part of the turn contract, not
# any one shell's concern. pending_*, pending_confirmation, last_action,
# session_facts, plan_steps, and current_step_index are intentionally NOT
# reset (the checkpointer carries them: multi-turn slot-fill, confirmation
# gates, grounding on the last completed action, the functional session cache,
# and plan pause/resume). last_reply_fingerprint / stall_count are NOT reset
# either — the stall detector (invariant 25) is by definition a cross-turn
# comparison. Same reasoning for objections_raised (the objection ledger) and
# turns_since_tiedown (the micro-commitment pacing counter): both measure across
# turns, and both are reset on restart by system_node, not per turn.
TURN_RESET = {
    "intent": "", "category": "", "slots": {},
    "cold_payload": {}, "tool_action_pending": False, "tool_result": {},
    "needs_enrichment": False, "draft_response": "", "final_response": "",
    "exit_conversation": False, "confirmation_declined": False,
    "retrieved_context": "", "execution_error": {},
    "tool_call_count": 0, "awaiting_human": False, "fast_routed": False,
    "handoff_requested": False, "refusal": {}, "action_outcome": {},
    "trace": [],   # reducer append_or_reset: an empty list resets the per-turn trace
}


# ---------------------------------------------------------------------------
# Per-turn trace (read by episode_trace.TraceWriter and the eval harness).
# Each node is wrapped so it appends ONE structured entry describing what it
# decided, derived from the update it returned — no node body changes, no
# model call, and the node's own exceptions (including a HITL interrupt)
# propagate untouched because the entry is built only after a normal return.
# Live model calls made while the node ran are attached as `model_calls`, with
# `degraded: true` when any of them failed (the node then answered from its
# heuristic fallback). Mock mode makes no calls, so neither key appears.
# ---------------------------------------------------------------------------
def _trace_entry(name: str, state: dict, update: dict) -> dict:
    entry: dict[str, Any] = {"node": name}
    if name == "intent_detect":
        entry.update(intent=update.get("intent"), category=update.get("category"),
                     slots=update.get("slots"), fast_routed=bool(update.get("fast_routed")),
                     confirmed_action=(update.get("cold_payload") or {}).get("tool") or None)
    elif name in ("think", "plan_step"):
        payload = update.get("cold_payload") or {}
        confirm = update.get("pending_confirmation") or {}
        entry.update(tool=payload.get("tool") or confirm.get("tool") or None,
                     args=payload.get("args") or confirm.get("args") or None,
                     act=bool(update.get("tool_action_pending")),
                     awaiting_confirmation=bool(confirm),
                     awaiting_human=bool(update.get("awaiting_human")))
    elif name == "hitl_gate":
        entry.update(approved=bool(update.get("tool_action_pending")),
                     refusal=update.get("refusal") or None)
    elif name == "tool_exec":
        result = update.get("tool_result") or {}
        payload = state.get("cold_payload") or {}
        entry.update(tool=result.get("tool") or payload.get("tool"), args=payload.get("args"),
                     ok=not result.get("error"), error=result.get("error"),
                     tool_status=result.get("tool_status"),
                     refusal=update.get("refusal") or None)
    elif name == "execution_validator":
        err = update.get("execution_error") or {}
        outcome = update.get("action_outcome") or {}
        entry.update(ok=not err, error=err.get("error"), outcome=outcome.get("outcome"),
                     verified=outcome.get("verified"), evidence=outcome.get("evidence"),
                     tool_status=outcome.get("tool_status"))
    elif name == "planner":
        entry.update(steps=len(update.get("plan_steps") or []))
    elif name in ("agentic_retrieval", "knowledge"):
        entry.update(retrieved_chars=len(update.get("retrieved_context") or ""))
    elif name == "validator":
        entry.update(final_response=update.get("final_response"),
                     stall_count=update.get("stall_count"),
                     handoff_requested=bool(update.get("handoff_requested")))
    return entry


def _traced(name: str, fn: Callable, ledger: authz.AuthorizationLedger) -> Callable:
    # Nodes that take part in authorization declare `thread_id` / `ledger`
    # keyword parameters; only those receive them. LangGraph injects the
    # run's config into this wrapper by the parameter NAME `config` — the
    # nodes themselves never see it (their module also imports `config`).
    params = inspect.signature(fn).parameters
    wants_thread, wants_ledger = "thread_id" in params, "ledger" in params

    async def node(state, config: RunnableConfig):
        kwargs: dict[str, Any] = {}
        if wants_thread:
            kwargs["thread_id"] = str((config.get("configurable") or {}).get("thread_id") or "")
        if wants_ledger:
            kwargs["ledger"] = ledger
        calls, token = open_call_log()
        try:
            update = fn(state, **kwargs)
            if inspect.isawaitable(update):
                update = await update
        finally:
            close_call_log(token)
        update = dict(update or {})
        entry = _trace_entry(name, state, update)
        if calls:
            entry["model_calls"] = calls
            entry["degraded"] = any(not c["ok"] for c in calls)
        update["trace"] = [entry]
        return update
    node.__name__ = getattr(fn, "__name__", name)
    return node


def build_pipeline(checkpointer=None, ledger: authz.AuthorizationLedger | None = None):
    # Startup preflight: a misdeclared flow never takes a call.
    authz.preflight_flows(config.FLOWS)
    if ledger is None:
        agent_dir = Path(config.__file__).resolve().parent
        ledger = authz.AuthorizationLedger(
            agent_id=agent_dir.name,
            fingerprint=config_fingerprint(agent_dir, config)["config_sha256"])
    b = StateGraph(AgentState)

    b.add_node("intent_detect", _traced("intent_detect", intent_detect_node, ledger))
    b.add_node("knowledge", _traced("knowledge", knowledge_node, ledger))
    b.add_node("agentic_retrieval", _traced("agentic_retrieval", agentic_retrieval_node, ledger))
    b.add_node("chitchat", _traced("chitchat", chitchat_node, ledger))
    b.add_node("closing", _traced("closing", closing_node, ledger))
    b.add_node("system", _traced("system", system_node, ledger))
    b.add_node("planner", _traced("planner", planner_node, ledger))
    b.add_node("plan_step", _traced("plan_step", plan_step_node, ledger))
    b.add_node("think", _traced("think", think_node, ledger))
    b.add_node("hitl_gate", _traced("hitl_gate", hitl_gate_node, ledger))
    b.add_node("tool_exec", _traced("tool_exec", tool_exec_node, ledger))
    b.add_node("execution_validator", _traced("execution_validator", execution_validator_node, ledger))
    b.add_node("failure", _traced("failure", failure_node, ledger))
    b.add_node("enrichment", _traced("enrichment", enrichment_node, ledger))
    b.add_node("validator", _traced("validator", validator_node, ledger))

    b.add_edge(START, "intent_detect")
    b.add_conditional_edges("intent_detect", route_by_intent, {
        "knowledge": "knowledge", "retrieval": "agentic_retrieval",
        "chitchat": "chitchat", "closing": "closing", "system": "system",
        "think": "think", "tool_exec": "tool_exec", "hitl_gate": "hitl_gate",
        "planner": "planner",
    })

    b.add_conditional_edges("planner", route_after_planner,
                            {"plan_step": "plan_step", "validator": "validator"})
    b.add_conditional_edges("plan_step", route_after_plan_step,
                            {"think": "think", "validator": "validator"})

    b.add_edge("agentic_retrieval", "knowledge")
    b.add_edge("knowledge", "validator")
    b.add_edge("chitchat", "validator")
    b.add_edge("closing", "validator")
    b.add_edge("system", "validator")

    b.add_conditional_edges("think", route_after_think,
                            {"tool_exec": "tool_exec", "hitl_gate": "hitl_gate",
                             "plan_step": "plan_step", "validator": "validator"})
    b.add_conditional_edges("hitl_gate", route_after_hitl,
                            {"tool_exec": "tool_exec", "validator": "validator"})

    b.add_edge("tool_exec", "execution_validator")
    b.add_conditional_edges("execution_validator", route_after_execution,
                            {"failure": "failure", "enrichment": "enrichment",
                             "plan_step": "plan_step", "validator": "validator"})
    b.add_conditional_edges("failure", route_to_exit,
                            {"plan_step": "plan_step", "validator": "validator"})
    b.add_conditional_edges("enrichment", route_to_exit,
                            {"plan_step": "plan_step", "validator": "validator"})
    b.add_edge("validator", END)

    return b.compile(checkpointer=checkpointer or MemorySaver())


if __name__ == "__main__":
    g = build_pipeline()
    try:
        print(g.get_graph().draw_ascii())
    except Exception:
        print("compiled: START -> intent_detect -> [route] -> "
              "[system/retrieval+knowledge/planner->plan_step/think -> hitl? -> tool "
              "-> exec-validator -> failure|enrich|bypass [-> plan_step]] "
              "-> validator -> END")
