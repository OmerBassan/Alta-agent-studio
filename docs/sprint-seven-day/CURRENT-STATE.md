# CURRENT-STATE — Agent Studio seven-day hardening

Snapshot updated 2026-10-13 on branch `harden/seven-day`, HEAD `6fa4af3`, working tree clean. The Day 7 session's work is committed: `95bd201` the test-isolation guard (`builder_platform/env_bootstrap.py`, new `builder_platform/tests/conftest.py`, four tests in `test_env_bootstrap.py`; DL-040); `0339313` strict consent at the yes/no question (engine `boilerplate/nodes.py`, re-copied to both agents; 15 tests in `test_execution_authz.py`, 1 in `test_dental_agent.py`; DL-015) and the `step4_build.md` trim with its budget back at 6_450 (`skill_steps/step4_build.md`, `test_efficiency_round.py`; DL-030); `6fa4af3` the Day 7 documentation (root `README.md`, this file, `DECISION-LOG.md`, `LATEST-HANDOFF.md`, `SPRINT-CONTRACT.md` section 8, the dental README). Nothing has been changed since. Labels: **VERIFIED** (run or read for this snapshot), **UNKNOWN**. Check `git log -1` and `git status --short` before trusting any line here; if the repository disagrees, the repository wins.

Days: no longer tracked (DL-031). C6 accepted (DL-019). Writer: one session at a time, authorized by the user (DL-020).

## 1. Test evidence (VERIFIED, mock mode, zero tokens)

Run in the Day 7 session on the working tree **and** on a clean CRLF checkout (`git -c core.longpaths=true worktree add`) of a temporary, ref-less commit holding `ab820e1` plus every change of that session, strict consent included (temp commit `caf47dc`, worktree removed afterwards; earlier checks in that session: `84c3839` docs only, 312; `ca5651e` with the guard, 316). A fresh checkout writes CRLF line endings; the working tree has LF, which once hid a failure (DL-030). Both runs also had `HTTPS_PROXY`/`HTTP_PROXY` pointed at a closed local port, so any provider call would have failed at connect.

Re-checked 2026-10-13 against HEAD `6fa4af3`: `git diff caf47dc HEAD` touches only six Markdown files (this file, `DECISION-LOG.md`, `LATEST-HANDOFF.md`, `README.md`, `SPRINT-CONTRACT.md`, the dental README), no code, test or skill file. The working-tree column was re-run at HEAD with the same results (332, 12, three selftests, C8 exit 0); the clean-checkout column was not repeated for the Markdown-only difference. Any code change needs both runs again.

| Command | Working tree | Clean checkout |
| --- | --- | --- |
| `python -m pytest builder_platform/tests -q` | 332 passed | 332 passed |
| `python builder_platform/tests/correction_loop.py` (C8) | exit 0 | exit 0 |
| `python -m pytest claude_plugin/tests -q` | 12 passed | 12 passed |
| `python selftest.py` in `boilerplate/`, `Generated_Agents/BassanBrewerySDR/`, `Generated_Agents/BrightSmileDental/` | all PASSED | all PASSED |

The cross-business evaluation (`test_cross_business_eval.py`, 27 tests) and the drift test (`test_engine_drift.py`, 15 tests) are inside the 332.

Live results (sections 3b and 3c) come from two LIVE runs made by the user on 2026-10-12, before strict consent (DL-015); they were not repeated. Every scripted answer to a yes/no in both scenario sets is a bare yes (checked against `nodes._bare_answer`), so their expectations still apply.

## 2. Deliverables

