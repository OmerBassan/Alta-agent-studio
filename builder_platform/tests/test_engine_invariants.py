# -*- coding: utf-8 -*-
"""Fixed-ENGINE invariants, proven once against boilerplate/'s own default
config — NOT re-run per generated agent.

2026-08-21 split: these checks used to live inside boilerplate/selftest.py as
"preflights", but every one of them runs on SYNTHETIC or monkeypatched data
specifically so it holds for EVERY domain — meaning it passes or fails
identically no matter which agent's config.py is loaded. Since engine files
(nodes.py, filler.py, compaction.py, graph.py, llm_client.py) are copied
VERBATIM per agent and never edited per agent (see repo CLAUDE.md), re-proving
them on every single generated agent's build was pure redundancy. They now run
here, once, as part of the platform's own test suite — triggered when
boilerplate/ itself changes, not per generation.

What STAYS in boilerplate/selftest.py instead (config-derived, must run per
agent): structural shape gates (escalation wiring, CALL_ARC/OBJECTION_INTENTS/
TIEDOWNS shape, FACTS leak), the smoke walk, voice/persona checks, retrieval
coverage, hook checks. See that file's own docstring.

Covers: stall detector, fast-router fall-through/kill-switch, planner clamp,
enrich verdict discipline, compaction, filler emit/rotation/kill-switch,
CALL_ARC director behavior, objection Acknowledge->Isolate->Pivot, tie-down
cadence/floor/stall-ordering, history-window cap, knowledge chunking, and
SUMMARY_TEMPLATE aggregation — all against boilerplate's shipped demo config,
which ships non-empty FLOWS/CALL_ARC-capable structures so every mechanic is
actually exercised (never skipped).
"""

import asyncio
import os
import sys

# Force mock mode BEFORE any boilerplate import reads the environment.
os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_BASE_URL"] = ""

BOILERPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "boilerplate")
sys.path.insert(0, os.path.abspath(BOILERPLATE_DIR))

import compaction  # noqa: E402
import config  # noqa: E402
import filler  # noqa: E402
import nodes  # noqa: E402
import tools  # noqa: E402
from langchain_core.messages import AIMessage, HumanMessage  # noqa: E402
from llm_client import llm_client  # noqa: E402
from schemas import EnrichVerdict, PlanResult, PlanStep  # noqa: E402


def test_stall_detector_trip_reset_killswitch():
    """The N-th consecutive identical reply is swapped for STALL_TEXT, a
    changed reply resets the counter, and STALL_THRESHOLD=0 disables the
    gate."""
    if not config.STALL_THRESHOLD:
        return  # gate disabled in this shipped config; nothing to prove

    trip = nodes.validator_node({"draft_response": "Same reply.",
                                 "last_reply_fingerprint": "same reply.",
                                 "stall_count": config.STALL_THRESHOLD - 1})
    assert ("talk to a human" in trip.get("final_response", "").lower()
            or trip.get("final_response") == config.STALL_TEXT), \
        f"threshold reply not swapped, got {trip.get('final_response')!r}"
    assert trip.get("stall_count") == 1, "counter did not reset after escalation"

    fresh = nodes.validator_node({"draft_response": "A different reply.",
                                  "last_reply_fingerprint": "same reply.",
                                  "stall_count": config.STALL_THRESHOLD - 1})
    assert fresh.get("final_response") == "A different reply." and fresh.get("stall_count") == 1, \
        "a changed reply must reset the counter, not escalate"

    real = config.STALL_THRESHOLD
    config.STALL_THRESHOLD = 0
    try:
        off = nodes.validator_node({"draft_response": "Same reply.",
                                    "last_reply_fingerprint": "same reply.",
                                    "stall_count": 99})
        assert off.get("final_response") == "Same reply." and "stall_count" not in off, \
            "gate ran while STALL_THRESHOLD=0"
    finally:
        config.STALL_THRESHOLD = real


