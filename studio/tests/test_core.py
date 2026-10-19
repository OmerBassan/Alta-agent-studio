"""The Core's guarantees, each proven by a scripted agent that tries to break it.

Every test names the requirement it proves. A scripted agent stands in for the
model so that each check is shown to fire on a deliberate violation (FR96),
rather than hoping a live model happens to attempt it.
"""

import asyncio
import typing
from datetime import datetime, timedelta, timezone

import pytest

from studio.core import AgentView, CoreSettings, EpisodeStore
from studio.core.types import (Claim, ClarifyRequest, EffectRequest, EscalateRequest, FactUpdate, ReadRequest,
                               ResolutionClaim, RespondRequest, RetrieveRequest, SuspendRequest)
from studio.core.vocabulary import REASON_CLASS, Reason
from studio.tests.helpers import (BUSINESSES, DENTAL_FACTS, MONDAY, SUNDAY, args, ask_to_confirm, book, check,
                                  booked_reply, build_world, facts, last_evidence)

DENTAL = BUSINESSES / "dental" / "specification.toml"
TENANT = "bright-smile-dental"


@pytest.fixture
def runner():
    with asyncio.Runner() as r:
        yield r


@pytest.fixture
def world(runner):
    return build_world(runner, [DENTAL])


def book_happily(world, conversation="c1"):
    """The full approved path: ask, confirm, requester says yes, book, reply."""
    first = world.send("Hi, I'd like a check-up on Monday at 9. Ada Lovelace, ada@example.com",
                       conversation=conversation, script=[ask_to_confirm()])
    second = world.send("yes", conversation=conversation, script=[check(), book(), booked_reply])
    return first, second


# --- the approved path ----------------------------------------------------------------

def test_confirmed_booking_is_executed_once_and_verified_by_read_back(world):
    first, second = book_happily(world)
    assert first.lifecycle == "active" and second.lifecycle == "closed"
    evidence = world.store.evidence(TENANT, second.episode_id)
    kinds = [e["kind"] for e in evidence]
    assert "confirmation_granted" in kinds and "effect_verified" in kinds
    assert sum(world.calendar.executions.values()) == 1
    resolution = world.store.resolutions(TENANT, second.episode_id)[0]
    assert resolution["served"] == 1 and resolution["authority"] == "capability:book_visit"
    assert world.store.get_episode(TENANT, second.episode_id).close_reason == "resolved"


def test_disclosure_is_in_the_first_message_only(world):
    first, second = book_happily(world)
    disclosure = "automated assistant"
    assert disclosure in first.messages[0].text
    assert disclosure not in second.messages[0].text


# --- FR53, DL-008: confirmation is the requester's, bound to the exact payload ----------

def test_effect_without_confirmation_is_refused_and_nothing_runs(world):
    out = world.send("Book me in", script=[check(), book(with_facts=True), RespondRequest(message="ok")])
    assert ("business_refusal", "confirmation_missing") in world.denials()
    assert sum(world.calendar.executions.values()) == 0
    assert out.lifecycle == "active"


def test_a_yes_inside_a_longer_sentence_is_not_consent(world):
    world.send("check-up Monday 9, Ada, ada@example.com", script=[ask_to_confirm()])
    world.send("yes, but my cheek is really puffy now", script=[check(), book(), RespondRequest(message="ok")])
    assert ("business_refusal", "confirmation_missing") in world.denials()
    assert sum(world.calendar.executions.values()) == 0


def test_a_bare_no_declines(world):
    world.send("check-up Monday 9", script=[ask_to_confirm()])
    out = world.send("no", script=[check(), book(), RespondRequest(message="No problem.")])
    offers = world.store.offers(TENANT, out.episode_id, "confirmation")
    assert [o["state"] for o in offers] == ["declined"]
    assert sum(world.calendar.executions.values()) == 0


def test_changing_the_payload_after_consent_is_refused(world):
    world.send("check-up Monday 9", script=[ask_to_confirm()])
    moved = {**DENTAL_FACTS, "preferred_time": "11:00"}
    world.send("yes", script=[check(moved), book(moved, with_facts=True), RespondRequest(message="ok")])
    assert ("business_refusal", "confirmation_missing") in world.denials()
    assert sum(world.calendar.executions.values()) == 0


def test_a_confirmation_cannot_be_reused_in_another_conversation(world):
    world.send("check-up Monday 9", conversation="a", script=[ask_to_confirm()])
    world.send("yes", conversation="a", script=[RespondRequest(message="Thanks.")])
    world.send("check-up Monday 9", conversation="b", script=[check(), book(with_facts=True), RespondRequest(message="ok")])
    assert ("business_refusal", "confirmation_missing") in world.denials()
    assert sum(world.calendar.executions.values()) == 0


def test_a_confirmation_expires_when_something_else_is_asked(world):
    world.send("check-up Monday 9", script=[ask_to_confirm()])
    world.send("hmm", script=[ClarifyRequest(message="Which day suits you best?")])
    out = world.send("yes", script=[check(), book(), RespondRequest(message="ok")])
    assert [o["state"] for o in world.store.offers(TENANT, out.episode_id, "confirmation")] == ["expired"]
    assert sum(world.calendar.executions.values()) == 0


