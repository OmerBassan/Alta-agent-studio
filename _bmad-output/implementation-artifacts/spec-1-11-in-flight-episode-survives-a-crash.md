---
title: 'Story 1.11: An in-flight episode survives a crash mid-turn'
type: 'feature'
created: '2026-10-17'
status: 'done'
route: 'dispatch'
baseline_commit: '2f9a88558421edca4f1e63b890b7176ba9ff4e6a'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A process that dies mid-turn can leave the journal half-written. The worst case is an effect row in state `started`: the adapter may have executed it, but no evidence was recorded and nothing ever reconciles it. That is an orphan effect, and later turns cannot tell whether the booking happened (FR64 remainder, NFR1 remainder, AD-12).

**Approach:**
- At the start of every turn, the Core reconciles any `started` effect of the episode with the adapter's read-back. This verifies an act that was already authorized; it decides no new step. The effect finishes as `verified` or `unverified` with its evidence, exactly once.
- Crash-injection tests prove that every journal boundary of a turn is recoverable in a new process. A real child process is killed with `os._exit` at the Nth journal write, then a new process continues the episode.

## Boundaries & Constraints

**Always:**
- Reconciliation reuses `_call_adapter(adapter.read_back, ...)` and `store.finish_effect`.
- Reconciliation runs inside the conversation lock, before the Agent is called, and records one `core` step `effect_reconciled` per effect.
- An unreachable read-back finishes the effect as `unverified`, which the Agent sees. It is never left `started`, and it is never treated as success.
- The crash tests use a file-backed `EpisodeStore`, a real subprocess killed with `os._exit(1)` at the Nth write, and a fresh process (new `Core` and new store objects on the same file) that sends the next inbound message.

**Never:**
- No re-execution of an effect by the Core during reconciliation (read-back only).
- No treating a journaled-but-unauthorized decision as authorized.
- No schema change, and no new dependency.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Crash after effect + evidence, before the reply is journaled | D1-style booking, crash after `finish_effect` | next inbound in a new process: the effect is not executed again (adapter executions = 1); `effect_verified` evidence appears exactly once | N/A |
| Crash after decision, before authorization | crash right after the `agent/decision` step | new process: that decision has no result step and is not executed; `effects` table unchanged | N/A |
| Crash between `start_effect` and `finish_effect` | effect row `started` | next turn: reconciled by read-back to `verified` (adapter ran) or `unverified` (it did not); one evidence row; no `started` rows remain | read-back failure → `unverified` |
| Every journal boundary (parametrized) | crash at write N, for every N in one full booking turn | after continuation: no `started` effect, no duplicate (tenant, episode, seq) step, no evidence row duplicated per idempotency key, lifecycle ∈ {active, pending, closed} | N/A |

</frozen-after-approval>

## Code Map

- `studio/core/harness.py` `_effect` (~:442-525): `start_effect` → offer consumed → adapter → read-back → `finish_effect`. These are the boundaries.
- `studio/core/harness.py` `_turn` (~:195): add the reconciliation before the agent loop. Find `started` effects via a new `store.started_effects(tenant, episode_id)`.
- `studio/core/store.py`: add `started_effects`. `start_effect`/`finish_effect` (~:439-453) are unchanged.
- `studio/extensions/simulated.py` `SimulatedCalendar`: its bookings live in memory. For a cross-process test, the child and parent need a shared system of record. Use a small file-backed calendar test double in the test module, keyed by idempotency key, with `read_back` checking the file. Do not change the product adapter.
- New `studio/tests/test_crash_recovery.py` with a child-process entry. The child counts writes by wrapping `EpisodeStore._exec` and `transaction` commits, and calls `os._exit(1)` at write N.

## Tasks & Acceptance

**Execution:**
- [x] `studio/core/store.py`, `studio/core/harness.py`: reconciliation of `started` effects at turn start.
- [x] `studio/tests/test_crash_recovery.py`: the three named cases and the parametrized all-boundaries test, with real subprocesses.
- [x] `studio/tests/test_checks_are_not_vacuous.py`: a mutation entry disabling the reconciliation, which must fail the crash suite. If the mutation runner only runs `test_core.py`, also add one in-process reconciliation test to `test_core.py` that leaves a `started` row and asserts it is reconciled.

