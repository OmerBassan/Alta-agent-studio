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

### DL-015 · APPROVED, REPLACED BY STRICT CONSENT · A handoff keyword bypasses yes/no resolution at a confirmation gate
**Resolution (Day 7 session, 2026-10-12):** the user chose option A, strict consent (only a bare yes or no answers the confirmation; anything else is classified normally and the confirmation stays pending), plus the user's own suggestion: guide the user to answer yes or no. User: "DL 015 option A and read my suggestion"; "why not just yes and no? and telling the agent to guide the user to answer with yes no only. or just paste a "YES/NO" label at the end of the question". The design was put to the user and approved: "Yes proceed toward completion". **Implemented:** `nodes._bare_answer` resolves the gate only when the whole message is answer words (yes, yeah, sure, ok, go ahead, sounds good… / no, nope, no thanks, cancel, wait…, plus please/thanks); anything else is classified normally, and a detour's reply ends "Please answer yes or no:" plus the question. Decline is strict too, so "no, get me a manager" reaches the handoff instead of a plain decline; the keyword bypass described below was deleted as redundant. The `(yes/no)` label already ends the Acme and dental questions; the brewery's voice question gets the spoken re-ask, not a printed label. Engine `boilerplate/nodes.py`, re-copied to both agents. Regression tests: four "yes plus something else" replies and the dental "okay, but my cheek is really puffy" (all booked before), the re-ask, five bare yeses, five bare noes; the five escalation phrasings of `test_escalation_at_the_confirmation_gate_is_not_consent` still hand off. Known cost: a longer yes ("yes, Tuesday works") is asked again.
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

### DL-026 · APPROVED (was PROPOSED) · Every declared tool runs only as the active flow's action
**Resolution (Day 7 session, 2026-10-12):** "dl 026 ok".
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

### DL-029 · APPROVED (was PROPOSED) · Remove dead code; keep test and simulation code
**Resolution (Day 7 session, 2026-10-12):** "DL 029 approve"; "about dead code. fry it up. delete it". The removal was already committed in `d9fecb7`. Standing rule from the user for any further deletion: "refer for approval before delteting".
**Decision:** Removed from the brewery's `tools.py`: `lookup_order`, `book_appointment`, `issue_refund` (pre-Day-3 copies, no flow declares them, no read-back) with their registry entries, `_BRANCH_LABELS`, `_stable_hash`, and the then-unused `hashlib` import; from the dental `tools.py`: `_stable_hash` and `hashlib`. Kept on purpose: `send_email` (the template marks it permanently available for any email flow a builder adds; refused until declared), `retrieve_full_result` (engine compaction tool), and the simulation/test support (`SimulatedBackend`, `VERIFIERS`, `verify_*`, `SIMULATED_FAILURE`, `agent_driver.py`). Scenario B2 now says the refund tool is not registered at all, and the brewery file asserts `registry_lacks` for the three removed tools.
**Status:** MSG-9 asked to "distinguish between dead code and test code"; removing the dead part is this session's judgement.

### DL-030 · SUPERSEDED · Raise the `step4_build.md` byte budget 6_450 → 6_475
**Resolution (Day 7 session, 2026-10-12):** trimmed instead of raised: "cant we just shorten the files?", "dl 030trim if possible". One sentence about `agent_sandbox.py` in `skill_steps/step4_build.md` was shortened (meaning and command kept): 6_462 → 6_389 bytes as checked out (CRLF). The budget is back at 6_450.
**Decision:** On a clean checkout (`core.autocrlf=true`, so CRLF) `step4_build.md` is 6_462 bytes and `test_step_files_exist_within_budget[step4_build.md]` failed: the sprint added `episode_trace.py` (Day 1, landing exactly on 6_450) and `authz.py` (Day 2, +12) to its write-blocked engine list. The suite was green only in a working tree with LF endings. The budget was raised by the size of that new required surface, following the test's own rule ("Raise a budget only for new REQUIRED surface") and its `agent_sandbox.py` precedent; making the test ignore line endings was rejected because it would loosen every budget by about 100 bytes.
**Status:** the user was shown the gap but did not choose a fix; this is the session's choice.


---

## Model-selection session (2026-10-12)

User messages in this session, in order: MSG-10 "we have enough days, focus on the work rather then the deadline / … I believe in a better model investigation fitst…"; MSG-11 "this project is a brownfield… the architecture spine is the more reliable ground truth for us"; MSG-12 "I will run the research with an external tool…"; MSG-13 "It is ok if the research does not tie a claim to a source…"; MSG-14 "the whole candidate table will be attached… a spend ceiling would be 50 cents."; MSG-15 "luna nd haiku are going to use the same amount of tokens approx. and cost the same we can go with luna".

