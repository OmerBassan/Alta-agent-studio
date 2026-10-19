---
title: 'Story 2.2: Reconstruct every answer from the record alone'
type: 'feature'
created: '2026-10-19'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** An operator cannot see which version of which material an answer relied on once the files change. Nothing assembles that from the record (FR37, FR73 retrievals part, NFR7, AD-6, AD-8).

**Approach:** Add `reconstruct(store, tenant, episode_id)` in `studio/core/reconstruct.py`. It reads only the store: steps, evidence, provenance, and the snapshots pinned by Story 2.1. It returns the episode's replies in order, each with the items its claims cited (text, title, source, version, locator). Retrievals come with their query and results. It never touches the registry or the business folder. A reply that cites nothing is marked `cites_nothing: true`, never shown as empty grounding. A reference whose pinned text cannot be found is reported as `unresolved`, never silently dropped.

</frozen-after-approval>

## Implementation Notes

- `studio/core/reconstruct.py`. Tests: identical result after the business folder is deleted; a clarifying reply cites nothing; a Core notice never inherits claims; unresolved references say why. Full suite 191 passed.

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
