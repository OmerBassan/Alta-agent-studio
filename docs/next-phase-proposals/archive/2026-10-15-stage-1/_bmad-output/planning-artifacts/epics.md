---
status: draft
stepsCompleted: [step-01-validate-prerequisites, step-02-design-epics, step-03-create-stories, step-04-final-validation]
validation: "2026-10-14: all checks pass (134/135 PRD IDs traced + FR8 declined; 30/30 UX-DRs; no forward dependencies). Awaiting user approval of the epic structure (step 2) and [C] completion (step 4) before status: final."
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-AgentStudio-2026-10-08/prd.md
  - _bmad-output/planning-artifacts/architecture/architecture-AgentStudio-2026-10-07/ARCHITECTURE-SPINE.md
  - _bmad-output/planning-artifacts/ux-designs/ux-AgentStudio-2026-10-08/EXPERIENCE.md
  - _bmad-output/planning-artifacts/ux-designs/ux-AgentStudio-2026-10-08/DESIGN.md
  - _bmad-output/planning-artifacts/briefs/brief-AgentStudio-2026-10-07/brief.md
  - _bmad-output/planning-artifacts/briefs/brief-AgentStudio-2026-10-07/spec-stress-test.md
  - _bmad-output/planning-artifacts/*/*/.memlog.md
  - docs/next-phase-proposals/BMAD-DECISION-REGISTER.md
  - docs/next-phase-proposals/NEXT-PHASE-PLAN.md
  - docs/next-phase-proposals/IMPLEMENTATION-STATE.md
  - docs/next-phase-proposals/PROOF-GATE.md
---

# AgentStudio - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for AgentStudio, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

**Scope.** The `studio/` product line: the approved V1 of the text, inbound, specification-driven, model-in-charge product (PRD §7.1 S1–S11). It does not cover the shipped voice product (`boilerplate/`, `builder_platform/`, `Generated_Agents/`), which stays governed by its own spec of record (`m-arch` 10).

**Single source of truth.** This file is the only home of **story-level acceptance criteria**. `docs/next-phase-proposals/NEXT-PHASE-PLAN.md` holds the program (phases, ordering, technical choices) and references stories by ID; `docs/next-phase-proposals/IMPLEMENTATION-STATE.md` holds verification evidence; `docs/next-phase-proposals/BMAD-DECISION-REGISTER.md` holds decision status. Requirement text below is condensed; **the PRD's wording is authoritative** wherever the two differ.

## Requirements Inventory

### Functional Requirements

FR1: The Builder opens with an open invitation ("Tell me about your business and what you want the Agent to handle"), never a form or a fixed question set.
FR2: The Builder accepts the business's own material in the formats the operator already has (price lists, terms, policies, care guides, fee guides, FAQs, prior correspondence).
FR3: The Builder decides adaptively what needs clarification; no fixed questionnaire; question count is a function of what is missing.
FR4: The Builder actively interviews for content that exists in no document: prohibitions, thresholds, exceptions, authority limits, routinely granted exceptions, always-escalate cases, what must be established before a decision.
FR5: The Builder surfaces contradictions (source↔source, source↔operator) rather than silently selecting one.
FR6: Where behaviour is unknown and the operator cannot resolve it, the Builder records a specification defect; it never invents a default.
FR7: The Builder probes the gap between printed and practised policy.
FR8: The Builder MAY offer optional pre-filled specification starting points. **Declined for V1** (`m-ux` 22 override, register B-06).
FR9: The Builder produces both the Business Specification and the Business Knowledge artifacts.
FR10: The Builder is itself agent-driven.
FR11: Human review is a blocking precondition of promotion: recorded approval, attributable to a named approver, retained as evidence (FR28). Who may approve is deferred (O1).
FR12: The Builder instruments its burden: wall-clock time to a passing validation suite and number of source artifacts, per business.
FR13: The Business Specification is one artifact; Agent context, capability surface and Core policy are all compiled from it.
FR14: Every expression area EX1–EX17 is expressible, separately addressable, reviewable and checkable; an empty area is a recorded absence, never a default.
FR15: The specification distinguishes obligations (required before an action) from diagnostic inputs (no fixed sufficient set).
FR16: Decision authority classes — at minimum informational, liability-bearing, state-changing — gated separately.
FR17: The specification can permit inferring a cause while forbidding determining fault.
FR18: The specification cannot express ordering or sequencing.
FR19: The specification is human-readable and diffable, neither a generated prompt nor generated code.
FR20: Evaluation criteria live inside the durable specification.
FR21: The specification is versioned; a promoted version is immutable.
FR22: Exactly one gate, the validation suite, in front of promotion and deployment: platform invariants block, business criteria warn unless declared blocking; a failing suite cannot be promoted or deployed.
FR23: Validation detects a capability that is granted but always denied by policy, and blocks promotion.
FR24: Validation rejects sequencing constructs with a comprehensible reason.
FR25: A passing validation suite is the unit of done for a built business; no separate, weaker pre-deployment check.
FR26: Rollback is selecting an earlier promoted version; no reconstruction, no migration.
FR27: An episode keeps the specification version pinned at its start; promotion does not alter running conversations.
FR28: Every promotion is reviewable, revertable and attributable.
FR29: Behaviour never mutates silently; no continuous automatic learning; changes only through promotion.
FR30: Knowledge sources are pinned to versions, not referenced.
FR31: A business declares precedence among its sources for when they conflict.
FR32: Every business-authoritative fact is grounded in a declared, version-pinned source; enforced as reference integrity (FR33), not as verified meaning.
FR33: Every authoritative context item carries a Core-issued provenance reference bound to tenant, source, source version and locator; unissued, altered or cross-tenant references are refused before reaching the person.
FR34: General domain knowledge may come from the model, must be marked in evidence, and is enabled or disabled per business.
FR35: Freshness is declared per read and per capability contract, never globally; a read an effect depends on must be fresh; the Core never sequences a read before an act.
FR36: The platform owns no system of record; external systems stay authoritative.
FR37: Every answer is reconstructible against the exact source versions used.
FR38: The Agent decides intent, needed information, when to retrieve, which capability, whether to act/continue/respond/escalate, phrasing, and unenumerated situations.
FR39: The Core never selects the Agent's next step.
FR40: A closed set of request kinds; every kind authorized and journaled, reads included; businesses grant over kinds and can never add one; no precedence or ordering among kinds.
FR41: The Agent never contacts anything outside the Core.
FR42: Five generic guardrails apply with zero configuration: no invented business facts; no action outside authority; no undeclared actions; no success claim without evidence; escalate when authority or evidence is unavailable.
FR43: Every constraint that must hold is enforced by the Core; no enforcement relies on prompt text.
FR44: Guards are evaluated before goal recognition; detection may be model-based; the verdict binds with exactly two outcomes (typed constraint or safety halt); a guard never composes a reply or chooses the next step.
FR45: The Core has exactly two exits: a typed result to the Agent, or a declared safety halt with a recorded outcome.
FR46: Errors cross boundaries as typed results; a degraded outcome is distinguishable by the caller.
FR47: The Agent alone escalates; the platform returns a typed refusal and never escalates on the Agent's behalf.
FR48: Where rules are silent the Agent escalates and the gap is recorded as a specification defect.
FR49: Goals come only from the declared set; no Agent-generated goals or plans.
FR50: Several related goals per episode, one active at a time, explicit parking and resumption.
FR51: Every capability is verb-first with a contract: input schema, effects, authority required, confirmation requirement, success evidence, idempotency scope; no success-evidence definition = not shippable.
FR52: Every capability declares a consequence class (reversible, costs money, reaches a customer), visible to the operator.
FR53: A confirm-required effect is not authorized until the confirmation is recorded.
FR54: Retry eligibility is a visible attribute; no idempotency key → not eligible.
FR55: External effects are at-least-once against a Core-issued key scoped by tenant and episode; no double effect, no false suppression.
FR56: External systems are reached only as Core contract → adapter → extension.
FR57: Adapter credentials are held at the adapter and resolved per tenant; no credential value in Core state, evidence, Agent context or prompt.
FR58: Business configuration never changes Core semantics; configuring vs requesting a capability is distinguished.
FR59: Custom code may be a leaf behind a declared contract, never control flow.
FR60: Lifecycle is exactly active / pending (awaiting a named external input) / closed; a declared deadline's expiry is an external system event that initiates or resumes an episode; the Core never acts on an expiry.
FR61: An episode is initiated or resumed only by an inbound interaction or an external system event; the platform never starts an outbound conversation.
FR62: An unresolved episode resumes later with state, evidence, specification version and context intact.
FR63: A result after close is a late result and never mutates the resolution.
FR64: An in-flight episode survives a process failure; clock, randomness, identifiers, environment and configuration are recorded or pinned.
FR65: The Core is the sole writer of episode state; concurrent inbound on one episode is serialized.
FR66: No cross-episode memory or profiling.
FR67: Lifecycle says nothing about outcome; pending is not failure, closed is not success.
FR68: Every resolution carries goal, served or not, authority, evidence and a business payload; the kind enumeration is deferred.
FR69: Escalation may be a declared success.
FR70: Only the Core's execution record attests an effect; evidence entries are typed records.
FR71: A resolution asserting an effect without a Core execution record is invalid.
FR72: An action record is not a resolution.
FR73: Episode evidence is durable product data: turns, retrievals, model decisions, actions, authorities, obligations and waivers, guard verdicts, errors, timings, and per-episode model calls, tool calls, tokens and cost.
FR74: Every escalation records its reason class.
FR75: Evidence is addressable and removable by tenant, episode and age without reshaping the schema.
FR76: Every per-episode and per-business criterion of PRD §10.1–10.2 is computable from the record without a human reading a transcript.
FR77: Every denial is recorded as exactly one of specification defect, business refusal, platform error.
FR78: Only specification defects enter the specification backlog.
FR79: The operator's primary surface is the classified divergence list.
FR80: An operator can open a single episode and see what happened within it.
FR81: Every operator-visible failure, refusal or status comes from a closed, enumerable vocabulary.
FR82: A divergence item is actionable toward a specification change.
FR83: The Agent and Core never learn the channel.
FR84: V1 ships one channel adapter, inbound email / messaging, ingress and egress.
FR85: The adapter is replaceable without touching behaviour.
FR86: The adapter correlates inbound to episode identity, with an explicit join key to any external system of record.
FR87: Duplicate and corrected re-sends never create a second episode or effect; turn handling is idempotent per logical turn.
FR88: All four exemplar businesses are built through the Builder.
FR89: Engine leaks are recorded and classified (configuration / extension point / genuinely novel).
FR90: Resolution-model strain is recorded.
FR91: Setup effort is recorded per business from FR12 and compared across the four in build order.
FR92: The usefulness test runs on real inbound requests; at least one business is real end to end; Agent failures reported separately from business-rule blocks.
FR93: The validity floor is recorded.
FR94: Two or three conversations with real small-business operators are conducted.
FR95: The validation suite is platform-owned, domain-agnostic, specification-derived, never authored by the Builder it gates, never stubbed; only platform checks block.
FR96: Every Core safety check sits before anything that mutates what it measures and is proven non-vacuous by reintroducing its condition.
FR97: Capability and extension code never blocks the request path; every external client has its own timeout.
FR98: Every channel adapter is built against captured real traffic, every discovered behaviour pinned by a test.
FR99: The Builder instruments its yield (rules recovered by interview, contradictions surfaced, defects recorded), reported together with burden.
FR100: Elicitation quality is tested against a seeded business fixture with withheld rules: recovered vs invented vs silently defaulted.
FR101: An operator revises a promoted specification through the Builder conversation, producing a new version through the same gate and promotion.
FR102: Human corrections are first-class records against the episode and the specification version in force.
FR103: An escalated episode is delivered to a business-declared destination over the V1 channel, with reason class and a link to the episode.
FR104: A narrated process is re-derived into declared context, policy, capability, authority, goal and obligation; no ordering is persisted.
FR105: Goals and outstanding obligations are typed Core state, readable by the Agent, asserted at resolution; holding is not deciding.
FR106: A waiver is explicit, attributable to a declared authority, and recorded.
FR107: The Agent loop has a Core-enforced termination bound plus a repetition/stall detector with a wired outcome.
FR108: Recorded human corrections are a first-class divergence source, classified under FR77, entering the same backlog.
FR109: For state-changing, money-moving or customer-reaching capabilities, authority is established, not assumed from the channel; no declared basis fails validation.
FR110: Immediate suspension of the Agent, or of effects only, without promotion or deployment; recorded; in-flight episodes end in a recorded outcome.
FR111: A safety halt emits the business's terminal notice through egress; Core-owned, not per guard.
FR112: The requester is told in the first message they are corresponding with an automated agent; wording per business.
FR113: The channel adapter shapes the Agent's writing for the channel; how the Agent writes may be judged by business criteria.
FR114: The email adapter handles threading and quoted history, additional recipients, attachments, bounces and delivery failures, and automated-sender loops — each pinned by a test.
FR115: Business refusals are sampled for human adjudication at a business-set rate; a refusal found wrong enters the backlog as a specification defect.
FR116: Variation resolves at exactly three levels (configuration / supported extension point / custom implementation), and the level is a recorded judgement.
FR117: Builder-side failures (unreadable source, abandoned session, contradicting new source) are distinguishable outcomes; a half-elicited specification is never presented as complete.

### NonFunctional Requirements

NFR1: Durability — every model decision, authorized execution and evidence write is durable; an in-flight episode is recoverable after process failure.
NFR2: Effect integrity — at-least-once with a Core-issued idempotency key; non-keyable actions not auto-retried.
NFR3: Isolation — tenant identity on every episode, specification, source, provenance reference, idempotency key, evidence record and action request; cross-tenant resolution rejected, not filtered.
NFR4: Auditability — every request kind authorized and journaled, reads included; only the Core authors evidence; every denial classified.
NFR5: Provenance integrity — references Core-issued, episode-scoped, unforgeable; invalid references refused before reaching the person; scoped to reference validity only.
NFR6: Semantic faithfulness — evaluated against a threshold, never guaranteed; threshold not set (O5), instrumented from day one.
NFR7: Reproducibility — specification, compiler and knowledge-source versions pinned at episode creation and read from episode state.
NFR8: Change safety — promoted versions immutable; validation a hard gate; rollback by version selection.
NFR9: Consistency — the Core is the sole writer of episode state; concurrent inbound serialized.
NFR10: Data lifecycle — a business can state its requirements; evidence addressable and removable by tenant, episode and age; policy and executor deferred.
NFR11: Secret handling — no credential value in Core state, evidence, Agent context, prompt or evidence export.
NFR12: Portability — changing model, provider or framework does not alter the architecture; no vendor SDK, no hardcoded provider or base URL, no provider branching, no vendor-specific key.
NFR13: Latency — no turn-latency target in V1 (A1); per-turn and per-episode latency instrumented from day one.
NFR14: Cost — no per-episode ceiling in V1; per-episode model and execution cost instrumented from day one.
NFR15: Availability, throughput, scale — not V1 concerns, stated as such; episode volume per business is the dimension that grows; its cost slope is measured during the four-business run.
NFR16: Observability — one correlation identity per episode on every record, reportable by a person who experienced a problem; evidence vocabulary follows GenAI telemetry naming where it exists.
NFR17: Configuration validity — configuration and credentials validated at startup; a health check never reports healthy on a configuration whose first real request would fail.
NFR18: Timestamps — UTC throughout.

