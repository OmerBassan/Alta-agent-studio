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
  * ENGINE PREFLIGHTS — exercise the FIXED engine mechanics (compaction, stall,
    filler, planner clamp, enrich verdict, RAG subgraph) with synthetic or
    config-derived inputs. The engine is copied verbatim per agent, so these
    hold for every domain.
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
        return await graph.ainvoke(Command(resume={"approved": True}), config=cfg), cfg
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

def stall_preflight() -> list:
    """Direct stall-detector invariants (invariant 25, no graph): the validator
    swaps the N-th consecutive identical reply for STALL_TEXT, a changed reply
    resets the counter, and STALL_THRESHOLD=0 disables the gate."""
    import nodes  # noqa: E402

    if not config.STALL_THRESHOLD:
        print("[stall preflight] skipped (STALL_THRESHOLD=0, gate disabled)")
        return []

    failures = []
    trip = nodes.validator_node({"draft_response": "Same reply.",
                                 "last_reply_fingerprint": "same reply.",
                                 "stall_count": config.STALL_THRESHOLD - 1})
    if "talk to a human" not in trip.get("final_response", "").lower() \
            and trip.get("final_response") != config.STALL_TEXT:
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
    print(f"[stall preflight] trip/reset/kill-switch, {len(failures)} failed")
    return failures


def fast_router_preflight() -> list:
    """Fast-router SAFETY invariants (tier-0 gate, no graph). The critical,
    domain-agnostic direction is FALL-THROUGH ON DOUBT: negation, no extraction,
    and the kill switch must never wrongly bypass the INTENT tier. The positive
    bypass depends on a domain slot value we can't synthesize generically, so it
    is a warning, exercised only if a fillable slot is discoverable."""
    import nodes  # noqa: E402

    if not config.FLOWS:
        print("[fast-router preflight] skipped (no FLOWS)")
        return []
    flow_name = next(iter(config.FLOWS))
    failures = []

    # Fall-through on doubt (holds for ANY domain).
    for msg, why in [
        ("no wait, cancel that", "negation must fall through"),
        ("hmm, let me think about it", "no extraction must fall through"),
    ]:
        if nodes._fast_route(msg, flow_name, {}) is not None:
            failures.append(f"fast_route({msg!r}): {why}")

    # Kill switch: disabled gate never routes.
    real = config.FAST_ROUTER_ENABLED
    config.FAST_ROUTER_ENABLED = False
    try:
        if nodes._fast_route("the usual please", flow_name, {}) is not None:
            failures.append("fast_route: ran while FAST_ROUTER_ENABLED=False")
    finally:
        config.FAST_ROUTER_ENABLED = real

    # Best-effort positive bypass: find a slot whose extractor accepts a value we
    # can pull from the mock knowledge / a slot prompt. Skip (warn) if none.
    exercised_positive = False
    for fn, flow in config.FLOWS.items():
        for slot in flow.slots:
            extractor = config.SLOT_EXTRACTORS.get(slot)
            if not extractor:
                continue
            # Try the slot's own prompt text and a few generic tokens.
            for probe in (flow.slot_prompts.get(slot, ""), "tomorrow at 3pm", "yes"):
                if probe and extractor(probe):
                    out = nodes._fast_route(probe, fn, {})
                    if out and out.get("fast_routed"):
                        exercised_positive = True
                    break
            if exercised_positive:
                break
        if exercised_positive:
            break
    if not exercised_positive:
        _warn("fast-router: no fillable slot found to exercise the positive bypass "
              "(only the fall-through guards were checked)")

    print(f"[fast-router preflight] fall-through + kill-switch"
          f"{' + positive bypass' if exercised_positive else ''}, {len(failures)} failed")
    return failures


async def plan_preflight() -> list:
    """Planner CLAMP invariant (no graph): a live model emitting an unknown
    action and too many steps is clamped in code — the bad action dropped, the
    array truncated to MAX_PLAN_STEPS, off-contract slots stripped. Uses the
    domain's first real flow name (no hard-coded action)."""
    import nodes  # noqa: E402
    from llm_client import llm_client  # noqa: E402
    from schemas import PlanResult, PlanStep  # noqa: E402

    if not config.FLOWS:
        print("[plan preflight] skipped (no FLOWS to plan over)")
        return []

    real_flow = next(iter(config.FLOWS))
    failures = []

    bogus = PlanResult(steps=(
        [PlanStep(action=real_flow, slots={"not_a_slot": "x"}),
         PlanStep(action="launch_the_missiles", slots={})]
        + [PlanStep(action=real_flow, slots={}) for _ in range(config.MAX_PLAN_STEPS + 2)]))

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
    if any("not_a_slot" in s.get("slots", {}) for s in plan):
        failures.append("planner clamp: a slot outside the flow contract survived")

    print(f"[plan preflight] clamp -> {len(plan)} step(s), {len(failures)} failed")
    return failures


