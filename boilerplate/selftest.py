# -*- coding: utf-8 -*-
"""Scripted self-test: runs a multi-intent conversation through the pipeline in
MOCK mode and asserts the architectural invariants. Run after every
customization pass (`python selftest.py`); exit code 0 = PASS.

What it proves (v3):
  - chitchat never ends the session (the classic premature-goodbye bug)
  - hierarchical routing: every turn lands in the right ANSWER/FLOW/SYSTEM category
  - SYSTEM intents (help/restart) are deterministic; restart clears pending state
  - knowledge questions are answered in the SAME turn
  - RETRIEVAL_INTENTS run the Agentic-RAG subgraph and the subgraph's private
    state (documents/grades/counters) NEVER leaks into the parent AgentState
  - a corpus miss loops, hits the RAG_MAX_ITERATIONS circuit breaker, and gets
    the honest "won't guess" fallback — never a hallucinated policy
  - a HUNG retrieval loop trips the RAG_TIMEOUT_SECONDS wall clock and degrades
    to a single deterministic retrieve pass — the turn still answers, never
    crashes or hangs
  - a single-utterance flow request runs intent -> think -> tool -> exec-validator
    -> enrich in one turn
  - slot validators normalize/reject values before they reach a tool
  - ENTITY RESOLVERS ground referential values ("any branch") against the
    catalog and bounce unresolvable ones with a clarifying question
  - LIVE-VALUE HOOKS (preflight, no graph): resolvers/validators are exercised
    DIRECTLY with raw LLM-style slot values. The conversation script alone
    cannot catch a missing resolver — mock extractors pre-normalize values
    before slots are set, so a live-only canonicalization gap (raw "tomatoes"
    against a "tomato" catalog key) is invisible to it
  - STRUCTURAL LINTS (preflight, no graph): config SHAPE is gated so a
    customization can't silently drop a mandatory rule — every distinct
    resolver/validator callable is exercised by a HOOK_CHECK, and the
    human_handoff escalation path is reachable with STALL_TEXT's escape phrase
    actually routing into it (invariants 21c / 25 / 26)
  - after a tool runs, last_action grounds follow-ups ("how do you know?")
    instead of a capabilities pitch — and the session stays alive
  - a failed tool routes execution_validator -> failure: graceful reply, session
    alive, flow re-pended for retry (never a crash, never silent success)
  - a knowledge detour mid slot-fill does NOT kill the pending flow; the reply
    carries a resume line and the flow completes afterwards
  - FAST ROUTER (tier-0 gate, preflight + script): mid slot-fill, a message
    that deterministically fills a missing slot bypasses the INTENT-tier call
    (fast_routed=True) — and EVERY doubt (negation, other-intent keyword, no
    extraction, resolver bounce, kill switch) falls through to the model path
  - INTERRUPT ARCHIVE (depth 1): a second tool FLOW mid slot-fill PARKS the
    pending flow (intent + collected slots) instead of clobbering it; the
    interrupting flow's completion carries a ONE-SHOT resume offer; a bare
    slot answer or re-entry by name restores the parked flow without
    re-asking collected slots; restart/goodbye clear the archive
  - a Flow(confirm=True) flow asks yes/no before acting and only acts on "yes"
  - a Flow(hitl=True) flow interrupt()-suspends for OPERATOR approval and only
    acts on Command(resume={"approved": True})
  - a Flow(enrich=False) result bypasses the SLM (needs_enrichment stays False)
    yet still produces a clean deterministic reply
  - the circuit breaker refuses tool execution past MAX_TOOL_CALLS_PER_TURN
  - FUNCTIONAL SESSION CACHE: successful tools merge ONLY Flow.cache_keys
    fields into session_facts (whitelist, zero-inference); restart clears it
  - PLAN-AND-EXECUTE: a compound utterance routes to the planner ONCE, then a
    deterministic bounded step walk runs each step through the ordinary
    think->act machinery — same-turn when possible, pausing cleanly at a
    missing slot / confirm gate / HITL interrupt and resuming next turn
  - plan variable mapping: a later step's missing slot auto-fills from
    session_facts produced by an earlier step (never re-asked)
  - PLANNER CLAMP (preflight, no graph): unknown actions are dropped and the
    step array is truncated to MAX_PLAN_STEPS before any execution
  - COMPACTION (preflight, no graph): oversized list fields crush to a bounded
    salient subset (error + rare-status items always survive), the sentinel
    ref round-trips through retrieve_full_result, error results and small
    lists pass through untouched, and crush_result never raises
  - STALL DETECTOR (invariant 25, preflight + script): the validator's in-node
    gate swaps the N-th consecutive identical reply for the deterministic
    clarify-then-escalate STALL_TEXT; a changed reply resets the counter;
    STALL_THRESHOLD=0 disables the gate entirely
  - ESCALATION PATH (invariant 26): an explicit ask for a person routes to the
    deterministic human_handoff SYSTEM intent — pending work clears, the
    handoff_requested flag is raised for the Shell/host, session stays alive
  - DYNAMIC RAG (report-12072026, preflight): a pronoun query is primed and
    rewritten with deterministic conversation context (co-reference rescue),
    an identical repeat question is served from the TTL context cache without
    touching the subgraph, referential queries are never cached, and
    RETRIEVAL_MIN_SCORE drops weak matches into the honest fallback
  - only an explicit goodbye sets exit_conversation
"""

import asyncio
import os
import sys

# Force mock mode BEFORE any project import reads the environment.
os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_BASE_URL"] = ""

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langchain_core.messages import HumanMessage  # noqa: E402
from langgraph.types import Command  # noqa: E402

import config  # noqa: E402
from graph import build_pipeline, TURN_RESET as _TURN_RESET  # noqa: E402

# Special message: resume an open HITL interrupt with an operator approval.
RESUME_APPROVE = "__RESUME_APPROVE__"