def test_a_consumed_confirmation_cannot_book_twice(world):
    world.send("check-up Monday 9", script=[ask_to_confirm()])
    out = world.send("yes", script=[check(), book(), book(), RespondRequest(message="ok")])
    effects = [r for r in world.results(out) if r["kind"] == "effect"]
    assert effects[0]["verified"] is True and effects[1]["note"] == "Already done; not repeated."
    assert sum(world.calendar.executions.values()) == 1


# --- FR53 / AD-3: effect arguments must be what the conversation established -------------

def test_effect_arguments_must_have_been_established(world):
    world.send("hi", script=[check(), book(), RespondRequest(message="ok")])
    assert ("business_refusal", "arguments_not_established") in world.denials()


def test_proposing_values_the_conversation_did_not_establish_is_refused(world):
    world.send("check-up Monday 9", script=[ClarifyRequest(message="?", facts=facts(DENTAL_FACTS))])
    later = {**DENTAL_FACTS, "preferred_time": "11:00"}
    out = world.send("ok", script=[ClarifyRequest(
        message="Shall I book 11?", confirm=ask_to_confirm(later).confirm), RespondRequest(message="ok")])
    assert ("business_refusal", "arguments_not_established") in world.denials()
    assert world.store.offers(TENANT, out.episode_id, "confirmation") == []


# --- EX6: rules are enforced by the Core, not by the prompt -------------------------------

@pytest.mark.parametrize("change,reason", [
    ({"visit_type": "whitening"}, "rule_denied"),
    ({"preferred_date": SUNDAY}, "rule_denied"),
])
def test_rules_deny_effects(world, change, reason):
    values = {**DENTAL_FACTS, **change}
    world.send("book", script=[ask_to_confirm(values), RespondRequest(message="ok")])
    assert ("business_refusal", reason) in world.denials()
    assert world.store.offers(TENANT, world.store.episodes(TENANT)[0].episode_id) == []


# --- AD-2, FR40: only granted capabilities, through the right kind ------------------------

def test_undeclared_capability_is_refused(world):
    world.send("refund me", script=[EffectRequest(capability="issue_refund"), RespondRequest(message="ok")])
    assert ("business_refusal", "not_granted") in world.denials()


def test_capability_through_the_wrong_kind_is_refused(world):
    world.send("x", script=[ReadRequest(capability="book_visit", arguments=args(DENTAL_FACTS)),
                            RespondRequest(message="ok")])
    assert ("business_refusal", "wrong_kind") in world.denials()


def test_reads_are_authorized_and_journaled(world):
    out = world.send("Any time Monday?", script=[
        ReadRequest(capability="check_availability", arguments=args({"visit_type": "checkup", "preferred_date": MONDAY})),
        RespondRequest(message="We have 9, 11, 2 and 4.")])
    steps = [s["kind"] for s in world.store.steps(TENANT, out.episode_id)]
    assert steps.count("decision") == 2 and steps.count("result") == 2
    assert any(e["kind"] == "read_result" for e in world.store.evidence(TENANT, out.episode_id))


# --- FR49, facts: declared goals and facts only; a bad request changes nothing ------------

def test_undeclared_goal_is_refused(world):
    world.send("x", script=[ClarifyRequest(goal="sell_insurance", message="?"), RespondRequest(message="ok")])
    assert ("business_refusal", "undeclared_goal") in world.denials()


def test_a_request_with_a_bad_fact_records_nothing(world):
    out = world.send("x", script=[
        ClarifyRequest(message="?", facts=(FactUpdate(name="patient_name", value="Ada"),
                                           FactUpdate(name="preferred_date", value="next monday"))),
        RespondRequest(message="ok")])
    assert ("business_refusal", "invalid_fact_value") in world.denials()
    assert world.store.facts(TENANT, out.episode_id) == {}


# --- EX12: what may never be asked ---------------------------------------------------------

def test_never_ask_is_refused(world):
    world.send("x", script=[ClarifyRequest(message="Any medical history?", asks_for=("medical_history",)),
                            RespondRequest(message="ok")])
    assert ("business_refusal", "never_ask") in world.denials()


# --- AD-7, FR32/33: provenance, refused before it reaches the person -----------------------

def cite(ref):
    return RespondRequest(message="A check-up costs 95 dollars.",
                          claims=(Claim(kind="business_fact", text="check-up 95 dollars", reference=ref),))


def fee_ref(view: AgentView) -> str:
    return next(r.ref for r in view.references if "95 dollars" in r.text)


def test_a_grounded_claim_passes(world):
    out = world.send("How much is a check-up?", script=[lambda v: cite(fee_ref(v))])
    assert out.messages and world.denials() == []


def test_a_minted_reference_is_refused(world):
    out = world.send("How much?", script=[cite("ref_madeup123"), RespondRequest(message="Let me check.")])
    assert ("business_refusal", "provenance_invalid") in world.denials()
    assert "95" not in out.messages[0].text


