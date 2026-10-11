# DECISION-LOG — Agent Studio seven-day hardening

Chronological. Status is one of `APPROVED`, `PROPOSED`, `OPEN`, `SUPERSEDED`. **`APPROVED` means the user said so in a quoted message.** Anything a session or the assistant recommended, and nobody confirmed, is `PROPOSED`.

User messages are cited by label. Their dates were not recorded, so the order below is conversation order; commit dates are exact.

| Label | Opening of the user message |
| --- | --- |
| MSG-1 | "Agent Studio — Scope Reassessment and Implementation Reset" |
| MSG-2 | "We have a major scope problem, and I want to reset the implementation planning." |
| MSG-3 | "This is a strong, concrete plan… Approved in principle. Please start Day 1" |
| MSG-4 | "Day 1 is complete and committed. Before starting Day 2, I want to move to a fresh Claude Code session…" |
| MSG-5 | "We have a synchronization problem between Claude Code sessions and the ChatGPT Project…" |
| MSG-6 | "Continue the Agent Studio seven-day hardening sprint. ## Confirmed decisions…" |
| MSG-7 | "You are the authorized sole writer for this working tree. Proceed with the smallest fix for the undeclared-tool execution gap…" |
| MSG-8 | "Good progress. Do not stage or commit anything yet. Before approval, investigate one specific inconsistency…" |
| MSG-9 | "gap #3: files made anywhere as early as 11/10 are approved to commit / gap #4 reshow me the proposed / gap #5 … tell me your opinion / gap#6 and 7 cant see problem / gap #8 all bmad files are ok to be comited / day 1 handoff is to be removed / … UPDATE CLAUDE.md AND ABOUT ARCHITECTURE.md IF WE DONT USE IT THROW IT / clear false comments / about the dead code, distinguish between dead code and test code" |

---

## Before the sprint

### DL-001 · APPROVED · The planning set is reference material
**Decision:** The finalized Brief, PRD, Architecture Spine and UX spines are reference points. Some describe future platform requirements rather than necessary V1 scope.
**Rationale:** The user wants to keep that work without implementing all of it.
**Source:** MSG-1: "treat the finalized Architecture Spine and UX spines as important reference points, while recognizing that some decisions describe future platform requirements rather than necessary V1 implementation scope."

### DL-002 · APPROVED · The product thesis and the portfolio objective are unchanged
**Decision:** An adaptive, business-configurable agent remains the direction. The aim is a portfolio project that demonstrates sound adaptive-agent engineering, not sales performance or a production SaaS.
**Source:** MSG-1: "This is **not** a change to the core product thesis." MSG-2: "The objective remains unchanged."

### DL-003 · SUPERSEDED · Platform-scale reassessment and the 37–55-day scope audit
**Decision:** MSG-1 asked for an implement-now / preserve / defer classification and a reduced platform scope. The assistant answered with `_bmad-output/planning-artifacts/scope/scope-audit-AgentStudio-2026-10-10.md`, estimating 37–55 working days.
**Rationale:** The user rejected the estimate: "That is not an acceptable adjustment to the original scope. It is a different project."
**Source:** MSG-2. Superseded by DL-004. The audit file remains on disk, untracked, and is **not** the plan.
**Carried forward:** MSG-1 also said "Do not weaken foundational properties such as tenant isolation, bounded authority, version consistency, or reliable tool execution merely to simplify the implementation." MSG-2 did not restate this and did not withdraw it; the sprint's own authorization and verification work is consistent with it.

### DL-023 · OPEN · Questions D1 and D2 from the scope audit were never answered
**Question:** D1: should the model propose the next step (the platform authorizes and executes), or should the platform select it? D2: should V1 test the runtime claim rather than the Builder-elicitation claim?
**Status:** The user moved to the seven-day reset instead of answering. The sprint does not need either answer, because it does not implement the model-in-charge loop (DL-007). Left open for any later phase.
**Source:** scope audit §1; MSG-2.

---

## The sprint

### DL-004 · APPROVED · Seven-working-day cap, hardening only
**Decision:** The total remaining work, including further planning, code, tests, debugging and documentation, fits seven developer working days. Treat the repository as the starting point: hardening and targeted improvement, not a greenfield rewrite. No Epics & Stories, no rewriting of finalized planning documents, no scope amendments. If the plan does not fit, reduce scope, not time.
**Source:** MSG-2: "The total remaining work must fit within seven developer working days, including any further planning…", "This is a hardening and targeted-improvement exercise, not a greenfield rewrite.", "If it does not fit, reduce the proposed scope rather than increasing the time budget."

