---
title: 'Story 1.12: Credential-free CI on a clean checkout'
type: 'chore'
created: '2026-10-17'
status: 'done'
route: 'dispatch'
baseline_commit: 'f925409d88eda0f6d081856414494904dd9eac41'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** "Green" has only ever meant green in one Windows working tree; nothing runs the suite on a fresh clone, so line-ending, platform and missing-file faults reach the repository unseen (register D-05, CLAUDE.md clean-checkout rule).

**Approach:** One GitHub Actions workflow runs the full credential-free verification set on every push and pull request, on a fresh checkout, on Linux (LF) and Windows (CRLF), with no secret referenced and the model key blanked; a repository test pins those properties so the workflow cannot drift into holding a secret or a live call.

## Boundaries & Constraints

**Always:** run exactly the Story 1.12 command set — `python -m pytest studio/tests -q`, `python -m studio scenarios --today 2026-10-13`, `python -m pytest builder_platform/tests -q`, `python -m pytest claude_plugin/tests -q`, and `python selftest.py` in `boilerplate/`, `Generated_Agents/BassanBrewerySDR/`, `Generated_Agents/BrightSmileDental/`; install from the pinned `requirements.txt`; `OPENAI_API_KEY` and `OPENAI_BASE_URL` set to empty at job level; `permissions: contents: read`; every step's failure fails the job.

**Never:** reference `secrets.*`; pass `--live`; skip, `continue-on-error`, or `|| true` any verification step; edit engine files, product code, or existing tests to make CI pass (a CI-only failure is a finding, reported, not patched around); leave the deliberately failing branch on the remote.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Healthy push | push to `studio/v1` | both matrix jobs green | N/A |
| Failing test | push of throwaway branch with one failing test | job fails, red run recorded | branch deleted after the run is recorded |
| Secret creeps in | workflow edited to reference `secrets.` or `--live` | `test_ci_workflow.py` fails locally and in CI | N/A |
| Key in runner env | a runner-level `OPENAI_API_KEY` | job-level empty value overrides it; conftests also pop it | N/A |

</frozen-after-approval>

## Code Map

- `requirements.txt` -- single pinned dependency set (pytest included); reuse as-is.
- `studio/__main__.py:41-49,163-164` -- live mode needs `--live` plus key/base URL plus model; without `--live` the deterministic agent runs (0 model calls).
- `studio/tests/conftest.py:13`, `builder_platform/tests/conftest.py:22` -- pop credentials before import; CI relies on, does not change, them.
- `builder_platform/tests/test_efficiency_round.py:42-44` -- byte budgets measured as checked out; LF is smaller than CRLF, so Linux cannot exceed them.
- Clean-worktree baseline (Windows, 2026-10-17, HEAD f925409): studio 126 passed; scenarios 10/10, 0 model calls; builder_platform 332 passed; claude_plugin 12 passed; three selftests exit 0.
- No `.github/` exists; no `gh` CLI locally; repo is public, so run status is readable from the unauthenticated Actions API.

## Tasks & Acceptance

**Execution:**
- [x] `.github/workflows/ci.yml` -- create: triggers `push` (all branches) and `pull_request`; matrix `ubuntu-latest`, `windows-latest`, `fail-fast: false`; Python 3.12 with pip cache; one step per verification command; job-level blank credentials; read-only permissions -- the CI itself.
- [x] `studio/tests/test_ci_workflow.py` -- create: assert the workflow has no `secrets.`, no `--live`, blanks both credentials, contains every required command and no `continue-on-error`/`|| true` -- makes AC2 an enforced invariant rather than a comment.
- [x] Remote proof -- push `studio/v1`, record the green run URL; push throwaway branch `ci/deliberate-failure` adding one failing test, record the red run URL, delete the remote branch.
- [x] `docs/next-phase-proposals/IMPLEMENTATION-STATE.md` -- record both run URLs as Story 1.12 evidence.

**Acceptance Criteria:**
- Given a clean clone with line endings as checked out, when CI runs on Linux and Windows, then all seven commands pass with no model credential.
- Given the CI configuration, when inspected (and by `test_ci_workflow.py`), then it holds no secret and cannot make a live model call.
- Given a failing test on a branch, when pushed, then the job fails.

