# Architecture Extraction for UX — Agent Studio

**Source (read in full):** `_bmad-output/planning-artifacts/architecture/architecture-AgentStudio-2026-10-07/ARCHITECTURE-SPINE.md`
(frontmatter: `type: architecture-spine`, `status: final`, `altitude: initiative`, `created/updated: 2026-10-08`)

**Method.** Every claim below is either a VERBATIM quote with its section reference, an explicit
`SPINE SILENT`, or marked `[INFERRED]`. Nothing is imported from the brief, the `.memlog.md`, or the
existing voice codebase — the spine is the only source read.

**Headline for UX:** this is a **substrate spine, not a product spec**. It fixes *where* things happen
and *what is invariant*; it is almost entirely silent on numbers, timing, surfaces and schemas. Three
quarters of the UX-relevant questions below land in `SPINE SILENT` or in the spine's own **Deferred**
table. That is itself the most important finding: the UX spec is not constrained by timing decisions,
because **no timing decision has been made yet**. Where the spine *does* bind the experience, it binds
it hard — the denial taxonomy, the evidence rule, the pinned-version rule, the two-exits rule and
AD-22 are each load-bearing for screens.

---

## 1. Latency and timing

**SPINE SILENT on every number.** There is no latency budget, no timeout value, no retry count, no
backoff policy, no p50/p95 target, no "sub-second" / "seconds" / "minutes" classification anywhere in
the document. `grep` for "latency" returns three hits, all of them deferrals or prohibitions, never a
budget.

What the spine *does* say, verbatim:

- **Stack §, preamble:** "**Seed, verified against primary sources 2026-10-08.** The code owns this
  once it exists. Model and provider are deliberately unpinned — see AD-14."
- **Deferred §, "Model routing and tiering policy":** "An evaluation question. The architecture must
  express tiering; the policy is **measured, not designed**."
- **Deferred §, "Context assembly":** "What sits permanently in agent context versus what is fetched
  on demand is a **latency and quality tuning question**, bounded by AD-7 (all authoritative context
  carries provenance) and AD-3. **Measured, not designed up front**."
- **Proof Gate §:** the end-to-end comparison against the old implementation is run on, among others,
  "number of model calls, **latency**, control and observability".

**Retries — the only retry statement in the document (AD-10):** "External effects are
at-least-once. **The Core issues the idempotency key, scoped by tenant and episode**; the adapter
honours it. **An action whose contract cannot define one is not eligible for automatic retry.**"
No retry *count*, no delay, no ceiling. SPINE SILENT on retry limits.

**Timeouts:** SPINE SILENT. The word does not appear.

**Async boundaries that ARE named (the structural, not numeric, timing picture):**

- **AD-13** — episode lifecycle is "`active` / `pending` awaiting a named external input / `closed`".
  `pending` is the spine's only named *wait* state.
- **AD-2** — `suspend` is one of the seven closed request kinds the Agent may emit.
- **AD-13** — "concurrent inbound messages on one episode are **serialized**"; "a result arriving
  after close is recorded as a **late result** and never mutates the resolution."
- **AD-12** — "Each model decision, authorized execution and evidence write is a **durable step**."
- **Runtime Interaction §** — the per-turn critical path is ordered: "guard evaluation · load or
  create episode · pin versions" → agent turn → typed request → "validate contract · authorize ·
  classify any denial" → adapter execution → "write evidence + result in one durable step" →
  resolution validation → egress.

**[INFERRED] timing shape, from structure alone (no numbers exist to quote):**
- A turn costs **at least** one guard evaluation (AD-21 allows it to be *model-based*) **plus** at
  least one model decision, **plus** possibly a model-based resolution validation at close — so a
  single inbound turn is a multi-model-call operation, i.e. seconds, not sub-second.
- `effect` requests go out through an adapter to a third-party system (AD-9/AD-10), so the slowest
  path is third-party-bound and unbounded by anything the spine states.
- Because **V1 channel is email / inbound messaging** (given as task context; the spine defers the
  channel entirely — Deferred §, "V1 channel": "Behaviour is channel-independent by AD-16 and AD-22"),
  the whole agent-side turn is *off* the human's interactive path. Per-turn latency is a delivery-time
  concern, **not** a UI progress-bar concern. The *Builder* conversation is the only place a human
  waits on a model in real time — and the spine says nothing about that wait.

---

## 2. Streaming

**SPINE SILENT.** No SSE, no WebSocket, no long-poll, no "stream", no "chunk", no token-level
delivery decision appears anywhere in the document, for either the Builder conversation or agent
output.

The only egress statement (**AD-22**) is message-granular, not token-granular: "Within an episode so
initiated, the Core may emit **messages** through a channel adapter's **egress port**."