async def enrich_preflight() -> list:
    """ENRICH verdict discipline (live-tier fake, no graph): the SLM returns a
    verdict, NEVER prose. A grounded verdict -> deterministic templated reply
    carrying the fact + closing question; an ungrounded fact is rejected and the
    node falls back to the summary verbatim. Tool name is config-derived."""
    import nodes  # noqa: E402
    from llm_client import llm_client  # noqa: E402
    from schemas import EnrichVerdict  # noqa: E402

    tool_name = next((f.tool for f in config.FLOWS.values()), None)
    if tool_name is None:
        print("[enrich preflight] skipped (no FLOWS/tools)")
        return []

    failures = []
    result = {"tool": tool_name, "summary": "Reference R-999 is set.",
              "ref_id": "R-999", "status": "done"}

    async def _run_verdict(verdict):
        async def _fake(*_a, **_k):
            return verdict
        real_mock, real_struct = llm_client.mock, llm_client.generate_structured
        llm_client.mock, llm_client.generate_structured = False, _fake
        try:
            out = await nodes.enrichment_node({"tool_result": result})
        finally:
            llm_client.mock, llm_client.generate_structured = real_mock, real_struct
        return out.get("draft_response", "")

    grounded = await _run_verdict(EnrichVerdict(tone="confirm", key_facts=["R-999", "done"], grounded=True))
    if "R-999" not in grounded:
        failures.append("enrich: grounded fact 'R-999' missing from templated reply")
    if not grounded.rstrip().endswith("?"):
        failures.append("enrich: deterministic closing question not appended")

    ungrounded = await _run_verdict(EnrichVerdict(tone="confirm", key_facts=["next Tuesday"], grounded=True))
    if "Tuesday" in ungrounded:
        failures.append("enrich: ungrounded fact 'next Tuesday' leaked to the user")
    if "R-999" not in ungrounded:
        failures.append("enrich: ungrounded verdict did not fall back to deterministic phrasing")

    print(f"[enrich preflight] grounded-templating + ungrounded-rejection, {len(failures)} failed")
    return failures


async def compaction_preflight() -> list:
    """Compaction invariants (no graph): an oversized list field crushes under
    the cap; the error item and the rare-status item ALWAYS survive; the
    sentinel ref round-trips; error results and small lists pass through
    untouched; crush_result never raises on hostile shapes. Fully synthetic."""
    import compaction  # noqa: E402

    if not getattr(config, "COMPACTION_ENABLED", True):
        print("[compaction preflight] skipped (COMPACTION_ENABLED=0)")
        return []

    failures = []
    n = 40
    rows = [{"id": i, "status": "ok", "name": f"item-{i}"} for i in range(n)]
    rows[17]["error"] = "gateway timeout"
    rows[23]["status"] = "backordered"
    result = {"tool": "search_catalog", "items": rows, "summary": f"Found {n} items."}

    crushed = compaction.crush_result(result)
    kept = crushed["items"]
    if len(kept) > config.COMPACTION_MAX_ITEMS + 3:
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

    print(f"[compaction preflight] {n} rows -> {len(kept)} kept, {len(failures)} failed")
    return failures