### DL-005 · APPROVED · Sprint priorities
**Decision:** (1) preserve and strengthen the existing implementation; (2) demonstrate adaptive behaviour across at least two meaningfully different business contexts on the same runtime; (3) prioritize decision-making abstractions, bounded authority, tool execution and verification, and a small evaluation suite; (4) reuse existing infrastructure, interfaces, storage and tests; (5) defer complete platform subsystems, production hardening, elaborate operator UX and speculative extension mechanisms.
**Source:** MSG-2, "priorities".

### DL-006 · APPROVED · The seven-day plan, in principle
**Decision:** The assistant's plan (changes C1–C8, a day-by-day schedule, tests, exclusions, accepted risks) was approved in principle, with the clarifications in DL-007 to DL-010. It is reproduced in `SPRINT-CONTRACT.md`.
**Rationale:** "Approved in principle" does not confirm every detail individually; only the clarifications were stated as changes.
**Source:** MSG-3: "This is a strong, concrete plan… **Approved in principle. Please start Day 1**, with the following clarifications incorporated." The plan text itself exists only in the earlier assistant message, not in any file.

### DL-007 · APPROVED · Architecture boundary
**Decision:** Harden the existing graph-based agent; do not implement the Architecture Spine's model-in-charge loop; do not claim the sprint realizes it. Demonstrate configurable behaviour across contexts, model decisions at defined points, execution-time authority enforcement, outcome verification, traceability and cross-business evaluation. Document the distinction and remaining limitation without triggering an architecture redesign.
**Source:** MSG-3 clarification 1. Restated in MSG-4.

### DL-008 · APPROVED · Execution authorization must be genuinely binding (C3)
**Decision:** Confirmation and operator-approval records are Core-owned and separate from model-controlled payload fields. Bind each to the conversation or episode, business/agent, effective configuration version, flow/tool and canonicalized action arguments. Not reusable for a different payload, conversation, or later execution. Targeted tests for payload mutation, approval replay, cross-conversation reuse, and forgery through model output. The authority declaration must express required gates unambiguously for an action with several properties (for example state-changing and liability-bearing).
**Source:** MSG-3 clarification 2. Restated in MSG-4, items 5 and 7.

### DL-009 · APPROVED · Fingerprint reflects the configuration actually used; C4 verification rule
**Decision:** The run fingerprint is a deterministic content fingerprint of the effective business configuration and must change when that configuration changes. Git revision and working-tree status may be recorded for context only. State-changing flows are not verified unless their declared read-back verification passes; where verification is required but unavailable, fail the structural preflight or return an explicit unverified outcome.
**Source:** MSG-3 clarification 3.

### DL-010 · APPROVED · Cut order
**Decision:** If implementation slips, drop the correction-demo script first, then the live-model report. Prioritize execution-boundary enforcement, outcome verification, deterministic tests and a reliable end-to-end demonstration.
**Source:** MSG-3: "Preserve the stated fallback order if implementation slips…"