# Direct hook checks with RAW, live-LLM-style slot values.        [CUSTOMIZE]
# In live mode the intent/think tiers hand over whatever text the model
# extracted — resolvers/validators are the ONLY normalization those values get
# (mock extractors pre-normalize, so the SCRIPT below can never catch a gap
# here). Every slot that keys into a catalog/DB must have a resolver, and its
# checks belong in this list: aliases, plural/synonym forms, unresolvable
# values, and out-of-bounds numbers quoting REAL catalog limits.
# (hook, flow, slot, raw_value, other_slots, want_ok, substring of output)
HOOK_CHECKS = [
    # Aliases and referential phrases canonicalize against the branch catalog.
    ("resolver", "book_fitting", "branch", "the River Street store", {}, True, "downtown"),
    ("resolver", "book_fitting", "branch", "Westfield", {}, True, "mall"),
    # Referential/unknown -> clarifying question listing the real options.
    ("resolver", "book_fitting", "branch", "whichever is closest", {}, False, "Downtown, Mall, or Airport"),
    ("resolver", "book_fitting", "branch", "the Paris branch", {}, False, "Downtown, Mall, or Airport"),
    # Format validators normalize raw shapes and bounce garbage with guidance.
    ("validator", "order_status", "order_id", "12345", {}, True, "AC-12345"),
    ("validator", "order_status", "order_id", "ac98765", {}, True, "AC-98765"),
    ("validator", "order_status", "order_id", "yesterday's one", {}, False, "AC-12345"),
]


def run_hook_checks() -> list:
    failures = []
    for kind, flow_name, slot, raw, others, want_ok, want_sub in HOOK_CHECKS:
        fn = (config.ENTITY_RESOLVERS.get(slot) if kind == "resolver"
              else config.FLOWS[flow_name].validators.get(slot))
        if fn is None:
            failures.append(f"hook check: no {kind} registered for slot {slot!r}")
            continue
        ok, out = fn(raw, dict(others))
        if ok != want_ok or want_sub.lower() not in str(out).lower():
            failures.append(f"hook check {kind}/{slot}({raw!r}): "
                            f"expected ok={want_ok} & …{want_sub!r}…, got ok={ok}, out={out!r}")
    return failures

