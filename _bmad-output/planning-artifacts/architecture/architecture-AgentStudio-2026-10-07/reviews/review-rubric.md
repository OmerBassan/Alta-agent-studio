# Rubric Review — ARCHITECTURE-SPINE.md (Agent Studio)

**Reviewed:** `_bmad-output/planning-artifacts/architecture/architecture-AgentStudio-2026-10-07/ARCHITECTURE-SPINE.md`
**Context read:** `briefs/brief-AgentStudio-2026-10-07/brief.md`
**Scope:** the spine document only. No repository code, diff or working tree was reviewed; `boilerplate/` and `builder_platform/` are treated as the legacy reference implementation the spine itself names, nothing more.
**Date:** 2026-10-08

---

## Verdict

**SOUND WITH GAPS** — the agent/Core axis is unusually disciplined and enforceable, but two of the brief's central primitives (goals, obligations) and the entire operational/environmental envelope are silent, and the Deterministic/Delegated split contradicts itself on guards; epics should not be cut until the CRITICAL findings land.

---

## CRITICAL

### C1 — The brief's two central primitives, **goals** and **obligations**, appear nowhere in the spine

**Where:** no AD; absent from both the *Platform-Owned vs Business-Configurable* and *Deterministic vs Delegated* tables.

The brief makes these load-bearing and bounded: "goals come **only** from the business's declared set; the agent may not invent a goal; one goal is active at a time, with parking and resumption both explicit", and names obligation the product's discriminator — "This agent knows what must be true before a request can resolve, and will not resolve it until those obligations are met or explicitly waived."

Both are constraints that *must hold*, so by AD-3 ("Any constraint that must hold is enforced by the Core") they are Core-enforced — yet the spine never says so, never names who tracks goal-set membership, who tracks obligation completeness, or where parking/resumption state lives. The success criteria the brief wants computed per episode ("obligations complete before any action") have no owner here.

**Why it matters:** this is the top divergence point for the level below. One epic will implement obligations as declarative spec predicates checked by the Core; another will put "ask for what's missing" in the prompt and call it done — and AD-3 makes the second a safety defect that the spine failed to forbid. Likewise goal invention: with no AD, nothing stops an epic letting the model name a new goal.

**Fix:** add two ADs. *AD-G: Goal identity is declared, never inferred into existence* — Rule: the active goal is a Core-held episode field whose value must be a member of the specification's declared goal set; a model-proposed goal outside the set is refused like an unauthorized action, and one goal is active at a time with parking recorded as a durable step. *AD-O: Obligation completeness is a Core gate, not a prompt instruction* — Rule: each declared outcome/action names its obligations; the Core refuses an action or a resolution whose obligations are unmet unless a declared waiver authority is exercised and recorded. Then add "active goal / goal-set membership" and "obligation completeness" to the Deterministic column.

### C2 — "Guard checks before a turn" is listed as **Deterministic**, but the brief's own guard families cannot be evaluated deterministically

**Where:** *Deterministic vs Delegated* — "Guard checks before a turn"; *Runtime Interaction* prose — "Guard checks run before the Agent turn and may pre-empt it."

The brief's candidate guard families are "**urgency**, **authorisation failure**, **policy violation**, **unsupported request**, **identity problem**", and it names "A dental practice's urgency triggers" as the canonical instance. Detecting urgency, an unsupported request, or a policy violation in free inbound text requires understanding the text. A deterministic check running *before* any model turn can do authorisation failure and identity problem (structural state), and nothing more.

**Why it matters:** this is a straight-out contradiction, and it is in the safety-critical mechanism. Independently built units will resolve it opposite ways — one builds keyword/regex urgency triggers (which will miss, and the spine will have blessed it as "deterministic"), another inserts a classifier model call before every turn (which silently adds a model call to the reply path and which AD-1 arguably makes a Core decision).

**Fix:** split the guard mechanism in the spine. Deterministic column: "structural guard evaluation (state-, authority- and identity-derived predicates)". Add a named mechanism for semantic guards — a Core-invoked classification step at the runtime boundary whose *output* is a structured guard verdict the Core acts on deterministically — and state explicitly that its result, not its reasoning, is binding. Say in AD form that a guard may pre-empt a turn but may never select the agent's next business step, since the current prose assertion ("Neither mechanism chooses the Agent's next step") is asserted rather than constrained.

### C3 — The **resolution record shape** is deferred, while the Core is required to validate resolutions against it