### DL-011 · APPROVED · Carry-forward decisions
**Decision:** Seven-working-day total scope; retain the existing LangGraph runtime; the three-business demonstration; do not resume broader BMAD planning; do not implement the full model-in-charge loop during this iteration.
**Source:** MSG-4, item 4 (the user's own list of carry-forward decisions).

### DL-012 · APPROVED · Day 2 investigation and adversarial tests
**Decision:** First verify the actual graph path when an action needs both user confirmation and operator approval, inspecting the implementation rather than trusting the graph description. Required tests: modified payload, replayed approval, cross-conversation reuse, model-forged approval; keep platform authorization records distinct from model-controlled data.
**Source:** MSG-4, items 6 and 7. Delivered in `589c3a0` (see CURRENT-STATE).

---

## Implementation choices made inside sessions (no explicit user approval)

### DL-013 · APPROVED (was PROPOSED) · Verifiers are a registry keyed by tool, not a `Flow.verify` field
**Resolution (MSG-9):** "gap#6 and 7 cant see problem" — gap #6 listed DL-013, DL-014, DL-016 and DL-017. Recorded as approval; the user may still object.
**Decision:** Read-back is registered in `tools.VERIFIERS` rather than as a `Flow.verify(args, result)` field as the plan stated.
**Rationale (commit):** "Flow is defined per agent in config.py, and config.py cannot import tools.py (tools -> compaction -> config)."
**Source:** commit `c7a86b4`; `boilerplate/tools.py` (`VERIFIERS`). Differs from the plan text. Consistent with DL-009's intent ("declared read-back verification"), but the user did not choose this mechanism.

### DL-014 · APPROVED (was PROPOSED) · An unverified outcome gets a fixed reply, no retry, and a handoff request
**Resolution (MSG-9):** "gap#6 and 7 cant see problem" — gap #6 listed DL-013, DL-014, DL-016 and DL-017. Recorded as approval; the user may still object.
**Decision:** On `unverified`, the agent replies with `UNVERIFIED_TEXT`, does not re-pend the action for retry, and sets `handoff_requested`. Tool calls and read-backs are time-bounded by `TOOL_TIMEOUT_S` and `VERIFY_TIMEOUT_S`.
**Source:** commit `c7a86b4`. DL-009 requires an explicit unverified outcome; the handoff-and-no-retry behaviour is a session choice.

### DL-015 · PROPOSED · A handoff keyword bypasses yes/no resolution at a confirmation gate
**Decision:** `intent_detect_node` now skips yes/no resolution when the message carries a `human_handoff` keyword; the message is classified and the handoff node clears the pending action. It can only withhold consent, never grant it.
**Rationale:** Found while testing the dental agent: "okay, but my face is swollen" had booked the visit, and five escalation phrasings were treated as consent in the Acme template.
**Source:** commit `b6c7800`; `test_escalation_at_the_confirmation_gate_is_not_consent`. It changes shared engine code, so it affects all three agents.

### DL-016 · APPROVED (was PROPOSED) · Legacy `confirm=` / `hitl=` booleans stay as spellings of the property set
**Resolution (MSG-9):** "gap#6 and 7 cant see problem" — gap #6 listed DL-013, DL-014, DL-016 and DL-017. Recorded as approval; the user may still object.
**Decision:** The booleans are folded into the same property set, and a `Flow` without a `properties` field still starts and is gated through them.
**Rationale (commit):** an agent whose `config.py` predated the field crashed at `build_pipeline`.
**Source:** commits `589c3a0`, `4e7a874`; test `test_flow_without_properties_field_still_starts_and_is_gated`.

### DL-017 · APPROVED (was PROPOSED) · The authorization ledger is in-process; approvals do not survive a restart
**Resolution (MSG-9):** "gap#6 and 7 cant see problem" — gap #6 listed DL-013, DL-014, DL-016 and DL-017. Recorded as approval; the user may still object.
**Decision:** Records live in memory outside `AgentState`. A run resumed from a durable checkpointer is refused (fail closed).
**Source:** commit `4e7a874`; `graph.py` docstring. A limitation consistent with the exclusion of durable episode storage (DL-006), but not separately acknowledged by the user.

---

## Open questions

### DL-018 · APPROVED (was OPEN) · Which instruction wins when `CLAUDE.md` conflicts with the sprint
**Resolution:** the user's own Day 3 handoff message said "Where CLAUDE.md conflicts with this handoff, this handoff wins", and MSG-9 said "UPDATE CLAUDE.md". `CLAUDE.md` now states the precedence: sprint documents win for sprint work; the voice rules govern the voice runtime surfaces.
**Question:** The project `CLAUDE.md` says "Voice-only" and describes a Vapi voice product. The sprint is channel-agnostic hardening in mock mode. A fresh session mistook the sprint for a voice task.
**Status:** The assistant proposed "where CLAUDE.md conflicts with this handoff, this handoff wins" in an earlier handoff text. The user did not approve or reject it. `CLAUDE.md` also carries the user's uncommitted edits, so it must not be edited without instruction.
**Source:** `CLAUDE.md` (working tree); the conversation turn asking to tighten the handoff.

### DL-019 · APPROVED (was OPEN) · Sprint-day accounting and C6 acceptance
**Resolution (MSG-6):** "Four of seven working days have been consumed." "C6 (the dental-practice agent) is accepted as complete." "C7, the deterministic cross-business evaluation suite, is the next priority."
**Question:** How many of the seven working days are consumed, and is C6 (dental) accepted as done?
**Evidence:** The commits implementing C1 to C6 are dated 2026-10-11, 12:41 to 19:51. The repository shows effort landing, not days spent. No message states days consumed or accepts C6.
**Source:** `git log`; absence of any such message.

### DL-020 · APPROVED (was OPEN) · Concurrent Claude Code sessions are editing the same branch
**Resolution (MSG-7):** "You are the authorized sole writer for this working tree." The authorized session is the one that made commits `589c3a0`, `4e7a874`, `c7a86b4` and `b6c7800` (the "second writer" this entry originally described); a peer session, `agentstudio-8c`, wrote the four sprint documents and was idle when C7 started.
**Question:** Which session is the single writer?
**Evidence:** During this inspection, `boilerplate/nodes.py` changed (mtime 19:49:05) and a commit (`b6c7800`, 19:51:24) appeared that this session did not make; HEAD moved from `c7a86b4`.
**Status:** No coordination rule is recorded. The handoff asks the next session to confirm a single writer before editing.
**Source:** `git log`, file mtimes, CURRENT-STATE section on the second writer.

### DL-021 · APPROVED (was OPEN) · The source documents are untracked
**Resolution (MSG-9):** "files made anywhere as early as 11/10 are approved to commit" (the four sprint documents) and "all bmad files are ok to be comited" (`_bmad/`, `_bmad-output/`, `.claude/skills/bmad-*`). `.claude/settings.local.json` and `.claude/scheduled_tasks.lock` stay out: they are local state and already gitignored.
**Question:** Should the Brief, PRD, Architecture Spine, UX spines, and these four sprint documents be committed?
**Evidence:** `git ls-files _bmad-output` returns 0 files; the sprint documents are new untracked files. Per the stated hierarchy these documents outrank handoffs, yet they have no version history.
**Source:** `git ls-files`, `git status`.

---

## This documentation task

### DL-022 · APPROVED · Source-of-truth hierarchy and this documentation task
**Decision:** (1) latest explicitly approved scope and decisions govern what we may do; (2) the repository and test results govern claims about implementation; (3) `brief.md` describes product intent; (4) `ARCHITECTURE-SPINE.md` is future-state and does not authorize the full model-in-charge loop; (5) existing handoffs and summaries are historical reports. Four documents are to be produced without implementing features, committing, or staging.
**Source:** MSG-5. Recorded last because it was stated last; it governs how all entries above are read.

---

## C7 session

### DL-024 · APPROVED · A tool no flow declares is refused before it runs
**Decision:** `tool_exec` refuses any tool that no flow in `config.FLOWS` declares, registered or not, with a typed `platform_error` ("tool … is not declared by any flow"), before the registry lookup and before any execution.
**Rationale:** Before the change a forged payload ran such tools: the brewery's leftover `issue_refund` (a money action, owned by no brewery flow) and `send_email` in Acme and dental (owned by no flow there). Gates were derived from the owning flow, so a tool with no owner had no gates. This contradicted SPRINT-CONTRACT §4 ("an undeclared tool is refused").
**Source:** MSG-7: "Proceed with the smallest fix for the undeclared-tool execution gap, first proving it with a failing regression test." Implemented in `boilerplate/nodes.py` `_authorize` (re-copied to both agents); regression test `test_forged_payload_for_an_undeclared_tool_is_refused` (3 cases, all failed before the change); not yet committed.

### DL-025 · APPROVED (was PROPOSED) · C7 scenario format and runner
**Resolution (MSG-9):** "gap#6 and 7 cant see problem" — gap #7 was DL-025.
**Decision:** One JSON file per business in `builder_platform/tests/eval_scenarios/` (no new dependency), each scenario a list of turns plus per-turn expectations on trace properties (intent, tools run, pending confirmation, operator pause, verification outcome, refusal kind, handoff, session-fact keys), never reply wording. Scenarios whose id starts with `X` send identical input to every business. Runner: `builder_platform/tests/test_cross_business_eval.py`, reusing `agent_driver.py` (one subprocess per business). The driver gained a `{"resume": {"approved": bool}}` step that echoes the offer id the interrupt showed.
**Status:** The design was stated before implementation in the C7 session and the user said to "continue with C7"; the format itself was not separately approved. After DL-026 the brewery gained scenario B4 (its authorized email path) and the X3 scenario id became `X3-same-forged-send-email` in all three files.
**Source:** this session; files listed in CURRENT-STATE.

### DL-026 · PROPOSED · Every declared tool runs only as the active flow's action
**Decision:** `nodes._authorize` checks that the payload's tool belongs to the active flow (`config.FLOWS[intent].tool == tool`) for EVERY declared tool, before the gate lookup. Previously that check ran only for gated tools, so an ungated tool ran in any turn. Authorization (may this tool run as this turn's action) is now separate from approval (must a human also say yes: the `confirm` / `hitl` gates).
**Evidence:** Before the change the brewery's ungated `send_email` (flow `send_followup`) ran from a forged payload in a greeting turn, with arguments its flow never produced; regression test `test_forged_payload_for_an_ungated_tool_outside_its_flow_is_refused` failed ("an ungated tool ran outside its flow") and passes after. The authorized path still runs (C7 scenario B4).
**Status:** MSG-8 said "Make the smallest correction only if the contract or execution boundary requires it". The judgement that the execution boundary required it is this session's; the user has not confirmed it.
**Not closed:** a forged payload sent on a turn whose message classifies as the ungated flow ("send me an email") still runs with forged arguments, because `route_by_intent` sends a pending payload straight to `tool_exec`, skipping `think` and its slot validation, and ungated flows have no platform record to check. Closing it needs a platform record for every execution, not only gated ones (a design change; not made).
**Source:** MSG-8; uncommitted change in `boilerplate/nodes.py` and both agent copies.