# (user message, dict of expected state assertions)                [CUSTOMIZE]
# Assertion keys: plain state keys, plus:
#   _reply_contains   substring (or list of substrings) expected in the reply
#   _tool             cold_payload tool name (None = no tool ran this turn)
#   _args             subset match on cold_payload args
#   _confirm_pending  whether a confirmation gate is open after the turn
#   _interrupted      whether a HITL interrupt is open after the turn
#   _absent           state keys that must NOT exist (subgraph isolation)
#   _facts_keys       keys that must be present in session_facts
#   _preseed          dict merged into the turn's input payload (breaker tests)
SCRIPT = [
    ("hi there, how are you?",
     {"intent": "chitchat", "category": "ANSWER", "exit_conversation": False}),
    # SYSTEM intent: deterministic capabilities listing, no model.
    ("what can you do for me?",
     {"intent": "help", "category": "SYSTEM", "exit_conversation": False,
      "_reply_contains": "track an order"}),
    ("what are your opening hours?",
     {"intent": "faq_hours", "category": "ANSWER", "exit_conversation": False,
      "_reply_contains": "9:00"}),
    # Agentic-RAG: retrieval subgraph answers policy questions; its private
    # loop state must never leak into the parent AgentState.
    ("what's your shipping policy?",
     {"intent": "faq_policy", "category": "ANSWER",
      "_reply_contains": "3-5 business days",
      "_absent": ["documents", "sufficient", "rewrite_count", "original_query"]}),
    # Corpus miss -> rewrite loop -> RAG_MAX_ITERATIONS circuit breaker ->
    # honest fallback, never a hallucinated policy.
    ("what's your policy on bringing pet llamas into the store?",
     {"intent": "faq_policy", "category": "ANSWER", "exit_conversation": False,
      "_reply_contains": "won't guess"}),
    # Validator normalization: bare digits -> canonical AC- id before the tool;
    # healthy result routes through the execution validator to ENRICH.
    ("where is my order 12345?",
     {"intent": "order_status", "category": "FLOW", "_tool": "lookup_order",
      "needs_enrichment": True, "_args": {"order_id": "AC-12345"}}),
    # Grounding: challenge the previous answer -> explained from last_action,
    # session stays alive (no deflection to a capabilities pitch).
    ("how do you know that?",
     {"intent": "chitchat", "exit_conversation": False, "_reply_contains": "live system"}),
    # Execution validator failure path: all-9s order simulates a backend
    # outage -> graceful failure reply, session alive, flow re-pended.
    ("where is my order 99999?",
     {"intent": "order_status", "_tool": "lookup_order", "needs_enrichment": False,
      "pending_intent": "order_status", "exit_conversation": False,
      "_reply_contains": "snag"}),
    # A second FLOW interrupting the re-pended one is ARCHIVED, not clobbered
    # (depth-1 interrupt archive): the failed order_status keeps its slots.
    ("can I book a fitting?",
     {"intent": "book_fitting", "pending_intent": "book_fitting", "needs_enrichment": False,
      "_paused": "order_status"}),
    # Detour mid slot-fill: knowledge answer + resume line, pending flow SURVIVES.
    ("actually, what's your return policy?",
     {"intent": "faq_returns", "pending_intent": "book_fitting",
      "_reply_contains": "Downtown", "exit_conversation": False}),
    # Entity resolution: "any branch" is referential — bounced against the
    # catalog with a clarifying question, never passed to a tool literally.
    ("any branch works, tomorrow at 3pm",
     {"intent": "book_fitting", "pending_intent": "book_fitting", "_tool": None,
      "fast_routed": False,   # resolver bounce -> the gate must NOT bypass
      "_reply_contains": "Downtown, Mall, or Airport"}),
    # Both slots now valid -> confirm gate (book_fitting is confirm=True):
    # asks yes/no, does NOT act yet. A bare slot answer mid slot-fill takes
    # the FAST-ROUTER path (no INTENT-tier call).
    ("the downtown store please",
     {"intent": "book_fitting", "_tool": None, "_confirm_pending": True,
      "fast_routed": True,
      "_reply_contains": "yes/no"}),
    # The booking completes -> ONE-SHOT resume offer for the archived
    # order_status flow is appended deterministically (and marked offered:
    # later completions must never nag again).
    ("yes please",
     {"intent": "book_fitting", "_tool": "book_appointment", "needs_enrichment": True,
      "_confirm_pending": False, "_reply_contains": ["booked", "didn't finish"]}),
    # HITL gate: refund is Flow(hitl=True) -> the graph SUSPENDS with the
    # ready payload; nothing executes until an operator approves.
    ("I'd like a refund for order 12345",
     {"intent": "request_refund", "category": "FLOW", "_interrupted": True}),
    # Operator approves -> tool runs; enrich=False -> SLM bypassed, reply is
    # the deterministic summary + declared hint.
    (RESUME_APPROVE,
     {"_tool": "issue_refund", "needs_enrichment": False, "_interrupted": False,
      "_args": {"order_id": "AC-12345"}, "_reply_contains": "refund",
      "exit_conversation": False}),
    # Circuit breaker: with the per-turn budget already spent, the Act is
    # refused and degrades gracefully instead of running away. Re-entering the
    # archived order_status BY NAME pops the archive (its slots restored, the
    # extracted id winning the merge).
    ("where is my order 12345?",
     {"_preseed": {"tool_call_count": 3}, "intent": "order_status",
      "_reply_contains": "snag", "pending_intent": "order_status",
      "_paused": None, "exit_conversation": False}),
    # SLOT REFUSAL (tier-0, no model): a lead who declines a question is never
    # asked it again — the engine marks the asked slot SLOT_REFUSED and Think
    # moves to the NEXT missing slot instead of looping on the refused one.
    ("can I book one more fitting?",
     {"intent": "book_fitting", "pending_intent": "book_fitting", "_tool": None}),
    ("I'd rather not say which branch",
     {"intent": "book_fitting", "pending_intent": "book_fitting",
      "fast_routed": True, "_tool": None,
      "_reply_contains": "day and time"}),   # asks slot_iso, NOT branch again
    # SYSTEM restart: the one explicit abandonment — clears pending state,
    # the functional session cache, any plan, and the interrupt archive.
    ("ok, let's start over",
     {"intent": "restart", "category": "SYSTEM", "pending_intent": None,
      "session_facts": {}, "plan_steps": [], "_paused": None,
      "_reply_contains": "clean slate", "exit_conversation": False}),
    # PLAN-AND-EXECUTE, same-turn until the HITL gate: a compound utterance is
    # planned ONCE (order lookup, then refund), step 1 executes and caches
    # order_id into session_facts, step 2's missing order_id auto-fills from
    # the cache ("it" carries no id) and suspends at the operator gate.
    # (by turn end `intent` holds the DISPATCHED step's action — the plan
    # controller sets it — so the dispatched flow is the assertion here)
    ("look up order 12345 and then refund it",
     {"intent": "request_refund", "category": "FLOW", "current_step_index": 1,
      "_interrupted": True, "_facts_keys": ["order_id"]}),
    # Approve -> the refund runs WITH the session-facts order id (variable
    # mapping), the plan finishes, and the reply reports BOTH steps.
    (RESUME_APPROVE,
     {"_tool": "issue_refund", "_args": {"order_id": "AC-12345"},
      "_interrupted": False, "plan_steps": [], "current_step_index": 0,
      "_reply_contains": ["Order AC-12345", "refund"],
      "_facts_keys": ["order_id", "reference"], "exit_conversation": False}),
    # PLAN PAUSE at a missing slot: step 1 completes; step 2 (book_fitting)
    # lacks a branch -> the plan pauses, the reply carries step 1's summary
    # AND the ask, and the paused step is re-pended for the next turn.
    ("check my order 67890 and then book a fitting",
     {"intent": "book_fitting", "pending_intent": "book_fitting",
      "current_step_index": 1,
      "_reply_contains": ["Order AC-67890", "branch"], "exit_conversation": False}),
    # Slot answer resumes the paused step -> its confirm gate opens (a plan
    # step honors Flow.confirm exactly like a standalone flow). The fast
    # router works mid-plan too (a paused step IS a pending flow).
    ("downtown tomorrow at 3pm",
     {"pending_intent": "book_fitting", "_confirm_pending": True,
      "fast_routed": True,
      "_reply_contains": "yes/no", "exit_conversation": False}),
    # yes -> the booking runs, the plan completes and clears.
    ("yes",
     {"_tool": "book_appointment", "plan_steps": [], "current_step_index": 0,
      "_reply_contains": "booked", "_facts_keys": ["confirmation"],
      "exit_conversation": False}),
    # INTERRUPT -> ARCHIVE -> OFFER -> DETERMINISTIC RESTORE, end to end:
    # start a booking and fill one slot via the fast router...
    ("can I book a fitting?",
     {"intent": "book_fitting", "pending_intent": "book_fitting", "_paused": None}),
    ("downtown works",
     {"intent": "book_fitting", "pending_intent": "book_fitting",
      "fast_routed": True, "_tool": None}),
    # ...interrupt it with ANOTHER FLOW: the booking (branch already collected)
    # is parked, the lookup runs, and the reply carries the order result PLUS
    # the one-shot resume offer.
    ("where is my order 12345?",
     {"intent": "order_status", "fast_routed": False, "_tool": "lookup_order",
      "_paused": "book_fitting",
      "_reply_contains": ["Order AC-12345", "book fitting"]}),
    # ...a bare slot answer RESTORES the parked flow through the fast-router
    # gate (no INTENT-tier call, branch not re-asked) -> its confirm gate opens.
    ("tomorrow at 3pm",
     {"intent": "book_fitting", "fast_routed": True, "_paused": None,
      "_confirm_pending": True, "_reply_contains": "yes/no"}),
    ("yes",
     {"_tool": "book_appointment", "_confirm_pending": False,
      "_reply_contains": "booked", "exit_conversation": False}),
    # ESCALATION PATH (invariant 26): an explicit ask for a person MID
    # SLOT-FILL routes to the deterministic human_handoff SYSTEM intent —
    # pending work clears (a person takes over) and handoff_requested is
    # raised for the Shell/host. The advertised handoff is a reachable node,
    # not conversational copy (report-11072026 defect #6).
    ("I want to book one more fitting",
     {"intent": "book_fitting", "pending_intent": "book_fitting", "_tool": None}),
    ("no, just let me talk to your manager",
     {"intent": "human_handoff", "category": "SYSTEM", "handoff_requested": True,
      "pending_intent": None, "_reply_contains": "human agent",
      "exit_conversation": False}),
    # STALL DETECTOR (invariant 25): the mock chitchat line repeats verbatim —
    # the THIRD consecutive identical reply is swapped for the deterministic
    # clarify-then-escalate STALL_TEXT (broken-record loops are report-11
    # defect #5; repetition is the earliest, cheapest failure signal). The
    # escape phrase routes to human_handoff above.
    ("krzzt fizzle blorp",
     {"intent": "chitchat", "stall_count": 1, "exit_conversation": False}),
    ("second krzzt fizzle blorp",
     {"intent": "chitchat", "stall_count": 2, "exit_conversation": False}),
    ("third krzzt fizzle blorp",
     {"intent": "chitchat", "stall_count": 1,
      "_reply_contains": "talk to a human", "exit_conversation": False}),
    ("that's all, thanks!",
     {"intent": "goodbye", "category": "SYSTEM", "_paused": None,
      "exit_conversation": True}),
]