async def filler_preflight() -> list:
    """Filler-channel invariants (no graph): bank SHAPE (non-empty lists of
    non-empty strings) and EMIT/ROTATION/KILL-SWITCH are gated; per-flow bank
    EXHAUSTIVENESS is a warning (quality nudge, not a blocker)."""
    import nodes  # noqa: E402
    import filler  # noqa: E402
    import tools  # noqa: E402

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

    sample_tool = next((f.tool for f in config.FLOWS.values()
                        if f.tool in tools.TOOL_REGISTRY), None)
    real_delay, real_enabled = config.FILLER_DELAY_MS, config.FILLER_ENABLED
    config.FILLER_DELAY_MS, config.FILLER_ENABLED = 0, True
    sink: asyncio.Queue = asyncio.Queue()
    token = filler.set_sink(sink)
    filler.reset_rotation()
    try:
        if sample_tool is None:
            _warn("filler: no FLOW tool registered — emit/rotation not exercised")
        first = config.FILLERS_BY_TOOL.get(sample_tool) or config.FILLER_DEFAULT
        emitted = []
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

    print(f"[filler preflight] bank-shape + emit/rotation/kill-switch, {len(failures)} failed")
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

    print(f"[structural preflight] escalation-wiring gate + coverage warnings, {len(failures)} failed")
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


def call_arc_preflight() -> list:
    """Proactive SDR director (config.CALL_ARC) invariants — the zero-model
    agenda gate at the head of validator_node. Behavior is exercised on a
    SYNTHETIC arc so the coverage holds for EVERY domain (an inbound agent ships
    an empty CALL_ARC and the director is a no-op); the shipped arc, when
    present, gets a structural shape-check. validator_node reads config.CALL_ARC
    at call time, so a monkeypatched arc needs no graph rebuild."""
    import nodes  # noqa: E402

    failures = []

    # --- Shape gate on the SHIPPED arc (skips cleanly when empty) ---
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

    # --- Behavioral gate on a SYNTHETIC arc (monkeypatched) ---
    Stage = config.Stage
    real_arc = getattr(config, "CALL_ARC", ())
    config.CALL_ARC = (
        Stage(name="discovery", objective="find the decision maker",
              line="Quick question — are you the right person for this?",
              advance_when={"agent_led_once": True}),
        Stage(name="close", objective="propose the next step",
              line="Can I set up a follow-up for you?", advance_when={}),
    )
    try:
        # (a) AGENT LEADS + lazy-init: a bare reactive turn with no floor held
        #     initializes the cursor and APPENDS the stage's proactive move.
        led = nodes.validator_node({"draft_response": "Nice to meet you.",
                                    "category": "ANSWER", "intent": "chitchat"})
        if led.get("call_stage") != "discovery":
            failures.append(f"call_arc: cursor must lazy-init to first stage, got {led.get('call_stage')!r}")
        if "right person" not in led.get("final_response", "").lower():
            failures.append("call_arc: agent must LEAD (append the stage move) on an idle reactive turn")
        if led.get("stage_nudged") != "discovery":
            failures.append("call_arc: the one-shot guard must mark the stage led")

        # (b) ADVANCE: once the discovery move is made (stage_nudged), the cursor
        #     advances to close and speaks its line.
        adv = nodes.validator_node({"draft_response": "Got it.", "category": "ANSWER",
                                    "intent": "chitchat", "call_stage": "discovery",
                                    "stage_nudged": "discovery"})
        if adv.get("call_stage") != "close":
            failures.append(f"call_arc: cursor must advance when a stage's exit holds, got {adv.get('call_stage')!r}")

        # (c) ONE-SHOT: a terminal stage already led makes NO second move.
        quiet = nodes.validator_node({"draft_response": "Okay.", "category": "ANSWER",
                                      "intent": "chitchat", "call_stage": "close",
                                      "stage_nudged": "close"})
        if "follow-up" in quiet.get("final_response", "").lower():
            failures.append("call_arc: broken-record — a led terminal stage must not re-nudge")

        # (d) FIRM-NO PRESERVED: a goodbye holds the floor -> director stands
        #     down (no stage line leaks, no cursor write).
        bye = nodes.validator_node({"draft_response": "Thanks for your time, take care.",
                                    "intent": "goodbye", "exit_conversation": True,
                                    "call_stage": "discovery"})
        if "right person" in bye.get("final_response", "").lower() or bye.get("call_stage"):
            failures.append("call_arc: director must stand down on a firm-no/goodbye")

        # (e) STANDS DOWN mid-flow: a pending flow means think leads -> no move.
        held = nodes.validator_node({"draft_response": "Could you tell me your order number?",
                                     "category": "FLOW", "intent": "some_flow",
                                     "pending_intent": "some_flow", "call_stage": "discovery"})
        if "right person" in held.get("final_response", "").lower() or held.get("call_stage"):
            failures.append("call_arc: director must stand down while a flow is pending")

        # (f) FLOW ENTRY (only if a flow exists): a qualify stage pointing at a
        #     real flow pends it and asks its first slot — the agent leads INTO it.
        flow_name = next(iter(config.FLOWS), None)
        if flow_name:
            config.CALL_ARC = (Stage(name="qualify", flow=flow_name,
                                     advance_when={"flow_complete": flow_name}),)
            enter = nodes.validator_node({"draft_response": "Hello!", "category": "ANSWER",
                                          "intent": "chitchat"})
            if enter.get("pending_intent") != flow_name:
                failures.append(f"call_arc: a flow stage must pend its flow, got {enter.get('pending_intent')!r}")
    finally:
        config.CALL_ARC = real_arc

    scope = f"{len(shipped)}-stage shipped arc" if shipped else "empty shipped arc (no-op)"
    print(f"[call-arc preflight] lead/advance/one-shot/firm-no/floor on a synthetic arc + {scope}, "
          f"{len(failures)} failed")
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