def test_a_reference_from_another_conversation_is_refused(world):
    stolen = {}
    world.send("fees?", conversation="a", script=[lambda v: (stolen.setdefault("ref", fee_ref(v)),
                                                             RespondRequest(message="hi"))[1]])
    world.send("fees?", conversation="b", script=[lambda v: cite(stolen["ref"]), RespondRequest(message="sorry")])
    assert ("business_refusal", "provenance_invalid") in world.denials()


def test_a_reference_from_another_business_is_rejected_not_filtered(runner, business_copy):
    other = business_copy("dental", replace=[('tenant = "bright-smile-dental"', 'tenant = "other-dental"')])
    w = build_world(runner, [DENTAL, other])
    stolen = {}
    w.send("fees?", tenant="other-dental", script=[lambda v: (stolen.setdefault("ref", fee_ref(v)),
                                                              RespondRequest(message="hi"))[1]])
    w.send("fees?", script=[lambda v: cite(stolen["ref"]), RespondRequest(message="sorry")])
    detail = [d["detail"] for d in w.store.denials(TENANT)]
    assert any("belongs to another business" in d for d in detail)


def test_general_knowledge_is_refused_when_disabled(world):
    world.send("what is a root canal", script=[
        RespondRequest(message="It removes the pulp.", claims=(Claim(kind="general_knowledge", text="pulp"),)),
        RespondRequest(message="I'll ask the team.")])
    assert ("business_refusal", "general_knowledge_disabled") in world.denials()


def test_a_forbidden_conclusion_is_refused_and_an_undeclared_one_is_a_spec_defect(world):
    world.send("do I need a root canal?", script=[
        RespondRequest(message="Yes, you need one.", claims=(Claim(kind="conclusion", text="needs it",
                                                                    conclusion="diagnose_condition"),)),
        RespondRequest(message="It is broken.", claims=(Claim(kind="conclusion", text="x", conclusion="assign_blame"),)),
        RespondRequest(message="The dentist will tell you at the consultation.")])
    assert ("business_refusal", "conclusion_forbidden") in world.denials()
    assert ("spec_defect", "conclusion_undeclared") in world.denials()


# --- FR71: no claim of an effect without a Core record -------------------------------------

def test_claiming_a_booking_that_never_happened_is_refused(world):
    out = world.send("book me", script=[booked_reply("ev_fabricated"), RespondRequest(message="Let me check.")])
    assert ("business_refusal", "action_without_evidence") in world.denials()
    assert "booked" not in out.messages[0].text


def test_claiming_an_unverified_effect_as_done_is_refused_even_without_a_resolution(runner):
    w = build_world(runner, [DENTAL])
    w.calendar.drop_writes = True
    w.send("check-up Monday 9", script=[ask_to_confirm()])
    out = w.send("yes", script=[check(), book(), lambda v: RespondRequest(
        message="You're booked.", claims=(Claim(kind="action_taken", text="booked", evidence=last_evidence(v)),)),
        RespondRequest(message="I couldn't confirm it yet.")])
    assert ("business_refusal", "action_without_evidence") in w.denials()
    assert "booked" not in out.messages[0].text


def test_a_served_resolution_with_obligations_outstanding_is_refused(world):
    world.send("info", script=[
        RespondRequest(message="Done.", resolution=ResolutionClaim(goal="book_visit", served=True, authority="agent")),
        RespondRequest(message="What name?")])
    assert ("business_refusal", "resolution_invalid") in world.denials()


# --- AD-21, FR44, FR111: guards before the Agent; a halt is never silence -------------------

def test_an_urgent_message_halts_before_the_agent_sees_it(world):
    out = world.send("My face is swollen and I can't swallow")
    assert world.agent.views == []
    assert out.halted == "guard" and out.lifecycle == "closed"
    assert out.messages[0].kind == "terminal_notice"
    assert "call 911" in out.messages[0].text and "automated assistant" in out.messages[0].text
    notices = [o for o in world.store.outbox(TENANT) if o["kind"] == "halt_notice"]
    assert notices and notices[0]["destination"] == "frontdesk@brightsmile.example"


def test_a_constraining_guard_reaches_the_agent_as_a_typed_constraint(world):
    out = world.send("I'm in severe pain", script=[
        EscalateRequest(reason_class="urgent_care", summary="severe pain", message="I've passed this to the team.")])
    assert any("severe pain" in c.lower() for c in world.agent.views[0].constraints)
    assert out.lifecycle == "closed"
    resolution = world.store.resolutions(TENANT, out.episode_id)[0]
    assert resolution["served"] == 1  # FR69: escalation as a declared success
    assert [o["kind"] for o in world.store.outbox(TENANT)] == ["escalation", "reply"]


# --- FR107, AD-18: bounded loop; stall and budget end in a declared halt --------------------

def test_budget_exhaustion_halts_with_notices(runner):
    w = build_world(runner, [DENTAL], settings=CoreSettings(max_requests_per_turn=3, stall_repeats=99))
    script = [RetrieveRequest(query=q) for q in ("hours", "fees", "booking")]
    out = w.send("hello", script=script)
    assert out.halted == "budget_exhausted" and out.messages[0].kind == "terminal_notice"
    assert any(o["kind"] == "halt_notice" for o in w.store.outbox(TENANT))


