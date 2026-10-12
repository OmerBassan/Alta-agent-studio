# LATEST-HANDOFF — for a fresh Claude Code session

Written 2026-10-12, updated at the end of the model-selection session, on branch `harden/seven-day` (committed on top of `9913278`; see CURRENT-STATE section 1). Read in this order: [SPRINT-CONTRACT.md](SPRINT-CONTRACT.md) (what is allowed), [CURRENT-STATE.md](CURRENT-STATE.md) (evidence), [DECISION-LOG.md](DECISION-LOG.md) (what is approved). `CLAUDE.md` holds the project rules and their precedence. If any of these and the repository disagree, the repository wins.

## 0. Before you touch anything

1. **Writer.** One session writes at a time, by the user's explicit authorization (DL-020). If you were not told you are the writer, ask before editing.
2. **State.** `git log -1 --format=%h` must be the commit that added this text (or a commit the user approved since), and `git status --short` must be clean apart from ignored files. If not, stop and tell the user.
3. **Re-verify** before relying on any number: `python -m pytest builder_platform/tests -q`, `python -m pytest claude_plugin/tests -q`, and `python selftest.py` in `boilerplate/`, `Generated_Agents/BassanBrewerySDR/`, `Generated_Agents/BrightSmileDental/`. Before claiming a new commit is green, also run the suite on a clean `git worktree` (line endings differ on checkout; DL-030).
4. **Not a voice task.** Mock mode only until the user provides a key for the live run. `CLAUDE.md` states the precedence (DL-018).

## 1. Where things are

- Engine (edit only in `boilerplate/`, then copy to both agents; the drift test enforces it): the list is `ENGINE_FILES` in `builder_platform/builder_core.py`.
- Authorization: `nodes._authorize` → `authz.AuthorizationLedger`. Verification: `nodes.execution_validator_node` → `tools.VERIFIERS`. Simulated systems of record and failure injection: `tools.SimulatedBackend`, `SIMULATED_FAILURE`.
- Agents: `boilerplate/` (Acme template), `Generated_Agents/BrightSmileDental`, `Generated_Agents/BassanBrewerySDR` (kept passing, not built on).
- Evaluation: `builder_platform/tests/test_cross_business_eval.py`, scenarios in `builder_platform/tests/eval_scenarios/`, runner `agent_driver.run_agent(agent_dir, request)` (one subprocess per agent; it blanks `OPENAI_API_KEY` itself). Step forms: a string; `{"message", "inject", "env"}`; `{"resume": {"approved": bool}}`.

## 2. The next task: Day 7

C7 is complete in both modes. The live run (LIVE, `gpt-6-luna`, reasoning effort `none`, `max_completion_tokens`, 3 runs): 22/22 business scenarios passed 3/3, 138 model calls, 0 failed, about US$0.015 spent (all probes plus the run: about US$0.02 of the US$0.50 ceiling, DL-035). Report: `builder_platform/tests/live_reports/20261012T103142Z-gpt-6-luna.md`; details and caveats in CURRENT-STATE section 3b. It was run by the user in their own terminal; the key is never stored.

To repeat it: `$env:OPENAI_API_KEY = "<key>"` then
`python builder_platform/tests/live_eval.py --model gpt-6-luna --price-in 0.10 --price-out 0.50 --runs 3 --max-cost 0.25 --token-param max_completion_tokens --reasoning-effort none`
(about 5 minutes; prints a progress line per batch). Always ask the user before any live call.

1. **C8: DONE.** `python builder_platform/tests/correction_loop.py` (mock, about 30 s, exit 0); evidence in CURRENT-STATE section 3d.
2. **Day 7:** README section "How this agent adapts and stays bounded", limitations stated in two halves (domain/method and operational; this is the existing LangGraph graph, not the Spine's model-in-charge loop; the live result is one model at one setting on easy phrasings), final full run including a clean-checkout run.
3. **Second live run (paraphrases), DONE 2026-10-12 (13/13 passed 3/3, CURRENT-STATE section 3c); command kept for repeating:** `builder_platform/tests/live_scenarios/` holds 13 pre-registered scenarios (same behaviours, different wording, expectations fixed before the first run; pytest does not run them, `test_live_scenarios.py` checks the files). Command, in the user's own shell after setting the key: `python builder_platform/tests/live_eval.py --model gpt-6-luna --price-in 0.10 --price-out 0.50 --runs 3 --max-cost 0.15 --token-param max_completion_tokens --reasoning-effort none --scenarios builder_platform/tests/live_scenarios`. Report it as it comes out; never edit those expectations to match.
4. **Candidate follow-ups, none approved:** a live run that includes the DL-015 weak phrasings; reasoning effort at the model's default; a schema change so intent/think parse natively (removes one rejected request per call).

## 3. Decisions still waiting for the user

DL-015 (escalation keyword at the yes/no gate), DL-026 (every declared tool only as the active flow's action), DL-029 (dead-code removal), DL-030 (step4 budget raise), DL-036 (model-call records and the live spend guard) are `PROPOSED` and already in the code. DL-023 is `OPEN` and does not block the sprint. DL-032 has an open scope question: does "the Spine is the more reliable ground truth" also override DL-022 for sprint work? Do not promote any of them without the user's words.

## 4. Caveats worth keeping

- Agents cannot share a process (every agent's modules are named `config`, `nodes`, `tools`…): use `agent_driver.py`.
- `Flow` is defined in each agent's `config.py`; engine changes must tolerate an older config.
- `config.py` cannot import `tools.py` (`tools → compaction → config`).
- On this Windows shell long inline heredocs fail; write scripts to a file first.
- Open limitations, with evidence: CURRENT-STATE section 4.

## 5. Do not change

Finalized planning documents under `_bmad-output/`; engine files inside agent directories (edit `boilerplate/` and re-copy); the approved scope in SPRINT-CONTRACT. Do not stage or commit without the user.
