# Spine Extract for PRD — Agent Studio

Source (authoritative, FINAL): `_bmad-output/planning-artifacts/architecture/architecture-AgentStudio-2026-10-07/ARCHITECTURE-SPINE.md`
Extracted: 2026-10-08. Purpose: give the PRD author the product-bearing surface of the Spine without re-opening architecture.

Paradigm of record (quoted): **"Hexagonal agent harness."** — "A model-in-charge agent decides what to do next; a deterministic Core decides what the agent is permitted to do, executes it, and records what happened. Everything outside the Core is reached through ports and adapters."

Control model of record (quoted, AD-1): "The Core never selects the Agent's next step."

---

## A. PRODUCT-BEARING CONSTRAINTS

Each line: the constraint (from the named AD or table) → the product consequence a PRD author must respect.

### A1. What the Agent is allowed to decide

| # | Constraint (source) | Product consequence |
|---|---|---|
| A1.1 | The Core never selects the Agent's next step; no business state machine, transition graph, workflow language or precondition-derived orchestration (AD-1) | The PRD may NOT specify per-business flows, steps, stages or "the agent then does X". Requirements describe context, policy, capability and outcome — never sequence. |
| A1.2 | Delegated to the Agent: what the person is trying to accomplish, what information is still needed, when to retrieve, which capability to use, whether to act/continue/respond, **whether to escalate**, how to phrase anything, how to handle a situation nobody enumerated (Deterministic vs Delegated table) | Any PRD requirement that fixes phrasing, retrieval timing, capability choice or escalation triggers as deterministic logic contradicts the Spine. Business owners configure *escalation conditions*, not escalation execution. |
| A1.3 | "Escalation has exactly one owner: **the Agent escalates.**" The platform refuses and returns a typed result stating required authority or evidence is unavailable; "it never escalates on the Agent's behalf." | Product must surface *a refusal reason to the Agent*, and must not advertise "the platform escalates automatically". Human-handoff UX is framed as the Agent choosing to escalate under business-declared conditions. |
| A1.4 | Litmus test: "can a new business be onboarded without generating a business-specific execution graph or state machine, while the Agent still reasons about situations nobody enumerated?" | This is the product's acceptance criterion for onboarding. A PRD success metric should be expressible against it. |

### A2. Capability boundaries and the closed request taxonomy

| # | Constraint | Product consequence |
|---|---|---|
| A2.1 | The Agent emits one of a **closed** set of request kinds — `retrieve`, `read`, `effect`, `clarify`, `respond`, `escalate`, `suspend` — and "every kind is authorized and journaled, reads included" (AD-2) | The product's capability model is a grant over these seven kinds. A business cannot invent a request kind; "add a new kind of thing the agent can do" is a platform release, not onboarding. |
| A2.2 | "The Agent never contacts anything outside the Core" (AD-2); external systems only as *Core contract → adapter → extension* (AD-9) | No product feature may promise direct agent↔third-party connection. Every integration is an extension behind an adapter. |
| A2.3 | "Business configuration never changes Core semantics. Extensions add capability behind stable interfaces. A genuinely new semantic capability is a platform evolution, performed once in the Core." (AD-15) | Onboarding/self-serve scope is bounded: businesses grant and bound capabilities; they do not author new semantics. PRD must distinguish "configure" from "request a platform capability". |
| A2.4 | Capabilities are verb-first (`check_availability`); action contracts declare input schema, effects, authority required, confirmation requirement, success evidence and idempotency scope (Consistency Conventions) | A capability catalog entry in the product has six mandatory declared fields. A capability with no success-evidence definition is not shippable. |
| A2.5 | "An action whose contract cannot define [an idempotency key] is not eligible for automatic retry." (AD-10) | Product must show, per capability, whether it is auto-retryable — a visible attribute, not an internal detail. |

### A3. Authorization, approval and confirmation semantics

| # | Constraint | Product consequence |
|---|---|---|
| A3.1 | "An `effect` whose contract requires confirmation is not authorized until that confirmation is recorded." (AD-2) | Human/customer confirmation is a first-class, recorded product object — a gate the Core enforces, configurable per business ("confirmation requirements" are business-configurable). |
| A3.2 | "Any constraint that must hold is enforced by the Core. The specification may also describe it to the Agent, but no enforcement path may rely on the model respecting what it was told." (AD-3) | The product may never market a policy as guaranteed if it is only prompt text. Every advertised guarantee maps to a Core enforcement point. |
| A3.3 | Business-configurable: "Authority boundaries, confirmation requirements"; platform-owned: "Authorization enforcement and denial classification" (Platform-Owned vs Business-Configurable) | Authoring surface the PRD must provide: authority boundaries + confirmation requirements per capability. Enforcement is not exposed as configurable. |
| A3.4 | Generic guardrail set is platform-owned and always on: "do not invent business facts · do not act outside declared authority · do not perform undeclared actions · do not claim success without evidence · escalate when required authority or evidence is unavailable" | These five are product promises available to every business with zero configuration — a baseline trust story. Domain safety packs are optional extensions on top. |
| A3.5 | AD-4: "A capability the Agent can see but policy will always deny is a defect." | Product requirement: the authoring/validation surface must detect granted-but-always-denied capabilities before promotion. Prevents "promise made to a customer and then broken, which is worse than a refusal" (AD-4 Prevents). |

