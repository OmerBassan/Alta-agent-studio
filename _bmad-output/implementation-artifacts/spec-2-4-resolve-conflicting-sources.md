---
title: 'Story 2.4: Resolve conflicting sources by declared precedence'
type: 'feature'
created: '2026-10-19'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Precedence was only a sort tie-break; two of a business's documents could disagree and the Agent could quote the outdated one (P2-F3; FR31, EX14, AD-7).

**Approach (T11, approved 2026-10-19):**
- A conflict is the same heading, in different text, in two places.
- At compile time the specification outranks every source, and between sources the lower declared precedence wins. The loser carries `superseded_by`.
- Retrieval returns the authoritative item ahead of a superseded hit, which is marked.
- Superseded material is never offered for citing, and citing it is refused (`source_superseded`).
- Equal precedence with different text is a blocking validation finding naming both sources.

</frozen-after-approval>

## Implementation Notes

- `ContextItem.superseded_by`; `_resolve_precedence` in compile; `_check_source_conflicts` in validate; `heading_key` in the loader. Core: the claim refusal, the retrieval ordering and marking, the view excluding superseded items. Reason `source_superseded`. Reconstruction shows `superseded_by`.
- Tests in `test_knowledge.py`: authoritative vs superseded on retrieval, refusal before egress, the specification outranking a source, and the equal-precedence finding naming both. Mutation entry "a superseded source cannot be cited".

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