### DL-031 · APPROVED · No day accounting; focus on the work
**Decision:** The remaining sprint work is not planned against a day count.
**Source:** MSG-10: "we have enough days, focus on the work rather then the deadline".

### DL-032 · APPROVED (research only) · The Architecture Spine is the ground truth for model and platform questions
**Decision:** For the model research, requirements come from the Architecture Spine and the PRD; the brownfield code is the reference implementation, and its constraints are a compatibility check for the sprint's live run only. Recorded in `MODEL-RESEARCH-BRIEF.md`.
**Source:** MSG-11: "this project is a brownfield. therefore, it has some misconseptions. some contradictions… the architecture spine is the more reliable ground truth for us".
**Clarified (Day 7 session):** the Spine is not claimed to be the highest ground truth; it is the up-to-date design, unlike the stale voice-era code. DL-022's order stands for sprint work; where the voice-era code and the Spine disagree on intent, the Spine is the current reference. User: "i dont know if it is the highest ground truth really, but at least i could say it was upto date and not like the stale code of voice agents", then "spine approved" to this wording.

### DL-033 · APPROVED · The external research report is accepted as reliable
**Decision:** `Agent Studio model research.pdf` (external tool, 2026-10-12) is accepted although it does not tie claims to sources and calls itself a provisional draft. The candidate table's truncated columns (P1, P2, P3, P6) were supplied by the user in MSG-14.
**Source:** MSG-13: "It is ok if the research does not tie a claim to a source. it is a reliable research." "It is ok that we never mentioned hebrew, we could ignore it anyway".

### DL-034 · APPROVED · The live evaluation model is `gpt-6-luna`, on all three tiers
**Decision:** "Luna 6" means OpenAI `gpt-6-luna`. Claude Haiku 5.5 (`claude-haiku-5-5`) was considered, and an engine change for it was acceptable on the condition that it be "more efficient and perform as good as luna 6". It was dropped because the two are expected to use about the same tokens at the same price. No Haiku-specific change was made.
**Source:** MSG-13: "Luna 6 and gpt-6-luna is the same", "claude-haiku-5-5 is the one i talked about of course. I am ok with an engine change if needed, so Haiku 5 5 could fit. only if it is more efficient and perform as good as luna 6", "I get your propose to take gpt 6 luna but i want it to not be too pricey." MSG-15: "luna nd haiku are going to use the same amount of tokens approx. and cost the same we can go with luna".

### DL-035 · APPROVED · Spend ceiling for the live evaluation: US$0.50
**Decision:** The whole live evaluation, compatibility probe included, spends at most US$0.50. `live_eval.py --max-cost` defaults to 0.50.
**Source:** MSG-14: "a spend ceiling would be 50 cents."

### DL-036 · APPROVED (was PROPOSED) · How live model calls are made visible and the spend is bounded
**Resolution (Day 7 session, 2026-10-12):** the bottom line was put to the user as a yes/no question (keep the call records on the trace and the spend stop for live runs) in the same message as the DL-015 design; the reply was "Yes proceed toward completion". Recorded as approval of both; the user may still object.
**Decision:** (1) `llm_client` records every live call (kind, path actually used: parse / json_mode / text, ok, error type, reported token usage, input size, latency) in a per-node log that `graph._traced` attaches to the node's trace entry as `model_calls`, with `degraded: true` when any call failed and the node fell back to its heuristic. Mock mode makes no calls, so its traces are unchanged. (2) `agent_driver.run_agent(live=True)` passes the caller's environment through, refuses to start without `OPENAI_API_KEY` or if the client still comes up in mock mode, and stops before the next turn once the estimated spend reaches the budget (overshoot of at most one turn). Calls the provider reported no usage for are estimated pessimistically (3 characters per token in, 400 tokens out). (3) `live_eval.py` runs every C7 scenario N times with one model pinned on all tiers and writes a Markdown report plus raw JSON.
**Status:** The user approved the live run on `gpt-6-luna` and the ceiling ("we can go with luna"); this mechanism is the session's design.
**Source:** this session; `boilerplate/llm_client.py`, `boilerplate/graph.py` (re-copied to both agents), `builder_platform/tests/agent_driver.py`, `builder_platform/tests/live_eval.py`; tests `test_model_call_trace.py` (2 of its tests failed before the change), `test_live_eval_tooling.py`.