### A4. What the Core guarantees (evidence, provenance, truthfulness)

| # | Constraint | Product consequence |
|---|---|---|
| A4.1 | "Only the Core's execution record may attest that an effect occurred; the Agent cannot author evidence." Evidence entries are "typed records against a platform-owned schema, never opaque blobs." A resolution asserting an effect without a Core execution record is invalid. (AD-6) | The product can honestly claim "the agent cannot claim it did something it didn't". Evidence is queryable/assertable — enables reporting features without transcript mining. |
| A4.2 | Every authoritative context item carries a **Core-issued provenance reference** bound to `(tenant, source, source version, locator)`, valid only for the issuing episode; "the Agent can neither mint, alter nor infer one"; a claim naming an unissued, altered or cross-tenant reference "is refused before it reaches the person." (AD-7) | Product guarantee: no fabricated business facts reach the customer. Citation/provenance is a user-visible feature, not internal plumbing. |
| A4.3 | "General domain knowledge may come from the model, must be marked as such in evidence, and is enabled or disabled per business." (AD-7) | A per-business toggle is a required product setting: may the agent use general world knowledge at all? Its use is auditable. |
| A4.4 | "Semantic faithfulness beyond provenance validity is **evaluated against a threshold, never guaranteed**." (AD-7) | The PRD must NOT promise correctness of meaning — only provenance validity plus a measured quality threshold. Marketing/acceptance language must match. |
| A4.5 | "The Agent decides *when* to retrieve; it never retrieves directly." Pinning is at source-version granularity. (AD-8) | Knowledge is versioned product content; every answer is reconstructible against the exact source version used. |

### A5. Observability, denial classification, evaluation

| # | Constraint | Product consequence |
|---|---|---|
| A5.1 | Every denial is recorded as exactly one of `spec_defect`, `business_refusal`, `platform_error`; "Only `spec_defect` enters the specification backlog. The divergence log is the specification's error signal and needs no human transcript review." (AD-5) | The product's improvement loop is a classified divergence list, not transcript review. This is a shippable surface: "here is what your specification got wrong". Strong PRD epic candidate. |
| A5.2 | Evidence vocabulary follows OpenTelemetry GenAI naming where it exists (Consistency Conventions; Stack) | Observability is standards-based; export/integration with existing telemetry is plausible as a product requirement. |
| A5.3 | Platform-owned: "Evaluation mechanism"; business-configurable: "Evaluation criteria" (Platform-Owned vs Business-Configurable) | Product must let a business state what good looks like; it must not let them build the evaluator. |
| A5.4 | Every Core mechanism declares a **closed outcome vocabulary** (AD-18) | Every failure/refusal a business owner sees comes from an enumerable list — enables a finite, documentable status taxonomy in the UI. |

### A6. Failure and degradation behavior a user or business owner would SEE

| # | Constraint | Product consequence |
|---|---|---|
| A6.1 | "The Core has exactly two exits": every outcome returns control to the Agent as a typed result, **except** a declared **safety halt**, which terminates the episode with a recorded outcome (AD-18) | There are exactly two visible failure shapes: the agent is told and keeps conversing, or the conversation is halted with a recorded reason. No silent degradation, no third path. |
| A6.2 | Guard verdicts are "enforced deterministically" with closed outcomes: typed constraint to the Agent, or declared safety halt. "A guard never composes a reply and never chooses the Agent's next step." (AD-21) | Safety features never produce canned replies. Business owners configure *which guard conditions apply*, not what the agent says when they fire. |
| A6.3 | "errors cross boundaries as typed results, never as defaults" (Consistency Conventions) | No fallback may read as success. A degraded result is always distinguishable — directly supports a product requirement that the owner can see degraded episodes. |
| A6.4 | External effects are at-least-once; Core issues tenant+episode-scoped idempotency key, adapter honours it (AD-10) | Product promise: retries do not double-book / double-charge, and a genuine effect is never silently suppressed as a cross-business duplicate. |
| A6.5 | "a result arriving after close is recorded as a late result and never mutates the resolution" (AD-13) | Late third-party callbacks are a visible, named condition in the product, not a correction of history. |
| A6.6 | Episode lifecycle is exactly `active` / `pending` awaiting a *named* external input / `closed` (AD-13) | The owner-facing episode status vocabulary is these three, plus the named awaited input. No other states may be invented in the UI. |
| A6.7 | "Clock, randomness, identifiers, environment and configuration are obtained through recorded steps or pinned at episode start"; each model decision, authorized execution and evidence write is a durable step (AD-12) | Product promise: an in-flight conversation survives a process failure. |