**Where:** *Deferred* — "Resolution enumeration and outcome taxonomy"; against *Deterministic* — "Resolution validation against evidence" and the sequence diagram's `C->>C: validate resolution against evidence`.

The brief already settled the shape and deferred only the enum: "The shape is settled — every resolution carries *whether the goal was served*, *under what authority*, and *on what evidence* — and the enumeration is an architecture decision". The spine deferred both together.

**Why it matters:** a deferral that leaves a shared contract undefined (rubric item 3). The resolution record is the contract between the Agent's close, the Core's validator, the evidence schema and every per-business evaluation criterion — four units, four inventions, no comparability across the four generalisation businesses, which is the project's actual test.

**Fix:** move the *shape* out of Deferred into an invariant: "Every resolution record carries goal reference, served/not-served, the authority exercised, and evidence references resolvable to Core execution records; the family enumeration is deferred." Leave only the enum deferred, with the reason as written.

### C4 — The operational/environmental envelope is almost entirely SILENT

**Where:** no AD, no Deferred row, no open question. Only `Store | PostgreSQL` in *Stack* touches it.

Nothing in the spine decides, defers or even names: deployment and environment model; **per-business isolation/tenancy** (the generalisation test runs four businesses — shared instance with a tenant key, schema-per-business, or deployment-per-business?); **how a specification version becomes live** (promotion, rollback, and whether validation/self-test is a hard gate — the brief says "validation and self-test → deployable instance" and "Behaviour changes are reviewed and promoted, never silently mutated"); **credential/secret handling for per-business extension adapters**; **data retention, PII and deletion** of durable episode evidence; operational posture (alerting, on-call, what a failed episode does); cost/latency envelope.

**Why it matters:** two of these are shared contracts whose absence guarantees divergence. (a) Tenancy: AD-11 pins a specification version into an episode and AD-13 fixes episode identity — but if tenancy is undecided, episode identity scope is undecided, and the "one episode identity scheme" convention is unimplementable. (b) Retention: the system durably records full customer conversations for, among the brief's own examples, a **dental practice** discussing a root canal — health-adjacent personal data. With no retention or deletion invariant, each epic chooses, and the choice is effectively irreversible once evidence is accumulating. (c) Promotion: with no gate AD, an unvalidated specification reaching a live episode is not forbidden anywhere, which undercuts AD-4 and AD-5 both.

**Fix:** add three short ADs and two Deferred rows. *AD-E1: A specification version reaches a live episode only through a passing validation gate* — Rule: deploy is a promotion of an immutable, validated specification version; the previous version remains resolvable so AD-11 episodes can finish under it; rollback is promotion of an earlier version, never mutation. *AD-E2: One business is one isolation boundary* — Rule: every Core-persisted row (episode, evidence, step, knowledge pin) carries the business identity and no query may cross it; whether isolation is row-, schema- or deployment-level is a seed choice, the boundary is not. *AD-E3: Episode evidence has a declared retention and deletion path* — Rule: the evidence schema distinguishes transcript/personal content from structural evidence, every episode's content is deletable without destroying the structural record evaluation depends on, and retention is a business-configurable period with a platform-owned maximum. Then defer, explicitly: environment topology and hosting; operational alerting.

---

## HIGH

### H1 — AD-7 enforces a check over a contract the spine leaves undefined, and gives the check no failure path

**Where:** AD-7 — "a citation whose span does not resolve is rejected. That resolution check is enforced"; *Deferred* — "Retrieval architecture ... hybrid versus dense versus deterministic lookup is not an invariant".

Deferring retrieval is right. But "span" is a shared addressing contract between the knowledge adapter that emits citations, the Agent that carries them, and the Core validator that resolves them. Nothing fixes what a span *is* (byte range? chunk id? document+locator?) or that it must remain resolvable against the pinned version.

Worse, the Rule says a bad citation is "rejected" and stops. Rejected how — the reply is blocked, the Agent re-asked, the episode escalated? If re-asked, there is no termination bound, in a product whose brief treats conversational failure modes as first-order.

**Fix:** keep the retrieval deferral; add the contract and the fallback to AD-7: "A citation is `(source id, pinned version, locator)` where the locator resolves deterministically against that pinned version. A non-resolving citation is rejected; the Core retries the claim at most once and otherwise withholds the claim and escalates under the generic guardrail set. Locator representation is a seed choice; its resolvability is the invariant."

### H2 — Rules, predicates and authorities fall in **neither** column of Platform-Owned vs Business-Configurable