### DL-037 · APPROVED (was PROPOSED) · Output-cap field and reasoning effort are env settings; the live run uses reasoning effort `none`
**Resolution (Day 7 session, 2026-10-12):** "dl 037 ok".
**Evidence (live, 2 probes, 18 rejected calls, no model output):** every call to `gpt-6-luna` failed with HTTP 400 `Unsupported parameter: 'max_tokens' is not supported with this model. Use 'max_completion_tokens' instead.` (probe reports `20261012T092629Z` and `20261012T094115Z`; the second captured the provider message). OpenAI's model page lists reasoning effort `medium` as the default and says Chat Completions supports function calling only with effort `none`; it is silent on `temperature` and on whether reasoning tokens count against the output cap (treated as likely, unconfirmed).
**Decision:** `OPENAI_TOKEN_PARAM` (`max_tokens` default | `max_completion_tokens`, anything else fails at startup) and `OPENAI_REASONING_EFFORT` (unset by default and then not sent; format-checked only) are read by `llm_client`. No provider check in code. `live_eval.py` takes `--token-param` and `--reasoning-effort`, and records both in the report. Regression tests in `test_llm_client_timeout.py` (failed before).
**Third probe (LIVE, `gpt-6-luna`, `--token-param max_completion_tokens --reasoning-effort none`, report `20261012T101247Z`):** 9 calls, 0 failed, so `temperature` and `max_completion_tokens` are accepted at effort `none`; 3/3 first scenarios (Acme, brewery, dental booking) passed; call latency p50 2.2 s / p95 4.1 s; 13.3k input / 2.9k output tokens including pessimistic estimates for the 6 rejected parse attempts (reported figures are lower). The native parse path is rejected for `IntentResult` and `ThinkDecision` ("Invalid schema for response_format … 'required' … Extra required key 'slots' supplied": the free-keyed `slots: Dict[str, Optional[str]]` is not valid for strict structured outputs) and succeeds in the JSON-mode fallback every time; `EnrichVerdict` parses natively. That costs one rejected request per intent/think call; not changed (a schema change is a separate decision).
**Status:** the settings are the session's design. Using effort `none` for the live run is a recommendation; the user ran the probe with it but did not otherwise say yes, so it stays PROPOSED.
**Source:** this session; `boilerplate/llm_client.py` re-copied to both agents.

**Full live run (report `20261012T103142Z`, 2026-10-12):** `gpt-6-luna`, effort `none`, `max_completion_tokens`, 3 runs: 22/22 business scenarios passed 3/3, 138 calls, 0 failed, about US$0.015 by provider-reported usage. Effort `none` is still PROPOSED: the user ran it with `--reasoning-effort none` but did not say yes. Second run (paraphrases, report `20261012T105341Z`, requested by the user: "one more run and then c8"): 13/13 scenarios passed 3/3, 84 calls, 0 failed, about US$0.0085. The result is recorded in CURRENT-STATE section 3b, with its limits.

### DL-038 · APPROVED (delegated) · C8 breaks the dental consent gate; no fingerprint or driver-trace change
**Decision:** The correction-loop demo removes `state_changing` from dental `book_visit` on a temporary copy of the agent, restores it, re-runs the failing scenarios and the full suite, and compares fingerprints within that copy. The fingerprint's dependence on the install folder (found while planning) is recorded as a limitation and not fixed, because C8 does not need it. The driver was not changed to write trace files; the fingerprint in the driver reply comes from the configuration the agent process loaded.
**Source:** MSG (2026-10-12): "about step 0 make sure you dont over engineer the situation. is it really such a big deal? proceed only if it is really required", "the rule to break - up to you", "about step 1 i dont care. i am more focused on the ai engineering here".
**Evidence:** `correction_loop.py` exit 0 in the working tree and on a clean CRLF checkout; `test_correction_loop.py`.

---

## Day 7 session (2026-10-12)

### DL-039 · APPROVED · The Day 7 section goes in the root README; stale text is corrected
**Decision:** "How this agent adapts and stays bounded", with the limitations in two halves, is a section of the root `README.md`, after the voice-era product description, which stays. Not `boilerplate/README.md`: it is the template README that generated agents inherit. Stale text found while preparing it was corrected: `CURRENT-STATE.md` (pre-live lines, test counts, superseded section 4 bullets, the temperature range), the dental README's "not covered" line (one live paraphrase now covers urgent-symptom classification), and the status list in `SPRINT-CONTRACT.md` section 8 (DL-037 and DL-038 were missing).
**Source:** the session proposed the root README and asked; the user answered "fix anything stale, and proceed with your plan".