### A7. Tenancy, data boundaries, lifecycle

| # | Constraint | Product consequence |
|---|---|---|
| A7.1 | "Every episode, specification, knowledge source, provenance reference, idempotency key, evidence record and action request carries a tenant identity. **Any resolution that crosses tenants is rejected, not filtered.**" (AD-17) | Hard multi-tenancy is a product guarantee at the data level. Cross-tenant anything is an error, never a quietly empty result. |
| A7.2 | "Cross-episode memory is out of scope." (AD-13) | The PRD must NOT promise an agent that remembers a customer across conversations. Scope line to state explicitly. |
| A7.3 | "Adapter credentials are held at the adapter boundary and resolved per tenant. No credential value appears in Core state, episode evidence, agent context or any prompt." (AD-24) | Credential handling is a per-tenant adapter concern; product can promise secrets never enter transcripts or evidence exports. |
| A7.4 | Evidence "must be storable such that per-business data lifecycle requirements *can* be honoured — addressable and removable by tenant, by episode and by age, without reshaping the evidence schema" (AD-25) | A PRD-level requirement exists today (businesses can state data-lifecycle requirements; data is addressable/removable by tenant, episode, age) even though the executor is deferred. Episodes "may hold sensitive and health-adjacent material" — compliance posture is in product scope. |
| A7.5 | Business-configurable includes "data lifecycle requirements" | The authoring surface must capture retention/deletion requirements per business from V1, independent of the executor. |

### A8. Specification, promotion, versioning (the business-facing lifecycle)

| # | Constraint | Product consequence |
|---|---|---|
| A8.1 | "A specification version is immutable once promoted. Promotion requires its validation suite to pass — **a hard gate, not advice**. Rollback is selecting an earlier version." (AD-23) | Product features: versions, a blocking validation gate with visible results, and one-click rollback-by-selection. Non-negotiable UX: you cannot ship a failing specification. |
| A8.2 | "In-flight episodes keep the version pinned at their start" (AD-23, AD-11); episode captures specification version, compiler version and knowledge-source versions at creation | Observable behavior: publishing a change does not alter conversations already running. Must be stated in the product, not discovered. |
| A8.3 | "The agent's context, the tool surface offered to the model, and the policy the Core enforces are **projections compiled from one specification artifact by the Core**. The Builder produces the artifact and never compiles projections." (AD-4) | Single source of truth for the business: one artifact. No separate prompt editor, tool list and policy file as independent product objects. |
| A8.4 | "The specification artifact may not contain ordering or sequencing constructs; the compiler rejects them." (Consistency Conventions) | The authoring UX must make sequencing *unexpressible*, and the validation gate must reject it with a comprehensible message. Direct, visible product constraint. |
| A8.5 | Builder scope: "Conversation and sources → specification + knowledge artifacts → validation → promotion" (layer table) | The Builder's product boundary is exactly these four stages. Compiling, enforcing, executing are not Builder features. |

### A9. Channel independence and initiation

| # | Constraint | Product consequence |
|---|---|---|
| A9.1 | "The Agent and Core never learn which channel an episode is on." One channel ships first; its adapter is replaceable without touching behaviour. (AD-16) | Product can promise "same agent, any channel" and must write all requirements channel-neutrally. Adding a channel is adapter work, not re-specification. |
| A9.2 | "An episode is **initiated or resumed only by an inbound interaction or an external system event** … **The platform never independently initiates an outbound conversation or episode.**" (AD-22) | Hard product boundary: **no outbound/cold outreach, no proactive campaigns, ever** in this architecture. Within an initiated episode the Core may emit messages via the egress port. This forbids a whole category of feature requests. |
| A9.3 | Scope line in frontmatter: "a deployed inbound **text** agent" | V1 product is inbound text. Voice/outbound is out of the Spine's declared scope. |

### A10. Goals and obligations (business outcome expectations)

| # | Constraint | Product consequence |
|---|---|---|
| A10.1 | "The goals in play for an episode and the obligations outstanding for each are **typed Core state** — readable by the Agent, asserted by the Core at resolution. They are never only prompt text." (AD-19) | Product gets real, inspectable "what this conversation is for / what's still outstanding" state — a dashboard-grade surface, and an enforcement point at close. |
| A10.2 | "Holding them is not deciding with them: the Core never selects which goal is pursued or what to do about an unmet obligation." (AD-19) | The product must not offer "if obligation X unmet then do Y" rules. Business declares goals + attached obligations; the Agent decides. |
| A10.3 | Resolution envelope is fixed (AD-20): every resolution carries "which declared goal it concerns, whether that goal was served, under which authority, the evidence supporting it, and a business-defined payload" | Reporting/analytics requirements can be written today against these five fields, shared across all businesses, without the kind enumeration. |
| A10.4 | Resolution validation: "a claimed outcome unsupported by evidence is refused and returned to the Agent as a typed result" (Runtime Interaction) — but flagged *provisional* (Deterministic vs Delegated; Deferred) | A PRD requirement "outcomes reported are evidence-backed" is sound; its *inline* enforcement is provisional pending the proof gate. Word the requirement as the guarantee, not the mechanism. |