def test_repeating_the_same_request_is_a_stall(world):
    looping = EffectRequest(capability="issue_refund")
    out = world.send("refund", script=[looping, looping, looping])
    assert out.halted == "stall"


def test_an_agent_failure_is_a_typed_result_not_a_crash(world):
    class Boom:
        name = "boom"
        calls = 0

        async def decide(self, view):
            Boom.calls += 1
            raise RuntimeError("model unreachable")

    world.core.agent = Boom()
    out = world.send("hello")
    assert out.halted == "budget_exhausted"
    assert ("platform_error", "agent_failed") in world.denials()


# --- FR47, FR48: the Agent escalates; silence in the rules is a spec defect ----------------

def test_escalating_because_the_rules_are_silent_records_a_spec_defect(world):
    out = world.send("Can I bring my dog?", script=[
        EscalateRequest(reason_class="rules_silent", summary="dogs at the practice", message="I've asked the team.")])
    assert ("spec_defect", "rules_silent") in world.denials()
    assert world.store.outbox(TENANT)[0]["kind"] == "escalation"
    assert out.lifecycle == "closed"


def test_an_undeclared_escalation_reason_is_delivered_and_recorded_as_a_defect(world):
    world.send("x", script=[EscalateRequest(reason_class="parking", summary="parking", message="Passed on.")])
    assert ("spec_defect", "escalation_reason_undeclared") in world.denials()
    assert world.store.outbox(TENANT)[0]["kind"] == "escalation"


# --- FR60, FR62: pending and resumption --------------------------------------------------

def test_pending_resumes_on_the_next_inbound_message(world):
    out = world.send("I'll send my insurance card", script=[
        SuspendRequest(awaiting="insurance card", message="Thanks, I'll wait for it.")])
    episode = world.store.get_episode(TENANT, out.episode_id)
    assert episode.lifecycle == "pending" and episode.awaiting == "insurance card"
    again = world.send("here it is", script=[RespondRequest(message="Got it.")])
    assert again.episode_id == out.episode_id
    assert "resumed" in [s["kind"] for s in world.store.steps(TENANT, out.episode_id)]


def test_pending_must_name_what_it_waits_for(world):
    world.send("x", script=[SuspendRequest(awaiting=" ", message="wait"), RespondRequest(message="ok")])
    assert ("business_refusal", "awaiting_unnamed") in world.denials()


# --- FR60, FR61, FR63: a passed deadline resumes the episode as an external event ---------

DEADLINE = "2026-10-14T09:00:00"  # naive: read as UTC


@pytest.fixture
def clocked(runner):
    clock = {"now": datetime(2026, 10, 13, 9, 0, tzinfo=timezone.utc)}
    return build_world(runner, [DENTAL], store=EpisodeStore(clock=lambda: clock["now"])), clock


def wait_for_card(w, deadline=DEADLINE):
    return w.send("I'll send my insurance card later", script=[
        SuspendRequest(awaiting="insurance card", message="Thanks, I'll wait for it.", deadline=deadline)])


def expire(w):
    return w.runner.run(w.core.expire_due())


def kinds_after_resumed(w, episode_id):
    steps = w.store.steps(TENANT, episode_id)
    start = max(i for i, s in enumerate(steps) if s["kind"] == "resumed")
    return [(s["actor"], s["kind"]) for s in steps[start + 1:]]


def test_a_passed_deadline_resumes_the_episode(clocked):
    w, clock = clocked
    out = wait_for_card(w)
    clock["now"] += timedelta(days=2)
    w.agent.extend([RespondRequest(message="We still need your insurance card; could you send it?")])
    [(tenant, episode_id, outcome)] = expire(w)
    assert (tenant, episode_id) == (TENANT, out.episode_id)
    assert outcome.lifecycle == "active" and outcome.messages
    event = {"kind": "deadline_expired", "awaiting": "insurance card", "deadline": "2026-10-14T09:00:00+00:00"}
    steps = w.store.steps(TENANT, out.episode_id)
    assert [s["payload"] for s in steps if s["kind"] == "external_event"] == [event]
    assert "resumed" in [s["kind"] for s in steps]
    assert [e["payload"] for e in w.store.evidence(TENANT, out.episode_id) if e["kind"] == "external_event"] == [event]
    seen = w.agent.views[-1].conversation[-1]
    assert seen.role == "external" and "insurance card" in seen.text
    assert w.store.get_episode(TENANT, out.episode_id).lifecycle == "active"


def test_on_an_expiry_the_core_initiates_nothing(clocked):
    w, clock = clocked
    out = wait_for_card(w)
    clock["now"] += timedelta(days=2)
    w.agent.extend([RespondRequest(message="We still need your insurance card.")])
    expire(w)
    # The only steps after the resumption are the Agent's decision and what it produced.
    assert kinds_after_resumed(w, out.episode_id) == [("agent", "decision"), ("core", "egress"), ("core", "result")]
    assert not any(o["kind"] in ("escalation", "halt_notice") for o in w.store.outbox(TENANT))
    assert w.store.resolutions(TENANT, out.episode_id) == []