### Additional Requirements

From the Architecture Spine (AD-1–AD-25 are traced through the FR/NFR they bind; the items below are those not fully carried by a single FR):

- **No starter template.** Brownfield repository: the product is a new package `studio/` beside the shipped voice product, which is not modified (`m-arch` 10). Epic 1 Story 1 is therefore not a scaffold story.
- **Namespaces** follow the Spine's layers: `agent/`, `core/`, `spec/`, `knowledge/`, `extensions/`, `builder/`, plus `channels/`, `evaluation/`, `web/` (NEXT-PHASE-PLAN §2).
- **Dependency direction inward only (AD-9):** extensions, adapters, channels and the agent runtime depend on Core contracts; the Core depends on none of them; no vendor name, branch or key in Core or Agent code.
- **AD-1 filter on every new mechanism** (register U4): *does this constrain the Agent, or decide its next step?* Asked in review of every Core story.
- **Litmus test (Spine):** a new business is onboarded without a business-specific execution graph or state machine.
- **Proof gate (Spine; PRD §7.5; `m-arch` 47, user):** before the whole runtime is committed, one realistic interaction end to end, compared with the 15-node system on the nine axes. It sits in front of E4–E9 and can fail. **Inline resolution validation is provisional until the gate validates it** (Spine Deferred).
- **Context assembly is measured, not designed up front** (Spine Deferred): what sits permanently in Agent context versus what is fetched on demand is chosen by measurement, bounded by AD-7 and AD-3.
- **Retrieval architecture deferred** (Spine Deferred, K-03); embeddings, if needed, through the OpenAI-compatible `/v1/embeddings` surface with lexical fallback in credential-free mode (K-08).
- **Model tiering expressible at the runtime boundary** (AD-14); routing policy measured, not designed. Model access only through env-configured OpenAI-compatible `/v1` (CLAUDE.md provider rule, NFR12).
- **Durability engine deferred; semantics fixed** (AD-12, A-09). Spine seed is PostgreSQL 16+ with a fallback floor of a unique `(tenant, episode, step, idempotency key)` constraint and evidence in the same transaction. Implemented on SQLite behind an `EpisodeStore` port (technical choice T3).
- **Evidence vocabulary** follows OpenTelemetry GenAI naming where it exists (Spine Consistency Conventions, NFR16).
- **Process-level isolation between deployed Agents is permanent** (PRD §7.4).
- **Migration assessment** (PRD §7.4, §12) is distributed across E3–E9: the fifteen-node pipeline is never ported because it exists; Core guarantees it earned become Core services, never steps.
- **MCP is one transport for capability contracts, not required** (K-07); the integrations catalog is copy-adapt, never imported.
- **Retention policy and deletion executor deferred** (AD-25); the evidence shape must not foreclose them.
- **Verification discipline** (CLAUDE.md, NEXT-PHASE-PLAN §8): `python -m pytest studio/tests -q`, `python -m studio scenarios`, and the legacy suites (`builder_platform/tests`, `claude_plugin/tests`, three `selftest.py`) stay green; no `--live` run without the user's approval; every new safety check proven by injection and by mutation (FR96); a clean-checkout run before any commit is called green; CI is an unmet commitment (register D-05).
- **Credential-free deterministic mode** (technical choice T8): the whole product runs and is demonstrable with zero tokens, so CI can run end to end.
- **System Frame** (global engineering manual §1.7): each phase that ships a runnable system answers failure, fallback, concurrency, scalability, observability, config, deployment and durable state in its phase report.

UX upstream contract gaps (EXPERIENCE.md, Amendments and Upstream Gaps — "raise each with the owning document before implementation"); each is owned by the story that first needs it:

- Gap 3 connect-your-mailbox surface (provider, authorisation) — originated in UX, needs a source owner.
- Gap 4 persistent suspended state / Agent status enum.
- Gap 5 specification version lifecycle as operator-visible states.
- Gap 7 approval vs validity (resolved in UX: the operator approves, approval does not determine validity) — confirm upstream.
- Gap 8 counterfactual replay (O11) — open.
- Gap 10 material intake limits (formats, size, duration, failure taxonomy).
- Gap 11 divergence item fields (resolved for V1: class, interaction label, one-line request).
- Gap 12 linking a reply to the specification item it relied on.
- Gap 13 validation finding shape and its link to a specification area.
- Gap 14 email subject and received time in the interaction record.
- Gap 15 judging sampled refusals — who and on which surface.
- Gap 16 rollback action.
- Gap 17 platform error reference format.
- Gap 18 mailbox connection status after go-live.
- Gap 19 undeliverable escalation email.
- Open question 3: what makes a divergence *material* (Amendment 1) — deliberately left upstream.
- Open question 4: whether the escalation address is declared during authoring or at mailbox connection.

### UX Design Requirements

UX-DR1: Information architecture is exactly two destinations (Understanding, Activity) and one mechanism (the Builder conversation); no further navigation, no list of all interactions (`m-ux` 87).
UX-DR2: Cold-start workspace: the first surface is the workspace with one open prompt ("Tell me about your business and the customer requests you want me to handle."), optional material; no funnel, welcome screen, templates or step indicator.
UX-DR3: Conversation panel: opens from a specification section, a divergence item or an interaction and shows that origin as a `meta` line; never a form or questionnaire; closed-vocabulary thinking state; a failed turn shows "The Builder could not reply. Nothing has changed." and keeps the operator's message for resending.
UX-DR4: Conversation input: labelled multi-line text area with a `border-strong` edge, pinned to the bottom of the Conversation pane, height reserved with `scroll-padding-bottom`.
UX-DR5: Understanding document: five peer sections mapping EX1–EX17 exactly as EXPERIENCE.md tabulates; a persistent frame saying it is what the Builder currently understands, not a live-editing surface; no form fields, toggles, dropdowns or settings rows; co-present with the conversation and updated as information is grounded.
UX-DR6: Sequencing prohibition on the authoring surface: no arrows, connectors, step numbers, progress rails, steppers, stage breadcrumbs, "next/then/after this/continue", percentages, completion meters or checklists.
UX-DR7: Item state marker: exactly one of Established / Not established / Changed / Affected by this change, as a text label plus its shape (label only; dashed bracket on `state-not-established-band`; solid 2px left rule + underline; dotted 2px left rule + italic).
UX-DR8: Section collapse control: the heading row is a disclosure button with a ≥24px square glyph; collapsed sections show which of Not established / Changed / Affected they contain; identical on all five; none collapsed on first view; following a link into a collapsed section expands it and focuses the item.
UX-DR9: Correction diff: Before / After / Also affected / Unchanged as labelled prose (before never struck through), Accept / Push back (push back returns to the conversation); opens in the Conversation pane with affected items marked in Understanding; no version-control vocabulary; accepting produces a new version.
UX-DR10: Validation result at the approval moment: only actual findings, each Blocking (2px `text-body` border) or Not blocking (label only), in plain language pointing at its Understanding area; no override; a distinct "The check could not run. Nothing has changed." state; pending as a sentence with no estimate.
UX-DR11: Approval: one primary action; the sentences "The automated check decided this version is valid. You are approving it to go live." and "Conversations already underway will finish on the previous understanding."; no celebration; a failed approval or version creation leaves the previous version live and says so.
UX-DR12: Version lifecycle draft → validated → approved → live shown to the operator; post-go-live propagation explained in words, never a spinner.
UX-DR13: Connect mailbox: one primary action and a sentence that connecting makes the Agent reachable; it is the go-live act, after approval, never a prerequisite for authoring or validation; no cognitive function test (WCAG 3.3.8); a failed connection leaves the Agent not live and says so.
UX-DR14: Agent status line above Activity: Live, mailbox connected · Suspended, not replying or acting · Suspended, replying but not acting · Not live, mailbox not connected · The mailbox is no longer connected. Customers cannot reach the Agent. Suspended states use `action-suspend` colour and words.
UX-DR15: Divergence list: grouped under the three class framings as kinds (shapes: solid 4px rule, double 6px rule, dashed 4px rule, each with its label); item = class + interaction label + one-line request; newest first per group; no counts, severity, retry eligibility, filters, charts or sorting by importance; the empty state "Nothing has come apart since {time}" only alongside the status line.
UX-DR16: Interaction viewer: opened only from an Activity item; customer email verbatim, Agent reply verbatim (or handed-to-human / declined statement), "What this reply was based on" (quoted rules and material linked to Understanding; general knowledge marked; reported actions stated with whether evidence exists), then This was wrong; Suspend reachable; label = email subject + received time with fallback "Customer email · {received date and time}"; no generated explanations, no pipeline or ordered trace; closing returns focus to the Activity item.
UX-DR17: Suspend: one press, no confirmation; Stop actions only adjacent; Let the Agent act again is secondary and never styled like Suspend; result announced and reflected in the status line; failure stated ("Suspend did not apply. The Agent is still live. Try again."); on mobile, Suspend and Stop actions only sit in the sticky top bar of Activity and the viewer.
UX-DR18: Material intake: list of ingested sources with name, version and a provenance `meta` line; progress state while reading; parse failure as the degraded notice "Could not be read. Nothing from it has been used."
UX-DR19: Degraded notice component and the degraded-states table: specification defect, business refusal, platform error, safety halt, general-knowledge answer, refused provenance, refused resolution, authority/evidence unavailable, non-retryable failed effect (with retry eligibility), consequence class — each distinguishable by the operator; platform errors show a reference code.
UX-DR20: Closed vocabulary module holding the EXPERIENCE.md seed list (item states, divergence classes, Agent status, validation, approval, interaction viewer, degraded and failed, pending, empty Activity); every operator-visible status string comes from it.
UX-DR21: Product voice rules: the banned-term list and say-this-instead table; no vertical framing, never "general-purpose", no hiring claim, no market statistics, no celebration; the platform never supplies an Agent voice, persona, mascot or avatar (EX1).
UX-DR22: Ledger tokens from DESIGN.md frontmatter (colours, typography, spacing, `rounded` 0): two weights only; 12px label floor; no shadow, no cards, hairline rules; a hairline is never the only edge of a control; `text-quiet` never on `surface-sunken`; light theme only.
UX-DR23: Actions: primary (one per view), secondary, suspend (outlined, never filled), disabled (dashed border plus a sentence saying why), pending (label replaced by pending text, cannot be pressed again); all real buttons, ≥44px tall.
UX-DR24: Focus indicator: 2px solid `focus-ring` outline at 2px offset on every focusable element; not blue; never removed.
UX-DR25: Application layout: Build desktop = Conversation and "What the Builder currently understands" as independently scrollable panes with sticky pane headings; Run desktop = Activity list beside the interaction detail; Run mobile = full-screen list → full-screen interaction with a back action; one state per screen; sticky elements reserve height with scroll padding (WCAG 2.4.11).
UX-DR26: Responsive: Activity, interaction viewer and Suspend at full fidelity on a phone; Understanding read-only on mobile; authoring, diff, approval and mailbox connection desktop-only in V1; 320 CSS px reflow without horizontal scroll in both orientations; 200% text without loss.
UX-DR27: Accessibility floor WCAG 2.2 AA: never colour alone; keyboard-complete with no traps; real heading structure; polite announcements without moving focus for Builder reply, new Understanding content, diff ready, validation pending/result, material finished/failed, suspend applied/failed, resume applied; panes as labelled regions; targets ≥24px and actions ≥44px; errors identified in text; focus return rules.
UX-DR28: Motion communicates state only; the thinking pulse is no faster than once every two seconds; every animation has a static equivalent under `prefers-reduced-motion`.
UX-DR29: Escalation email: what request triggered it, why the Agent could not safely resolve it, relevant context and evidence, what the human needs to do, and a link to the interaction (sign-in then land on it); product voice and closed vocabulary; plain HTML with a complete plain-text part, readable without images or CSS; may also carry a material divergence (Amendment 1) without any notification system, digest or inbox.
UX-DR30: Out of the V1 UX by decision: dark theme, i18n, offline, compliance/audit/retention surfaces, operator test playground (`m-ux` 35), templates (`m-ux` 22), metrics dashboard, escalation inbox, in-product specification editor, outbound affordances, customer profile, publish-anyway override, editing a promoted version in place.

### FR Coverage Map

Every one of the PRD's 135 requirement IDs (FR1–FR117, NFR1–NFR18) is listed. Where a requirement is delivered across epics, the first epic delivers the part named and the later epic completes it. The **story-level** trace for each ID is in [Story Traceability](#story-traceability) at the end of this document.

| ID | Epic(s) | ID | Epic(s) | ID | Epic(s) |
| --- | --- | --- | --- | --- | --- |
| FR1 | 5 | FR40 | 1 | FR79 | 7 |
| FR2 | 5 | FR41 | 1 | FR80 | 7 |
| FR3 | 5 | FR42 | 1 (prose measured in 4) | FR81 | 4 (vocabulary) · 6, 7 (surfaces) |
| FR4 | 5 | FR43 | 1 | FR82 | 5 (backend) · 7 (action) |
| FR5 | 5 | FR44 | 1 | FR83 | 1 |
| FR6 | 5 | FR45 | 1 | FR84 | 8 |
| FR7 | 5 | FR46 | 1 | FR85 | 1 (port) · 8 (second adapter) |
| FR8 | **declined for V1** (`m-ux` 22) — no story | FR47 | 1 | FR86 | 1 · 8 |
| FR9 | 5 | FR48 | 1 | FR87 | 1 · 8 |
| FR10 | 5 | FR49 | 1 | FR88 | 9 |
| FR11 | 3 (gate) · 6 (approval surface) | FR50 | 1 | FR89 | 1 (log started) · 9 |
| FR12 | 5 | FR51 | 1 | FR90 | 9 |
| FR13 | 1 | FR52 | 1 (declared) · 7 (visible) | FR91 | 9 |
| FR14 | 1 · 6 (Understanding) | FR53 | 1 | FR92 | 9 |
| FR15 | 1 | FR54 | 1 | FR93 | 9 |
| FR16 | 1 | FR55 | 1 | FR94 | 9 (human track, starts now) |
| FR17 | 1 · 2 (garden centre) | FR56 | 1 | FR95 | 1 · 3 |
| FR18 | 1 · 5 · 6 | FR57 | 8 | FR96 | every epic |
| FR19 | 1 | FR58 | 1 | FR97 | 1 |
| FR20 | 1 (in schema) · 4 (evaluated) | FR59 | 1 · 9 | FR98 | 8 |
| FR21 | 1 (content version) · 3 (immutability) | FR60 | 1 | FR99 | 5 |
| FR22 | 1 (suite) · 3 (gate on promotion) | FR61 | 1 | FR100 | 5 |
| FR23 | 1 | FR62 | 1 · 2 (after knowledge edits) | FR101 | 5 · 6 |
| FR24 | 1 | FR63 | 1 | FR102 | 4 |
| FR25 | 1 · 3 | FR64 | 1 | FR103 | 1 (outbox) · 8 (email) |
| FR26 | 3 | FR65 | 1 | FR104 | 5 |
| FR27 | 1 · 3 (durable) | FR66 | 1 | FR105 | 1 |
| FR28 | 3 | FR67 | 1 | FR106 | 1 |
| FR29 | 3 | FR68 | 1 | FR107 | 1 |
| FR30 | 1 (in version hash) · 2 | FR69 | 1 | FR108 | 4 · 7 |
| FR31 | 2 | FR70 | 1 | FR109 | 1 |
| FR32 | 1 (spec projection) · 2 (retrieval) | FR71 | 1 (provisional until gate) | FR110 | 1 (Core) · 7 (surface) |
| FR33 | 1 · 2 | FR72 | 1 | FR111 | 1 |
| FR34 | 1 · 2 | FR73 | 1 · 4 (cost) | FR112 | 1 · 8 |
| FR35 | 2 | FR74 | 1 | FR113 | 8 |
| FR36 | 1 | FR75 | 1 | FR114 | 8 |
| FR37 | 2 | FR76 | 4 | FR115 | 4 |
| FR38 | 1 | FR77 | 1 | FR116 | 1 · 9 |
| FR39 | 1 | FR78 | 4 | FR117 | 5 |