**[INFERRED]** For an email/inbound-messaging V1, agent output is inherently **whole-message**, not
streamed — the channel has no streaming affordance. Streaming is therefore a *Builder-surface-only*
question, and it is entirely open: the UX spec may choose it freely without contradicting the
architecture.

---

## 3. The Business Specification as a stored artifact

### Schema — explicitly deferred

**Deferred §, "The concrete specification schema":** "Its invariants are fixed — one artifact compiled
by the Core (AD-4), goals and obligations as typed state (AD-19), the resolution envelope (AD-20),
immutable gated versions (AD-23), and no ordering constructs. **The field-level schema belongs to the
Specification and Builder epics**."

So: **no field list exists.** The UX spec cannot render a spec editor against a known schema.

### What IS fixed about its content

- **Layer table:** `spec/` owns "The business's declared **context, policies, authorities, capability
  grants and outcome expectations**".
- **Diagram node:** "Business Specification — context · policies · authorities · grants".
- **Platform-Owned vs Business-Configurable §** — the complete business-configurable list, which is
  the closest thing to a field inventory the spine offers: "Identity, context, terminology,
  communication preferences"; "Which capabilities are granted"; "Authority boundaries, confirmation
  requirements"; "Which guard conditions apply"; "Which goals exist and what obligations attach";
  "The rules and predicates themselves"; "Expected outcomes and the resolution payload";
  "Authoritative sources and their precedence"; "Escalation conditions, data lifecycle requirements";
  "Evaluation criteria"; "Domain safety packs, as optional extensions".
- **Consistency Conventions §:** "specification fields use **business vocabulary**"; and
  "Vocabulary borrowed from existing agent-manifest practice (**autonomy level, boundaries, risk
  profile**) rather than coined. The term 'AgentSpec' is avoided — it collides with two unrelated
  projects."
- **A hard prohibition:** "**The specification artifact may not contain ordering or sequencing
  constructs; the compiler rejects them.**" (Consistency Conventions §) — reinforced by **AD-1**'s ban
  on "no business transition graph, no business state machine, no workflow language".

### Versioning, validation, promotion

- **AD-23 (verbatim, whole rule):** "A specification version is **immutable once promoted**.
  Promotion requires its validation suite to pass — **a hard gate, not advice**. **Rollback is
  selecting an earlier version.** In-flight episodes keep the version pinned at their start (AD-11)."
- **AD-23 Prevents:** "unreviewed behaviour change, and having no way back".
- **Builder layer, Builder §:** `builder/` owns "Conversation and sources → specification + knowledge
  artifacts → **validation → promotion**".
- **AD-4:** "the Builder produces the artifact and **never compiles projections**"; "The agent's
  context, the tool surface offered to the model, and the policy the Core enforces are **projections
  compiled from one specification artifact by the Core**"; "The **compiler version** is pinned into
  the episode alongside the specification version."

### Does an edit propagate instantly, or require a rebuild?

**The spine answers the *semantics* and is silent on the *duration*.**

- **It is NOT instant for live work.** **AD-11:** "An episode captures its specification version,
  compiler version and knowledge-source versions **at creation**, and reads them from episode state
  thereafter, **never live**." Prevents: "an episode **resuming days later under changed rules**".
  **AD-23** repeats it: "In-flight episodes keep the version pinned at their start".
- **There IS a compile step.** AD-4's projection compilation is a real build: spec artifact → agent
  context + tool surface + enforced policy. **SPINE SILENT on how long compiling projections takes,
  whether it is synchronous with promotion, or whether it is cached.**
- **There IS a blocking gate.** AD-23's validation suite "must pass" before promotion. **SPINE SILENT
  on how long the validation suite runs**, what it contains, or whether it is interactive.

**UX consequence [INFERRED]:** a spec correction has **two** waits the UX must cover — a validation-
suite wait at promotion (duration unknown) and then an indefinite **tail period in which already-
running episodes still behave the old way**. The second is not a spinner; it is a state the operator
must be able to *see and understand* ("conversations started before this change still follow the old
rules"). Nothing in the spine provides a mechanism to surface that tail, and nothing forbids one.

**A defect class the UX must help prevent (AD-4):** "**A capability the Agent can see but policy will
always deny is a defect.**" And AD-4 Prevents: "the Agent believing it may do what the Core will
refuse — **a promise made to a customer and then broken, which is worse than a refusal**". [INFERRED]
This is the strongest argument in the document for showing the operator a *coherent* preview of what
the agent can and cannot do, before promotion.

---

## 4. Asynchronous and long-running work

**SPINE SILENT on all of it as a job system.** There is no job queue, no worker, no scheduler, no
cron, no "background", no "notification", no "nightly", no "batch" anywhere in the document.

What exists structurally:

- **`pending` episodes (AD-13):** "one lifecycle (`active` / `pending` **awaiting a named external
  input** / `closed`)". This is the one first-class "waiting on the world" state.
