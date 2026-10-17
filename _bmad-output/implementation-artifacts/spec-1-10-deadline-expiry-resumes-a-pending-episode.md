---
title: 'Story 1.10: A deadline expiry resumes a pending episode as an external event'
type: 'feature'
created: '2026-10-17'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'aebb2027f4e6bd1c39ef530a49ac86be8485eaa8'
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A `suspend` stores a deadline on the pending episode (`studio/core/harness.py` `_suspend`), but nothing ever reads it. A request waiting on a missing document or a lapsed hold is silently forgotten (FR60 remainder, FR61, FR63; NEXT-PHASE-PLAN §7 risk 1).

**Approach:** Add an expiry source on the Core. It reads the recorded clock (AD-12), finds pending episodes whose deadline has passed, and for each one records an external-system event on the episode and resumes it. The Agent receives the expiry as its input, and its next request is the next step: the Core itself never replies, escalates or closes because of an expiry. Expiries are idempotent, and an expiry for a closed episode is a late result.

## Boundaries & Constraints

**Always:**
- Reuse the existing pieces: the conversation lock, `store.now()`, `_agent_loop`, `record_external_result`'s late-result path and `add_late_result`.
- A deadline that cannot be parsed is refused at `suspend` time (typed refusal `invalid_deadline`), so a malformed deadline never sits as one that silently never fires.
- Deadlines are ISO 8601 date-times. A naive deadline is read as UTC.
- The Agent sees the expiry in its view as a conversation entry with a new role, `external`.
- The deterministic agent, given an `external` latest entry, escalates; it hands over when unsure.

**Never:**
- No scheduler, thread or timer in the Core. The expiry source is a method a caller invokes; a scenario or a CLI decides when it runs.
- No Core-initiated reply, escalation or close on expiry.
- No change to the store schema, beyond one query method to list due pending episodes.
- No new dependency.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Due expiry | pending episode, deadline ≤ clock | `external_event` step + evidence {kind `deadline_expired`, awaiting, deadline}; `resumed` step; lifecycle active; the Agent is called with an `external` entry, and its request drives the outcome | N/A |
| Not yet due | deadline > clock | nothing recorded | N/A |
| No deadline | pending, deadline null | never expires | N/A |
| Duplicate | the same expiry delivered twice (e.g. `expire_due` run twice, or `record_expiry` called again) | processed once; the second call returns `"duplicate"` and records nothing | N/A |
| Closed | `record_expiry` on a closed episode | late result recorded; resolution and lifecycle unchanged; returns `"late"` | N/A |
| Bad deadline | `suspend` with deadline `"next week"` | refused, reason `invalid_deadline`; episode not pending | typed refusal |

</frozen-after-approval>

## Code Map

- `studio/core/harness.py` `_suspend` (~:694): validate the deadline here. Add `record_expiry(tenant, episode_id)` and `expire_due()` beside `record_external_result` (~:828). Take the per-conversation lock exactly as `handle` does (:156-160), re-check the lifecycle under the lock, then call `_agent_loop(episode, entry, (), effects_suspended)`. `_view` (~:755) maps `external_event` steps to `ConversationEntry(role="external", text=...)`.
- `studio/core/ports.py:53`: `ConversationEntry.role` gains `"external"`.
- `studio/core/store.py`: add `due_pending(now: str) -> list[Episode]`, covering every tenant (lifecycle `pending`, deadline not null). Compare parsed datetimes in Python, not strings.
- `studio/agent/llm_agent.py` `render`: an `external` entry renders as `EXTERNAL: ...`. One line in the request guide says an EXTERNAL entry is an event from a system, not the person.
- `studio/agent/deterministic.py` `_decide`: if the latest conversation entry is `external`, escalate.
- `studio/tests/test_core.py`: add tests for every matrix row. Drive the clock with `EpisodeStore(clock=...)`, the way existing tests do.
- `studio/tests/test_checks_are_not_vacuous.py` `CHECKS`: add `"a passed deadline resumes the episode"`, disabling the due comparison in `expire_due` / `record_expiry` (FR96).

## Tasks & Acceptance