def test_a_deadline_not_yet_passed_records_nothing(clocked):
    w, clock = clocked
    out = wait_for_card(w)
    clock["now"] = datetime(2026, 10, 14, 8, 59, tzinfo=timezone.utc)
    before = w.store.steps(TENANT, out.episode_id)
    assert expire(w) == []
    assert w.runner.run(w.core.record_expiry(TENANT, out.episode_id)) == "not_due"
    assert w.store.steps(TENANT, out.episode_id) == before
    assert w.store.get_episode(TENANT, out.episode_id).lifecycle == "pending"


def test_a_deadline_is_compared_as_an_instant_not_as_text(clocked):
    w, clock = clocked
    out = wait_for_card(w, deadline="2026-10-14T12:00:00+05:00")  # 07:00 UTC
    clock["now"] = datetime(2026, 10, 14, 8, 0, tzinfo=timezone.utc)
    w.agent.extend([RespondRequest(message="Still waiting on the card.")])
    assert [r[1] for r in expire(w)] == [out.episode_id]


def test_a_pending_episode_without_a_deadline_never_expires(clocked):
    w, clock = clocked
    out = wait_for_card(w, deadline=None)
    clock["now"] += timedelta(days=365)
    assert expire(w) == []
    assert w.runner.run(w.core.record_expiry(TENANT, out.episode_id)) == "not_due"
    assert w.store.get_episode(TENANT, out.episode_id).lifecycle == "pending"


@pytest.mark.parametrize("then", [
    RespondRequest(message="We still need your insurance card."),
    EscalateRequest(reason_class="rules_silent", summary="card never came", message="I've passed this on."),
])
def test_the_same_expiry_delivered_twice_is_processed_once(clocked, then):
    w, clock = clocked
    out = wait_for_card(w)
    clock["now"] += timedelta(days=2)
    w.agent.extend([then])
    assert len(expire(w)) == 1
    assert expire(w) == []
    assert w.runner.run(w.core.record_expiry(TENANT, out.episode_id)) == "duplicate"
    steps = w.store.steps(TENANT, out.episode_id)
    assert [s["kind"] for s in steps].count("external_event") == 1
    assert w.store.late_results(TENANT, out.episode_id) == []


def test_an_expiry_for_a_closed_episode_is_late_and_changes_nothing(clocked):
    w, clock = clocked
    out = wait_for_card(w)
    w.send("Actually, please just pass me to someone", script=[
        EscalateRequest(reason_class="rules_silent", summary="wants a person", message="I've passed this on.")])
    clock["now"] += timedelta(days=2)
    before = w.store.resolutions(TENANT, out.episode_id)
    assert w.runner.run(w.core.record_expiry(TENANT, out.episode_id)) == "late"
    assert w.store.resolutions(TENANT, out.episode_id) == before
    episode = w.store.get_episode(TENANT, out.episode_id)
    assert episode.lifecycle == "closed" and episode.close_reason == "escalated"
    assert [r["payload"] for r in w.store.late_results(TENANT, out.episode_id)] == [
        {"kind": "deadline_expired", "awaiting": "insurance card", "deadline": "2026-10-14T09:00:00+00:00"}]
    assert w.runner.run(w.core.record_expiry(TENANT, out.episode_id)) == "duplicate"
    assert len(w.store.late_results(TENANT, out.episode_id)) == 1


def test_a_closed_episode_that_never_had_a_deadline_does_not_expire(world):
    first, second = book_happily(world)
    assert world.runner.run(world.core.record_expiry(TENANT, second.episode_id)) == "not_due"
    assert world.store.late_results(TENANT, second.episode_id) == []


@pytest.mark.parametrize("deadline", ["next week", "2026-10-20", "0001-01-01T00:00:00+01:00"])
def test_a_deadline_that_cannot_be_read_is_refused_at_suspend(world, deadline):
    out = world.send("x", script=[SuspendRequest(awaiting="photo", message="wait", deadline=deadline),
                                  RespondRequest(message="ok")])
    assert ("business_refusal", "invalid_deadline") in world.denials()
    assert world.store.get_episode(TENANT, out.episode_id).lifecycle == "active"


def test_a_deadline_already_passed_is_refused_at_suspend(clocked):
    w, clock = clocked
    out = w.send("I'll send my card", script=[
        SuspendRequest(awaiting="insurance card", message="I'll wait.", deadline="2026-10-13T08:00:00"),
        RespondRequest(message="ok")])
    assert ("business_refusal", "invalid_deadline") in w.denials()
    assert w.store.get_episode(TENANT, out.episode_id).lifecycle == "active"


def test_an_expiry_while_the_agent_is_stopped_records_nothing(clocked):
    w, clock = clocked
    out = wait_for_card(w)
    w.core.set_suspension(TENANT, agent=True, effects=True, by="owner")
    clock["now"] += timedelta(days=2)
    called = len(w.agent.views)
    assert expire(w) == [(TENANT, out.episode_id, "agent_suspended")]
    kinds = [s["kind"] for s in w.store.steps(TENANT, out.episode_id)]
    assert "external_event" not in kinds and "resumed" not in kinds
    assert w.store.get_episode(TENANT, out.episode_id).lifecycle == "pending"
    assert len(w.agent.views) == called