- **`suspend` (AD-2)** is an Agent request kind.
- **Late results (AD-13):** "a result arriving after close is recorded as a **late result** and never
  mutates the resolution."
- **Durability (AD-12):** "**Prevents:** episodes that cannot be recovered after a process failure";
  every model decision / execution / evidence write is a durable step — so work survives restarts.
- **Deferred §, "Durability engine selection":** "Semantics fixed. Fallback floor: Postgres with a
  unique constraint on `(tenant, episode, step, idempotency key)` and evidence written in the same
  transaction." Candidate: "DBOS *(co-commit requires the evidence store and application store to be
  the **same** Postgres database)*".

**Ingestion / indexing as a job:** SPINE SILENT — see §6.
**Generation as a job:** SPINE SILENT. The Builder is named as a unit ("Conversation and sources →
specification + knowledge artifacts → validation → promotion") with **no statement that any of it is
async**.
**Evaluation as a job:** only "evaluation hooks" (Core layer) and "Evaluation mechanism" /
"Evaluation criteria" (Platform-Owned table). **Deferred §** notes assertion-based evaluation is
"standard **offline**" — the single hint that an offline/batch evaluation lane exists:
"**Inline resolution validation as a shipped mechanism** — Assertion-based evaluation is standard
offline; enforcing it **inline at episode close** is **our own extension**, provisional everywhere it
appears, and to be validated by the proof gate before being relied upon."
**Deployment as a job:** SPINE SILENT. No deploy pipeline, no rollout, no health check is described.

**[INFERRED]** The only architecturally-guaranteed "it finished while you were away" events are
(a) a `pending` episode being resumed by an inbound interaction or external system event, and (b) a
late result landing on a closed episode. Both are *episode* events, not *operator-task* events. A
"we'll notify you" pattern for ingestion or generation is **unconstrained** by this spine — invent it
freely, but know it is not yet backed by any named mechanism.

**A hard constraint on notification UX — AD-22:** "An episode is **initiated or resumed only by an
inbound interaction or an external system event**… **The platform never independently initiates an
outbound conversation or episode.**" **Prevents:** "a `pending` episode that can never be delivered;
and the platform cold-contacting people on its own initiative." [INFERRED] This governs the *agent's*
channel, not operator-facing notifications in the product UI — but any UX that offers "have the agent
follow up" / "nudge the lead" / "re-engage after 3 days" is **architecturally forbidden in V1**. See
§12.

---

## 5. Failure modes the user will actually witness

The spine's strongest UX-binding content. It supplies three closed vocabularies and one absolute
no-silent-defaults rule.

### The denial taxonomy — AD-5 (verbatim, whole rule)

> "Every denial is recorded as **exactly one** of `spec_defect` (the projections led the Agent to
> believe it was permitted), `business_refusal` (policy correctly denied), or `platform_error`. **Only
> `spec_defect` enters the specification backlog.** The divergence log is the specification's error
> signal and **needs no human transcript review**."

**Prevents:** "correct business refusals polluting the defect signal, and genuine specification
errors never surfacing."

**UX obligation [INFERRED]:** three visibly different things, in business language, never collapsed
into one "error" list:
- `spec_defect` → "the agent thought it was allowed to do this, and it wasn't" → **an item the
  operator must fix**. This is the only one that belongs on a to-do list.
- `business_refusal` → "the agent correctly declined" → **evidence the rules are working**, must NOT
  read as a problem.
- `platform_error` → "our fault, not yours" → must NOT be presented as something the operator can fix.

### The errors-are-typed rule — the no-benign-value guarantee

- **Consistency Conventions §:** "errors cross boundaries as **typed results, never as defaults**."
- **AD-18:** "Every Core mechanism declares a **closed outcome vocabulary**. Every outcome returns
  control to the Agent as a typed result, except a declared **safety halt**, which terminates the
  episode with a recorded outcome."

This is the project-rule alignment the task asks about: the architecture already forbids a failure
degrading into a default. **UX obligation:** anywhere a value could be absent, the UI must render the
typed outcome, not a zero/empty/"none found".

### Episode-terminating failure — the safety halt

- **AD-18:** "a declared **safety halt**, which **terminates the episode with a recorded outcome**."
- **AD-21:** a guard's closed outcomes are "return a typed constraint to the Agent, or **trigger a
  declared safety halt**."

**UX obligation [INFERRED]:** a halted episode is categorically different from a closed-successfully
episode and from an abandoned one. It needs its own visible state and its recorded outcome shown.