async def rag_subgraph_checks() -> list:
    """Direct subgraph invariants: a corpus hit yields context; a miss loops,
    gets capped by RAG_MAX_ITERATIONS, and finalizes EMPTY (honest, bounded)."""
    from rag_subgraph import rag_subgraph  # noqa: E402

    failures = []
    hit = await rag_subgraph.ainvoke(
        {"query": "warranty defects", "original_query": "warranty defects", "rewrite_count": 0})
    if not hit.get("context"):
        failures.append("rag subgraph: expected non-empty context for a corpus hit")

    miss = await rag_subgraph.ainvoke(
        {"query": "zzz qqq xyzzy", "original_query": "zzz qqq xyzzy", "rewrite_count": 0})
    if miss.get("context"):
        failures.append("rag subgraph: expected empty context for a corpus miss")
    if miss.get("rewrite_count", 0) > config.RAG_MAX_ITERATIONS:
        failures.append(f"rag subgraph: circuit breaker exceeded "
                        f"({miss.get('rewrite_count')} > {config.RAG_MAX_ITERATIONS})")
    print(f"[rag preflight] hit->context({len(hit.get('context', ''))} chars), "
          f"miss->empty after {miss.get('rewrite_count', 0)} rewrite(s)")
    return failures


async def rag_timeout_degrade_check() -> list:
    """Wall-clock ceiling (Agentic_RAG_Explained.txt rule 6): a HUNG retrieval
    loop must trip RAG_TIMEOUT_SECONDS and degrade to one deterministic
    single-hop retrieve — the turn still answers from DOCS; no crash, no hang."""
    import nodes  # noqa: E402

    class _HungSubgraph:
        async def ainvoke(self, *_a, **_k):
            await asyncio.sleep(30)  # far past any sane ceiling

    msg = "what's your shipping policy?"
    graph = build_pipeline()
    cfg = {"configurable": {"thread_id": "selftest-rag-timeout"}}
    real_subgraph, real_timeout = nodes.rag_subgraph, config.RAG_TIMEOUT_SECONDS
    real_ttl = config.RAG_CACHE_TTL_SECONDS
    # The SCRIPT already asked this question — disable and clear the TTL
    # context cache so this turn genuinely exercises the hung-subgraph path.
    nodes.rag_subgraph, config.RAG_TIMEOUT_SECONDS = _HungSubgraph(), 0.2
    config.RAG_CACHE_TTL_SECONDS = 0
    nodes._RAG_CACHE.clear()
    try:
        payload = dict(_TURN_RESET)
        payload["user_message"] = msg
        payload["recent_messages"] = [HumanMessage(content=msg)]
        state = await graph.ainvoke(payload, config=cfg)
    finally:
        nodes.rag_subgraph, config.RAG_TIMEOUT_SECONDS = real_subgraph, real_timeout
        config.RAG_CACHE_TTL_SECONDS = real_ttl

    reply = state.get("final_response", "")
    print(f"[T] U (RAG loop hung; 0.2s wall clock): {msg}")
    print(f"    A: {reply}")
    failures = []
    if not reply:
        failures.append("rag timeout: empty final_response (turn did not degrade gracefully)")
    elif "3-5 business days" not in reply:
        failures.append(f"rag timeout: expected single-hop DOCS context in reply, got {reply!r}")
    return failures


def stall_preflight() -> list:
    """Direct stall-detector invariants (invariant 25, no graph): the
    validator's in-node gate swaps the N-th consecutive identical reply for
    STALL_TEXT, a changed reply resets the counter, and STALL_THRESHOLD=0
    disables the gate entirely."""
    import nodes  # noqa: E402

    failures = []
    trip = nodes.validator_node({"draft_response": "Same reply.",
                                 "last_reply_fingerprint": "same reply.",
                                 "stall_count": config.STALL_THRESHOLD - 1})
    if "talk to a human" not in trip.get("final_response", ""):
        failures.append(f"stall: threshold reply not swapped, got {trip.get('final_response')!r}")
    if trip.get("stall_count") != 1:
        failures.append("stall: counter did not reset after escalation")
    fresh = nodes.validator_node({"draft_response": "A different reply.",
                                  "last_reply_fingerprint": "same reply.",
                                  "stall_count": config.STALL_THRESHOLD - 1})
    if fresh.get("final_response") != "A different reply." or fresh.get("stall_count") != 1:
        failures.append("stall: a changed reply must reset the counter, not escalate")
    real = config.STALL_THRESHOLD
    config.STALL_THRESHOLD = 0
    try:
        off = nodes.validator_node({"draft_response": "Same reply.",
                                    "last_reply_fingerprint": "same reply.",
                                    "stall_count": 99})
        if off.get("final_response") != "Same reply." or "stall_count" in off:
            failures.append("stall: gate ran while STALL_THRESHOLD=0")
    finally:
        config.STALL_THRESHOLD = real
    print(f"[stall preflight] trip/reset/kill-switch checks, {len(failures)} failed")
    return failures