def test_fast_router_fallthrough_and_killswitch():
    """FALL-THROUGH ON DOUBT (negation, no extraction, disabled gate) must
    never wrongly bypass the INTENT tier — holds for ANY domain."""
    if not config.FLOWS:
        return
    flow_name = next(iter(config.FLOWS))

    for msg, why in [
        ("no wait, cancel that", "negation must fall through"),
        ("hmm, let me think about it", "no extraction must fall through"),
    ]:
        assert nodes._fast_route(msg, flow_name, {}) is None, f"fast_route({msg!r}): {why}"

    real = config.FAST_ROUTER_ENABLED
    config.FAST_ROUTER_ENABLED = False
    try:
        assert nodes._fast_route("the usual please", flow_name, {}) is None, \
            "fast_route: ran while FAST_ROUTER_ENABLED=False"
    finally:
        config.FAST_ROUTER_ENABLED = real


def test_planner_clamp():
    """A live model emitting an unknown action and too many steps is clamped
    in code: the bad action dropped, the array truncated to MAX_PLAN_STEPS,
    off-contract slots stripped. Uses the domain's first real flow name."""
    if not config.FLOWS:
        return
    real_flow = next(iter(config.FLOWS))

    bogus = PlanResult(steps=(
        [PlanStep(action=real_flow, slots={"not_a_slot": "x"}),
         PlanStep(action="launch_the_missiles", slots={})]
        + [PlanStep(action=real_flow, slots={}) for _ in range(config.MAX_PLAN_STEPS + 2)]))

    async def _fake_structured(*_a, **_k):
        return bogus

    async def _run():
        real_mock, real_structured = llm_client.mock, llm_client.generate_structured
        llm_client.mock, llm_client.generate_structured = False, _fake_structured
        try:
            return await nodes.planner_node({"user_message": "do many things"})
        finally:
            llm_client.mock, llm_client.generate_structured = real_mock, real_structured

    out = asyncio.run(_run())
    plan = out.get("plan_steps", [])
    assert len(plan) <= config.MAX_PLAN_STEPS, f"{len(plan)} steps survived (cap {config.MAX_PLAN_STEPS})"
    assert all(s["action"] in config.FLOWS for s in plan), "an unknown action survived into the plan"
    assert not any("not_a_slot" in s.get("slots", {}) for s in plan), \
        "a slot outside the flow contract survived"


def test_enrich_verdict_discipline():
    """The SLM returns a verdict, NEVER prose. A grounded verdict yields a
    deterministic templated reply carrying the fact + closing question; an
    ungrounded fact is rejected and the node falls back to the summary
    verbatim."""
    tool_name = next((f.tool for f in config.FLOWS.values()), None)
    if tool_name is None:
        return
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

    grounded = asyncio.run(_run_verdict(
        EnrichVerdict(tone="confirm", key_facts=["R-999", "done"], grounded=True)))
    assert "R-999" in grounded, "grounded fact 'R-999' missing from templated reply"
    assert grounded.rstrip().endswith("?"), "deterministic closing question not appended"

    ungrounded = asyncio.run(_run_verdict(
        EnrichVerdict(tone="confirm", key_facts=["next Tuesday"], grounded=True)))
    assert "Tuesday" not in ungrounded, "ungrounded fact 'next Tuesday' leaked to the user"
    assert "R-999" in ungrounded, "ungrounded verdict did not fall back to deterministic phrasing"


