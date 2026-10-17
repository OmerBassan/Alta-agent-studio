---
title: 'Story 9.1 — Engine-leak classification rules, written before the evidence'
type: 'chore'
created: '2026-10-17'
status: 'done'
baseline_commit: '44c80942f6b7b7ebb091b973df1f06ad55105f0e'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-9-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** FR89 requires engine leaks to be classified as *should have been configuration*, *justifies an extension point* or *genuinely novel* (FR116's three levels), but the current log (PROOF-GATE.md, one entry plus one legacy note) uses ad-hoc labels and no stated test. That leaves the generalisation measurement graded after the fact and self-graded (PRD review F4.3).

**Approach:** Write the rules once, before any Builder-built business (Story 9.2): what counts as a leak, one test per class that a second person could apply, a fixed order for applying the tests, and the fields every entry records. Then reclassify the two existing entries under them.

## Boundaries & Constraints

**Always:**
- Class names are FR89's; levels map to FR116 (configuration / supported extension point / custom implementation).
- A leak is any change outside the business layer that a business needed (PRD §10.3: "every instance where the Core had to change rather than the business layer"). The business layer is `studio/businesses/<business>/` (specification and knowledge).
- Every entry records the business, its build position, the need in one sentence, the engine paths changed, the evidence (file and line, test, or diff), the class, which test decided it, who judged it, and the second check.
- A business-specific branch in engine code is always logged and flagged as a litmus-test violation (Spine litmus test; FR59), whatever its class.
- Any change to the rules after first use is a dated amendment. Earlier entries are graded under both versions.

**Decisions (user, 2026-10-17):**
- Judge of record: Claude proposes each classification; the user confirms it and is recorded as the judge. An unconfirmed entry reads "judged by: pending user confirmation".
- Trend: hand-written businesses (dental, brewery, and the garden centre of Story 2.6) are logged as pre-programme entries outside the business 1 → 4 trend. The trend starts with Story 9.2's Builder-built business.

**Never:** no code changes; no numeric thresholds; no change to any decision status; no deciding the build order (a separate technical choice, Story 9.2); no new classes beyond FR89's, apart from the two non-leak outcomes "no leak" and "defect, not a leak".

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Business-layer only | Need met in `studio/businesses/<b>/` | Logged as "no leak" with evidence | N/A |
| Simulated system of record gains business data | e.g. per-tenant open times in `SimulatedCalendar` | "No leak (fixture data)", because the real system would hold it (FR36) | A change to the adapter's contract is tested as an extension point instead |
| Engine bug exposed by a build | The fix makes the engine meet an already recorded requirement or test | "Defect, not a leak", still logged | Without such a prior requirement, it is a leak |
| Two classes fit | — | The first test that answers yes, in the order configuration → extension point → novel | Rationale recorded |

</frozen-after-approval>

## Code Map

- `docs/next-phase-proposals/PROOF-GATE.md:33-39` -- current leak log (entry 1, brewery: "test fixture leaf"; legacy note DL-015). Keep the text; add a pointer to the new home.
- `studio/extensions/simulated.py:45,67` and `studio/__main__.py:94,122` -- entry 1's evidence: `tenant_times` added to the simulated calendar, data supplied by the CLI. No change in `studio/core` or `studio/spec`.
- `studio/core/consent.py` -- where DL-015's strict-consent rule landed in the candidate. The legacy change was in the voice engine, a different engine.
- PRD FR89, FR116, FR58, FR59, §10.3; Spine litmus test -- the sources of the rules.
- `docs/next-phase-proposals/NEXT-PHASE-PLAN.md` §9 -- sources-of-truth table. One row gives the leak log its single home.

## Tasks & Acceptance

**Execution:**
- [x] `docs/next-phase-proposals/ENGINE-LEAK-LOG.md` -- create: rules (definition, the three class tests, order, non-leak outcomes, entry fields, amendment rule) and the reclassified log -- the successor home the story allows
- [x] `docs/next-phase-proposals/PROOF-GATE.md` -- append one line under the leak-log heading pointing to the new file; existing rows unchanged -- one home, no lost history
- [x] `docs/next-phase-proposals/NEXT-PHASE-PLAN.md` -- add one §9 row for the engine-leak log -- single source of truth

**Acceptance Criteria:**
- Given the rules, when a second person applies a class test to an entry's evidence, then the test is a yes/no question about the change itself (paths, contract, semantics), not about intent.
- Given entry 1 and the DL-015 note, when reclassified, then each has every required field, and its judge field reads "pending user confirmation" until the user confirms it.
- Given the files changed, when compared, then only the three files above changed.

## Implementation Notes

- 2026-10-17: implemented by a fresh subagent from this spec; verified against the diff since `44c80942f6b7b7ebb091b973df1f06ad55105f0e`. Files changed: `docs/next-phase-proposals/ENGINE-LEAK-LOG.md` (new), `PROOF-GATE.md` (one pointer paragraph), `NEXT-PHASE-PLAN.md` (one §9 row). No code changed.
- Matrix audit: this is a documentation story, so the I/O matrix rows are covered by rule steps, not automated tests. Business-layer only → step 0; fixture data → step 1 (with the contract check routing to test E); defect → step 2 (needs a requirement or test recorded before the build); two classes fit → the fixed order with recorded rationale (§1.2).
- Judgement calls flagged for the user: test-only changes under `studio/tests/` are not counted as engine changes (PRD §10.3 "where the Core had to change"); tenant id `hopfield-brewery` in `studio/__main__.py:30` is noted as fixture wiring, not a litmus violation; P2 (DL-015) graded *genuinely novel*, shape *platform semantics*, after step 2 answered no.
- Citations spot-checked against code and commits `b6c7800`, `0339313`: all resolve.
- Tests: `pytest studio/tests -q` 126 passed; `python -m studio scenarios --today 2026-10-13` 10/10, 0 model calls.

## Review Triage Log

Pass 1 (2026-10-17). Layers: blind hunter (12 findings), edge-case hunter (12), verification gap (none: the diff is static text and no code reads these documents).

| # | Finding | Verdict | Evidence | Route |
| --- | --- | --- | --- | --- |
| 1 | Step 1 sends a contract-altering simulator change straight to test E, skipping steps 2–3; if E says no, test N cannot be answered (blind, edge ×2) | medium | ENGINE-LEAK-LOG.md:56 vs :60: test N needs a recorded test-C answer | patch: route to step 2 |
| 2 | Test N answering no has no defined outcome (edge) | low | :60 defines only yes | patch: no → entry incomplete; redo C and E |
| 3 | Test E (b) lets a typed result choose the next step (blind) | medium | :59 "selects no next step except through that contract's typed result" admits Core branching on a verdict, which FR59 forbids | patch: no engine code branches on the result; it returns to the Agent (AD-18) |
| 4 | Test E (c) depends on build order (blind) | medium | :59 "another business's recorded material": at business 1 only earlier material exists | patch: any of the four exemplars' recorded material, regardless of build order |
| 5 | Defect step lacks proof of date, a definition of "build began", and a justification (blind, edge) | medium | :57; P2's fix lands in the commit that added dental | patch: required date evidence, defined build start, written justification |
| 6 | The fixture step absorbs the business literal `hopfield-brewery` in engine wiring, `__main__.py:30` (blind) | medium | The frozen matrix row decides this case as fixture data, so the rule stands; the tension is real | patch: P1 asks the judge this question explicitly |
| 7 | Second-check eligibility and blindness undefined (blind, edge) | medium | :100 "someone other than the proposer" could be another Claude with the same context | patch: the checker is the user or someone the user names, never the proposer's session; gets an evidence-only extract |
| 8 | Pending or disputed entries have no rule in the trend (blind) | medium | §1.5 and §1.3 silent | patch: the trend counts judged entries only; pending ones reported separately |
| 9 | PROOF-GATE axis 8 "zero Core changes (entry 1)" reads as contradicting P1 (blind) | low | Core (`studio/core`) truly unchanged; "engine" is wider | patch: one sentence relating Core and engine; epics.md not edited (final; out of the three files) |
| 10 | P2 says "both agents" and "all three agents"; lines not pinned to a commit; `test_dental_agent.py:89` → 88 (blind) | low | verified: the function is at :88 | patch |
| 11 | P2 step 2 asserts without quoting C3; step 3 adds an argument outside its question (blind) | medium | `docs/sprint-seven-day/SPRINT-CONTRACT.md:48` C3 binds records to payload and never says which message is consent | patch: quote C3; remove the extra step-3 sentence |
| 12 | Litmus flag narrower than the Spine litmus test, unstated (blind) | low | §1.4 checks identity tests only | patch: state the narrowness and add "a path that exists for one business only" |
| 13 | Business-layer content could act as code and game "no leak" (blind) | false | `studio/spec/model.py:74` `extra="forbid"`: new constructs need an engine change, so step 0 answers yes | reject |
| 14 | Legacy engine has no equivalent for steps 1 and 4 (edge) | low | §1.1 maps only the business layer for legacy entries | patch: name the legacy equivalents or state "no" with the reason |
| 15 | Fixture scope limited to `simulated.py` (edge) | low | :56 | patch: any simulator under `studio/extensions/` |
| 16 | Dependency manifests and new top-level modules not listed as engine (edge) | low | :43 | patch: every path outside the business layer and `studio/tests/` |
| 17 | One change serving two needs is double-counted (edge) | low | :45 | patch: trend counts needs; mark shared-change entries |
| 18 | "Build began" undefined (edge) | medium | merged with #5 | patch (#5) |
| 19 | P2 merges two commits into one need (edge, low confidence) | low | one need (consent at the gate), two fixes; step 2 is cut at the first | patch: say so in P2 |
| 20 | "No leak (fixture data)" is a third non-leak outcome against the spec's Never (edge) | low | Never allows two non-leak outcomes | patch: "No leak" with reason "fixture data" |
| 21 | Spec and sprint-status also changed, beyond the three files (edge) | false | Those are bmad-build bookkeeping; the AC concerns deliverables | reject |

## Verification

**Commands:**
- `python -m pytest studio/tests -q` -- expected: same pass count as 2026-10-14 (126); this story changes no code
- `python -m studio scenarios --today 2026-10-13` -- expected: 10/10

**Manual checks:**
- Every log entry has all required fields; class names match FR89 exactly.

Patches applied by the implementation subagent (2026-10-17); re-verified: 126 passed, scenarios 10/10, commit dates of `589c3a0`, `b6c7800`, `085929d` (C3 first committed, followed across the rename), `0339313` checked. P1 outcome label is now "No leak" with reason *fixture data*; P2 unchanged (genuinely novel).
