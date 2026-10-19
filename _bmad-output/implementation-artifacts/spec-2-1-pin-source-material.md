---
title: 'Story 2.1: Pin source material so episodes survive knowledge edits'
type: 'feature'
created: '2026-10-19'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A specification's version is a content hash that includes its sources (`studio/spec/loader.py:185`), so editing a leaflet creates a new version. Compiled versions live only in the in-memory `SpecRegistry`, so after a restart an episode pinned to the old version cannot be served at all, and none of its references resolve (P2-F2; FR30, FR33, FR62, NFR7, AD-8, AD-11).

**Approach:**
- At episode start, the Core pins what the episode runs on into the durable store:
  - each source's sections in `source_snapshots`, addressed by the source's content hash and written once (`INSERT OR IGNORE`, never updated);
  - the compiled specification in `spec_snapshots`, with source item texts stripped (they live once in `source_snapshots`).
- When the registry does not hold an episode's pinned version (after a restart, following an edit), the Core rebuilds it from the store, rehydrates the source texts, and registers it as non-live.
- The rest of the Core is unchanged. Provenance rows already carry tenant, source, source version and locator.
- Durable promotion and rollback of versions remain Story 3.1. This pins only what episodes already started on.

</frozen-after-approval>

## Implementation Notes

- Store: `source_snapshots` (content hash → sections, INSERT OR IGNORE) and `spec_snapshots` ((tenant, version) → compiled JSON with source texts stripped). Core: `_pin` inside the episode-creation transaction, plus `_entry`, which falls back to the store on a registry miss; `_turn`, `waive` and `record_expiry` use it.
- Tests: `studio/tests/test_knowledge.py`. A restart after an edit serves the pinned text, and every reference resolves. A new episode gets the new text. Content is stored once and never rewritten. References name tenant, source, version and locator. Mutation entry "an episode pins the material it starts on"; the mutation runner now also runs `test_knowledge.py`.

## Review Triage Log (Blind Hunter, shared with Story 2.2)

| # | Finding | Verdict | Route |
|---|---------|---------|-------|
| 1 | `spec_version` excludes the compiler version, so a compiler upgrade serves a recompilation to old episodes | medium | defer → Story 3.1 (durable immutable versions) |
| 2 | Claims attached to Core notices / a second egress | medium | patch (2.2) |
| 3 | `waive` and the expiry `_entry` swaps untested | low | rejected: same function, covered by the restart test |
| 4 | Episodes from before 2.1 have no snapshot | low | patch: reconstruct reports "no pinned specification"; no deployed data exists |
| 5 | A claim with no reference was reported as "never issued" | low | patch |
| 6 | Untested reconstruct branches | low | partly patched (no-reference, never-issued, Core notice); foreign-reference rejected (the Core refuses such claims before egress) |
| 7 | Closed-episode test didn't check ordering | low | patch (retrieval precedes reply) |
| 8 | Docstring did not match the output | low | patch |
| 9 | `_pin` serialises on every episode start | low | rejected: a few kB per start; measure before optimizing (E-07) |
| 10 | No integrity check on restored sections | low | rejected: written once by the Core itself |
| 11 | Test spelled the source id two ways | low | patch |
| 12 | Snapshot tables grow without a stated rule | low | patch: a schema comment states "kept for audit; retention deferred with AD-25" |