| ID | Epic(s) | ID | Epic(s) | ID | Epic(s) |
| --- | --- | --- | --- | --- | --- |
| NFR1 | 1 | NFR7 | 1 · 2 · 3 | NFR13 | 1 (instrumented) · 4 (reported) |
| NFR2 | 1 | NFR8 | 3 | NFR14 | 1 · 4 |
| NFR3 | 1 | NFR9 | 1 | NFR15 | 9 |
| NFR4 | 1 | NFR10 | 1 | NFR16 | 1 (correlation id) · 4, 7 (reference code) |
| NFR5 | 1 · 2 | NFR11 | 1 · 8 (sentinel) | NFR17 | 1 (startup) · 8 (health) |
| NFR6 | 4 (threshold O5 after 9) | NFR12 | 1 | NFR18 | 1 |

UX-DR1–UX-DR30 are covered by Epics 6, 7 and 8 (traced per story below).

## Epic List

Nine epics, ordered by dependency. Each delivers something a person can use: the **requester** (a business's customer), the **operator** (the business), or the **platform developer** proving the claim. The PRD's E1–E12 are capability groupings, not delivery increments; the column on the right maps them. Epics 1–9 map to the program's phases in `docs/next-phase-proposals/NEXT-PHASE-PLAN.md` §2.

| Epic | User outcome | PRD epics | Program phase |
| --- | --- | --- | --- |
| 1 | A declared business is served by an Agent that reasons freely and acts only within what the business allows | E1, E3 (suite), E4, E5, E7, E8, E9 | 1 (+ close-out) |
| 2 | Requesters get answers grounded in the business's own, version-pinned material | E6 | 2 |
| 3 | The operator changes behaviour safely: immutable versions, gated and approved promotion, rollback | E3 | 3 |
| 4 | The operator learns where the specification is wrong, from evidence rather than transcripts | E9 (evaluation), E10 (backend) | 3 |
| 5 | The operator creates and revises an Agent by conversation and their own material | E2 | 4 |
| 6 | The operator teaches and approves in a workspace built on the Understanding document | E10 surfaces, UX Build | 5 |
| 7 | The operator sees what went wrong, opens it, corrects it, and can stop the Agent from a phone | E10 surfaces, UX Run | 5 |
| 8 | Real customers reach the Agent by email; escalations reach the business | E11 | 6 |
| 9 | The thesis is tested: four businesses through the Builder, one of them real | E12 | 7 |

### Epic 1: Bounded agent runtime for a declared business

A business declared in one specification artifact is served by a model-in-charge Agent: it handles multi-turn requests, asks, reads, acts with confirmation and verification, escalates and halts, and every request is authorized, journaled and evidenced by the Core. Mostly delivered and verified in Phase 1; remaining stories close the proof gate and two lifecycle gaps.
**FRs covered:** FR13–FR19, FR20–FR25 (part), FR27, FR30 (part), FR32–FR34 (part), FR36, FR38–FR56, FR58–FR75, FR77, FR83, FR85–FR87 (part), FR89 (start), FR95–FR97, FR103 (outbox), FR105–FR107, FR109–FR112 (Core), FR116 (start); NFR1–NFR5, NFR7, NFR9–NFR14 (instrumentation), NFR16–NFR18 (part).

### Epic 2: Grounded answers from the business's own material

Requesters receive answers drawn from version-pinned business material, with per-item provenance, declared precedence, freshness on effect-gating reads and the two knowledge tiers; every answer can be reconstructed after a restart. Proven on the garden centre.
**FRs covered:** FR17 (exemplar), FR30, FR31, FR32, FR33, FR34, FR35, FR37, FR62 (after knowledge edits); NFR5, NFR7.

### Epic 3: Safe change — versions, promotion and rollback

The operator's specification moves only through immutable, durable versions; promotion requires a passing validation suite and a recorded, attributable approval; rollback selects an earlier version; running interactions keep their version.
**FRs covered:** FR11, FR21, FR22, FR25, FR26, FR27, FR28, FR29, FR95; NFR7, NFR8.

### Epic 4: Learn from what happened — evaluation and the divergence backlog

Every interaction is evaluated from its record; specification defects, human corrections and adjudicated sampled refusals form one backlog in a closed vocabulary; faithfulness, latency and cost are measured, never claimed. Counterfactual replay is in this epic **only if O11 is approved**.
**FRs covered:** FR20, FR42 (measurement), FR73 (cost), FR76, FR78, FR81, FR102, FR108, FR115; NFR6, NFR13, NFR14, NFR16 (reference code).

### Epic 5: Create and revise an Agent by conversation

The operator describes the business and supplies material; an agent-driven Builder elicits the undocumented rules, surfaces contradictions, records defects instead of inventing defaults, re-derives narrated processes without ordering, and produces a specification and knowledge that pass the gate; it measures its own burden and yield against a seeded fixture.
**FRs covered:** FR1–FR7, FR9, FR10, FR12, FR18 (Builder side), FR82 (backend), FR99, FR100, FR101, FR104, FR117.

### Epic 6: The teaching workspace — Understanding, correction and approval

The operator works in a two-pane workspace: the Builder conversation beside the Understanding document; corrections arrive as exact diffs; validation findings and approval happen at one moment; the Ledger visual system and the accessibility floor hold throughout.
**FRs covered:** FR11 (surface), FR14 (surface), FR18 (surface), FR81 (Build surfaces), FR101 (surface). **UX-DRs:** 1–13, 18, 20–28, 30.

### Epic 7: Review, correct and stop — the Run surfaces

The operator sees the Agent's status, the divergence list and any single interaction with what it was based on; "This was wrong" opens the correction conversation; Suspend and Stop actions only work in one press, from a phone.
**FRs covered:** FR52 (visible), FR79, FR80, FR81 (Run surfaces), FR82, FR108 (entry), FR110 (surface); NFR16 (reportable reference). **UX-DRs:** 14–17, 19, 20, 25–27.

### Epic 8: Go live on email

Customers reach the Agent by email; the adapter handles threading, recipients, attachments, bounces and auto-responder loops against captured traffic; escalations arrive at the business's address as a designed email; connecting the mailbox is the go-live act; credentials never leave the adapter.
**FRs covered:** FR57, FR84, FR85, FR86, FR87, FR98, FR103, FR112, FR113, FR114; NFR11, NFR17. **UX-DRs:** 13, 29.

### Epic 9: Prove it generalises

All four exemplar businesses are built through the Builder; engine leaks, resolution strain, setup effort, the validity floor and the cost slope are recorded; at least one real business runs end to end on real inbound mail; the operator conversations test the premise.
**FRs covered:** FR59, FR88, FR89, FR90, FR91, FR92, FR93, FR94, FR116; NFR15.


---

## Story conventions

Each story carries, between its user story and its acceptance criteria, one compact block:

- **Traces** — the PRD requirement IDs (FR/NFR/EX), Spine ADs, UX-DRs, UX gaps and register IDs it delivers. "(part)" means the remainder is named elsewhere in the Story Traceability table.
- **Depends on** — earlier stories (never later ones in the same epic) and any **decision gate**: a PROPOSED technical choice or OPEN product item the story cannot complete without. Decision gates D1–D13 are defined in `docs/next-phase-proposals/NEXT-PHASE-PLAN.md` §6.
- **Verification** — the test, command or artifact that proves it. For delivered stories, the tests that already prove it, re-run on 2026-10-14.
- **Status** — `done` (delivered and verified), `ready`, or `blocked` (a decision gate is unresolved). Sprint state proper lives in `_bmad-output/implementation-artifacts/sprint-status.yaml`.

Standing acceptance criteria apply to **every** story and are not repeated: `python -m pytest studio/tests -q` and `python -m studio scenarios` pass, the legacy suites stay green, no live model call is made without the user's approval, every new Core safety check has an injection test and a mutation proof (FR96), and each new Core mechanism passes the AD-1 filter (*does it constrain the Agent, or decide its next step?*).

## Epic 1: Bounded agent runtime for a declared business

A business declared in one specification artifact is served by a model-in-charge Agent; every request is authorized, journaled and evidenced by the Core. Stories 1.1–1.8 were delivered and verified in Phase 1 (`IMPLEMENTATION-STATE.md` §0); 1.9–1.12 close the proof gate and the remaining lifecycle and delivery gaps.

### Story 1.1: Declare a business in one specification artifact

As a platform developer,
I want a business's identity, goals, obligations, rules, authorities, capabilities, guards, escalation, sources and criteria declared in one human-readable artifact with a content-addressed version,
So that every runtime projection derives from one diffable source and behaviour changes are attributable to a version.

**Traces:** FR13, FR14, FR15, FR16, FR17 (declaration), FR18, FR19, FR21 (part: content version), FR30 (part: source hashes in the version), FR51, FR52 (part: declared), FR54, FR58, EX1–EX17, AD-4, AD-15, NFR7 (part) · technical choice T2 · **Depends on:** — · **Verification:** `studio/tests/test_specification.py` · **Status:** done

**Acceptance Criteria:**

**Given** the dental or brewery specification with every area established
**When** it is loaded and compiled
**Then** the Agent context, the capability surface and the enforced policy all come from that one artifact (`test_projections_come_from_one_artifact`)
**And** an area left empty is reported as not established, never defaulted (`test_missing_optional_area_is_reported_not_defaulted`).

**Given** an ordering key, sequencing prose or an unknown field
**When** the specification is loaded
**Then** it is rejected with a readable reason (`test_an_ordering_key_is_rejected_with_a_reason`, `test_ordering_in_prose_is_rejected`, `test_unknown_field_is_rejected`).

**Given** the same specification reordered, moved to another folder, or edited
**When** its version is computed
**Then** reordering and moving leave it unchanged, and editing the specification or a source changes it (`test_order_of_entries_carries_no_meaning`, `test_version_is_the_content_not_the_folder`, `test_editing_the_specification_changes_the_version`, `test_editing_a_source_changes_the_version`).

**Given** a fact declared both as an obligation and as a diagnostic input
**When** validated
**Then** it is refused (`test_a_fact_cannot_be_both_obligation_and_diagnostic`).

### Story 1.2: Validate a specification with the platform's own suite

As a platform developer,
I want a platform-owned, domain-agnostic validation suite derived from the specification, with blocking invariants and non-blocking findings,
So that a specification that would promise what the Core refuses, or that lacks what safety requires, can never run.

**Traces:** FR22 (part: the suite), FR23, FR24, FR25 (part), FR95, FR96 (part), FR51, FR52 (part), FR109 (part: declared basis), FR16, FR103 (part: destination declared), FR111 (part: notice declared), FR112 (part: disclosure declared) · **Depends on:** 1.1 · **Verification:** `studio/tests/test_specification.py`; `python -m studio validate` · **Status:** done (the gate in front of promotion and deployment is Story 3.2)

**Acceptance Criteria:**

**Given** a capability that is granted but that policy always denies, implicitly or explicitly
**When** validated
**Then** a blocking finding is produced, and a narrow rule is not misreported (`test_granted_but_always_denied_blocks`, `test_explicit_always_deny_blocks`, `test_a_narrow_rule_is_not_reported_as_always_denying`).

**Given** an effect without success evidence or without a consequence class, a consequential effect without an authority basis, or a liability capability without operator approval
**When** validated
**Then** each blocks with its own finding (`test_effect_without_success_evidence_blocks`, `test_effect_without_consequence_class_blocks`, `test_consequential_effect_without_authority_basis_blocks`, `test_liability_capability_must_require_operator_approval`).

**Given** a missing escalation destination, an empty disclosure, a guard without a detector, an obligation naming an undeclared fact, or an unreadable source
**When** validated
**Then** each blocks, and nothing from an unreadable source is used (`test_missing_escalation_destination_blocks`, `test_empty_disclosure_blocks`, `test_guard_without_detector_blocks`, `test_obligation_naming_an_undeclared_fact_blocks`, `test_an_unreadable_source_blocks_and_nothing_from_it_is_used`).

**Given** a specification that fails the gate
**When** compilation is attempted
**Then** it is refused (`test_compile_refuses_a_specification_that_fails_the_gate`).

### Story 1.3: Every Agent request crosses the Core under a closed taxonomy

As a business operator,
I want the Agent to decide what to do next while the Core authorizes and journals every request it makes,
So that the Agent can reason about anything but can only act within what my business allows.

**Traces:** FR38, FR39, FR40, FR41, FR43, FR49, FR56, FR77, FR96, NFR4, AD-1, AD-2, AD-3, AD-5, AD-9 · **Depends on:** 1.1, 1.2 · **Verification:** `studio/tests/test_core.py`; 12 mutation proofs in `studio/tests/test_checks_are_not_vacuous.py` · **Status:** done

**Acceptance Criteria:**

**Given** a request of any of the seven kinds (`retrieve`, `read`, `effect`, `clarify`, `respond`, `escalate`, `suspend`)
**When** the Agent emits it
**Then** the Core authorizes it and journals the request and its result, reads included (`test_reads_are_authorized_and_journaled`, `test_every_request_and_result_is_journaled`).

**Given** an undeclared capability, a capability used through the wrong kind, or an undeclared goal
**When** requested
**Then** it is refused with a typed reason and nothing runs (`test_undeclared_capability_is_refused`, `test_capability_through_the_wrong_kind_is_refused`, `test_undeclared_goal_is_refused`).

**Given** any denial reason
**When** recorded
**Then** it has exactly one classification among spec_defect, business_refusal and platform_error (`test_every_denial_reason_has_exactly_one_classification`).

**Given** the Agent's view
**When** inspected
**Then** it carries no channel, store or adapter handle (`test_the_agent_view_carries_no_channel_store_or_adapter`)
**And** no Core code selects the Agent's next step.

### Story 1.4: Durable, tenant-scoped episodes

As a requester,
I want my conversation to be one episode that keeps its rules, survives restarts and is never confused with anyone else's,
So that a request left waiting resumes exactly where it was.

**Traces:** FR27, FR60 (part), FR61, FR62, FR63, FR64 (part), FR65, FR66, FR67, FR75, FR86, FR87, NFR1 (part), NFR3, NFR9, NFR10, NFR18, AD-11, AD-12, AD-13, AD-17, AD-22, AD-25 · technical choice T3 · **Depends on:** 1.3 · **Verification:** `studio/tests/test_core.py` · **Status:** done (deadline expiry → 1.10; crash mid-turn → 1.11; restart after a knowledge edit → 2.1; restart after a specification edit → 3.1)

**Acceptance Criteria:**

**Given** a pending episode awaiting a named input
**When** the next inbound message arrives, including in a new process
**Then** the episode resumes on the specification version it started on (`test_pending_resumes_on_the_next_inbound_message`, `test_a_pending_episode_survives_a_new_process`, `test_an_episode_keeps_the_version_it_started_on`)
**And** a pending request that names nothing is refused (`test_pending_must_name_what_it_waits_for`).

**Given** a resent message, or two concurrent messages on one conversation
**When** handled
**Then** the message is processed once and the turns are serialized (`test_a_resent_message_is_processed_once`, `test_concurrent_messages_on_one_conversation_are_serialised`).

**Given** a result arriving after close
**When** recorded
**Then** it is a late result and the resolution is unchanged (`test_a_result_after_close_is_late_and_changes_nothing`).

**Given** a reference belonging to another business
**When** cited
**Then** it is rejected, not filtered (`test_a_reference_from_another_business_is_rejected_not_filtered`)
**And** evidence is removable by episode and by age (`test_evidence_is_removable_by_episode_and_by_age`).

### Story 1.5: Act with confirmation, idempotency and read-back verification

As a requester,
I want the Agent to act only on details I confirmed, exactly once, and to tell me something is done only when the business's system shows it,
So that I am never double-booked and never told a booking exists when it does not.

**Traces:** FR36, FR46, FR53, FR54, FR55, FR70, FR72, FR97, FR109, NFR2, AD-6, AD-9, AD-10 · technical choice T4 · **Depends on:** 1.3, 1.4 · **Verification:** `studio/tests/test_core.py`, `studio/tests/test_brewery.py` · **Status:** done

**Acceptance Criteria:**

**Given** a confirm-required effect
**When** it is requested without a confirmation, with a yes inside a longer sentence, after a bare no, with a changed payload, from another conversation, after the confirmation expired, or a second time
**Then** it is refused and nothing runs (`test_effect_without_confirmation_is_refused_and_nothing_runs`, `test_a_yes_inside_a_longer_sentence_is_not_consent`, `test_a_bare_no_declines`, `test_changing_the_payload_after_consent_is_refused`, `test_a_confirmation_cannot_be_reused_in_another_conversation`, `test_a_confirmation_expires_when_something_else_is_asked`, `test_a_consumed_confirmation_cannot_book_twice`).

**Given** a confirmed effect
**When** executed
**Then** it runs once under a Core-issued key scoped to tenant and episode and is verified by read-back against the business's own system, which stays authoritative — the Core stores evidence, never the business record (`test_confirmed_booking_is_executed_once_and_verified_by_read_back`, `test_the_same_booking_in_two_episodes_is_two_keys`).

**Given** an adapter that hangs, rejects a write, or cannot be read back
**When** the effect runs
**Then** the result is a typed platform error or an unverified effect, never reported as done (`test_a_hung_write_times_out_and_is_not_reported_as_done`, `test_a_rejected_write_is_a_platform_error_not_a_decision`, `test_an_effect_that_cannot_be_read_back_is_unverified_and_cannot_be_claimed`).

**Given** arguments the conversation did not establish, or identity-based authority not yet verified
**When** an effect is requested
**Then** it is refused (`test_effect_arguments_must_have_been_established`, `test_proposing_values_the_conversation_did_not_establish_is_refused`, `test_identity_based_authority_is_refused_until_identity_is_verified`).

### Story 1.6: Guards, two exits, halts, escalation and suspension

As a business operator,
I want urgent or unsafe messages stopped before the Agent reasons about them, every halt to tell the person it has ended, escalations recorded for my declared destination, and the Agent stoppable without a deployment,
So that the Agent never leaves a customer in silence and I can always stop it.

**Traces:** FR44, FR45, FR47, FR48, FR69, FR74, FR103 (part: outbox), FR107, FR110 (part: Core), FR111, FR112, AD-18, AD-21 · technical choice T5 · register CX-03 · **Depends on:** 1.3, 1.4 · **Verification:** `studio/tests/test_core.py` · **Status:** done

**Acceptance Criteria:**

**Given** an urgent message matching a halting guard
**When** it arrives
**Then** the episode halts before the Agent sees it and the requester receives the terminal notice (`test_an_urgent_message_halts_before_the_agent_sees_it`)
**And** a constraining guard reaches the Agent only as a typed constraint (`test_a_constraining_guard_reaches_the_agent_as_a_typed_constraint`).

**Given** an exhausted turn budget, or the Agent repeating the same request
**When** detected
**Then** the episode ends in a declared halt with notices to the requester and the escalation destination (`test_budget_exhaustion_halts_with_notices`, `test_repeating_the_same_request_is_a_stall`)
**And** an Agent failure is a typed result, not a crash (`test_an_agent_failure_is_a_typed_result_not_a_crash`).

**Given** the Agent escalating because the rules are silent, or with an undeclared reason
**When** recorded
**Then** the escalation reaches the outbox with its reason class and a spec defect is recorded (`test_escalating_because_the_rules_are_silent_records_a_spec_defect`, `test_an_undeclared_escalation_reason_is_delivered_and_recorded_as_a_defect`).

**Given** the operator stopping actions only, or suspending the Agent
**When** the next request arrives
**Then** effects are refused while replies continue, or replies and actions stop and in-flight episodes record an outcome (`test_stopping_actions_refuses_effects_but_keeps_replying`, `test_suspending_the_agent_stops_replies_and_records_the_outcome`)
**And** the first message of every episode carries the disclosure (`test_disclosure_is_in_the_first_message_only`).

### Story 1.7: Goals, obligations, grounded claims and verified resolutions

As a business operator,
I want the Agent's business facts to cite material it was given, its conclusions to stay within what I allow, and its resolutions to be backed by evidence,
So that the Agent cannot pass off an invented fact, a forbidden conclusion or an action that never happened.

**Traces:** FR15 (enforced), FR17, FR32 (part: specification projection), FR33 (part), FR34, FR42 (part: typed claims), FR50, FR68, FR71 (provisional until 1.9), FR105, FR106, NFR5 (part), EX12, EX13, AD-7, AD-19, AD-20 · technical choice T6 · **Depends on:** 1.3–1.6 · **Verification:** `studio/tests/test_core.py`, `studio/tests/test_brewery.py` · **Status:** done

**Acceptance Criteria:**

**Given** a claim citing a Core-issued reference
**When** the Agent responds
**Then** it passes, while a minted reference or one issued to another conversation is refused before egress (`test_a_grounded_claim_passes`, `test_a_minted_reference_is_refused`, `test_a_reference_from_another_conversation_is_refused`).

**Given** general knowledge disabled for one business and enabled for another
**When** the Agent makes a general-knowledge claim
**Then** it is refused in the first and allowed and marked in the record in the second (`test_general_knowledge_is_refused_when_disabled`, `test_general_knowledge_is_allowed_here_and_marked_in_the_record`).

**Given** a forbidden conclusion, an undeclared conclusion, or a question the business must never ask
**When** the Agent attempts it
**Then** the first is refused, the second is refused and recorded as a spec defect, and the third is refused (`test_a_forbidden_conclusion_is_refused_and_an_undeclared_one_is_a_spec_defect`, `test_never_ask_is_refused`).

**Given** a resolution claiming an effect with no record, an unverified effect, or a served goal with obligations outstanding
**When** the Agent closes
**Then** it is refused (`test_claiming_a_booking_that_never_happened_is_refused`, `test_claiming_an_unverified_effect_as_done_is_refused_even_without_a_resolution`, `test_a_served_resolution_with_obligations_outstanding_is_refused`)
**And** only a declared waiver satisfies an obligation, and a goal switch parks the previous goal (`test_only_a_declared_waiver_is_accepted`, `test_a_declared_waiver_satisfies_an_obligation`, `test_switching_goals_parks_the_previous_one`).

### Story 1.8: Provider-agnostic Agent boundary, scenario channel and two businesses

As a platform developer,
I want the Agent behind a boundary we own, reachable through any OpenAI-compatible endpoint or run credential-free, and two Brief exemplars running on the same Core,
So that the architecture is demonstrable with zero tokens and the second business costs a specification, not code.

**Traces:** FR41, FR73 (part: model calls with tokens and latency), FR83, FR85 (part: channel port), FR89 (part: leak log started), FR116 (part), NFR12, NFR13 (part: instrumented), NFR14 (part: instrumented), NFR16 (part: episode id on every record), NFR17 (part: startup validation), AD-14, AD-16 · technical choices T1, T7, T8 · **Depends on:** 1.3–1.7 · **Verification:** `studio/tests/test_agent_boundary.py`, `studio/tests/test_end_to_end.py`, `studio/tests/test_brewery.py`; `python -m studio scenarios --today 2026-10-13` → 10/10 PASS, 0 model calls · **Status:** done for credential-free mode; the live model agent has made **no live call yet** (Story 1.9)

**Acceptance Criteria:**

**Given** no model credentials
**When** the product starts
**Then** it runs credential-free, and a half-configured endpoint or invalid model settings are rejected at startup (`test_no_credentials_means_credential_free_mode`, `test_a_half_configured_endpoint_is_rejected_at_startup`, `test_invalid_model_settings_are_rejected_at_startup`).

**Given** a configured endpoint
**When** the Agent decides
**Then** the port sends a plain `/v1` request configured only by environment, with no vendor SDK, every call is recorded with tokens and latency, and failures are typed (`test_the_port_sends_a_plain_v1_request_configured_by_environment`, `test_model_failures_are_typed_errors_with_a_call_record`, `test_a_valid_model_request_reaches_the_core_and_its_call_is_recorded`).

**Given** the dental scenarios D1–D6 and the brewery scenarios B1–B4
**When** run credential-free
**Then** all ten pass on record-level expectations (`test_scenario`)
**And** the brewery needed zero Core changes (engine-leak log entry 1, `PROOF-GATE.md`).

### Story 1.9: Complete the proof gate with a live comparison

As a platform developer,
I want the model-in-charge runtime measured with a real model on the same scenarios and compared with the fifteen-node system on all nine axes,
So that the architecture is committed on evidence, inline resolution validation is confirmed or demoted, and context assembly has a measured baseline.

**Traces:** PRD §7.5 and §12; Spine Proof Gate and Deferred (inline resolution validation, context assembly); `m-arch` 47 (user); FR71; NFR13; NFR14; register A-18 · **Depends on:** 1.1–1.8 · **decision gate D1** (approval to spend on one live run) · **Verification:** `python -m studio scenarios --live --runs 3 --max-cost 0.25 --today 2026-10-13` (full command in `PROOF-GATE.md`); updated `PROOF-GATE.md` · **Status:** blocked (D1)

**Acceptance Criteria:**

**Given** the user's approval and a spend cap
**When** the ten scenarios run three times against a live model
**Then** the run stops before exceeding the cap and reports its actual cost.

**Given** the live run's recorded model calls
**When** the gate report is written
**Then** axes 3 and 4 state model calls per turn and per-call and per-turn latency (p50, p95) from the store, beside the legacy figures.

**Given** each scenario's record-level expectations
**When** evaluated across the three runs
**Then** the pass rate per scenario is reported, and every failure is classified as an Agent, specification or Core finding with its evidence.

**Given** every resolution the live model claimed
**When** inline resolution validation refused one
**Then** each refusal is counted and judged correct or false, and the report states whether inline validation is relied on or demoted to offline evaluation.

**Given** the nine axes
**When** the verdict is written
**Then** it is pass or fail, and a fail is escalated to the user with evidence, never patched (PRD §7.5)
**And** the measurement is recorded as the context-assembly baseline for Story 2.3.

### Story 1.10: A deadline expiry resumes a pending episode as an external event

As a requester,
I want a request that waits on something with a deadline to be picked up again when the deadline passes,
So that a lapsed hold or a missing document is dealt with instead of silently forgotten.

**Traces:** FR60 (remainder: expiry is an external system event), FR61, FR63, AD-1, AD-12, AD-22 · replaces NEXT-PHASE-PLAN §7's former lapsed-pending mitigation · **Depends on:** 1.4; 1.9 (the proof gate sits in front of further E4–E9 runtime work, PRD §7.5 and §12) · **Verification:** new tests in `studio/tests/test_core.py`; injection test and mutation proof · **Status:** ready

**Acceptance Criteria:**

**Given** a pending episode whose named input carries a declared deadline
**When** the clock passes the deadline and the expiry source runs
**Then** an external-system event is recorded on the episode and the episode resumes with the Agent receiving the expiry as its input.

**Given** that resumed episode
**When** the Core handles the expiry
**Then** the Core itself takes no action: no reply, escalation or close is initiated by the Core, and the next step is the Agent's request.

**Given** an expiry for an episode that has already closed, or the same expiry delivered twice
**When** recorded
**Then** the first is a late result that changes nothing and the second is processed once.

**Given** the expiry check
**When** it reads the time
**Then** it uses the recorded clock (AD-12), so tests drive it deterministically
**And** disabling the expiry source makes a test fail (FR96).

### Story 1.11: An in-flight episode survives a crash mid-turn

As a requester,
I want a conversation interrupted by a platform failure to continue without a repeated action,
So that a crash never books me twice or loses what I was told.

**Traces:** FR64 (remainder), NFR1 (remainder), AD-12 · **Depends on:** 1.4, 1.5; 1.9 (proof gate, PRD §7.5 and §12) · **Verification:** new crash-injection tests (stop the process between journal writes, then continue in a new process) · **Status:** ready

**Acceptance Criteria:**

**Given** a crash after an effect executed and its evidence was written, but before the reply was journaled
**When** a new process handles the episode's next inbound message
**Then** the effect is not executed again and its evidence is present once.

**Given** a crash after the Agent's decision was journaled but before authorization
**When** the episode continues
**Then** the decision is not treated as authorized, and nothing un-journaled is read.

**Given** a crash injected at each journal boundary of a turn (parametrized)
**When** the episode continues in a new process
**Then** its record is consistent — no orphan effect, no duplicate step — and its lifecycle is exactly one of active, pending or closed.

### Story 1.12: Credential-free CI on a clean checkout

As a platform developer,
I want every push to run the full credential-free suite on a fresh clone,
So that "green" means green for the repository and not only for one working tree.

**Traces:** register D-05 (unmet sprint commitment); Additional Requirements: verification discipline; CLAUDE.md clean-checkout rule · **Depends on:** 1.1–1.8 · **decision gate D3** (authorization to commit and push) · **Verification:** a passing CI run on the remote, and one deliberately failing branch run · **Status:** blocked (D3)

**Acceptance Criteria:**

**Given** a clean clone, with line endings as checked out
**When** CI runs
**Then** `python -m pytest studio/tests -q`, `python -m studio scenarios`, `python -m pytest builder_platform/tests -q`, `python -m pytest claude_plugin/tests -q` and the three `selftest.py` pass with no model credential configured.

**Given** the CI configuration
**When** inspected
**Then** it holds no secret and cannot make a live model call.

**Given** a failing test on a branch
**When** pushed
**Then** the job fails.

## Epic 2: Grounded answers from the business's own material

Requesters receive answers drawn from version-pinned business material, with per-item provenance, declared precedence, freshness on effect-gating reads and both knowledge tiers; every answer is reconstructible after a restart. Phase 2 findings P2-F1–P2-F5 (NEXT-PHASE-PLAN §3.1, verified in code 2026-10-14) are the starting point. This epic is E6, which PRD §7.5 and §12 place behind the proof gate: it starts after Story 1.9's verdict. Technical choices T9–T12 are **PROPOSED, not approved**; the stories that depend on them name the gate.

### Story 2.1: Pin source material so episodes survive knowledge edits

As a requester,
I want an answer I was given to stay grounded in the version of the business's material that was in force when my conversation started,
So that a leaflet revised tomorrow cannot change or break a conversation already underway.

**Traces:** FR30, FR33 (source, version, locator on every reference), FR62 (after knowledge edits), NFR7, AD-8, AD-11 · finding P2-F2 · **Depends on:** Epic 1, including the proof-gate verdict of 1.9 · **Verification:** new `studio/tests/test_knowledge.py`; injection test and mutation proof · **Status:** ready

**Acceptance Criteria:**

**Given** an episode started while a source was at version v1
**When** the source file is edited and the process restarts
**Then** the resumed episode is served v1's text and every reference issued to it still resolves (this fails today).

**Given** a source's content
**When** it is pinned
**Then** it is stored once, addressed by its content hash, and never rewritten.

**Given** any provenance reference
**When** inspected
**Then** it names tenant, source, source version and locator.

**Given** the snapshot step disabled
**When** the suite runs
**Then** the restart test fails (FR96).

### Story 2.2: Reconstruct every answer from the record alone

As a business operator,
I want to see exactly which version of which material an answer relied on, even after my files changed,
So that I can tell whether the Agent or my material was wrong.

**Traces:** FR37, FR73 (part: retrievals), NFR7, AD-6, AD-8 · **Depends on:** 2.1 · **Verification:** new tests run with the business's knowledge folder removed · **Status:** ready

**Acceptance Criteria:**

**Given** a closed episode
**When** it is reconstructed using only the store
**Then** every reply is returned with each item its claims cited — text, source, version, locator — and each retrieval's query and results.

**Given** the business's knowledge folder deleted after the episode
**When** reconstruction runs
**Then** it returns the same result.

**Given** a reply whose claims cite nothing
**When** reconstructed
**Then** it is shown as citing nothing, never as empty grounding.

### Story 2.3: Choose context assembly by measurement

As a platform developer,
I want what the Agent always sees, and what it must retrieve, decided by measured cost and quality rather than by design up front,
So that retrieval is a real decision the Agent makes, provenance stays exact, and the product scales past tiny sources.

**Traces:** AD-7, AD-8, Spine Deferred (context assembly: "measured, not designed up front"), FR32, FR33, NFR5, FR38 (the Agent decides when to retrieve), NFR13, NFR14 · finding P2-F1 · technical choices **T9 (PROPOSED)** and **T10 (PROPOSED)** · **Depends on:** 2.1, 2.2, 1.9 (baseline) · **decision gates D2 (T9), D4 (T10)**, and D1-style approval for the comparison run · **Verification:** credential-free tests for both modes; one approved live comparison run · **Status:** blocked (D2, D4)

**Acceptance Criteria:**

**Given** the Core's context-assembly setting
**When** it is set to *standing* (today's behaviour: source items in view, references issued at episode start) or *on-demand* (source material reachable only through `retrieve`, references issued for the items a retrieval returns)
**Then** the specification projection stays in context in both modes, and the setting is platform configuration validated at startup, never business configuration (AD-15).

**Given** on-demand mode
**When** a claim cites a source item no retrieval in this episode returned
**Then** it is refused before egress as unissued.

**Given** any retrieval
**When** recorded
**Then** its evidence lists, per returned item, the source, version, locator and reference, and the retriever sits behind a port so another implementation can replace the lexical default (T10).

**Given** the user's approval of a live comparison
**When** the same scenarios run in both modes
**Then** the report gives calls per turn, latency, pass rate and retrieval misses per mode, and the default mode is set by the user's decision on T9, not by this story.

### Story 2.4: Resolve conflicting sources by declared precedence

As a business operator,
I want my declared order of authority applied when two of my documents disagree,
So that a customer is never quoted an outdated price list over the current one.

**Traces:** FR31, EX14, AD-7 · finding P2-F3 · technical choice **T11 (PROPOSED)** · **Depends on:** 2.1 · **decision gate D5 (T11)** · **Verification:** new tests; injection test and mutation proof · **Status:** blocked (D5)

**Acceptance Criteria:**

**Given** two sources of different declared precedence with a conflicting section
**When** the item is retrieved
**Then** the higher-precedence item is returned as authoritative, and the lower one is marked superseded.

**Given** a claim citing a superseded item
**When** the Agent responds
**Then** it is refused with a typed reason, before egress.

**Given** a source conflicting with the specification
**When** resolved
**Then** the specification outranks it.

**Given** conflicting sources with no declared precedence between them
**When** validated
**Then** the suite reports a finding naming both sources.

### Story 2.5: Require fresh reads before effects that depend on them

As a requester,
I want an action taken on information that was current when it was taken,
So that I am not double-booked on yesterday's availability.

**Traces:** FR35, register U3 / reconcile G45 (measure the read-to-effect gap), AD-1, AD-18 · finding P2-F4 · technical choice **T12 (PROPOSED)** · **Depends on:** Epic 1 · **decision gate D6 (T12)** · **Verification:** new tests; injection test and mutation proof; U3 distribution in the phase report · **Status:** blocked (D6)

**Acceptance Criteria:**

**Given** an effect contract that names the read it depends on and that read's maximum age
**When** the effect is requested with no such read in the episode, or with one older than allowed
**Then** it is refused with a typed reason (missing or stale basis), and the Core schedules no read on the Agent's behalf.

**Given** a fresh read
**When** the effect is requested
**Then** it proceeds, and the gap between read and effect (turns and seconds) is recorded on the effect's evidence.

**Given** freshness declared globally rather than per read or per contract
**When** the specification is loaded
**Then** it is rejected.

**Given** all scenarios after this story
**When** the phase report is written
**Then** it states the distribution of read-to-effect gaps, which answers U3.

### Story 2.6: A garden centre served from its own material

As a garden-centre customer,
I want advice on my dying plant and an honest account of my guarantee position,
So that I am helped without being accused of killing the plant.

**Traces:** FR16 (liability class), FR17, FR34, FR50, FR69, FR89 (leak log entry), FR116, EX7, EX13; Brief exemplar 3 (`spec-stress-test.md` §3); register V-09, CX-04 · finding P2-F5 · **Depends on:** 2.1, 2.2 (needs no new Core feature, finding P2-F5; its scenarios are re-run whenever 2.3–2.5 land) · **Verification:** `studio/businesses/garden-centre/` (specification, guides, scenarios — no Python); `python -m studio scenarios` · **Status:** ready

**Acceptance Criteria:**

**Given** the garden-centre specification and care guides
**When** validated
**Then** it passes the gate with no business-specific Python.

**Given** the lavender case ("in a pot on my balcony… gone grey and crispy… I water it every day")
**When** run credential-free
**Then** the record shows care advice marked as general knowledge, the guarantee position stated as undetermined, the claim deferred (pending or handed to a human) and not refused, and no conclusion of neglect.

**Given** a customer who wants advice and a replacement
**When** both goals are pursued
**Then** one is active at a time and parking and resumption are explicit (FR50).

**Given** an excluded category, an expired guarantee, or a missing proof of purchase
**When** a claim is attempted
**Then** it is refused citing the rule.

**Given** the build of this business
**When** it is complete
**Then** the engine-leak log has an entry: no Core change, or each change classified per FR116.

## Epic 3: Safe change — versions, promotion and rollback

The operator's specification moves only through immutable, durable versions; promotion needs a passing suite and a recorded approval; rollback selects an earlier version; running interactions keep theirs.

### Story 3.1: Durable, immutable specification versions

As a business operator,
I want every version of my specification kept exactly as it was,
So that an interaction resumed after a restart runs on the rules it started with, even if the files changed since.

**Traces:** FR21, FR27, NFR7, NFR8, AD-11, AD-23 · finding P2-F2 (specification half) · **Depends on:** Epic 1 · **Verification:** new tests in `studio/tests/test_versions.py` · **Status:** ready

**Acceptance Criteria:**

**Given** a specification version is registered
**When** stored
**Then** its canonical content and compiler version are written durably under its content-addressed identifier.

**Given** a running episode pinned to version v1
**When** the specification files change and the process restarts
**Then** the episode continues on v1, loaded from the store.

**Given** a promoted version
**When** anything attempts to change it
**Then** the attempt is refused, and different content can never take an existing identifier.

### Story 3.2: Promote only through the gate and a recorded approval

As a business operator,
I want a new version to go live only when the platform's check passes and I have approved it,
So that nothing changes my Agent's behaviour behind my back.

**Traces:** FR11, FR22 (gate in front of promotion and deployment), FR25, FR28, FR29, FR95, AD-23; UX gap 7 (operator is the approver, approval is not validity); PRD O1 stays open beyond V1 · **Depends on:** 3.1 · **Verification:** new tests; injection test and mutation proof · **Status:** ready

**Acceptance Criteria:**

**Given** a version with a blocking finding
**When** promotion is attempted
**Then** it is refused, and no override exists in any interface.

**Given** a version without an approval record
**When** promotion is attempted
**Then** it is refused.

**Given** an approval
**When** recorded
**Then** it names the approver and time and is bound to that exact version, so an approval of v2 cannot promote v3.

**Given** a promotion
**When** it completes
**Then** new episodes start on the new live version, running episodes keep theirs, and the promotion is recorded as reviewable and attributable
**And** nothing but a promotion changes the live version (FR29).

**Given** the runtime starting for a tenant
**When** it loads a specification
**Then** it loads only the live promoted version, so deployment has no weaker check (FR25).

**Given** the suite cannot run
**When** promotion is attempted
**Then** the outcome is "could not run", distinct from a failure, and nothing changes.

### Story 3.3: Readable validation findings and version states

As a business operator,
I want every validation finding to say whether it blocks and which part of my business it concerns, and every version to have a clear state,
So that I know what to fix and what is live.

**Traces:** FR22, FR81; UX gaps 5 (version lifecycle) and 13 (finding shape); UX-DR10, UX-DR12 (data) · **Depends on:** 3.1, 3.2 · **Verification:** contract tests on the finding and version-state types · **Status:** ready

**Acceptance Criteria:**

**Given** any validation finding
**When** produced
**Then** it carries an identifier, whether it blocks, a plain-language message, the expression area it concerns, and the item it points at where there is one.

**Given** any version
**When** its state is asked for
**Then** it is exactly one of draft, validated, approved, live, derived from records rather than stored as a free field.

**Given** these two contracts
**When** introduced
**Then** they are recorded in the decision register as technical contracts answering UX gaps 5 and 13.

### Story 3.4: Roll back by selecting an earlier version

As a business operator,
I want to return to an earlier version I already approved,
So that a bad change can be undone at once.

**Traces:** FR26, FR28, NFR8, AD-23 · UX gap 16 (the rollback **surface** is undesigned; see Story 7.7) · **Depends on:** 3.2 · **Verification:** new tests · **Status:** ready

**Acceptance Criteria:**

**Given** an earlier promoted version
**When** it is selected
**Then** it becomes live with no rebuild and no migration, and the act is recorded and attributable.

**Given** a version that was never promoted
**When** selected for rollback
**Then** it is refused.

**Given** episodes running on the version being rolled back from
**When** rollback completes
**Then** they keep their pinned version.

## Epic 4: Learn from what happened — evaluation and the divergence backlog

Every interaction is evaluated from its record; specification defects, human corrections and adjudicated sampled refusals form one backlog in a closed vocabulary; faithfulness, latency and cost are measured, never claimed.

### Story 4.1: Evaluate every interaction from its record

As a business operator,
I want each interaction judged against what good looks like for my business, computed from the record,
So that nobody has to read transcripts to know how the Agent is doing.

**Traces:** FR20 (evaluated), FR67, FR72, FR73 (cost), FR76, PRD §10.1–10.2 and §10.4 guards, NFR13, NFR14 · **Depends on:** Epics 1–3 · **Verification:** new `studio/evaluation/` tests over recorded scenario episodes · **Status:** ready

**Acceptance Criteria:**

**Given** closed episodes
**When** evaluated
**Then** every §10.1 per-episode criterion is computed from the store alone.

**Given** a business's episodes
**When** the per-business report is produced
**Then** it gives the §10.2 shares, with Agent failures reported separately from blocks by the business's own rules, and never reads lifecycle as success or failure.

**Given** a business criterion
**When** it names a machine check
**Then** it is evaluated, and a criterion without one is listed for human judgement, never scored.

**Given** model calls on the record
**When** the report is produced
**Then** per-episode latency and cost (from configured prices) are reported with no threshold.

### Story 4.2: Specification defects become the backlog

As a business operator,
I want one list of the places my specification led the Agent astray,
So that I fix the specification, not chase correct refusals.

**Traces:** FR77, FR78, FR48, AD-5 · **Depends on:** 4.1 · **Verification:** new tests · **Status:** ready

**Acceptance Criteria:**

**Given** denials of all three classifications
**When** the backlog is built
**Then** it holds only specification defects.

**Given** a backlog item
**When** inspected
**Then** it names the episode, the specification version in force and the reason, and building the backlog twice yields the same items.

### Story 4.3: Record human corrections as divergences

As a business operator,
I want to record that an answer was wrong even when nothing was refused,
So that confidently wrong answers reach the same backlog as refusals.

**Traces:** FR102, FR108, PRD §10.2 (corrections per hundred and their trend) · **Depends on:** 4.2 · **Verification:** new tests · **Status:** ready

**Acceptance Criteria:**

**Given** an operator's correction on an episode
**When** recorded
**Then** it is stored against the episode and the specification version in force, with who made it and when.

**Given** a correction
**When** the backlog is built
**Then** it appears as a specification defect.

**Given** episodes and corrections over time
**When** reported
**Then** corrections per hundred episodes and their trend are computable.

### Story 4.4: Sample business refusals for adjudication

As a business operator,
I want a share of my Agent's refusals set aside for a human to judge,
So that my specification cannot drift toward strictness unnoticed.

**Traces:** FR115; UX gap 15 (who adjudicates, and where, is **OPEN** — see Story 7.8) · **Depends on:** 4.2 · **Verification:** new tests; deterministic sampling under a seed · **Status:** ready (queue and adjudication record only)

**Acceptance Criteria:**

**Given** a business's declared refusal sample rate
**When** business refusals occur
**Then** that share is sampled deterministically and queued, and the sampling is recorded.

**Given** a sampled refusal adjudicated wrong
**When** recorded
**Then** it enters the backlog as a specification defect, and one adjudicated right does not.

### Story 4.5: A closed vocabulary and reportable error references

As a business operator,
I want every status, refusal and failure I see in fixed, plain words, and a reference I can quote when something on your side fails,
So that I can understand and report problems.

**Traces:** FR81, NFR16 (reportable correlation), UX-DR20; UX gap 17 (reference format: technical choice, recorded) · **Depends on:** 4.1 · **Verification:** a test that fails if an operator-facing interface emits a status string outside the vocabulary · **Status:** ready

**Acceptance Criteria:**

**Given** the vocabulary module
**When** inspected
**Then** it holds the EXPERIENCE.md seed list in full.

**Given** any operator-facing status, refusal or failure
**When** produced
**Then** it comes from the vocabulary.

**Given** a platform error
**When** reported
**Then** it carries a reference code that resolves to the episode and its records.

### Story 4.6: Measure faithfulness, never claim it

As a platform developer,
I want how often replies say more than their citations support measured over the record,
So that the product reports meaning-faithfulness honestly as a rate.

**Traces:** NFR6, FR42 (prose remainder), PRD review F6.5 (no evaluator FR); O5 (threshold) stays open until Epic 9 · **Depends on:** 4.1 · **Verification:** evaluator tests with seeded faithful and unfaithful replies · **Status:** ready (live evaluation needs approval per run)

**Acceptance Criteria:**

**Given** recorded replies and their cited items
**When** the evaluator runs
**Then** it reports per business the rate of replies stating business facts that their citations do not cover.

**Given** credential-free mode
**When** the evaluator cannot run a model
**Then** the report says "not measured", never zero.

**Given** the report
**When** read
**Then** it states a rate with no threshold and makes no guarantee.

### Story 4.7: Replay a closed interaction against a later version

As a business operator,
I want to see what my Agent would now do differently on a past interaction,
So that I know a correction fixes the case that prompted it.

**Traces:** PRD O11; UX gap 8; register E-04 · **Depends on:** 4.1, 3.1, 2.2 · **decision gate D7 (O11: is counterfactual replay in V1?)** · **Verification:** replay tests credential-free; any live replay needs approval · **Status:** blocked (D7)

**Acceptance Criteria:**

**Given** a closed episode and a later specification version
**When** replayed
**Then** the recorded inbound messages and external results are fed again, no effect reaches any external system, and the differences in requests, refusals and resolution are reported.

**Given** a replay
**When** it finishes
**Then** the original episode's record is unchanged.

## Epic 5: Create and revise an Agent by conversation

The operator describes the business and supplies material; an agent-driven Builder elicits what no document holds and produces a specification and knowledge that pass the gate. This is the PRD's highest-risk epic (E2). **Soft prerequisite:** the 2–3 operator conversations of Story 9.8 (FR94) should precede Story 5.3, so that the elicitation design is tested against real operators rather than none (PRD A4).

### Story 5.1: A Builder conversation that drafts a specification and its knowledge

As a business operator,
I want to describe my business in my own words and get a draft of how my Agent would work,
So that I never fill in a form to create an Agent.

**Traces:** FR1, FR9, FR10, FR19, AD-4 (the Builder produces the artifact and never compiles), AD-14, NFR12 · **Depends on:** Epics 1–3 · **Verification:** new `studio/builder/` tests with a scripted model; output loads through `studio.spec` · **Status:** ready

**Acceptance Criteria:**

**Given** a new session
**When** it opens
**Then** the first turn is the open invitation, and no question bank or fixed question list exists in the Builder's code.

**Given** a session
**When** the Builder reasons
**Then** it runs behind the same provider-agnostic runtime boundary as the Agent, and credential-free tests drive it with a scripted model.

**Given** a session's output
**When** produced
**Then** it is a draft specification plus knowledge files that load through `studio.spec`, and the Builder imports nothing from the Core compiler.

**Given** a draft
**When** it exists
**Then** it is never live until promoted through Story 3.2.

### Story 5.2: Take in the operator's own material

As a business operator,
I want to hand over the price lists, terms and guides I already have,
So that the Agent starts from my real material.

**Traces:** FR2, FR30, FR117 (unreadable source); UX gap 10 (formats, size and duration limits — technical defaults chosen and recorded) · **Depends on:** 5.1, 2.1 · **Verification:** ingestion tests per format, including a corrupt file · **Status:** ready

**Acceptance Criteria:**

**Given** plain text, Markdown or a PDF with extractable text
**When** supplied
**Then** it is stored as a version-pinned source with provenance and is available to the Builder.

**Given** a file that cannot be read, or a format not accepted
**When** supplied
**Then** the outcome is stated to the operator and nothing from it is used.

**Given** the chosen limits
**When** recorded
**Then** they appear in the decision register as the technical answer to UX gap 10.

### Story 5.3: Interview for what no document holds

As a business operator,
I want the Builder to ask about the exceptions, thresholds and limits that live only in my head, and about where practice differs from what is written,
So that my Agent knows how my business really works.

**Traces:** FR3, FR4, FR7 · **Depends on:** 5.1, 5.2 · soft prerequisite Story 9.8 · **Verification:** fixture tests where the amount of withheld information varies · **Status:** ready

**Acceptance Criteria:**

**Given** two fixtures, one complete and one withholding several rules
**When** the Builder runs on each
**Then** it asks more questions where more is missing, never from a fixed list.

**Given** material stating a policy
**When** the Builder interviews
**Then** it asks whether practice matches what is written.

**Given** an answer about a prohibition, threshold, exception, authority limit or always-escalate case
**When** given
**Then** it lands in the matching expression area of the draft.

### Story 5.4: Surface contradictions and record what cannot be settled

As a business operator,
I want to be shown where my documents disagree with each other or with me, and to have unresolved points recorded rather than guessed,
So that the Agent never improvises a rule I did not make.

**Traces:** FR5, FR6, FR31 (precedence asked), FR48 (build side), FR117 (a new source contradicting a promoted specification) · **Depends on:** 5.2, 5.3 · **Verification:** fixtures with seeded contradictions · **Status:** ready

**Acceptance Criteria:**

**Given** two sources that conflict, or a source that conflicts with what the operator says
**When** the Builder finds it
**Then** it raises the conflict with the operator and does not choose silently.

**Given** a point the operator cannot settle
**When** the session continues
**Then** it is recorded as a specification defect and its area stays "Not established", with no default.

**Given** a new source that contradicts the promoted specification
**When** supplied
**Then** the conflict is a stated outcome the operator sees.

### Story 5.5: Turn a narrated process into declarations, not steps

As a business operator,
I want to describe how we do things "first this, then that" and have it understood,
So that the Agent knows what must be true, not a script to follow.

**Traces:** FR104, FR18, FR24 (backstop), AD-1 · **Depends on:** 5.3 · **Verification:** fixtures with narrated processes; the gate rejects any ordering the Builder emits · **Status:** ready

**Acceptance Criteria:**

**Given** a narration such as "first we check the diary, then we take a deposit"
**When** the Builder records it
**Then** the draft declares an obligation of the booking goal and a granted capability, and contains no ordering.

**Given** a Builder output that contains ordering
**When** validated
**Then** the gate rejects it with a reason.

### Story 5.6: The Builder measures its own burden and yield

As a platform developer,
I want each Builder session to record what it cost the operator and what it recovered,
So that a Builder that asks less is never mistaken for a better one.

**Traces:** FR12, FR99, input to FR91 · **Depends on:** 5.3, 5.4 · **Verification:** session record tests · **Status:** ready

**Acceptance Criteria:**

**Given** a session that reaches a passing validation suite
**When** it ends
**Then** its record holds the wall-clock time to that point and the number of sources used.

**Given** the same session
**When** reported
**Then** the rules recovered by interview, the contradictions surfaced and the defects recorded are reported together with burden, and never alone.

### Story 5.7: Test elicitation against a seeded business

As a platform developer,
I want a business whose key rules exist only in the operator's answers,
So that how well the Builder elicits is measured, not asserted.

**Traces:** FR100, FR3, FR4, FR5, FR7 (made falsifiable) · **Depends on:** 5.3–5.6 · **Verification:** the fixture runs credential-free with a scripted operator in CI; a live run needs approval · **Status:** ready

**Acceptance Criteria:**

**Given** a seeded business with a known set of withheld rules
**When** the Builder runs against its scripted operator
**Then** the report counts rules recovered, rules invented and rules silently defaulted.

**Given** the fixture
**When** inspected
**Then** the withheld rules exist nowhere in the material supplied to the Builder.

### Story 5.8: Revise a promoted specification by conversation, with an exact change

As a business operator,
I want to say in my own words what is wrong and see precisely what will change before it does,
So that I can correct my Agent without editing anything.

**Traces:** FR101, FR82 (backend), FR21, FR28; UX-DR9 (data contract); UX gap 12 (items addressable by area and identifier) · **Depends on:** 5.1, 3.2 · **Verification:** diff tests over pairs of specifications · **Status:** ready

**Acceptance Criteria:**

**Given** a promoted version, a correction in the operator's words and an optional origin (a section, a divergence item or an interaction)
**When** the Builder proposes a change
**Then** Before, After, Also affected and Unchanged are computed from the two specifications, not narrated by a model.

**Given** the proposal
**When** the operator accepts
**Then** a new draft version exists, and it reaches live only through the same gate and promotion (Story 3.2).

**Given** the proposal
**When** the operator pushes back
**Then** nothing changes and the conversation continues.

### Story 5.9: Unfinished sessions are stated outcomes

As a business operator,
I want an interrupted or failed Builder session to say what state it is in,
So that I never mistake half an Agent for a whole one.

**Traces:** FR117 · **Depends on:** 5.1 · **Verification:** session lifecycle tests · **Status:** ready

**Acceptance Criteria:**

**Given** a session abandoned part-way
**When** reopened
**Then** its draft is labelled incomplete and never presented as complete.

**Given** a Builder turn that fails
**When** it fails
**Then** the outcome says the Builder could not reply and nothing changed, and the operator's message is kept.

## Epic 6: The teaching workspace — Understanding, correction and approval

The operator's Build surfaces from EXPERIENCE.md and DESIGN.md: the Builder conversation beside the Understanding document, the correction diff, and validation and approval at one moment. The web stack is a technical choice recorded in the program. Each story meets UX-DR21–UX-DR28 for the surfaces it adds; Story 6.6 verifies them across the epic.

### Story 6.1: The cold-start workspace and the Builder conversation

As a business operator,
I want to open a workspace and simply start telling it about my business,
So that creating an Agent feels like briefing a colleague.

**Traces:** FR1, FR3, NFR3 (operator access scoped to one tenant); UX-DR2, UX-DR3, UX-DR4, UX-DR21, UX-DR22, UX-DR23, UX-DR24, UX-DR25 (Build), UX-DR28 · **Depends on:** Epic 5 · **Verification:** UI tests; banned-term and token-conformance checks · **Status:** ready

**Acceptance Criteria:**

**Given** a signed-in operator with no specification yet
**When** the workspace opens
**Then** the only prompt is the open invitation, material is optional, and there is no funnel, welcome screen, template or step indicator.

**Given** the operator
**When** signed in
**Then** they reach only their own business's data, and sign-in involves no cognitive function test (WCAG 3.3.8).

**Given** a Builder turn in progress, or one that fails
**When** shown
**Then** the thinking state is a closed-vocabulary line that is static under reduced motion, and a failure keeps the operator's message for resending.

**Given** any screen of this epic
**When** checked
**Then** it uses only the DESIGN.md tokens, no shadows, radius or cards, and none of the banned terms.

### Story 6.2: The Understanding document

As a business operator,
I want to read what the Builder understands about my business as a document in five sections,
So that I recognise my business written down, including what is not yet established.

**Traces:** FR14, FR18 (surface); UX-DR5, UX-DR6, UX-DR7, UX-DR8; UX gap 12 · **Depends on:** 6.1 · **Verification:** DOM tests (five peer sections covering EX1–EX17; no arrows, step numbers, progress or checklist; every item has one state label and shape) · **Status:** ready

**Acceptance Criteria:**

**Given** a draft
**When** Understanding renders
**Then** it shows the five sections mapping EX1–EX17 as EXPERIENCE.md tabulates, under a persistent frame saying this is what the Builder currently understands.

**Given** any item
**When** rendered
**Then** it carries exactly one of the four states as text plus its shape, and "Not established" is never rendered as empty, blank, a default or "no".

**Given** the authoring surface
**When** inspected
**Then** it has no form fields, toggles, arrows, step numbers, progress or checklist.

**Given** a collapsed section
**When** rendered
**Then** its heading states which of Not established, Changed and Affected it contains, and following a link to an item inside it expands the section and focuses the item.

### Story 6.3: Add material and see what was taken in

As a business operator,
I want to see each document I added, its version, and whether it could be read,
So that I know what my Agent is working from.

**Traces:** FR2, FR117; UX-DR18 · **Depends on:** 6.1, 5.2 · **Verification:** UI tests including a parse failure · **Status:** ready

**Acceptance Criteria:**

**Given** material added
**When** ingested
**Then** the list shows each source's name, version and provenance line, with a progress state while reading.

**Given** an unreadable file
**When** added
**Then** the degraded notice "Could not be read. Nothing from it has been used." appears.

### Story 6.4: The correction diff

As a business operator,
I want to see exactly what my correction changes, what else it touches and what stays the same,
So that I can say "yes, that is exactly the rule I meant".

**Traces:** FR101 (surface), FR21; UX-DR9 · **Depends on:** 6.2, 5.8 · **Verification:** UI tests; the diff reads correctly as linear text · **Status:** ready

**Acceptance Criteria:**

**Given** a proposed change
**When** shown
**Then** Before, After, Also affected and Unchanged appear as labelled prose in the Conversation pane, Before is never struck through, and affected items are marked in Understanding.

**Given** Accept or Push back
**When** chosen
**Then** accept produces a new version and push back returns to the conversation, and focus returns to the conversation input.

**Given** the diff
**When** read
**Then** it uses no version-control vocabulary.

### Story 6.5: Validation result, approval and version states

As a business operator,
I want the platform's check result shown at the moment I approve, in plain words, with no way around a blocking finding,
So that I approve knowing what the check found and what going live means.

**Traces:** FR11 (surface), FR22, FR28; UX-DR10, UX-DR11, UX-DR12; UX gaps 5, 7, 13 · **Depends on:** 6.2, 3.2, 3.3 · **Verification:** UI tests for blocking, non-blocking and could-not-run outcomes · **Status:** ready

**Acceptance Criteria:**

**Given** validation results
**When** shown
**Then** only actual findings appear, each Blocking or Not blocking, pointing at its Understanding area, and a blocking finding leaves approval unavailable with no override.

**Given** the check cannot run
**When** shown
**Then** the operator sees "The check could not run. Nothing has changed." and approval stays unavailable.

**Given** approval
**When** shown
**Then** it is one primary action with the two approval sentences, and no celebration.

**Given** approval or version creation fails
**When** shown
**Then** the previous version stays live and the operator is told plainly.

### Story 6.6: The Build surfaces meet the accessibility floor

As a business operator who uses a keyboard or a screen reader,
I want every Build flow to be fully operable and announced,
So that teaching my Agent does not depend on how I use a computer.

**Traces:** UX-DR1, UX-DR26 (Understanding read-only on a phone), UX-DR27, UX-DR28, UX-DR30; EXPERIENCE.md Flows 1 and 2 (Build parts) · **Depends on:** 6.1–6.5 · **Verification:** automated accessibility scan plus a recorded keyboard-only walkthrough of Flow 1 and Flow 2's Build steps · **Status:** ready

**Acceptance Criteria:**

**Given** Flow 1 and Flow 2's Build steps
**When** completed by keyboard alone
**Then** no step needs a pointer, focus is always visible, and there is no keyboard trap.

**Given** the listed status changes (Builder reply, new Understanding content, diff ready, validation pending and result, material finished or failed)
**When** they occur
**Then** each is announced politely without moving focus.

**Given** a 320 CSS px viewport and 200% text
**When** Understanding is opened on a phone
**Then** it is read-only, single-column and has no horizontal scroll.

**Given** the out-of-scope list (UX-DR30)
**When** the Build surfaces are inspected
**Then** none of those affordances exists.

**Given** the application's routes
**When** inventoried
**Then** the operator's destinations are exactly Understanding and Activity, the conversation opens from a place rather than being a destination, and there is no list of all interactions (UX-DR1).

## Epic 7: Review, correct and stop — the Run surfaces

The operator's Run surfaces: the Agent status line, Activity, the interaction viewer, "This was wrong" and Suspend, usable from a phone. Two stories are blocked on open product items and are listed so they cannot be forgotten.

### Story 7.1: The Agent status line and Suspend

As a business operator,
I want to see in words whether my Agent is live, and to stop it — or stop only its actions — in one press,
So that I can always stop it, even from my phone.

**Traces:** FR110 (surface); UX-DR14, UX-DR17, UX-DR23; UX gap 4 (persistent suspended state) · **Depends on:** 6.1, Story 1.6 · **Verification:** UI tests including a forced suspend failure · **Status:** ready

**Acceptance Criteria:**

**Given** the Activity pane
**When** shown
**Then** the status line above it states the Agent's status in the closed vocabulary, in words.

**Given** Suspend or Stop actions only
**When** pressed once
**Then** it applies with no confirmation, is announced, and the status line changes, and Let the Agent act again resumes as a secondary action never styled like Suspend.

**Given** a suspension that does not apply
**When** pressed
**Then** the operator sees "Suspend did not apply. The Agent is still live. Try again."

**Given** the suspended state
**When** the platform restarts
**Then** it persists, recorded under the technical answer to UX gap 4.

### Story 7.2: Activity — the divergence list

As a business operator,
I want one list of where my Agent's behaviour and my intent came apart, grouped by kind,
So that I see what needs me without a dashboard.

**Traces:** FR79, FR81, FR77, FR78, FR108, FR115 (sources); UX-DR15 · **Depends on:** 7.1, Epic 4 · **Verification:** UI tests over seeded divergences of all three classes and three sources · **Status:** ready

**Acceptance Criteria:**

**Given** divergences
**When** Activity renders
**Then** they are grouped under the three class framings, as kinds with their shapes and labels, newest first.

**Given** an item
**When** rendered
**Then** it shows only its class, the interaction label and the request on one line, with no counts, severity, retry eligibility, filters or charts.

**Given** no divergences
**When** rendered
**Then** "Nothing has come apart since {time}" appears, and only together with the status line.

### Story 7.3: The interaction viewer

As a business operator,
I want to open one interaction and see what the customer asked, what the Agent replied and what that reply was based on,
So that I can judge it against how my business works.

**Traces:** FR80, FR34 (general knowledge marked), FR52 (consequence class visible), FR71 (evidence stated); UX-DR16; UX gaps 12, 14 · **Depends on:** 7.2, 2.2 · **Verification:** UI tests; a test asserting that viewing an interaction makes no model call · **Status:** ready

**Acceptance Criteria:**

**Given** an Activity item
**When** opened
**Then** the viewer shows the customer's message verbatim, the reply verbatim (or the handed-to-human or declined statement), and what the reply was based on, quoted and linked to Understanding.

**Given** a reply from general knowledge, or a reported action
**When** shown
**Then** it is marked as not from the business's material, or stated with whether evidence exists.

**Given** any view
**When** rendered
**Then** every word is recorded material or a closed-vocabulary sentence, no model is called, and no pipeline or ordered trace appears.

**Given** an interaction with no subject
**When** labelled
**Then** the label is "Customer email · {received date and time}".

### Story 7.4: "This was wrong" opens the correction conversation

As a business operator,
I want to say an interaction was wrong and correct it right there,
So that a confidently wrong answer becomes a fixed rule.

**Traces:** FR82, FR102, FR108; EXPERIENCE.md Flow 3 · **Depends on:** 7.3, 6.4, 4.3 · **Verification:** UI end-to-end test of Flow 3 · **Status:** ready

**Acceptance Criteria:**

**Given** an interaction
**When** This was wrong is chosen
**Then** a correction is recorded against it, and the Builder conversation opens with the interaction as its origin.

**Given** that conversation
**When** the operator accepts a change
**Then** it follows the same diff, gate and approval as any correction.

### Story 7.5: Degraded and failure states, with error references

As a business operator,
I want every degraded or failed state to look different from success and to tell me whose problem it is,
So that nothing bad ever reads as good news.

**Traces:** FR46, FR52, NFR16; UX-DR19, UX-DR20 · **Depends on:** 7.3, 4.5 · **Verification:** one UI test per row of the degraded-states table · **Status:** ready

**Acceptance Criteria:**

**Given** each condition in EXPERIENCE.md's degraded-states table
**When** it occurs
**Then** it is shown in its closed-vocabulary words with the degraded notice, and never as a benign value.

**Given** a platform error
**When** shown
**Then** it carries a reference code the operator can quote and that resolves to the episode.

### Story 7.6: The Run surfaces work on a phone and by keyboard

As a business operator on the shop floor,
I want to check Activity, open an interaction and suspend the Agent from my phone,
So that I can act when something needs me.

**Traces:** UX-DR25 (Run), UX-DR26, UX-DR27; EXPERIENCE.md Flows 3 and 5 · **Depends on:** 7.1–7.5 · **Verification:** automated accessibility scan; phone-width and keyboard walkthroughs of Flows 3 and 5 · **Status:** ready

**Acceptance Criteria:**

**Given** a 320 CSS px viewport in either orientation
**When** the Run surfaces are used
**Then** the list and the interaction are full-screen with a back action, Suspend and Stop actions only sit in the sticky top bar, and nothing scrolls horizontally.

**Given** keyboard-only use
**When** Flows 3 and 5 are completed
**Then** they need no pointer, and closing the viewer returns focus to its Activity item.

### Story 7.7: Roll back from the operator's surface

As a business operator,
I want to return to my previous version from the product,
So that undoing a bad change does not need a developer.

**Traces:** FR26 (surface); UX gap 16 · **Depends on:** 3.4, 6.5 · **decision gate D9 (whether, and where, a rollback action appears)** · **Verification:** decided with D9 · **Status:** blocked (D9)

**Acceptance Criteria:**

**Given** the user's decision on D9
**When** this story is refined
**Then** its acceptance criteria are written from that decision and EXPERIENCE.md is amended by the UX workflow, not by this story.

### Story 7.8: Adjudicate sampled refusals

As a business operator, or someone I name,
I want to judge the refusals set aside for review,
So that wrong refusals reach the backlog.

**Traces:** FR115 (judging act); UX gap 15 · **Depends on:** 4.4, 7.3 · **decision gate D8 (who adjudicates, and on which surface)** · **Verification:** decided with D8 · **Status:** blocked (D8)

**Acceptance Criteria:**

**Given** the user's decision on D8
**When** this story is refined
**Then** its acceptance criteria are written from that decision, and the adjudication record of Story 4.4 is the only data it writes.

## Epic 8: Go live on email

Customers reach the Agent by email; escalations arrive at the business's address; connecting the mailbox is the go-live act. The provider and credentials are a user dependency (D10).

### Story 8.1: Capture real email traffic as fixtures

As a platform developer,
I want the adapter built against real messages,
So that email's real behaviour, not vendor documentation, defines what the adapter handles.

**Traces:** FR98, FR114 (preparation) · **Depends on:** Epic 1 · **decision gate D10 (a test mailbox and its credentials)** · **Verification:** a fixture set in `studio/tests/fixtures/email/`, anonymized, with a test per discovered behaviour · **Status:** blocked (D10)

**Acceptance Criteria:**

**Given** a test mailbox
**When** messages are captured
**Then** the fixtures include a reply with quoted history, a message with additional recipients, an attachment, a bounce and an automatic reply, anonymized.

**Given** each behaviour discovered in the captures
**When** recorded
**Then** a test pins it.

### Story 8.2: Customer email becomes episodes, replies go back as email

As a requester,
I want to email the business and get a reply that reads like a message from the business,
So that I can deal with it in my normal inbox.

**Traces:** FR83, FR84, FR85, FR86, FR87, FR112 (first email), FR113, AD-16, AD-22 · **Depends on:** 8.1 · **Verification:** adapter tests over the fixtures; a test that the Core has no channel field or import · **Status:** ready

**Acceptance Criteria:**

**Given** an inbound email
**When** received
**Then** its thread maps to one episode by an explicit join key, and a resend or corrected resend is processed once.

**Given** the Agent's reply
**When** sent
**Then** the adapter shapes it as written correspondence, and the first reply carries the business's disclosure.

**Given** the Core and the Agent
**When** inspected
**Then** neither carries any channel field, and the harness and email adapters implement one port.

### Story 8.3: Handle what makes email email

As a requester,
I want a reply-all, an attachment, a bounce or an auto-reply handled sensibly,
So that the Agent never re-reads old mail as new, writes to the wrong person, or loops forever.

**Traces:** FR114 (threading and quoted history, additional recipients, attachments, bounces and delivery failures, automated-sender loops), FR98 · **Depends on:** 8.2 · **Verification:** one pinned test per hazard over captured fixtures · **Status:** ready

**Acceptance Criteria:**

**Given** a reply carrying quoted history
**When** received
**Then** only the new text becomes input.

**Given** additional recipients
**When** replying
**Then** episode content reaches only those party to the episode.

**Given** an attachment
**When** received
**Then** it is accepted as material or refused, never silently ignored.

**Given** a bounce
**When** received
**Then** the reply is recorded as not delivered and is never treated as a served goal.

**Given** an automatic reply
**When** received
**Then** no unbounded exchange follows.

### Story 8.4: Credentials never leave the adapter

As a business operator,
I want my mailbox credentials kept out of everything the Agent and the records see,
So that a transcript or an export can never leak them.

**Traces:** FR57, NFR11, AD-24 · **Depends on:** 8.2 · **Verification:** a sentinel-credential test that searches the store, evidence, prompts, model-call records and exports · **Status:** ready

**Acceptance Criteria:**

**Given** a sentinel value as the mailbox credential
**When** a full scenario runs
**Then** the value appears nowhere in Core state, evidence, Agent context, prompts or any export.

**Given** credentials
**When** resolved
**Then** they are resolved per tenant at the adapter boundary only.

### Story 8.5: Escalations arrive as a designed email

As a business operator,
I want an escalation to arrive in my inbox with everything I need to act,
So that I can handle it without logging in.

**Traces:** FR103, FR74, FR69; UX-DR29; UX gap 19 and EXPERIENCE open question 4 · **Depends on:** 8.2 · **decision gates D10 (where the escalation address is declared), D12 (what happens when the escalation email is undeliverable)** · **Verification:** rendering tests (HTML and plain text); delivery tests · **Status:** blocked (D10, D12) for the last criterion only

**Acceptance Criteria:**

**Given** an escalation
**When** delivered
**Then** the email states the request, why the Agent could not resolve it, the relevant context and evidence, what the human needs to do, and a link to the interaction, in the product voice.

**Given** the email
**When** read without images or CSS
**Then** it is fully understandable, and no meaning is carried by colour.

**Given** the link
**When** followed while signed out
**Then** the operator signs in and lands on that interaction.

**Given** an undeliverable escalation email
**When** it bounces
**Then** it is never treated as delivered, and what the operator sees follows the decision on D12.

### Story 8.6: Connecting the mailbox is the go-live act

As a business operator,
I want my Agent to become reachable only when I connect the mailbox, after approval,
So that nothing reaches a customer before I decide.

**Traces:** FR61, NFR17 (health asserts what a real request needs); UX-DR13, UX-DR14 (mailbox statuses); UX gaps 3, 18 · **Depends on:** 8.2, 6.5, 7.1 · **decision gate D10 (provider and authorisation model)** · **Verification:** UI and adapter tests; a health-check test with a deliberately broken configuration · **Status:** blocked (D10)

**Acceptance Criteria:**

**Given** no approved live version
**When** connecting is attempted
**Then** it is unavailable, with the reason stated.

**Given** an approved live version
**When** the mailbox is connected
**Then** the Agent becomes reachable and the status line reads "Live, mailbox connected"; before that, no customer can reach it.

**Given** the mailbox disconnects after go-live
**When** detected
**Then** the status line reads "The mailbox is no longer connected. Customers cannot reach the Agent."

**Given** a configuration whose first real request would fail
**When** the health check runs
**Then** it does not report healthy.

### Story 8.7: A material divergence can ride the escalation email

As a business operator,
I want a divergence that genuinely needs me to reach my inbox by the same email path as escalations,
So that I do not miss it between visits to Activity.

**Traces:** UX Amendment 1 (`m-ux` 58, explicit PRD amendment against §13.2); EXPERIENCE open question 3 · **Depends on:** 8.5, 4.2 · **decision gate D11 (what makes a divergence material)** · **Verification:** decided with D11 · **Status:** blocked (D11)

**Acceptance Criteria:**

**Given** the user's decision on D11
**When** this story is refined
**Then** its acceptance criteria are written from it, and no notification system, digest, inbox or severity model is introduced.

## Epic 9: Prove it generalises

All four exemplars built through the Builder; the generalisation measurements recorded; at least one real business end to end. V1 is not complete without this epic (PRD §7.1 S11).

### Story 9.1: Fix the engine-leak classification rules before the fourth business

As a platform developer,
I want the rules for classifying an engine leak written before the evidence arrives,
So that the generalisation measurement is not graded after the fact.

**Traces:** FR89, FR116, FR59; PRD review F4.3 (self-graded, learning-curve confounded) · **Depends on:** Story 1.8 (leak log exists) · **Verification:** the rules document and the reclassified log in `PROOF-GATE.md` (or its successor) · **Status:** ready

**Acceptance Criteria:**

**Given** the FR116 taxonomy
**When** the rules are written
**Then** each class has a test a second person could apply, and every log entry records its evidence and who judged it.

**Given** the existing entries
**When** the rules exist
**Then** they are reclassified under them.

### Story 9.2: The first exemplar business through the Builder

As a platform developer,
I want one of the four exemplars built through the Builder by the path an operator would take,
So that setup effort starts being measured from the first business.

**Traces:** FR88, FR91, FR12 · **Depends on:** Epics 5–6, 9.1 · **Verification:** the session record and the passing gate · **Status:** ready (build order is a recorded technical choice)

**Acceptance Criteria:**

**Given** the exemplar's material and a person acting as the operator
**When** built through the Builder
**Then** the result passes the gate, and burden, yield and any engine leak are recorded.

### Story 9.3: The second exemplar business through the Builder

As a platform developer,
I want the second exemplar built the same way,
So that setup effort can be compared in build order.

**Traces:** FR88, FR89, FR91 · **Depends on:** 9.2 · **Verification:** as 9.2 · **Status:** ready

**Acceptance Criteria:**

**Given** the second exemplar
**When** built through the Builder
**Then** it passes the gate, and its burden, yield and leaks are recorded and compared with the first.

### Story 9.4: The third exemplar business through the Builder

As a platform developer,
I want the third exemplar built the same way,
So that the trend has a third point.

**Traces:** FR88, FR89, FR91 · **Depends on:** 9.3 · **Verification:** as 9.2 · **Status:** ready

**Acceptance Criteria:**

**Given** the third exemplar
**When** built through the Builder
**Then** it passes the gate, and its burden, yield and leaks are recorded and compared.

### Story 9.5: The fourth exemplar business through the Builder

As a platform developer,
I want the fourth exemplar built the same way, including the gym's identity verification as an extension point,
So that the generalisation claim is tested at four.

**Traces:** FR88, FR89, FR91, FR109 (identity verification as an extension point), FR116 · **Depends on:** 9.4 · **Verification:** as 9.2; the gym's pregnancy case escalates with two recorded specification gaps (`spec-stress-test.md` §2) · **Status:** ready

**Acceptance Criteria:**

**Given** the fourth exemplar
**When** built through the Builder
**Then** it passes the gate, and its burden, yield and leaks are recorded and compared.

**Given** the gym's deliberate failure case ("I'm pregnant, so I need six months")
**When** run
**Then** the Agent escalates rather than refuses, and two specification defects are recorded.

### Story 9.6: The generalisation report

As a platform developer,
I want resolution strain, setup effort, the validity floor and the cost slope reported across the four,
So that the thesis is judged by its own falsifiers.

**Traces:** FR89, FR90, FR91, FR93, NFR15, PRD §10.3; O4 (resolution-kind candidates) and O5 (faithfulness threshold) informed, not decided · **Depends on:** 9.2–9.5, 4.1, 4.6 · **Verification:** the report, computed from records and session logs · **Status:** ready

**Acceptance Criteria:**

**Given** the four builds
**When** the report is written
**Then** it states whether leaks fell toward zero, whether any business could not be expressed, and whether effort fell, against PRD §10.3's failure conditions.

**Given** the episodes run
**When** reported
**Then** the validity floor and the cost slope in episodes per business are stated, measured at the size reached.

**Given** O4 and O5
**When** the report is written
**Then** it presents evidence and options, and leaves both decisions to the user.

### Story 9.7: One real business, end to end

As a real business operator,
I want my own Agent answering my real customers' email,
So that usefulness is tested on requests nobody on the team wrote.

**Traces:** FR92, PRD A2 · **Depends on:** Epics 1–8, 9.1 · **decision gate D13 (a real business, its operator, material and inbound mail)** · **Verification:** the usefulness report with Agent failures separated from business-rule blocks · **Status:** blocked (D13)

**Acceptance Criteria:**

**Given** a real operator, their material and their inbound mail
**When** the Agent runs live with their approval
**Then** the usefulness report separates Agent failures from blocks caused by their own rules or capacity.

### Story 9.8: Two or three operator conversations

As the product owner,
I want to talk with two or three real small-business operators about how their rules really work,
So that the premise that operators can articulate their tacit rules is tested before the Builder's design hardens.

**Traces:** FR94, PRD A4, Brief research questions · **Depends on:** — (human track; can start now) · **decision gate D13 (the user's time and contacts)** · **Verification:** written notes per conversation, feeding Stories 5.3 and 5.7 · **Status:** blocked (D13; owner: the user)

**Acceptance Criteria:**

**Given** each conversation
**When** held
**Then** notes record how the operator describes their rules, where printed and practised policy differ, and their answer to "how would you know the Agent did a bad job?"

## Story Traceability

Generated from each story's **Traces** line (`docs/next-phase-proposals/tools/trace_epics.py`; it also reports any requirement ID left without a story), so it cannot drift from the stories. **State** is derived from story statuses: *done* = every story delivering it is done and verified; *partly done* = some delivering story is done; *open* = none done yet; *blocked* = every delivering story waits on a decision gate. FR96 (non-vacuous checks) is also a standing criterion of every story, so *done* there means the mechanism exists, not that the obligation ends. Acceptance criteria live only in the stories above; verification evidence for done stories is in `docs/next-phase-proposals/IMPLEMENTATION-STATE.md` §0.

| ID | Stories | State |
| --- | --- | --- |
| FR1 | 5.1, 6.1 | open |
| FR2 | 5.2, 6.3 | open |
| FR3 | 5.3, 5.7, 6.1 | open |
| FR4 | 5.3, 5.7 | open |
| FR5 | 5.4, 5.7 | open |
| FR6 | 5.4 | open |
| FR7 | 5.3, 5.7 | open |
| FR8 | — declined for V1 (`m-ux` 22 override; register B-06) | n/a |
| FR9 | 5.1 | open |
| FR10 | 5.1 | open |
| FR11 | 3.2, 6.5 | open |
| FR12 | 5.6, 9.2 | open |
| FR13 | 1.1 | done |
| FR14 | 1.1, 6.2 | partly done |
| FR15 | 1.1, 1.7 | done |
| FR16 | 1.1, 1.2, 2.6 | partly done |
| FR17 | 1.1, 1.7, 2.6 | partly done |
| FR18 | 1.1, 5.5, 6.2 | partly done |
| FR19 | 1.1, 5.1 | partly done |
| FR20 | 4.1 | open |
| FR21 | 1.1 (part), 3.1, 5.8, 6.4 | partly done |
| FR22 | 1.2 (part), 3.2, 3.3, 6.5 | partly done |
| FR23 | 1.2 | done |
| FR24 | 1.2, 5.5 | partly done |
| FR25 | 1.2 (part), 3.2 | partly done |
| FR26 | 3.4, 7.7 | open |
| FR27 | 1.4, 3.1 | partly done |
| FR28 | 3.2, 3.4, 5.8, 6.5 | open |
| FR29 | 3.2 | open |
| FR30 | 1.1 (part), 2.1, 5.2 | partly done |
| FR31 | 2.4, 5.4 | open |
| FR32 | 1.7 (part), 2.3 | partly done |
| FR33 | 1.7 (part), 2.1, 2.3 | partly done |
| FR34 | 1.7, 2.6, 7.3 | partly done |
| FR35 | 2.5 | blocked |
| FR36 | 1.5 | done |
| FR37 | 2.2 | open |
| FR38 | 1.3, 2.3 | partly done |
| FR39 | 1.3 | done |
| FR40 | 1.3 | done |
| FR41 | 1.3, 1.8 | done |
| FR42 | 1.7 (part), 4.6 | partly done |
| FR43 | 1.3 | done |
| FR44 | 1.6 | done |
| FR45 | 1.6 | done |
| FR46 | 1.5, 7.5 | partly done |
| FR47 | 1.6 | done |
| FR48 | 1.6, 4.2, 5.4 | partly done |
| FR49 | 1.3 | done |
| FR50 | 1.7, 2.6 | partly done |
| FR51 | 1.1, 1.2 | done |
| FR52 | 1.1 (part), 1.2 (part), 7.3, 7.5 | partly done |
| FR53 | 1.5 | done |
| FR54 | 1.1, 1.5 | done |
| FR55 | 1.5 | done |
| FR56 | 1.3 | done |
| FR57 | 8.4 | open |
| FR58 | 1.1 | done |
| FR59 | 9.1 | open |
| FR60 | 1.4 (part), 1.10 | partly done |
| FR61 | 1.4, 1.10, 8.6 | partly done |
| FR62 | 1.4, 2.1 | partly done |
| FR63 | 1.4, 1.10 | partly done |
| FR64 | 1.4 (part), 1.11 | partly done |
| FR65 | 1.4 | done |
| FR66 | 1.4 | done |
| FR67 | 1.4, 4.1 | partly done |
| FR68 | 1.7 | done |
| FR69 | 1.6, 2.6, 8.5 | partly done |
| FR70 | 1.5 | done |
| FR71 | 1.7, 1.9, 7.3 | partly done |
| FR72 | 1.5, 4.1 | partly done |
| FR73 | 1.8 (part), 2.2 (part), 4.1 | partly done |
| FR74 | 1.6, 8.5 | partly done |
| FR75 | 1.4 | done |
| FR76 | 4.1 | open |
| FR77 | 1.3, 4.2, 7.2 | partly done |
| FR78 | 4.2, 7.2 | open |
| FR79 | 7.2 | open |
| FR80 | 7.3 | open |
| FR81 | 3.3, 4.5, 7.2 | open |
| FR82 | 5.8, 7.4 | open |
| FR83 | 1.8, 8.2 | partly done |
| FR84 | 8.2 | open |
| FR85 | 1.8 (part), 8.2 | partly done |
| FR86 | 1.4, 8.2 | partly done |
| FR87 | 1.4, 8.2 | partly done |
| FR88 | 9.2, 9.3, 9.4, 9.5 | open |
| FR89 | 1.8 (part), 2.6, 9.1, 9.3, 9.4, 9.5, 9.6 | partly done |
| FR90 | 9.6 | open |
| FR91 | 5.6, 9.2, 9.3, 9.4, 9.5, 9.6 | open |
| FR92 | 9.7 | blocked |
| FR93 | 9.6 | open |
| FR94 | 9.8 | blocked |
| FR95 | 1.2, 3.2 | partly done |
| FR96 | 1.2 (part), 1.3 | done |
| FR97 | 1.5 | done |
| FR98 | 8.1, 8.3 | open |
| FR99 | 5.6 | open |
| FR100 | 5.7 | open |
| FR101 | 5.8, 6.4 | open |
| FR102 | 4.3, 7.4 | open |
| FR103 | 1.2 (part), 1.6 (part), 8.5 | partly done |
| FR104 | 5.5 | open |
| FR105 | 1.7 | done |
| FR106 | 1.7 | done |
| FR107 | 1.6 | done |
| FR108 | 4.3, 7.2, 7.4 | open |
| FR109 | 1.2 (part), 1.5, 9.5 | partly done |
| FR110 | 1.6 (part), 7.1 | partly done |
| FR111 | 1.2 (part), 1.6 | done |
| FR112 | 1.2 (part), 1.6, 8.2 | partly done |
| FR113 | 8.2 | open |
| FR114 | 8.1, 8.3 | open |
| FR115 | 4.4, 7.2, 7.8 | open |
| FR116 | 1.8 (part), 2.6, 9.1, 9.5 | partly done |
| FR117 | 5.2, 5.4, 5.9, 6.3 | open |
| NFR1 | 1.4 (part), 1.11 | partly done |
| NFR2 | 1.5 | done |
| NFR3 | 1.4, 6.1 | partly done |
| NFR4 | 1.3 | done |
| NFR5 | 1.7 (part), 2.3 | partly done |
| NFR6 | 4.6 | open |
| NFR7 | 1.1 (part), 2.1, 2.2, 3.1 | partly done |
| NFR8 | 3.1, 3.4 | open |
| NFR9 | 1.4 | done |
| NFR10 | 1.4 | done |
| NFR11 | 8.4 | open |
| NFR12 | 1.8, 5.1 | partly done |
| NFR13 | 1.8 (part), 1.9, 2.3, 4.1 | partly done |
| NFR14 | 1.8 (part), 1.9, 2.3, 4.1 | partly done |
| NFR15 | 9.6 | open |
| NFR16 | 1.8 (part), 4.5, 7.5 | partly done |
| NFR17 | 1.8 (part), 8.6 | partly done |
| NFR18 | 1.4 | done |
| UX-DR1 | 6.6 | open |
| UX-DR2 | 6.1 | open |
| UX-DR3 | 6.1 | open |
| UX-DR4 | 6.1 | open |
| UX-DR5 | 6.2 | open |
| UX-DR6 | 6.2 | open |
| UX-DR7 | 6.2 | open |
| UX-DR8 | 6.2 | open |
| UX-DR9 | 5.8, 6.4 | open |
| UX-DR10 | 3.3, 6.5 | open |
| UX-DR11 | 6.5 | open |
| UX-DR12 | 3.3, 6.5 | open |
| UX-DR13 | 8.6 | blocked |
| UX-DR14 | 7.1, 8.6 | open |
| UX-DR15 | 7.2 | open |
| UX-DR16 | 7.3 | open |
| UX-DR17 | 7.1 | open |
| UX-DR18 | 6.3 | open |
| UX-DR19 | 7.5 | open |
| UX-DR20 | 4.5, 7.5 | open |
| UX-DR21 | 6.1 | open |
| UX-DR22 | 6.1 | open |
| UX-DR23 | 6.1, 7.1 | open |
| UX-DR24 | 6.1 | open |
| UX-DR25 | 6.1, 7.6 | open |
| UX-DR26 | 6.6, 7.6 | open |
| UX-DR27 | 6.6, 7.6 | open |
| UX-DR28 | 6.1, 6.6 | open |
| UX-DR29 | 8.5 | blocked |
| UX-DR30 | 6.6 | open |
