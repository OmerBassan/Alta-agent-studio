---
title: 'Story 1.9: Complete the proof gate with a live comparison'
type: 'feature'
created: '2026-10-17'
status: 'done'
route: 'dispatch'
baseline_commit: '3245e9d07fb44319d6bfad5a34bb938389222411'
review_loop_iteration: 0
context:
  - '{project-root}/docs/next-phase-proposals/PROOF-GATE.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The proof gate's axes 3 (model calls) and 4 (latency) and its inline-resolution-validation judgement need one live run, but the scenario runner cannot produce that evidence: `--runs N` replays run 1's record N times (verified 2026-10-17: same episode id, no new steps, zero replies on runs 2–3, because message ids restart per run against one shared store), `--max-cost` is checked per scenario rather than for the whole run, and the in-memory store is discarded, so latency and refusals are unrecoverable.

**Approach:** Make each run independent and the cap cumulative, persist every run's record to a directory, add a report command that computes the gate's figures from those records alone; then (D1 authorized by the user 2026-10-17) run the live command once and write the verdict into `PROOF-GATE.md`.

## Boundaries & Constraints

**Always:** each run gets a fresh store, Core and simulated calendar; the spend total is summed across every run so far and the run stops once it reaches `--max-cost`, printing the actual estimated spend; figures in the report come from the persisted store files (model_calls, steps, denials), never from stdout; credential-free behaviour and output of `python -m studio scenarios` without the new flag stay as they are (10/10, 0 model calls); one live invocation only, the PROOF-GATE.md command plus the record flag, ≤ US$0.25.

**Never:** change `studio/core`, `studio/spec`, `studio/agent` or any scenario expectation; re-run the live command to chase a better result; patch anything in response to a live failure (a FAIL is written up with evidence and escalated, PRD §7.5); print or write the API key; commit the record directory (it goes under the scratchpad or a gitignored path).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Independent runs | `scenarios --runs 3` (credential-free) | 3 distinct episode ids per scenario, each with its own steps and replies; 30/30 PASS | N/A |
| Cumulative cap | prices set, cap reached after scenario k | stops, prints `Stopping: estimated spend $X reached --max-cost $Y`, exit 2 | spend is the total over all runs so far |
| Record | `--record DIR` | one SQLite file per (business, scenario, run) plus `results.jsonl` (pass, failures, per-turn wall latency, episode id) | DIR created if absent |
| Report | `gate-report DIR` | per-scenario pass rate; model calls per turn; per-call and per-turn latency p50/p95; every resolution refusal with its detail; spend | empty or missing DIR → exit 1 with a message |
| No model calls | report over a credential-free record | calls per turn 0, latency rows "no model calls" — not 0 ms | N/A |

</frozen-after-approval>

## Code Map

- `studio/__main__.py:84-112` -- `_scenarios`: Core/store/calendar built once per scenario outside the runs loop (the replay defect); `_spend(core, …)` per Core (the per-scenario cap). Add `--record`, add `gate-report` subcommand.
- `studio/__main__.py:52-61` -- `_spend`: reuse, but sum across runs.
- `studio/core/store.py:227` -- `EpisodeStore(path)` already file-backed; `model_calls()` (`latency_ms`, tokens), `steps()`, `denials()`.
- `studio/core/harness.py:291` -- every Core result journaled as step `kind="result"`; resolution refusals are `kind="respond"`, `status="refused"`, reason `resolution_invalid` or `action_without_evidence` (`_check_resolution`, :602-629).
- `studio/channels/harness.py:114-130` -- `run_scenario`; time each `channel.send` for per-turn wall latency. Do not change `check()`.
- Legacy figures for the report: PROOF-GATE.md axes 3–4 (1.5 calls/turn; p50 1.7 s, p95 3.7 s per call).

## Tasks & Acceptance

**Execution:**
- [x] `studio/__main__.py` -- fresh registry/store/calendar/Core per run; cumulative spend; `--record DIR`; `gate-report DIR` -- the measurement must be real before money is spent.
- [x] `studio/proof_gate.py` -- new: pure functions reading a record directory into the report figures (percentiles, rates, refusals) -- keeps the CLI thin and the maths testable.
- [x] `studio/tests/test_proof_gate.py` -- new: runs are independent (3 episode ids, replies on every run); cap is cumulative; record + report round-trip on the credential-free agent; percentiles on fixed data; empty dir fails loudly; "no model calls" is not rendered as 0 ms.
- [x] Live run (orchestrator, not the implementation subagent) -- once, key read from the root `.env` into the process environment only.
- [x] `docs/next-phase-proposals/PROOF-GATE.md` (orchestrator, after the live run; the implementation subagent does not touch it, makes no model call, and does not commit or push) -- axes 3–4 filled beside legacy; per-scenario pass rate with each failure classified Agent / specification / Core with evidence; each resolution refusal judged correct or false and inline validation declared relied-on or demoted; PRD §7.4 inventory dispositions; confirmation the 15-node pipeline was not ported; pass/fail verdict; the run recorded as the Story 2.3 context-assembly baseline.

