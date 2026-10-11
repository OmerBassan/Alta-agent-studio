# LATEST-HANDOFF — for a fresh Claude Code session

Written 2026-10-12 for the commit that adds this text, on branch `harden/seven-day`. Read in this order: [SPRINT-CONTRACT.md](SPRINT-CONTRACT.md) (what is allowed), [CURRENT-STATE.md](CURRENT-STATE.md) (evidence), [DECISION-LOG.md](DECISION-LOG.md) (what is approved). `CLAUDE.md` holds the project rules and their precedence. If any of these and the repository disagree, the repository wins.

## 0. Before you touch anything

1. **Writer.** One session writes at a time, by the user's explicit authorization (DL-020). If you were not told you are the writer, ask before editing.
2. **State.** `git log -1 --format=%h` must be the commit that added this file, and `git status --short` must be clean apart from ignored files. If not, stop and tell the user.
3. **Re-verify** before relying on any number: `python -m pytest builder_platform/tests -q`, `python -m pytest claude_plugin/tests -q`, and `python selftest.py` in `boilerplate/`, `Generated_Agents/BassanBrewerySDR/`, `Generated_Agents/BrightSmileDental/`. Before claiming a new commit is green, also run the suite on a clean `git worktree` (line endings differ on checkout; DL-030).
4. **Not a voice task.** Mock mode only until the user provides a key for the live run. `CLAUDE.md` states the precedence (DL-018).

## 1. Where things are

- Engine (edit only in `boilerplate/`, then copy to both agents; the drift test enforces it): the list is `ENGINE_FILES` in `builder_platform/builder_core.py`.
- Authorization: `nodes._authorize` → `authz.AuthorizationLedger`. Verification: `nodes.execution_validator_node` → `tools.VERIFIERS`. Simulated systems of record and failure injection: `tools.SimulatedBackend`, `SIMULATED_FAILURE`.
- Agents: `boilerplate/` (Acme template), `Generated_Agents/BrightSmileDental`, `Generated_Agents/BassanBrewerySDR` (kept passing, not built on).
- Evaluation: `builder_platform/tests/test_cross_business_eval.py`, scenarios in `builder_platform/tests/eval_scenarios/`, runner `agent_driver.run_agent(agent_dir, request)` (one subprocess per agent; it blanks `OPENAI_API_KEY` itself). Step forms: a string; `{"message", "inject", "env"}`; `{"resume": {"approved": bool}}`.

## 2. The next task: Day 6

In the cut order fixed by DL-010 (C8 first to go, then the live report):

1. **C7 live-model mode and Markdown report.** Each scenario repeated 3 times against a real model, reported as rates. Needs the user's `OPENAI_API_KEY`; spends tokens. The driver currently forces mock mode, so a live switch is needed; intent expectations are keyword-derived in mock mode and will not transfer one-for-one to a model — report the results, do not tune expectations to pass.
2. **C8 correction-loop demo script:** a deliberately wrong config rule fails a scenario, the config is fixed, that scenario and the full suite are re-run, and the trace shows the fingerprint changed with no regression.

Day 7: README section "How this agent adapts and stays bounded", limitations (this is the existing graph, not the Spine's model-in-charge loop), final full run.

## 3. Decisions still waiting for the user

DL-015 (escalation keyword at the yes/no gate), DL-026 (every declared tool only as the active flow's action), DL-029 (dead-code removal), DL-030 (step4 budget raise) are `PROPOSED` and already in the code. DL-023 is `OPEN` and does not block the sprint. Do not promote any of them without the user's words.

## 4. Caveats worth keeping

- Agents cannot share a process (every agent's modules are named `config`, `nodes`, `tools`…): use `agent_driver.py`.
- `Flow` is defined in each agent's `config.py`; engine changes must tolerate an older config.
- `config.py` cannot import `tools.py` (`tools → compaction → config`).
- On this Windows shell long inline heredocs fail; write scripts to a file first.
- Open limitations, with evidence: CURRENT-STATE section 4.

## 5. Do not change

Finalized planning documents under `_bmad-output/`; engine files inside agent directories (edit `boilerplate/` and re-copy); the approved scope in SPRINT-CONTRACT. Do not stage or commit without the user.
