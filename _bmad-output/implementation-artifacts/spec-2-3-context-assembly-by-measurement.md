---
title: 'Story 2.3: Choose context assembly by measurement'
type: 'feature'
created: '2026-10-19'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Every source item's reference and full text sits in the Agent's view from episode start, so retrieval is nearly vacuous and does not scale past tiny sources (P2-F1; AD-7, AD-8, FR32, FR33, FR38, NFR5). The Spine says context assembly is "measured, not designed up front".

**Approach (T9 and T10, approved by the user 2026-10-19):**
- Context assembly becomes a platform setting, `STUDIO_CONTEXT_ASSEMBLY` = `standing` (today's behaviour, the default) or `on_demand`. It is validated at startup by `Settings` and by `Core`, and it is never business configuration.
- In on-demand mode an episode starts with only the specification projection's references. A retrieval searches the episode's pinned material and issues references for exactly the items it returns. A claim citing anything else is refused before egress as unissued.
- Retrieval sits behind a `Retriever` port (`studio/knowledge/retrieval.py`), with the lexical default. Its evidence lists source, version, locator and reference for each returned item.
- The gate report shows the mode and the retrieval misses, so one live comparison can set the default later.
- The live comparison run itself is out of scope here: the user asked for no model spend in this phase. The default stays `standing` until that measurement.

</frozen-after-approval>

## Implementation Notes

- `studio/knowledge/{__init__,retrieval}.py` (port and lexical default; tie-break by precedence then item id, replacing the old tie-break on a random reference). `CoreSettings.context_assembly` + `CONTEXT_ASSEMBLY_MODES`; `Core(retriever=...)`; `_start_episode` issues only specification items when on demand; `_retrieve` issues references for returned items. Config: `Settings.context_assembly` from `STUDIO_CONTEXT_ASSEMBLY`. CLI passes it to the Core, and `status.json` records it. Report: per-run retrieval hit/miss counts; the status line names the mode. One agent-guide line: material not listed must be retrieved before citing.
- Tests in `studio/tests/test_knowledge.py`: setting validation, on-demand start and retrieval issuance, standing issuance, refusal of an unretrieved citation, a replaced retriever, and the scenarios passing 10/10 in both modes credential-free.
- Open: AC4 (the live comparison per mode) waits on a spend approval. The user chose no model spend for Phase 2.
- After review: in on-demand mode `AgentView.context.items` is projected to the specification items plus retrieved items, with a titles-only `material_index` of the rest. The mode is pinned per episode (read from its `references_issued` step). The modes list lives once in `studio.config.CONTEXT_ASSEMBLY_MODES`, and the Core raises `ConfigurationError`.
- Known measurement confounds for the live comparison: in on-demand mode a retrieved item's text appears both in the turn's results and in the citable material, and issued references are never evicted, so long episodes drift toward the standing prompt size. Retrieval "miss" means nothing returned, not a recall measure. Compare input tokens per decision (already on every model call) alongside it.

## Review Triage Log (Blind Hunter)

| # | Finding | Verdict | Route |
|---|---------|---------|-------|
| 1 | On-demand view still carries every source text in `context.items` | high | patch |
| 2 | Mode not pinned per episode | medium | patch |
| 3 | Refusal test passed in either mode | medium | patch (foreign reference refused; retrieved reference accepted) |
| 4 | Reference-reuse branch untested | low | patch |
| 5 | Proof-gate additions untested | low | rejected: display-only counts; the live comparison will exercise them |
| 6 | "Miss" is a weak recall measure; prompt size per mode | medium | recorded as a measurement note (tokens per call already recorded) |
| 7 | Retrieved text duplicated; references only grow | medium | recorded as a known confound |
| 8 | On demand, the Agent cannot know what exists | medium | patch (titles-only index) |
| 9 | Modes listed in three places; two exception types | low | patch |
| 10 | Subprocess test had no timeout and did not count passes | low | patch |
| 11 | Constructor retriever parameter untested | low | patch |
| 12 | Stale refusal wording; tie-break changed in standing mode | low | rejected: deterministic tie-break replaces a random one; scenarios unchanged |