## Implementation Notes

- Implementation subagent committed `339fb32` and pushed `studio/v1` plus throwaway `ci/deliberate-failure` during step 3 (the workflow reserves remote ops for later; the user had authorized commits and pushes for this sprint on 2026-10-17). Green run 39045384600 (`339fb32`), red run 39045399062 (`ab2b4c3`, failed at "studio tests"); throwaway branch deleted.
- Review patches (triage rows 1–8): pin test grew from 8 to 12 tests, each weakness mutation-checked; `ANTHROPIC_API_KEY` blanked; an "Assert checkout line endings" step observes CRLF on Windows and LF on Linux instead of assuming it.
- Correction to Design Notes: the developer's main working tree is LF (`git ls-files --eol` shows `w/lf`) despite global `core.autocrlf=true`; a fresh Windows checkout is CRLF (probe printed `win32 CRLF` in a new worktree). The CRLF coverage CI adds is therefore a fresh-clone property, not a mirror of the main tree.
- Local: `python -m pytest studio/tests -q` 138 passed (credential-free).

## Spec Change Log

## Review Triage Log

| # | Finding | Verdict | Evidence / route |
|---|---------|---------|------------------|
| 1 | `if:` on a step skips it while pin tests pass | medium | No `if:` check in test file; patch |
| 2 | Trigger narrowing (`branches: [main]`, `paths:`) passes | medium | Test only checks keys exist; patch |
| 3 | `STUDIO_SKIP_MUTATION` could silently skip 12 mutation proofs | medium | `test_checks_are_not_vacuous.py:46` honours it; patch |
| 4 | Masking via `\|\| :`, `set +e`, `exit 0` not rejected | low | Trivial regex extension; patch |
| 5 | `vars.*`, step-level-only blanks, job-level write permission undetected | low | Textual checks too narrow; trivial extension; patch |
| 6 | `ANTHROPIC_API_KEY` not blanked | low | `builder_platform/app.py:185` reads it; one env line; patch |
| 7 | Windows CRLF checkout assumed, not observed (doc says VERIFIED) | medium | No `.gitattributes`, no autocrlf step; patch with an observing step |
| 8 | IMPLEMENTATION-STATE:37 "Not yet done: clean-checkout run" contradicts new block | low | Direct text correction; patch. Header lines 3–4/14 are a dated historical revision — false |
| 9 | Sprint status in-progress vs doc "closes D-05" | false | Status advances at step 5; in-progress is correct mid-review |
| 10 | Red run unreproducible after branch deletion | low | Run record remains in the Actions API; procedure is in the spec; rejected (low, not everyday) |
| 11 | "Dev deps separated" row is false | medium | Pre-existing row (§3.6:245), not this story; defer |
| 12 | Only Python 3.12 tested | false | `requirements.txt` pins one tested set; 3.12 is the one supported interpreter |
| 13 | Actions pinned by tag, not SHA | low | Read-only token, no secrets; rejected (adds maintenance for negligible risk here) |
| 14 | Push + PR double runs, no concurrency group | low | Public repo, free minutes; rejected |
| 15 | Selftest regex depends on key order | low | Fails loudly if reordered, never passes falsely; rejected |
| 16 | `studio scenarios` exits 0 when no scenario files exist | medium | Pre-existing `studio/__main__.py:85,112`; defer |

## Design Notes

Two runners rather than one: the developer works on Windows with `core.autocrlf=true` (CRLF), and a Linux runner checks out LF; byte budgets and file parsing have broken on line endings before. Windows-only would miss LF faults, Linux-only would miss the developer's own platform. Decided by Claude under the user's delegation.

## Verification

**Commands:**
- `python -m pytest studio/tests/test_ci_workflow.py -q` -- expected: pass.
- Actions API `GET /repos/OmerBassan/Alta-agent-studio/actions/runs?branch=studio/v1` -- expected: latest run `conclusion: success`; same for `ci/deliberate-failure` -- expected: `failure`.
