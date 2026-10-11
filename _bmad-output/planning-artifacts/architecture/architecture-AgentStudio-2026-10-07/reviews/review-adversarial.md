---
name: 'Adversarial review — Architecture Spine, Agent Studio'
target: '../ARCHITECTURE-SPINE.md'
lens: adversarial — divergence-pair construction
reviewed: '2026-10-08'
scope: 'The spine document only. The existing LangGraph/voice code was deliberately NOT reviewed; it is a reference implementation of a different product line.'
---

# Adversarial Review — ARCHITECTURE-SPINE.md

**Verdict:** The direction is sound and AD-1/AD-2/AD-9/AD-14 genuinely hold under attack, but the spine fixes the *flow of control* and almost none of the *shared data shapes* or *ownership of mutation*, so a dozen pairs of units can each obey every AD to the letter and still fail to compose — most severely around tenancy, the action-request/evidence/citation envelopes, outbound messaging, and who compiles the specification.

Method: for each finding, two independently-built units, two choices that each pass every AD as written, the consequence at integration, and replacement AD text.

---

## 1. No business/tenant identity is a first-class key — business two collides with business one `[CRITICAL]`

**Units:** the knowledge subsystem + the extension/booking adapter, versus the Core (and the second business's agent onboarded six months later).

**The two compliant choices.** The spine names "one specification, many projections," "version-pinned sources," "one episode identity scheme," and an idempotency key "named by the action contract." It never once names a business, tenant or deployment as part of any identity. So:

- Knowledge author: sources are rows in the shared Postgres store keyed `(source_id, version)`; which sources a business may read is the grant list in its specification. Citation resolution (AD-7) is implemented exactly as written — "a citation whose span does not resolve is rejected" — i.e. look up `(source_id, version, span)` and check it resolves.
- Booking adapter author: AD-10 says the *contract* names the key. The natural contract-level key for `book_appointment` is `(customer_email, slot_start)`, written into the adapter's dedupe table.

**Consequence.** Two concrete integration failures, both silent:

- Business A's agent emits a citation naming business B's `source_id@version` (a hallucinated or transcript-echoed id). It resolves. AD-7's one *enforced* check passes, and business A quotes business B's prices with a green grounding signal. The grant list was consulted at retrieval time, not at resolution time, and AD-7 only requires resolution.
- Two businesses sharing a tenant-neutral idempotency keyspace: a dentist and a salon both book `omer@x.com` at `2026-11-02T10:00Z`. The second real booking is recognised as "the same effect," suppressed, and AD-10 reports success. A dedupe that *suppresses a genuine effect* is worse than the duplicate it prevents, and AD-6 will happily attest the effect occurred because a record exists.

**Proposed AD (new) — AD-17, Tenancy is part of identity, not configuration.**
> Every identity in the platform is tenant-scoped. The business identifier is a mandatory component of the episode identity, the specification version, every knowledge source and source version, every evidence record, every journal step and every idempotency key. The Core resolves nothing — no source, no span, no contract, no evidence record, no join key — outside the episode's own tenant; a cross-tenant resolution is an error, never a miss. Citation resolution additionally re-checks that the cited source is in the episode's pinned grant set, so resolution and authorization cannot disagree. Tenant isolation is platform-owned and is not expressible in business configuration.

---

## 2. Nothing can send an outbound message — the dependency arrows forbid it `[CRITICAL]`

**Units:** the channel adapter, versus the episode runtime handling a resumed `pending` episode.

**The two compliant choices.** AD-16 makes the channel an adapter; the dependency diagram points the channel adapter *inward* at the Core, and the closing note says "nothing the Core depends on may depend on an extension, a channel, a provider." The sequence diagram shows exactly one `C->>CH: reply`, after episode close. AD-13 allows `pending` "awaiting a named external input."

- Channel-adapter author reads it as strict request/response: the adapter calls the Core with a normalised turn and the Core returns the reply synchronously. There is no inbound-to-adapter entry point, because the Core may not depend on the channel.
- Runtime author reads "pending awaiting a named external input" as resumable: a booking webhook arrives, the episode resumes, the Agent emits a `respond` action request, and the Core must deliver it — so the Core needs an outbound channel port it calls.

**Consequence.** The first unit ships an adapter with no outbound capability and no callback registration. The second ships a Core that resumes episodes and produces replies nobody can deliver. The entire `pending` lifecycle state — one third of AD-13's lifecycle — is undeliverable in the integrated system, and the first realistic business interaction (book, confirm asynchronously, tell the person) cannot complete. The Proof Gate as written requires an external side effect and escalation, both of which can land asynchronously.

**Proposed AD (new) — AD-18, Delivery is an outbound port.**
> Reply delivery is an outbound Core port, `deliver(episode, message)`, implemented by the channel adapter like any other adapter: the Core depends on the port contract, never on the adapter. Every reply — whether produced during a turn, on resume of a `pending` episode, or by a guard pre-empt — is delivered through that one port and journaled as a durable step. Synchronous request/response is an adapter-local optimisation of this port, never an assumption the Core may make. The number of messages the Core may deliver per inbound turn is zero or more, and the adapter must tolerate all three cases.

---

## 3. Citations as model-authored tuples make AD-7's only enforced check forgeable `[CRITICAL]`

**Units:** the Agent runtime boundary + the knowledge subsystem, versus the Core's citation-span resolver.

**The two compliant choices.** AD-7 says business-authoritative facts "must carry a citation into a version-pinned source, and a citation whose span does not resolve is rejected."

- Knowledge/runtime author: the retrieval result shown to the model contains `(source_id, version, offsets, text)`; the model emits `{source_id, version, span}` alongside each claim. The Core resolves the span against the store. Compliant, and reads naturally.
- Core author: retrieval mints opaque, episode-scoped handles (`ret_7f2#3`); the model may cite only handles it was shown; the Core resolves the handle to the recorded retrieval step.

**Consequence.** Under the first choice the enforced check is near-vacuous: any syntactically valid span in a real pinned document resolves, so a model that invents a price and attaches the first chunk's coordinates passes structural grounding with full confidence. The spine's own distinction — structural tier enforced, semantic tier only evaluated — collapses, because the structural tier was supposed to guarantee *provenance*, and tuple citations guarantee only *existence*. Worse, the two units produce incompatible evidence records, so the evaluation subsystem built in week three cannot compute a grounding rate across episodes.

**Proposed AD (tighten AD-7, add clause).**
> A citation is an opaque handle issued by the Core when it performs a retrieval, scoped to the episode and bound to the recorded retrieval step and the source version that step read. The Agent may cite only handles delivered to it within the current episode. A citation that is not such a handle is rejected without resolution; a handle whose underlying span no longer resolves is rejected. Models never author source identifiers, versions or offsets.

---

## 4. "Action request" has no fixed taxonomy — reads escape authorization and the journal `[CRITICAL]`

**Units:** the records-system extension adapter, versus the authorization/validation layer.

**The two compliant choices.** AD-2 governs "every effect." The sequence diagram lists five action-request kinds (`retrieve / tool / clarify / escalate / respond`). AD-12 journals "each authorized execution."

- Adapter author: `lookup_customer(email)` is a read with no effect. AD-2 binds effects; AD-10 explicitly contemplates actions ineligible for retry because they cannot define an idempotency key, which reads do not need. So the lookup is modelled as a cheap, unauthorized, unjournaled context fetch — it is not an *effect*, so no AD touches it.
- Authorization-layer author: everything the Agent asks for passes the PEP, because AD-2's sentence "the Agent cannot invoke an external system" is unqualified, and AD-15 says businesses configure authority boundaries — which obviously include who may read a customer record.

**Consequence.** Three failures stack. (a) Replay diverges: AD-12's promise of consistent replay breaks the moment an un-journaled external read feeds a model decision, because the read returns different data on replay and the journaled decision no longer follows from the journaled inputs. (b) PII reads are unauthorized for business one and must become authorized for business two under stricter policy — that is a Core semantic change driven by business requirements, exactly what AD-15 forbids. (c) The evidence record has a hole: a resolution grounded in a record lookup has no corresponding Core record, so AD-6's validator cannot tell "no evidence" from "evidence not required."

**Proposed AD (tighten AD-2).**
> Every interaction between the Agent and anything outside the Core — tool, API, external system, retrieval, reply, escalation — is an action request of one closed, Core-owned kind set, is validated against its contract, is authorized, and is journaled as a durable step. Reads are not exempt. A contract declares its effect class (`none` / `external`) solely to govern retry eligibility and idempotency-key requirements, never to exempt it from authorization or journaling.

---

## 5. Two defensible compilers for one specification `[CRITICAL]`

**Units:** the Builder, versus the Core/episode runtime.

**The two compliant choices.** AD-4 requires agent context, tool surface and enforced policy to be "projections compiled from one specification artifact." AD-11 pins "the specification version" into the episode. Neither names the compiler's owner or its versioning.

- Builder author: the Builder owns compilation — "conversation and sources → specification + knowledge artifacts → validation → deploy" — and deploys an immutable bundle of three projections. The Core loads projections.
- Core author: the Core compiles at episode start from the pinned specification version, because that is the only way AD-11's "reads them from episode state thereafter" can be satisfied for a spec that changed since deploy, and because AD-15 makes projection semantics platform-owned, i.e. Core.

**Consequence.** If both get built, policy is enforced from one compilation and the tool surface is offered from another — precisely the AD-4 failure mode ("the Agent believing it may do what the Core will refuse"), reintroduced by the AD meant to prevent it. Even if only the Core compiles, the *compiler version* is not pinned, so a compiler bug fix silently re-projects every running and `pending` episode mid-flight, and AD-11's stated purpose — "evaluation comparing episodes judged by different contracts" — fails for reasons AD-11 does not cover.

**Proposed AD (tighten AD-4 / AD-11).**
> Compilation happens exactly once, in the Builder, at deploy. It produces a single immutable specification bundle containing all three projections, identified by `(tenant, specification version, compiler version)`. The Core never compiles, never derives a projection, and never reads the specification source. An episode pins the bundle identifier at creation and reads only that bundle thereafter. A bundle is immutable and is retained while any episode references it.

---

## 6. Two concurrent inbound messages on one episode — no ordering rule exists `[HIGH]`

**Units:** the channel adapter, versus the episode runtime and state store.

**The two compliant choices.** AD-13 gives an episode one identity and one lifecycle; AD-12 makes each model decision and each write a durable step; the deferred-durability note offers a fallback floor of "Postgres tables with a unique constraint on `(episode, step, idempotency key)`." Nothing states who serializes.

- Adapter author: fire each inbound message at the Core as it arrives — people double-text constantly, and the Core owns episode lifecycle and durability per AD-13, so serialization is the Core's job.
- Runtime author: the unique constraint *is* the concurrency control. Two turns race, both read step 14, both write step 15, one gets a constraint violation and the Core returns a typed error.

**Consequence.** Best case the second message is dropped with a typed error the adapter has no handling for, and the person's correction ("no, Tuesday") is lost. Worst case the two turns interleave at different steps and the Agent runs twice on divergent views of the same episode, double-booking with two different idempotency keys — AD-10 cannot help, because the two requests genuinely differ. This is the single most likely production incident in the whole design and no AD addresses it.

**Proposed AD (new) — AD-19, One writer per episode, ordered inbound.**
> An episode has exactly one writer at a time, held under a lease by the Core. Inbound turns are appended to a durable per-episode inbox in arrival order and are processed strictly in order; an inbound turn arriving while a turn is in flight is enqueued, never dropped and never processed concurrently. Adapters are fire-and-forget against the inbox and must assume at-least-once delivery with a stable per-message identifier for de-duplication. No unit outside the Core serializes, retries or coalesces inbound turns.

---

## 7. A result that arrives after the episode closed `[HIGH]`

**Units:** the booking extension adapter, versus the episode runtime.

**The two compliant choices.** AD-10 makes effects at-least-once; AD-6 makes the Core's record the only valid attestation; AD-13 makes `closed` a lifecycle state. Scenario: the adapter call times out, the Core records a failed execution, the Agent escalates and closes the episode — and the booking actually succeeded, with the vendor webhook arriving four minutes later.

- Adapter author: AD-6 says only a Core record may attest an effect and the effect *occurred*, so the late confirmation must be delivered to the Core as evidence. An episode without it is a lie.
- Runtime author: `closed` is terminal and the resolution was already validated against the evidence set; accepting a new evidence write would invalidate an already-validated resolution, so the late result is logged and dropped.

**Consequence.** Either a real appointment exists with no evidence anywhere in the system (and the escalated human double-books), or evidence mutates under a validated resolution and AD-6's validation becomes a statement about a snapshot nobody can reconstruct. The spine specifies only the happy path here, and both units are behaving correctly.

**Proposed AD (new) — AD-20, Terminal states and late effects.**
> `closed` is terminal for agent decision-making and for the validated resolution, which is immutable once validated. Evidence is append-only and may still be appended after close: a late or reconciled execution outcome is recorded as a post-close evidence entry against the same episode, never by mutating or re-validating the resolution. Appending a post-close entry that contradicts the validated resolution raises a reconciliation event for the tenant and is counted as such by evaluation. No unit may discard an effect outcome because the episode is closed.

---

## 8. Is authorization stateless, or can it return "pending approval"? `[HIGH]`

**Units:** the authorization/validation layer, versus the episode runtime (and the evaluation subsystem downstream).

**The two compliant choices.** AD-2 puts authorization on the critical path for every effect; AD-3 makes Core constraints binding; the configurable column includes "confirmation requirements"; AD-13 has a `pending` state "awaiting a named external input."

- Auth author: authorization is a pure total function `(request, bundle, episode state) -> allow | deny(reason)`. A confirmation requirement that is unmet yields `deny`; the Agent then asks the person and re-requests. Stateless, replayable, trivially testable — and it keeps the Core off the decision path per AD-2's second sentence.
- Runtime author: authorization returns `allow | deny | pending_approval`; on `pending_approval` the Core parks the episode in `pending`, and the human approval resumes execution of the already-validated request.

**Consequence.** Two incompatible outcomes. (a) The second choice executes a request authorized before intervening turns — by the time approval lands, the person may have changed the slot, and the parked request carries stale arguments with a stale idempotency key. (b) AD-5 fires on the first choice: every unmet confirmation is recorded as a *specification defect*, because the Core denied an action the Agent believed permitted. The divergence log — explicitly the specification's error signal requiring no transcript review — fills with normal confirmation flow and becomes unreadable. Two units, both compliant, and the evaluation subsystem is poisoned by the one that is otherwise better.

**Proposed AD (tighten AD-2, add clause).**
> Authorization is a pure, total, side-effect-free function returning `allow` or `deny` with a typed reason. It never parks, queues, defers or holds state. A human confirmation or approval requirement is modelled as a named external input obtained through its own action contract, whose recorded outcome then becomes part of the episode state the next authorization reads; the Core never executes a request authorized before that input was recorded. Arguments are re-validated and re-authorized at execution time, never carried across a resume.

---

## 9. Evidence: typed in Core vocabulary, or an opaque vendor blob? `[HIGH]`

**Units:** the extension adapter, versus the Core's resolution validator and the evaluation subsystem.

**The two compliant choices.** AD-6 makes the Core the sole author of evidence; AD-9 says the Core knows contracts, never vendors; the conventions table says contracts declare "success evidence" and evidence vocabulary follows OTel GenAI "where it exists" — which, for a booking confirmation, it does not.

- Adapter author: the Core must not know vendors, so the adapter hands back the vendor response and the Core stores it opaquely under the contract name. Core stays vendor-free, exactly as AD-9 demands.
- Core author: the contract's declared "success evidence" is a typed schema in platform vocabulary; the adapter maps into it.

**Consequence.** Under the first, deterministic resolution validation — listed under "Deterministic (Core)" — degenerates to "a record with this contract name exists." It cannot check that the booking is for the slot the Agent claims, so the Agent can claim "booked you for Tuesday 10am" over an execution record for Thursday and pass validation. The evaluation subsystem then writes per-vendor parsers to recover meaning, relocating vendor logic into evaluation, which AD-9 did not think to bind.

**Proposed AD (tighten AD-6 / conventions).**
> Every action contract declares a typed success-evidence schema expressed in platform vocabulary. The adapter's sole evidence responsibility is mapping the vendor response into that schema at the boundary; a response that cannot be mapped is a typed failure, not a success. Raw vendor payloads may be attached only in an opaque diagnostic field that no Core, resolution-validation or evaluation logic reads or parses. Resolution validation operates exclusively on typed evidence fields and citation handles.

---

## 10. The resolution envelope is deferred, but two units must agree on it now `[HIGH]`

**Units:** the Agent runtime boundary, versus the Core's resolution validator (and the Builder, which authors "which outcomes are expected").

**The two compliant choices.** AD-6 requires validating a claimed resolution against evidence; the Deferred table defers "resolution enumeration and outcome taxonomy"; the configurable column includes "which outcomes are expected."

- Builder author: outcomes are declared per business in the specification, so a resolution is a business-defined enum value plus free text.
- Core author: taxonomy is deferred, so a resolution is a free-form claim string plus asserted effect references, and validation checks the references.

**Consequence.** With the business enum, the Core must interpret business-specific outcome labels to validate them, which is per-business semantics inside the Core (AD-15 violation) or a per-business validator (the workflow-engine drift AD-1 exists to stop). With free text, validation reduces to "some evidence exists" and the enforced half of AD-6 is cosmetic. The deferral is defensible for the *taxonomy*; it is not defensible for the *envelope*, because the envelope is a shared data shape across two independently built units.

**Proposed AD (tighten AD-6).**
> The resolution envelope is Core-owned and fixed now, independently of the deferred outcome taxonomy: `{ outcome_label, asserted_effects: [evidence_ref], asserted_facts: [citation_handle], unresolved: [...] }`. `outcome_label` is business vocabulary and is opaque to the Core — never branched on, only recorded and compared by evaluation. Validation is purely referential: every asserted effect must resolve to a successful execution record in this episode, and every asserted fact to a citation handle from a recorded retrieval in this episode. Business-specific outcome semantics never enter Core code.

---

## 11. AD-5 does not say which denials are specification defects `[MEDIUM]`

**Units:** the authorization layer (which emits the signal), versus the evaluation subsystem (which consumes it).

**The two compliant choices.** AD-5: "When the Core denies an action the Agent believed permitted, the episode evidence records it as a specification defect."

- Auth author: the tool surface is projected from the specification (AD-4), so the Agent believed permitted anything it could see. Every denial of a visible capability is a specification defect — including schema-invalid arguments and malformed requests.
- Eval author: a defect means the *specification* was wrong, so only denials where the contract validated and the capability was granted but an authority condition failed. A malformed argument is an agent-quality issue, not a specification error.

**Consequence.** The signal AD-5 promises "requires no human transcript review" is either dominated by model argument errors — making the specification-defect rate a measure of model quality and useless for its stated purpose — or silently excludes genuine authority-boundary gaps if the two units disagree about which bucket a case falls in. Two readings, two dashboards, one number that means different things week to week.

**Proposed AD (tighten AD-5).**
> Every refusal carries a Core-owned typed reason from a closed set, and only one class counts as a specification defect: a contract-valid request for a granted capability refused because a declared authority condition was unmet. Contract-invalid requests, requests for ungranted capabilities, and refusals pending a named external input are recorded as distinct classes and are excluded from the divergence signal. Evaluation reads the reason class, never the message.

---

## 12. Knowledge pinning: a manifest at creation, or per-source at first read? `[MEDIUM]`

**Units:** the knowledge subsystem, versus the episode runtime.

**The two compliant choices.** AD-11: "An episode captures its specification version and knowledge-source versions at creation and reads them from episode state thereafter, never live."

- Knowledge author: pin one immutable manifest id covering the whole authoritative source set at creation; sources published later are invisible to this episode.
- Runtime author: "knowledge-source versions" are pinned per source — and you cannot know at creation which sources the episode will touch, so pin each source's version lazily at first retrieval and reuse it. Still never live after the first read.

**Consequence.** Under lazy pinning, two retrievals in one episode read versions published hours apart, and two citations in one reply can contradict each other while both resolve. Under manifest pinning, a mid-episode correction to a wrong price cannot reach a long-running `pending` episode, and nothing in the spine says that is intended or how an operator would force it. There is also an unaddressed retention hazard: a pinned version garbage-collected by the knowledge unit makes every citation in a replayed episode unresolvable, failing AD-7 retroactively.

**Proposed AD (tighten AD-11).**
> Knowledge pinning is a single immutable source-set manifest identifier resolved once at episode creation and covering every source the episode may read; per-source lazy pinning is forbidden. Sources or versions published after creation are invisible to that episode, with no mid-episode upgrade path. A manifest and every version it names are retained while any episode — `active`, `pending` or `closed` and subject to replay or evaluation — references them.

---

## 13. Who owns the idempotency key, and over what scope? `[MEDIUM]`

**Units:** the extension adapter, versus the Core.

**The two compliant choices.** AD-10: "Each action contract names the key under which a repeat is recognised as the same effect, and the adapter honours it."

- Core author: the contract *names* it (declares which fields compose it); the Core derives the value and passes it down; the adapter forwards it.
- Adapter author: the adapter honours it, therefore the adapter computes it from the declared fields at the boundary, where vendor key-format constraints are known.

Independently, scope is unspecified: a key over contract input fields alone is global; a key including the episode is episode-scoped.

**Consequence.** Divergent derivations mean the Core's journal replay dedupes on one key while the vendor dedupes on another, so a replayed step produces a second real effect — exactly the failure AD-10 names. On scope: an input-only key collapses two intentionally identical bookings made weeks apart into one (an effect suppressed), while an episode-scoped key lets a replay after an episode-identity change duplicate the effect. The spine states a target behaviour and leaves both the owner and the scope open.

**Proposed AD (tighten AD-10).**
> The Core derives every idempotency key deterministically from `(tenant, episode, step intent, contract-declared key fields)` and passes it to the adapter. Adapters never mint, extend, truncate or re-derive keys; an adapter whose vendor cannot accept the key must emulate de-duplication against it at the boundary and declare that it does so in the contract. Key derivation is a pinned, versioned function; changing it is a contract version bump.

---

## 14. Who creates an episode, and who maps a conversation to one? `[MEDIUM]`

**Units:** the channel adapter, versus the Core — and a second channel adapter at business two.

**The two compliant choices.** AD-16 says "the Agent and Core never learn which channel an episode is on"; AD-13 gives the Core episode lifecycle; conventions require "one episode identity scheme."

- Adapter author: the adapter must own the `channel_thread → episode` mapping, since only it knows channel threading, and it calls the Core with an episode id — creating one when the thread is new.
- Core author: the normalised turn carries an opaque `conversation_key` (channel-agnostic, so AD-16 holds) and the Core performs lookup-or-create.

**Consequence.** Under the first, episode creation — part of the lifecycle AD-13 assigns to the Core, and the moment AD-11 pins versions — happens in an adapter, so adapter two invents a second identity scheme and a second creation path with different pinning behaviour, breaking the "one episode identity scheme" convention in practice rather than on paper. It also makes episode-close semantics channel-dependent: what reopens a thread becomes the adapter's decision.

**Proposed AD (tighten AD-13 / AD-16).**
> Episodes are created, identified, pinned and closed only by the Core. A normalised inbound turn carries an opaque, channel-agnostic conversation key plus a stable message identifier; the Core performs lookup-or-create and owns the rule by which a key maps to a new or existing episode. No adapter mints episode identities, creates episodes, or decides when one ends.

---

## 15. Guard pre-empt has no defined outcome shape or author `[MEDIUM]`

**Units:** the Core's guard mechanism, versus the channel adapter and the resolution validator.

**The two compliant choices.** "Guard checks run before the Agent turn and may pre-empt it… Neither mechanism chooses the Agent's next step." The guard *mechanism* is platform-owned; the *conditions* are business-configurable.

- Guard author: a pre-empt emits a specification-authored message and closes the episode — no Agent turn, no agent-claimed resolution.
- Validator/adapter author: every episode close carries a validated resolution (AD-6), and every reply follows an Agent turn, so a pre-empt must surface as an escalation the Agent handles.

**Consequence.** Under the first, an episode reaches `closed` with no resolution, and the resolution validator — built to AD-6 — either crashes or records a null outcome that evaluation silently scores. The adapter receives a reply with no corresponding turn and may have no path for it (compounding finding 2). There is also a live AD-1 question nobody will notice: a business-configured guard that selects a business-authored message *is* the Core choosing a business-specific response, which is tolerable only if the outcome set is closed and Core-owned rather than a growing table of conditions and replies.

**Proposed AD (tighten the guard clause).**
> Guard evaluation returns one of a closed, Core-owned outcome set: `allow`, `block` (delivering a specification-provided message verbatim, with no selection logic beyond the matched condition), or `escalate`. A blocked or escalated episode still produces a resolution, authored by the Core and marked as non-agent, so that every closed episode has exactly one resolution of one shape. Channel adapters cannot distinguish a guard-produced reply from an Agent-produced one. Extending the outcome set is platform evolution under AD-15, never business configuration.

---

## What held up under attack

Stated honestly, so the findings above are not mistaken for a verdict on the direction:

- **AD-1** is unusually well defended: the "does this constrain or decide?" test is operational, and I could not construct a compliant pair that smuggled in a business state machine. The pressure on it shows up only indirectly, in findings 10 and 15, where an underspecified *shape* invites per-business Core logic as the path of least resistance.
- **AD-9 / AD-14** hold. The one leak I found (finding 9, vendor parsing migrating into evaluation) is a gap in AD-9's *binds* list, not a flaw in its rule.
- **AD-3** holds and is correctly scoped.
- **AD-7's** honesty about the semantic tier is the strongest paragraph in the document; finding 3 attacks the structural tier's mechanism, not its claim.
- **Terseness is not a finding.** Every item above is a shared data shape, an ownership of mutation, or an ordering rule — the class of thing a spine exists to fix — not structural detail properly left to code.

## Suggested disposition

Four of these are cheap to close and change the shape of everything built on top: tenancy in identity (1), the outbound delivery port (2), citation handles (3), and action-request coverage including reads (4). Compilation ownership (5) and single-writer episodes (6) are next. Findings 7–15 are each one or two sentences of AD text. None requires reopening settled direction, and none argues for more mechanism than the paradigm already implies.
