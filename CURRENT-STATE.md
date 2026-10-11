# CURRENT-STATE — Agent Studio seven-day hardening

Snapshot of the commit that adds this text, on branch `harden/seven-day`, made 2026-10-12 on top of `b6c7800`. Labels: **VERIFIED** (run or read for this snapshot), **UNKNOWN**. Check `git log -1` and `git status --short` before trusting any line here; if the repository disagrees, the repository wins.

Days: four of seven consumed when C7 started; C6 accepted (DL-019). Writer: one session at a time, authorized by the user (DL-020).

## 1. Test evidence (VERIFIED, mock mode, zero tokens)

Run on this working tree **and** on a clean `git worktree` of `b6c7800` with this commit's diff applied (a fresh checkout writes CRLF line endings; the working tree had LF, which once hid a failure — see DL-030).

| Command | Working tree | Clean checkout |
| --- | --- | --- |
| `python -m pytest builder_platform/tests -q` | 287 passed | 287 passed |
| `python -m pytest claude_plugin/tests -q` | 12 passed | 12 passed |
| `python -m pytest builder_platform/tests/test_cross_business_eval.py -v` | 27 passed | (inside the 287) |
| `python -m pytest builder_platform/tests/test_engine_drift.py -q` | 15 passed | (inside the 287) |
| `python selftest.py` in `boilerplate/`, `Generated_Agents/BassanBrewerySDR/`, `Generated_Agents/BrightSmileDental/` | all PASSED | all PASSED |

**No live-model run exists.** Behaviour under a real model is UNKNOWN.

## 2. Deliverables

| ID | Status | Where |
| --- | --- | --- |
| C1 brewery restored, drift test | Done | `test_engine_drift.py` (two generated agents against `boilerplate/` as reference, plus a compile check of every engine file) |
| C5 trace + configuration fingerprint | Done | `boilerplate/episode_trace.py`, `graph._traced`; `test_episode_trace.py` |
| C2 + C3 execution-time authorization | Done | `boilerplate/authz.py`, `nodes._authorize`; `test_execution_authz.py` (34). Refuses a tool no flow declares (DL-024), a tool that is not the active flow's (DL-026, PROPOSED), and a gated tool without a one-time record bound to the exact payload |
| C4 outcome verification | Done | `tools.VERIFIERS`, `execution_validator_node`; `test_outcome_verification.py` (11) |
| C6 dental agent | Done, accepted | `Generated_Agents/BrightSmileDental/`; `test_dental_agent.py` (9) |
| C7 cross-business evaluation, deterministic mode | Done | `test_cross_business_eval.py` + `eval_scenarios/{acme,dental,brewery}.json`: 16 scenarios, 22 business runs (section 3) |
| C7 live-model mode + report | Not started | Day 6; needs the user's `OPENAI_API_KEY`, spends tokens; second to cut |
| C8 correction-loop demo | Not started | Day 6; first to cut |
| Day 7 README section, limitations, final run | Not started | |

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

## 4. Open limitations (each recorded; none closed in this commit)

- **Forged payload on a matching turn of an ungated flow runs with forged arguments** (e.g. brewery "send me an email" + a forged payload sent mail to `anyone@elsewhere.com`): `route_by_intent` sends a pending payload straight to `tool_exec`, skipping `think`'s slot validation, and ungated flows have no platform record. Affects Acme `order_status`, brewery `send_followup` and `lead_profile`. Gated flows are not affected. DL-026.
- **Escalation at the yes/no gate is keyword-based** (DL-015, PROPOSED): measured false positives ("yes, I'm the store manager, go ahead", "it's not urgent" → handoff instead of booking) and a false negative ("okay, but my cheek is really puffy" → booked).
- **Approvals are in-process** and do not survive a restart (DL-017).
- **Untested / unreconciled:** an unverified step inside a multi-step plan; a timed-out write that lands later.
- **The brewery's follow-up email** has no confirmation gate and no read-back (outcome `unchecked`): a domain decision nobody has made.
- **Selftests** never exercise the operator gate (`RESUME_APPROVE` is unused); the dental selftest warns that `visit_type` has no `HOOK_CHECK` (they live in the shared engine `selftest.py`).
- **Mock mode only;** urgent-symptom detection is a keyword list.
- **Commit messages that cannot be changed without rewriting history:** `43e5fed` says 203 tests (it was 204); `b6c7800` says the drift test covers "all three agents" (it covers the two generated agents against `boilerplate/`).
- **Windows path length:** the longest tracked path is 110 characters (`_bmad-output/planning-artifacts/architecture/…/reviews/review-adversarial.md`). A checkout whose root folder is longer than about 150 characters fails with "Filename too long" unless `git config core.longpaths true` is set. The current folder (`C:/Users/Omer Bassan/Desktop/Projects/AgentStudio`, 50 characters) is fine. The fresh-checkout proof of `c9a56d8` was run with `core.longpaths` enabled: 287 platform, 12 plugin, three selftests PASSED.
- **Dangling references:** `ARCHITECTURE.md` was deleted (DL-027); the finalized voice-era documents under `_bmad-output/specs/spec-alta-agent-studio/` still list it as a companion. Recover with `git show b6c7800:ARCHITECTURE.md`.

## 5. Next task

Day 6 per the plan, in cut order: the C7 live-model mode and its Markdown report (needs the user's key), then C8. See [LATEST-HANDOFF.md](LATEST-HANDOFF.md).