### DL-040 · APPROVED · The platform test suite never reads a developer's `.env`
**Decision:** `builder_platform/tests/conftest.py` sets `ALTA_SKIP_DOTENV=1` and removes `OPENAI_API_KEY` / `OPENAI_BASE_URL` before any test module is imported; `env_bootstrap.autoload()` reads no `.env` file when that variable is set. Production behaviour is unchanged when it is unset. The repo-root `.env` and its key stay: the user needs them for the voice platform.
**Rationale:** the root `.env` holds a live key; mock mode rested on each test module blanking it, and on Windows a blanked variable is dropped when a subprocess inherits the environment (reproduced with a fake key; `test_child_process_does_not_load_a_dotenv_key` and three other tests failed before the change). A non-empty opt-out variable survives inheritance. Rejected: deleting the key (the user needs it) and pointing tests at a closed proxy (a workaround, not a guard).
**Source:** the user, asked whether to remove the key: "why removing the api key if i need it", then "add guard ifit is a good practice".

### DL-041 · APPROVED (record only, not scheduled) · Decision models are a candidate for the engine's narrow decision points
**Decision:** keep the idea of typed decision models (TypeSafe Jev, OpenAI Decisions API, Microsoft-Decision-1) for the narrow classify-or-constrain points of this engine, recorded here because the finalized planning documents are not edited. It builds on the PRD addendum AD3.2 ("Not every intelligent decision needs the full Agent loop"; no vendor becomes an architectural dependency; a decision call may constrain or classify, never sequence). Nothing is built in this sprint.
**Candidate seams in the engine (all in `boilerplate/`):**

| Decision point | Today | Shape for a decision model |
| --- | --- | --- |
| Answer to a pending yes/no, when it is not a bare answer (`nodes._bare_answer` returns nothing) | normal intent classification; the question is asked again | choice: consent / decline / change / other. Code accepts consent only if the extracted details match the pending payload exactly; "change" goes to `think`. The approval record (`authz`) still binds the exact payload |
| Intent (`intent_detect_node`, `IntentResult`) | INTENT-tier chat call, JSON mode | choice over the business's declared intents. Slot extraction stays with the language model: the free-keyed `slots` dict is not a fixed-choice task (and is why strict structured output is rejected today, DL-037) |
| Urgency / escalation guard (dental urgent symptoms, `human_handoff`) | keyword list in mock and in the fast router; the intent model live | predicate with a binding verdict (Spine AD-21: two closed outcomes, never a reply) |
| RAG sufficiency (`rag_subgraph` grade) | INTENT-tier call live, deterministic in mock | predicate |
| Enrichment tone (`EnrichVerdict`) | ENRICH-tier structured call | choice for the tone only; fact selection stays as it is |

Not candidates: `ThinkDecision` (act or ask, and the tool payload) and `PlanResult`. Both choose the next step, which AD3.2 / FR39 forbid for a decision call.
**Conditions before any of it is built:** (1) the provider-agnostic rule holds: a decision model is reached through one env-configured port in `llm_client` that returns a typed result, never a vendor import or provider branch; the vendor endpoints (non-`/v1`, own request format, per the research report) belong behind the Spine's runtime boundary (AD-14), so this is likely work for that runtime, not a patch to this engine. (2) Mock mode keeps a deterministic answer and a failed decision call is visible as `degraded` on the trace (DL-036). (3) It is measured, not assumed: the same C7 and paraphrase scenarios against the current INTENT tier, comparing accuracy, latency and cost per decision.
**Facts on file, unverified beyond the research report (2026-10-12):** OpenAI Decisions API (`POST /v1/decisions`, documented with `gpt-6-luna`; reported $0.10 per million input tokens, output free; "10x faster than the Responses API" is a provider claim). Jev (`jev-1.13.0`; typed question kinds "Noul" (sic in the report text; likely Bool) / Choice / Score; reported $0.042 per million input tokens, output free). Microsoft-Decision-1: named by the user, not in the research report or the PRD; unverified.
**Source:** the user: "decisions LMs is a TREND. JEV, DecisionsAPI, Microsoft-Decision-1. all of those are new and would become a standard very fast. I feel like we should save the idea of integrating decision models in some partsof thecode (as intent detectors, yes no detectors etc) some where in some of the design files". Context: the user first asked for an LLM or decision-model fallback on "yes, Tuesday works"; the session argued against building it now (such a sentence is often a change, not a yes; live, it already reaches the intent model; the vendor endpoints break the `/v1`-only rule) and proposed a zero-extra-call typed field plus a live probe first. Neither is approved yet.