async def rag_dynamic_preflight() -> list:
    """Dynamic-RAG invariants (report-12072026, no parent graph):
    1. co-reference rescue (R-03): a query that retrieves nothing standalone
       is rewritten WITH the parent-composed history hint and lands the right
       doc — the standalone rewrite happens on a MISS, never as a standing
       pre-search model hop;
    2. deterministic priming (rule 8): _context_hint mines last_action /
       recent messages with zero model calls, and a referential ("it") query
       enters retrieval pre-primed;
    3. TTL context cache (rule 9): an identical repeat question skips the
       subgraph entirely; RAG_CACHE_TTL_SECONDS=0 disables it;
    4. confidence floor (R-05): RETRIEVAL_MIN_SCORE drops weak matches before
       grading -> honest empty context, never a low-confidence synthesis."""
    import nodes  # noqa: E402
    from rag_subgraph import rag_subgraph  # noqa: E402

    failures = []

    # 1) History-aware rewrite-on-miss resolves the reference.
    out = await rag_subgraph.ainvoke(
        {"query": "how long is the coverage?", "original_query": "how long is the coverage?",
         "history_hint": "warranty defects", "rewrite_count": 0})
    if "warranty" not in out.get("context", "").lower():
        failures.append(f"dynamic rag: hinted rewrite missed the warranty doc, got {out.get('context')!r}")

    # 2) Deterministic priming from grounding state.
    hint = nodes._context_hint(
        {"user_message": "does it cover normal wear?",
         "last_action": {"summary": "Your gear carries the standard warranty."},
         "recent_messages": [HumanMessage(content="does it cover normal wear?")]})
    if "warranty" not in hint.lower():
        failures.append(f"dynamic rag: _context_hint missed the last_action entity, got {hint!r}")
    primed = await nodes.agentic_retrieval_node(
        {"user_message": "how long is it valid?",
         "last_action": {"summary": "Your gear carries the standard warranty."},
         "recent_messages": [HumanMessage(content="how long is it valid?")]})
    if "warranty" not in primed.get("retrieved_context", "").lower():
        failures.append("dynamic rag: referential query was not primed from last_action")

    # 3) TTL cache: the second identical question must not touch the retriever.
    calls = {"n": 0}
    real_retriever = config.RETRIEVER

    def _counting(query, top_k=2):
        calls["n"] += 1
        return real_retriever(query, top_k)

    nodes._RAG_CACHE.clear()
    config.RETRIEVER = _counting
    try:
        await nodes.agentic_retrieval_node(
            {"user_message": "what is the warranty policy?", "recent_messages": []})
        first = calls["n"]
        await nodes.agentic_retrieval_node(
            {"user_message": "what is the warranty policy?", "recent_messages": []})
        if calls["n"] != first:
            failures.append("dynamic rag: repeat question re-ran retrieval (cache miss)")
        real_ttl = config.RAG_CACHE_TTL_SECONDS
        config.RAG_CACHE_TTL_SECONDS = 0
        try:
            await nodes.agentic_retrieval_node(
                {"user_message": "what is the warranty policy?", "recent_messages": []})
            if calls["n"] == first:
                failures.append("dynamic rag: cache served while RAG_CACHE_TTL_SECONDS=0")
        finally:
            config.RAG_CACHE_TTL_SECONDS = real_ttl
    finally:
        config.RETRIEVER = real_retriever
        nodes._RAG_CACHE.clear()

    # 4) Confidence floor: an absurd floor yields the honest empty context.
    real_floor = config.RETRIEVAL_MIN_SCORE
    config.RETRIEVAL_MIN_SCORE = 99
    try:
        floored = await rag_subgraph.ainvoke(
            {"query": "warranty defects", "original_query": "warranty defects",
             "rewrite_count": 0})
        if floored.get("context"):
            failures.append("dynamic rag: below-floor docs survived RETRIEVAL_MIN_SCORE")
    finally:
        config.RETRIEVAL_MIN_SCORE = real_floor

    print(f"[dynamic-rag preflight] rewrite/prime/cache/floor checks, {len(failures)} failed")
    return failures


def fast_router_preflight() -> list:
    """Direct fast-router gate invariants (no graph): the tier-0 deterministic
    gate bypasses the INTENT tier ONLY for an unambiguous missing-slot answer;
    every doubt (negation, other-intent keyword, no extraction, resolver
    bounce, kill switch) falls through to the model path."""
    import nodes  # noqa: E402

    failures = []
    # Confident slot answer mid book_fitting -> bypass with the slot filled.
    out = nodes._fast_route("the downtown store please", "book_fitting", {})
    if not out or not out.get("fast_routed") or out.get("slots", {}).get("branch") != "downtown":
        failures.append(f"fast_route: expected a downtown bypass, got {out!r}")
    if out and (out.get("intent") != "book_fitting" or out.get("category") != "FLOW"):
        failures.append(f"fast_route: bypass returned wrong routing {out!r}")
    # Every doubt falls through (None = INTENT-tier path).
    for msg, why in [
        ("no wait, cancel that", "negation must fall through"),
        ("where is my order 12345?", "another intent's keyword must fall through"),
        ("hmm, let me think about it", "no extraction must fall through"),
        ("any branch works, tomorrow at 3pm", "a resolver bounce must fall through"),
    ]:
        if nodes._fast_route(msg, "book_fitting", {}) is not None:
            failures.append(f"fast_route({msg!r}): {why}")
    # Kill switch: FAST_ROUTER_ENABLED=False disables the gate entirely.
    real = config.FAST_ROUTER_ENABLED
    config.FAST_ROUTER_ENABLED = False
    try:
        if nodes._fast_route("the downtown store please", "book_fitting", {}) is not None:
            failures.append("fast_route: ran while FAST_ROUTER_ENABLED=False")
    finally:
        config.FAST_ROUTER_ENABLED = real
    print(f"[fast-router preflight] 6 gate checks, {len(failures)} failed")
    return failures