def test_compaction_invariants():
    """An oversized list field crushes under the cap; the error item and the
    rare-status item ALWAYS survive; the sentinel ref round-trips; error
    results and small lists pass through untouched; crush_result never raises
    on hostile shapes. Fully synthetic."""
    n = 40
    rows = [{"id": i, "status": "ok", "name": f"item-{i}"} for i in range(n)]
    rows[17]["error"] = "gateway timeout"
    rows[23]["status"] = "backordered"
    result = {"tool": "search_catalog", "items": rows, "summary": f"Found {n} items."}

    crushed = compaction.crush_result(result)
    kept = crushed["items"]
    assert len(kept) <= config.COMPACTION_MAX_ITEMS + 3, \
        f"kept {len(kept)} items (budget {config.COMPACTION_MAX_ITEMS})"
    assert any(isinstance(x, dict) and x.get("id") == 17 for x in kept), "the error item was dropped"
    assert any(isinstance(x, dict) and x.get("id") == 23 for x in kept), "the rare-status item was dropped"

    sentinel = next((x for x in kept if isinstance(x, dict) and compaction.SENTINEL_KEY in x), None)
    assert sentinel is not None, "no sentinel marker appended"
    import re as _re
    m = _re.search(r"ref='([0-9a-f]+)'", sentinel[compaction.SENTINEL_KEY])
    full = compaction.retrieve_full_result(ref=m.group(1)) if m else {}
    assert len(full.get("items") or []) == n, "retrieve_full_result did not return the full original"
    assert compaction.retrieve_full_result(ref="nope").get("error") is not None, \
        "unknown ref did not return an error result"

    err = {"tool": "search_catalog", "error": "backend down", "items": rows, "summary": "x"}
    assert compaction.crush_result(err) is err, "an ERROR result was modified (must pass through)"
    small = {"tool": "t", "items": rows[:3], "summary": "x"}
    assert compaction.crush_result(small)["items"] == rows[:3], "a small list was modified"
    for hostile in (None, "text", {"items": [object()] * 50, "summary": "x"}):
        compaction.crush_result(hostile)  # type: ignore[arg-type]  # must not raise


def test_filler_emit_rotation_killswitch():
    """Tool fillers emit exactly once per call, rotate across repeated calls,
    and respect the FILLER_ENABLED kill switch."""
    sample_tool = next((f.tool for f in config.FLOWS.values()
                        if f.tool in tools.TOOL_REGISTRY), None)
    if sample_tool is None:
        return
    # tool_exec runs a tool only as the active flow's action.
    sample_flow = next(n for n, f in config.FLOWS.items() if f.tool == sample_tool)

    async def _run():
        real_delay, real_enabled = config.FILLER_DELAY_MS, config.FILLER_ENABLED
        config.FILLER_DELAY_MS, config.FILLER_ENABLED = 0, True
        sink: asyncio.Queue = asyncio.Queue()
        token = filler.set_sink(sink)
        filler.reset_rotation()
        try:
            first = config.FILLERS_BY_TOOL.get(sample_tool) or config.FILLER_DEFAULT
            emitted = []
            for _ in range(2):
                await nodes.tool_exec_node(
                    {"cold_payload": {"tool": sample_tool, "args": {}}, "intent": sample_flow,
                     "tool_call_count": 0, "session_facts": {}})
                events = []
                while not sink.empty():
                    events.append(sink.get_nowait())
                tool_events = [e for e in events if e.get("kind") == "tool"]
                assert len(tool_events) == 1, f"expected exactly 1 tool filler per call, got {len(tool_events)}"
                if tool_events[0].get("text"):
                    emitted.append(tool_events[0]["text"])
            if len(first) >= 2 and len(emitted) == 2:
                assert emitted[0] != emitted[1], "variants did not rotate across calls (same phrase twice)"

            config.FILLER_ENABLED = False
            filler.reset_rotation()
            await nodes.tool_exec_node(
                {"cold_payload": {"tool": sample_tool, "args": {}}, "intent": sample_flow,
                 "tool_call_count": 0, "session_facts": {}})
            assert sink.empty(), "emitted while FILLER_ENABLED=False"
        finally:
            filler.reset_sink(token)
            config.FILLER_DELAY_MS, config.FILLER_ENABLED = real_delay, real_enabled
            filler.reset_rotation()

    asyncio.run(_run())