def test_a_second_wait_after_an_expiry_expires_again(clocked):
    w, clock = clocked
    out = wait_for_card(w)
    clock["now"] += timedelta(days=2)
    w.agent.extend([SuspendRequest(awaiting="insurance card", message="I'll wait a little longer.",
                                   deadline="2026-10-17T09:00:00+00:00")])
    assert expire(w)[0][2].lifecycle == "pending"
    clock["now"] += timedelta(days=3)
    w.agent.extend([RespondRequest(message="We still need your card.")])
    [(_, _, outcome)] = expire(w)
    assert outcome != "duplicate" and outcome.lifecycle == "active"
    events = [s["payload"]["deadline"] for s in w.store.steps(TENANT, out.episode_id) if s["kind"] == "external_event"]
    assert events == ["2026-10-14T09:00:00+00:00", "2026-10-17T09:00:00+00:00"]


def test_an_unreadable_legacy_deadline_does_not_stop_the_sweep(clocked):
    w, clock = clocked
    valid = wait_for_card(w)
    legacy = w.send("I'll send a photo", conversation="c2", script=[
        SuspendRequest(awaiting="photo", message="ok", deadline="2026-10-14T09:00:00")])
    w.store.set_lifecycle(TENANT, legacy.episode_id, "pending", awaiting="photo", deadline="next week")
    clock["now"] += timedelta(days=2)
    w.agent.extend([RespondRequest(message="We still need your card.")])
    assert [r[1] for r in expire(w)] == [valid.episode_id]
    assert w.runner.run(w.core.record_expiry(TENANT, legacy.episode_id)) == "unreadable_deadline"
    assert w.store.get_episode(TENANT, legacy.episode_id).lifecycle == "pending"


def test_the_deterministic_agent_hands_over_on_an_expiry(clocked):
    from studio.agent.deterministic import DeterministicAgent
    from studio.agent.llm_agent import render
    w, clock = clocked
    out = wait_for_card(w)
    clock["now"] += timedelta(days=2)
    seen = []

    class Watching(DeterministicAgent):
        async def decide(self, view):
            seen.append(view)
            return await super().decide(view)

    w.core.agent = Watching()
    [(_, _, outcome)] = expire(w)
    assert outcome.lifecycle == "closed"
    assert w.store.get_episode(TENANT, out.episode_id).close_reason == "escalated"
    assert any(o["kind"] == "escalation" for o in w.store.outbox(TENANT))
    assert kinds_after_resumed(w, out.episode_id)[0] == ("agent", "decision")
    assert "EXTERNAL: The deadline" in render(seen[0])[1]["content"]


# --- FR87: a re-sent message is processed once ---------------------------------------------

def test_a_resent_message_is_processed_once(world):
    world.send("hello", message_id="same", script=[RespondRequest(message="Hi!")])
    again = world.send("hello", message_id="same")
    assert again.duplicate and again.messages == []
    assert len(world.store.outbox(TENANT)) == 1


def test_concurrent_messages_on_one_conversation_are_serialised(world):
    world.agent.extend([RespondRequest(message="one"), RespondRequest(message="two")])

    async def both():
        from studio.core import InboundMessage
        return await asyncio.gather(*(world.core.handle(InboundMessage(
            tenant=TENANT, conversation_key="c1", message_id=f"x{i}", text="hi")) for i in range(2)))

    a, b = world.runner.run(both())
    assert a.episode_id == b.episode_id
    assert len(world.store.episodes(TENANT)) == 1


# --- FR110: suspension ------------------------------------------------------------------------

def test_stopping_actions_refuses_effects_but_keeps_replying(world):
    world.send("check-up Monday 9", script=[ask_to_confirm()])
    world.core.set_suspension(TENANT, agent=False, effects=True, by="owner")
    out = world.send("yes", script=[check(), book(), RespondRequest(message="I can't book right now.")])
    assert ("business_refusal", "effects_suspended") in world.denials()
    assert out.messages and sum(world.calendar.executions.values()) == 0


def test_suspending_the_agent_stops_replies_and_records_the_outcome(world):
    world.core.set_suspension(TENANT, agent=True, effects=True, by="owner")
    out = world.send("hello")
    assert out.messages == [] and out.lifecycle == "closed"
    assert world.store.get_episode(TENANT, out.episode_id).close_reason == "suspended"
    assert world.agent.views == []


# --- AD-6, FR51: success is a read-back, never the adapter's say-so ------------------------

@pytest.mark.parametrize("fault", ["drop_writes", "fail_read_backs"])
def test_an_effect_that_cannot_be_read_back_is_unverified_and_cannot_be_claimed(runner, fault):
    w = build_world(runner, [DENTAL])
    setattr(w.calendar, fault, True)
    w.send("check-up Monday 9", script=[ask_to_confirm()])
    out = w.send("yes", script=[check(), book(), lambda v: booked_reply(last_evidence(v)),
                                EscalateRequest(reason_class="billing", summary="booking not confirmed",
                                                message="I couldn't confirm it; the team will.")])
    kinds = [e["kind"] for e in w.store.evidence(TENANT, out.episode_id)]
    assert "effect_unverified" in kinds and "effect_verified" not in kinds
    assert ("business_refusal", "action_without_evidence") in w.denials()
    assert "booked" not in out.messages[0].text