async def plan_preflight() -> list:
    """Direct planner-clamp + session-cache invariants (no graph):
    1. a fake live PlanResult with an unknown action and too many steps is
       clamped in code — the bad action dropped, the array truncated;
    2. tool_exec merges ONLY Flow.cache_keys fields into session_facts (a
       result field outside the whitelist never lands in the cache)."""
    import nodes  # noqa: E402
    from llm_client import llm_client  # noqa: E402
    from schemas import PlanResult, PlanStep  # noqa: E402

    failures = []

    # 1) Planner clamp: simulate a LIVE model emitting garbage.
    bogus = PlanResult(steps=(
        [PlanStep(action="order_status", slots={"order_id": "12345", "not_a_slot": "x"}),
         PlanStep(action="launch_the_missiles", slots={})]
        + [PlanStep(action="order_status", slots={}) for _ in range(config.MAX_PLAN_STEPS + 2)]))

    async def _fake_structured(*_a, **_k):
        return bogus

    real_mock, real_structured = llm_client.mock, llm_client.generate_structured
    llm_client.mock, llm_client.generate_structured = False, _fake_structured
    try:
        out = await nodes.planner_node({"user_message": "do many things"})
    finally:
        llm_client.mock, llm_client.generate_structured = real_mock, real_structured

    plan = out.get("plan_steps", [])
    if len(plan) > config.MAX_PLAN_STEPS:
        failures.append(f"planner clamp: {len(plan)} steps survived (cap {config.MAX_PLAN_STEPS})")
    if any(s["action"] not in config.FLOWS for s in plan):
        failures.append("planner clamp: an unknown action survived into the plan")
    if any("not_a_slot" in s["slots"] for s in plan):
        failures.append("planner clamp: a slot outside the flow contract survived")

    # 2) Session-cache whitelist: lookup_order returns "status" (NOT in
    #    cache_keys) and "order_id" (in cache_keys) — only the latter caches.
    exec_out = await nodes.tool_exec_node(
        {"cold_payload": {"tool": "lookup_order", "args": {"order_id": "AC-12345"}},
         "tool_call_count": 0, "session_facts": {}})
    facts = exec_out.get("session_facts", {})
    if "order_id" not in facts:
        failures.append("session cache: whitelisted key order_id was not cached")
    if "status" in facts:
        failures.append("session cache: non-whitelisted key 'status' leaked into the cache")

    print(f"[plan preflight] clamp -> {len(plan)} step(s), cache -> {sorted(facts)}, "
          f"{len(failures)} failed")
    return failures


async def enrich_preflight() -> list:
    """ENRICH verdict discipline (live-tier fake, no graph): the SLM returns an
    EnrichVerdict, NEVER prose. Assert:
    1. a GROUNDED verdict -> deterministic templated reply carrying the fact,
       with the config next-step tail appended (the SLM wrote no sentence).
    2. an UNGROUNDED verdict (a fact absent from the result) -> the node
       independently rejects it and falls back to _phrase_result (the summary
       verbatim), never to model text. This is the scrubber's replacement."""
    import nodes  # noqa: E402
    from llm_client import llm_client  # noqa: E402
    from schemas import EnrichVerdict  # noqa: E402

    failures = []
    result = {"tool": "lookup_order", "summary": "Order AC-999 is shipped.",
              "order_id": "AC-999", "status": "shipped"}

    async def _run(verdict):
        async def _fake(*_a, **_k):
            return verdict
        real_mock, real_struct = llm_client.mock, llm_client.generate_structured
        llm_client.mock, llm_client.generate_structured = False, _fake
        try:
            out = await nodes.enrichment_node({"tool_result": result})
        finally:
            llm_client.mock, llm_client.generate_structured = real_mock, real_struct
        return out.get("draft_response", "")

    # 1) Grounded verdict -> templated prose carrying the verbatim fact + tail.
    grounded = await _run(EnrichVerdict(tone="confirm", key_facts=["AC-999", "shipped"], grounded=True))
    if "AC-999" not in grounded:
        failures.append("enrich: grounded fact 'AC-999' missing from templated reply")
    if not grounded.rstrip().endswith("?"):
        failures.append("enrich: deterministic closing question not appended")

    # 2) Ungrounded verdict (fact NOT in result) -> reject -> _phrase_result fallback.
    ungrounded = await _run(EnrichVerdict(tone="confirm", key_facts=["arrives Tuesday"], grounded=True))
    if "Tuesday" in ungrounded:
        failures.append("enrich: ungrounded fact 'arrives Tuesday' leaked to the user")
    if "AC-999" not in ungrounded:  # fallback = _phrase_result(summary)
        failures.append("enrich: ungrounded verdict did not fall back to deterministic phrasing")

    print(f"[enrich preflight] grounded-templating + ungrounded-rejection, "
          f"{len(failures)} failed")
    return failures


async def compaction_preflight() -> list:
    """Direct compaction invariants (no graph):
    1. an oversized list field is crushed under the cap+sentinel bound, the
       error item and the rare-status item ALWAYS survive, and the sentinel
       ref round-trips through retrieve_full_result to the full original;
    2. protection gates: error results and small lists pass through unchanged;
    3. crush_result never raises on hostile shapes (a lost saving is safe,
       a crashed Act node is not);
    4. strip_sentinels restores a uniform-schema list for downstream code."""
    import compaction  # noqa: E402

    failures = []
    n = 40
    rows = [{"id": i, "status": "ok", "name": f"item-{i}"} for i in range(n)]
    rows[17]["error"] = "gateway timeout"          # error item, mid-array
    rows[23]["status"] = "backordered"             # rare status, mid-array
    result = {"tool": "search_catalog", "items": rows, "summary": f"Found {n} items."}

    crushed = compaction.crush_result(result)
    kept = crushed["items"]
    if len(kept) > config.COMPACTION_MAX_ITEMS + 3:  # budget + 2 salient + sentinel
        failures.append(f"compaction: kept {len(kept)} items (budget {config.COMPACTION_MAX_ITEMS})")
    if not any(isinstance(x, dict) and x.get("id") == 17 for x in kept):
        failures.append("compaction: the error item was dropped")
    if not any(isinstance(x, dict) and x.get("id") == 23 for x in kept):
        failures.append("compaction: the rare-status item was dropped")
    sentinel = next((x for x in kept if isinstance(x, dict) and compaction.SENTINEL_KEY in x), None)
    if sentinel is None:
        failures.append("compaction: no sentinel marker appended")
    else:
        import re as _re
        m = _re.search(r"ref='([0-9a-f]+)'", sentinel[compaction.SENTINEL_KEY])
        full = compaction.retrieve_full_result(ref=m.group(1)) if m else {}
        if len(full.get("items") or []) != n:
            failures.append("compaction: retrieve_full_result did not return the full original")
    if compaction.retrieve_full_result(ref="nope").get("error") is None:
        failures.append("compaction: unknown ref did not return an error result")
    if len(compaction.strip_sentinels(kept)) != len(kept) - 1:
        failures.append("compaction: strip_sentinels did not remove exactly the sentinel")

    # Protection gates + never-raises.
    err = {"tool": "search_catalog", "error": "backend down", "items": rows, "summary": "x"}
    if compaction.crush_result(err) is not err:
        failures.append("compaction: an ERROR result was modified (must pass through)")
    small = {"tool": "t", "items": rows[:3], "summary": "x"}
    if compaction.crush_result(small)["items"] != rows[:3]:
        failures.append("compaction: a small list was modified")
    for hostile in (None, "text", {"items": [object()] * 50, "summary": "x"}):
        try:
            compaction.crush_result(hostile)  # type: ignore[arg-type]
        except Exception as e:
            failures.append(f"compaction: raised on hostile input {type(hostile).__name__}: {e}")

    print(f"[compaction preflight] {n} rows -> {len(kept)} kept "
          f"(error+rare preserved, ref round-trip), {len(failures)} failed")
    return failures


