"""Epic 2: grounded answers from the business's own material.

Story 2.1 — an episode stays grounded in the material in force when it started,
even after the material is edited and the process restarts.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

from studio.core import Core, EpisodeStore, InboundMessage, SpecRegistry
from studio.core.ports import AgentDecision
from studio.core.types import RespondRequest
from studio.extensions.simulated import SimulatedCalendar
from studio.spec import compile_specification, load_specification

TENANT = "bright-smile-dental"
OLD, NEW = "costs 95 dollars", "costs 140 dollars"


class Capture:
    """Records every view and answers plainly."""

    name = "capture"

    def __init__(self):
        self.views = []

    async def decide(self, view):
        self.views.append(view)
        return AgentDecision(request=RespondRequest(message="Thanks, one moment."))


def _process(spec: Path, db: Path) -> tuple[Core, Capture, EpisodeStore]:
    """A fresh process: the registry is compiled from the files as they are now, nothing carried in memory."""
    registry = SpecRegistry()
    registry.register(compile_specification(load_specification(spec)))
    store = EpisodeStore(db, clock=lambda: datetime(2026, 10, 13, 9, 0, tzinfo=timezone.utc))
    agent = Capture()
    return Core(registry, store, agent, {"calendar": SimulatedCalendar()}), agent, store


def _send(core: Core, text: str, message_id: str):
    return asyncio.run(core.handle(InboundMessage(tenant=TENANT, conversation_key="k1", message_id=message_id,
                                                  text=text)))


def _guide(spec: Path) -> Path:
    return spec.parent / "knowledge" / "practice-guide.md"


def _start_then_edit_and_restart(business_copy, tmp_path):
    spec = business_copy("dental")
    db = tmp_path / "episodes.db"
    core, _, store = _process(spec, db)
    first = _send(core, "Hello, I have a question about prices.", "m1")
    pinned_version = store.get_episode(TENANT, first.episode_id).spec_version
    store.close()
    guide = _guide(spec)
    guide.write_text(guide.read_text(encoding="utf-8").replace(OLD, NEW), encoding="utf-8")
    core, agent, store = _process(spec, db)
    assert core.registry.live(TENANT).spec_version != pinned_version, "the edit must create a new version"
    return core, agent, store, first.episode_id, pinned_version


def test_an_episode_resumed_after_an_edit_and_a_restart_is_served_the_pinned_text(business_copy, tmp_path):
    core, agent, store, eid, pinned = _start_then_edit_and_restart(business_copy, tmp_path)
    out = _send(core, "So how much is a check-up?", "m2")
    assert out.episode_id == eid and store.get_episode(TENANT, eid).spec_version == pinned
    texts = " ".join(r.text for r in agent.views[-1].references)
    assert OLD in texts and NEW not in texts
    entry = core.registry.entry(TENANT, pinned)
    for row in store.references(TENANT, eid):  # every reference issued to the episode still resolves
        assert row["item_id"] in entry.items
    store.close()


def test_a_new_episode_after_the_edit_is_served_the_new_text(business_copy, tmp_path):
    core, agent, store, _, _ = _start_then_edit_and_restart(business_copy, tmp_path)
    asyncio.run(core.handle(InboundMessage(tenant=TENANT, conversation_key="k2", message_id="n1",
                                           text="How much is a check-up?")))
    texts = " ".join(r.text for r in agent.views[-1].references)
    assert NEW in texts and OLD not in texts
    store.close()


def test_source_content_is_stored_once_under_its_hash_and_never_rewritten(business_copy, tmp_path):
    spec = business_copy("dental")
    core, _, store = _process(spec, tmp_path / "episodes.db")
    _send(core, "Hello", "m1")
    asyncio.run(core.handle(InboundMessage(tenant=TENANT, conversation_key="k2", message_id="m2", text="Hello")))
    compiled = core.registry.live(TENANT)
    hashes = {i.source_version for i in compiled.context.items if i.origin == "source"}
    rows = store._all("SELECT content_hash, stored_at FROM source_snapshots")
    assert {r["content_hash"] for r in rows} == hashes and len(rows) == len(hashes)
    before = {r["content_hash"]: r["stored_at"] for r in rows}
    store.put_source_snapshot(next(iter(hashes)), "practice_guide", [{"locator": "x", "title": "x", "text": "REWRITTEN"}])
    after = {r["content_hash"]: r["stored_at"] for r in store._all("SELECT content_hash, stored_at "
                                                                     "FROM source_snapshots")}
    assert after == before
    assert "REWRITTEN" not in str(store.source_snapshot(next(iter(hashes))))
    store.close()


def test_every_reference_names_tenant_source_version_and_locator(business_copy, tmp_path):
    spec = business_copy("dental")
    core, _, store = _process(spec, tmp_path / "episodes.db")
    out = _send(core, "Hello", "m1")
    refs = store.references(TENANT, out.episode_id)
    assert refs
    for row in refs:
        assert row["tenant"] == TENANT and row["source_id"] and row["source_version"] and row["locator"]
    store.close()


# --- Story 2.2: reconstruct every answer from the record alone -------------------------------

def _run_d4_and_d1(spec: Path, db: Path) -> tuple[str, str]:
    """A grounded fee answer (retrieve, then a cited reply) and a clarifying reply that cites nothing."""
    from datetime import date
    from studio.agent.deterministic import DeterministicAgent
    registry = SpecRegistry()
    registry.register(compile_specification(load_specification(spec)))
    store = EpisodeStore(db, clock=lambda: datetime(2026, 10, 13, 9, 0, tzinfo=timezone.utc))
    core = Core(registry, store, DeterministicAgent(today=lambda: date(2026, 10, 13)),
                {"calendar": SimulatedCalendar()})
    fee = asyncio.run(core.handle(InboundMessage(tenant=TENANT, conversation_key="fee", message_id="f1",
                                                 text="How much does a check-up cost?")))
    ask = asyncio.run(core.handle(InboundMessage(tenant=TENANT, conversation_key="ask", message_id="a1",
                                                 text="I'd like to book a check-up")))
    store.close()
    return fee.episode_id, ask.episode_id


def test_a_closed_episode_is_reconstructed_from_the_store_even_after_the_material_is_deleted(
        business_copy, tmp_path):
    import shutil
    from studio.core.reconstruct import reconstruct
    spec = business_copy("dental")
    db = tmp_path / "episodes.db"
    fee, _ = _run_d4_and_d1(spec, db)
    store = EpisodeStore(db)
    before = reconstruct(store, TENANT, fee)
    store.close()
    shutil.rmtree(spec.parent)  # the business's folder, knowledge included, is gone
    store = EpisodeStore(db)
    after = reconstruct(store, TENANT, fee)
    store.close()
    assert after == before
    retrieval = next(r for r in after if r["kind"] == "retrieval")
    assert retrieval["query"] and retrieval["results"]
    reply = next(r for r in after if r["kind"] == "reply" and r["claims"])
    assert retrieval["seq"] < reply["seq"], "the retrieval precedes the reply that relied on it"
    item = reply["claims"][0]["item"]
    assert OLD in item["text"] and item["source_id"] == "practice_guide"
    assert item["source_version"] and item["locator"] and "unresolved" not in item


def test_a_reply_that_cites_nothing_is_shown_as_citing_nothing(business_copy, tmp_path):
    from studio.core.reconstruct import reconstruct
    _, ask = _run_d4_and_d1(business_copy("dental"), tmp_path / "episodes.db")
    store = EpisodeStore(tmp_path / "episodes.db")
    replies = [r for r in reconstruct(store, TENANT, ask) if r["kind"] == "reply"]
    store.close()
    assert replies and all(r["cites_nothing"] and r["claims"] == [] for r in replies)


def test_a_core_notice_never_inherits_the_previous_replys_claims_and_bad_references_say_why(tmp_path):
    from studio.core.reconstruct import reconstruct
    store = EpisodeStore(tmp_path / "e.db")
    ep = store.create_episode(TENANT, "k", "v1", "1")
    store.put_spec_snapshot(TENANT, "v1", '{"context": {"items": []}}')
    d = store.append_step(TENANT, ep.episode_id, "agent", "decision", {"request": {"kind": "respond"}})
    store.add_evidence(TENANT, ep.episode_id, "reply_claims", {"claims": [
        {"kind": "business_fact", "text": "a", "reference": None},
        {"kind": "business_fact", "text": "b", "reference": "ref_nope"}]}, d)
    store.append_step(TENANT, ep.episode_id, "core", "egress", {"kind": "reply", "text": "answer"})
    store.append_step(TENANT, ep.episode_id, "core", "egress", {"kind": "terminal_notice", "text": "closed"})
    reply, notice = reconstruct(store, TENANT, ep.episode_id)
    assert [c["item"]["unresolved"] for c in reply["claims"]] == [
        "the claim carried no reference", "the reference was never issued"]
    assert notice["egress"] == "terminal_notice" and notice["cites_nothing"]
    store.close()


# --- Story 2.3: context assembly by setting; retrieval behind a port --------------------------

def _world(mode: str, retriever=None):
    from studio.core import CoreSettings
    from studio.tests.helpers import BUSINESSES, build_world
    runner = asyncio.Runner()
    w = build_world(runner, [BUSINESSES / "dental" / "specification.toml"],
                    settings=CoreSettings(adapter_timeout_s=1.0, context_assembly=mode))
    if retriever is not None:
        w.core.retriever = retriever
    return w, runner


def test_context_assembly_is_platform_configuration_validated_at_startup():
    import pytest
    from studio.config import ConfigurationError, Settings
    from studio.core import CoreSettings
    assert Settings.from_env({}).context_assembly == "standing"
    assert Settings.from_env({"STUDIO_CONTEXT_ASSEMBLY": "on_demand"}).context_assembly == "on_demand"
    with pytest.raises(ConfigurationError):
        Settings.from_env({"STUDIO_CONTEXT_ASSEMBLY": "lazy"})
    with pytest.raises(ValueError):
        Core(SpecRegistry(), EpisodeStore(), Capture(), {}, CoreSettings(context_assembly="lazy"))


def test_on_demand_starts_with_the_specification_only_and_retrieval_issues_what_it_returns():
    from studio.core.types import RetrieveRequest
    w, runner = _world("on_demand")
    out = w.send("How much is a check-up?", script=[RetrieveRequest(query="check-up cost"),
                                                     RespondRequest(message="One moment.")])
    first, second = w.agent.views[0], w.agent.views[1]
    # Nothing of the source material crosses the boundary before it is retrieved, only its titles.
    assert first.references and all(not r.item_id.startswith("src:") for r in first.references)
    assert all(i.origin == "specification" for i in first.context.items)
    assert OLD not in repr(first) and "Services and fees" in first.material_index
    retrieved = [r for r in second.references if r.item_id.startswith("src:")]
    assert retrieved and OLD in " ".join(r.text for r in retrieved)
    assert {r.item_id for r in retrieved} <= {i.item_id for i in second.context.items}
    evidence = next(e for e in w.store.evidence(TENANT, out.episode_id) if e["kind"] == "retrieval")
    for item in evidence["payload"]["items"]:
        assert item["reference"] and item["source_id"] and item["source_version"] and item["locator"]
    runner.close()


def test_retrieving_the_same_item_again_reuses_its_reference():
    from studio.core.types import RetrieveRequest
    w, runner = _world("on_demand")
    out = w.send("How much is a check-up?", script=[RetrieveRequest(query="check-up cost"),
                                                     RetrieveRequest(query="check-up cost again"),
                                                     RespondRequest(message="One moment.")])
    refs = [r["item_id"] for r in w.store.references(TENANT, out.episode_id)]
    assert len(refs) == len(set(refs))
    runner.close()


def test_the_mode_is_pinned_at_episode_start():
    from studio.core import CoreSettings
    from studio.core.types import RetrieveRequest
    w, runner = _world("on_demand")
    w.send("Hello", script=[RespondRequest(message="Hello.")])
    w.core.settings = CoreSettings(adapter_timeout_s=1.0, context_assembly="standing")  # a restart, reconfigured
    out = w.send("How much is a check-up?", script=[RetrieveRequest(query="check-up cost"),
                                                     RespondRequest(message="One moment.")])
    result = next(s["payload"] for s in w.store.steps(TENANT, out.episode_id)
                  if s["kind"] == "result" and s["payload"]["kind"] == "retrieve")
    assert result["items"] and OLD in result["items"][0]["text"]
    assert w.agent.views[0].material_index  # still on demand for this episode
    runner.close()


def test_standing_issues_every_item_at_start():
    w, runner = _world("standing")
    w.send("Hello", script=[RespondRequest(message="Hello.")])
    assert any(r.item_id.startswith("src:") for r in w.agent.views[0].references)
    assert w.agent.views[0].material_index == ()
    runner.close()


def test_on_demand_a_claim_may_cite_only_what_this_episode_retrieved():
    from studio.core.types import Claim, RetrieveRequest
    w, runner = _world("on_demand")
    other = w.send("Prices?", conversation="other", script=[RetrieveRequest(query="check-up cost"),
                                                            RespondRequest(message="One moment.")])
    foreign = next(r["ref"] for r in w.store.references(TENANT, other.episode_id) if r["item_id"].startswith("src:"))

    def cite_retrieved(view):
        ref = next(r.ref for r in view.references if r.item_id.startswith("src:"))
        return RespondRequest(message="A check-up costs 95 dollars.",
                              claims=(Claim(kind="business_fact", text="95 dollars", reference=ref),))

    out = w.send("How much is a check-up?", script=[
        RespondRequest(message="It costs 95 dollars.",
                       claims=(Claim(kind="business_fact", text="95 dollars", reference=foreign),)),
        RetrieveRequest(query="check-up cost"), cite_retrieved])
    sent = [s["payload"]["text"] for s in w.store.steps(TENANT, out.episode_id) if s["kind"] == "egress"]
    assert len([t for t in sent if "95 dollars" in t]) == 1  # the unretrieved citation never left; the retrieved one did
    assert w.store.denials(TENANT, out.episode_id)
    runner.close()


def test_the_retriever_is_a_port_another_implementation_can_replace():
    from studio.core import CoreSettings
    from studio.core.types import RetrieveRequest

    class FirstSourceOnly:
        def search(self, query, items, limit):
            return [i for i in items if i.origin == "source"][:1]

    w, runner = _world("on_demand")
    w.core = Core(w.core.registry, w.store, w.agent, {"calendar": w.calendar},
                  CoreSettings(adapter_timeout_s=1.0, context_assembly="on_demand"), retriever=FirstSourceOnly())
    out = w.send("anything at all", script=[RetrieveRequest(query="zzz"), RespondRequest(message="ok")])
    result = next(s["payload"] for s in w.store.steps(TENANT, out.episode_id)
                  if s["kind"] == "result" and s["payload"]["kind"] == "retrieve")
    assert len(result["items"]) == 1
    runner.close()


def test_the_scenarios_pass_credential_free_in_both_modes():
    import os
    import subprocess
    import sys
    root = Path(__file__).resolve().parents[2]
    for mode in ("standing", "on_demand"):
        env = {k: v for k, v in os.environ.items() if k not in ("OPENAI_API_KEY", "OPENAI_BASE_URL")}
        env["STUDIO_CONTEXT_ASSEMBLY"] = mode
        done = subprocess.run([sys.executable, "-m", "studio", "scenarios", "--today", "2026-10-13"], cwd=root,
                              env=env, capture_output=True, text=True, timeout=600)
        assert done.returncode == 0, f"{mode}:\n{done.stdout[-1500:]}{done.stderr[-500:]}"
        lines = [line for line in done.stdout.splitlines() if line.startswith(("PASS", "FAIL"))]
        assert len(lines) >= 10 and all(line.startswith("PASS") for line in lines), f"{mode}: {lines}"


# --- Story 2.4: conflicting sources resolved by declared precedence ---------------------------

STALE = "A check-up and clean costs 70 dollars."


def _with_second_source(business_copy, precedence: int, body: str, source_id: str = "old_price_list",
                        folder: str = "copy"):
    spec = business_copy("dental", folder=folder, replace=[("precedence = 10\n", f'''precedence = 10

[[grounding.sources]]
id = "{source_id}"
path = "knowledge/{source_id}.md"
description = "An earlier price list."
precedence = {precedence}
''')])
    (spec.parent / "knowledge" / f"{source_id}.md").write_text(body, encoding="utf-8")
    return spec


def _core_on(spec: Path):
    from studio.tests.helpers import World
    from studio.agent.scripted import ScriptedAgent
    runner = asyncio.Runner()
    registry = SpecRegistry()
    registry.register(compile_specification(load_specification(spec)))
    store, agent, calendar = EpisodeStore(), ScriptedAgent(), SimulatedCalendar()
    return World(core=Core(registry, store, agent, {"calendar": calendar}), agent=agent, store=store,
                 calendar=calendar, runner=runner), runner


def test_the_higher_precedence_source_is_authoritative_and_the_lower_is_marked_superseded(business_copy):
    from studio.core.types import Claim, RetrieveRequest
    spec = _with_second_source(business_copy, 50, f"# Services and fees\n\n{STALE}\n")
    items = {i.item_id: i for i in compile_specification(load_specification(spec)).context.items}
    stale = next(i for i in items.values() if i.source_id == "old_price_list")
    assert items[stale.superseded_by].source_id == "practice_guide"
    w, runner = _core_on(spec)

    def cite_stale(view):
        ref = next(r["reference"] for _, res in view.turn_results for r in res.items if r.get("superseded"))
        return RespondRequest(message="It costs 70 dollars.",
                              claims=(Claim(kind="business_fact", text="70 dollars", reference=ref),))

    out = w.send("How much does a check-up cost?", script=[
        RetrieveRequest(query="check-up clean costs dollars"), cite_stale, RespondRequest(message="Let me check.")])
    result = next(s["payload"] for s in w.store.steps(TENANT, out.episode_id)
                  if s["kind"] == "result" and s["payload"]["kind"] == "retrieve")
    texts = [(r["text"], r.get("superseded", False)) for r in result["items"]]
    authoritative = [t for t, sup in texts if OLD in t]
    assert authoritative and (STALE, True) in [(t.strip(), s) for t, s in texts]
    assert [t for t, _ in texts].index(authoritative[0]) < [t.strip() for t, _ in texts].index(STALE)
    assert ("business_refusal", "source_superseded") in [(d["classification"], d["reason"])
                                                         for d in w.store.denials(TENANT, out.episode_id)]
    sent = " ".join(s["payload"]["text"] for s in w.store.steps(TENANT, out.episode_id) if s["kind"] == "egress")
    assert "70 dollars" not in sent
    assert all(STALE not in r.text for r in w.agent.views[0].references)  # never offered for citing
    runner.close()


def test_the_specification_outranks_every_source(business_copy):
    spec = _with_second_source(business_copy, 1, "# About the business\n\nWe are a veterinary clinic.\n")
    items = compile_specification(load_specification(spec)).context.items
    clash = next(i for i in items if i.source_id == "old_price_list")
    assert clash.superseded_by == "spec:identity"


def test_conflicting_sources_of_equal_precedence_are_a_finding_naming_both(business_copy):
    from studio.spec import validate
    spec = _with_second_source(business_copy, 10, f"# Services and fees\n\n{STALE}\n")
    report = validate(load_specification(spec))
    finding = next(f for f in report.findings if f.code == "conflicting_sources_without_precedence")
    assert finding.severity == "blocking" and "practice_guide" in finding.message and "old_price_list" in finding.message
    agreeing = _with_second_source(business_copy, 10, "# Opening hours\n\nSee the practice guide.\n", "notes",
                                   folder="agreeing")
    assert not [f for f in validate(load_specification(agreeing)).findings
                if f.code == "conflicting_sources_without_precedence" and "Services" in f.message]


# --- Story 2.5: fresh reads before effects that depend on them (T12) --------------------------

def _clocked_world():
    from studio.tests.helpers import BUSINESSES, build_world
    runner = asyncio.Runner()
    now = {"t": datetime(2026, 10, 13, 9, 0, tzinfo=timezone.utc)}
    w = build_world(runner, [BUSINESSES / "dental" / "specification.toml"],
                    store=EpisodeStore(clock=lambda: now["t"]))
    return w, runner, now


def _confirmed(w):
    from studio.tests.helpers import ask_to_confirm
    w.send("Hi, I'd like a check-up on Monday at 9. Ada Lovelace, ada@example.com", script=[ask_to_confirm()])


def _reasons(w, out):
    return [d["reason"] for d in w.store.denials(TENANT, out.episode_id)]


def test_an_effect_with_no_basis_read_is_refused_and_the_core_reads_nothing_itself():
    from studio.tests.helpers import book
    w, runner, _ = _clocked_world()
    _confirmed(w)
    out = w.send("yes", script=[book(), RespondRequest(message="One moment.")])
    assert "basis_missing" in _reasons(w, out)
    assert sum(w.calendar.executions.values()) == 0
    assert not [e for e in w.store.evidence(TENANT, out.episode_id) if e["kind"] == "read_result"]
    runner.close()


def test_a_read_about_other_details_is_no_basis():
    from studio.tests.helpers import DENTAL_FACTS, book, check
    w, runner, _ = _clocked_world()
    _confirmed(w)
    out = w.send("yes", script=[check({**DENTAL_FACTS, "preferred_date": "2026-10-20"}), book(),
                                RespondRequest(message="One moment.")])
    assert "basis_missing" in _reasons(w, out) and sum(w.calendar.executions.values()) == 0
    runner.close()


def _read_then_confirm(w):
    from studio.tests.helpers import ask_to_confirm, check
    w.send("Hi, I'd like a check-up on Monday at 9. Ada Lovelace, ada@example.com",
           script=[check(), ask_to_confirm()])


def test_a_stale_read_is_refused():
    from datetime import timedelta
    from studio.tests.helpers import book
    w, runner, now = _clocked_world()
    _read_then_confirm(w)
    now["t"] += timedelta(seconds=901)
    out = w.send("yes", script=[book(), RespondRequest(message="One moment.")])
    assert "basis_stale" in _reasons(w, out) and sum(w.calendar.executions.values()) == 0
    runner.close()


def test_a_fresh_read_lets_the_effect_proceed_and_the_gap_is_recorded():
    from datetime import timedelta
    from studio.tests.helpers import book, booked_reply
    w, runner, now = _clocked_world()
    _read_then_confirm(w)
    now["t"] += timedelta(seconds=120)
    out = w.send("yes", script=[book(), booked_reply])
    effect = next(e for e in w.store.evidence(TENANT, out.episode_id) if e["kind"] == "effect_verified")
    basis = effect["payload"]["basis"]
    assert basis["read_evidence"] and basis["age_seconds"] == 120.0 and basis["turns"] == 1
    assert sum(w.calendar.executions.values()) == 1
    runner.close()


def test_freshness_declared_globally_is_rejected(business_copy):
    import pytest
    from studio.spec import SpecificationError
    spec = business_copy("dental", replace=[("[grounding]\n", "[grounding]\nmax_read_age_seconds = 900\n")])
    with pytest.raises(SpecificationError):
        load_specification(spec)
    top = business_copy("dental", folder="top")
    top.write_text("freshness_seconds = 900\n" + top.read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(SpecificationError):
        load_specification(top)


def test_a_dependency_must_name_a_declared_read(business_copy):
    from studio.spec import validate
    spec = business_copy("dental", replace=[('read = "check_availability"', 'read = "book_visit"')])
    codes = [f.code for f in validate(load_specification(spec)).findings]
    assert "basis_not_a_read" in codes


# --- Story 2.6: a garden centre served from its own material ---------------------------------

GC = "greenway-garden-centre"
GARDEN = Path(__file__).resolve().parents[1] / "businesses" / "garden-centre" / "specification.toml"
LAVENDER = "It's a lavender in a pot on my balcony. It's gone grey and crispy. I water it every day."


def test_the_garden_centre_passes_the_gate_with_no_business_python():
    from studio.spec import validate
    assert validate(load_specification(GARDEN)).passed
    assert not list(GARDEN.parent.rglob("*.py"))


def test_the_lavender_case_is_advised_as_general_knowledge_deferred_and_never_blamed():
    """The Brief's deliberate failure case, run credential-free: the Core lets the right answer through and
    stops the wrong one. Blaming the customer is refused before egress; the claim is handed to a person."""
    from studio.core.types import Claim, EscalateRequest
    w, runner = _core_on(GARDEN)
    blame = RespondRequest(goal="plant_care_advice", message="You overwatered it, so the guarantee does not apply.",
                           claims=(Claim(kind="conclusion", text="overwatered", conclusion="customer_neglect"),))
    advise = RespondRequest(
        goal="plant_care_advice",
        message="Lavender in a pot usually wants water only when the top of the compost is dry; daily watering can "
                "turn it grey. Whether the guarantee covers a balcony pot is for our plant desk to decide.",
        claims=(Claim(kind="general_knowledge", text="potted lavender needs little water"),
                Claim(kind="conclusion", text="guarantee position undetermined",
                      conclusion="guarantee_position_undetermined")))
    defer = EscalateRequest(goal="guarantee_claim", reason_class="cause_ambiguous",
                            summary="Lavender in a balcony pot, grey and crispy; customer may want to claim. "
                                    "Whether a potted balcony plant is covered is not declared.",
                            message="I've passed the guarantee question to our plant desk, who will reply.")
    out = w.send(LAVENDER, conversation="lavender", tenant=GC, script=[blame, advise])
    w.send("Can I get a replacement?", conversation="lavender", tenant=GC, script=[defer])
    eid = out.episode_id
    reasons = [d["reason"] for d in w.store.denials(GC, eid)]
    assert "conclusion_forbidden" in reasons  # the finding of neglect never left
    assert "rule_denied" not in reasons       # the claim was not refused
    sent = " ".join(s["payload"]["text"] for s in w.store.steps(GC, eid) if s["kind"] == "egress")
    assert "overwatered" not in sent
    claims = next(e for e in w.store.evidence(GC, eid) if e["kind"] == "reply_claims")
    assert claims["payload"]["general_knowledge_used"] is True
    kinds = {c["kind"]: c for c in claims["payload"]["claims"]}
    assert kinds["conclusion"]["conclusion"] == "guarantee_position_undetermined"
    episode = w.store.get_episode(GC, eid)
    assert episode.close_reason == "escalated"  # deferred to a person, not refused
    assert sum(w.calendar.executions.values()) == 0
    runner.close()


def test_advice_and_a_replacement_are_pursued_one_at_a_time_with_explicit_parking():
    w, runner = _core_on(GARDEN)
    out = w.send(LAVENDER, conversation="both", tenant=GC, script=[
        RespondRequest(goal="plant_care_advice", message="Let's look at the plant first.")])
    w.send("And I want a replacement.", conversation="both", tenant=GC, script=[
        RespondRequest(goal="guarantee_claim", message="I can look at a claim. When did you buy it?")])
    goals = w.store.goals(GC, out.episode_id)
    assert goals == {"plant_care_advice": "parked", "guarantee_claim": "active"}
    w.send("Back to the plant, please.", conversation="both", tenant=GC, script=[
        RespondRequest(goal="plant_care_advice", message="Of course.")])
    goals = w.store.goals(GC, out.episode_id)
    assert goals == {"plant_care_advice": "active", "guarantee_claim": "parked"}
    assert list(goals.values()).count("active") == 1
    runner.close()


def test_an_approved_claim_is_written_to_the_records_system_and_read_back():
    """The claim path end to end: the plant desk approves the exact payload, the claim is created on the
    records system the specification names, and success is its read-back."""
    from studio.core.types import EffectRequest, FactUpdate
    from studio.tests.helpers import World
    from studio.agent.scripted import ScriptedAgent
    from studio.tests.helpers import args as as_args
    runner = asyncio.Runner()
    registry = SpecRegistry()
    registry.register(compile_specification(load_specification(GARDEN)))
    store, agent, records = EpisodeStore(), ScriptedAgent(), SimulatedCalendar()
    w = World(core=Core(registry, store, agent, {"records": records}), agent=agent, store=store,
              calendar=records, runner=runner)
    values = {"customer_name": "Ada Lovelace", "contact_email": "ada@example.com", "item_category": "hardy_outdoor",
              "purchase_window": "within_a_year", "proof_of_purchase": "receipt"}
    claim_args = {k: values[k] for k in ("item_category", "purchase_window", "proof_of_purchase")}
    claim = EffectRequest(goal="guarantee_claim", capability="create_guarantee_claim", arguments=as_args(claim_args),
                          facts=tuple(FactUpdate(name=k, value=v) for k, v in values.items()))
    out = w.send("My hardy shrub died; replacement please.", conversation="claim", tenant=GC, script=[
        claim, RespondRequest(goal="guarantee_claim", message="I've asked the plant desk to approve your claim.")])
    offer = next(o for o in store.offers(GC, out.episode_id, "operator_approval"))
    assert sum(records.executions.values()) == 0
    w.core.decide_approval(GC, offer["offer_id"], approve=True, by="plantdesk")
    w.send("Any news on my claim?", conversation="claim", tenant=GC, script=[
        EffectRequest(goal="guarantee_claim", capability="create_guarantee_claim", arguments=as_args(claim_args)),
        RespondRequest(goal="guarantee_claim", message="Your claim has been created.")])
    verified = [e for e in store.evidence(GC, out.episode_id) if e["kind"] == "effect_verified"]
    assert len(verified) == 1 and sum(records.executions.values()) == 1
    runner.close()