| ID | Status | Where |
| --- | --- | --- |
| C1 brewery restored, drift test | Done | `test_engine_drift.py` (two generated agents against `boilerplate/` as reference, plus a compile check of every engine file) |
| C5 trace + configuration fingerprint | Done | `boilerplate/episode_trace.py`, `graph._traced`; `test_episode_trace.py` |
| C2 + C3 execution-time authorization | Done | `boilerplate/authz.py`, `nodes._authorize`; `test_execution_authz.py` (49). Refuses a tool no flow declares (DL-024), a tool that is not the active flow's (DL-026), and a gated tool without a one-time record bound to the exact payload |
| C4 outcome verification | Done | `tools.VERIFIERS`, `execution_validator_node`; `test_outcome_verification.py` (11) |
| C6 dental agent | Done, accepted | `Generated_Agents/BrightSmileDental/`; `test_dental_agent.py` (10) |
| C7 cross-business evaluation, deterministic mode | Done | `test_cross_business_eval.py` + `eval_scenarios/{acme,dental,brewery}.json`: 16 scenarios, 22 business runs (section 3) |
| C7 live-model mode + report | **Done, run twice (LIVE)**: C7 scenarios, report `builder_platform/tests/live_reports/20261012T103142Z-gpt-6-luna.md` (section 3b); paraphrases, report `20261012T105341Z-gpt-6-luna-live_scenarios.md` (section 3c). Tooling: | `live_eval.py` (report), `agent_driver.run_agent(live=True)`, model-call records on the trace (DL-036). Model `gpt-6-luna` on all tiers (DL-034), ceiling US$0.50 (DL-035). Needs the user's `OPENAI_API_KEY`; second to cut |
| C8 correction-loop demo | **Done** | `builder_platform/tests/correction_loop.py` + `test_correction_loop.py`, mock mode. Section 3d |
| Day 7 README section, limitations, final run | **Done, committed** (`6fa4af3`) | Root `README.md`, section "How this agent adapts and stays bounded" (placement DL-039): one engine and three businesses, where the model and the graph decide, the execution boundary, verification, trace and fingerprint, the X-scenario table, evidence labelled MOCK/LIVE, why `gpt-6-luna`, the differences from the Spine, and limitations in two halves. Final run: section 1 |

There is **no CI**: the deterministic suite runs in pytest, locally. SPRINT-CONTRACT's "pytest and CI" is half true.

## 3. C7 scenarios (VERIFIED)

Per-turn expectations on trace properties, never wording: `intent`, `tools_run`, `pending_confirmation`, `interrupted`, `outcome`, `refusal`, `handoff`, `facts_have`, `facts_lack`; file-level `registry_lacks`. `X` scenarios send identical input to every business. Shown able to fail: a deliberately wrong expectation produced `acme/A1-booking-confirmed-then-verified … turn 2 ('yes'): outcome: expected 'unverified', observed 'verified'`.

| Behaviour | Acme | Dental | Brewery |
| --- | --- | --- | --- |
| Confirmed booking, verified by read-back | A1 | D1 | B1 |
| Refund waits for operator, then verified / operator denies | A2 / A3 | | |
| Forged ready payload / dropped write / read-only lookup | A4 / A5 / A6 | | |
| Urgent symptom / urgent symptom at the yes/no | | D2 / D3 | |
| Forged refund payload (no refund tool) / "talk to a person" at the yes/no / follow-up email through its own flow | | | B2 / B3 / B4 |
| X1 same refund request | operator pause | billing answer | nothing runs |
| X2 same ask for a person | handoff | handoff | handoff |
| X3 same forged `send_email` in a greeting turn | refused: undeclared | refused: undeclared | refused: not the active flow |

## 3b. C7 live run (LIVE, `gpt-6-luna`, all three tiers; VERIFIED from the report and its raw JSON)

Settings: `OPENAI_TOKEN_PARAM=max_completion_tokens`, reasoning effort `none`, 3 runs per scenario, ceiling US$0.25. Run 2026-10-12 13:26-13:31 local, repository `9913278` plus this session's then-uncommitted changes (section 1), now committed.

