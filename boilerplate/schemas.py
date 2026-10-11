"""State + structured-output schemas. Generic — do not edit per domain.

Five Pydantic schemas only (anti-sprawl rule):
  * IntentResult   — intent-detection tier: classification + extracted slots.
  * ThinkDecision  — reasoning tier's Think step: act now, or ask for a slot.
  * PlanStep / PlanResult — planner tier's structured output for COMPOUND
    requests: an ordered array of flow actions (same rationale as the others).
  * EnrichVerdict  — ENRICH (SLM) tier: the SLM NEVER writes user-facing prose.
    It returns a structured verdict (tone enum + grounded fact selection +
    self-grounding boolean); a deterministic templater builds the sentence.
    This is a tier CONTRACT, not a variant — the SLM's only safe enrichment
    mode is structured-output-with-verdict, never free rephrasing (which
    reopened anti-pattern #9 and needed a post-hoc regex scrubber).

`intent`, `action`, and slot keys are plain strings (not Literals) because the
intent catalog and slot vocabulary are config-driven; nodes.py clamps invalid
values.
"""

from __future__ import annotations

from typing import Annotated, Dict, Literal, Optional, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


def append_or_reset(old: list | None, new: list | None) -> list:
    """Reducer for AgentState.trace: an EMPTY list resets (the Shell passes
    TURN_RESET's ``trace: []`` at the start of every turn); a non-empty list is
    appended. Nodes only ever emit non-empty lists, so the two cannot collide."""
    if new is None:
        return list(old or [])
    if not new:
        return []
    return list(old or []) + list(new)


class IntentResult(BaseModel):
    """Intent-detection tier output. Extracts slots opportunistically so a
    single-utterance request can be served in one turn.

    Hierarchical routing: the model first commits to a macro CATEGORY
    (ANSWER / FLOW / SYSTEM), then the intent within it — a small model
    classifies far more reliably against 3 categories than a flat list.
    The node re-derives the category from the final intent (config is the
    source of truth), so a category/intent mismatch never corrupts routing."""

    reasoning: str = Field(default="", description="One brief sentence of thought before committing.")
    category: str = Field(default="", description="Macro category first: ANSWER, FLOW, or SYSTEM.")
    intent: str = Field(description="One intent name from the provided catalog (within the category).")
    slots: Dict[str, Optional[str]] = Field(
        default_factory=dict,
        description="Slot values found in the message, keyed by the slot names listed in the prompt. Omit unknowns.",
    )


class ThinkDecision(BaseModel):
    """Reasoning tier (Think step) for tool-backed flows.

    status:
      - act       : all required slots known; the tool will run (Act), then enrich.
      - need_info : a required slot is missing; `response` asks for exactly it.
    """

    reasoning: str = Field(default="", description="Brief thought (chain-of-thought).")
    status: Literal["act", "need_info"] = Field(description="Act now or ask for missing info.")
    slots: Dict[str, Optional[str]] = Field(
        default_factory=dict, description="Resolved slot values (only the flow's slots)."
    )
    response: str = Field(
        default="", description="When need_info: ONE short English clarifying question."
    )


class PlanStep(BaseModel):
    """One step of a compound plan: which flow to run and any slot values the
    planner could extract for it from the user's message alone."""

    action: str = Field(description="One flow intent name from the provided catalog.")
    slots: Dict[str, Optional[str]] = Field(
        default_factory=dict,
        description="Slot values for this step found in the user's message. Omit unknowns.",
    )


class PlanResult(BaseModel):
    """Planner tier output for COMPOUND requests: the ANSWER model is called
    EXACTLY ONCE to turn a multi-action utterance into an ordered step array;
    execution of each step is then fully deterministic (plan_step_node)."""

    reasoning: str = Field(default="", description="One brief sentence of thought.")
    steps: list[PlanStep] = Field(
        default_factory=list,
        description="Ordered steps; only actions from the catalog; at most the stated maximum.",
    )


class EnrichVerdict(BaseModel):
    """ENRICH (SLM) tier output. The SLM is FRAMED, not trusted with prose: it
    classifies the tone of a tool result and SELECTS which facts are worth
    surfacing (copied verbatim from the result), and self-reports whether every
    selected fact is grounded in the source. It writes NO user-facing sentence —
    a deterministic templater (nodes._phrase_from_verdict) assembles the reply
    from a tone-keyed template (config.ENRICH_TEMPLATES) plus these facts.

    Why structured-only: a small model rephrasing free text invents steering
    follow-ups (anti-pattern #9) and needed a fragile post-hoc scrubber. A
    verdict is a narrow, verifiable job a small model does reliably — and every
    field is checkable against the source before it reaches the user."""

    tone: Literal["confirm", "regret", "neutral"] = Field(
        default="neutral",
        description="Tone of the tool result: confirm (success/created), regret (failed/unavailable), neutral (info).",
    )
    key_facts: list[str] = Field(
        default_factory=list,
        description="The few facts worth surfacing, each copied VERBATIM as a value/substring from the tool result JSON. No new words.",
    )
    grounded: bool = Field(
        default=False,
        description="True only if EVERY key_fact appears verbatim in the tool result. Self-check; the node also verifies independently.",
    )