def context_budget_preflight() -> list:
    """Context payload budgets — the TTFT levers. The raw history window is
    capped at config.HISTORY_TURNS (older detail lives in session_facts /
    last_action / call_summary, not the prompt), and any uploaded knowledge is
    CHUNKED into retrieval-sized DOCS rather than appended to the static FACTS
    prompt (which would ride every think call)."""
    import nodes  # noqa: E402
    from langchain_core.messages import AIMessage, HumanMessage  # noqa: E402
    failures = []

    # (a) history window cap + recency (keep the MOST RECENT turns).
    n = config.HISTORY_TURNS
    msgs = []
    for i in range(n + 6):
        msgs.append(HumanMessage(content=f"u{i}"))
        msgs.append(AIMessage(content=f"a{i}"))
    hist = nodes._history({"recent_messages": msgs})
    if len(hist) != n:
        failures.append(f"history window: expected {n} turns in the prompt, got {len(hist)}")
    if hist and hist[-1]["content"] != f"a{n + 5}":
        failures.append("history window: must keep the MOST RECENT turns (recency)")

    # (b) uploaded knowledge -> chunked DOCS (loader tested directly; the demo
    #     ships no knowledge/ folder, so DOCS is unchanged there).
    sample = "\n\n".join(f"Paragraph {i} " + "word " * 40 for i in range(6))
    docs = config._chunk_text_to_docs("faq.md", sample, max_words=50)
    if len(docs) < 2:
        failures.append(f"knowledge chunking: a long file must split into >=2 docs, got {len(docs)}")
    for d in docs:
        if not d.get("id") or d.get("title") != "faq.md" or not d.get("text"):
            failures.append(f"knowledge chunking: malformed doc {d!r}")
    if "Additional uploaded knowledge" in getattr(config, "FACTS", ""):
        failures.append("knowledge: uploaded files must NOT be appended to FACTS — retrieval-gate them via DOCS")

    print(f"[context-budget preflight] history cap={n} + knowledge->DOCS chunking, {len(failures)} failed")
    return failures