async def filler_preflight() -> list:
    """Direct filler-channel invariants (no graph): the display-only side channel
    that covers tool latency with canned, natural acknowledgments.
    1. BANK SHAPE: FILLER_DEFAULT / FILLER_PLAN_CONTINUE non-empty; every
       FILLERS_BY_TOOL entry is a non-empty list of non-empty strings.
    2. EXHAUSTIVENESS (only when enabled): every FLOW tool has its OWN bank —
       the ROI is tool-specific acks, not the generic fallback.
    3. EMIT + ROTATION: with a sink set and the debounce forced off
       (FILLER_DELAY_MS=0, since MOCK tools are instant), tool_exec_node emits
       exactly one 'tool' filler per call and rotates variants across calls.
    4. KILL SWITCH: FILLER_ENABLED=False -> no emission even at delay 0."""
    import nodes  # noqa: E402
    import filler  # noqa: E402
    import tools  # noqa: E402

    failures = []

    # A registered FLOW tool to drive the emit path (domain-agnostic — never
    # hardcode a demo tool name; a renamed catalog would silently skip the test).
    sample_tool = next((f.tool for f in config.FLOWS.values()
                        if f.tool in tools.TOOL_REGISTRY), None)

    # 1) Bank shape.
    def _bad_list(lst):
        return (not isinstance(lst, list) or not lst
                or any(not isinstance(s, str) or not s.strip() for s in lst))
    if _bad_list(config.FILLER_DEFAULT):
        failures.append("filler: FILLER_DEFAULT must be a non-empty list of non-empty strings")
    if _bad_list(config.FILLER_PLAN_CONTINUE):
        failures.append("filler: FILLER_PLAN_CONTINUE must be a non-empty list of non-empty strings")
    for tool, variants in config.FILLERS_BY_TOOL.items():
        if _bad_list(variants):
            failures.append(f"filler: FILLERS_BY_TOOL[{tool!r}] must be a non-empty list of non-empty strings")

    # 2) Exhaustiveness: every flow tool needs its own bank (when the feature is on).
    if config.FILLER_ENABLED:
        for flow_name, flow in config.FLOWS.items():
            if flow.tool not in config.FILLERS_BY_TOOL:
                failures.append(f"filler: FLOW {flow_name!r} tool {flow.tool!r} has no FILLERS_BY_TOOL "
                                f"entry — add tool-specific acks (the generic default defeats the ROI)")

    # 3) Emit + rotation: drive tool_exec_node twice with the debounce forced off.
    real_delay, real_enabled = config.FILLER_DELAY_MS, config.FILLER_ENABLED
    config.FILLER_DELAY_MS, config.FILLER_ENABLED = 0, True
    sink: asyncio.Queue = asyncio.Queue()
    token = filler.set_sink(sink)
    filler.reset_rotation()
    try:
        first = config.FILLERS_BY_TOOL.get(sample_tool) or config.FILLER_DEFAULT
        emitted = []
        if sample_tool is None:
            failures.append("filler: no FLOW tool is registered — cannot exercise the emit path")
        for _ in range(2 if sample_tool else 0):
            await nodes.tool_exec_node(
                {"cold_payload": {"tool": sample_tool, "args": {}},
                 "tool_call_count": 0, "session_facts": {}})
            events = []
            while not sink.empty():
                events.append(sink.get_nowait())
            tool_events = [e for e in events if e.get("kind") == "tool"]
            if len(tool_events) != 1:
                failures.append(f"filler: expected exactly 1 tool filler per call, got {len(tool_events)}")
            elif tool_events[0].get("text"):
                emitted.append(tool_events[0]["text"])
        if len(first) >= 2 and len(emitted) == 2 and emitted[0] == emitted[1]:
            failures.append("filler: variants did not rotate across calls (same phrase twice)")
        if emitted and emitted[0] != first[0]:
            failures.append(f"filler: first emission {emitted[0]!r} was not the first bank variant {first[0]!r}")

        # 4) Kill switch.
        if sample_tool:
            config.FILLER_ENABLED = False
            filler.reset_rotation()
            await nodes.tool_exec_node(
                {"cold_payload": {"tool": sample_tool, "args": {}},
                 "tool_call_count": 0, "session_facts": {}})
            if not sink.empty():
                failures.append("filler: emitted while FILLER_ENABLED=False")
    finally:
        filler.reset_sink(token)
        config.FILLER_DELAY_MS, config.FILLER_ENABLED = real_delay, real_enabled
        filler.reset_rotation()

    print(f"[filler preflight] bank shape + exhaustiveness + emit/rotation + kill switch, "
          f"{len(failures)} failed")
    return failures


