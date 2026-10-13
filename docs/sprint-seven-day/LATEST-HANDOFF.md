# LATEST-HANDOFF — for a fresh Claude Code session

Written 2026-10-12, updated 2026-10-13, on branch `harden/seven-day`: the Day 7 session's work is committed (`95bd201`, `0339313`, `6fa4af3`; see CURRENT-STATE header); the only later commit is the one that updated this file. Read in this order: [SPRINT-CONTRACT.md](SPRINT-CONTRACT.md) (what is allowed), [CURRENT-STATE.md](CURRENT-STATE.md) (evidence), [DECISION-LOG.md](DECISION-LOG.md) (what is approved). `CLAUDE.md` holds the project rules and their precedence. If any of these and the repository disagree, the repository wins.

## 0. Before you touch anything

1. **Writer.** One session writes at a time, by the user's explicit authorization (DL-020). If you were not told you are the writer, ask before editing.
2. **State.** `git log -1 --format=%h` must be the commit that added this text (or a commit the user approved since), and `git status --short` must be clean apart from ignored files. If this text is still uncommitted, the only changes must be the move of the sprint documents, the model research brief and its PDF from the repository root into `docs/sprint-seven-day/`, the matching path updates in `CLAUDE.md` and `README.md`, and the edits to `CURRENT-STATE.md` and this file. If not, stop and tell the user.
   The repo-root `.env` holds a live `OPENAI_API_KEY` that the user keeps for the voice platform. The platform suite cannot read it (`builder_platform/tests/conftest.py`, DL-040). Do not delete that file.
3. **Re-verify** before relying on any number: `python -m pytest builder_platform/tests -q`, `python -m pytest claude_plugin/tests -q`, and `python selftest.py` in `boilerplate/`, `Generated_Agents/BassanBrewerySDR/`, `Generated_Agents/BrightSmileDental/`. Before claiming a new commit is green, also run the suite on a clean `git worktree` (line endings differ on checkout; DL-030).
4. **Not a voice task.** Mock mode only until the user provides a key for the live run. `CLAUDE.md` states the precedence (DL-018).

## 1. Where things are

- Engine (edit only in `boilerplate/`, then copy to both agents; the drift test enforces it): the list is `ENGINE_FILES` in `builder_platform/builder_core.py`.
- Authorization: `nodes._authorize` → `authz.AuthorizationLedger`. Verification: `nodes.execution_validator_node` → `tools.VERIFIERS`. Simulated systems of record and failure injection: `tools.SimulatedBackend`, `SIMULATED_FAILURE`.
- Agents: `boilerplate/` (Acme template), `Generated_Agents/BrightSmileDental`, `Generated_Agents/BassanBrewerySDR` (kept passing, not built on).
- Evaluation: `builder_platform/tests/test_cross_business_eval.py`, scenarios in `builder_platform/tests/eval_scenarios/`, runner `agent_driver.run_agent(agent_dir, request)` (one subprocess per agent; it blanks `OPENAI_API_KEY` itself). Step forms: a string; `{"message", "inject", "env"}`; `{"resume": {"approved": bool}}`.

## 2. Status: every approved deliverable is done

C7 is complete in both modes. The live run (LIVE, `gpt-6-luna`, reasoning effort `none`, `max_completion_tokens`, 3 runs): 22/22 business scenarios passed 3/3, 138 model calls, 0 failed, about US$0.015 spent (all probes plus the run: about US$0.02 of the US$0.50 ceiling, DL-035). Report: `builder_platform/tests/live_reports/20261012T103142Z-gpt-6-luna.md`; details and caveats in CURRENT-STATE section 3b. It was run by the user in their own terminal; the key is never stored.

To repeat it: `$env:OPENAI_API_KEY = "<key>"` then
`python builder_platform/tests/live_eval.py --model gpt-6-luna --price-in 0.10 --price-out 0.50 --runs 3 --max-cost 0.25 --token-param max_completion_tokens --reasoning-effort none`
(about 5 minutes; prints a progress line per batch). Always ask the user before any live call.

1. **C8: DONE.** `python builder_platform/tests/correction_loop.py` (mock, about 30 s, exit 0); evidence in CURRENT-STATE section 3d.
2. **Day 7: DONE, committed** (`95bd201`, `0339313`, `6fa4af3`). The section "How this agent adapts and stays bounded" is in the root `README.md` (DL-039), with the limitations in two halves; stale text fixed in CURRENT-STATE, the dental README and SPRINT-CONTRACT section 8. Also this session, at the user's request: the test-isolation guard (DL-040); strict consent at the yes/no question, replacing the DL-015 keyword bypass (engine `nodes.py`, re-copied); `step4_build.md` trimmed back under its 6_450 budget instead of raising it (DL-030). Final run, mock mode, on the working tree and on a clean CRLF checkout: 332 + 12 passed, three selftests PASSED, C8 exit 0; re-run on the working tree at `6fa4af3` on 2026-10-13 with the same results (CURRENT-STATE section 1).

   **Exact next step:** none scheduled. The user decides what follows: merging `harden/seven-day` into `main` (ask before any push or PR), or one of the candidate follow-ups in item 5. If any code changes, re-run step 0.3 and the clean-checkout run.
3. **Second live run (paraphrases), DONE 2026-10-12 (13/13 passed 3/3, CURRENT-STATE section 3c); command kept for repeating:** `builder_platform/tests/live_scenarios/` holds 13 pre-registered scenarios (same behaviours, different wording, expectations fixed before the first run; pytest does not run them, `test_live_scenarios.py` checks the files). Command, in the user's own shell after setting the key: `python builder_platform/tests/live_eval.py --model gpt-6-luna --price-in 0.10 --price-out 0.50 --runs 3 --max-cost 0.15 --token-param max_completion_tokens --reasoning-effort none --scenarios builder_platform/tests/live_scenarios`. Report it as it comes out; never edit those expectations to match.
4. **Recorded idea, not scheduled (DL-041):** typed decision models (Jev, OpenAI Decisions API, Microsoft-Decision-1) for the engine's narrow decision points: the non-bare answer at a yes/no question, intent choice, the urgency guard, RAG sufficiency, enrichment tone. Never for `think` or the planner. Conditions and seams are in DL-041.
5. **Candidate follow-ups, none approved:** a live run of sentences answered at a yes/no question ("okay, but my cheek is really puffy", "yes, I'm the store manager, go ahead"), to see how the model classifies them now that strict consent sends them to classification; reasoning effort at the model's default; a schema change so intent/think parse natively (removes one rejected request per call).

## 3. Decisions still waiting for the user

None is `PROPOSED`: the user settled DL-015, DL-026, DL-029, DL-030, DL-036 and DL-037 and clarified DL-032 in the Day 7 session (see DECISION-LOG for the quotes). DL-023 is `OPEN` and does not block. Standing rule from the user: ask before deleting any code ("refer for approval before delteting").

## 4. Caveats worth keeping

- Agents cannot share a process (every agent's modules are named `config`, `nodes`, `tools`…): use `agent_driver.py`.
- `Flow` is defined in each agent's `config.py`; engine changes must tolerate an older config.
- `config.py` cannot import `tools.py` (`tools → compaction → config`).
- On this Windows shell long inline heredocs fail; write scripts to a file first.
- Open limitations, with evidence: CURRENT-STATE section 4.

## 5. Do not change

Finalized planning documents under `_bmad-output/`; engine files inside agent directories (edit `boilerplate/` and re-copy); the approved scope in SPRINT-CONTRACT. Do not stage or commit without the user.
