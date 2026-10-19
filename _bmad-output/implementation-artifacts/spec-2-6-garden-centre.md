---
title: 'Story 2.6: A garden centre served from its own material'
type: 'feature'
created: '2026-10-19'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Business three must show that the Core serves a new business by declaration alone (P2-F5; FR16, FR17, FR34, FR50, FR69, FR89, FR116, EX7, EX13; Brief exemplar 3).

**Approach:**
- `studio/businesses/garden-centre/` holds a specification, guarantee terms, care guides and scenarios, with no Python.
- The guarantee exclusions, timeframe and proof are deny rules on the claim. The claim is liability-class, behind operator approval, so an eligible claim is deferred to a person.
- `customer_neglect` is a forbidden conclusion, and general knowledge is allowed but must be marked.
- The lavender case is proven credential-free with a scripted agent (the Core's side). The CLI scenarios cover what the deterministic stand-in can show.
- Engine-leak entry P3.

</frozen-after-approval>

## Implementation Notes

- The specification passed the validation suite as written. The CLI and the pytest scenario runner register the generic simulated system of record under `records` as well as `calendar` (leak-log P3: no leak, fixture wiring).
- Tests (`test_knowledge.py`): the gate passes with no Python; the lavender record (general knowledge marked, guarantee position undetermined, neglect refused before egress, deferred as `cause_ambiguous`); two goals with one active and the other parked; an approved claim written to `records` and read back. Scenarios G1–G5 pass in both context modes.

## Review Triage Log (Blind Hunter)

| # | Finding | Verdict | Route |
|---|---------|---------|-------|
| 1 | G1 proves less than the lavender criterion | medium | patch: G1 says what the stand-in shows and points to the scripted test that proves the Core's side |
| 2 | The care guide held the cause inference, so labelling it general knowledge was wrong | medium | patch: guides trimmed to care instructions; the cause is general knowledge |
| 3 | Unlabelled blame is not enforced | medium | deferred: the T6 limitation, measured in Epic 4 |
| 4 | The `records` adapter was never exercised; pytest wired different adapters | medium | patch: the same adapters in the pytest runner, plus an approve, claim, read-back test |
| 5 | An approved claim is never created | medium | patch (test of the path when the requester writes again); deferred: approval as an external event |
| 6 | G5 holds an `operator_approval_required` denial | low | patch: asserted exactly and explained |
| 7 | Booking wording in claim evidence | low | recorded in P3 |
| 8 | Adapter connectedness not validated at startup | medium | deferred |
| 9 | Brief rules and actions not declared | low | recorded in P3; `cause_ambiguous` escalation added |
| 10 | No contact details on an escalated claim | medium | patch: name and email are claim obligations |
| 11 | No scenarios for the guard or other escalations | low | rejected (no new mechanism; covered for dental and brewery) |
| 12 | Parking is not journaled | low | rejected: pre-existing (goals table, FR50); the test checks the state |
| 13 | Scope change of the proof-gate test | low | recorded in the Phase 2 report |
| 14 | Hard-coded tenant strings and ambiguous leak-log wording | low | patch |