class AgentState(TypedDict, total=False):
    """Lean same-turn state. The Shell re-invokes from START each user turn;
    pending_* fields carry an in-progress slot-fill across turns."""

    recent_messages: Annotated[list[BaseMessage], add_messages]
    user_message: str

    # Intent-detection outputs for this turn. `category` is the macro bucket
    # (ANSWER / FLOW / SYSTEM) derived deterministically from the intent.
    intent: str
    category: str
    slots: Dict[str, Optional[str]]

    # Multi-turn slot-fill memory (persisted by the checkpointer).
    pending_intent: Optional[str]
    pending_slots: Dict[str, Optional[str]]

    # Fast-router flag (per-turn): True when the tier-0 deterministic gate
    # filled a missing slot of the pending flow and the INTENT-tier LLM call
    # was skipped. Telemetry only — routing derives from intent/category.
    fast_routed: bool

    # Depth-1 interrupt archive: when a second tool FLOW interrupts a flow
    # mid slot-fill, the interrupted flow is parked here instead of clobbered:
    # {"intent", "slots", "offered"} — {} when empty. Restored (and cleared)
    # when the user re-enters the flow by name or answers its missing slot;
    # one proactive resume offer is appended after the interrupting flow
    # completes ("offered" makes it one-shot). Overwritten by a newer
    # interruption (depth 1, never a stack). Persisted by the checkpointer;
    # cleared on restart and goodbye; never touched by the plan walk.
    paused_flow: dict

    # Confirmation gate for destructive flows (Flow.confirm=True): the Think
    # step stashes the ready payload here and asks yes/no instead of acting.
    # {"intent", "tool", "args", "question"} — persisted until answered.
    pending_confirmation: dict
    confirmation_declined: bool   # this turn: user said no at a confirm gate

    # Functional session cache: flat whitelist map of HARD transactional
    # identifiers ({"order_id": "AC-12345", "confirmation": "FIT-042"}) merged
    # DETERMINISTICALLY in tool_exec from Flow.cache_keys — no model ever
    # writes here. Injected into intent/think prompts as a KNOWN FACTS line
    # (mirrors the date injection) and used as the variable-mapping bus between
    # plan steps. Persisted by the checkpointer; cleared only on restart.
    session_facts: Dict[str, str]

    # Plan-and-Execute (COMPOUND requests): the planner's ordered step array
    # [{"step", "action", "slots", "status", "summary", "reported",
    #   "dispatch_calls"}] plus the deterministic walk index. status is one of
    # pending/running/paused/complete/failed/skipped. Persist across turns
    # (pause/resume); cleared on completion, abort, restart, decline, HITL
    # denial, or goodbye. The walk is monotonic and doubly bounded
    # (MAX_PLAN_STEPS at creation, MAX_TOOL_CALLS_PER_TURN at execution).
    plan_steps: list
    current_step_index: int

    # Grounding memory: the last completed tool action, persisted across turns
    # ({"tool", "summary", "result"}). Lets the intent tier treat short replies
    # ("cash", "thanks", "why?") as referring to it, and lets chitchat/knowledge
    # answer "how do you know?" from the actual system check instead of a
    # capabilities pitch. Never reset per turn.
    last_action: dict

    # Proactive SDR director (config.CALL_ARC): the cursor + one-shot guard that
    # let an OUTBOUND agent LEAD the sales arc (opener -> discovery -> qualify ->
    # close) instead of only reacting. Both are written ONLY by the director
    # gate at the head of validator_node (nodes._director), a zero-model
    # deterministic function; routing never reads them (routing stays intent-
    # driven). Persisted by the checkpointer and NOT in TURN_RESET — the arc
    # cursor is by definition cross-turn, like stall_count/plan_steps. No-op
    # (both untouched) when config.CALL_ARC is empty, so inbound agents are
    # unchanged.
    #   call_stage    — name of the current Stage; lazy-init to CALL_ARC[0].name,
    #                   advanced monotonically when a Stage's structured
    #                   advance_when is met, reset on restart.
    #   stage_nudged  — the stage whose one-shot proactive move (nudge/line/flow
    #                   entry) has already been made; blocks broken-record
    #                   re-nudging, cleared on every stage advance.
    call_stage: str
    stage_nudged: str

    # Objection architecture (config.OBJECTION_INTENTS): the ordered ledger of
    # distinct objections this lead raised. ONE field serves both jobs — the
    # isolate one-shot guard AND the SDR deliverable — so the A-I-P layer costs
    # a single state field (anti-sprawl).
    #   WRITER    — nodes._objection_gate (zero-model, head of validator_node);
    #               appends the STRUCTURED intent name, never parsed prose.
    #   READER    — the gate itself (empty ⇒ this is the first objection ⇒ the
    #               isolate question fires), _director (a repeat objection
    #               bypasses the stage one-shot so the pivot always happens),
    #               and the "objections" SUMMARY_TEMPLATE source.
    #   LIFECYCLE — persisted by the checkpointer, NOT in TURN_RESET (an
    #               objection ledger is by definition cross-turn, like
    #               stall_count); append-only within a call; reset on restart.
    #               Untouched when OBJECTION_INTENTS is empty.
    objections_raised: list

    # Micro-commitments (config.TIEDOWNS): consecutive agent turns that ended in
    # a STATEMENT since the last landed agreement. The pacing counter behind the
    # tie-down gate.
    #   WRITER    — nodes.validator_node's tie-down block (zero-model): reset to
    #               0 when a tie-down is emitted or when the lead's own message
    #               matches _AFFIRM_RE outside a confirmation gate (a
    #               micro-commitment landed on its own — never nag a lead who is
    #               already agreeing); otherwise incremented.
    #   READER    — nodes._tiedown (fires at >= config.TIEDOWN_EVERY_N_TURNS).
    #   LIFECYCLE — persisted by the checkpointer, NOT in TURN_RESET (pacing is
    #               cross-turn); reset on restart. NEVER written at all when
    #               TIEDOWN_EVERY_N_TURNS is 0, so inbound agents are unchanged.
    turns_since_tiedown: int

    # Lead record (config.SUMMARY_TEMPLATE): the structured, cross-turn record of
    # this call — both durable memory and the SDR's deliverable.
    #   WRITER  — nodes._update_summary (zero-model, at the head of validator_node
    #             every turn) aggregates the structured fields from session_facts /
    #             captured slots / last_action; nodes.build_call_record fills the
    #             'freetext' fields ONCE at call-end, off the reply path.
    #   READER  — nodes._summary_ctx injects a compact view into prompts (so the
    #             short HISTORY_TURNS window never loses what was qualified); the
    #             platform runtime flushes it to a JSON artifact at call-end.
    #   LIFECYCLE — persisted by the checkpointer, NOT in TURN_RESET (cross-turn,
    #             like session_facts); monotonic (fields are set, never cleared);
    #             reset on restart. No-op ({} untouched) when SUMMARY_TEMPLATE is
    #             empty, so inbound/non-SDR agents are unchanged.
    call_summary: dict

    # Agentic-RAG output: the finalized context payload the retrieval subgraph
    # hands back to the parent. The subgraph's internal state (documents,
    # grades, rewrite counters) lives in its OWN TypedDict and never appears
    # here — this single key is the whole contract.
    retrieved_context: str

    # Think→Act payload + result.
    cold_payload: dict          # {"tool": ..., "args": {...}} — set only by the Think step
    tool_action_pending: bool
    tool_result: dict           # deterministic tool output (structured, no prose)
    needs_enrichment: bool      # set by the execution validator: route via ENRICH or bypass
    tool_call_count: int        # circuit breaker: tool executions this turn (reset per turn)
    execution_error: dict       # set by the execution validator on tool failure/breaker trip

    # HITL gate (Flow.hitl=True): the graph is interrupt()-suspended awaiting
    # an OPERATOR decision (distinct from Flow.confirm, the end-user yes/no).
    awaiting_human: bool

    draft_response: str         # pre-validation assistant text
    final_response: str         # post-validation (what the user sees)

    # Stall detector (invariant 25): fingerprint of the previous turn's final
    # reply + how many CONSECUTIVE turns emitted that same reply. Maintained
    # deterministically inside validator_node (an in-node gate, never a graph
    # node); at config.STALL_THRESHOLD identical replies the outgoing text is
    # swapped for the clarify-then-escalate STALL_TEXT. Persisted by the
    # checkpointer — a stall is by definition a cross-turn phenomenon.
    last_reply_fingerprint: str
    stall_count: int

    # Escalation path (invariant 26): set by the deterministic human_handoff
    # SYSTEM intent. The Shell / host system observes this flag to actually
    # page a person — the advertised handoff must be a reachable state, not
    # conversational copy. Never set by a model.
    handoff_requested: bool

    exit_conversation: bool     # Shell ends the session when True

    # Per-turn execution trace (episode_trace.py persists it).
    #   writer:    graph.py's node wrapper — one entry per node that ran, in run
    #              order (sequential nodes only; the reducer appends).
    #   reader:    the Shell after each turn (TraceWriter) and the eval harness,
    #              which assert over it instead of over reply wording.
    #   lifecycle: reset to [] by TURN_RESET at the start of every turn.
    trace: Annotated[list, append_or_reset]
