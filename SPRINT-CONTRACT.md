# SPRINT-CONTRACT — Agent Studio seven-day hardening

Status of this file: written 2026-10-11 from the conversation record and the repository. It restates what the user approved; it does not add to it. Every item cites a decision ID in [DECISION-LOG.md](DECISION-LOG.md). Where something is a proposal, it is in section 8 and is **not** part of the contract.

Source-of-truth order (DL-022): (1) latest explicitly approved scope and decisions; (2) the repository and its test results; (3) `brief.md` (product intent); (4) `ARCHITECTURE-SPINE.md` (future state, does not authorize the model-in-charge loop in this sprint); (5) earlier handoffs and summaries (historical reports, not proof).

## 1. Objective (DL-002, DL-005)

Make the existing project materially stronger and demonstrate adaptive-agent engineering within a tightly controlled amount of work:

- one agent runtime whose behaviour adapts to different business contexts through business configuration, not separate hardcoded agents;
- meaningful agent agency with platform-enforced authority boundaries;
- appropriate use of knowledge, tools, evidence and verification;
- a convincing demonstration across multiple business contexts.

It is not an attempt to build a production-grade agent platform.

## 2. Hard constraints

| # | Constraint | ID |
| --- | --- | --- |
| 1 | Total remaining work fits **seven working days, including planning**, code, tests, debugging and documentation. If it does not fit, reduce scope, never time. | DL-004 |
| 2 | Treat the existing repository as the starting point: hardening and targeted improvement, **not** a greenfield rewrite. | DL-004 |
| 3 | **Retain the existing LangGraph runtime.** Do not implement the Architecture Spine's model-in-charge loop, and do not claim the sprint realizes it. Document the distinction and the remaining limitation accurately. | DL-007, DL-011 |
| 4 | Do not resume BMAD planning, create Epics & Stories, or rewrite finalized planning documents (Brief, PRD, Architecture Spine, UX spines). | DL-004, DL-011 |
| 5 | Do not weaken tenant isolation, bounded authority, version consistency or reliable tool execution to simplify the work. | DL-003* |

\* Constraint 5 comes from the superseded reassessment message and was not restated in the seven-day message; it is carried because nothing in the later approval contradicts it. See DL-003.

## 3. Approved deliverables

The plan below was presented by the assistant in chat and approved by the user "in principle" with three clarifications (DL-006 to DL-009). **No file contained this plan before this contract.** Wording is condensed from that message.

| ID | Deliverable | Planned day |
| --- | --- | --- |
| C1 | Re-sync the brewery agent's engine copy from `boilerplate/`; add a drift test; fix its failing selftest. | 1 |
| C5 | Per-conversation trace of what was decided, authorized, run and verified, plus a configuration fingerprint. | 1 |
| C2 + C3 | Declared action properties and **execution-time authorization**. | 2 |
| C4 | **Outcome verification** by read-back; unverified outcomes never reported as success. | 3 |
| C6 | A third, different business (dental practice) made by the existing copy-and-edit path. | 4 |
| C7 | Cross-business evaluation suite: scenario files per business (inbound turns plus expected properties of the trace); deterministic mode runs in pytest and CI; a live-model mode repeats each scenario N times and writes a Markdown report. | 5 (deterministic), 6 (live) |
| C8 | Correction-loop demonstration **script**: a deliberately wrong rule fails a scenario, the config is fixed, that scenario and the full suite are re-run, and the trace shows the fingerprint changed with no regression. | 6 |
| — | README section "How this agent adapts and stays bounded", limitations statement, final full run. Day 7 is half buffer. | 7 |

### Clarifications that amend the plan (user-approved)