async def summary_preflight() -> list:
    """Lead record (config.SUMMARY_TEMPLATE): the zero-model aggregator in
    validator_node + the call-end freetext synthesis (build_call_record).
    Exercised on a SYNTHETIC template so coverage holds for EVERY domain — an
    agent without a template ships an empty one and the record is a no-op.
    _update_summary / build_call_record read config.SUMMARY_TEMPLATE at call
    time, so a monkeypatch needs no graph rebuild."""
    import nodes  # noqa: E402
    failures = []
    SF = config.SummaryField
    real = getattr(config, "SUMMARY_TEMPLATE", ())

    try:
        # --- empty template => no record written; build_call_record passes through ---
        config.SUMMARY_TEMPLATE = ()
        out = nodes.validator_node({"draft_response": "Hi.", "category": "ANSWER",
                                    "intent": "chitchat"})
        if "call_summary" in out:
            failures.append("summary: empty template must not write call_summary")
        passthrough = await nodes.build_call_record({"call_summary": {"x": 1}})
        if passthrough != {"x": 1}:
            failures.append("summary: empty template build_call_record must pass the record through")

        # --- synthetic template: structured aggregation is ZERO-model ---
        config.SUMMARY_TEMPLATE = (
            SF(key="contact", source="fact:name", label="Contact"),
            SF(key="volume", source="slot:qualify.volume", label="Volume"),
            SF(key="follow_ups", source="followups", label="Follow-ups"),
            SF(key="needs", source="freetext", label="Needs"),
        )
        upd = nodes.validator_node({
            "draft_response": "Great.", "category": "FLOW", "intent": "qualify",
            "session_facts": {"name": "Dana"}, "slots": {"volume": "500"},
            "last_action": {"summary": "Booked a demo"}})
        rec = upd.get("call_summary") or {}
        if rec.get("contact") != "Dana":
            failures.append(f"summary: fact source must populate, got {rec.get('contact')!r}")
        if rec.get("volume") != "500":
            failures.append(f"summary: slot source must populate, got {rec.get('volume')!r}")
        if rec.get("follow_ups") != ["Booked a demo"]:
            failures.append(f"summary: followups must accumulate, got {rec.get('follow_ups')!r}")
        if "needs" in rec:
            failures.append("summary: _update_summary must NOT write freetext fields (they're off-path)")

        # --- call-end synthesis (mock): fills freetext, preserves structured ---
        done = await nodes.build_call_record({"call_summary": dict(rec), "recent_messages": []})
        if "needs" not in done:
            failures.append("summary: build_call_record must fill the freetext keys")
        if done.get("contact") != "Dana":
            failures.append("summary: build_call_record must preserve the structured fields")
    finally:
        config.SUMMARY_TEMPLATE = real

    print(f"[summary preflight] aggregate/freetext/no-op on a synthetic template, {len(failures)} failed")
    return failures


def objection_preflight() -> list:
    """Objection architecture (Acknowledge -> Isolate -> Pivot) invariants — the
    zero-model gate at the head of validator_node. Behavior runs on a SYNTHETIC
    objection intent + arc so coverage holds for EVERY domain (an agent with an
    empty OBJECTION_INTENTS is a no-op); the SHIPPED config gets a strict shape
    and word-budget gate. nodes reads these tuples at call time, so monkeypatched
    config needs no graph rebuild."""
    import nodes  # noqa: E402

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

    # --- Behavioral gate on a SYNTHETIC objection (monkeypatched) ---
    Stage = config.Stage
    real = (getattr(config, "OBJECTION_INTENTS", ()), getattr(config, "OBJECTION_TOPICS", {}),
            getattr(config, "OBJECTION_ISOLATE_TEMPLATE", ""), getattr(config, "CALL_ARC", ()),
            tuple(config.KNOWLEDGE_INTENTS), tuple(config.VALID_INTENTS))
    config.OBJECTION_INTENTS = ("obj_probe",)
    config.OBJECTION_TOPICS = {"obj_probe": "the price"}
    config.OBJECTION_ISOLATE_TEMPLATE = "Besides {topic}, is anything else holding you back?"
    config.KNOWLEDGE_INTENTS = tuple(config.KNOWLEDGE_INTENTS) + ("obj_probe",)
    config.VALID_INTENTS = tuple(config.VALID_INTENTS) + ("obj_probe",)
    config.CALL_ARC = (
        Stage(name="pitch", objective="book the meeting",
              nudge="Would a short demo next week help?", advance_when={}),
    )
    try:
        base = {"category": "ANSWER", "intent": "obj_probe", "call_stage": "pitch",
                "draft_response": "Totally fair, our price is locked for a year."}

        # (a) ISOLATE fires on the FIRST objection, and the director's pivot is
        #     SUPPRESSED so the turn ships exactly ONE question.
        first = nodes.validator_node(dict(base))
        out = first.get("final_response", "")
        if "anything else holding you back" not in out.lower():
            failures.append(f"objection: first objection must ask the isolate question, got {out!r}")
        if "demo next week" in out.lower():
            failures.append("objection: the stage nudge must be SUPPRESSED on the isolate turn "
                            "(one question per turn)")
        if out.count("?") != 1:
            failures.append(f"objection: isolate turn must ship exactly one question, got {out!r}")
        if first.get("objections_raised") != ["obj_probe"]:
            failures.append(f"objection: ledger must record the intent, got {first.get('objections_raised')!r}")

        # (b) ISOLATE IS ONE-PER-CALL: a second objection never re-isolates, but
        #     DOES pivot (the old one-shot guard let it end on the lead's terms).
        second = nodes.validator_node({**base, "intent": "obj_probe",
                                       "objections_raised": ["obj_probe"],
                                       "stage_nudged": "pitch"})
        out2 = second.get("final_response", "")
        if "anything else holding you back" in out2.lower():
            failures.append("objection: the isolate question must fire ONCE per call, never twice")
        if "demo next week" not in out2.lower():
            failures.append(f"objection: a REPEAT objection must still pivot back to the arc, got {out2!r}")

        # (c) LEDGER is deduped and ordered.
        if second.get("objections_raised") != ["obj_probe"]:
            failures.append(f"objection: ledger must dedupe, got {second.get('objections_raised')!r}")

        # (d) FLOOR: mid slot-fill the reply already ends in the flow's question,
        #     so the isolate must NOT fire — but the ledger still records it.
        held = nodes.validator_node({**base, "pending_intent": "some_flow",
                                     "draft_response": "Fair. What's your monthly volume?"})
        if "anything else holding you back" in held.get("final_response", "").lower():
            failures.append("objection: isolate must stand down while the lead holds the floor")
        if held.get("objections_raised") != ["obj_probe"]:
            failures.append("objection: the ledger must still record an objection raised mid-flow")

        # (e) NO-OP: an agent with no OBJECTION_INTENTS is untouched.
        config.OBJECTION_INTENTS = ()
        noop = nodes.validator_node(dict(base))
        if "objections_raised" in noop:
            failures.append("objection: empty OBJECTION_INTENTS must not write the ledger")
        if "holding you back" in noop.get("final_response", "").lower():
            failures.append("objection: empty OBJECTION_INTENTS must not isolate")
    finally:
        (config.OBJECTION_INTENTS, config.OBJECTION_TOPICS,
         config.OBJECTION_ISOLATE_TEMPLATE, config.CALL_ARC,
         config.KNOWLEDGE_INTENTS, config.VALID_INTENTS) = real

    scope = f"{len(shipped)} shipped objection intent(s)" if shipped else "no shipped objections (no-op)"
    print(f"[objection preflight] acknowledge/isolate-once/pivot/floor/word-budget + {scope}, "
          f"{len(failures)} failed")
    return failures


