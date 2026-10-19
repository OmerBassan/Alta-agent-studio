"""Reconstruct an episode's answers from the record alone (Story 2.2, FR37).

Reads only the store — steps, evidence, provenance and the material pinned at
episode start (Story 2.1). It never consults the registry or the business's
files, so the answer to "what did this reply rely on?" survives any later edit
or deletion of the material.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from studio.core.store import EpisodeStore


def _pinned_item(store: EpisodeStore, ref_row: Optional[dict], spec_items: dict[str, dict],
                 sources: dict[str, dict[str, dict]]) -> dict[str, Any]:
    if ref_row is None:
        return {"unresolved": "the reference was never issued"}
    item = {"source_id": ref_row["source_id"], "source_version": ref_row["source_version"],
            "locator": ref_row["locator"]}
    if ref_row["item_id"].startswith("src:"):
        version = ref_row["source_version"]
        if version not in sources:
            sources[version] = {s["locator"]: s for s in store.source_snapshot(version) or ()}
        section = sources[version].get(ref_row["locator"])
        if section is None:
            return {**item, "unresolved": "the pinned source text is missing from the store"}
        return {**item, "title": section["title"], "text": section["text"]}
    spec_item = spec_items.get(ref_row["item_id"])
    if spec_item is None:
        return {**item, "unresolved": "the pinned specification text is missing from the store"}
    return {**item, "title": spec_item["title"], "text": spec_item["text"]}


def reconstruct(store: EpisodeStore, tenant: str, episode_id: str) -> list[dict[str, Any]]:
    """The episode's replies and retrievals, in order.

    Each message sent: ``{"kind": "reply", "seq", "egress" (reply | terminal_notice | ...), "text",
    "claims": [...], "cites_nothing"}``. A claim is ``{"kind", "text"}`` plus, by kind, ``reference`` and
    ``item`` (business fact: the cited item's text, title, source, version, locator), ``evidence`` (action
    taken) or ``conclusion``. Each retrieval: ``{"kind": "retrieval", "seq", "query", "results":
    [{"reference", "item"}]}``. An item that cannot be resolved carries ``unresolved`` with the reason. A
    message that cites nothing says so; claims belong only to the reply their decision produced, never to a
    notice the Core sent on its own."""
    episode = store.get_episode(tenant, episode_id)
    if episode is None:
        raise LookupError(f"no episode {episode_id} for {tenant}")
    raw = store.spec_snapshot(tenant, episode.spec_version)
    spec_items = {i["item_id"]: i for i in json.loads(raw)["context"]["items"]} if raw else None
    sources: dict[str, dict[str, dict]] = {}

    def cite(ref: Optional[str]) -> dict[str, Any]:
        if not ref:
            return {"unresolved": "the claim carried no reference"}
        if spec_items is None:
            return {"unresolved": "no pinned specification for this episode in the store"}
        row = store.lookup_reference(ref)
        if row is not None and (row["tenant"] != tenant or row["episode_id"] != episode_id):
            return {"unresolved": "the reference belongs to another conversation"}
        return _pinned_item(store, row, spec_items, sources)

    evidence = store.evidence(tenant, episode_id)
    claims_at = {e["step_seq"]: e["payload"]["claims"] for e in evidence if e["kind"] == "reply_claims"}
    out: list[dict[str, Any]] = []
    last_decision = None
    for step in store.steps(tenant, episode_id):
        if step["kind"] == "decision":
            last_decision = step["seq"]
        elif step["kind"] == "egress":
            claims = []
            own = claims_at.get(last_decision, ()) if step["payload"]["kind"] == "reply" else ()
            last_decision = None  # a decision's claims belong to the one reply it produced
            for claim in own:
                entry = {"kind": claim["kind"], "text": claim.get("text")}
                if claim["kind"] == "business_fact":
                    entry["reference"] = claim.get("reference")
                    entry["item"] = cite(claim.get("reference"))
                elif claim["kind"] == "action_taken":
                    entry["evidence"] = claim.get("evidence")
                elif claim["kind"] == "conclusion":
                    entry["conclusion"] = claim.get("conclusion")
                claims.append(entry)
            out.append({"kind": "reply", "seq": step["seq"], "egress": step["payload"]["kind"],
                        "text": step["payload"]["text"], "claims": claims, "cites_nothing": not claims})
    for e in evidence:
        if e["kind"] == "retrieval":
            outranked = {r["reference"]: r.get("superseded_by") for r in e["payload"].get("items", ())}
            out.append({"kind": "retrieval", "seq": e["step_seq"], "query": e["payload"]["query"],
                        "results": [{"reference": ref, "item": cite(ref), "superseded_by": outranked.get(ref)}
                                    for ref in e["payload"]["references"]]})
    return sorted(out, key=lambda r: (r["seq"], r["kind"] != "retrieval"))