**Acceptance Criteria:**
- Given the fix, when `python -m studio scenarios --today 2026-10-13` runs, then output is unchanged (10/10, 0 model calls) and the full studio suite passes.
- Given the live record, when the gate report is written, then every figure in it is reproducible by `python -m studio gate-report DIR`.

## Implementation Notes

- Measurement fixes (pre-spend): independent runs; cumulative cap; `--record`; `gate-report`; startup refusal of `--live` without prices; `status.json` with outcome; non-empty record dirs refused; refusal source taken from the refused respond step and pinned to the Core's wording by a real-Core test. `python -m pytest studio/tests -q` 157 passed; default scenarios unchanged (10/10, 0 calls).
- Live run 2026-10-17, once: 9/30 passed, US$0.0242. Verdict FAIL, escalated, nothing patched. Four defects named in PROOF-GATE.md: L1 the AgentView has no date (displaced fault, masked because the deterministic agent receives `today` from the CLI); L2 the agent contract does not say resolution evidence takes evidence ids; L3 refusal feedback loops until budget/stall; L4 `clarify` bypasses claim enforcement. B2, B4 and D6 expectations are also path-dependent or contradict the declared guard (specification findings).
- Fix and re-run (user-approved 2026-10-17, smallest diffs): L1–L4 plus L5 found in run 2; B2/B4/D6/B3/D4 expectations made outcome-based. Run 2: 17/30. Run 3 (declared last): 21/30, 0.95 calls/turn, p50 1.57 s / p95 2.24 s per call, 0 refusals. Final verdict PASS on the nine axes; D1, B1 and D6 remain as Agent findings. `gate-report` no longer loads model settings.
- Record kept outside the repo (session scratchpad, `rec-live`); not committed.

## Spec Change Log

## Review Triage Log

| # | Finding | Verdict | Evidence / route |
|---|---------|---------|------------------|
| 1 | `--live --max-cost` without prices: cap inert, spend $0 | high | `_spend` returns 0.0 when `price_in_per_mtok` is None; patch (startup ConfigurationError) |
| 2 | Cap stop or exception leaves a record that reports as complete; spend unprinted on exception | medium | No status marker; patch (`status.json`, printed in report) |
| 3 | Leftover `.db` from a crashed run reopened and double-counted; file path → raw FileExistsError | medium | `prepare_record_dir` checks only `results.jsonl`; patch |
| 4 | `undeclared_goal` from `_apply_common` counted as a resolution refusal | medium | `harness.py:326-329` applies to any kind; patch (source from the refused respond step) |
| 5 | Claim/resolution split rests on untested Core wording | medium | No test produces "the resolution rests on"; patch (real-Core test) |
| 6 | Other denials and halts dropped from the report | medium | Gate must classify every failure; patch (counts by classification:reason, close reasons) |
| 7 | Percentiles printed without n | low | Trivial; patch |
| 8 | "not priced" path untested | medium | Only priced fixtures exist; patch (test) |
| 9 | Malformed `results.jsonl` → traceback | low | Trivial wrap; patch |
| 10 | `--runs 0` exits 0 having run nothing | low | Trivial guard; patch |
| 11 | Turn latency mixes model-less turns | false | A guard halt is a real turn of the live system; the row is labelled wall time |
| 12 | Duplicate business args / unsafe scenario ids | low | Ids are repo-controlled; not met in use; rejected |
| 13 | PROOF-GATE.md and gitignore missing from diff | false | PROOF-GATE is the orchestrator's task after the run; record goes to the scratchpad |
| 14 | Test nits (import in loop, `__import__`, exact counts) | low | Cosmetic; rejected |
| 15 | Refusal fixture uses `platform_error` classification | low | Superseded by the real-Core test in row 5 |

## Verification

**Commands:**
- `python -m pytest studio/tests -q` -- expected: all pass, credential-free.
- `python -m studio scenarios --today 2026-10-13` -- expected: 10/10, 0 model calls.
- `python -m studio scenarios --runs 3 --record <tmp> --today 2026-10-13 && python -m studio gate-report <tmp>` -- expected: 30/30, 3 episodes per scenario.