def test_call_arc_director_behavioral():
    """The zero-model CALL_ARC director: agent LEADS on an idle turn, ADVANCES
    when a stage's exit holds, is ONE-SHOT on a led terminal stage, STANDS DOWN
    on a firm-no/goodbye or mid-flow, and a qualify stage pends its flow.
    Exercised on a SYNTHETIC arc so coverage holds for EVERY domain (an inbound
    agent ships an empty CALL_ARC and the director is a no-op)."""
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
        led = nodes.validator_node({"draft_response": "Nice to meet you.",
                                    "category": "ANSWER", "intent": "chitchat"})
        assert led.get("call_stage") == "discovery", \
            f"cursor must lazy-init to first stage, got {led.get('call_stage')!r}"
        assert "right person" in led.get("final_response", "").lower(), \
            "agent must LEAD (append the stage move) on an idle reactive turn"
        assert led.get("stage_nudged") == "discovery", "the one-shot guard must mark the stage led"

        adv = nodes.validator_node({"draft_response": "Got it.", "category": "ANSWER",
                                    "intent": "chitchat", "call_stage": "discovery",
                                    "stage_nudged": "discovery"})
        assert adv.get("call_stage") == "close", \
            f"cursor must advance when a stage's exit holds, got {adv.get('call_stage')!r}"

        quiet = nodes.validator_node({"draft_response": "Okay.", "category": "ANSWER",
                                      "intent": "chitchat", "call_stage": "close",
                                      "stage_nudged": "close"})
        assert "follow-up" not in quiet.get("final_response", "").lower(), \
            "broken-record — a led terminal stage must not re-nudge"

        bye = nodes.validator_node({"draft_response": "Thanks for your time, take care.",
                                    "intent": "goodbye", "exit_conversation": True,
                                    "call_stage": "discovery"})
        assert "right person" not in bye.get("final_response", "").lower() and not bye.get("call_stage"), \
            "director must stand down on a firm-no/goodbye"

        held = nodes.validator_node({"draft_response": "Could you tell me your order number?",
                                     "category": "FLOW", "intent": "some_flow",
                                     "pending_intent": "some_flow", "call_stage": "discovery"})
        assert "right person" not in held.get("final_response", "").lower() and not held.get("call_stage"), \
            "director must stand down while a flow is pending"

        flow_name = next(iter(config.FLOWS), None)
        if flow_name:
            config.CALL_ARC = (Stage(name="qualify", flow=flow_name,
                                     advance_when={"flow_complete": flow_name}),)
            enter = nodes.validator_node({"draft_response": "Hello!", "category": "ANSWER",
                                          "intent": "chitchat"})
            assert enter.get("pending_intent") == flow_name, \
                f"a flow stage must pend its flow, got {enter.get('pending_intent')!r}"
    finally:
        config.CALL_ARC = real_arc


def test_objection_acknowledge_isolate_pivot_behavioral():
    """The zero-model objection gate: ISOLATE fires on the first objection
    (suppressing the director's pivot so exactly one question ships), never
    re-isolates on a repeat (which instead pivots), the ledger dedupes, the
    floor (mid-flow) suppresses isolate but still records it, and an agent
    with no OBJECTION_INTENTS is untouched. Exercised on a SYNTHETIC objection
    intent + arc so coverage holds for EVERY domain."""
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

        first = nodes.validator_node(dict(base))
        out = first.get("final_response", "")
        assert "anything else holding you back" in out.lower(), \
            f"first objection must ask the isolate question, got {out!r}"
        assert "demo next week" not in out.lower(), \
            "the stage nudge must be SUPPRESSED on the isolate turn (one question per turn)"
        assert out.count("?") == 1, f"isolate turn must ship exactly one question, got {out!r}"
        assert first.get("objections_raised") == ["obj_probe"], \
            f"ledger must record the intent, got {first.get('objections_raised')!r}"

        second = nodes.validator_node({**base, "intent": "obj_probe",
                                       "objections_raised": ["obj_probe"],
                                       "stage_nudged": "pitch"})
        out2 = second.get("final_response", "")
        assert "anything else holding you back" not in out2.lower(), \
            "the isolate question must fire ONCE per call, never twice"
        assert "demo next week" in out2.lower(), \
            f"a REPEAT objection must still pivot back to the arc, got {out2!r}"
        assert second.get("objections_raised") == ["obj_probe"], \
            f"ledger must dedupe, got {second.get('objections_raised')!r}"

        held = nodes.validator_node({**base, "pending_intent": "some_flow",
                                     "draft_response": "Fair. What's your monthly volume?"})
        assert "anything else holding you back" not in held.get("final_response", "").lower(), \
            "isolate must stand down while the lead holds the floor"
        assert held.get("objections_raised") == ["obj_probe"], \
            "the ledger must still record an objection raised mid-flow"

        config.OBJECTION_INTENTS = ()
        noop = nodes.validator_node(dict(base))
        assert "objections_raised" not in noop, "empty OBJECTION_INTENTS must not write the ledger"
        assert "holding you back" not in noop.get("final_response", "").lower(), \
            "empty OBJECTION_INTENTS must not isolate"
    finally:
        (config.OBJECTION_INTENTS, config.OBJECTION_TOPICS,
         config.OBJECTION_ISOLATE_TEMPLATE, config.CALL_ARC,
         config.KNOWLEDGE_INTENTS, config.VALID_INTENTS) = real


