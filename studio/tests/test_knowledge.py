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
