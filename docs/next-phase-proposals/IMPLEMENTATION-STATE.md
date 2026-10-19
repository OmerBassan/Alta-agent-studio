# IMPLEMENTATION-STATE — Agent Studio

**PROPOSAL, for review. Nothing committed. No code and no original planning document was changed.**
Revision 2, 2026-10-13. Verified against branch `harden/seven-day`, HEAD `dcc2860` (`dcc286032ed20ee0c211a0fd790ecb23f7b8cf80`), working tree clean apart from this folder (`git status --short` → `?? docs/next-phase-proposals/`).

IDs (V-, C-, B-, S-, A-, K-, E-, D-, CX-, U-, Q-) refer to [BMAD-DECISION-REGISTER.md](BMAD-DECISION-REGISTER.md). Where this document and the repository disagree, the repository wins.

Classes: **VERIFIED IMPLEMENTED** · **PARTIALLY IMPLEMENTED** · **NOT IMPLEMENTED** · **UNKNOWN / NEEDS VERIFICATION** · **DEFERRED BY DECISION**.

---

## 0. Latest phase report — Phase 2 (grounded answers, Epic 2), 2026-10-19

**Status:** Phase 2 delivered. Sprint 1 (Epic 1, Stories 1.9–1.12) closed on 2026-10-18; Sprint 2 (Epic 2, Stories 2.1–2.6) closed on 2026-10-19. T9–T12 were approved by the user on 2026-10-19. No model tokens were spent in Phase 2: every story is verified credential-free, as the user asked.

### What was built

| Story | Delivered |
| --- | --- |
| 2.1 Pin source material | At episode start the Core pins each source's sections under its content hash (`source_snapshots`) and the compiled specification with source texts stripped (`spec_snapshots`). Both are written once. After an edit and a restart, a resumed episode is rebuilt from the store and served the text it started on. |
| 2.2 Reconstruct from the record | `studio/core/reconstruct.py`: every reply with the items its claims cited (text, source, version, locator), and every retrieval with its query and results, from the store alone, identical after the business folder is deleted. A reply that cites nothing says so. |
| 2.3 Context assembly | `STUDIO_CONTEXT_ASSEMBLY` = `standing` (default) or `on_demand`. It is platform configuration validated at startup and pinned per episode. On demand, the boundary carries the specification projection plus a titles-only index, and a retrieval issues references for exactly what it returns. Retrieval sits behind a `Retriever` port (`studio/knowledge/`), with the lexical default. |
| 2.4 Precedence | The same heading in different text is a conflict. The specification outranks every source, and between sources the lower declared precedence wins. Superseded material is marked on retrieval and never offered for citing, and citing it is refused (`source_superseded`). Equal precedence is a blocking validation finding. |
| 2.5 Fresh reads | `depends_on = {read, max_age_seconds}` on an effect contract. A missing or stale basis is a typed refusal, and the Core never reads on the Agent's behalf. The read-to-effect gap is recorded on the effect's evidence. Dental and brewery bookings now depend on a fresh availability read. |
| 2.6 Garden centre | `studio/businesses/garden-centre/`: specification, guarantee terms, care guides and scenarios, with no Python. Engine-leak entry P3: no leak (fixture wiring). |

### Verification (2026-10-19, credential-free)

- `python -m pytest studio/tests -q`: all pass, including 17 mutation proofs (5 new in this sprint). CI runs on Linux and Windows on every push.
- `python -m studio scenarios --today 2026-10-13`: 15/15 (dental 6, brewery 4, garden centre 5), in both `standing` and `on_demand` modes.

### U3: the read-to-effect gap (Story 2.5)

Credential-free, 3 runs of every scenario. Six effects carried a basis. Every one came **one turn** after its read and about **0 s** later. The seconds measure nothing yet, because scripted turns arrive instantly. The distribution that answers U3 needs real or live traffic. `python -m studio gate-report <dir>` prints it from any recorded run.

### Open, and why

- **Story 2.3, AC4, the live comparison of the two context modes.** It needs a model-spend approval; the user chose no spend for Phase 2. The default stays `standing` until then. The gate report already gives calls, latency, pass rate, retrieval misses and mode per run. Known confounds: retrieved text appears twice on demand, and references only grow over a long episode.
- **The live proof-gate figures (PROOF-GATE.md, 2026-10-17) predate Story 2.5.** Booking now needs an availability read first, so live calls per turn are expected to rise for booking scenarios. The credential-free decision count went from 1.38 to 1.85 per turn by design. Re-measure with the 2.3 comparison.
- **Deferred items** (`_bmad-output/implementation-artifacts/deferred-work.md`):
  - the compiler version is not part of the pinned version (Story 3.1);
  - a capability's adapter is not checked as connected at startup;
  - an operator's approval does not resume its episode;
  - blame stated in prose is not caught deterministically (T6, measured in Epic 4).

### System Frame (global manual §1.7), Phase 2