---

## Gap-closing session (MSG-9)

### DL-027 · APPROVED · Remove `DAY-1-HANDOFF.md` and `ARCHITECTURE.md`; update `CLAUDE.md`
**Decision:** `DAY-1-HANDOFF.md` deleted (stale, never committed). `ARCHITECTURE.md` deleted: no code, README, DEMO or setup file referenced it; only the voice-era planning documents (`_bmad-output/specs/spec-alta-agent-studio/SPEC.md` and `brownfield.md`, `extract-brownfield.md`, `.memlog.md`) list it, and those finalized documents now point at a file that exists only in git history (`git show b6c7800:ARCHITECTURE.md`). The user's uncommitted edit to it (test count 161 → 183) is dropped with it. `CLAUDE.md` rewritten on top of the user's edits: sprint precedence (DL-018), the full engine-file list, the two generated agents, verification commands without hardcoded counts, and the clean-checkout rule.
**Source:** MSG-9: "day 1 handoff is to be removed", "remove stale handoff files", "UPDATE CLAUDE.md AND ABOUT ARCHITECTURE.md IF WE DONT USE IT THROW IT".

### DL-028 · APPROVED · Correct comments and README text that no longer told the truth
**Decision:** `nodes._authorize` docstring and the `tool_exec` line of the `nodes.py` module docstring now name all three refusals (undeclared, not the active flow, missing gate record); `authz.py`'s header separates authorization from approval; `tools.py` `issue_refund` no longer says `Flow(hitl=True)`; the dental config no longer calls itself "this Acme demo"; `boilerplate/README.md` and the brewery's README no longer claim a `--session` flag or an operator console, and state the `offer_id` resume and in-process approvals.
**Source:** MSG-9: "clear false comments".