**Acceptance Criteria:**
- Given a crash after an effect executed and its evidence was written, but before the reply was journaled, when a new process handles the next inbound, then the effect is not executed again and its evidence is present once.
- Given a crash after the Agent's decision was journaled but before authorization, then the decision is not treated as authorized, and nothing un-journaled is read.
- Given a crash injected at each journal boundary of a turn, when the episode continues in a new process, then its record is consistent: no orphan effect, no duplicate step, and the lifecycle is exactly one of active, pending or closed.

## Implementation Notes

- Implemented directly: the implementation subagent stopped on a session rate limit before changing anything. `store.started_effects`; `Core._reconcile_started_effects`, run at the start of every Agent loop (its typed results seed the turn, so the Agent sees "done" or "may or may not have happened" exactly as if the effect had just run), and before the suspended and halting-guard exits, so no orphan survives into a closed episode.
- Tests: `studio/tests/test_crash_recovery.py` uses real child processes killed with `os._exit(97)` after the Nth committed write, for every one of the booking turn's 17 commits, plus one inside the adapter call. Three in-process cases are in `test_core.py`: written-but-unrecorded becomes verified; never-received becomes unverified; an unreachable read-back becomes unverified, with the reason recorded. One more covers the suspended exit. Mutation entry "an effect a crash left started is reconciled". 183 passed.
- Finding while testing: a crash after `start_effect` but before the adapter runs reconciles to unverified. The Agent then hands the case to a person rather than claiming or retrying the booking. The invariant asserted is therefore "never executed twice; either booked once with verified evidence, or not booked and handed over".
- Known gaps, stated rather than solved:
  - (1) An expiry turn (Story 1.10) that crashes after committing `resumed` but before the Agent's decision leaves an active episode, and re-delivery counts as duplicate. The requester's next message continues it, but a silent requester leaves it waiting. Carried from 1.10 review row 10.
  - (2) Reconciliation runs when the episode is next touched. A quiet episode keeps its `started` row until then.
  - (3) The read-back is keyed by the idempotency key; the adapter's own reference was never recorded.
  - (4) The single-writer store is assumed (T3), and the conversation lock is per process.
- Carried from Story 1.10 review (row 10): `record_expiry` commits `external_event` + `resumed` + lifecycle active, then runs the Agent loop. A crash in between leaves an active episode with no Agent decision, and re-delivery is "duplicate". Include an expiry turn among the crash boundaries if it fits without new mechanism; otherwise record it as a known gap here.

## Spec Change Log

## Review Triage Log

| # | Finding | Verdict | Route |
|---|---------|---------|-------|
| 1 | Reconciliation skipped on the suspended and halting-guard exits → orphan on a closed episode | high | patch |
| 2 | The Agent never sees the reconciled outcome | high | patch (typed results seed the turn) |
| 3 | `on_unverified` policy dropped on reconciliation | medium | patch |
| 4 | Read-back raising is untested; evidence omits why it is unverified | medium | patch (test + `adapter_problem`) |
| 5 | Child exit code 1 is indistinguishable from an ordinary failure | medium | patch (`os._exit(97)`) |
| 6 | No per-key verified-evidence check; the continuation loop gave up silently | medium | patch |
| 7 | `started_effects` order not deterministic | low | patch (ORDER BY) |
| 8 | An unverified then a later verified row for one key | false | legitimate history: the interrupted attempt, then the confirmed retry; per-key verified ≤ 1 asserted |
| 9 | Swapping read-back for effect would pass | false | `test_an_interrupted_effect_the_system_never_received_is_unverified_not_success` asserts 0 executions |
| 10 | Expiry-turn crash; quiet episodes; reference=None; multi-process | medium | recorded as known gaps (Implementation Notes) |
| 11 | No crash between BEGIN and COMMIT | low | rejected: SQLite's transaction rollback is the guarantee; the harness crashes at every commit boundary |
| 12 | SQLite error during reconciliation propagates | low | rejected |

## Verification

**Commands:**
- `python -m pytest studio/tests -q`: all pass.
- `python -m studio scenarios --today 2026-10-13`: 10/10.
