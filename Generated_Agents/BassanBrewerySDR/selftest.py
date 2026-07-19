# -*- coding: utf-8 -*-
"""Scripted self-test: runs a multi-intent conversation through the pipeline in
MOCK mode and asserts the architectural invariants. Run after every
customization pass (`python selftest.py`); exit code 0 = PASS.

Domain: Tom, an outbound sales agent for Bassan Brewery. See config.py for the
intent/flow catalog this script exercises.

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
  - ENTITY RESOLVERS ground referential values ("whatever's cheapest") against
    the catalog and bounce unresolvable ones with a clarifying question
  - LIVE-VALUE HOOKS (preflight, no graph): resolvers/validators are exercised
    DIRECTLY with raw LLM-style slot values. The conversation script alone
    cannot catch a missing resolver — mock extractors pre-normalize values
    before slots are set, so a live-only canonicalization gap is invisible to it
  - STRUCTURAL LINTS (preflight, no graph): config SHAPE is gated so a
    customization can't silently drop a mandatory rule — every distinct
    resolver/validator callable is exercised by a HOOK_CHECK, and the
    human_handoff escalation path is reachable with STALL_TEXT's escape phrase
    actually routing into it (invariants 21c / 25 / 26)
  - after a tool runs, last_action grounds follow-ups instead of a
    capabilities pitch — and the session stays alive
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
    (here: the read-back scene before the lead profile is submitted)
  - a Flow(enrich=False) result bypasses the SLM (needs_enrichment stays False)
    yet still produces a clean deterministic reply
  - the circuit breaker refuses tool execution past MAX_TOOL_CALLS_PER_TURN
  - FUNCTIONAL SESSION CACHE: successful tools merge ONLY Flow.cache_keys
    fields into session_facts (whitelist, zero-inference); restart clears it
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
    # drink_mix resolver: raw phrasing canonicalizes against the product catalog.
    ("resolver", "lead_profile", "drink_mix", "just coke and bottled water", {}, True, "everyday"),
    ("resolver", "lead_profile", "drink_mix", "mostly Singha and Evian", {}, True, "specialty"),
    ("resolver", "lead_profile", "drink_mix", "a bit of both, some cola and some Perrier", {}, True, "mix of both"),
    ("resolver", "lead_profile", "drink_mix", "whatever's cheapest", {}, False, "specialty imports"),
    # buyer_character resolver: raw phrasing canonicalizes against the buying-style catalog.
    ("resolver", "lead_profile", "buyer_character", "we'd want a yearly deal", {}, True, "annual contract"),
    ("resolver", "lead_profile", "buyer_character", "just a bulk order for one event", {}, True, "bulk order"),
    ("resolver", "lead_profile", "buyer_character", "not sure, depends on the month", {}, True, "ordering as needed"),
    # monthly_volume validator: format normalization + bounds rejection.
    ("validator", "lead_profile", "monthly_volume", "about 500 guests", {}, True, "500"),
    ("validator", "lead_profile", "monthly_volume", "0", {}, False, "guests or customers"),
    ("validator", "lead_profile", "monthly_volume", "5000000", {}, False, "quite high"),
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
      "_reply_contains": "sales team"}),
    ("how does your pricing work?",
     {"intent": "pricing_info", "category": "ANSWER", "exit_conversation": False,
      "_reply_contains": "locked"}),
    # Agentic-RAG: retrieval subgraph answers product-details questions; its
    # private loop state must never leak into the parent AgentState.
    ("does the cola have caffeine in it",
     {"intent": "product_details", "category": "ANSWER",
      "_reply_contains": "caffeine",
      "_absent": ["documents", "sufficient", "rewrite_count", "original_query"]}),
    # Corpus miss -> rewrite loop -> RAG_MAX_ITERATIONS circuit breaker ->
    # honest fallback, never a hallucinated answer.
    ("how many calories does a twelve ounce serving have",
     {"intent": "product_details", "category": "ANSWER", "exit_conversation": False,
      "_reply_contains": "won't guess"}),
    # Flow trigger: the lead confirms they're the right contact -> lead_profile
    # becomes pending; first missing slot (monthly_volume) is asked.
    ("Yes, speaking - I handle our drink orders.",
     {"intent": "lead_profile", "category": "FLOW", "pending_intent": "lead_profile",
      "_tool": None, "_reply_contains": "guests or customers"}),
    # Fast router: a bare slot answer mid slot-fill bypasses the INTENT tier.
    ("we serve about 500 guests a month",
     {"intent": "lead_profile", "pending_intent": "lead_profile", "_tool": None,
      "fast_routed": True}),
    # Entity resolution: an unresolvable/referential drink-mix phrase is
    # bounced with a clarifying question, never passed to the tool literally.
    ("whatever's cheapest is fine",
     {"intent": "lead_profile", "pending_intent": "lead_profile", "_tool": None,
      "fast_routed": False,   # resolver bounce -> the gate must NOT bypass
      "_reply_contains": "Singha or Evian"}),
    ("mostly everyday stuff like cola and water",
     {"intent": "lead_profile", "pending_intent": "lead_profile", "_tool": None,
      "fast_routed": True}),
    ("it renews in about 3 months",
     {"intent": "lead_profile", "pending_intent": "lead_profile", "_tool": None,
      "fast_routed": True}),
    # Detour mid slot-fill: knowledge answer + resume line, pending flow SURVIVES.
    ("actually, what's your contract length?",
     {"intent": "contract_terms", "pending_intent": "lead_profile",
      "_reply_contains": ["weekly", "renewal"], "exit_conversation": False}),
    # A second FLOW interrupting the pending one is ARCHIVED, not clobbered
    # (depth-1 interrupt archive): flag_request completes in one turn (its
    # only slot auto-fills from the raw message) while lead_profile is parked.
    ("actually, before that - can we get a discount on this order?",
     {"intent": "flag_request", "category": "FLOW", "_tool": "flag_for_team",
      "_paused": "lead_profile",
      "_reply_contains": ["team", "didn't finish"]}),
    # A bare slot answer RESTORES the parked flow through the fast-router gate
    # (no INTENT-tier call, nothing re-asked) -> all 5 slots now known ->
    # the confirm gate (the read-back) opens.
    ("we'd want this as a bulk order for one big event",
     {"intent": "lead_profile", "fast_routed": True, "_paused": None,
      "_confirm_pending": True, "_tool": None,
      "_reply_contains": "get that right"}),
    # Yes -> the lead profile is submitted; enrich=False -> SLM bypassed, the
    # reply is the deterministic summary + the declared next-step hint.
    ("yes",
     {"intent": "lead_profile", "_tool": "submit_lead_profile", "needs_enrichment": False,
      "_confirm_pending": False, "_reply_contains": "team",
      "_facts_keys": ["lead_reference"], "exit_conversation": False}),
    # Circuit breaker: with the per-turn budget already spent, the Act is
    # refused and degrades gracefully instead of running away; the flow is
    # re-pended for retry.
    ("we'd also like a custom recipe suggestion",
     {"_preseed": {"tool_call_count": 3}, "intent": "flag_request",
      "_reply_contains": "snag", "pending_intent": "flag_request",
      "exit_conversation": False}),
    # SYSTEM restart: the one explicit abandonment — clears pending state,
    # the functional session cache, any plan, and the interrupt archive.
    ("ok, let's start over",
     {"intent": "restart", "category": "SYSTEM", "pending_intent": None,
      "session_facts": {}, "plan_steps": [], "_paused": None,
      "_reply_contains": "clean slate", "exit_conversation": False}),
    # ESCALATION PATH (invariant 26): an explicit ask for a person MID
    # SLOT-FILL routes to the deterministic human_handoff SYSTEM intent —
    # pending work clears and handoff_requested is raised for the Shell/host.
    ("I handle drink orders for our second location too",
     {"intent": "lead_profile", "pending_intent": "lead_profile", "_tool": None}),
    ("no, just let me talk to your manager",
     {"intent": "human_handoff", "category": "SYSTEM", "handoff_requested": True,
      "pending_intent": None, "_reply_contains": "person from our team",
      "exit_conversation": False}),
    # STALL DETECTOR (invariant 25): the mock chitchat line repeats verbatim —
    # the THIRD consecutive identical reply is swapped for the deterministic
    # clarify-then-escalate STALL_TEXT. The escape phrase routes to human_handoff.
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
        {"query": "ingredients allergens caffeine", "original_query": "ingredients allergens caffeine",
         "rewrite_count": 0})
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

    msg = "what ingredients are in your drinks?"
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
    elif "carbonated water" not in reply:
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
        {"query": "how long does this stay fresh", "original_query": "how long does this stay fresh",
         "history_hint": "ingredients allergens caffeine", "rewrite_count": 0})
    if "caffeine" not in out.get("context", "").lower():
        failures.append(f"dynamic rag: hinted rewrite missed the ingredients doc, got {out.get('context')!r}")

    # 2) Deterministic priming from grounding state.
    hint = nodes._context_hint(
        {"user_message": "is that included every time?",
         "last_action": {"summary": "Your order includes our standard weekly delivery."},
         "recent_messages": [HumanMessage(content="is that included every time?")]})
    if "delivery" not in hint.lower():
        failures.append(f"dynamic rag: _context_hint missed the last_action entity, got {hint!r}")
    primed = await nodes.agentic_retrieval_node(
        {"user_message": "is it included every week?",
         "last_action": {"summary": "Your order includes our standard weekly delivery."},
         "recent_messages": [HumanMessage(content="is it included every week?")]})
    if "delivery" not in primed.get("retrieved_context", "").lower():
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
            {"user_message": "what ingredients are in your drinks?", "recent_messages": []})
        first = calls["n"]
        await nodes.agentic_retrieval_node(
            {"user_message": "what ingredients are in your drinks?", "recent_messages": []})
        if calls["n"] != first:
            failures.append("dynamic rag: repeat question re-ran retrieval (cache miss)")
        real_ttl = config.RAG_CACHE_TTL_SECONDS
        config.RAG_CACHE_TTL_SECONDS = 0
        try:
            await nodes.agentic_retrieval_node(
                {"user_message": "what ingredients are in your drinks?", "recent_messages": []})
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
            {"query": "ingredients allergens caffeine", "original_query": "ingredients allergens caffeine",
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
    # Confident slot answer mid lead_profile -> bypass with the slot filled.
    out = nodes._fast_route("just coke and water please", "lead_profile", {})
    if not out or not out.get("fast_routed") or out.get("slots", {}).get("drink_mix") != "everyday drinks":
        failures.append(f"fast_route: expected an 'everyday drinks' bypass, got {out!r}")
    if out and (out.get("intent") != "lead_profile" or out.get("category") != "FLOW"):
        failures.append(f"fast_route: bypass returned wrong routing {out!r}")
    # Every doubt falls through (None = INTENT-tier path).
    for msg, why in [
        ("no wait, forget that", "negation must fall through"),
        ("I'd like a discount on this order", "another intent's keyword must fall through"),
        ("hmm, let me think about it", "no extraction must fall through"),
        ("whatever's cheapest is fine", "a resolver bounce must fall through"),
    ]:
        if nodes._fast_route(msg, "lead_profile", {}) is not None:
            failures.append(f"fast_route({msg!r}): {why}")
    # Kill switch: FAST_ROUTER_ENABLED=False disables the gate entirely.
    real = config.FAST_ROUTER_ENABLED
    config.FAST_ROUTER_ENABLED = False
    try:
        if nodes._fast_route("just coke and water please", "lead_profile", {}) is not None:
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
        [PlanStep(action="lead_profile", slots={"monthly_volume": "500", "not_a_slot": "x"}),
         PlanStep(action="launch_the_missiles", slots={})]
        + [PlanStep(action="lead_profile", slots={}) for _ in range(config.MAX_PLAN_STEPS + 2)]))

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

    # 2) Session-cache whitelist: submit_lead_profile returns "monthly_volume"
    #    (NOT in cache_keys) and "lead_reference" (in cache_keys) — only the
    #    latter caches.
    exec_out = await nodes.tool_exec_node(
        {"cold_payload": {"tool": "submit_lead_profile", "args": {
            "monthly_volume": "500", "drink_mix": "everyday drinks",
            "contract_renewal": "next year",
            "buyer_character": "a standing annual contract"}},
         "tool_call_count": 0, "session_facts": {}})
    facts = exec_out.get("session_facts", {})
    if "lead_reference" not in facts:
        failures.append("session cache: whitelisted key lead_reference was not cached")
    if "monthly_volume" in facts:
        failures.append("session cache: non-whitelisted key 'monthly_volume' leaked into the cache")

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
    result = {"tool": "submit_lead_profile", "summary": "Logged lead LD-999.",
              "lead_reference": "LD-999", "monthly_volume": "500"}

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
    grounded = await _run(EnrichVerdict(tone="confirm", key_facts=["LD-999", "500"], grounded=True))
    if "LD-999" not in grounded:
        failures.append("enrich: grounded fact 'LD-999' missing from templated reply")
    if not grounded.rstrip().endswith("?"):
        failures.append("enrich: deterministic closing question not appended")

    # 2) Ungrounded verdict (fact NOT in result) -> reject -> _phrase_result fallback.
    ungrounded = await _run(EnrichVerdict(tone="confirm", key_facts=["arrives Tuesday"], grounded=True))
    if "Tuesday" in ungrounded:
        failures.append("enrich: ungrounded fact 'arrives Tuesday' leaked to the user")
    if "LD-999" not in ungrounded:  # fallback = _phrase_result(summary)
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
       un-hooked canonicalization gap is invisible to the SCRIPT — the prose
       'its checks belong in HOOK_CHECKS' becomes a gate here. (Shared
       callables count as covered once, by identity.)
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