### Unverifiable claims — refused before the person sees them

- **AD-7:** "a claim naming an **unissued, altered, or cross-tenant reference is refused before it
  reaches the person**."
- **AD-7:** "Semantic faithfulness beyond provenance validity is **evaluated against a threshold,
  never guaranteed**." **[UX: this is an explicit, architect-stated uncertainty ceiling. The product
  may not promise the agent never says anything wrong — only that it never cites a source it wasn't
  given.]**
- **AD-7:** "General domain knowledge may come from the model, **must be marked as such in evidence**,
  and is **enabled or disabled per business**."
  **UX obligation:** a model-general-knowledge answer is a *marked, lower-assurance* answer and a
  per-business switch. The Episode Viewer can and should distinguish "this came from your material"
  from "this came from the model's general knowledge".
- **AD-6:** "A resolution asserting an effect **without a corresponding Core execution record is
  invalid**." **Runtime Interaction §:** "a claimed outcome **unsupported by evidence is refused** and
  returned to the Agent as a typed result."
  **UX obligation:** "the agent said it booked the meeting" and "the meeting is booked" are different
  facts, and the architecture guarantees only the second is shown as done.

### Escalation / authority unavailable

- **Deterministic vs Delegated §:** "The platform's guardrail obligation is to **refuse and return a
  typed result stating that required authority or evidence is unavailable**; it never escalates on the
  Agent's behalf."
- **Platform-Owned §, generic guardrail set:** "**escalate when required authority or evidence is
  unavailable**."
  **UX obligation:** "the agent stopped because it wasn't allowed / couldn't verify" is a distinct,
  nameable, operator-visible state.

### Duplicate-effect risk

- **AD-10 Prevents:** "duplicate real-world effects on retry, and — worse — a key colliding across
  businesses so that **a genuine effect is silently suppressed as a duplicate**."
- **AD-10:** "An action whose contract cannot define one is **not eligible for automatic retry**."
  **[INFERRED] UX obligation:** an action that failed and cannot be auto-retried must surface as
  "needs a human", not quietly retried or quietly dropped.

### Cross-tenant

- **AD-17:** "**Any resolution that crosses tenants is rejected, not filtered.**" [INFERRED] Rejection
  is loud and visible by design; a UI must never show a silently-empty result where a cross-tenant
  reference was involved.

### Explicitly NOT covered

- **Rate limits:** SPINE SILENT.
- **Provider outages:** SPINE SILENT (AD-14 makes the provider swappable; nothing states what happens
  when it is down).
- **Document-parsing failures:** SPINE SILENT — see §6.
- **Partial results / degraded retrieval:** SPINE SILENT on a degraded-retrieval mode. Retrieval
  architecture is deferred: "Grounding, provenance and version-pinning are required; **hybrid versus
  dense versus deterministic lookup is not an invariant**."

---

## 6. Document / knowledge ingestion

**Almost entirely SPINE SILENT.** No accepted format is named. No size limit. No page/token cap. No
processing stage list. No OCR, chunking, embedding or parse-failure handling. No duration.

Everything the spine says about Knowledge, verbatim and complete:

- **Layer table:** `knowledge/` owns "**Version-pinned authoritative business material and retrieval
  over it**".
- **Diagram node:** "Business Knowledge — version-pinned sources".
- **Builder §:** "Conversation and **sources** → specification + **knowledge artifacts** → validation
  → promotion" — so ingestion is a Builder-phase activity producing artifacts.
- **AD-8 (whole rule):** "The Agent decides *when* to retrieve; it never retrieves directly. Pinning
  is at **source-version granularity**, and every provenance reference carries its source version."
- **AD-7:** provenance is "bound to `(tenant, source, source version, locator)` and **valid only for
  the issuing episode**"; "Authoritative sources include **recorded retrieval results**, the
  version-pinned Business Specification projection, and **any other source the specification declares
  authoritative**."
- **AD-11:** an episode pins "**knowledge-source versions** at creation".
- **Business-configurable:** "**Authoritative sources and their precedence**" — so the operator
  declares which material wins when two sources disagree.
- **Deferred §, "Retrieval architecture":** quoted in §5.