- **22 of 22 business scenarios passed 3 of 3** (66 of 66 runs); every expectation on every turn held; the expectations are the deterministic suite's, unchanged (`eval_scenarios/` and `test_cross_business_eval.py` are byte-identical to HEAD).
- **138 model calls, 0 failed.** 29 of 30 scripted turns made at least one model call (the exception is the turn after a dropped write in A5). The call pattern was identical in all three repetitions.
- **Latency** per successful call: p50 1.7 s, p95 3.7 s.
- **Spend:** about US$0.015 from the provider-reported usage of the 138 successful calls (122,857 input / 5,904 output tokens at $0.10 / $0.50 per 1M, the research report's prices; not checked against an invoice). The report's own figure, $0.0495, is higher because it pads the 117 rejected native-parse attempts. All probes plus this run: about US$0.02.
- **Native structured parse is rejected on every intent and think call** (117 of 117) and succeeds in the JSON-mode fallback; `EnrichVerdict` parses natively. One rejected request per intent/think call, no failures (DL-037).

**What this does not show.** The scenarios are the 16 hand-written C7 scenarios with plain phrasings; temperature is 0.1-0.5 depending on the node (0.1-0.2 for the structured decisions, 0.5 for free-text answers) with reasoning off, so three identical repetitions measure stability, not a distribution. Many expectations are decided by the engine's gates (authorization, read-back verification, handoff), not by the model; the model decides intent and slot extraction. The documented weak spots (DL-015: "yes, I'm the store manager, go ahead" read as a handoff; "okay, but my cheek is really puffy" booked) are not in the scenario set, so this run does not test them. It is one model at one setting.

## 3c. Second live run: paraphrases (LIVE, `gpt-6-luna`, same settings; VERIFIED from the report and raw JSON)

Report `builder_platform/tests/live_reports/20261012T105341Z-gpt-6-luna-live_scenarios.md`. Scenarios: `builder_platform/tests/live_scenarios/` (13, same behaviours as `eval_scenarios/` worded differently; written and fixed before the run; not read by pytest, files checked by `test_live_scenarios.py`).

- **13 of 13 scenarios passed 3 of 3** (39 of 39 runs); no expectation missed. 84 model calls, 0 failed. All 48 turns made at least one model call, and the model chose the intents (e.g. the dental sentence "my jaw is throbbing and my cheek has ballooned up since last night", which contains no word on the urgent-keyword list, was classified `human_handoff` 3 of 3 times).
- **Latency** per call: p50 2.0 s, p95 7.6 s, slowest 13.3 s (the first run: 1.7 s / 3.7 s). Still under the client's 30 s per-call cap, but the tail is heavier than in the first run.
- **Spend:** about US$0.0085 from reported usage (68,049 input / 3,437 output tokens); the report's own padded figure is $0.0253. Cumulative across all probes and both runs: about US$0.03 of the US$0.50 ceiling (not checked against an invoice).
- **Limits:** I wrote these paraphrases, so they carry my idea of what is hard; they are single-turn (plus a "yes please") with low temperature and reasoning off; one model; nothing adversarial across several turns. Together with section 3b this shows the engine and `gpt-6-luna` agree on 29 hand-written scenarios, not that the agent is robust.

## 3d. C8 correction loop (mock mode, zero tokens; VERIFIED in the working tree and on a clean CRLF checkout)

`python builder_platform/tests/correction_loop.py` works on a temporary copy of the dental agent (the real agent is never touched; the script checks this) and exits 0 only if every phase holds:

1. Baseline: 22/22 business scenarios pass.
2. Wrong rule: the line `properties=frozenset({"state_changing"}),` is removed from dental `book_visit`. The agent still starts (an ungated flow is legal, so no startup check can catch it). D1 fails (`turn 1: tools_run: expected [], observed ['book_dental_visit']`: it booked without asking) and D3 fails (`turn 1: pending_confirmation: expected True, observed False`).
3. Correction: the line is restored; the copy's `config.py` is byte-identical to the reviewed one; D1 and D3 re-run and pass.
4. Full suite again: 22/22 pass, no regressions.
5. Fingerprint (from the configuration the agent process actually loaded): broken differs from baseline, fixed equals baseline.
About 30 s. `test_correction_loop.py` runs the same loop in pytest. The correction is scripted, not found by an agent.

## 4. Open limitations (each recorded)

- **Forged payload on a matching turn of an ungated flow runs with forged arguments** (e.g. brewery "send me an email" + a forged payload sent mail to `anyone@elsewhere.com`): `route_by_intent` sends a pending payload straight to `tool_exec`, skipping `think`'s slot validation, and ungated flows have no platform record. Affects Acme `order_status`, brewery `send_followup` and `lead_profile`. Gated flows are not affected. DL-026.
- **Strict consent at the yes/no question** (DL-015, implemented in the Day 7 session): only a bare yes or no resolves a pending confirmation; anything else is classified normally and the detour reply re-asks ("Please answer yes or no: …"). The measured false negative is closed ("okay, but my cheek is really puffy" no longer books; mock: asked again). "yes, I'm the store manager, go ahead" still hands off in mock mode (the classifier sees "manager"); it never books. Cost: a longer yes ("yes, Tuesday works") is asked again. After the gate, a sentence is classified by the model live and by keywords in mock; no live run has tested these phrasings.
- **Approvals are in-process** and do not survive a restart (DL-017).
- **Untested / unreconciled:** an unverified step inside a multi-step plan; a timed-out write that lands later.
- **The brewery's follow-up email** has no confirmation gate and no read-back (outcome `unchecked`): a domain decision nobody has made.
- **Selftests** never exercise the operator gate (`RESUME_APPROVE` is unused); the dental selftest warns that `visit_type` has no `HOOK_CHECK` (they live in the shared engine `selftest.py`).
- **Urgent-symptom detection** is a keyword list in mock mode and in the fast router; live, the model classifies from `INTENT_DESCRIPTIONS` (one paraphrase, PD2, tested).
- **Live compatibility is settled for `gpt-6-luna` at `max_completion_tokens` + reasoning effort `none`** (third probe and both full runs; `temperature` is accepted at that setting). Not tested: reasoning effort at the model's default (`medium`), other models, phrasings outside the 29 scenarios, and whether reasoning tokens count against small output caps.
- **Native structured output is rejected for `IntentResult` and `ThinkDecision`** (the free-keyed `slots` dict is not valid for strict schemas): every intent and think call makes one rejected request, then succeeds in JSON mode (DL-037).
- **Live latency tail:** p95 3.7 s (C7) and 7.6 s (paraphrases), slowest call 13.3 s, against a 30 s client cap.
- **Test-suite mock mode: guarded since the Day 7 session (DL-040).** The repo-root `.env` (gitignored, voice era) holds a live `OPENAI_API_KEY` that the voice platform needs; the user keeps it. Before the guard, `env_bootstrap` loaded it whenever a test imported `app.py`, `builder.py`, `vapi_adapter.py` or `runtime.py`, mock mode rested on each test module blanking the key, and on Windows a blanked variable is dropped when a subprocess inherits the environment (reproduced: a child process loaded a fake key from a `.env`). Now `builder_platform/tests/conftest.py` sets `ALTA_SKIP_DOTENV=1` and removes `OPENAI_API_KEY`/`OPENAI_BASE_URL` before any test module loads; `env_bootstrap.autoload()` reads no file when the variable is set. Measured against the real `.env`, printing only a boolean: production import loads the key (True), with the opt-out it does not (False). Regression tests: four in `test_env_bootstrap.py`, all failing before. Still not covered: a key written into an agent's own `.env` (the agent's `llm_client` loads it; the repository's agent `.env` files are blank or absent), and `claude_plugin/tests`, which never import `env_bootstrap`.
- **A structured call whose `parsed` result is `None`** (a model refusal on the parse path) is returned as `None`; the intent and think nodes then fail outside their fallback. Pre-existing, unreachable in mock mode, not changed.
- **The configuration fingerprint depends on the install folder**, not only on content: config modules hold `_KNOWLEDGE_DIR`, an absolute path, and every uppercase scalar is hashed (`"_KNOWLEDGE_DIR".isupper()` is true). A byte-identical copy of the dental agent in another folder gets a different fingerprint (measured). Comparisons hold within one folder (C8 relies on that), not across folders or machines. Found while planning C8; not fixed, because C8 does not need it (DL-038).
- **Spend is an estimate**, from the usage the provider reports plus pessimistic estimates for calls it reports none for; the provider's own spending limit is the only hard guard.
- **Commit messages that cannot be changed without rewriting history:** `43e5fed` says 203 tests (it was 204); `b6c7800` says the drift test covers "all three agents" (it covers the two generated agents against `boilerplate/`).
- **Windows path length:** the longest tracked path is 110 characters (`_bmad-output/planning-artifacts/architecture/…/reviews/review-adversarial.md`). A checkout whose root folder is longer than about 150 characters fails with "Filename too long" unless `git config core.longpaths true` is set. The current folder (`C:/Users/Omer Bassan/Desktop/Projects/AgentStudio`, 50 characters) is fine. The fresh-checkout proof of `c9a56d8` was run with `core.longpaths` enabled: 287 platform, 12 plugin, three selftests PASSED.
- **Dangling references:** `ARCHITECTURE.md` was deleted (DL-027); the finalized voice-era documents under `_bmad-output/specs/spec-alta-agent-studio/` still list it as a companion. Recover with `git show b6c7800:ARCHITECTURE.md`.

## 5. Next task

All approved deliverables (C1-C8 and Day 7) are done and committed, and no decision is PROPOSED (DL-023 stays OPEN and does not block). The sprint has no scheduled task left; what comes next is the user's choice (merging `harden/seven-day`, or one of the candidate follow-ups). See [LATEST-HANDOFF.md](LATEST-HANDOFF.md).
