---
title: 'Story 2.5: Require fresh reads before effects that depend on them'
type: 'feature'
created: '2026-10-19'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Freshness was only a label on read evidence; nothing stopped a booking made on yesterday's availability (P2-F4; FR35, U3/G45, AD-1, AD-18).

**Approach (T12, approved 2026-10-19):**
- An effect contract may declare `depends_on = {read, max_age_seconds}`.
- The Core refuses the effect (`basis_missing` / `basis_stale`) without a read of that capability, in this conversation, about the same details (shared arguments equal), recent enough. It never reads on the Agent's behalf.
- A fresh read lets the effect proceed, with the gap (turns, seconds) on its evidence.
- Global freshness is rejected by the strict schema.
- The gate report aggregates the gaps (U3).

</frozen-after-approval>

## Implementation Notes

- `ReadBasis` and `Capability.depends_on` (model); validation (`basis_on_a_read`, `basis_not_a_read`, `basis_shares_no_details`, unresolved read). Compile: `depends_on_read` / `max_basis_age_s` on the policy and the tool definition. Core: `_basis`, checked after the already-done short-circuit; the basis recorded on effect evidence. Reasons `basis_missing` and `basis_stale`.
- Businesses: dental `book_visit` depends on `check_availability`; brewery `place_event_hold` on `check_event_availability` (900 s).
- Agents: the deterministic agent makes the dependency's read before proposing confirmation, and again after a basis refusal. The LLM capability line names the dependency.
- Tests: 15 Core test scripts now read before booking (`helpers.check()`). The pinned credential-free decision count moved from 1.38 to 1.85 per turn by design. New tests cover missing, stale, other-details, fresh with gap, global freshness rejected, and a non-read dependency. Mutation entry "an effect needs a fresh basis read". Full suite 210 passed.
- U3, credential-free (30 runs): 6 effects with a basis, all 1 turn after their read, ~0 s apart. Scripted turns are instantaneous, so the seconds measure nothing yet; real gaps need live or real traffic.

## Review Triage Log (Blind Hunter, shared by Stories 2.4 and 2.5)

| # | Finding | Verdict | Route |
|---|---------|---------|-------|
| 1 | The basis check ignores what the read found | false for T12 | T12 bounds the read's presence and age; whether the slot is still free is the system of record's answer at execution (the simulated calendar refuses a taken slot). The agent's comment was reworded so it no longer claims more |
| 2 | `same_details` is trivially true when nothing is shared | medium | patch: a blocking `basis_shares_no_details` finding |
| 3 | Compile supersedes even identical text; validation requires different text | medium | patch: identical text is no conflict in either |
| 4 | Heading normalisation duplicated | low | patch: one `heading_key` in the loader |
| 5 | The conflict message could print "None" | low | patch |
| 6 | Only the first two sources compared | low | rejected: three equal-precedence sources under one heading, where only the later two differ, has no case yet |
| 7 | Retrieval can return more than k | false | references are issued for exactly the items returned; k is the retriever's budget, and the winner is the point of T11 |
| 8 | Deterministic pre-confirm read accepted any read | low | patch: only the dependency's read counts |
| 9 | Basis check runs before the authority and confirmation checks | low | intended: freshness is a precondition of the act; the Core tests read first, as the contract requires |
| 10 | Reconstruction ignores supersession | low | patch: retrieval results carry `superseded_by` |
| 11 | More mutation proofs | low | rejected: the two gates (superseded citation, basis) are mutation-proven |
| 12 | Untested findings and the agent recovery path | low | rejected: the recovery path is exercised by every D1/B1 scenario run |
| 13 | Global-freshness test predates the change | low | kept as a regression guard for the AC |
| 14 | No test of the 900 s boundary | low | rejected (exclusive by `>`; documented) |
| 15 | U3 aggregation missing | medium | patch: the gate report prints the read-to-effect gap distribution |
| 16 | Docs and status lag | medium | sprint status updated at commit; PROOF-GATE row 3's 1.38 is labelled 2026-10-13 history in the phase report; the extra read per booking changes live calls per turn, to be re-measured |