**Execution:**
- [x] `studio/core/ports.py`, `studio/core/store.py`, `studio/core/harness.py`: the expiry source, as in the Code Map.
- [x] `studio/agent/llm_agent.py`, `studio/agent/deterministic.py`: handle the `external` entry.
- [x] `studio/tests/test_core.py`: one test per matrix row, plus a test that the Core initiated nothing (the only steps after `resumed` are the Agent's decision and its results).
- [x] `studio/tests/test_checks_are_not_vacuous.py`: add the mutation entry.

**Acceptance Criteria:**
- Given a pending episode whose deadline has passed, when the expiry source runs, then an external-system event is recorded and the episode resumes, with the Agent receiving the expiry as its input.
- Given that resumed episode, when the Core handles the expiry, then the Core itself initiates no reply, escalation or close, and the next step is the Agent's request.
- Given an expiry for a closed episode, or the same expiry delivered twice, then the first is a late result that changes nothing and the second is processed once.
- Given the expiry check, then it reads the recorded clock, and disabling the expiry source makes a test fail.

## Implementation Notes

- `record_expiry` is async (it runs `_agent_loop`) and returns the turn's `TurnOutcome` when delivered, else `"duplicate"`, `"late"`, `"not_due"` (not pending, no deadline, or not yet due) or `"agent_suspended"` (operator stopped the Agent: nothing recorded, the episode stays pending and due). `expire_due` returns `(tenant, episode_id, outcome)` per due episode and reports a missing specification as `"unknown_tenant"`.
- Duplicate = a `deadline_expired` event already recorded since the episode's latest successful `suspend` result, or a `deadline_expired` late result. Checked before the late path, so an expiry whose own handling closed the episode is a duplicate, not late.
- `parse_instant` (store.py) is shared by `_suspend` and `due_pending`. A date without a time of day ("2026-10-20") is refused as `invalid_deadline` (start vs end of day would be a guess). Accepted deadlines are stored normalised to UTC ISO (`...+00:00`).
- New reason `invalid_deadline` (business_refusal) in `vocabulary.py`.
- `render` needed no code change: `role.upper()` already yields `EXTERNAL: ...`.

## Spec Change Log

## Review Triage Log

| # | Finding | Verdict | Route |
|---|---------|---------|-------|
| 1 | Closed episode with no deadline gets a `deadline_expired` late result (deadline None) | medium | patch |
| 2 | Legacy unparseable deadline raises from `record_expiry` | medium | patch (`unreadable_deadline`) |
| 3 | OverflowError on extreme deadlines | low | patch (trivial) |
| 4 | Deadline already passed at suspend → due-loop | medium | patch (refused) |
| 5 | One failing episode aborts `expire_due` | medium | patch (per-episode catch) |
| 6 | Deterministic external branch ignores turn results → stall | low | patch (trivial) |
| 7 | Prompt says date-only; Core refuses date-only | medium | patch (guide line) |
| 8 | Mutation disables the due check, not the source (AC4) | medium | patch |
| 9 | Untested: agent stopped, second wait, legacy row, closed-no-deadline, past deadline | medium | patch (tests) |
| 10 | Crash between expiry commit and the Agent turn strands the episode | medium | defer → Story 1.11 (crash mid-turn) |
| 11 | No product entry point calls `expire_due` | medium | defer → Epic 8 (the email channel is V1's first long-running host); spec says the caller decides |
| 12 | Duplicate suppression is in-process only | low | rejected: single-writer store is a stated limitation (T3) |
| 13 | `_locks` grows unbounded | low | pre-existing; rejected |
| 14 | Deterministic expiry escalation may record `rules_silent` | low | rejected: the deterministic agent is a stand-in (T8) |
| 15 | Core halt on an expiry turn contradicts "Core never closes" | false | the halt is the Core's declared safety exit (AD-18) for a failing agent, not a response to the expiry |
| 16 | No log line on expiry outcomes; UTC wording; Python-version parsing | low | rejected (outcomes are returned and journaled; CI pins 3.12) |

## Verification

**Commands:**
- `python -m pytest studio/tests -q`: all pass.
- `python -m studio scenarios --today 2026-10-13`: 10/10, 0 model calls.
