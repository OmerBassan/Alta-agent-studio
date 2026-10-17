"""The second business on the same Core: the Brief's brewery-events exemplar.

It exercises what dental does not — a liability-bearing capability gated by
operator approval (FR16), integer rules, an operator waiver (FR106) — with zero
changes to the Core."""

import asyncio

import pytest

from studio.core.types import (ClarifyRequest, ConfirmProposal, EffectRequest, EscalateRequest, ReadRequest,
                               RespondRequest)
from studio.tests.helpers import BUSINESSES, MONDAY, args, build_world, facts

BREWERY = BUSINESSES / "brewery" / "specification.toml"
TENANT = "hopfield-brewery"
EVENT = {"contact_name": "Grace Hopper", "contact_email": "grace@example.com", "event_date": MONDAY,
         "start_time": "18:00", "party_size": 40}
FEE = {"contact_name": "Grace Hopper", "event_date": MONDAY}


@pytest.fixture
def world():
    with asyncio.Runner() as runner:
        w = build_world(runner, [BREWERY])
        w.calendar.tenant_times[TENANT] = ("12:00", "15:00", "18:00")
        yield w


def send(world, text, script, conversation="c1"):
    return world.send(text, tenant=TENANT, conversation=conversation, script=script)


def denials(world):
    return world.denials(TENANT)


def hold(values=EVENT):
    return EffectRequest(goal="plan_event", capability="place_event_hold", arguments=args(values))


def confirm_hold(values=EVENT):
    return ClarifyRequest(goal="plan_event", facts=facts(values), message="Shall I hold Monday at 6pm for 40? (yes/no)",
                          confirm=ConfirmProposal(capability="place_event_hold", arguments=args(values)))


def test_a_hold_is_placed_after_consent_and_read_back(world):
    send(world, "Can I host 40 people Monday evening?", [
        ReadRequest(goal="plan_event", capability="check_event_availability", arguments=args({"event_date": MONDAY})),
        confirm_hold()])
    out = send(world, "yes please", [hold(), RespondRequest(message="Held for 7 days.")])
    assert any(e["kind"] == "effect_verified" for e in world.store.evidence(TENANT, out.episode_id))


def test_integer_rules_bind_party_size(world):
    send(world, "80 people", [confirm_hold({**EVENT, "party_size": 80}), RespondRequest(message="Too many.")])
    assert ("business_refusal", "rule_denied") in denials(world)


def test_a_liability_capability_waits_for_the_operator(world):
    out = send(world, "Can you waive the fee?", [
        EffectRequest(goal="plan_event", capability="waive_hire_fee", arguments=args(FEE), facts=facts(FEE)),
        RespondRequest(message="I've asked the team.")])
    assert ("business_refusal", "operator_approval_required") in denials(world)
    pending = world.store.offers(TENANT, out.episode_id, "operator_approval")
    assert [o["state"] for o in pending] == ["offered"]
    assert sum(world.calendar.executions.values()) == 0

    world.core.decide_approval(TENANT, pending[0]["offer_id"], approve=True, by="owner@hopfield")
    again = send(world, "any news?", [
        EffectRequest(goal="plan_event", capability="waive_hire_fee", arguments=args(FEE)),
        RespondRequest(message="The team agreed.")])
    assert any(e["kind"] == "effect_verified" for e in world.store.evidence(TENANT, again.episode_id))
    assert any(e["kind"] == "approval_granted" and e["payload"]["by"] == "owner@hopfield"
               for e in world.store.evidence(TENANT, again.episode_id))


def test_an_approval_is_bound_to_its_payload(world):
    send(world, "waive it", [
        EffectRequest(goal="plan_event", capability="waive_hire_fee", arguments=args(FEE), facts=facts(FEE)),
        RespondRequest(message="asked")])
    offer = world.store.offers(TENANT, world.store.episodes(TENANT)[0].episode_id, "operator_approval")[0]
    world.core.decide_approval(TENANT, offer["offer_id"], approve=True, by="owner")
    other = {**FEE, "event_date": "2026-10-20"}
    send(world, "actually the 20th", [
        EffectRequest(goal="plan_event", capability="waive_hire_fee", arguments=args(other), facts=facts(other)),
        RespondRequest(message="asked again")])
    assert sum(world.calendar.executions.values()) == 0
    assert denials(world).count(("business_refusal", "operator_approval_required")) == 2


def test_a_declined_approval_is_a_business_refusal(world):
    out = send(world, "waive it", [
        EffectRequest(goal="plan_event", capability="waive_hire_fee", arguments=args(FEE), facts=facts(FEE)),
        RespondRequest(message="asked")])
    offer = world.store.offers(TENANT, out.episode_id, "operator_approval")[0]
    world.core.decide_approval(TENANT, offer["offer_id"], approve=False, by="owner")
    send(world, "?", [EffectRequest(goal="plan_event", capability="waive_hire_fee", arguments=args(FEE)),
                      EscalateRequest(reason_class="money", summary="fee waiver declined", message="The team said no.")])
    assert ("business_refusal", "operator_denied") in denials(world)


def test_an_approval_cannot_be_decided_by_another_business(world):
    out = send(world, "waive it", [
        EffectRequest(goal="plan_event", capability="waive_hire_fee", arguments=args(FEE), facts=facts(FEE)),
        RespondRequest(message="asked")])
    offer = world.store.offers(TENANT, out.episode_id, "operator_approval")[0]
    with pytest.raises(LookupError):
        world.core.decide_approval("bright-smile-dental", offer["offer_id"], approve=True, by="intruder")


def test_a_declared_waiver_satisfies_an_obligation(world):
    partial = {k: v for k, v in EVENT.items() if k != "start_time"}
    out = send(world, "we don't know the time yet", [
        ClarifyRequest(goal="plan_event", facts=facts(partial), message="No problem.")])
    world.core.waive(TENANT, out.episode_id, "plan_event", "start_time", by="owner")
    obligations = world.agent.views[-1].obligations  # the view before the waiver
    assert "start_time" in next(o for o in obligations if o.goal == "plan_event").outstanding
    send(world, "thanks", [RespondRequest(message="ok")])
    after = next(o for o in world.agent.views[-1].obligations if o.goal == "plan_event")
    assert after.waived == ("start_time",) and "start_time" not in after.outstanding


def test_general_knowledge_is_allowed_here_and_marked_in_the_record(world):
    from studio.core.types import Claim
    out = send(world, "what is a lager?", [RespondRequest(
        message="A lager is a bottom-fermented beer.",
        claims=(Claim(kind="general_knowledge", text="lager is bottom-fermented"),))])
    assert denials(world) == []
    record = next(e for e in world.store.evidence(TENANT, out.episode_id) if e["kind"] == "reply_claims")
    assert record["payload"]["general_knowledge_used"] is True