**Where:** the split table; and the brief's open question it was meant to answer — "How are authority, evidence, state, tools and evaluation represented? Determines whether rules are declarative data or executable leaves".

The table has "Authorization enforcement | Authority boundaries, confirmation requirements" and "Guard mechanism | Which guard conditions apply" — but a business's eligibility/pricing/timing rules are, per the brief, "Declared predicates over collected information and **live external reads**". A predicate that performs a live external read is not plain configuration and not obviously an extension. The spine never says which, and "Rules" never appears in either column.

**Why it matters:** rubric item 7 directly — a builder genuinely cannot tell which side this falls on. The three-level variation contract in the brief (configuration / extension point / custom) is referenced nowhere in the spine, so the mechanism that was supposed to be decided here is still a policy.

**Fix:** add a row: "Rule/predicate evaluation engine and the predicate vocabulary (platform-owned) | Which predicates a business declares, and their parameters (business-configurable)", and one AD line: a predicate needing a live external read expresses it as a declared read capability executed by the Core (so AD-8/AD-2 apply), never as inline vendor access — which also closes the gap where a business predicate could otherwise become the one piece of business-authored control flow the brief forbids ("Custom code may be a leaf. It may never be control flow").

### H3 — `pending` episodes have no defined resumption trigger, and the obvious one is out of scope

**Where:** AD-13 — "one lifecycle (`active` / `pending` awaiting a named external input / `closed`)"; AD-16 — "The Agent and Core never learn which channel an episode is on"; brief *Out* — "Outbound conversation of any kind".

The brief's own pending examples are time-driven: "a brewery hold **approaching expiry**", "a gym freeze awaiting a medical note", and pending carries "a deadline". Something must notice the deadline and do something, and the product is inbound-only with no outbound. The spine never names what wakes a pending episode, nor what happens when its deadline passes.

**Why it matters:** an undefined shared contract between the durability layer, the lifecycle owner and the channel adapter. One epic builds a scheduler that messages the customer (violating the outbound exclusion); another silently lets pending episodes rot.

**Fix:** state it in AD-13: a pending episode is resumed by a named external input arriving, or by its deadline elapsing, which is a journaled Core-side timer step producing exactly one of: escalate to a human, or close with a declared lapsed resolution. Never customer-facing outbound.

### H4 — The explicit-confirmation requirement is promised but unenforced and absent from the runtime path

**Where:** *Business-Configurable* — "Authority boundaries, **confirmation requirements**"; AD-2's Rule covers only "validates it against the action's contract and the specification's authorities"; the sequence diagram goes `validate contract · authorize against specification` straight to `execute via adapter`.

The brief's contracted-action primitive is "Propose, validate against contract, **confirm**, execute, obtain evidence of success", and "which require explicit confirmation" is a declared per-business property.

**Why it matters:** confirmation is the user-facing safety interlock before a state change, and as written it survives only as a prompt instruction — which AD-3 says may never be an enforcement path. The contradiction is between two sections of the same spine.

**Fix:** extend AD-2's Rule: "An action contract whose specification entry requires confirmation is not executable until the Core holds a recorded confirmation step for that specific action instance (same idempotency key, same parameters); a re-proposal with changed parameters voids it." Add the confirmation branch to the sequence diagram.

### H5 — "Inline resolution validation" is simultaneously a Core invariant and an unvalidated deferral

**Where:** *Deferred* — "Inline resolution validation as a shipped mechanism ... is to be validated by the proof gate before being relied upon"; versus *Deterministic (Core)* — "Resolution validation against evidence", AD-6's "A resolution asserting an effect without a corresponding Core execution record is invalid", and the sequence diagram step.

**Why it matters:** the level below cannot tell whether to build it. An epic reading the ADs builds it as a hard gate; an epic reading Deferred builds offline assertions only. AD-6 is the product's integrity claim, so this one must not be ambiguous.

**Fix:** separate the two things. AD-6's *invalidity* claim is an invariant and stays. What is genuinely unproven is the *enforcement posture* — whether an invalid resolution blocks episode close or is recorded and escalated. Reword the Deferred row to that one question, with a named default until the proof gate rules: record, refuse the claim, escalate.

---

## MEDIUM

### M1 — AD-1's prohibition list collides with obligations and preconditions

**Where:** AD-1 — "no precondition-derived orchestration standing in for agent decision-making", against the brief's "Obligation tracking | What must be established before a given outcome or action is permitted" and "Allowed action | ... their **preconditions**".

