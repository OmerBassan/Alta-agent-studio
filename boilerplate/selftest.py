# -*- coding: utf-8 -*-
"""Domain-AGNOSTIC self-test: proves the ENGINE invariants hold for the agent's
CURRENT config, WITHOUT hard-coding any single domain's flows, tools, facts, or
replies.

WHY THIS SHAPE (read before "simplifying" it):
  The old selftest hard-coded the demo domain (branch names, AC-12345 order ids,
  lookup_order / book_fitting, "3-5 business days") across a 36-turn SCRIPT,
  HOOK_CHECKS, and preflights. Every NEW domain therefore forced the builder to
  rewrite all of it correctly in one shot; a single wrong assertion failed the
  gate and drove a fix->rerun loop (the "10-minute build"). This file removes
  that coupling: it DISCOVERS the domain from `config` and asserts STRUCTURE,
  so the builder edits only config.py / prompts.py and NEVER this file.

TWO LAYERS:
  * SHAPE GATES — check THIS agent's shipped config.py/prompts.py structure
    (CALL_ARC/OBJECTION_INTENTS/TIEDOWNS/FILLERS_BY_TOOL wiring, escalation
    reachability, voice/persona/knowledge budgets) against config-derived
    inputs. Fixed engine MECHANICS (compaction, stall, filler rotation,
    planner clamp, enrich verdict, RAG subgraph, CALL_ARC/objection/tie-down
    BEHAVIOR) are proven once, on synthetic data, in
    `builder_platform/tests/test_engine_invariants.py` — not here.
  * SMOKE WALK — drives short, INDEPENDENT conversations (fresh thread per
    check) built from config.INTENT_KEYWORDS / FLOWS / SYSTEM_INTENTS, asserting
    routing category, session-alive, and exit-only-on-goodbye — never a specific
    reply string.

ADAPT, DON'T ASSUME: a check needing a shape the domain may lack (RETRIEVAL
INTENTS, a fillable slot, a cache key) discovers it from config and SKIPS with a
printed note when absent — a renamed flow can never FAIL the gate.

NOT TOO AGGRESSIVE: per-domain AUTHORING gates (HOOK_CHECK coverage, retrieval
probe coverage, filler-bank exhaustiveness) are WARNINGS, not failures — they
nudge quality without blocking a correct build.

SCOPE (2026-08-21 split): this file only holds checks whose PASS/FAIL depends
on THIS agent's actual config.py/prompts.py content — shape gates on shipped
CALL_ARC/OBJECTION_INTENTS/TIEDOWNS/FILLERS_BY_TOOL, the smoke walk, voice/
context budgets, persona, retrieval coverage, hook checks. Checks that instead
prove a fixed ENGINE mechanic on SYNTHETIC/monkeypatched data — meaning they'd
pass or fail identically no matter which domain's config.py is loaded — live in
`builder_platform/tests/test_engine_invariants.py` and run once when
`boilerplate/` itself changes, not on every generated agent (the engine files
are copied verbatim per agent, so re-proving them per agent was pure
redundancy). See that file's docstring for the full list moved there.

Exit code 0 = PASS. Run: python selftest.py
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
import prompts  # noqa: E402
from graph import build_pipeline, TURN_RESET as _TURN_RESET  # noqa: E402

RESUME_APPROVE = "__RESUME_APPROVE__"

# Quality nudges that must NOT block a correct build (printed at the end).
WARNINGS: list = []


def _warn(msg: str) -> None:
    WARNINGS.append(msg)


def _first_keyword(intent: str):
    """A deterministic trigger phrase for an intent, from its keyword bank."""
    kws = config.INTENT_KEYWORDS.get(intent) or ()
    return kws[0] if kws else None


# Optional per-domain raw-value hooks (resolvers/validators exercised with
# live-LLM-style values). Left EMPTY by default — coverage is a warning, not a
# gate (structural_preflight). A domain MAY add entries; the builder need not.
# (kind, flow, slot, raw_value, other_slots, want_ok, substring_of_output)
HOOK_CHECKS: list = []


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


# ── SMOKE WALK (config-derived integration) ─────────────────────────────────
_thread_counter = 0


def _fresh_cfg() -> dict:
    """A clean checkpointer thread so each smoke check starts from zero state —
    no cross-turn contamination between independent invariants."""
    global _thread_counter
    _thread_counter += 1
    return {"configurable": {"thread_id": f"smoke-{_thread_counter}"}}


async def _run(graph, msg, cfg=None):
    """Invoke one turn (or resume an open HITL interrupt)."""
    cfg = cfg or _fresh_cfg()
    if msg == RESUME_APPROVE:
        # An operator approves the SPECIFIC offer the interrupt showed; an
        # approval that names no offer is refused by the engine (authz.py).
        snap = await graph.aget_state(cfg)
        offer_id = snap.interrupts[0].value.get("offer_id") if snap.interrupts else None
        return await graph.ainvoke(Command(resume={"approved": True, "offer_id": offer_id}),
                                   config=cfg), cfg
    payload = dict(_TURN_RESET)
    payload["user_message"] = msg
    payload["recent_messages"] = [HumanMessage(content=msg)]
    return await graph.ainvoke(payload, config=cfg), cfg


async def smoke_walk(graph) -> list:
    """Drive short, independent conversations built from config. Asserts the
    engine's cross-domain invariants (routing category, session-alive,
    exit-only-on-goodbye, deterministic SYSTEM intents, stall escalation),
    never a domain-specific reply string."""
    failures = []

    def hard(cond, label):
        if not cond:
            failures.append(f"smoke: {label}")

    # 1) chitchat: answered, session stays alive (the classic premature-goodbye
    #    guard — an ANSWER-tier turn must never set exit_conversation).
    st, _ = await _run(graph, "hi there, how are you today?")
    hard(st.get("category") == "ANSWER", "greeting must land in category ANSWER")
    hard(not st.get("exit_conversation"), "greeting must NOT end the call")
    hard(bool(st.get("final_response")), "greeting must produce a spoken reply")

    # 2) each knowledge intent: answered IN THE SAME TURN, session alive.
    #    Exact intent-match is a warning (keyword disambiguation is the domain
    #    author's concern); the ENGINE guarantee is a non-empty in-turn answer.
    for intent in config.KNOWLEDGE_INTENTS:
        kw = _first_keyword(intent)
        if not kw:
            _warn(f"knowledge intent {intent!r} has no INTENT_KEYWORDS — its routing isn't smoke-tested")
            continue
        st, _ = await _run(graph, kw)
        hard(bool(st.get("final_response")), f"knowledge intent {intent!r} must answer in-turn (got empty)")
        hard(not st.get("exit_conversation"), f"knowledge intent {intent!r} must not end the call")
        if st.get("intent") != intent:
            _warn(f"keyword {kw!r} routed to {st.get('intent')!r}, expected {intent!r} "
                  f"— check INTENT_KEYWORDS ordering/overlap")

    # 3) each tool-backed flow: triggering it stays in-domain and alive. A flow
    #    with missing slots asks for one (need_info) — still a non-empty reply,
    #    still no exit. (Tool execution / enrich are proven by the preflights.)
    for flow_name in config.FLOWS:
        kw = _first_keyword(flow_name)
        if not kw:
            _warn(f"flow {flow_name!r} has no INTENT_KEYWORDS — its routing isn't smoke-tested")
            continue
        st, _ = await _run(graph, kw)
        hard(bool(st.get("final_response")) or bool(st.get("__interrupt__")),
             f"flow {flow_name!r} must respond (ask a slot, confirm, or act)")
        hard(not st.get("exit_conversation"), f"flow {flow_name!r} must not end the call")
        if st.get("category") not in ("FLOW", "COMPOUND"):
            _warn(f"keyword {kw!r} routed to category {st.get('category')!r}, expected FLOW")

    # 4) help (SYSTEM): deterministic, non-empty, session alive.
    if "help" in config.SYSTEM_INTENTS:
        kw = _first_keyword("help") or "what can you do"
        st, _ = await _run(graph, kw)
        hard(bool(st.get("final_response")), "help must produce a capabilities reply")
        hard(not st.get("exit_conversation"), "help must not end the call")

    # 5) restart (SYSTEM): clears pending flow state deterministically.
    if "restart" in config.SYSTEM_INTENTS:
        kw = _first_keyword("restart") or "start over"
        cfg = _fresh_cfg()
        # Prime a pending flow first (if any flow exists), then restart it away.
        if config.FLOWS:
            fkw = _first_keyword(next(iter(config.FLOWS)))
            if fkw:
                await _run(graph, fkw, cfg)
        st, _ = await _run(graph, kw, cfg)
        hard(st.get("pending_intent") in (None, ""), "restart must clear pending_intent")
        hard(not st.get("session_facts"), "restart must clear session_facts")
        hard(not st.get("exit_conversation"), "restart must not end the call")

    # 6) escalation (invariant 26): an explicit ask for a person routes to the
    #    deterministic human_handoff SYSTEM intent and raises handoff_requested.
    if "human_handoff" in config.SYSTEM_INTENTS:
        kw = _first_keyword("human_handoff") or "let me talk to a human"
        st, _ = await _run(graph, kw)
        hard(bool(st.get("handoff_requested")),
             "human_handoff must raise handoff_requested (the escalation must be a real node)")
        hard(not st.get("exit_conversation"), "human_handoff keeps the session alive for the human")

    # 7) stall detector (invariant 25): repeating an identical unresolved turn
    #    STALL_THRESHOLD times swaps in the clarify-then-escalate reply.
    if config.STALL_THRESHOLD and config.STALL_THRESHOLD > 0:
        cfg = _fresh_cfg()
        nonsense = "krzzt fizzle blorp"
        last = ""
        for _ in range(config.STALL_THRESHOLD):
            st, _ = await _run(graph, nonsense, cfg)
            last = st.get("final_response", "")
        handoff_kw = config.INTENT_KEYWORDS.get("human_handoff", ())
        escalated = (last == config.STALL_TEXT
                     or any(kw in last.lower() for kw in handoff_kw))
        hard(escalated, f"stall detector must escalate after {config.STALL_THRESHOLD} identical replies")

    # 8) goodbye: an explicit closing — and ONLY that — sets exit_conversation.
    kw = _first_keyword("goodbye") or "goodbye, that's all"
    st, _ = await _run(graph, kw)
    hard(st.get("exit_conversation") is True, "explicit goodbye must set exit_conversation")

    print(f"[smoke walk] {_thread_counter} turns across "
          f"{len(config.KNOWLEDGE_INTENTS)} knowledge + {len(config.FLOWS)} flow intents, "
          f"{len(failures)} failed")
    return failures


# ── ENGINE PREFLIGHTS (fixed-engine mechanics) ──────────────────────────────
# stall_preflight, fast_router_preflight, plan_preflight, enrich_preflight,
# compaction_preflight, and summary_preflight moved to
# builder_platform/tests/test_engine_invariants.py (2026-08-21 split — pure
# synthetic/monkeypatched engine mechanics, domain-independent).


def filler_shape_preflight() -> list:
    """Per-agent filler-bank SHAPE gate (config-derived): FILLER_DEFAULT,
    FILLER_PLAN_CONTINUE, and every FILLERS_BY_TOOL entry must be a non-empty
    list of non-empty strings. Per-flow bank EXHAUSTIVENESS is a WARNING (the
    generic default still covers a missing bank). Emit/rotation/kill-switch
    mechanics are engine behavior — see test_engine_invariants.py."""
    failures = []

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

    # Exhaustiveness -> WARNING (the generic default still covers a missing bank).
    if config.FILLER_ENABLED:
        for flow_name, flow in config.FLOWS.items():
            if flow.tool not in config.FILLERS_BY_TOOL:
                _warn(f"filler: flow {flow_name!r} tool {flow.tool!r} has no FILLERS_BY_TOOL entry "
                      f"— add tool-specific acks (the generic default works, but is less warm)")

    print(f"[filler-shape preflight] bank-shape + exhaustiveness warnings, {len(failures)} failed")
    return failures


def structural_preflight() -> list:
    """Config-shape lints. ESCALATION WIRING (invariants 25/26) is a GATE — an
    advertised handoff must be a reachable node and the stall escape phrase must
    reach it. RESOLVER/VALIDATOR HOOK_CHECK coverage is a WARNING (per-domain
    authoring nudge, not a blocker)."""
    failures = []

    # Escalation path reachable + stall escape phrase routes into it.
    handoff_kw = config.INTENT_KEYWORDS.get("human_handoff", ())
    if "human_handoff" not in config.SYSTEM_INTENTS:
        failures.append("structural: human_handoff must be a deterministic SYSTEM intent (invariant 26)")
    if not handoff_kw:
        failures.append("structural: human_handoff has no INTENT_KEYWORDS — the escalation path "
                        "is unreachable (an advertised handoff must be a real node)")
    elif config.STALL_THRESHOLD and not any(kw in config.STALL_TEXT.lower() for kw in handoff_kw):
        failures.append("structural: STALL_TEXT's escape phrase matches no human_handoff keyword "
                        "(invariant 25 — the escape phrase must actually escalate)")

    # Every gated flow's effect must be readable back (outcome verification).
    import authz
    import tools
    failures.extend(authz.verification_gaps(config.FLOWS, getattr(tools, "VERIFIERS", {})))

    # HOOK_CHECK coverage -> WARNING.
    exercised = set()
    for kind, flow_name, slot, *_rest in HOOK_CHECKS:
        fn = (config.ENTITY_RESOLVERS.get(slot) if kind == "resolver"
              else config.FLOWS[flow_name].validators.get(slot))
        if fn is not None:
            exercised.add(id(fn))
    for slot, fn in config.ENTITY_RESOLVERS.items():
        if id(fn) not in exercised:
            _warn(f"structural: entity resolver for slot {slot!r} has no HOOK_CHECK "
                  f"— a raw-value check would catch live-only canonicalization gaps")
    for flow_name, flow in config.FLOWS.items():
        for slot, fn in flow.validators.items():
            if id(fn) not in exercised:
                _warn(f"structural: validator for {flow_name}.{slot} has no HOOK_CHECK")

    print(f"[structural preflight] escalation-wiring + verification gates + coverage warnings, "
          f"{len(failures)} failed")
    return failures


def retrieval_coverage_preflight() -> list:
    """Consumer-vocabulary recall — a WARNING pass (not a gate). A probe that
    retrieves nothing means an answerable question would be declined; surfaced
    so the author can add aliases, but never blocks a build."""
    if not config.RETRIEVAL_INTENTS:
        print("[retrieval-coverage] skipped (no RETRIEVAL_INTENTS)")
        return []
    n_probes = 0
    for intent in config.RETRIEVAL_INTENTS:
        probes = config.RETRIEVAL_PROBES.get(intent, ())
        if len(probes) < 3:
            _warn(f"retrieval coverage: intent {intent!r} has {len(probes)} probes — "
                  f"write >=3 consumer phrasings")
        for probe in probes:
            n_probes += 1
            docs = [d for d in config.RETRIEVER(probe)
                    if d.get("score", 0) >= config.RETRIEVAL_MIN_SCORE]
            if not docs:
                _warn(f"retrieval coverage: probe {probe!r} ({intent}) retrieves nothing — "
                      f"add consumer-vocabulary aliases to the matching DOCS entry")
    print(f"[retrieval-coverage] {n_probes} consumer probes (warnings only)")
    return []


async def rag_preflight() -> list:
    """Agentic-RAG subgraph invariants — ONLY when the domain uses retrieval.
    A corpus hit yields context; a miss loops, is capped by RAG_MAX_ITERATIONS,
    and finalizes EMPTY; a hung loop trips the wall clock and degrades to a
    single deterministic retrieve. Queries are DERIVED from DOCS."""
    if not config.RETRIEVAL_INTENTS or not getattr(config, "DOCS", ()):
        print("[rag preflight] skipped (no RETRIEVAL_INTENTS / DOCS)")
        return []

    import nodes  # noqa: E402
    from rag_subgraph import rag_subgraph  # noqa: E402

    failures = []
    doc0 = config.DOCS[0]
    hit_query = doc0.get("title", "") or " ".join(doc0.get("text", "").split()[:4])

    hit = await rag_subgraph.ainvoke(
        {"query": hit_query, "original_query": hit_query, "rewrite_count": 0})
    if not hit.get("context"):
        failures.append(f"rag: expected non-empty context for corpus hit {hit_query!r}")

    miss = await rag_subgraph.ainvoke(
        {"query": "zzz qqq xyzzy", "original_query": "zzz qqq xyzzy", "rewrite_count": 0})
    if miss.get("context"):
        failures.append("rag: expected empty context for a corpus miss")
    if miss.get("rewrite_count", 0) > config.RAG_MAX_ITERATIONS:
        failures.append(f"rag: circuit breaker exceeded ({miss.get('rewrite_count')} > {config.RAG_MAX_ITERATIONS})")

    # TTL context cache: an identical repeat question skips the retriever.
    calls = {"n": 0}
    real_retriever = config.RETRIEVER

    def _counting(query, top_k=2):
        calls["n"] += 1
        return real_retriever(query, top_k)

    nodes._RAG_CACHE.clear()
    config.RETRIEVER = _counting
    try:
        await nodes.agentic_retrieval_node({"user_message": hit_query, "recent_messages": []})
        first = calls["n"]
        await nodes.agentic_retrieval_node({"user_message": hit_query, "recent_messages": []})
        if config.RAG_CACHE_TTL_SECONDS and calls["n"] != first:
            failures.append("rag: repeat question re-ran retrieval (TTL cache miss)")
    finally:
        config.RETRIEVER = real_retriever
        nodes._RAG_CACHE.clear()

    # Confidence floor: an absurd floor yields the honest empty context.
    real_floor = config.RETRIEVAL_MIN_SCORE
    config.RETRIEVAL_MIN_SCORE = 99
    try:
        floored = await rag_subgraph.ainvoke(
            {"query": hit_query, "original_query": hit_query, "rewrite_count": 0})
        if floored.get("context"):
            failures.append("rag: below-floor docs survived RETRIEVAL_MIN_SCORE")
    finally:
        config.RETRIEVAL_MIN_SCORE = real_floor

    # Hung-loop wall clock -> degrade to single-hop (turn still answers).
    real_subgraph, real_timeout = nodes.rag_subgraph, config.RAG_TIMEOUT_SECONDS
    real_ttl = config.RAG_CACHE_TTL_SECONDS

    class _HungSubgraph:
        async def ainvoke(self, *_a, **_k):
            await asyncio.sleep(30)

    graph = build_pipeline()
    kw = _first_keyword(config.RETRIEVAL_INTENTS[0]) or hit_query
    nodes.rag_subgraph, config.RAG_TIMEOUT_SECONDS = _HungSubgraph(), 0.2
    config.RAG_CACHE_TTL_SECONDS = 0
    nodes._RAG_CACHE.clear()
    try:
        payload = dict(_TURN_RESET)
        payload["user_message"] = kw
        payload["recent_messages"] = [HumanMessage(content=kw)]
        state = await graph.ainvoke(payload, config={"configurable": {"thread_id": "rag-timeout"}})
    finally:
        nodes.rag_subgraph, config.RAG_TIMEOUT_SECONDS = real_subgraph, real_timeout
        config.RAG_CACHE_TTL_SECONDS = real_ttl
    if not state.get("final_response"):
        failures.append("rag timeout: empty reply (turn did not degrade gracefully)")

    print(f"[rag preflight] hit/miss/cache/floor/timeout on {len(config.DOCS)} docs, {len(failures)} failed")
    return failures


def call_arc_shape_preflight() -> list:
    """Per-agent CALL_ARC shape gate (config-derived): stage names unique, and
    every flow reference (`stage.flow`, `advance_when.flow_complete`) points at
    a real FLOWS entry. Skips cleanly when CALL_ARC is empty (inbound agent).
    The director's lead/advance/one-shot/firm-no BEHAVIOR is a fixed engine
    mechanic proven on a synthetic arc — see test_engine_invariants.py."""
    failures = []
    shipped = tuple(getattr(config, "CALL_ARC", ()) or ())
    if shipped:
        names = [s.name for s in shipped]
        if len(names) != len(set(names)):
            failures.append("call_arc: stage names must be unique")
        for s in shipped:
            if s.flow and s.flow not in config.FLOWS:
                failures.append(f"call_arc: stage {s.name!r} points at unknown flow {s.flow!r}")
            fc = (s.advance_when or {}).get("flow_complete")
            if fc and fc not in config.FLOWS:
                failures.append(f"call_arc: stage {s.name!r} advance_when flow_complete -> unknown flow {fc!r}")

    scope = f"{len(shipped)}-stage shipped arc" if shipped else "empty shipped arc (no-op)"
    print(f"[call-arc shape preflight] {scope}, {len(failures)} failed")
    return failures


def voice_budget_preflight() -> list:
    """Config-derived voice/latency budgets on GENERATED output: the OPENER word
    count (a long cached opener delays pickup) and FILLER_THINKING token shape
    (ultra-short, no ellipsis — they precede ANY reply type). Makes the '<=20
    words / compact' voice rules an automated gate, not only a human pass.
    Punctuation-only tokens (an em dash) are not counted as words."""
    failures = []

    def _words(s: str) -> int:
        return len([w for w in s.split() if any(c.isalnum() for c in w)])

    opener = getattr(config, "OPENER", "") or ""
    if opener and _words(opener) > 20:
        failures.append(f"OPENER is {_words(opener)} words (>20): a long cached opener delays pickup — {opener!r}")

    for tok in getattr(config, "FILLER_THINKING", []) or []:
        t = tok.strip()
        if t.endswith("..."):
            failures.append(f"FILLER_THINKING token ends in an ellipsis (TTS trails): {tok!r}")
        if _words(t) > 6:
            _warn(f"FILLER_THINKING token is wordy ({_words(t)} words) — keep pre-think tokens ultra-short: {tok!r}")

    facts = getattr(config, "FACTS", "") or ""
    cap = getattr(config, "_KNOWLEDGE_MAX_CHARS", 8000)
    if len(facts) > cap * 2:
        _warn(f"FACTS is {len(facts)} chars (injected every knowledge turn) — consider RETRIEVAL_INTENTS for a large corpus")

    print(f"[voice-budget preflight] opener + filler-token shape + facts-size, {len(failures)} failed")
    return failures


def persona_preflight() -> list:
    """An OUTBOUND agent must not ship the boilerplate's INBOUND help-desk voice.

    prompts.py's module docstring already calls leaving its generic wording
    untouched "a build defect, not a shortcut" — but that was enforced only as
    prose aimed at the builder, so an unedited copy shipped anyway and the agent
    forgot it had placed the call. This makes it a gate.

    A non-empty CALL_ARC is the outbound signal: the director only leads a call
    the agent initiated. When it is set, the two prompts that carry the persona
    must no longer say "support assistant" (reactive framing) or "steer to what
    you can help with" (waits for the lead's agenda). Inbound agents keep an
    empty arc, so this preflight is a no-op for them and the boilerplate's own
    selftest stays green.

    Asserts against the RENDERED prompt, not the source text, so it holds however
    the wording was produced (f-string, constant, or config-driven persona).
    """
    failures = []
    arc = getattr(config, "CALL_ARC", ()) or ()
    if not arc:
        print("[persona preflight] inbound (CALL_ARC empty) — skipped")
        return failures

    # Phrases that encode "they called us, and I wait for their agenda".
    inbound_markers = (
        "support assistant",
        "steer to what you can help with",
    )
    rendered = {
        "build_knowledge_system": prompts.build_knowledge_system(""),
        "build_chitchat_system": prompts.build_chitchat_system(),
    }
    for fn_name, text in rendered.items():
        low = text.lower()
        for marker in inbound_markers:
            if marker in low:
                failures.append(
                    f"{fn_name} still carries the inbound default {marker!r} while "
                    f"CALL_ARC defines {len(arc)} outbound stage(s) — an outbound "
                    f"agent must state that IT placed the call (see prompts.py docstring)"
                )

    print(f"[persona preflight] outbound voice on {len(rendered)} persona prompts, "
          f"{len(failures)} failed")
    return failures


def knowledge_facts_preflight() -> list:
    """Per-agent FACTS leak gate (config-derived): uploaded knowledge must be
    retrieval-gated via DOCS, never appended to the static FACTS prompt (which
    would ride every think call). The history-window cap and the knowledge
    chunker are fixed engine mechanics — see test_engine_invariants.py."""
    failures = []
    if "Additional uploaded knowledge" in getattr(config, "FACTS", ""):
        failures.append("knowledge: uploaded files must NOT be appended to FACTS — retrieval-gate them via DOCS")
    print(f"[knowledge-facts preflight] {len(failures)} failed")
    return failures


def objection_shape_preflight() -> list:
    """Per-agent objection shape + STRICT word-budget gate (config-derived):
    every OBJECTION_INTENTS name is valid and a KNOWLEDGE_INTENT, every
    OBJECTION_TOPICS key is a known intent, and the isolate template renders
    and fits the reply's word budget alongside its rebuttal. Skips cleanly
    when OBJECTION_INTENTS is empty. The Acknowledge->Isolate->Pivot BEHAVIOR
    is a fixed engine mechanic proven on synthetic data — see
    test_engine_invariants.py."""
    failures = []
    cap = int(getattr(config, "MAX_REPLY_WORDS", 20) or 20)

    def _words(s: str) -> int:
        return len([w for w in (s or "").split() if any(c.isalnum() for c in w)])

    # --- Shape + STRICT word budget on the SHIPPED config (skips when empty) ---
    shipped = tuple(getattr(config, "OBJECTION_INTENTS", ()) or ())
    template = getattr(config, "OBJECTION_ISOLATE_TEMPLATE", "") or ""
    topics = getattr(config, "OBJECTION_TOPICS", {}) or {}
    if shipped:
        for name in shipped:
            if name not in config.VALID_INTENTS:
                failures.append(f"objection: {name!r} is not a valid intent")
            if name not in config.KNOWLEDGE_INTENTS:
                failures.append(f"objection: {name!r} must also be a KNOWLEDGE_INTENT "
                                "(objections route through knowledge_node for grounding)")
        for name in topics:
            if name not in shipped:
                failures.append(f"objection: OBJECTION_TOPICS has {name!r}, not in OBJECTION_INTENTS")
        if template:
            if "{topic}" not in template:
                failures.append("objection: OBJECTION_ISOLATE_TEMPLATE must contain {topic}")
            if not template.rstrip().endswith("?"):
                failures.append("objection: OBJECTION_ISOLATE_TEMPLATE must end in a question mark")
            for name, topic in topics.items():
                try:
                    rendered = template.format(topic=topic)
                except (KeyError, IndexError) as e:
                    failures.append(f"objection: isolate template does not render for {name!r}: {e}")
                    continue
                # STRICT budget: the isolate question shares the turn with the
                # rebuttal that precedes it, so it must leave room for one.
                if _words(rendered) > cap // 2:
                    failures.append(
                        f"objection: isolate question for {name!r} is {_words(rendered)} words "
                        f"(>{cap // 2}); it shares the {cap}-word reply with the rebuttal — {rendered!r}")
                rebuttal = (config.MOCK_KNOWLEDGE.get(name) or "").strip()
                if rebuttal and _words(rebuttal) + _words(rendered) > cap:
                    failures.append(
                        f"objection: rebuttal + isolate for {name!r} is "
                        f"{_words(rebuttal) + _words(rendered)} words (>{cap}) — shorten "
                        f"MOCK_KNOWLEDGE[{name!r}]")

    scope = f"{len(shipped)} shipped objection intent(s)" if shipped else "no shipped objections (no-op)"
    print(f"[objection-shape preflight] word-budget + {scope}, {len(failures)} failed")
    return failures


def tiedown_shape_preflight() -> list:
    """Per-agent tie-down shape gate (config-derived): every shipped TIEDOWNS
    entry must be a short question (a micro-commitment ask). The
    fire/cadence/floor/word-budget/stall-ordering BEHAVIOR is a fixed engine
    mechanic proven on synthetic data — see test_engine_invariants.py."""
    failures = []
    for t in (getattr(config, "TIEDOWNS", []) or []):
        if not t.rstrip().endswith("?"):
            failures.append(f"tiedown: {t!r} must be a question (it is a micro-commitment ask)")
        if len([w for w in t.split() if any(c.isalnum() for c in w)]) > 6:
            _warn(f"tiedown: {t!r} is wordy — a tie-down should be 3-6 words")

    print(f"[tiedown-shape preflight] {len(failures)} failed")
    return failures


async def main() -> int:
    failures = []
    failures += run_hook_checks()
    failures += structural_preflight()
    failures += retrieval_coverage_preflight()
    failures += call_arc_shape_preflight()
    failures += objection_shape_preflight()
    failures += tiedown_shape_preflight()
    failures += voice_budget_preflight()
    failures += persona_preflight()
    failures += knowledge_facts_preflight()
    failures += filler_shape_preflight()
    failures += await rag_preflight()

    graph = build_pipeline()
    failures += await smoke_walk(graph)

    print()
    if WARNINGS:
        print(f"WARNINGS ({len(WARNINGS)}) — quality nudges, not blockers:")
        for w in WARNINGS:
            print("  ~", w)
        print()
    if failures:
        print("SELF-TEST FAILED:")
        for f in failures:
            print("  -", f)
        return 1
    print("SELF-TEST PASSED — config-derived shape gates + smoke walk, "
          "all invariants hold. (Engine mechanics proven once in "
          "builder_platform/tests/test_engine_invariants.py.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