---

## B. EXPLICITLY DEFERRED TOPICS

Thirteen deferrals. Twelve are in the `## Deferred` table; one more is deferred inside AD-20 (resolution vocabulary, also tabled) and one inside AD-25 (retention, also tabled) — plus the Stack's explicit non-pinning of model/provider and the shortlisted-not-committed durability engine. Counted as distinct deferred topics: **13**.

| # | Deferred topic | Spine's quoted justification | Does a PRODUCT-level requirement plausibly depend on it? |
|---|---|---|---|
| B1 | **Resolution vocabulary** (the enumeration of kinds) | "The envelope is fixed by AD-20; the enumeration follows from running real episodes" | **Yes.** Reporting, "did the agent succeed", per-business outcome dashboards. Write requirements against the AD-20 envelope's five fields + business-defined payload; leave the kind list to emerge. |
| B2 | **Policy engine technology** (OPA, Cedar, purpose-built) | "AD-2 and AD-18 fix *where* and *how* authorization happens; the engine is selectable once real policy requirements exist" | **Yes, indirectly.** Authority-boundary authoring, confirmation requirements, denial classification are product requirements; the engine is not. PRD must name no engine. |
| B3 | **Durability engine selection** (DBOS shortlisted, "not committed") | "Semantics fixed. Fallback floor: Postgres with a unique constraint on `(tenant, episode, step, idempotency key)` and evidence written in the same transaction" | **Yes.** "An in-flight conversation survives a crash" and "no duplicate real-world effects" are product promises; the engine is free. Note the DBOS co-commit cost: "requires the evidence store and application store to be the **same** Postgres database". |
| B4 | **Model routing and tiering policy** | "An evaluation question. The architecture must express tiering; the policy is measured, not designed" | **Partly.** Cost/latency targets and per-capability quality expectations are product requirements. Which model serves which class is measured later. PRD must not pin a model. |
| B5 | **Retrieval architecture** (hybrid vs dense vs deterministic lookup) | "Grounding, provenance and version-pinning are required; hybrid versus dense versus deterministic lookup is not an invariant" | **Yes.** Knowledge ingestion, source versioning, provenance-bearing answers and source precedence are product requirements. Retrieval technique is not. |
| B6 | **V1 channel** | "Behaviour is channel-independent by AD-16 and AD-22" | **Yes.** The PRD must still pick a launch channel for scope/go-to-market, while writing every behavioral requirement channel-neutrally. Flag as a PRD decision the Spine deliberately left open. |
| B7 | **Long-term memory semantics** | "Out of scope by AD-13" | **Yes, as a negative requirement.** The PRD must state that cross-conversation memory/personalization is out of scope, so it isn't assumed in UX or metrics. |
| B8 | **Tenancy deployment model** (shared runtime, per-tenant workers, per-tenant deployment) | "AD-17 makes tenancy correct at the data level regardless of topology" | **Partly.** Isolation *guarantees* are product requirements (AD-17). Enterprise asks like "dedicated deployment" are a commercial/packaging question the PRD may note as open. |
| B9 | **Marketplace and extension distribution** | "The adapter contract is the invariant; distribution is later product work" | **Yes — explicitly called "later product work".** PRD should treat an integration catalog/marketplace as out of V1 scope but name the adapter contract as the forward-compatible seam. |
| B10 | **The concrete specification schema** (field level) | "Its invariants are fixed — one artifact compiled by the Core (AD-4), goals and obligations as typed state (AD-19), the resolution envelope (AD-20), immutable gated versions (AD-23), and no ordering constructs. The field-level schema belongs to the Specification and Builder epics" | **Yes, heavily.** The whole onboarding/authoring experience is product. Write requirements as *what a business must be able to express* (context, policies, capabilities, authorities, boundaries, goals, obligations, outcome expectations, data-lifecycle requirements) — never as field names. |
| B11 | **Context assembly** (permanent context vs on-demand fetch) | "a latency and quality tuning question, bounded by AD-7 (all authoritative context carries provenance) and AD-3. Measured, not designed up front" | **Partly.** Response-latency targets and grounding guarantees are product requirements; the assembly strategy is not. |
| B12 | **Retention policy, deletion executor, data-lifecycle implementation** | "AD-25 fixes that the evidence store must not foreclose per-business retention and deletion. The concrete policy, the executor and their implementation belong to the infrastructure and data-handling epic — deferred deliberately, not dropped" | **Yes.** The *capture* of per-business data-lifecycle requirements and addressability by tenant/episode/age are product-level now; the executor and a deletion SLA are deferred. |
| B13 | **Inline resolution validation as a shipped mechanism** | "Assertion-based evaluation is standard offline; enforcing it inline at episode close is **our own extension**, provisional everywhere it appears, and to be validated by the proof gate before being relied upon" | **Yes, with care.** "Reported outcomes are evidence-backed" is a legitimate requirement; stating that it is enforced synchronously at close is not yet safe. Phrase as guarantee, not timing. |