### DL-029 · PROPOSED · Remove dead code; keep test and simulation code
**Decision:** Removed from the brewery's `tools.py`: `lookup_order`, `book_appointment`, `issue_refund` (pre-Day-3 copies, no flow declares them, no read-back) with their registry entries, `_BRANCH_LABELS`, `_stable_hash`, and the then-unused `hashlib` import; from the dental `tools.py`: `_stable_hash` and `hashlib`. Kept on purpose: `send_email` (the template marks it permanently available for any email flow a builder adds; refused until declared), `retrieve_full_result` (engine compaction tool), and the simulation/test support (`SimulatedBackend`, `VERIFIERS`, `verify_*`, `SIMULATED_FAILURE`, `agent_driver.py`). Scenario B2 now says the refund tool is not registered at all, and the brewery file asserts `registry_lacks` for the three removed tools.
**Status:** MSG-9 asked to "distinguish between dead code and test code"; removing the dead part is this session's judgement.

### DL-030 · PROPOSED · Raise the `step4_build.md` byte budget 6_450 → 6_475
**Decision:** On a clean checkout (`core.autocrlf=true`, so CRLF) `step4_build.md` is 6_462 bytes and `test_step_files_exist_within_budget[step4_build.md]` failed: the sprint added `episode_trace.py` (Day 1, landing exactly on 6_450) and `authz.py` (Day 2, +12) to its write-blocked engine list. The suite was green only in a working tree with LF endings. The budget was raised by the size of that new required surface, following the test's own rule ("Raise a budget only for new REQUIRED surface") and its `agent_sandbox.py` precedent; making the test ignore line endings was rejected because it would loosen every budget by about 100 bytes.
**Status:** the user was shown the gap but did not choose a fix; this is the session's choice.