Obligations *are* preconditions. AD-1 as phrased reads as forbidding exactly the mechanism C1 asks for. The distinction the spine means is presumably gating (refusing an action whose obligations are unmet) versus sequencing (deriving the next step from unmet preconditions) — but it never draws it, and the whole AD then rests on a human applying "apply the test" by judgment.

**Fix:** add one sentence: "Preconditions may *refuse* an action and may be *reported* to the Agent as unmet; they may never be used to select which action or question comes next. Gating is Core; sequencing is Agent."

### M2 — The second mermaid diagram contradicts its own caption and is near-trivial

**Where:**

```
    CORE --> SPECM["Specification model"]
    CORE --> KN["Knowledge"]
```

under the caption *"Dependency direction: inward only."*

Every other edge in that graph is a dependency pointing inward at the Core; these two are dependencies pointing *outward* from the Core, which is precisely what AD-9's "the Core depends on nothing outside itself" forbids. Either Specification and Knowledge are *inside* the Core's dependency closure (then draw them inside, not as targets), or the Core reaches them through ports (then the adapter is the node and the arrow reverses). As drawn the diagram teaches the wrong rule, and otherwise adds nothing the AD-9 prose doesn't already say — six nodes, five arrows, no information of its own. Note also that diagram 1 uses data-flow/"produces" semantics while diagram 2 uses dependency semantics, with nothing labelling the difference.

**Fix:** redraw as Core at the centre with a port ring — `Channel adapter -> Inbound port -> Core`, `Core -> Retrieval port -> Knowledge adapter`, `Core -> Action port -> Extension adapter`, `Core -> Runtime boundary -> Provider` — so the diagram carries the *port inventory*, which is information the prose does not list anywhere. Label diagram 1 "data flow" and diagram 2 "dependency direction".

### M3 — The sequence diagram omits three paths the prose or the brief requires

**Where:** the `sequenceDiagram` block. It shows no guard **pre-emption** path (though the prose says guards "may pre-empt" the turn), no **escalation to a human**, and no **close into `pending`** — and it shows a single action request where the brief's episodes are multi-turn and multi-action (no loop frame, hence no visible termination bound).

**Fix:** add a `loop` frame around the turn with its bound stated, an `alt guard pre-empts` branch returning straight to the channel, an escalation arrow to a human-handoff participant, and `pending` as an alternative close.

### M4 — Escalation has no port

**Where:** *Business-Configurable* — "Escalation conditions"; *Delegated* — "Whether to act, continue, respond or escalate"; the generic guardrail set — "escalate when required authority or evidence is unavailable".

