---
title: 'Story 9.1 — Engine-leak classification rules, written before the evidence'
type: 'chore'
created: '2026-10-17'
status: 'draft'
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

**Never:** no code changes; no numeric thresholds; no change to any decision status; no deciding the build order (a separate technical choice, Story 9.2); no new classes beyond FR89's, apart from the two non-leak outcomes "no leak" and "defect, not a leak".

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Business-layer only | Need met in `studio/businesses/<b>/` | Logged as "no leak" with evidence | N/A |
| Simulated system of record gains business data | e.g. per-tenant open times in `SimulatedCalendar` | "No leak (fixture data)", because the real system would hold it (FR36) | A change to the adapter's contract is tested as an extension point instead |
| Engine bug exposed by a build | The fix makes the engine meet an already recorded requirement or test | "Defect, not a leak", still logged | Without such a prior requirement, it is a leak |
| Two classes fit | — | The first test that answers yes, in the order configuration → extension point → novel | Rationale recorded |

</frozen-after-approval>

## Open Questions

1. **Who is the judge of record?** Options:
   - (a) Claude proposes each classification and the user confirms it, as the recorded judge. This satisfies FR76's "recorded by a person" and addresses the self-grading critique, at a few minutes per entry.
   - (b) Claude judges and the user spot-checks. Faster, but the measurement stays self-graded.
   - (c) As (a), plus an independent second classification by a fresh session before the user confirms. Strongest, and costs one extra session per business.
2. **Do pre-programme businesses count in the trend?** Dental, brewery and the coming garden centre (Story 2.6) were hand-written, not built through the Builder. Options:
   - (a) Log them, but keep them out of the business 1 → 4 trend that §10.3 judges, because FR88 says the four are the businesses built through the Builder. The trend starts at Story 9.2.
   - (b) Count them in the trend. That gives more points, but mixes hand-written and Builder-built setup and leans the trend toward success.

## Code Map

- `docs/next-phase-proposals/PROOF-GATE.md:33-39` -- current leak log (entry 1, brewery: "test fixture leaf"; legacy note DL-015). Keep the text; add a pointer to the new home.
- `studio/extensions/simulated.py:45,67` and `studio/__main__.py:94,122` -- entry 1's evidence: `tenant_times` added to the simulated calendar, data supplied by the CLI. No change in `studio/core` or `studio/spec`.
- `studio/core/consent.py` -- where DL-015's strict-consent rule landed in the candidate. The legacy change was in the voice engine, a different engine.
- PRD FR89, FR116, FR58, FR59, §10.3; Spine litmus test -- the sources of the rules.
- `docs/next-phase-proposals/NEXT-PHASE-PLAN.md` §9 -- sources-of-truth table. One row gives the leak log its single home.

## Tasks & Acceptance

**Execution:**
- [ ] `docs/next-phase-proposals/ENGINE-LEAK-LOG.md` -- create: rules (definition, the three class tests, order, non-leak outcomes, entry fields, amendment rule) and the reclassified log -- the successor home the story allows
- [ ] `docs/next-phase-proposals/PROOF-GATE.md` -- append one line under the leak-log heading pointing to the new file; existing rows unchanged -- one home, no lost history
- [ ] `docs/next-phase-proposals/NEXT-PHASE-PLAN.md` -- add one §9 row for the engine-leak log -- single source of truth

**Acceptance Criteria:**
- Given the rules, when a second person applies a class test to an entry's evidence, then the test is a yes/no question about the change itself (paths, contract, semantics), not about intent.
- Given entry 1 and the DL-015 note, when reclassified, then each has every required field, and the judge field follows Open Question 1.
- Given the files changed, when compared, then only the three files above changed.

## Implementation Notes

## Verification

**Commands:**
- `python -m pytest studio/tests -q` -- expected: same pass count as 2026-10-14 (126); this story changes no code
- `python -m studio scenarios --today 2026-10-13` -- expected: 10/10

**Manual checks:**
- Every log entry has all required fields; class names match FR89 exactly.