def structural_preflight() -> list:
    """Config-structure lints (no graph): turn the architecture's 'mandatory'
    prose rules into actual gates, so a customization pass cannot silently drop
    one. These check the SHAPE of config, not a conversation.
    1. RESOLVER/VALIDATOR COVERAGE (invariant 21c): every DISTINCT entity
       resolver and slot validator callable must be exercised by >=1 HOOK_CHECK
       with a raw live-style value. Mock extractors pre-normalize, so an
       un-hooked canonicalization gap (raw 'tomatoes' vs 'tomato') is invisible
       to the SCRIPT — the prose 'its checks belong in HOOK_CHECKS' becomes a
       gate here. (Shared callables count as covered once, by identity.)
    2. ESCALATION WIRING (invariants 25/26): human_handoff must be a real
       deterministic SYSTEM intent WITH keywords, and (unless the stall gate is
       disabled) STALL_TEXT's escape phrase must contain one of those keywords —
       an advertised handoff the escape phrase can't actually reach is the
       judged 'advertised-but-unwired escalation' failure (#17 in
       Same_Turn_Pipeline.txt)."""
    failures = []

    # 1) Coverage by callable identity (a shared validator is covered once).
    exercised = set()
    for kind, flow_name, slot, *_rest in HOOK_CHECKS:
        fn = (config.ENTITY_RESOLVERS.get(slot) if kind == "resolver"
              else config.FLOWS[flow_name].validators.get(slot))
        if fn is not None:
            exercised.add(id(fn))
    for slot, fn in config.ENTITY_RESOLVERS.items():
        if id(fn) not in exercised:
            failures.append(f"structural: entity resolver for slot {slot!r} has no HOOK_CHECK "
                            f"— add a raw-value 'resolver' check (mock runs can't catch its gaps)")
    for flow_name, flow in config.FLOWS.items():
        for slot, fn in flow.validators.items():
            if id(fn) not in exercised:
                failures.append(f"structural: validator for {flow_name}.{slot} has no HOOK_CHECK "
                                f"— add a raw-value 'validator' check")

    # 2) Escalation path is reachable, and the stall escape phrase reaches it.
    handoff_kw = config.INTENT_KEYWORDS.get("human_handoff", ())
    if "human_handoff" not in config.SYSTEM_INTENTS:
        failures.append("structural: human_handoff must be a deterministic SYSTEM intent (invariant 26)")
    if not handoff_kw:
        failures.append("structural: human_handoff has no INTENT_KEYWORDS — the escalation path "
                        "is unreachable (an advertised handoff must be a real node)")
    elif config.STALL_THRESHOLD and not any(kw in config.STALL_TEXT.lower() for kw in handoff_kw):
        failures.append("structural: STALL_TEXT's escape phrase matches no human_handoff keyword "
                        "(invariant 25 — the escape phrase must actually escalate)")

    print(f"[structural preflight] resolver/validator coverage + escalation wiring, "
          f"{len(failures)} failed")
    return failures


def retrieval_coverage_preflight() -> list:
    """Consumer-vocabulary recall gate. RETRIEVAL_PROBES are written from the
    USER's side — deliberately not derived from DOCS text or INTENT_KEYWORDS,
    so this samples the distribution real users type instead of the author's
    vocabulary (a corpus-derived probe passes trivially and catches nothing).
    A probe that retrieves nothing means an answerable question would get the
    honest decline — the exact silent failure the guard otherwise hides."""
    failures = []
    n_probes = 0
    for intent in config.RETRIEVAL_INTENTS:
        probes = config.RETRIEVAL_PROBES.get(intent, ())
        if len(probes) < 3:
            failures.append(f"retrieval coverage: intent {intent!r} has only "
                            f"{len(probes)} probes — write >=3 consumer phrasings")
        for probe in probes:
            n_probes += 1
            docs = [d for d in config.RETRIEVER(probe)
                    if d.get("score", 0) >= config.RETRIEVAL_MIN_SCORE]
            if not docs:
                failures.append(f"retrieval coverage: probe {probe!r} ({intent}) retrieves "
                                "nothing — an answerable question would be declined; "
                                "add consumer-vocabulary aliases to the matching DOCS entry")
    print(f"[retrieval-coverage preflight] {n_probes} consumer probes, "
          f"{len(failures)} failed")
    return failures


async def main() -> int:
    graph = build_pipeline()
    cfg = {"configurable": {"thread_id": "selftest"}}
    failures = run_hook_checks()        # live-value preflight (see HOOK_CHECKS)
    print(f"[hook preflight] {len(HOOK_CHECKS)} raw-value checks, "
          f"{len(failures)} failed")
    failures += structural_preflight()  # config-shape lints: coverage + escalation wiring
    failures += retrieval_coverage_preflight()  # consumer-probe recall gate (no silent misses)
    failures += fast_router_preflight()  # tier-0 gate: bypass + fall-throughs
    failures += stall_preflight()       # invariant 25: trip / reset / kill switch
    failures += await rag_dynamic_preflight()  # report-12: rewrite/prime/cache/floor
    failures += await plan_preflight()  # planner clamp + session-cache whitelist
    failures += await enrich_preflight()  # ENRICH verdict: grounded-templating + rejection
    failures += await compaction_preflight()  # crush invariants + ref round-trip
    failures += await filler_preflight()  # filler channel: bank/emit/rotation/kill

    for i, (msg, expect) in enumerate(SCRIPT, 1):
        if msg == RESUME_APPROVE:
            # Resume the open HITL interrupt as an approving operator.
            state = await graph.ainvoke(Command(resume={"approved": True}), config=cfg)
        else:
            payload = dict(_TURN_RESET)
            payload.update(expect.get("_preseed", {}))
            payload["user_message"] = msg
            payload["recent_messages"] = [HumanMessage(content=msg)]
            state = await graph.ainvoke(payload, config=cfg)

        interrupted = bool(state.get("__interrupt__"))
        reply = state.get("final_response", "")
        print(f"[{i}] U: {msg}")
        print(f"    A: {'[suspended - awaiting operator approval]' if interrupted and not reply else reply}")

        for key, want in expect.items():
            if key == "_preseed":
                continue
            if key == "_reply_contains":
                wants = want if isinstance(want, list) else [want]
                ok = all(w.lower() in reply.lower() for w in wants)
                got = reply
            elif key == "_facts_keys":
                facts = state.get("session_facts") or {}
                got = sorted(facts)
                ok = all(k in facts for k in want)
            elif key == "_tool":
                got = state.get("cold_payload", {}).get("tool")
                ok = got == want
            elif key == "_args":
                got = state.get("cold_payload", {}).get("args", {})
                ok = all(got.get(k) == v for k, v in want.items())
            elif key == "_confirm_pending":
                got = bool(state.get("pending_confirmation"))
                ok = got == want
            elif key == "_paused":
                got = (state.get("paused_flow") or {}).get("intent")
                ok = got == want
            elif key == "_interrupted":
                got = interrupted
                ok = got == want
            elif key == "_absent":
                got = [k for k in want if k in state]
                ok = not got
            else:
                got = state.get(key)
                ok = got == want
            if not ok:
                failures.append(f"turn {i}: expected {key}={want!r}, got {got!r}")

        if not reply and not interrupted:
            failures.append(f"turn {i}: empty final_response")

    failures += await rag_subgraph_checks()
    failures += await rag_timeout_degrade_check()

    print()
    if failures:
        print("SELF-TEST FAILED:")
        for f in failures:
            print("  -", f)
        return 1
    print(f"SELF-TEST PASSED — {len(SCRIPT)} turns + structural/RAG/stall/dynamic-rag/plan/cache/"
          "enrich/compaction/filler preflights, all invariants hold.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