| # | Answer |
| --- | --- |
| Failure | Adapters keep their timeouts (`adapter_timeout_s`). A missing or stale basis is a typed refusal, not a hidden read. An unreadable pinned snapshot raises `UnknownTenant`; it never falls back to today's text. |
| Fallback | A degraded result is visible to the caller: a superseded item is marked, an unresolved citation says why, a reply that cites nothing says so, and a retrieval miss is counted. |
| Concurrency | Single-writer SQLite store (T3), with a per-process conversation lock. Pinning runs inside the episode-creation transaction. |
| Scalability | The growing dimension is source size. In standing mode every item is in view on every turn; on-demand exists to bound that, and its cost is to be measured (2.3 AC4). Snapshots grow by one copy per edited version (retention deferred with AD-25). |
| Observability | Every retrieval, basis gap, supersession and pin is on the episode record under one episode id. Reconstruction reads it back. |
| Config & secrets | `STUDIO_CONTEXT_ASSEMBLY` is validated at startup by `Settings` and by the Core. No new secret. Adapter connectedness is not yet validated at startup (deferred). |
| Deployment | No new dependency. CI on Linux and Windows. |
| Durable state | Snapshots are `INSERT OR IGNORE`, content-addressed and never rewritten. Everything else is unchanged from Phase 1 (transactions, crash reconciliation from Story 1.11). |

### Next step

Phase 3 (Epics 3–4: versions, promotion, rollback, evaluation) needs the user's go-ahead. Its gates are D7 (counterfactual replay, OPEN) and D14 and D15 (PROPOSED, wording applied). Live-spend items waiting on an approval: the 2.3 comparison run.

## 0a. Earlier phase report — Phase 1 (runtime foundation + proof gate), 2026-10-14

**Status: Phase 1 delivered, except the proof gate's two live axes (needs approval to spend).** Nothing committed.

### What was built (new package `studio/`; no existing file outside it changed except `CLAUDE.md`)