Also deliberately unpinned (not in the Deferred table but stated as open): **model and provider** — "Model and provider are deliberately unpinned — see AD-14", and AD-14: "Changing the model, provider or agent framework must not alter the business agent architecture."

---

## C. VOCABULARY OF RECORD

Terms the PRD must use. Definitions reproduced verbatim from the Spine where it defines them (layer table "Owns" column, ADs, or conventions).

| Term | Verbatim definition / defining text |
|---|---|
| **Agent** (`agent/`) | Owns: "Understanding, reasoning, deciding the next step, adapting to unenumerated situations". Also: "A model-in-charge agent decides what to do next". |
| **Core** (`core/`) | Owns: "Runtime, state, memory, capability exposure, validation, authorization, guardrails, execution, evidence, evaluation hooks, persistence". Also: "a deterministic Core decides what the agent is permitted to do, executes it, and records what happened". Diagram label: "Core / Harness — validate · authorize · execute · observe · persist". |
| **Harness** | Used as a synonym for the Core in the runtime diagram ("Core / Harness"); paradigm is "hexagonal agent harness … a model-driven tool-use loop inside a harness, with authorization at a policy enforcement point". |
| **Specification** / **Business Specification** (`spec/`) | Owns: "The business's declared context, policies, authorities, capability grants and outcome expectations". Diagram label: "Business Specification — context · policies · authorities · grants". Note: "The term 'AgentSpec' is avoided — it collides with two unrelated projects." |
| **Knowledge** / **Business Knowledge** (`knowledge/`) | Owns: "Version-pinned authoritative business material and retrieval over it". Diagram label: "Business Knowledge — version-pinned sources". |
| **Extensions** (`extensions/`) | Owns: "Tools, APIs, external systems, external knowledge — behind adapters". |
| **Builder** (`builder/`) | Owns: "Conversation and sources → specification + knowledge artifacts → validation → promotion". |
| **Channel adapter** | "A channel adapter provides both ingress and egress (AD-22)." Diagram: "Channel adapter — ingress + egress". |
| **Episode** | "One episode has one identity, one tenant, one lifecycle (`active` / `pending` awaiting a named external input / `closed`), one evidence record, and one join key where it touches an external system of record." Naming convention: "`episode` is the only word for a unit of interaction". |
| **Request kind** (closed taxonomy) | "It emits one of a closed set of request kinds — `retrieve`, `read`, `effect`, `clarify`, `respond`, `escalate`, `suspend` — and **every kind is authorized and journaled, reads included**." |
| **Effect** | A request kind producing an external change: "An `effect` whose contract requires confirmation is not authorized until that confirmation is recorded." "External effects are at-least-once." |
| **Capability** | Naming: "Capabilities are verb-first (`check_availability`)". Contract content: "action contracts declare input schema, effects, authority required, confirmation requirement, success evidence and idempotency scope". Business-configurable: "Which capabilities are granted". |
| **Projection** | "The agent's context, the tool surface offered to the model, and the policy the Core enforces are **projections compiled from one specification artifact by the Core**." |
| **Compiler / compiler version** | The Core compiles projections; "The compiler version is pinned into the episode alongside the specification version." "The compiler rejects [ordering or sequencing constructs]." |
| **Policy** | What the Core enforces, as one of the compiled projections (AD-4); platform-owned: "Authorization enforcement and denial classification"; business-configurable: "Authority boundaries, confirmation requirements", "The rules and predicates themselves". |
| **Denial classification** | "Every denial is recorded as exactly one of `spec_defect` (the projections led the Agent to believe it was permitted), `business_refusal` (policy correctly denied), or `platform_error`." |
| **`spec_defect`** | "the projections led the Agent to believe it was permitted" — "Only `spec_defect` enters the specification backlog." |
| **`business_refusal`** | "policy correctly denied" |
| **`platform_error`** | Third denial class (AD-5). |
| **Divergence log** | "The divergence log is the specification's error signal and needs no human transcript review." |
| **Evidence** | "Only the Core's execution record may attest that an effect occurred; the Agent cannot author evidence. Evidence entries are **typed records against a platform-owned schema**, never opaque blobs." |
| **Provenance reference** | "a **Core-issued provenance reference**, bound to `(tenant, source, source version, locator)` and valid only for the issuing episode". "the Agent can neither mint, alter nor infer one". |
| **Authoritative source** | "Authoritative sources include recorded retrieval results, the version-pinned Business Specification projection, and any other source the specification declares authoritative." |
| **General domain knowledge** | "General domain knowledge may come from the model, must be marked as such in evidence, and is enabled or disabled per business." |
| **Resolution** | "Every resolution carries: which declared goal it concerns, whether that goal was served, under which authority, the evidence supporting it, and a business-defined payload. The **enumeration** of resolution kinds is deferred; the **envelope** is not." Also: "A resolution asserting an effect without a corresponding Core execution record is invalid." |
| **Goal** | "The goals in play for an episode … are **typed Core state** — readable by the Agent, asserted by the Core at resolution." Business-configurable: "Which goals exist and what obligations attach". |
| **Obligation** | "the obligations outstanding for each are **typed Core state**"; "the Core never selects which goal is pursued or what to do about an unmet obligation." |
| **Guard** | "Guard conditions may be evaluated by a model … The **verdict is enforced deterministically** and its outcomes are closed: return a typed constraint to the Agent, or trigger a declared safety halt. A guard never composes a reply and never chooses the Agent's next step." |
| **Safety halt** | "a declared **safety halt**, which terminates the episode with a recorded outcome" — one of the Core's exactly two exits. |
| **Typed result** | "Every outcome returns control to the Agent as a typed result"; "errors cross boundaries as typed results, never as defaults". |
| **Escalate / escalation** | A request kind; "Escalation has exactly one owner: **the Agent escalates.**" Business-configurable: "Escalation conditions". |
| **Suspend / `pending`** | Request kind `suspend`; episode lifecycle state "`pending` awaiting a named external input". |
| **Late result** | "a result arriving after close is recorded as a late result and never mutates the resolution". |
| **Idempotency key** | "**The Core issues the idempotency key, scoped by tenant and episode**; the adapter honours it." |
| **Join key** | "one join key where it touches an external system of record"; "external correlation is an explicit join key". |
| **Tenant / tenant identity** | "Every episode, specification, knowledge source, provenance reference, idempotency key, evidence record and action request carries a tenant identity. **Any resolution that crosses tenants is rejected, not filtered.**" |
| **Step** | "Each model decision, authorized execution and evidence write is a durable step. **Step boundaries are a durability concern only — nothing may read the step sequence as a permitted order.**" |
| **Agent runtime boundary** | "Provider and framework abstractions live behind a runtime boundary defined by this platform. No framework type and no provider type crosses into Core, Specification or Extension code." |
| **Adapter** | "An external system is reached only as *Core contract → adapter → extension*." |
| **Promotion** | "A specification version is immutable once promoted. Promotion requires its validation suite to pass — **a hard gate, not advice**. Rollback is selecting an earlier version." |
| **Validation suite** | The gate promotion must pass (AD-23). |
| **Pinning** | "An episode captures its specification version, compiler version and knowledge-source versions at creation, and reads them from episode state thereafter, never live." Knowledge pinning is "at **source-version granularity**". |
| **Specification authoring vocabulary** | "Vocabulary borrowed from existing agent-manifest practice (autonomy level, boundaries, risk profile) rather than coined." |
| **Domain safety pack** | Business-configurable: "Domain safety packs, as optional extensions". |
| **Proof gate** | "Before the whole runtime is committed to this architecture, one realistic business interaction is implemented end to end…" |