Escalation is an effect on an external system (a human's inbox, a queue, a dashboard), so by AD-2 it must be an authorized Core-executed action through an adapter — but the Extensions layer is described as "Tools, APIs, external systems, external knowledge" and no AD names a handoff port. The channel adapter is the customer's channel, not the operator's.

**Fix:** name the operator/handoff port as a first-class port in the Design Paradigm table and state that escalation is an action contract like any other, with evidence (so AD-6 covers "a human was actually notified").

### M5 — Untrusted content is never named, and retrieved business documents are an injection surface

**Where:** nothing in the spine; AD-3 covers only the model's *compliance* with instructions, not adversarial *content*.

Inbound customer text and retrieved business material both enter the model's context. AD-2 and AD-10 structurally blunt the damage (no effect without authorization, idempotency), which is genuinely the right primary defence and worth crediting — but with no AD naming the surface, units will diverge on whether retrieved spans are delimited/marked, and a business's own uploaded PDF becomes an unexamined instruction channel.

**Fix:** one AD: all content entering model context — inbound turns, retrieved spans, tool results — is marked as data at the runtime boundary and may never carry authority; authority derives only from the compiled specification projection. Note that AD-2 remains the enforcement, not the marking.

### M6 — `Store | PostgreSQL` is the one hard technology pin, and the altitude doesn't support it

**Where:** *Stack* — "Store | PostgreSQL", alongside "Agent runtime *(candidate, behind AD-14)*" and "Durability *(shortlisted, not committed)*".

The policy engine, the durability engine and the retrieval architecture are all deferred, yet the store is pinned unqualified — and *Deferred* then presumes it anyway ("the fallback floor is Postgres tables with a unique constraint on `(episode, step, idempotency key)`"). Either the store is an invariant, in which case say which invariant demands it, or mark it seed like the rest.

**Fix:** mark it "seed" and state the invariant it serves: the evidence write and the action result must land in one transaction (AD-12), so the store must be transactional. That is the architectural fact; Postgres is the seed that satisfies it.

### M7 — Named technology is asserted verified but is not independently confirmable from this document

**Where:** *Stack* — "**Seed, verified 2026-10-08.**", with "Pydantic AI 2.x", "MCP, spec revision 2026-07-28", "OpenTelemetry GenAI conventions *(Development stability; moved repos 2026-06-12 — expect churn)*".

The OTel row is exemplary — it names the stability tier and a dated caveat, which is exactly what a seed pin should carry. The other two carry no evidence of the verification and I cannot confirm either: a Pydantic AI major-version `2.x` and an MCP revision dated `2026-07-28` both postdate what I can verify independently. Given the project's own evidence standard, a bare "verified" is weaker than the OTel row it sits beside.

**Fix:** carry the OTel row's discipline across — for each pinned name, a release date or a link, and for Pydantic AI the one line that matters at this altitude: which AD-14 obligation it was checked against (structured output, tool-loop control, provider swap, model tiering). If `2.x` cannot be re-confirmed, write `1.x+` and let the code own it.

---

## LOW

### L1 — AD-5 names an error signal with no consumer

"the episode evidence records it as a specification defect ... The divergence log is the specification's error signal and requires no human transcript review." Enforceable as a write; but nothing says who reads the log, on what cadence, or what a non-zero divergence rate blocks. A signal with no consumer decays. Consider one clause: divergence rate is a named metric on the per-business evaluation surface, and a new specification version's promotion gate reports it.

### L2 — Two Rules use unmeasurable verbs

AD-14: "Model tiering across capability classes **must be expressible** at this boundary" — expressibility is not checkable. AD-15: "Business configuration never changes **Core semantics**" — "semantics" is undefined, so the line cannot be drawn by a builder. Fix AD-14 to a concrete obligation: the boundary accepts a per-capability-class model selection as configuration, with no Core or Agent code change. Fix AD-15 by defining the mechanical test: business configuration is data validated against a platform-owned schema; anything requiring new code is an extension or platform work.

### L3 — "what it will not say" has no home

The brief gives each business "Identity — what the business is, how it speaks, **what it will not say**". In the spine this lands in business-configurable "Identity, context, terminology, communication preferences" — i.e. prompt text, which AD-3 declares advisory. If a prohibition must hold, it needs to be a guard or an output check, not persona copy. State which, or say explicitly that prohibitions are advisory-only in V1 and accept that.

### L4 — AD-13 forbids cross-episode memory but the returning-customer case is unaddressed

"Cross-episode memory and profiling are out of scope" is correct and matches the brief. But a returning customer resuming a pending episode requires *finding* their episode, which is a lookup by a person-identifying key — adjacent enough to profiling that units will be unsure. One clause distinguishing "episode lookup by join key" (allowed) from "persisted person profile across episodes" (out of scope) removes the doubt.

### L5 — The Builder's own surface is thin for a layer the paradigm table owns

`builder/` owns "Conversation and sources → specification + knowledge artifacts → validation → deploy", and the brief says "The builder's hard problem is elicitation, not generation" with gaps "recorded as specification defects rather than guessed". No AD constrains the Builder beyond AD-4's compile-once rule. The one invariant worth fixing at this altitude: the Builder may never author a specification value it did not obtain from the business or from a declared default — an unknown is recorded as a specification gap, never inferred. That is the same error-signal discipline as AD-5 and it belongs beside it.

---

## What the spine gets right

- AD-2, AD-4, AD-6, AD-11 and AD-12 are genuinely enforceable, each prevents what it claims, and together they close the integrity loop — no effect without authorization, no divergence between what the Agent sees and what policy allows, no evidence the Agent can author, no episode judged under shifted rules, no un-journaled read.
- AD-7 is the most honest line in the document: "Semantic faithfulness beyond structural citation resolution is **evaluated against a threshold, not guaranteed** — no architecture may claim otherwise." That distinction between enforced and evaluated is what most grounding architectures elide.
- The *Durability engine selection* deferral is the model all deferrals should follow — semantics fixed, technology open, and a named fallback floor. C3, H1 and H2 are asking the other deferrals to meet that bar.
- The Litmus test and the Proof Gate give the whole document a falsification condition, which is rarer than it should be.
- Terseness is not a defect anywhere in this review; every finding above is a missing *decision*, contradiction or undefined shared contract, not missing implementation detail.