| Area | Files | Requirements now verified (BMAD Stories 1.1–1.8, `_bmad-output/planning-artifacts/epics.md`) |
| --- | --- | --- |
| Business Specification | `studio/spec/` — schema for all 17 expression areas, TOML loader with content-addressed versions, platform validation suite, Core compiler into three projections | FR13◐ FR14 FR15 FR16 FR18 FR19 FR21◐ FR22◐ FR23 FR24 FR51 FR52◐ FR54 FR58 FR109 |
| Core | `studio/core/` — closed 7-kind taxonomy, authorization of every kind, journal, SQLite episode store (tenant on every row, idempotency `UNIQUE`, evidence in the effect's transaction), strict consent, guards, two exits, terminal notice, disclosure, suspension, operator approval, waivers, late results, purge | FR38–FR50, FR53, FR55, FR56, FR60–FR72, FR74, FR75, FR77, FR83, FR86, FR87, FR97, FR105–FR107, FR111, FR112, NFR3, NFR4, NFR18 |
| Agent boundary | `studio/agent/` — provider-agnostic `/v1` model port (plain HTTP, no vendor SDK), live model agent, credential-free deterministic agent, scripted agent | AD-14◐ (live run pending), FR41, NFR12 |
| Channel | `studio/channels/harness.py` — scenario harness as the first channel adapter | FR83, FR85◐ |
| Businesses | `studio/businesses/dental/`, `studio/businesses/brewery/` (Brief's events exemplar) — specification + guide + scenarios, no Python | FR89 log started: business 2 needed zero Core changes |
| Entry point | `python -m studio` with `validate`, `scenarios`, `chat` | NFR17 (config validated at startup) |

### Verification (re-run in full on 2026-10-14, after the last test was added; HEAD `dcc2860`, tree = `M CLAUDE.md`, `?? docs/next-phase-proposals/`, `?? studio/`)

| Command | Result |
| --- | --- |
| `python -m pytest studio/tests -q` | **126 passed** in 117 s, including the 12 mutation proofs (each disables one Core check in a temporary copy and requires the suite to fail) |
| `python -m studio scenarios --today 2026-10-13` | **10/10 PASS** (dental D1–D6, brewery B1–B4), credential-free, 0 model calls each |
| `python -m pytest builder_platform/tests -q` (legacy) | **332 passed**, 7 warnings, 156 s. Unchanged by Phase 1 |
| `python -m pytest claude_plugin/tests -q` (legacy) | **12 passed**, 1 warning |
| `python selftest.py` in `boilerplate/`, `BassanBrewerySDR/`, `BrightSmileDental/` | all three **exit 0** |

Not yet done: a clean-checkout run (`git worktree add`), which needs `studio/` committed first. *(Done 2026-10-17 by Story 1.12: fresh-checkout CI on Linux and Windows; see the Story 1.12 block below.)*

**Re-verified 2026-10-14 (second session, before any planning edit), same HEAD and tree:** `studio/tests` 126 passed, all 12 mutation proofs run and passing (checked individually, none skipped); `python -m studio scenarios --today 2026-10-13` 10/10 PASS with 0 model calls; `builder_platform/tests` 332 passed; `claude_plugin/tests` 12 passed; the three `selftest.py` exit 0; `git status` unchanged by the runs. No application code was changed in that session.

### Story 1.12 — credential-free CI on a clean checkout (2026-10-17, commit `339fb32`)

`.github/workflows/ci.yml` runs the seven commands above on every push and pull request, on a fresh checkout, on `ubuntu-latest` (LF) and `windows-latest` (CRLF), with `OPENAI_API_KEY`/`OPENAI_BASE_URL` blank at job level, `permissions: contents: read`, no `secrets.*` and no `--live`. `studio/tests/test_ci_workflow.py` pins those properties (8 tests).

| Evidence | Result |
| --- | --- |
| Green run, `studio/v1` @ `339fb32` | [run 39045384600](https://github.com/OmerBassan/Alta-agent-studio/actions/runs/39045384600) — `success`; both jobs, every step green |
| Red run, throwaway `ci/deliberate-failure` @ `ab2b4c3` (one `assert False` test) | [run 39045399062](https://github.com/OmerBassan/Alta-agent-studio/actions/runs/39045399062) — `failure`; both jobs failed at the `studio tests` step, later steps skipped. Branch deleted from the remote after the run was recorded |

This closes D-05 and the clean-checkout gap noted above: the full set now passes on a fresh clone on both line-ending platforms with no model credential. No product code, engine file or existing test was changed to make CI pass.

### Found and fixed during the phase

1. Agent recorded a bare "yes" as the patient's name (agent bug; Core cannot catch a wrongly established fact). Fixed; pinned by a test.
2. Two Core checks were untested until mutation showed it. Isolating tests added; both in the permanent mutation suite.
3. Scenario D6 expected escalation for a Sunday booking; the Brief requires a refusal citing the rule. Expectation corrected; denials now carry the rule id.
4. Three Core defects found by review before testing: two first messages could create two episodes (lock moved to the conversation); a repeat of a verified effect was refused instead of "already done"; resolving one goal closed the episode while another was active.

### Not done in Phase 1, and why

- **Proof-gate axes 3–4 (model calls, latency)** — need one live run; command in `PROOF-GATE.md`. Asking before any spend is a standing user rule.
- FR42 is ◐: the five guardrails are enforced at the level of typed claims and requests; prose that asserts a fact without a claim is measured (NFR6), not blocked.
- FR64 is ◐: a pending episode survives a new process (tested); a crash *mid-turn* is not yet tested.
- FR57: no real credentials exist yet; the sentinel-credential test lands with the first real adapter (Phase 6, Story 8.4).
- FR60 is ◐, not ✓ (corrected 2026-10-14): a declared deadline is stored on a pending episode, but nothing turns its expiry into the external event FR60 requires (Story 1.10).
- FR71: inline resolution validation is delivered but **provisional** until the proof gate validates it (Spine Deferred; Story 1.9).

### Phase 2 status (2026-10-14): planned, **not authorized**

The user asked that Phase 2 not start until they reconcile it with the full BMAD implementation plan. Findings P2-F1–F5 from the Phase 1 code, the proposed steps and the **proposed (not approved)** choices T9–T12 are in NEXT-PHASE-PLAN §3.1. The largest: retrieval is nearly vacuous today (all source text is in the agent's view every turn), and FR37 breaks after a restart that follows a knowledge edit. The live proof-gate timing is unresolved: the recommendation is to run it after Phase 2, but PRD §12 places the gate in front of E4–E9 (Phase 2 is E6), so it needs the user's ruling.

### Next step

**Current (2026-10-14, revision 4 of the program):** Sprint 1 — Phase 1 close-out — Stories 1.12, 1.9, 1.10, 1.11, with 9.1 and 9.8 in parallel (NEXT-PHASE-PLAN §2.3). Blocking decisions: D1 (spend on the live gate run) and D3 (commit and push). Epic 2 (knowledge) starts after the 1.9 verdict.

### Superseded next step (as written at the end of Phase 1; kept for the record)

**Phase 2 — knowledge and grounding** (program §3): version-pinned sources with declared precedence, retrieval as a decided action with Core-issued provenance per retrieved item, the two knowledge tiers, freshness per contract, and the **garden-centre** exemplar. Start by reading `studio/core/harness.py` `_retrieve` (the minimal lexical retrieval Phase 1 shipped) and `studio/spec/compile.py` `_items`. *(Superseded: Phase 2 now depends on the proof-gate verdict and on T9–T12, gates D1, D2, D4–D6.)* Phase 3 will need one: counterfactual replay in V1 (PRD O11) — recommendation yes.

**User actions that can start any time:** approve the live proof-gate run; 2–3 operator conversations (FR94); a real business for Phase 7 (FR92).

---

## 1. Evidence gathered this session

### 1.1 Commands run (new results, not historical)

| Check | Result |
| --- | --- |
| `git status` · `git branch --show-current` · `git rev-parse HEAD` · `git log` | branch `harden/seven-day`; HEAD `dcc2860` "Archive sprint-seven-day documents to docs/sprint-seven-day/"; clean. `CURRENT-STATE.md`'s header still says HEAD `6fa4af3`; the later commit is the archive move, which `LATEST-HANDOFF.md` acknowledges. |
| `python -m pytest builder_platform/tests -q` (mock mode) | **332 passed**, 7 warnings, 143.7 s. Matches CS §1. |
| `python -m pytest builder_platform/tests --collect-only -q` | **332 tests collected** — the count is tests, not assertions. |
| `python -m pytest claude_plugin/tests -q` | **12 passed**. Matches CS §1. |
| `python selftest.py` in `boilerplate/`, `Generated_Agents/BassanBrewerySDR/`, `Generated_Agents/BrightSmileDental/` | all three **exit 0**. |
| `git status --short` after the runs | only `?? docs/next-phase-proposals/`. The test runs left nothing behind; no user change was disturbed. |
| `python --version` | 3.12.7 — meets the Spine's Python 3.12+ floor. |

No model was called. The platform suite blanks `OPENAI_API_KEY` before any test module loads (`builder_platform/tests/conftest.py`, DL-040), and I made no live request. **Cost incurred: zero.**

**Taken from `CURRENT-STATE.md` and not re-run** — historical, and labelled as such everywhere below: the clean-CRLF-checkout run · `correction_loop.py` (C8) · both LIVE runs (22/22 and 13/13 at 3/3 on `gpt-6-luna`, ≈US$0.03 of the US$0.50 ceiling).

### 1.2 Code facts established this session

| # | Fact | How |
| --- | --- | --- |
| 1 | **The runtime is 15 nodes with 8 conditional-edge calls.** | `grep -c "add_node(" boilerplate/graph.py` → 15; node names enumerated; `grep -c "add_conditional_edges"` → 8. This is the shape the Spine and PRD call "the existing fifteen-node system". |
| 2 | **`nodes.py` is 2 047 lines across 68 top-level functions.** Attribution by function span: voice/director/objection/tie-down ≈ **236 lines (11 %)** (`_director` 90, `_objection_gate` 36, `_tiedown` 30, `_update_summary` 29, `_objection_ctx` 19, `_speak_value` 17, `_stage_satisfied` 15); `planner_node`/`plan_step_node`/`enrichment_node` ≈ **144 lines (7 %)**. Largest functions: `intent_detect_node` 172, `think_node` 114, `validator_node` 111, `tool_exec_node` 104. | Parsed `def`/`async def` spans. **Approximate** — it attributes whole functions and does not count voice constants, call sites elsewhere, or coupling. |
| 3 | **A text-only cut leaves roughly 1 650 lines in `nodes.py`.** | (2) minus both buckets. Bears directly on U2 — see §5. |
| 4 | **"tenant" appears in no engine or platform module.** | `git grep -il tenant -- boilerplate builder_platform claude_plugin` → one unrelated hit in `claude_plugin/hooks/guard_engine_files.py`. Only `agent_id` exists, inside the authz binding. |
| 5 | **An ordered stage agenda is live in one shipped agent.** `CALL_ARC` is non-empty in `Generated_Agents/BassanBrewerySDR/config.py:237`; empty (`= ()`) in `boilerplate/config.py:275` and `Generated_Agents/BrightSmileDental/config.py:286`. | Read all three. This is a sequencing construct of exactly the kind FR18/FR24 forbid in a specification (CX-02). |
| 6 | **The stall detector does not set `handoff_requested`.** It replaces the reply with `config.STALL_TEXT`, "whose escape phrase routes to `human_handoff`" on a later turn (`nodes.py:1990-2002`). The flag is set in only two places: the handoff node (`:673`) and the unverified-outcome path (`:1443`). | Read the region and grepped every occurrence. Contradicts PRD §7.4's "stall detector with a wired handoff" as an *earned* guarantee (CX-03). |
| 7 | **Nothing outside the engine consumes `handoff_requested` except the test driver.** | `git grep -n handoff_requested -- builder_platform claude_plugin` → `builder_platform/tests/agent_driver.py:30,160` plus recorded values inside live-report JSON. The voice runtime does not read it. Escalation therefore arrives nowhere in code today (C-06). |
| 8 | **Dental holds its authoritative facts as a prompt string.** `FACTS` at `Generated_Agents/BrightSmileDental/config.py:43`; `RETRIEVAL_INTENTS = ()` at `:136`; the `knowledge/` loader exists (`:65`–`:127`) but the directory is absent, so `_UPLOADED_DOCS` is empty. | Read. Resolves revision 1's U2. |
| 9 | **Dental's urgent-symptom handling is an intent keyword list, not a guard.** `INTENT_KEYWORDS["human_handoff"]` (`config.py:764-776`) holds ~22 phrases ranked above every task intent; the comment says the fast router scans them "as its interruption guard (an other-intent keyword hit forces the LLM path)". | Read. Confirms A-13 PARTIAL: ranking inside intent classification, with no binding verdict, no halt and no terminal notice. |
| 10 | **`tools.VERIFIERS` holds two verifiers** — `book_appointment`, `issue_refund` (`tools.py:247-250`) — plus the engine's `retrieve_full_result` registered separately. | Read. |
| 11 | **`/health` cannot detect a configuration whose first real request would fail.** It returns `{"status": "ok", "active_sessions": …, "runtime": runtime_supervisor.status()}` (`app.py:829-832`) with no probe. | Read. Resolves revision 1's U3 for the platform endpoint (the per-agent selftest is a separate, real gate). |
| 12 | **`RESUME_APPROVE` is defined and handled but never scripted.** `boilerplate/selftest.py:67` defines it, `:120` handles it, and no selftest `SCRIPT` sends it. | Grepped. Confirms CS §4: the operator gate is never exercised by a selftest. |
| 13 | **The deleted `ARCHITECTURE.md` was recovered and read in full** (`git show b6c7800:ARCHITECTURE.md`, 6 950 bytes). | See §1.3. |

### 1.3 A correction to the record: the "measured rejection" was not a measurement

`m-spec` 51 recommends against replacing LangGraph with an agent-loop SDK because it "would reintroduce model-driven routing (**the measured rejection** in ARCHITECTURE.md section 1)". I recovered that file. Section 1 contains a *reasoned* comparison table — "Cost per turn: 0 tokens, 0 calls" vs "+1 model round-trip"; "Latency ~0 ms" vs "**+200–800 ms on the reply path**" — and the latency figure is an estimate carrying no measurement. The same voice spec's own improvement audit records that **no instrumentation existed to measure it**: "zero latency or token instrumentation exists — no `perf_counter`/`monotonic` timing on any model call, and `vapi_adapter.py:200` hardcodes `usage` to zeros" (`m-spec` 44).

Three further things about that argument, all from the recovered file:

- It is an argument about an **outbound SDR leading a call agenda** ("An outbound SDR must *lead*"), which V1 excludes.
- It was made under a **voice latency budget**, which PRD §1.3 explicitly retires for an asynchronous channel — naming the superseded principle rather than reversing it silently.
- The file itself states `CALL_ARC = ()` makes the director "a documented no-op" for inbound agents, so the mechanism being defended is inactive in the inbound case.

This does not make model-in-charge correct. It means the strongest-sounding objection to the approved direction (A-01) is not evidence, and the proof gate (A-18) is the first place real numbers will exist on either side.

---

## 2. Part A — the sprint (a completed, bounded engineering workstream)

The seven-day sprint hardened the **existing** runtime in mock mode. It was never the product plan: DL-001 makes the planning set reference material, and SC §6 states "the planning artifacts describe a larger product than this iteration builds".

| ID | Delivered | Class | Evidence |
| --- | --- | --- | --- |
| C1 | Brewery engine re-synced; drift test across both generated agents against `boilerplate/` | **VERIFIED IMPLEMENTED** | `test_engine_drift.py` inside today's 332; three selftests exit 0 |
| C5 | Per-turn trace + effective-configuration fingerprint | **VERIFIED IMPLEMENTED** as a library; **PARTIAL** in use | `episode_trace.py` read in full; `graph._traced`; `test_episode_trace.py`. `TraceWriter` is called **only** from `agent_sandbox.py` — the platform runtime persists nothing |
| C2+C3 | Declared action properties; execution-time authorization bound to conversation, agent, config fingerprint, flow, tool and canonical args; one-time records | **VERIFIED IMPLEMENTED** | `authz.py` (header read in full), `nodes._authorize`; `test_execution_authz.py`. Refuses an undeclared tool, a tool that is not the active flow's, and a gated tool without a matching record |
| C4 | Outcome verification by read-back; an unverified outcome is never reported as success | **VERIFIED IMPLEMENTED** for tool effects | `tools.VERIFIERS` (two verifiers), `execution_validator_node`; unverified → fixed reply, no retry, `handoff_requested: True` (`nodes.py:1443`) |
| C6 | Third business (dental front desk) through the copy-and-edit path | **VERIFIED IMPLEMENTED** | `Generated_Agents/BrightSmileDental`, `test_dental_agent.py`, selftest exit 0 |
| C7 | Cross-business evaluation, deterministic and live | **VERIFIED IMPLEMENTED** (deterministic, re-run today); live results historical | `test_cross_business_eval.py`, 27 tests inside the 332; 16 scenarios / 22 business runs; reports under `builder_platform/tests/live_reports/` |
| C8 | Correction-loop demonstration | **Reported done; not re-run** | `correction_loop.py`; `test_correction_loop.py` is inside the 332 |
| — | Test-suite `.env` guard (DL-040); strict consent at the yes/no gate (DL-015) | **VERIFIED IMPLEMENTED** | `conftest.py`; `nodes._bare_answer`; tests inside the 332 |
| — | README section "How this agent adapts and stays bounded", limitations in two halves | Done (read in CS, not re-read) | root `README.md` |

### 2.1 What the sprint proves, and what it does not

It supports the **bounded-authority** half of V-02 and the **evidence-of-effect** rule (A-05) for tool effects, on three authored businesses, with a regression net. It does not exercise: the model-in-charge loop (A-01) · the closed request taxonomy (A-02) · a specification artifact (S-01) · the Builder (B-01) · provenance (A-06) · tenant identity (A-11) · durable episodes (A-09) · the divergence loop (E-03) · any real traffic (E-06).

### 2.2 Sprint limitations carried forward (CS §4, re-read not re-derived)

- A forged payload on a matching turn of an **ungated** flow runs with forged arguments (DL-026). Closing it needs a platform record for *every* execution — a capability-contract design change (K-04).
- Approvals are **in-process** and lost on restart (DL-017).
- The configuration fingerprint **depends on the install folder** (`_KNOWLEDGE_DIR` is absolute and hashed). Comparisons hold within one folder only — which matters the moment versions (S-06) are compared across machines or CI.
- Native structured parse is rejected on every intent and think call (117 of 117); each costs one rejected request before JSON mode succeeds (DL-037).
- A structured call whose `parsed` is `None` is returned as `None`, and the node then fails outside its fallback. Pre-existing, unreachable in mock mode.
- No CI (D-05).

---

## 3. Part B — product capabilities against the approved direction

### 3.1 Builder and operator surface

| Capability | Source | Class | Evidence |
| --- | --- | --- | --- |
| Adaptive elicitation Builder (FR1–7, 99, 100, 104, 117) | B-00, B-01 | **NOT IMPLEMENTED** | The repo's Builder is the voice-SDR builder: `SKILL.md` is `voice-agent-architect`; `skill_steps/step1_discovery.md` prescribes six fixed phases, `alta:ask` cards and "walk phases 2–5 IN ORDER"; output is Python domain files. The opposite of FR3's "MUST NOT present a fixed questionnaire". |
| Reusable builder plumbing — write policy, ship-gate-as-subprocess, Agent SDK driver, second front door | PRD §7.4 "reusable largely as-is" | **VERIFIED IMPLEMENTED** | `builder_core.py` (`ENGINE_FILES`), `claude_plugin/` (12 tests pass), `builder_platform/storage/` (SQLite: `sessions`, `built_agents`) |
| Understanding document (five sections over EX1–17, four item states, "Not established") | B-04 | **NOT IMPLEMENTED** | `static/index.html` (78 KB) contains zero occurrences of Understanding / Activity / divergence |
| Correction diff → new version | B-03 | **NOT IMPLEMENTED** (product); **PARTIAL** analogue | C8 is a scripted config fix on a temporary copy |
| Validation result + operator approval at go-live | S-07, S-08, B-10 | **NOT IMPLEMENTED** | Analogue: the per-agent selftest gate |
| Activity / divergence list / interaction viewer | B-09, B-13 | **NOT IMPLEMENTED** | — |
| **Episode list, search or operator-visible identifier** | U1 (adversarial F3.1, critical, unfixed) | **NOT IMPLEMENTED**, and **not designed** | An `episode_id` exists in the sandbox trace only; nothing surfaces it. See Q2 |
| Suspend / stop-actions-only / status line | B-12 | **NOT IMPLEMENTED** | No suspend flag anywhere (`git grep -i suspend` returns only LangGraph interrupt wording). AUDIT §3.7 sizes it at "twenty lines" |
| Connect-mailbox surface; escalation email | B-11, C-06 | **NOT IMPLEMENTED** | `handoff_requested` is set but consumed only by the test driver (§1.2 #7) |
| Accessibility floor, responsive panes, closed vocabulary | B-07, B-08 | **NOT IMPLEMENTED** (nothing to apply it to) | DSN tokens exist as design only; `mockups/` lags the spines in four recorded ways |

### 3.2 Business specification

| Capability | Class | Evidence |
| --- | --- | --- |
| One diffable artifact; context, capability surface and policy **compiled** from it | **PARTIALLY IMPLEMENTED** | Three hand-maintained Python files plus `knowledge/`; the sprint deliberately kept this (DL-006). No compiler — so AD-4's failure mode (the Agent believing it may do what the Core will refuse) is reachable today |
| EX1–EX17 expression surface | **PARTIALLY IMPLEMENTED** | `Flow` (`config.py:151`): tool, slots, `properties`, validators, `confirm_template`, `enrich`. Identity in `prompts.py`. Authoritative facts in `FACTS` (dental) and `DOCS`/`knowledge/`. **Not located: EX3, EX5, EX11–EX13, EX15–EX17** — not located is not the same as proven absent |
| Authority classes, separately gated | **VERIFIED IMPLEMENTED** for two of three | `authz.PROPERTY_GATES`: `state_changing`→confirm, `liability`→hitl; a misdeclared flow fails at startup. "Informational" is implicit; cause-vs-fault (FR17) absent |
| Typed goals and obligations; waivers | **PARTIALLY IMPLEMENTED** | Per-flow slots act as per-action obligations in typed state. No goal set, no obligation/diagnostic split, no waiver |
| No-ordering rule enforced | **NOT IMPLEMENTED**, and contradicted | `CALL_ARC` non-empty in the brewery agent (§1.2 #5); turn order is graph-fixed everywhere |
| Immutable promoted versions, pinning, rollback | **NOT IMPLEMENTED** (registry); **PARTIAL** (identity) | The fingerprint is bound into every authorization record and each trace turn; folder-dependent |
| One platform-owned, spec-derived validation gate incl. FR23 | **PARTIALLY IMPLEMENTED** | Selftest + startup preflight + drift test. Not spec-derived; no granted-but-always-denied check; no business criteria |
| Evaluation criteria inside the specification | **NOT IMPLEMENTED** as specified | Scenarios sit in `builder_platform/tests/eval_scenarios/` |

### 3.3 Knowledge subsystem

| Capability | Class | Evidence |
| --- | --- | --- |
| Retrieval over business material | **VERIFIED IMPLEMENTED** (basic) | `config.RETRIEVER` term-overlap scorer over chunked `knowledge/`; agentic-RAG subgraph with iteration bound and confidence floor. Dental runs with no corpus at all (§1.2 #8) |
| Version-pinned sources | **PARTIALLY IMPLEMENTED** | Per-file sha256 inside the config fingerprint |
| Source precedence on conflict | **NOT IMPLEMENTED** | — |
| Core-issued provenance; refusal of unissued or cross-tenant references before egress | **NOT IMPLEMENTED** | `git grep -i provenance`: no hits in engine or platform |
| Two knowledge tiers marked in evidence | **NOT IMPLEMENTED** | Not distinguished. Dental's authoritative tier is a prompt string, which is the tier that must be grounded and pinned |
| Faithfulness evaluation (NFR6) | **DEFERRED BY DECISION** | Threshold unset (O5); no evaluator FR exists (U5/F6.5) |

### 3.4 Runtime architecture

| Capability | Class | Evidence |
| --- | --- | --- |
| Model-in-charge Agent; Core never selects the next step | **NOT IMPLEMENTED** · **DEFERRED** for the sprint only (DL-007) | 15 nodes, 8 conditional-edge calls. The decision is APPROVED and user-binding (A-01) |
| Closed seven-kind request taxonomy, all authorized **and journaled** | **NOT IMPLEMENTED** | Per-node trace exists; only tool execution is authorized |
| Core-binding constraints at execution | **VERIFIED IMPLEMENTED** for tool execution | `test_execution_authz.py`: forged payload refused three ways; payload mutation, replay and cross-conversation reuse covered |
| Evidence only from the Core; read-back verification | **VERIFIED IMPLEMENTED** for tool effects | `VERIFIERS`, `execution_validator_node` |
| Resolution envelope + validation against evidence | **NOT IMPLEMENTED** | — |
| Denial classification | **PARTIALLY IMPLEMENTED** | `business_refusal` and `platform_error` exist (`authz.py:73-74`); **`spec_defect` and the backlog do not** — the class that drives the improvement loop |
| Guards before goal recognition; safety halt; terminal notice | **PARTIALLY IMPLEMENTED** | Urgent handling is intent-ranking by keyword (§1.2 #9); no halt, no notice |
| Loop bound; stall detector with a **wired** handoff | **PARTIALLY IMPLEMENTED — weaker than the PRD states** | Budget and threshold exist; the stall path never sets the handoff flag (§1.2 #6) |
| Tenant identity on every record; cross-tenant rejected | **NOT IMPLEMENTED** | "tenant" absent from all engine and platform modules (§1.2 #4) |
| Tenant-scoped idempotency keys | **NOT IMPLEMENTED** | — |
| Episode lifecycle, resume, late results, one writer | **PARTIALLY IMPLEMENTED** | `thread_id` + `MemorySaver`; an `episode_id` in the sandbox trace; no lifecycle, no late results |
| Durable steps; survives process failure | **NOT IMPLEMENTED** | In-process approvals (DL-017); the sqlite checkpointer is a commented-out optional requirement |
| Provider-agnostic runtime boundary | **PARTIALLY IMPLEMENTED** | Env-configured `/v1` client, blank-key mock mode, per-call records, timeouts: VERIFIED. LangGraph types cross every layer; `openai.AsyncOpenAI` imported as the compatible transport (`llm_client.py:50`) |
| Process isolation between deployed agents | **VERIFIED IMPLEMENTED** | Subprocess-per-agent |
| Proof gate against the 15-node system | **NOT IMPLEMENTED** | Never started. Reference-side numbers exist for three of nine axes (CS §3b/3c) |
| Email channel adapter; FR114 hazards; disclosure | **NOT IMPLEMENTED** · sprint-**DEFERRED** | Only the Vapi voice adapter exists |

### 3.5 Evaluation, evidence, feedback

| Capability | Class | Evidence |
| --- | --- | --- |
| Deterministic cross-business suite on trace properties | **VERIFIED IMPLEMENTED** | 27 tests inside today's 332; shown able to fail (CS §3) |
| Live repeated runs with a report; per-call tokens, latency, path, degraded flag | **VERIFIED IMPLEMENTED** (tooling tested today; results historical) | `live_eval.py`; `model_calls` on trace entries |
| Durable per-episode evidence store incl. cost, under one correlation id | **PARTIALLY IMPLEMENTED** | Fields exist per trace entry; sandbox-only writer; no store; cost only in `live_eval.py` |
| Divergence log / backlog; correction records; sampled adjudication | **NOT IMPLEMENTED** | — |
| Counterfactual replay | **PARTIALLY IMPLEMENTED** (analogue) | C8 re-runs scenarios after a config fix |
| Engine-leak log, resolution strain, setup effort, validity floor | **NOT IMPLEMENTED** | No leak log exists. One unclassified data point: DL-015 surfaced while building the third business and changed shared engine code |
| Usefulness test on real traffic; one real business; operator conversations | **NOT IMPLEMENTED** · sprint-**DEFERRED** | Ranked first in V-04 and entirely unstarted |

### 3.6 Deployment and operations

| Capability | Class | Evidence |
| --- | --- | --- |
| CI running the suite | **VERIFIED IMPLEMENTED** (2026-10-17) | `.github/workflows/ci.yml`, Linux + Windows; green run 39045384600, red run 39045399062 (§0, Story 1.12) |
| Startup validation; health check proving a real request | **PARTIALLY IMPLEMENTED** | Startup validators exist; `/health` has no probe (§1.2 #11) |
| Pinned dependencies, dev separated | **VERIFIED IMPLEMENTED** | Both requirements files pinned |
| Clean-checkout reproducibility (CRLF) | **VERIFIED IMPLEMENTED** (2026-10-17, `339fb32`) | Fresh-checkout CI on LF (Linux) and CRLF (Windows), every push |
| Tenancy topology, hosting, retention executor | **DEFERRED BY DECISION** | PRD §7.2–7.3 |

---

## 4. Reusable assets, with what each is good for

| Asset | Use in the next phases |
| --- | --- |
| `authz.py` bindings (thread, agent, fingerprint, flow, tool, canonical args) + its 49 tests | The closest thing in the repo to a Policy Enforcement Point. Template for Core-owned authorization records (AD-2/AD-3), and the test set transfers almost directly |
| `tools.SimulatedBackend`, `VERIFIERS`, `SIMULATED_FAILURE` | Simulated systems of record with failure injection and read-back — AUDIT §6 calls this "essential", because without it "verified outcome" means "the function returned" |
| `eval_scenarios/*.json` + `agent_driver.run_agent` (one subprocess per agent) | The same scenarios and trace-property assertions can drive a **new** runtime, which is what makes the proof-gate comparison cheap |
| `llm_client.py` (env-driven `/v1`, mock mode, per-call records, timeouts, `OPENAI_TOKEN_PARAM`, `OPENAI_REASONING_EFFORT`) | The "thin interface over the existing client" the AUDIT recommends keeping instead of adopting a framework early |
| `episode_trace.py` — fingerprint + `TraceWriter` | Seed of the episode record and of version identity; fix the folder dependence when versions become comparable |
| `correction_loop.py`, `live_eval.py` | Replay-style verification and repeated-run reporting, already written |
| `builder_core.py`, `claude_plugin/`, `integrations/` | Builder plumbing, a second front door, and copy-adapt recipes |
| Model compatibility settled for `gpt-6-luna` at `max_completion_tokens` + reasoning effort `none` (DL-034, DL-037) | Live mode works for one model at one setting; no re-probing needed to run a live comparison |
| `_bmad-output/implementation-artifacts/` (BMAD-configured, does not exist yet) | Where BMAD expects implementation artifacts, if the next phase uses the method's own folders |

---

## 5. What remains unverified, and the cheapest safe way to verify it

Ordered by how much a phase depends on it. None of these needs a model call.

| # | Claim still unverified | Cheapest safe verification | Cost |
| --- | --- | --- | --- |
| **V1** | **U2 — is "evolve rather than discard" falsified?** §1.2 #3 answers the line-count half decisively (≈1 650 lines remain against a 1 000-line falsifier) but not the **coupling** half, which was the other half of the stated criterion. | Do not strip anything. Measure coupling statically: count cross-imports and shared-state reads among the surviving node functions, and count how many distinct `AgentState` keys each writes. A `grep`-level script over `nodes.py` and `schemas.py`, no edits. | ~1 hour, read-only |
| **V2** | **U3 — do side-effect-gating reads cluster at episode end, or occur per turn?** FR35's affordability rests on the former; nobody measured it. | Count, per scenario in the existing 22 business runs, how many tool calls occur and at which turn index, from the traces the deterministic suite already produces. No new instrumentation and no model. | ~1 hour, read-only |
| **V3** | Which EX areas (EX3, EX5, EX11–EX13, EX15–EX17) have any representation in the three agents' configs. | One pass over the three `config.py` and `prompts.py` files with the EX list in hand; write the answer into the schema work (O7). | ~1 hour |
| **V4** | Whether a credential can reach agent state, a trace or a prompt (AD-24/NFR11). | Grep the state schema and trace writer for env-derived values; run one mock-mode sandbox turn with a sentinel value in the environment and search the written JSONL for it. | ~30 min, no cost |
| **V5** | Concurrency: does the platform serialize concurrent turns on one thread (AD-13)? | Read `runtime.py`'s locking around `graph.ainvoke`; no execution needed. | ~30 min |
| **V6** | Clean-CRLF-checkout green at HEAD `dcc2860`. | `git -c core.longpaths=true worktree add` on HEAD, run the three commands, remove the worktree. CS records the difference from the last verified commit as Markdown-only, so this is confirmation rather than discovery. | ~5 min of attention, ~3 min of runtime |
| **V7** | C8 (`correction_loop.py`) at this HEAD. | Run it — mock mode, ~30 s, exit code is the result. | negligible |
| **V8** | Whether the selftest can detect a half-set or invalid live configuration (D-02). | Set `OPENAI_TOKEN_PARAM` to an invalid value and an empty-but-set `OPENAI_API_KEY`, then run one agent's selftest and record what it says. Mock-mode only; no request leaves the machine. | ~30 min |
| **V9** | The live results in CS §3b/3c at this HEAD. | **Do not re-run.** The scenarios and expectations are byte-identical to the reported run, the user ran it themselves, and it costs money. Re-run only if a code change touches the engine, and then only with explicit approval and the US$0.50 ceiling restated (DL-035). | — |

**Not verifiable by inspection, by nature:** anything about real operators (E-06, A4) and anything about real inbound mail (C-02, FR114). Those need the human track, not a test.

---

## 6. Operational half of the limitations

This document describes a system; it adds none, so the global manual's System Frame is **n/a** for the document itself. For the *existing* system, the eight questions stand as follows at this HEAD — and any phase that produces a runnable system must answer all eight before writing code:

1. **Failure** — provider calls carry per-call timeouts and a client cap; tool and verify calls are time-bounded. No retry policy is documented.
2. **Fallback** — a degraded model call is flagged on the trace entry (DL-036) and an unverified effect produces a typed outcome, never a success message. But the trace is written only by the sandbox, so in the platform path the flag reaches no caller.
3. **Concurrency** — subprocess-per-agent is enforced; per-thread serialization is **UNVERIFIED** (V5).
4. **Scalability** — the dimension that grows is episodes per business; unmeasured, and no store exists to grow.
5. **Observability** — a correlation id exists only in the sandbox trace; there is no way for a person to report an incident and have anyone locate it.
6. **Config and secrets** — validated at startup; `/health` cannot prove a real request (§1.2 #11).
7. **Deployment** — no CI; a green run in this working tree is not proof for a fresh clone (DL-030).
8. **Durable state** — JSONL append-only with one `write()` per line, so a crash truncates at most the last line; **unbounded**, with no rotation or eviction, and no recovery path.