def test_a_hung_write_times_out_and_is_not_reported_as_done(runner):
    w = build_world(runner, [DENTAL], settings=CoreSettings(adapter_timeout_s=0.2))
    w.calendar.hang_writes_s = 0.5
    w.calendar.fail_read_backs = True
    w.send("check-up Monday 9", script=[ask_to_confirm()])
    out = w.send("yes", script=[check(), book(), RespondRequest(message="I couldn't confirm the booking.")])
    assert ("platform_error", "adapter_timeout") in w.denials()
    assert any(e["kind"] == "effect_unverified" for e in w.store.evidence(TENANT, out.episode_id))


def test_a_rejected_write_is_a_platform_error_not_a_decision(runner):
    w = build_world(runner, [DENTAL])
    w.calendar.fail_writes = True
    w.send("check-up Monday 9", script=[ask_to_confirm()])
    w.send("yes", script=[check(), book(), RespondRequest(message="Something went wrong on our side.")])
    assert ("platform_error", "adapter_failed") in w.denials()


# --- AD-10, FR55: idempotency keys are the Core's, scoped by tenant and episode ------------

def test_the_same_booking_in_two_episodes_is_two_keys(world):
    book_happily(world, conversation="a")
    world.calendar.open_times[MONDAY] = ("09:00",)
    world.calendar.bookings.clear()
    book_happily(world, conversation="b")
    keys = {k for k in world.calendar.executions}
    assert len(keys) == 2


# --- AD-11, FR27, FR64: pinned versions; survival across a restart -------------------------

def test_an_episode_keeps_the_version_it_started_on(world, business_copy):
    out = world.send("x", script=[SuspendRequest(awaiting="photo", message="ok")])
    newer = business_copy("dental", replace=[("refusal_sample_rate = 0.2", "refusal_sample_rate = 0.5")])
    from studio.spec import compile_specification, load_specification
    world.core.registry.register(compile_specification(load_specification(newer)))
    again = world.send("here", script=[RespondRequest(message="thanks")])
    original = world.store.get_episode(TENANT, out.episode_id)
    assert again.episode_id == out.episode_id
    assert original.spec_version != world.core.registry.live(TENANT).spec_version


def test_a_pending_episode_survives_a_new_process(runner, tmp_path):
    path = tmp_path / "episodes.db"
    first = build_world(runner, [DENTAL], store=EpisodeStore(path))
    out = first.send("x", script=[SuspendRequest(awaiting="photo", message="ok")])
    first.store.close()
    second = build_world(runner, [DENTAL], store=EpisodeStore(path))
    again = second.send("photo attached", script=[RespondRequest(message="thanks")])
    assert again.episode_id == out.episode_id


# --- FR63, FR75, FR106: late results, purge, waivers ---------------------------------------

def test_a_result_after_close_is_late_and_changes_nothing(world):
    first, second = book_happily(world)
    before = world.store.resolutions(TENANT, second.episode_id)
    assert world.core.record_external_result(TENANT, second.episode_id, {"status": "cancelled"}) == "late"
    assert world.store.resolutions(TENANT, second.episode_id) == before
    assert world.store.late_results(TENANT, second.episode_id)


def test_evidence_is_removable_by_episode_and_by_age(runner):
    clock = {"now": datetime(2026, 1, 1, tzinfo=timezone.utc)}
    w = build_world(runner, [DENTAL], store=EpisodeStore(clock=lambda: clock["now"]))
    old = w.send("x", conversation="old", script=[RespondRequest(message="hi")])
    clock["now"] += timedelta(days=400)
    new = w.send("x", conversation="new", script=[RespondRequest(message="hi")])
    assert w.store.purge(TENANT, older_than_days=365) == 1
    assert w.store.get_episode(TENANT, old.episode_id) is None
    assert w.store.steps(TENANT, old.episode_id) == []
    assert w.store.get_episode(TENANT, new.episode_id) is not None
    assert w.store.purge(TENANT, episode_id=new.episode_id) == 1


def test_only_a_declared_waiver_is_accepted(world):
    out = world.send("x", script=[SuspendRequest(awaiting="x", message="ok")])
    with pytest.raises(PermissionError):
        world.core.waive(TENANT, out.episode_id, "book_visit", "contact_email", by="owner")


# --- FR50: multiple goals, one active, explicit parking -------------------------------------

def test_switching_goals_parks_the_previous_one(world):
    out = world.send("book, but first what does a root canal involve?", script=[
        ClarifyRequest(goal="book_visit", message="Name?"),
    ])
    world.send("Ada. Also what is a root canal consult?", script=[
        ClarifyRequest(goal="explain_treatment", message="It's an exam and X-ray. Shall we continue booking?")])
    goals = world.store.goals(TENANT, out.episode_id)
    assert goals == {"book_visit": "parked", "explain_treatment": "active"}


# --- FR41, AD-16: the Agent sees a view, nothing it could act through ---------------------

def test_the_agent_view_carries_no_channel_store_or_adapter():
    fields = set(AgentView.model_fields)
    assert not fields & {"store", "adapters", "channel", "core", "conversation_key"}