def test_tiedown_cadence_floor_stall_ordering_behavioral():
    """The zero-model tie-down gate: FIRES on a due statement turn, NEVER a
    second question, NOT YET DUE increments the counter, a lead affirmation
    resets cadence, stands down on the floor (firm-no), drops under the word
    budget, the KILL SWITCH disables it — and, load-bearing, the tie-down is
    fingerprinted for stall detection BEFORE it's appended (an identical
    repeated reply must still trip the stall detector)."""
    real = (getattr(config, "TIEDOWNS", []), getattr(config, "TIEDOWN_EVERY_N_TURNS", 0),
            getattr(config, "MAX_REPLY_WORDS", 20), getattr(config, "CALL_ARC", ()))
    config.TIEDOWNS = ["Does that make sense?", "Are we on the same page?"]
    config.TIEDOWN_EVERY_N_TURNS = 2
    config.MAX_REPLY_WORDS = 20
    config.CALL_ARC = ()          # isolate the tie-down from the director
    filler.reset_rotation()
    try:
        due = nodes.validator_node({"draft_response": "We ship within two days.",
                                    "category": "ANSWER", "intent": "chitchat",
                                    "turns_since_tiedown": 2})
        assert "?" in due.get("final_response", ""), \
            f"must append on a due statement turn, got {due.get('final_response')!r}"
        assert due.get("turns_since_tiedown") == 0, "emitting must reset the pacing counter"

        q = nodes.validator_node({"draft_response": "What's your monthly volume?",
                                  "category": "ANSWER", "intent": "chitchat",
                                  "turns_since_tiedown": 5})
        assert q.get("final_response", "").count("?") == 1, \
            f"must never add a 2nd question, got {q.get('final_response')!r}"

        early = nodes.validator_node({"draft_response": "We ship within two days.",
                                      "category": "ANSWER", "intent": "chitchat",
                                      "turns_since_tiedown": 0})
        assert "?" not in early.get("final_response", ""), "must not fire before TIEDOWN_EVERY_N_TURNS"
        assert early.get("turns_since_tiedown") == 1, "a non-firing statement turn must increment the counter"

        agreed = nodes.validator_node({"draft_response": "Great.", "category": "ANSWER",
                                       "intent": "chitchat", "user_message": "yes, that works",
                                       "turns_since_tiedown": 1})
        assert agreed.get("turns_since_tiedown") == 0, "a lead affirmation must reset the pacing counter"

        bye = nodes.validator_node({"draft_response": "Thanks for your time.",
                                    "intent": "goodbye", "exit_conversation": True,
                                    "turns_since_tiedown": 9})
        assert "?" not in bye.get("final_response", ""), "must stand down when the lead holds the floor"

        long_reply = " ".join(["word"] * 19) + "."
        capped = nodes.validator_node({"draft_response": long_reply, "category": "ANSWER",
                                       "intent": "chitchat", "turns_since_tiedown": 5})
        assert "?" not in capped.get("final_response", ""), \
            "must be dropped when it would exceed MAX_REPLY_WORDS"

        if config.STALL_THRESHOLD:
            body = "We ship within two days."
            st = {"draft_response": body, "category": "ANSWER", "intent": "chitchat",
                  "last_reply_fingerprint": body.casefold(),
                  "stall_count": config.STALL_THRESHOLD - 1, "turns_since_tiedown": 5}
            trip = nodes.validator_node(st)
            escalated = (config.STALL_TEXT.casefold() in trip.get("final_response", "").casefold())
            assert escalated, ("ORDERING BUG — a rotating tie-down masked the stall detector; "
                               "fingerprint the body BEFORE appending the tie-down")

        config.TIEDOWN_EVERY_N_TURNS = 0
        off = nodes.validator_node({"draft_response": "We ship within two days.",
                                    "category": "ANSWER", "intent": "chitchat",
                                    "turns_since_tiedown": 9})
        assert "?" not in off.get("final_response", "") and "turns_since_tiedown" not in off, \
            "gate ran while TIEDOWN_EVERY_N_TURNS=0"
    finally:
        (config.TIEDOWNS, config.TIEDOWN_EVERY_N_TURNS,
         config.MAX_REPLY_WORDS, config.CALL_ARC) = real
        filler.reset_rotation()