Deprecated/forbidden vocabulary (the Spine bans these for business-level description): workflow, state machine, business transition graph, workflow language, primitive precedence table, execution graph, stage, node, "AgentSpec".

---

## EXTRA 1. Major components / surfaces (epic-informing)

From the layer table, the diagrams, and the Deferred table's epic references.

| Surface | Spine basis | Epic signal |
|---|---|---|
| **Agent runtime boundary** (`agent/` + AD-14) | Owns understanding/reasoning/deciding; provider & framework abstraction behind an owned boundary; "Model tiering across capability classes is expressible at this boundary" | Epic: agent loop + runtime boundary + tiering expressibility |
| **Core enforcement** (`core/`) | Validation, authorization, denial classification, guardrails, request taxonomy | Epic: request taxonomy + policy enforcement point |
| **Core execution & extensions** (AD-9, AD-10, AD-24) | Contract → adapter → extension; idempotency; per-tenant credentials | Epic: capability execution + integrations |
| **Evidence & observability** (AD-6, AD-5, OTel GenAI) | Typed evidence schema, divergence log, evaluation hooks | Epic: evidence, divergence log, evaluation |
| **Episode lifecycle & durability** (AD-11, AD-12, AD-13) | Single-writer episode state, durable steps, version pinning, serialization, late results | Epic: episode runtime & durability |
| **Specification subsystem** (`spec/`, AD-4, AD-19, AD-20, AD-23) | One artifact, Core-compiled projections, typed goals/obligations, resolution envelope, immutable gated versions | Epic: Specification (field schema explicitly assigned here by the Deferred table) |
| **Knowledge subsystem** (`knowledge/`, AD-7, AD-8) | Version-pinned sources, retrieval via Core, provenance issuance | Epic: knowledge ingestion + grounded retrieval |
| **Builder** (`builder/`, AD-23) | Conversation and sources → artifacts → validation → promotion | Epic: Builder (named jointly with Specification in the Deferred table) |
| **Channel adapters** (AD-16, AD-22) | Ingress + egress; one channel first; no initiation | Epic: channel adapter(s) |
| **Guard mechanism** (AD-21) | Model-based detection, deterministic binding verdict, two closed outcomes | Epic: guards & safety |
| **Tenancy & data boundaries** (AD-17, AD-24, AD-25) | Tenant as first-class key; credentials at adapter; lifecycle-capable evidence store | Epic: infrastructure and data-handling (explicitly named by AD-25 and the Deferred table) |
| **Evaluation** (AD-5, AD-20, Platform/Business table) | Platform owns the mechanism, business owns criteria | Epic: evaluation |
| **Proof gate** (closing section) | One end-to-end realistic business interaction, compared against the existing 15-node LangGraph system on nine named axes | A gate/milestone, not an epic — but PRD-visible as a V1 decision point |