def test_every_denial_reason_has_exactly_one_classification():
    assert set(typing.get_args(Reason)) == set(REASON_CLASS)
    assert set(REASON_CLASS.values()) <= {"spec_defect", "business_refusal", "platform_error"}


def test_every_request_and_result_is_journaled(world):
    out = world.send("x", script=[EffectRequest(capability="issue_refund"), RespondRequest(message="ok")])
    kinds = [s["kind"] for s in world.store.steps(TENANT, out.episode_id)]
    assert kinds.count("decision") == 2 and kinds.count("result") == 2 and kinds.count("egress") == 1


# --- FR109: authority established, never assumed from the channel -------------------------

def test_identity_based_authority_is_refused_until_identity_is_verified(runner, business_copy):
    spec = business_copy("dental", replace=[('authority_basis = "requester_self"', 'authority_basis = "verified_identity"')])
    w = build_world(runner, [spec])
    w.send("check-up Monday 9", script=[ask_to_confirm()])
    w.send("yes", script=[check(), book(), RespondRequest(message="I need to verify who you are first.")])
    assert ("business_refusal", "authority_not_established") in w.denials()
    assert sum(w.calendar.executions.values()) == 0


# --- Story 1.11: an effect a crash left 'started' --------------------------------------------

def test_an_effect_left_started_by_a_crash_is_settled_by_read_back_not_repeated(world):
    """A process stopped after the adapter wrote but before the outcome was recorded. The next turn settles the
    effect by read-back before the Agent decides anything; it is never executed again."""
    first = world.send("Hi, I'd like a check-up on Monday at 9. Ada Lovelace, ada@example.com",
                       script=[ask_to_confirm()])
    eid, key = first.episode_id, "k-interrupted"
    world.calendar.effect(TENANT, "book", DENTAL_FACTS, key)          # the system of record holds it
    world.store.start_effect(TENANT, eid, key, "book_visit", DENTAL_FACTS)  # its outcome was never recorded
    world.send("hello?", script=[RespondRequest(message="One moment, please.")])
    assert world.store.get_effect(TENANT, eid, key)["state"] == "verified"
    assert world.store.started_effects(TENANT, eid) == []
    assert world.calendar.executions[(TENANT, key)] == 1
    assert any(s["kind"] == "effect_reconciled" for s in world.store.steps(TENANT, eid))
    assert [e["kind"] for e in world.store.evidence(TENANT, eid)].count("effect_verified") == 1
    seen = world.agent.views[-1].turn_results  # the Agent sees the settled outcome before it decides
    assert seen and seen[0][1].kind == "effect" and seen[0][1].verified is True


def test_an_interrupted_effect_the_system_never_received_is_unverified_not_success(world):
    first = world.send("Hi, I'd like a check-up on Monday at 9. Ada Lovelace, ada@example.com",
                       script=[ask_to_confirm()])
    eid, key = first.episode_id, "k-never-sent"
    world.store.start_effect(TENANT, eid, key, "book_visit", DENTAL_FACTS)
    world.send("hello?", script=[RespondRequest(message="One moment, please.")])
    assert world.store.get_effect(TENANT, eid, key)["state"] == "unverified"
    assert sum(world.calendar.executions.values()) == 0


def test_an_interrupted_effect_with_an_unreachable_read_back_is_unverified_and_says_why(world):
    first = world.send("Hi, I'd like a check-up on Monday at 9. Ada Lovelace, ada@example.com",
                       script=[ask_to_confirm()])
    eid, key = first.episode_id, "k-unreachable"
    world.store.start_effect(TENANT, eid, key, "book_visit", DENTAL_FACTS)
    world.calendar.fail_read_backs = True
    world.send("hello?", script=[RespondRequest(message="One moment, please.")])
    assert world.store.get_effect(TENANT, eid, key)["state"] == "unverified"
    assert world.store.started_effects(TENANT, eid) == []
    unverified = [e for e in world.store.evidence(TENANT, eid) if e["kind"] == "effect_unverified"]
    assert len(unverified) == 1 and "unreachable" in unverified[0]["payload"]["adapter_problem"]
    seen = world.agent.views[-1].turn_results[0][1]
    assert seen.status == "failed" and seen.verified is False
    assert sum(world.calendar.executions.values()) == 0


def test_an_interrupted_effect_is_settled_even_when_the_turn_ends_without_the_agent(world):
    first = world.send("Hi, I'd like a check-up on Monday at 9. Ada Lovelace, ada@example.com",
                       script=[ask_to_confirm()])
    eid, key = first.episode_id, "k-suspended"
    world.calendar.effect(TENANT, "book", DENTAL_FACTS, key)
    world.store.start_effect(TENANT, eid, key, "book_visit", DENTAL_FACTS)
    world.core.set_suspension(TENANT, agent=True, effects=True, by="operator")
    world.send("hello?")
    assert world.store.get_episode(TENANT, eid).close_reason == "suspended"
    assert world.store.started_effects(TENANT, eid) == []
    assert world.store.get_effect(TENANT, eid, key)["state"] == "verified"