def tiedown_preflight() -> list:
    """Micro-commitment (tie-down) invariants — the zero-model gate at the TAIL
    of validator_node. The load-bearing one is ORDERING: the tie-down must be
    appended AFTER the stall fingerprint, or its rotating text gives an
    identical repeated reply a fresh fingerprint every turn and silently
    disables the stall detector (invariant 25)."""
    import nodes  # noqa: E402
    import filler  # noqa: E402

    failures = []
    real = (getattr(config, "TIEDOWNS", []), getattr(config, "TIEDOWN_EVERY_N_TURNS", 0),
            getattr(config, "MAX_REPLY_WORDS", 20), getattr(config, "CALL_ARC", ()))
    config.TIEDOWNS = ["Does that make sense?", "Are we on the same page?"]
    config.TIEDOWN_EVERY_N_TURNS = 2
    config.MAX_REPLY_WORDS = 20
    config.CALL_ARC = ()          # isolate the tie-down from the director
    filler.reset_rotation()
    try:
        # (a) FIRES on a statement-ending turn once the cadence is due.
        due = nodes.validator_node({"draft_response": "We ship within two days.",
                                    "category": "ANSWER", "intent": "chitchat",
                                    "turns_since_tiedown": 2})
        if "?" not in due.get("final_response", ""):
            failures.append(f"tiedown: must append on a due statement turn, got {due.get('final_response')!r}")
        if due.get("turns_since_tiedown") != 0:
            failures.append("tiedown: emitting must reset the pacing counter")

        # (b) NEVER a second question: a reply already ending in "?" is skipped.
        q = nodes.validator_node({"draft_response": "What's your monthly volume?",
                                  "category": "ANSWER", "intent": "chitchat",
                                  "turns_since_tiedown": 5})
        if q.get("final_response", "").count("?") != 1:
            failures.append(f"tiedown: must never add a 2nd question, got {q.get('final_response')!r}")

        # (c) NOT YET DUE: counter increments instead of firing.
        early = nodes.validator_node({"draft_response": "We ship within two days.",
                                      "category": "ANSWER", "intent": "chitchat",
                                      "turns_since_tiedown": 0})
        if "?" in early.get("final_response", ""):
            failures.append("tiedown: must not fire before TIEDOWN_EVERY_N_TURNS")
        if early.get("turns_since_tiedown") != 1:
            failures.append("tiedown: a non-firing statement turn must increment the counter")

        # (d) LEAD AGREED: an affirmation resets the cadence (never nag a yes).
        agreed = nodes.validator_node({"draft_response": "Great.", "category": "ANSWER",
                                       "intent": "chitchat", "user_message": "yes, that works",
                                       "turns_since_tiedown": 1})
        if agreed.get("turns_since_tiedown") != 0:
            failures.append("tiedown: a lead affirmation must reset the pacing counter")

        # (e) FLOOR: never speak over a firm no / handoff.
        bye = nodes.validator_node({"draft_response": "Thanks for your time.",
                                    "intent": "goodbye", "exit_conversation": True,
                                    "turns_since_tiedown": 9})
        if "?" in bye.get("final_response", ""):
            failures.append("tiedown: must stand down when the lead holds the floor")

        # (f) WORD BUDGET: a reply at the cap drops the tie-down rather than
        #     blowing the spoken budget.
        long_reply = " ".join(["word"] * 19) + "."
        capped = nodes.validator_node({"draft_response": long_reply, "category": "ANSWER",
                                       "intent": "chitchat", "turns_since_tiedown": 5})
        if "?" in capped.get("final_response", ""):
            failures.append("tiedown: must be dropped when it would exceed MAX_REPLY_WORDS")

        # (g) THE ORDERING INVARIANT: with tie-downs ON, an identical repeated
        #     reply must STILL trip the stall detector — proof the fingerprint is
        #     taken on the body, before the rotating tie-down is appended.
        if config.STALL_THRESHOLD:
            body = "We ship within two days."
            st = {"draft_response": body, "category": "ANSWER", "intent": "chitchat",
                  "last_reply_fingerprint": body.casefold(),
                  "stall_count": config.STALL_THRESHOLD - 1, "turns_since_tiedown": 5}
            trip = nodes.validator_node(st)
            escalated = (config.STALL_TEXT.casefold() in trip.get("final_response", "").casefold())
            if not escalated:
                failures.append("tiedown: ORDERING BUG — a rotating tie-down masked the stall "
                                "detector; fingerprint the body BEFORE appending the tie-down")

        # (h) KILL SWITCH: 0 disables the gate and never writes the counter.
        config.TIEDOWN_EVERY_N_TURNS = 0
        off = nodes.validator_node({"draft_response": "We ship within two days.",
                                    "category": "ANSWER", "intent": "chitchat",
                                    "turns_since_tiedown": 9})
        if "?" in off.get("final_response", "") or "turns_since_tiedown" in off:
            failures.append("tiedown: gate ran while TIEDOWN_EVERY_N_TURNS=0")
    finally:
        (config.TIEDOWNS, config.TIEDOWN_EVERY_N_TURNS,
         config.MAX_REPLY_WORDS, config.CALL_ARC) = real
        filler.reset_rotation()

    # Shipped-config shape: every tie-down must be a SHORT question.
    for t in (getattr(config, "TIEDOWNS", []) or []):
        if not t.rstrip().endswith("?"):
            failures.append(f"tiedown: {t!r} must be a question (it is a micro-commitment ask)")
        if len([w for w in t.split() if any(c.isalnum() for c in w)]) > 6:
            _warn(f"tiedown: {t!r} is wordy — a tie-down should be 3-6 words")

    print(f"[tiedown preflight] fire/no-2nd-question/cadence/floor/budget/stall-ordering/kill-switch, "
          f"{len(failures)} failed")
    return failures


async def main() -> int:
    failures = []
    failures += run_hook_checks()
    failures += structural_preflight()
    failures += retrieval_coverage_preflight()
    failures += stall_preflight()
    failures += call_arc_preflight()
    failures += objection_preflight()
    failures += tiedown_preflight()
    failures += voice_budget_preflight()
    failures += persona_preflight()
    failures += context_budget_preflight()
    failures += await summary_preflight()
    failures += fast_router_preflight()
    failures += await plan_preflight()
    failures += await enrich_preflight()
    failures += await compaction_preflight()
    failures += await filler_preflight()
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
    print("SELF-TEST PASSED — engine preflights + config-derived smoke walk, "
          "all invariants hold.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