- **Architecture boundary (DL-007).** Demonstrate configurable business behaviour, model decisions at defined points, execution-time authority enforcement, outcome verification, traceability and cross-business evaluation. Do not claim the future model-in-charge runtime.
- **C3 binding (DL-008).** Confirmation and operator-approval records are Core-owned and separate from model-controlled payload fields. Each is bound to the conversation or episode, business/agent, effective configuration version, flow and tool, and canonicalized action arguments. An approval must not be reusable for a different payload, a different conversation, or a later execution. Required tests: payload mutation, approval replay, cross-conversation reuse, forgery through model output. The authority declaration must express the required gates unambiguously when an action has more than one relevant property (for example state-changing and liability-bearing).
- **Fingerprint and C4 (DL-009).** The configuration fingerprint is a deterministic content fingerprint of the effective business configuration used for a run, and must change when that configuration changes. Git revision and working-tree status may be recorded for context only. State-changing flows are not considered successfully verified unless their declared read-back verification actually passes. Where verification is required but unavailable, fail the structural preflight or return an explicit unverified outcome rather than implying success.

## 4. Success tests and demonstrations (from the approved plan)

- **Same engine, several businesses:** the drift test shows the engine files are byte-identical across agents; each agent's selftest passes.
- **Bounded authority:** a forged payload that skips a gate is refused at execution; an undeclared tool is refused; a misdeclared flow fails at startup.
- **Verified outcomes:** a tool that reports success while the read-back fails produces a failure reply and an unverified trace entry, never a success message.
- **Adaptive behaviour:** the same kind of request ("book me in", "I want my money back", "it really hurts") produces different, correct behaviour per business (confirm-then-book, operator-approved refund, urgent handoff, refusal), asserted on the trace, not on wording.
- **Correction loop:** fail, config change, pass, no regressions.
- **Regression net:** the deterministic evaluation runs in pytest alongside the existing tests.

Day 5 target as planned: about 15 scenarios across Acme, dental and brewery, one command to run them, all passing in mock mode.

## 5. Explicitly excluded from this iteration (DL-006)

The Builder conversation and any operator UI (including the UX spines' surfaces); a real email channel; the Architecture Spine's model-in-charge loop and closed request taxonomy; the Business Specification as a single YAML artifact (configuration stays in Python); Core-issued provenance references; durable episode storage and crash recovery; multi-tenant hosting; policy engines, DBOS, MCP rewrite; the four-business generalization programme; real-business usefulness testing; notifications.

## 6. Risks and compromises accepted at plan approval (DL-006)

- Agency is bounded by a fixed graph, not the Spine's loop: the model decides intent, act-or-ask, plan and retrieve, but the graph decides order. Honest framing: structured agency with execution-point enforcement.
- Business behaviour is a typed Python config, not a declarative diffable artifact.
- Verification uses simulated systems; it proves the mechanism, not integration with a real system.
- The live-model evaluation is small (about 15 scenarios times 3 runs): behaviour, not statistical reliability.
- All businesses are authored; usefulness for a real business is untested.
- The brewery agent is voice- and sales-shaped; it is kept passing but the demonstration leans on Acme and dental.
- The planning artifacts describe a larger product than this iteration builds.

## 7. Cut order if time slips (DL-010)

1. Drop the correction-demo script (C8).
2. Drop the live-model report.
3. Never cut: execution-boundary enforcement, outcome verification, deterministic tests, and a reliable end-to-end demonstration.

## 8. Not part of the contract (proposals and open points)

Decisions made inside sessions are not part of this contract until the user approves them. Their current status lives in [DECISION-LOG.md](DECISION-LOG.md), which is the single place to check: as of the end of 2026-10-12, DL-015, DL-026, DL-029, DL-030 and DL-036 are `PROPOSED` (all already in the code) and DL-023 is `OPEN`; the others raised during the sprint (DL-013, DL-014, DL-016 to DL-021, DL-024, DL-025, DL-027, DL-028, DL-031 to DL-035) are `APPROVED`, DL-032 for research only.

## 9. Ambiguities resolved since this contract was written

1. **Days consumed** — four of seven when C7 started (DL-019).
2. **Whether C6 is complete** — accepted by the user (DL-019).
3. **Which instructions win when `CLAUDE.md` conflicts** — the sprint documents, for sprint work; `CLAUDE.md` now says so (DL-018).

One factual correction to section 3: the deterministic C7 suite runs in pytest; the repository has **no CI configuration**, so "pytest and CI" is half true until CI is added.
