# Epic 1 Context: Bounded agent runtime for a declared business

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Serve a business declared in one specification artifact with a model-in-charge Agent. The Agent handles multi-turn requests: it asks, reads, acts with confirmation and verification, escalates and halts. The Core authorizes, journals and evidences every request the Agent makes. This epic is the foundation of the `studio/` product line and the test of its central claim: the Agent reasons freely and acts only within what the business allows. Stories 1.1–1.8 were delivered and verified in Phase 1, credential-free. The remaining stories:

- close the proof gate with a live model comparison against the fifteen-node system;
- close two lifecycle gaps: deadline expiry and a crash mid-turn;
- deliver credential-free CI on a clean checkout.

The proof gate sits in front of all further runtime work in Epics 4–9, and it can fail.

## Stories

- Story 1.1: Declare a business in one specification artifact
- Story 1.2: Validate a specification with the platform's own suite
- Story 1.3: Every Agent request crosses the Core under a closed taxonomy
- Story 1.4: Durable, tenant-scoped episodes
- Story 1.5: Act with confirmation, idempotency and read-back verification
- Story 1.6: Guards, two exits, halts, escalation and suspension
- Story 1.7: Goals, obligations, grounded claims and verified resolutions
- Story 1.8: Provider-agnostic Agent boundary, scenario channel and two businesses
- Story 1.9: Complete the proof gate with a live comparison
- Story 1.10: A deadline expiry resumes a pending episode as an external event
- Story 1.11: An in-flight episode survives a crash mid-turn
- Story 1.12: Credential-free CI on a clean checkout

## Requirements & Constraints

- **One specification, human-readable and diffable.** It is neither a generated prompt nor generated code. It has a content-addressed version: reordering entries or moving the folder leaves the version unchanged, and editing the specification or a source changes it. An empty area is recorded as not established, never defaulted. Ordering or sequencing constructs, sequencing prose and unknown fields are rejected with a readable reason.
- **The validation suite is platform-owned**, domain-agnostic, derived from the specification and never stubbed. Only platform invariants block, and a failing specification cannot compile. Blocking cases:
  - a capability that is granted but that policy always denies;
  - an effect with no success evidence or no consequence class;
  - a consequential effect with no authority basis;
  - a missing escalation destination, an empty disclosure or a guard without a detector.
- **Every request crosses the Core.** The request kinds form a closed set: `retrieve`, `read`, `effect`, `clarify`, `respond`, `escalate`, `suspend`. Every kind is authorized and journaled, reads included. A business grants request kinds and can never add one. Every denial is exactly one of `spec_defect`, `business_refusal` or `platform_error`.
- **Effects:**
  - A confirm-required effect is not authorized until a confirmation is recorded. Only a bare yes counts, and it is bound to the exact payload and the episode.
  - Effects are at-least-once against a Core-issued key scoped to tenant and episode.
  - An effect is verified by read-back against the business's own system, which stays authoritative.
  - A hung, rejected or unreadable effect is a typed error or an unverified effect, never reported as done.
  - Identity-based authority is refused until identity is verified.
- **Episodes:**
  - Lifecycle is exactly active, pending (awaiting a named input) or closed. Lifecycle says nothing about outcome.
  - An episode keeps its pinned versions across restarts.
  - Resent messages are processed once, and concurrent inbound messages are serialized.
  - A result after close is a late result and changes nothing.
  - Cross-tenant references are rejected, not filtered.
  - Evidence can be removed by tenant, episode and age.
  - There is no cross-episode memory, and all timestamps are UTC.
- **Exits, guards and halts:**
  - Guards are evaluated before the Agent sees the message. Detection may use a model, but the verdict binds and has two outcomes only: a typed constraint or a safety halt.
  - The turn budget and the stall detector end the episode in a declared halt, with notices to the requester and to the escalation destination.
  - The terminal notice and the first-message disclosure are Core-owned.
  - Only the Agent escalates. Escalating where the rules are silent records a spec defect.
  - "Stop actions only" refuses effects while replies continue. "Suspend" stops replies and records an outcome for every in-flight episode.
- **Grounding and resolutions:**
  - Business facts must cite a provenance reference the Core issued to this episode. The Agent cannot mint, alter or borrow one.
  - General knowledge can be enabled or disabled per business, and it is marked in the record.
  - The Core refuses forbidden conclusions. An undeclared conclusion is refused and recorded as a spec defect.
  - A resolution cannot claim an effect that has no execution record or was not verified.
  - A served goal cannot close while obligations are outstanding. Only a declared waiver satisfies an obligation.