def test_history_window_cap_and_recency():
    """The raw history window is capped at config.HISTORY_TURNS and keeps the
    MOST RECENT turns (older detail lives in session_facts/last_action/
    call_summary, not the prompt)."""
    n = config.HISTORY_TURNS
    msgs = []
    for i in range(n + 6):
        msgs.append(HumanMessage(content=f"u{i}"))
        msgs.append(AIMessage(content=f"a{i}"))
    hist = nodes._history({"recent_messages": msgs})
    assert len(hist) == n, f"expected {n} turns in the prompt, got {len(hist)}"
    assert hist[-1]["content"] == f"a{n + 5}", "must keep the MOST RECENT turns (recency)"


def test_knowledge_chunking():
    """Uploaded knowledge is chunked into retrieval-sized DOCS rather than
    appended to the static FACTS prompt (which would ride every think call)."""
    sample = "\n\n".join(f"Paragraph {i} " + "word " * 40 for i in range(6))
    docs = config._chunk_text_to_docs("faq.md", sample, max_words=50)
    assert len(docs) >= 2, f"a long file must split into >=2 docs, got {len(docs)}"
    for d in docs:
        assert d.get("id") and d.get("title") == "faq.md" and d.get("text"), f"malformed doc {d!r}"


def test_summary_template_aggregation():
    """config.SUMMARY_TEMPLATE: the zero-model aggregator in validator_node +
    the call-end freetext synthesis (build_call_record). Exercised on a
    SYNTHETIC template so coverage holds for EVERY domain — an agent without a
    template ships an empty one and the record is a no-op."""
    SF = config.SummaryField
    real = getattr(config, "SUMMARY_TEMPLATE", ())

    async def _run():
        try:
            config.SUMMARY_TEMPLATE = ()
            out = nodes.validator_node({"draft_response": "Hi.", "category": "ANSWER",
                                        "intent": "chitchat"})
            assert "call_summary" not in out, "empty template must not write call_summary"
            passthrough = await nodes.build_call_record({"call_summary": {"x": 1}})
            assert passthrough == {"x": 1}, "empty template build_call_record must pass the record through"

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
            assert rec.get("contact") == "Dana", f"fact source must populate, got {rec.get('contact')!r}"
            assert rec.get("volume") == "500", f"slot source must populate, got {rec.get('volume')!r}"
            assert rec.get("follow_ups") == ["Booked a demo"], \
                f"followups must accumulate, got {rec.get('follow_ups')!r}"
            assert "needs" not in rec, "_update_summary must NOT write freetext fields (they're off-path)"

            done = await nodes.build_call_record({"call_summary": dict(rec), "recent_messages": []})
            assert "needs" in done, "build_call_record must fill the freetext keys"
            assert done.get("contact") == "Dana", "build_call_record must preserve the structured fields"
        finally:
            config.SUMMARY_TEMPLATE = real

    asyncio.run(_run())