**UX-relevant vocabulary that IS fixed:** a knowledge item has a **source**, a **source version**, and
a **locator** (AD-7's provenance tuple). [INFERRED] That tuple is exactly what an Episode Viewer can
render as a citation: *which document, which version of it, and where inside it*. It is the one
retrieval detail the architecture guarantees will be available.

**[INFERRED] UX consequence:** because the UX spec cannot state formats, limits or durations, it must
either (a) treat ingestion as an open design area and define the experience it *wants* (progress,
per-file state, parse-failure surfacing) as a requirement back on the Specification/Builder epics, or
(b) note the gap. Option (a) is the useful move — the spine forecloses nothing here. The one thing
the UX can rely on is that **replacing a document creates a new source version**, and that in-flight
episodes keep the old one (AD-8 + AD-11).

---

## 7. Divergence detection

- **AD-5:** "**The divergence log is the specification's error signal and needs no human transcript
  review.**"
- **AD-5:** "Every denial **is recorded** as exactly one of…" — present tense, inline, at the moment
  of denial.
- **Runtime Interaction §, in the per-turn sequence:** "`C->>C: validate contract · authorize ·
  **classify any denial**`" and, on the denied branch, "`C->>C: record as spec_defect /
  business_refusal / platform_error`".
- **AD-5 Binds:** "Core, Specification, evaluation".
- **AD-12:** "Each model decision, authorized execution and **evidence write** is a durable step."

**Cadence — answer:** **real-time / inline, synchronously inside the turn that produced the denial.**
There is no batch, nightly or scheduled classification step anywhere in the document; classification
is part of the authorization path itself, not a downstream analysis pass.

**SPINE SILENT on:** aggregation, deduplication, grouping of repeated divergences, prioritisation,
counts, trend windows, and on any "backlog" data structure beyond the phrase "**enters the
specification backlog**".

**[INFERRED] UX consequence:** the operator's divergence list can be **as fresh as the last message
the agent handled** — effectively live. A "last updated 3h ago" or "refreshed nightly" framing would
*understate* the system. The UX may legitimately show divergences arriving live. But because nothing
aggregates them, the UX must decide grouping itself — a raw append-only log of every `spec_defect`
will repeat the same underlying gap many times, and presenting it unaggregated would read as noise.

---

## 8. Episode records — what the Episode Viewer CAN show

No episode schema is given. The following is the complete field inventory **implied by the ADs**, each
with its quote. Treat it as the Viewer's maximum possible content.

| Field | Quote / AD |
| --- | --- |
| Episode identity | AD-13: "One episode has **one identity**" |
| Tenant identity | AD-13 "one tenant"; AD-17: "**Every episode**, specification, knowledge source, provenance reference, idempotency key, evidence record and action request carries a tenant identity" |
| Lifecycle state | AD-13: "one lifecycle (`active` / `pending` awaiting a **named external input** / `closed`)" — note the *name of what it awaits* is part of `pending` |
| Specification version (pinned) | AD-11: "An episode captures its **specification version**… at creation" |
| Compiler version (pinned) | AD-4: "The **compiler version** is pinned into the episode alongside the specification version"; AD-11 |
| Knowledge-source versions (pinned) | AD-11: "and **knowledge-source versions** at creation" |
| Evidence record (one per episode) | AD-13: "**one evidence record**"; AD-6: "Evidence entries are **typed records against a platform-owned schema**, never opaque blobs" |
| External join key | AD-13: "one **join key** where it touches an external system of record"; Conventions: "external correlation is an **explicit join key**" |
| Durable step sequence | AD-12: "**Each model decision, authorized execution and evidence write is a durable step**" — a complete, replayable trace exists |
| Every request, by kind | AD-2: closed taxonomy `retrieve` · `read` · `effect` · `clarify` · `respond` · `escalate` · `suspend`, and "**every kind is authorized and journaled, reads included**" |
| Every denial, classified | AD-5: `spec_defect` / `business_refusal` / `platform_error` |
| Confirmations recorded | AD-2: "An `effect` whose contract requires confirmation is **not authorized until that confirmation is recorded**" |
| Execution records for effects | AD-6: "Only the **Core's execution record** may attest that an effect occurred" |
| Provenance references issued | AD-7: bound to `(tenant, source, source version, locator)`, "valid only for the issuing episode" |
| Knowledge-vs-model-knowledge marking | AD-7: "General domain knowledge may come from the model, **must be marked as such in evidence**" |
| Goals in play + outstanding obligations | AD-19: "The goals in play for an episode and the **obligations outstanding** for each are **typed Core state**" |
| Resolution envelope (5 fixed parts) | AD-20: "Every resolution carries: **which declared goal it concerns, whether that goal was served, under which authority, the evidence supporting it, and a business-defined payload**" |
| Resolution kind | AD-20: enumeration **deferred**; envelope fixed |
| Safety-halt outcome | AD-18: "terminates the episode **with a recorded outcome**" |
| Late results | AD-13: "a result arriving after close is **recorded as a late result** and never mutates the resolution" |
| Guard verdicts | AD-21: verdict is enforced and its outcomes closed. **[INFERRED]** journaled — AD-12 requires un-journaled reads not to occur, but guard verdicts are not named as a step. |
| Timestamps | Conventions: "**timestamps UTC**" |
| Evidence naming vocabulary | Conventions: "evidence vocabulary follows **OpenTelemetry GenAI naming** where it exists"; Stack: "OpenTelemetry GenAI conventions *(Development stability… expect churn)*" |

**NOT available / excluded:**
- **Cross-episode memory.** AD-13: "**Cross-episode memory is out of scope.**" Deferred §: "Long-term
  memory semantics — Out of scope by AD-13." **[INFERRED] No "everything we know about this lead"
  view is backed by the architecture in V1.**
- **Channel identity.** AD-16: "**The Agent and Core never learn which channel an episode is on.**"
  [INFERRED] A channel badge, if shown, comes from the adapter layer, not from episode state.
- **Credentials.** AD-24: "**No credential value appears in Core state, episode evidence, agent
  context or any prompt.**"
- **A human-readable summary field, a title, a subject, a participant name, a sentiment or an outcome
  label in business language:** SPINE SILENT on all. **[INFERRED] the Viewer must derive its headline
  from the resolution envelope (goal + served/not-served), because nothing else is guaranteed.**

**Critical AD-12 caveat for the Viewer — verbatim:** "**Step boundaries are a durability concern only
— nothing may read the step sequence as a permitted order.**" **[INFERRED] A UI that renders the step
list as a *workflow* — numbered stages, a progress pipeline, "step 3 of 7" — misrepresents the
architecture. The trace is a history, not a process diagram.** This is the single most direct
UX-pattern prohibition in the document (see §12).

---

## 9. Authority / permission model

Named, closed vocabularies the UI may need to express in business language:

**Request kinds (AD-2, closed):** `retrieve` · `read` · `effect` · `clarify` · `respond` ·
`escalate` · `suspend`. "Adding a request kind is **platform evolution (AD-15), never business
configuration**."

**Denial classes (AD-5, closed):** `spec_defect` · `business_refusal` · `platform_error`.

**Episode lifecycle (AD-13, closed):** `active` · `pending` · `closed`.

**Core exits (AD-18, closed):** typed result to the Agent, **or** safety halt. "**The Core has exactly
two exits.**"

**Guard outcomes (AD-21, closed):** "return a typed constraint to the Agent, or trigger a declared
safety halt."

**Authority concepts, verbatim:**
- **Action contract fields (Conventions §):** "action contracts declare **input schema, effects,
  authority required, confirmation requirement, success evidence and idempotency scope**." [UX: this
  is the per-capability field set an "what can the agent do" screen can render.]
- **Confirmation gate (AD-2):** "An `effect` whose contract requires confirmation is **not authorized
  until that confirmation is recorded**." **SPINE SILENT on who confirms** — customer, operator, or
  external system — and on any confirmation UI.
- **Business-configurable:** "**Authority boundaries, confirmation requirements**"; "**Which
  capabilities are granted**"; "**Escalation conditions**"; "**Which guard conditions apply**".
- **Authoring vocabulary (Conventions §):** "**autonomy level, boundaries, risk profile**" — borrowed
  from agent-manifest practice. **[INFERRED] This is the nearest thing to a named authority *tier* in
  the document: an "autonomy level" exists as a concept but its values are not enumerated. SPINE
  SILENT on the tiers themselves.**
- **Escalation ownership (Deterministic vs Delegated §, emphatic):** "Escalation has exactly one
  owner: **the Agent escalates.**… it **never escalates on the Agent's behalf**." Delegated column:
  "Whether to act, continue, respond — **and whether to escalate**".
- **Resolution authority (AD-20):** every resolution records "**under which authority**" it was made.
- **The generic guardrail set (Platform-Owned §, verbatim, the operator's implicit safety promise):**
  "do not invent business facts · do not act outside declared authority · do not perform undeclared
  actions · do not claim success without evidence · escalate when required authority or evidence is
  unavailable". **[INFERRED] This is almost directly speakable as the product's trust story, in
  business language, with no leakage of agent/prompt/graph vocabulary.**
- **Domain safety packs:** business-configurable, "as optional extensions".
- **AD-3, the framing that justifies showing authority as real:** "Any constraint that must hold is
  enforced by the Core… **no enforcement path may rely on the model respecting what it was told.**"
  **Prevents:** "safety and authority depending on the model choosing to comply." [INFERRED] The UX
  may honestly tell the operator their boundaries are *enforced*, not *requested* — this is the
  thesis "reasoning is broad; authority is bounded" made literal.

---

## 10. Multi-tenancy, accounts, roles, auth

- **Tenancy is absolute and data-level. AD-17 (whole rule):** "Every episode, specification, knowledge
  source, provenance reference, idempotency key, evidence record and action request carries a tenant
  identity. **Any resolution that crosses tenants is rejected, not filtered.**" **Binds: all.**
  **Prevents:** "a citation resolving against another business's source; idempotency keys colliding
  across businesses; **a second business silently sharing the first's state**."
- **AD-7:** cross-tenant provenance references are "**refused before** [they reach] the person".
- **AD-24:** "Adapter credentials are held at the adapter boundary and **resolved per tenant**."
- **Deferred §, "Tenancy deployment model (shared runtime, per-tenant workers, per-tenant
  deployment)":** "AD-17 makes tenancy correct at the **data level regardless of topology**."

**Users, roles, authentication, authorization-of-humans, seats, invitations, permissions-per-person:
SPINE SILENT — completely.** The document models the *business* as the tenant and never models a
*person* inside it. The only human actors it names are "Person" (the customer, in the Runtime
Interaction sequence diagram) and, implicitly, whoever converses with the Builder.

**[INFERRED]** Nothing supports *or* forbids multiple operators per business. The UX spec should treat
single-operator-per-business as the safe V1 assumption and flag any role-differentiated UI as an
unbacked requirement. Note also AD-5's "**needs no human transcript review**" — the architecture is
designed so the operator is *not* a reviewer-of-conversations by obligation. [INFERRED] That argues
against a reviewer/approver role existing at all in V1.

---

## 11. State the operator can see

**Fixed, quotable:**
- **Episode:** `active` / `pending` / `closed` (AD-13), plus **safety-halted with recorded outcome**
  (AD-18) and **has late results** (AD-13).
- **Specification version:** `promoted` and thereby **immutable** (AD-23); earlier versions remain
  **selectable for rollback** (AD-23); a version is **pinned into episodes** (AD-11).
- **Obligations:** per-goal **outstanding** vs met, as typed Core state (AD-19).
- **Goal:** per resolution, **served or not served** (AD-20).
- **Denial:** the three-way classification (AD-5).

**SPINE SILENT on:**
- Any **agent** status enum — no `draft`, `testing`, `live`, `paused`, `published`, `disabled`
  anywhere in the document. **There is no concept of an agent being on or off.** [INFERRED] The spine
  has no "agent" object at all as a user-facing entity: there is a specification, and episodes run
  against the version pinned at their start. A "pause the agent" control has **no architectural
  backing** and would need inventing.
- A **pre-promotion** spec state. AD-23 names only "immutable once promoted" and a validation suite
  that must pass; it does not name a draft/in-review state, though [INFERRED] one necessarily exists
  before promotion.
- Any **document** status enum (uploaded/processing/indexed/failed). SPINE SILENT.
- Any **run/test** status. SPINE SILENT — the Proof Gate is a one-off engineering exercise, not a
  product feature.

---

## 12. Constraints that forbid a UX pattern

Each is a direct quote plus the pattern it rules out.

1. **No workflow, pipeline or stage-based UI for behaviour.** AD-1: "No deterministic next-action
   selection, no primitive precedence table, **no business transition graph, no business state
   machine, no workflow language**, no precondition-derived orchestration standing in for agent
   decision-making." Conventions: "**The specification artifact may not contain ordering or sequencing
   constructs; the compiler rejects them.**" **Forbids:** a flow-builder, a node canvas, a
   drag-and-drop journey editor, an "if the lead says X then…" branch editor, a numbered script. The
   operator describes *what is true and what is allowed*, never *what order to do things in*.
2. **No step-sequence-as-progress UI.** AD-12: "**Step boundaries are a durability concern only —
   nothing may read the step sequence as a permitted order.**" **Forbids:** "step 3 of 7", a progress
   pipeline over an episode, a stage tracker.
3. **No operator-initiated outbound.** AD-22: "An episode is initiated or resumed **only** by an
   inbound interaction or an external system event… **The platform never independently initiates an
   outbound conversation or episode.**" **Forbids:** "start a conversation", "send a follow-up",
   "re-engage after N days", campaigns, scheduled nudges, drip sequences. This is the single biggest
   feature-shaped prohibition in the document.
4. **No instant-effect spec editing.** AD-11 + AD-23: in-flight episodes "read them from episode
   state thereafter, **never live**". **Forbids:** presenting a spec change as immediately in force
   everywhere; forbids optimistic "applied" messaging without qualification.
5. **No edit-in-place on a promoted version.** AD-23: "**immutable once promoted**". **Forbids:** an
   always-live editor that silently saves into the running version. Editing must be understood as
   creating a next version.
6. **No save-past-a-failing-gate.** AD-23: "Promotion requires its validation suite to pass — **a hard
   gate, not advice**." **Forbids:** "publish anyway", a dismissible warning, a soft override.
7. **No cross-business view or shared library of real material.** AD-17: "**Any resolution that
   crosses tenants is rejected, not filtered.**" **Forbids:** benchmarks against other businesses
   built from their episodes, a shared knowledge pool.
8. **No "the agent remembers this customer".** AD-13: "**Cross-episode memory is out of scope.**"
   **Forbids:** a lead profile that accumulates across conversations, "as we discussed last week".
9. **No agent-authored proof.** AD-6: "the Agent **cannot author evidence**"; "A resolution asserting
   an effect without a corresponding Core execution record is **invalid**." **Forbids:** showing the
   agent's own account of what it did as the record of what happened.
10. **No channel-aware behaviour authoring.** AD-16: "The Agent and Core **never learn which channel**
    an episode is on." **Forbids:** per-channel behaviour rules in the spec ("be shorter on SMS").
11. **No model/provider configuration surface.** AD-14: "Provider and framework abstractions live
    behind a runtime boundary defined by this platform… **Changing the model, provider or agent
    framework must not alter the business agent architecture.**" Stack: "Model and provider are
    **deliberately unpinned**." Deferred: model routing is "**measured, not designed**". **Aligns
    exactly with the brief's rule that the operator never sees model configuration — and makes it an
    architectural fact, not just a UX preference.**
12. **No business-level extension of platform semantics.** AD-15: "**Business configuration never
    changes Core semantics.**" **Forbids:** an operator-facing "advanced" escape hatch, custom
    request kinds, a rules DSL that reaches into the Core.
13. **No transcript-review-as-the-job.** AD-5: the divergence log "**needs no human transcript
    review**". **[INFERRED] Forbids** designing the operator's primary loop as reading conversations;
    the architecture deliberately replaces that with a classified divergence signal.

---

## 13. Explicitly named UI / API surfaces, endpoints, client-facing contracts

**No endpoint, route, URL, HTTP verb, GraphQL schema, screen, page or UI component is named anywhere
in the document. SPINE SILENT.**

The spine names **ports**, not surfaces:

| Named surface | Quote |
| --- | --- |
| Channel adapter ingress | AD-16: "A channel adapter provides **both ingress and egress** (AD-22)"; Runtime Interaction: "`CH->>C: normalised turn (tenant, episode)`" |
| Channel adapter **egress port** | AD-22: "the Core may emit messages through a channel adapter's **egress port**" |
| Episode creation | AD-13: "It **creates episodes on an adapter's request**" |
| Agent→Core request port | AD-2: the seven closed request kinds |
| Core→Agent result contract | AD-18: "Every outcome returns control to the Agent as a **typed result**" |
| Extension/adapter contract | AD-9: "An external system is reached only as *Core contract → adapter → extension*"; Deferred: "**The adapter contract is the invariant**" |
| Capability transport | Stack: "**MCP, spec revision 2026-07-28** *(verified current 2026-10-08)*" |
| Agent runtime boundary | AD-14; Stack: "Pydantic AI 2.54.0 *(candidate, behind AD-14)*" |
| Store | Stack: "**PostgreSQL 16+**"; Python 3.12+ |
| Capability naming | Conventions: "Capabilities are **verb-first (`check_availability`)**" — **[INFERRED] the only concrete example of a capability name in the document, and it is technical. The UX must translate: the operator should read "check whether a time is free", never `check_availability`.** |

**Builder surface:** the Builder is named as a *layer* — `builder/` owns "Conversation and sources →
specification + knowledge artifacts → validation → promotion" — with **no UI, no API, no endpoint and
no interaction model specified**. The entire Builder experience is open design space.

---

## Summary of gaps the UX spec must own rather than inherit

| Area | Status |
| --- | --- |
| All latency numbers, timeouts, retry counts | SPINE SILENT — "measured, not designed" |
| Streaming (Builder and agent) | SPINE SILENT |
| Spec field-level schema | Deferred to Specification & Builder epics |
| Validation-suite duration and contents | SPINE SILENT |
| Projection-compile duration | SPINE SILENT |
| Ingestion formats, limits, stages, failures, duration | SPINE SILENT |
| Background job system / notifications | SPINE SILENT |
| Rate limits, provider outages | SPINE SILENT |
| Users, roles, auth, seats | SPINE SILENT (tenant ≠ user) |
| Agent on/off/paused state | SPINE SILENT — no such concept exists |
| Resolution kind enumeration | Deferred (AD-20: envelope fixed, vocabulary deferred) |
| Autonomy-level tier values | SPINE SILENT (the concept is named; the values are not) |
| Any endpoint or screen | SPINE SILENT |