Proof-gate comparison axes (verbatim): "architectural simplicity, amount of custom code, number of model calls, latency, control and observability, failure handling, extensibility to a second business, and ease of enforcing business boundaries."

Migration posture (verbatim): "The existing 15-node LangGraph system is the reference implementation and migration source, not the foundation. It is neither preserved because it exists nor replaced to avoid it."

---

## EXTRA 2. NFR-shaped guarantees stated as architecture

These are architecture-stated, so the PRD should restate them as NFRs rather than invent new ones.

| NFR area | What the Spine fixes | Quantified? |
|---|---|---|
| **Durability** | Every model decision, authorized execution and evidence write is a durable step; clock/randomness/ids/env/config via recorded steps or pinned at start (AD-12). Fallback floor: "Postgres with a unique constraint on `(tenant, episode, step, idempotency key)` and evidence written in the same transaction" | No number — recoverability is binary ("episodes that cannot be recovered after a process failure" is what AD-12 prevents) |
| **Effect exactly-onceness** | "External effects are at-least-once" + Core-issued tenant/episode-scoped idempotency key (AD-10); non-keyable actions not auto-retryable | Qualitative |
| **Isolation / tenancy** | Tenant identity on every record; "Any resolution that crosses tenants is rejected, not filtered" (AD-17); per-tenant credential resolution (AD-24) | Qualitative, absolute |
| **Auditability** | Every request kind authorized AND journaled, reads included (AD-2); only Core authors evidence, typed schema (AD-6); denial classification (AD-5); OTel GenAI evidence vocabulary | Qualitative, complete-coverage |
| **Provenance integrity** | Core-issued references bound to `(tenant, source, source version, locator)`, episode-scoped, unforgeable by the Agent; invalid claims "refused before it reaches the person" (AD-7) | Qualitative, absolute |
| **Semantic faithfulness** | "evaluated against a threshold, never guaranteed" (AD-7) | Threshold — value not set; PRD must set it |
| **Latency** | Not quantified anywhere. Named as a concern in two deferrals: model routing/tiering ("latency … measured, not designed") and context assembly ("a latency and quality tuning question"). Latency is a proof-gate comparison axis. | **No number — the PRD must supply the target** |
| **Consistency / single writer** | "The Core is the sole writer of episode state"; concurrent inbound messages on one episode are serialized (AD-13) | Qualitative |
| **Reproducibility** | Specification, compiler and knowledge-source versions pinned at episode creation, read from episode state, "never live" (AD-11) | Qualitative, absolute |
| **Change safety** | Immutable promoted versions, hard validation gate, rollback by version selection (AD-23) | Qualitative, absolute |
| **Data lifecycle** | Evidence addressable and removable "by tenant, by episode and by age, without reshaping the evidence schema" (AD-25) | Capability fixed; policy/SLA deferred |
| **Portability** | "Changing the model, provider or agent framework must not alter the business agent architecture" (AD-14); no vendor name/branch/key in Core or Agent code (AD-9) | Qualitative, absolute |
| **Timestamps** | "timestamps UTC" (Consistency Conventions) | Fixed |

Stack seed (the Spine says "The code owns this once it exists"): Python 3.12+; Pydantic AI 2.54.0 as a *candidate* behind AD-14; DBOS *shortlisted, not committed*; MCP spec revision 2026-07-28 as capability transport; OpenTelemetry GenAI conventions (Development stability, "expect churn"); PostgreSQL 16+. The PRD should not restate these as product requirements.