- **Provider-agnostic.** The product runs credential-free when no model is configured. A half-configured endpoint is rejected at startup. A live model is reached through plain HTTP to an env-configured OpenAI-compatible `/v1`, with no vendor SDK. Every model call is recorded with tokens and latency.
- **Proof gate (1.9):**
  - It needs the user's approval and a spend cap.
  - The ten scenarios run three times. The report gives model calls per turn and per-call and per-turn latency (p50, p95), with the per-scenario pass rate.
  - Every failure is classified as an Agent, specification or Core finding.
  - Every inline resolution refusal is judged correct or false. On that evidence, inline resolution validation is either relied on or demoted to offline evaluation.
  - Each item of the shipped system is recorded with its disposition.
  - The verdict is pass or fail. A fail is escalated to the user, never patched. The run's measurements become the context-assembly baseline.
- **Deadline expiry (1.10):** an expiry is an external-system event that resumes the episode with the expiry as the Agent's input. The Core takes no action of its own. A duplicate expiry is processed once, and an expiry after close is a late result. The recorded clock is used.
- **Crash recovery (1.11):** a crash at any journal boundary leaves a consistent record: no re-executed effect, no orphan, no duplicate step. A decision journaled before authorization is never treated as authorized.
- **CI (1.12):** a clean clone runs every studio and legacy suite and the three selftests with no credential configured. CI holds no secret and can make no live call. A failing branch fails the job.
- **Standing criteria:** `python -m pytest studio/tests -q` and `python -m studio scenarios` pass, and the legacy suites stay green. No `--live` run without the user's approval. Every new Core safety check has an injection test and a mutation proof (it is shown to fail when its condition is reintroduced).

## Technical Decisions

- **The Agent decides; the Core constrains.** The Core never selects the next step. That rules out a precedence table, a transition graph, a workflow language and precondition-derived orchestration. Ask of every new mechanism: *does it constrain the Agent, or decide its next step?*
- **Prompt text is advisory.** Every constraint that must hold is enforced by the Core.
- **The Core compiles the projections.** The Agent's context, its tool surface and the enforced policy are all compiled from the one specification. The compiler version is pinned into the episode beside the specification version, and knowledge-source versions are pinned at start.
- **The Core is the only author of evidence.** Evidence is a typed record. An action record is not a resolution.
- **The resolution envelope is fixed:** goal, served or not, authority, evidence and business payload. The kind enumeration is deferred.
- **Durability:** the loop reads nothing un-journaled. Clock, randomness, identifiers and configuration are recorded or pinned. Step boundaries are a durability concern only and never imply a permitted order. Storage is SQLite behind an `EpisodeStore` port. The engine is deferred and its semantics are fixed: a unique `(tenant, episode, step, idempotency key)` constraint, with evidence written in the same transaction.
- **Dependencies point inward.** Extensions, adapters, channels and the Agent runtime depend on Core contracts. No vendor name, branch or key appears in Core or Agent code. Credentials never enter Core state, evidence, context or a prompt. The Agent never learns the channel. The channel is a port, and the scenario channel implements it.
- **Tenant identity sits on every record.**
- **Namespaces:** `agent/`, `core/`, `spec/`, `knowledge/`, `extensions/`, `builder/`, `channels/`, `evaluation/` and `web/` in `studio/`. Do not modify `boilerplate/`, `builder_platform/` or `Generated_Agents/`.
- **Engine-leak log:** it lives in `docs/next-phase-proposals/PROOF-GATE.md`. Entry 1 (the brewery as business 2) needed zero Core changes. A Core change made to fit a business is a leak and must be logged.
- **Context assembly and model tiering are measured, not designed.**

## Cross-Story Dependencies

- 1.1 → 1.2 → 1.3 → 1.4 → 1.5 and 1.6 → 1.7 → 1.8 are done.
- 1.9 depends on 1.1–1.8 and is **blocked on gate D1** (spend approval for one live run). It gates further runtime work in Epics 4–9, and its measurement is the baseline for Story 2.3.
- 1.10 (needs 1.4) and 1.11 (needs 1.4 and 1.5) are ready. Both sit behind the proof gate (1.9).
- 1.12 depends on 1.1–1.8 and is **blocked on gate D3** (authorization to commit and push).
- Remainders handled elsewhere:
  - a restart after a knowledge edit → Story 2.1;
  - a restart after a specification edit, and the promotion gate → Stories 3.1 and 3.2;
  - leak classification → Story 9.1.