---

## EXTRA 3. FLAGGED — where workflow / state-machine / execution-graph thinking lives

The Spine bans this model, but it discusses it, and several of its own mechanisms are *shaped* like orchestration. These are the temptation sites. The PRD must not convert any of them into a per-business flow.

| # | Location | The temptation | Why it is NOT a flow (Spine's own guard) |
|---|---|---|---|
| F1 | **AD-1's own prohibition list** — "no deterministic next-action selection, no primitive precedence table, no business transition graph, no business state machine, no workflow language, no precondition-derived orchestration" | Reading the list as a menu of things the platform *could* offer; or re-litigating "but a little precedence table would help" | AD-1 supplies the test to apply before adding any mechanism: "does this constrain the Agent, or decide its next step?" Use that sentence as the PRD's own filter. |
| F2 | **AD-12 durable steps** | "Step" reads as a workflow step; a step sequence invites being treated as a permitted order, and a PRD could describe "step 1 … step 2" | Verbatim: "**Step boundaries are a durability concern only — nothing may read the step sequence as a permitted order.**" AD-12 explicitly prevents "durability decomposition being mistaken for a control graph". |
| F3 | **AD-13 episode lifecycle `active`/`pending`/`closed`** | A three-state lifecycle is a state machine, and it is tempting to hang business sub-states off it ("qualified", "booked", "awaiting docs") | The lifecycle is *platform* state, listed under platform-owned "Episode lifecycle, durability, tenancy". Business outcome lives in goals/obligations (AD-19) and the resolution envelope (AD-20), not in lifecycle states. Adding business sub-states is building a state machine. |
| F4 | **The Runtime Interaction sequence diagram** | It is a sequence diagram with `alt permitted effect / else denied` — it looks exactly like an execution graph and is the single easiest thing to transcribe into PRD flows | It is one turn of a model-driven loop, not an ordering of business steps. The Spine appends the guard immediately after it: "Neither mechanism chooses the Agent's next step, and neither has any exit but those two." The `alt` branch is an *authorization* branch inside the Core, not an agent decision. |
| F5 | **AD-21 guards running "before the Agent turn"** | A pre-turn gate with verdicts reads like a router; tempting to let a guard "handle" certain inputs or compose a response | "A guard never composes a reply and never chooses the Agent's next step." Outcomes are closed: typed constraint back to the Agent, or declared safety halt. A PRD requirement like "when X is detected, reply with Y" violates this. |
| F6 | **AD-19 goals + outstanding obligations** | Obligations outstanding → gating conditions → "if obligation unmet, ask for it" → a BANT-style qualification flow | "Holding them is not deciding with them: the Core never selects which goal is pursued or what to do about an unmet obligation." The business declares *which goals exist and what obligations attach* — not what to do when one is unmet. |
| F7 | **AD-20 / resolution validation at close** | A validation-at-close checkpoint reads like a terminal workflow state with exit criteria | Validation only refuses a claimed resolution and "returned to the Agent as a typed result" (AD-18). It does not pick a recovery path. Also flagged provisional (Deferred B13). |
| F8 | **AD-2's closed request taxonomy** | Seven named kinds invites a precedence/ordering table among them ("clarify before effect", "always retrieve first") | AD-1 bans a "primitive precedence table" by name. The taxonomy is a *set of authorized kinds*, never an order. |
| F9 | **Specification authoring surface** | The most dangerous site: a business owner given a form will try to describe a process, and an authoring UX can quietly become a flow builder | Verbatim: "**The specification artifact may not contain ordering or sequencing constructs; the compiler rejects them.**" The PRD must require the authoring surface to make sequencing unexpressible and the gate to reject it legibly. |
| F10 | **The existing 15-node LangGraph system** named as "the reference implementation and migration source" | Porting the 15 nodes forward as requirements — the nodes ARE a business execution graph | It is "not the foundation. It is neither preserved because it exists nor replaced to avoid it." Any PRD requirement traceable to a LangGraph node name needs re-deriving as context/policy/capability/outcome. The repo's own CLAUDE.md engine (`graph.py`, `nodes.py`) is this same temptation in code form. |
| F11 | **The Litmus test itself** | — | Use it as the PRD's self-check, verbatim: "can a new business be onboarded without generating a business-specific execution graph or state machine, while the Agent still reasons about situations nobody enumerated? Yes means an agent platform. No means a workflow engine with a model attached." |

---

## EXTRA 4. Two sentences the PRD should quote directly

- Control model: "A model-in-charge agent decides what to do next; a deterministic Core decides what the agent is permitted to do, executes it, and records what happened."
- Scope boundary: "An episode is **initiated or resumed only by an inbound interaction or an external system event** … **The platform never independently initiates an outbound conversation or episode.**"
