---
title: "Agent Studio — Business-Specific Agent Platform"
status: final
created: 2026-10-08
updated: 2026-10-08
amended: 2026-10-16
---

# Agent Studio — Business-Specific Agent Platform

Product Requirements Document · V1

> **Scope of this document.** This PRD defines the forward-looking product: a channel-independent platform that turns a business's own context, knowledge, policies, capabilities and boundaries into a deployable business-specific Agent. It is **not** a retrospective specification of the shipped voice agent builder, which remains covered by its own `SPEC.md` and is referenced here only as implementation evidence, a source of reusable assets, and a set of brownfield constraints.
>
> **Amended after finalization (§14).** Later approved decisions supersede or narrow a few statements below. Each keeps its original wording and carries an inline *[§14 An]* marker; where a marker appears, §14 governs.
>
> Architecture is settled elsewhere. `ARCHITECTURE-SPINE.md` is authoritative and this document is subordinate to it: requirements here describe **what a business must be able to express and what the platform must guarantee**, never how the runtime is built. Where a requirement depends on a deliberately deferred architectural decision, the requirement is captured and the implementation decision is left deferred.

---

## 1. Vision

### 1.1 Centre of gravity

> **Reasoning is broad; authority is bounded.**

The Agent may think widely about any request a person brings, including situations nobody enumerated in advance. What it may **conclude**, what it may **promise**, and what it may **do** are narrow, declared, and enforced.

The control model is settled and is not re-opened by this document:

> A model-in-charge Agent decides what to do next; a deterministic Core decides what the Agent is permitted to do, executes it, and records what happened.

What makes this a primitive set rather than a framework is what it **refuses**: no reasoning unanchored to a declared goal, no decision outside an authority class, no claim without a source, no action without a contract, no episode without a terminal outcome. Each refusal appears below as a requirement; together they are the product's definition.

The business supplies a **Business Specification** — context, knowledge, policies, capabilities, authorities and boundaries. It does **not** supply a per-business sequence of steps. The platform has no business-level control flow to author, and the authoring surface must make sequencing unexpressible.

### 1.2 Three framings, kept distinct

These are routinely collapsed, which produces either an over-promising PRD or an under-ambitious one. They are held apart deliberately.

| Layer | Statement | Status |
|---|---|---|
| **Internal product thesis** | One capable Agent system, many Business Specifications. | The architecture claim — under test. |
| **North-star experience** | A small business can effectively *hire* and configure an AI worker. | Direction of travel. **Not a V1 commercial promise.** |
| **V1 objective** | Prove that a short onboarding conversation can produce an Agent that genuinely behaves like a worker for *that* business. | What this PRD scopes. |

"General-purpose" is the correct description of the architecture and a poor message to a customer. It is **not** the customer-facing differentiator and does not appear in customer-facing positioning. What is sold is the outcome; what is built is one engine driven by many specifications.

### 1.3 A superseded principle, named

Earlier work on this project adopted **“deterministic-first, LLM-on-escalation”** — do not spend a model call generating a reply you already know; do not classify every turn if the job structure already supplies direction. It was a decided principle, and it is **superseded** by the control model above rather than forgotten. It is named here because a reader of the earlier material would otherwise find it silently reversed, and because its reversal has a reason and a limit.

The reason: that principle was derived under a **voice latency budget**, where an extra round trip is dead air and dead air is a failure. V1 is asynchronous (§8.10), so the arithmetic that justified it is gone. Its corollaries fell with it — FR38 hands the model precisely the decisions the principle withheld, deliberately.

The limit, which survives intact: **cost and latency are not licences.** Harvest the structured output the system already produces rather than paying a model to restate it; keep prose synthesis off any path a person is waiting on; and hold to §4.3's third standing condition, which generalises the point past determinism. Any later synchronous channel re-imports a weaker form of the original principle, and should re-derive it from measurement rather than from this document.

### 1.4 The V1 product problem

Everything in this document serves one question:

> **Can we make the transition from "this is my business" to "this Agent behaves like someone who works here" short, reliable, and repeatable across materially different businesses?**

Three words in that sentence carry the requirements. **Short** is onboarding burden. **Reliable** is behavioural correctness under the business's real rules. **Repeatable** is the generalisation claim — that the second, third and fourth business cost materially less than the first, and that what changes between them is the specification and not the engine.

### 1.5 The narrow thesis under test

What is and is not claimed as novel is settled in §4.1 — none of the established patterns there is claimed. The claim this product actually makes, and the one V1 exists to falsify, is narrower than any of them:

> **A non-engineer can describe how their business actually operates — including the tacit rules and boundaries that exist in no document — and the platform turns that description into a business-specific Agent that behaves correctly across real conversations.**

Two halves of that sentence carry unequal risk. Turning a written description into a running Agent is engineering. Getting the description to be *true* — surfacing the thresholds, exceptions, prohibitions and the gap between printed and practised policy — is the hard part, and it is where V1 invests.

---

## 2. Who this is for

**Primary Builder user: the Business Operator.** A role archetype, deliberately not a named persona — no primary operator evidence has been obtained yet, and inventing a persona would manufacture confidence the research does not support.

The Business Operator is the owner-operator, or the person responsible for customer-facing operations. The defining characteristic is **not** company size, headcount or revenue:

> They possess the business's actual operational knowledge, including the rules that exist in no document.

**[ASSUMPTION A4]** Such a person exists, is reachable, and can articulate those rules when interviewed. The entire Builder thesis rests on it, and FR94 exists to test it.

That person is frequently also the buyer. **[ASSUMPTION A3]** The product may assume this commercially; it must **not** encode `buyer = builder` as an architectural requirement, and nothing in the authoring model may depend on it.

**Other roles in play**, each real but none yet drawn as a persona:

| Role | Relationship to the product |
|---|---|
| **Requester** | The person who brings an inbound request to the Agent. Known only by role; the platform never initiates contact with them. |
| **Specification reviewer** | Whoever reads and approves a specification before promotion. Human review stays in the loop; the competence required is an open item (§11). *[Narrowed for V1 — §14 A3]* |
| **Escalation recipient** | Where a handed-off episode lands. Destination, notification and response expectation are an open item (§11). |

**The four exemplar businesses.** They carry the generalisation test, chosen for deliberate anti-vertical diversity — *"These are not one workflow with four skins."*

| Business | The real request | What it stresses |
|---|---|---|
| Brewery | "I want to host a 40-person event next month." | Negotiated multi-constraint planning; no slots, no practitioners |
| Gym | "I want to freeze my membership for two months." | Account state mutation under policy; recurring commitments |
| Garden centre | "This plant I bought is dying. What should I do?" | Diagnostic advice; ambiguous goal; a liability boundary |
| Dental practice | "I was told I need a root canal. What happens?" | High-stakes grounding; mandatory override; explanation, not transaction |

These four demonstrate that the specification can **express** materially different businesses. They are **not** evidence that it can **drive behaviour**. That distinction is load-bearing throughout this document. **[ASSUMPTION A2]** These specifications are constructions, not any real business's rules (§13.1). Treating them as an adequate substitute is defensible for the *architecture* claim and explicitly not for the *usefulness* claim, which is why FR92 requires one real business.

---

## 3. Problem

### 3.1 Problem statement

> Small businesses answer the same requests endlessly, and the knowledge needed to answer them well already exists — in a price list, a policy, a care guide, a membership agreement, the owner's head. What does not exist is anything that can hold the conversation and act on that material.

Root cause: **a small business's rules and knowledge are not in a form anything can act on**, so every inbound request consumes human attention from scratch.

### 3.2 Why each existing option fails

Each coping strategy fails for a *different* reason, which is why none of them composes into a solution.

| Existing option | Specific failure |
|---|---|
| A person answers when they can | Misses the rest — concentrating failure after hours and at peak |
| A web form | Captures a fraction of what is needed, then begins a round of clarifying messages |
| A scripted chatbot | Deflects to a link |
| An answering service | Takes a message but cannot apply the business's rules |
| A document-retrieval chatbot | Answers questions but cannot *do* anything, so every request needing an action still reaches a person |

The discriminator against the closest of these — the retrieval chatbot — is **obligation**. This Agent knows what must be true before a request can resolve, and will not resolve it until those obligations are met or explicitly waived. A document chatbot has no obligations, no authority model, no completion condition and no outcome.

Four things it must do that a retrieval chatbot cannot:

1. **Hold an unfinished request open** — across turns and across sessions — driving toward what is missing.
2. **Refuse with a reason** drawn from the business's own rules, rather than failing to find an answer.
3. **Change something in the world** through a bounded, contracted, verified action.
4. **Close with a structured resolution** that can be evaluated, counted and audited.

### 3.3 The documentation gap

The pain that shapes the Builder, discovered rather than assumed:

> The least-documented content is the most safety-critical: prohibitions, guard conditions, escalation thresholds and the operational rules — billing cut-offs, lead times, which exceptions are routinely granted — frequently exist in no document at all.

And beneath it, the gap between each business's **printed** policy and its **practised** one. A Builder that ingests documents and stops has captured the safe part and missed the dangerous part.

### 3.4 Evidence status

Stated plainly, because it bounds what this PRD may claim. No quantified pain figure anchors the problem statement in this document, and that is a choice rather than an omission: the public record is contaminated — at least one vendor selling human staffing publishes fabricated AI-abandonment statistics, and the category's headline number is inflated by roughly a factor of two — while **no primary operator evidence has been obtained**. One partially defensible independent figure does exist in the source material, drawn from a large lead-tracking dataset; it is not load-bearing here, and it is recorded in the sources rather than promoted into a product claim.

**Outstanding research action, not an open question:** two or three conversations with real small-business operators remain the only test of the problem statement, and of the printed-versus-practised gap. Nothing in this document substitutes for them.

---

## 4. Positioning

### 4.1 What is and is not claimed as novel

Not claimed: model-in-charge agents, agent harnesses, tool calling, declarative agent configuration, business rules represented as data. Established patterns, all of them.

Claimed, narrowly: **a specification that is declarative about *the business* — what we do, who we serve, what we promise, what we never do, what we will not let an agent decide — authored in business language by a non-engineer, compiled into a bounded deployable Agent.**

### 4.2 Prior art, named

Declarative-specification-drives-autonomous-agent exists and ships today, at the enterprise tier. Recorded here so that the differentiation claim is stated at a width that survives contact with a reviewer.

| Prior art | What it is |
|---|---|
| Salesforce **Agentforce Script** | A declarative single versioned file expressing instructions, actions, rules and subagents |
| Microsoft **Foundry** | Declarative agent authoring as a first-class mode alongside a visual canvas |
| **Sierra** Agent SDK | A declarative way to define an agent's goals and guardrails |
| Oracle **Open Agent Specification** | A declarative agent definition with portability across compatible runtimes |
| Intercom **Fin Procedures** | Natural-language documents as configuration, in production, priced per outcome |
| Coding-agent convention | `CLAUDE.md` / `SKILL.md` / `AGENTS.md` — behavioural specifications read by a general-purpose agent, no control flow |

The paradigm is **validated, not owned**. Two distinctions remain, and both are narrow by design:

- Every example above is declarative about *the agent* — subagents, instructions, actions, rules — which are author-side engineering objects. This product's artifact is declarative about *the business*.
- Every example above is enterprise-priced and enterprise-shaped. Nobody in the small-business tier is selling "describe how your business works, get a bounded Agent."

**No moat is claimed.** This is a technically substantial system built against a real problem. Commercial potential is unproven, and the project is not justified by it.

### 4.3 Three standing conditions on this product

Stated as conditions rather than opinions, because each one is a veto that can reject an otherwise attractive direction.

1. **Prior art must not become an excuse for building a worse copy.** That an incumbent occupies a space is a reason to be honest, not a reason to ship a thinner version of what they already do. "Like theirs, but ours" is not an acceptable thesis.
2. **An unsaturated vertical is not the goal.** The point is that the *same underlying product* is useful across many small-business contexts. Market evidence is recorded (§4.2) and is **not permitted to steer the product toward hunting an empty niche** — that is precisely how this becomes the vertical product §4.4 says it is not.
3. **No principle is adopted for elegance.** A named technique — determinism, caching, routing, tiering — is a hypothesis about this system, not a specification. Confirm the mechanism it targets exists on the path that matters, and measure that path, before committing to it.

### 4.4 What this is not

| Not | Consequence for this PRD |
|---|---|
| **A workflow engine** | No business-level step sequences, transitions or control flow anywhere — not in the product, not in the specification, not in these requirements |
| **A template library of behaviour** | Pre-filled Business Specifications are in scope as onboarding accelerators (FR8). Template-*defined behaviour* is not *[Superseded for V1 — §14 A1]* |
| **A vertical product** | Not a booking, appointment, healthcare, sales or FAQ product. Any vertical framing is out |
| **An outbound or proactive system** | An episode is initiated or resumed only by an inbound interaction or an external system event. The platform never independently starts an outbound conversation or episode |
| **A system of record** | External business systems stay authoritative |
| **An autonomous planner** | The purpose is conversational robustness, not autonomous planning. No decomposition of goals into agent-generated plans |
| **A memory product** | No general long-term customer memory, no cross-episode profiling |
| **A self-modifying system** | Behaviour changes are reviewed and promoted, never silently mutated |

### 4.5 The reliability counter-argument, answered

The loudest evidence against this product's shape is that autonomy is precisely where small-business agent platforms accumulate reliability complaints — agents that confirm an email they never sent, reply on the wrong thread, or loop expensively. A competitor's deterministic pitch is a genuine *feature* to an operator whose business depends on not contacting the wrong customer.

This is not answered by asserting better reasoning. It is answered by the Core: the parts that must not vary — irreversible actions, anything costing money, anything reaching a customer — are constrained, authorized, verified and recorded deterministically, while the reasoning above them stays broad. The product's position is **declared intent with deterministic, validated execution on the irreversible path**, which is also where the market is converging. No credible system runs pure autonomy on business-critical actions, and this document does not claim to.

---

## 5. Falsifiable posture

V1 is a **validation phase**, not a confident build-out. Neither of the project's two claims is proven, and this document does not assume either.

| Claim | Status | What would falsify it |
|---|---|---|
| **Architecture claim** — one Agent system handles materially different small-business requests while only the business layer changes | Partially tested. A four-business specification stress test established that the specification can **express** four businesses sharing no control flow. It did **not** establish that it can drive behaviour | Engine changes do not fall toward zero across the four businesses; or setup effort does not fall materially across the sequence |
| **Usefulness claim** — the resulting Agents resolve a meaningful class of real inbound requests well enough to be useful, not merely technically impressive | Untested | A low share of real inbound requests reaching a correct resolution without a human; or a high share of requests needing only plain information, which would make a good result prove nothing |

The acceptance criterion for the whole architecture, applied as a standing self-check on every requirement in this document:

> **Can a new business be onboarded without generating a business-specific execution graph or state machine, while the Agent still reasons about situations nobody enumerated?** Yes means an agent platform. No means a workflow engine with a model attached.

---

## 6. Vocabulary of record

Terms are used as the Architecture Spine defines them, and this document uses no others for these concepts.

| Term | Meaning as used here |
|---|---|
| **Agent** | Understanding, reasoning, deciding the next step, adapting to unenumerated situations |
| **Core** | Validate · authorize · execute · observe · persist. Deterministic. Never selects the Agent's next step |
| **Business Specification** | The business's declared context, policies, authorities, capability grants and outcome expectations. One artifact |
| **Business Knowledge** | Version-pinned authoritative business material, and retrieval over it |
| **Builder** | Conversation and sources → specification and knowledge artifacts → validation → promotion |
| **Episode** | One unit of interaction. One identity, one tenant, one lifecycle, one evidence record, and one join key where it touches an external system of record |
| **Requester** | The person who brings an inbound request to the Agent. Known only by role; the platform never initiates contact with them |
| **Request kind** | One of the closed set the Agent may emit: `retrieve`, `read`, `effect`, `clarify`, `respond`, `escalate`, `suspend`. Every kind is authorized and journaled, reads included. The set carries no precedence and no order, and no business may add to it (FR40) |
| **Safety halt** | One of the Core's exactly two exits: the episode terminates with a recorded outcome, rather than control returning to the Agent (FR45) |
| **Capability** | A verb-first declared action with a contract: input schema, effects, authority required, confirmation requirement, success evidence, idempotency scope |
| **Goal / obligation** | What an episode is for, and what must be established before it can resolve. Both are **typed Core state**, readable by the Agent and asserted by the Core at resolution — never only prompt text. Holding them is not deciding with them (FR105) |
| **Resolution** | The structured outcome at close: which goal, whether served, under which authority, on what evidence, plus a business-defined payload |
| **Evidence** | Typed records authored only by the Core. The Agent cannot author evidence |
| **Provenance reference** | A Core-issued reference binding a context item to a tenant, source, source version and locator. The Agent can neither mint nor alter one |
| **Escalation** | The Agent's decision to hand off, under conditions the business declares. One of the request kinds |
| **Guard condition** | A declared condition evaluated before the Agent's turn, whose verdict binds deterministically with exactly two outcomes: a typed constraint returned to the Agent, or a declared safety halt. A guard never composes a reply and never chooses the Agent's next step (FR44) |
| **Promotion** | Publishing an immutable specification version, gated on its validation suite passing |
| **Extension** | An external system or capability reached only as Core contract → adapter → extension |

**Forbidden vocabulary**, because each one smuggles the rejected model back in: *workflow, state machine, business transition graph, workflow language, execution graph, stage, node*. Where this document must refer to them, it does so only to exclude them.

---

## 7. V1 scope

### 7.1 In scope

| # | In V1 | Note |
|---|---|---|
| S1 | The reusable behavioural Core, complete | Request taxonomy, guard conditions, decision authority classes, obligations, contracted capabilities with verification, generic guardrail library |
| S2 | The Business Specification model | One artifact. Human-readable, diffable, versioned, with version-pinned knowledge |
| S3 | The Builder, with **deep elicitation** | Minimal burden and UI for the operator; *not* minimal reasoning by the Builder. See §8.1 |
| S4 | Episode lifecycle with pending and resumable episodes | Separated from resolution and from action evidence |
| S5 | Bounded multi-goal episodes | Explicit parking and resumption |
| S6 | Grounded retrieval with the two knowledge tiers enforced and recorded | Business-authoritative versus general domain knowledge |
| S7 | Durable structured episode evidence with stable episode identity | Product data, not operational logs |
| S8 | Invariant evaluation checks plus per-business criteria | |
| S9 | **One channel adapter: inbound email / messaging** | Behaviour written channel-neutrally. See §8.10 |
| S10 | **Operator surface: classified divergence list + single-episode viewer** | The improvement loop, and nothing more. See §8.9 |
| S11 | **The four-business generalisation programme, with all three measurements recorded** | V1 is not complete until these exist. See §8.11 |

### 7.2 Out of scope

| Out | Why it is out |
|---|---|
| Everything §4.4 excludes as product identity — vertical framing, platform-initiated outbound, owning a system of record, agent-generated planning, long-term memory and cross-episode profiling, continuous automatic learning | Out permanently rather than out of V1. §4.4 is canonical; this table lists only what is out of **V1** |
| Voice | A separate, already-proven project. Channel is an adapter |
| Multi-tenant hosting, billing, onboarding automation, commercial packaging | Tenant *identity* on every record is in scope (§9); tenant *hosting and commerce* are not |
| Domain-specific regulatory packs | The extension point exists; the packs do not |
| Metrics dashboard, escalation **inbox**, in-product specification **editor** | Out of the V1 operator surface by decision. Note the two narrow things that *are* in: an escalated episode is **delivered** to a declared destination (FR103), and a specification is **revised through the Builder conversation** rather than an editor (FR101). Neither is a console surface |
| Integration catalog or extension marketplace | The adapter contract is the forward-compatible seam; distribution is later product work |

### 7.3 Deferred, not excluded

Captured as requirements with their implementation left open, per the Architecture Spine's deliberate deferrals: the resolution-kind enumeration; the policy engine; the durability engine; model routing and tiering; retrieval architecture; long-term memory semantics; tenancy deployment topology; extension distribution; the concrete specification field schema; context assembly; retention policy and its executor; and inline resolution validation as a shipped mechanism.

Where a requirement below depends on one of these, the requirement states the guarantee and names no mechanism.

### 7.4 Relationship to the shipped voice system

The existing voice agent builder is **the reference implementation and migration source, not the foundation**. It is neither preserved because it exists nor replaced to avoid it. Three things carry forward, and one explicitly does not.

| Posture | What it covers |
|---|---|
| **Reusable largely as-is** | The shared deterministic core that owns paths and write policy; the ship-gate-as-subprocess mechanism; single-ingress credential bootstrap; the provider-agnostic LLM contract with a credential-free mock mode; deterministic context compaction; the post-execution validator *concept*; bounded tool budgets; the human-authorization interrupt; off-thread tool execution (FR97); the structured-verdict-then-deterministic-text pattern; the validated integrations catalog; one-core-many-front-doors. One of these is bounded: the structured-verdict-then-deterministic-text pattern may render a Core-owned notice such as the terminal notice of FR111, and may never become a guard that composes the Agent's reply (FR44) |
| **Concept transfers, code does not** | Typed state discipline with a writer, reader and lifecycle per field; typed argument collection with resolvers before execution; the slim-core-plus-phase-files skill technique; the write-policy enforcement paradigm; the zero-model structured record harvested from work already done |
| **Not reusable** | Everything shaped by voice transport and telephony: the vendor adapter and control plane, dead-air filler, the pre-speech sanitizer, the twenty-word spoken-string contract, phone-sales micro-tactics, the tunnel dependency, and the phone-craft reference material |
| **Deliberately not carried forward** | The fixed fifteen-node pipeline. The code is good and the shape is wrong: it is a hand-rolled agent loop with the agency removed, where the Core decides the next step. What that system actually earned is an **inventory of Core guarantees** — a bounded tool budget, a deterministic post-execution validator, a typed tool-result contract, a human-authorization interrupt, a stall detector with a wired handoff, a degraded path distinguishable from success, an output check before anything reaches a person, and durable-state discipline. Each becomes a Core service, none becomes a step. Two items in that inventory — the bounded tool budget and the stall detector with a wired handoff — are now **required** rather than merely available (FR107) |

Two inherited constraints are load-bearing for V1. **Process-level isolation between deployed Agents is permanent**, not a deployment preference — generated artifacts collide on module identity, so isolation belongs at the process or container boundary from day one. And the shipped system's **absence of instrumentation** is a gap this product does not inherit: no timing exists on any model call there, and every latency and cost claim in it is reasoned rather than measured. Measurement — latency, tokens, cost, and one correlation identity per episode — is a day-one Core capability here (NFR13, NFR14, NFR16), which is also why §10 can mandate instrumentation while setting no thresholds.

One further inherited caution bears directly on FR43: **a stronger model increases fidelity to what the prompts say, never to what is true.** Escalating a model tier to fix behaviour that was never declared anywhere is a category error, and no requirement in this document may be satisfied that way.

### 7.5 The proof gate

Before the full runtime is committed to this architecture, **one realistic business interaction is implemented end to end** and compared against the existing fifteen-node system on nine axes: architectural simplicity, amount of custom code, number of model calls, latency, control and observability, failure handling, extensibility to a second business, and ease of enforcing business boundaries.

This is a decision point, not an epic. It sits in front of E4–E9 and it is the only place where the comparison against the shipped system is made deliberately rather than by assertion. Two consequences for this document:

- The proof gate can **fail**. If the hexagonal harness is worse than the system it replaces on the axes that matter, that is a finding, and §5 already commits to treating the architecture claim as under test rather than settled.
- Inline resolution validation is **provisional until this gate**. Requirements in this document state outcome guarantees (FR71) and deliberately avoid asserting *when* they are enforced, because enforcing assertion-based evaluation synchronously at episode close is this project's own extension rather than established practice.

---

## 8. Features and functional requirements

Requirement IDs are globally numbered and stable. Each describes an outcome or a constraint. **None describes a sequence** — the standing self-check from §5 applies to every one of them.

### 8.1 Builder — conversational elicitation

The hard problem is **elicitation, not generation**. Generating configuration from a description is engineering; discovering how the business actually operates is the product risk. "Minimal Builder" means minimal burden and interface complexity *for the operator*, never minimal reasoning *by the Builder*.

| ID | Requirement |
|---|---|
| **FR1** | The Builder opens with an open invitation — in substance, *"Tell me about your business and what you want the Agent to handle"* — and never with a form or a fixed question set. |
| **FR2** | The Builder accepts the business's own material in the formats the operator already has: price lists, terms, policies, care guides, fee guides, published FAQs, prior customer correspondence. *[Specified for V1 — §14 A4]* |
| **FR3** | The Builder decides adaptively what needs clarification, from what the operator says and what the material contains. It MUST NOT present a fixed questionnaire, and the number of questions asked is a function of what is missing, not of a template. |
| **FR4** | The Builder MUST actively interview the operator for the safety-critical content that characteristically exists in no document: prohibitions, thresholds, exceptions, authority limits, which exceptions are routinely granted, what must always be escalated, and what must be established before a decision may be made. |
| **FR5** | The Builder MUST surface contradictions — between two sources, and between a source and what the operator says — rather than silently selecting one. |
| **FR6** | Where business behaviour is unknown or ambiguous and the operator cannot resolve it, the Builder MUST record a specification defect. It MUST NOT invent a default. **Never improvise a rule.** |
| **FR117** | Builder-side failures are **distinguishable outcomes, never silent ones**, on the same rule as FR46: a source that cannot be read, a session abandoned part-way, and a newly supplied source that contradicts an already-promoted specification each produce a stated outcome the operator can see. A half-elicited specification is never presented as a complete one. |
| **FR7** | The Builder MUST probe explicitly for the gap between printed policy and practised policy, because that gap is the likeliest place a specification is wrong. |
| **FR8** | The Builder MAY offer optional pre-filled Business Specification starting points (for example "dental practice", "gym") that seed terminology, candidate requests, questions worth asking and policies worth considering. Such a starting point: MUST be optional; MUST be fully editable; MUST contain no behavioural sequence of any kind; and MUST NOT be the source of agent behaviour. It is a specification starting point, never a behaviour template. *[Superseded for V1 — §14 A1: not offered in V1]* |
| **FR9** | The Builder produces both the Business Specification and the Business Knowledge artifacts. |
| **FR10** | The Builder is itself agent-driven. The platform's Agent nature is visible on the Builder side, not only at runtime. |
| **FR11** | Human review is a **blocking precondition of promotion**, alongside the validation suite: a specification cannot be promoted without a recorded approval, attributable to a named approver, retained as evidence under FR28. Who may approve, and what competence that requires, is deferred (O1) *[Narrowed for V1 — §14 A3]* — but *whether* approval is enforced and recorded is a product decision, and it is yes. |
| **FR12** | The Builder instruments its own burden: wall-clock time to a passing validation suite, and the number of source artifacts required. Both are recorded per business. |
| **FR99** | The Builder instruments its own **yield**, not only its burden: how much business behaviour was recovered that the supplied material did not contain — the prohibitions, thresholds, exceptions, authority limits and always-escalate cases obtained by interview (FR4), the contradictions surfaced (FR5), and the specification defects recorded rather than guessed (FR6). **Burden and yield are reported together and neither is read alone.** Burden measured by itself rewards a Builder that asks less, which is the opposite of the product. |
| **FR104** | When an operator narrates a **process** — and they will, because that is how people describe their own work — the Builder MUST re-derive it into declared context, policy, capability, authority, goal and obligation, and **persist no ordering**. The operator may say "first we check the diary, then we take a deposit"; what is recorded is that a deposit is an obligation of a booking goal and that checking availability is a granted capability. Rejection at the validation gate (FR24) is the backstop, not the mechanism: the Builder is where a narrated process stops being a sequence. |
| **FR100** | Elicitation quality is tested against a **seeded business fixture**: a business whose material is supplied to the Builder with a known set of operational rules deliberately withheld from it, where those rules exist only in the operator's answers. The measure is how many of the withheld rules the Builder recovers, and how many it invents or silently defaults instead. This makes FR3, FR4, FR5 and FR7 falsifiable without requiring a numeric target to be invented, and it is the only way the Builder's hardest requirements become testable at all. |

**Why starting points are seeded rather than authored (FR8).** *[Superseded for V1 — §14 A1]* A per-vertical library was rejected on economics, not architecture: its cost scales with the number of verticals, and a starting point reintroduces that axis if it is allowed to become the thing being maintained. Starting points are therefore seeded *from specifications businesses already wrote*, and a starting point is never a prerequisite for a business type nobody has built yet.

### 8.2 Business Specification — what a business must be able to express

Stated as expressive capability, not as a field schema: the concrete schema is deferred to the Specification and Builder implementation. The specification is **one artifact**, from which the Core compiles everything the runtime uses.

| ID | Requirement |
|---|---|
| **FR13** | The Business Specification is a single artifact. The Agent's context, the capability surface offered to the model, and the policy the Core enforces are all compiled from it. There is no separate prompt, tool list or policy file as an independently authored product object. |
| **FR14** | A business MUST be able to express every area in the **expression surface** below. Each area is separately addressable, separately reviewable, and separately checkable by the validation suite. An area a business leaves empty is a recorded absence, never an implied default. |
| **FR15** | The specification MUST distinguish **obligations** — what must be true before an action — from **diagnostic inputs**, which are gathered to support a judgement and have no fixed sufficient set. The term *evidence* is reserved throughout this document for Core-authored records (FR70) and is never used for material the Agent gathers. |
| **FR105** | The goals in play for an episode, and the obligations outstanding for each, are **typed Core state** — readable by the Agent, asserted by the Core at resolution, and **never only prompt text**. But **holding them is not deciding with them**: the Core never selects which goal is pursued, and never decides what to do about an unmet obligation. A business declares which goals exist and what obligations attach; what to do about an outstanding one is the Agent's to reason about. No requirement in this document may be read as "if obligation X is unmet, do Y". |
| **FR106** | Where an obligation is **waived**, the waiver is explicit, attributable to a declared authority, and recorded. An obligation that quietly stops applying is indistinguishable from one that was never enforced. |
| **FR16** | The specification MUST support **decision authority classes** — at minimum informational, liability-bearing and state-changing — gated separately from one another. |
| **FR17** | The specification MUST be able to permit inferring a **cause** while forbidding determining **fault**. These are different acts with different consequences: an Agent may be authorized to say that overwatering is almost certainly the problem, and simultaneously forbidden from concluding that this constitutes neglect and the claim is therefore denied. |
| **FR18** | The specification MUST NOT be able to express ordering or sequencing. The authoring surface makes sequencing unexpressible; validation is the backstop, not the mechanism (FR24). |
| **FR19** | The specification is human-readable and diffable. It is **neither a generated prompt nor generated code** — otherwise diffing behaviour, asserting over behaviour, reviewing a proposed change, reverting a regression and attributing an outcome to a version are all unavailable. |
| **FR20** | Evaluation criteria live inside the durable specification, not recreated per generation. |
| **FR21** | The specification is versioned. A promoted version is immutable. |

**The expression surface (FR14).** Seventeen areas, each individually addressable. These are *areas a business must be able to express*, deliberately not field names — the concrete schema belongs to E1 (see O7).

| ID | A business must be able to express | Notes |
|---|---|---|
| **EX1** | Its identity — what the business is, how it speaks, **and what it will not say** | The only place agent voice is set. **The platform deliberately has no default voice and no character of its own** — this is a decision, not an omission, and nothing downstream (UX, a later design pass, a starting point under FR8) may invent one. A business that says nothing here gets a plainly-written agent, not a platform persona |
| **EX2** | Which goals exist, and what resolving each one means | |
| **EX3** | What may **never** become a goal | |
| **EX4** | Obligations — what must be established before each outcome or action | Distinguished from EX5 by FR15 |
| **EX5** | Diagnostic inputs — what helps the Agent reason without being required | No fixed sufficient set |
| **EX6** | Its rules — eligibility, pricing, timing, policy, constraints | |
| **EX7** | What the Agent may conclude, and on whose authority | Carries the authority classes of FR16 |
| **EX8** | Which capabilities are granted, and under what contract | Contract content fixed by FR51 |
| **EX9** | Guard conditions — what overrides the ordinary conversational path | |
| **EX10** | Escalation conditions — **what this business will not let an Agent decide** | The operator's authority dial, in the operator's own words |
| **EX11** | Refusal conditions | |
| **EX12** | What may be asked, and what must **never** be asked | Load-bearing in every exemplar business |
| **EX13** | What the Agent must **not infer or do** | Load-bearing in every exemplar business; carries the cause-versus-fault line of FR17 |
| **EX14** | Authoritative sources, and their precedence when they conflict | Version-pinned per FR30 |
| **EX15** | What evidence is required, and what happens when it is absent | |
| **EX16** | Evaluation criteria — what good looks like here | Lives in the durable specification per FR20 |
| **EX17** | Data-lifecycle requirements | Captured in V1 even though the executor is deferred (NFR10) |

### 8.3 Validation, promotion and rollback

The governing shape: specification, evidence, evaluation and deliberate changes behave like version control, and **promotion is a pull request on behaviour**. The product's job is not to measure conversational quality objectively — quality is irreducibly contested — but to make **disagreement cheap to express and fast to propagate**.

| ID | Requirement |
|---|---|
| **FR22** | There is exactly **one gate**, the **validation suite**, and it stands in front of both promotion and deployment. It comprises platform-owned invariant checks, which block, and the business's own declared criteria, which warn unless the business declares them blocking. A failing validation suite cannot be promoted or deployed. This is a hard gate, not advice. |
| **FR23** | Validation MUST detect a capability that is granted but which policy will always deny, and block promotion. A promise made to a customer and then broken is worse than a refusal. |
| **FR24** | Validation MUST reject sequencing constructs, with a comprehensible reason. |
| **FR25** | A **passing validation suite is the unit of done for a built business** (FR22). No business is deployed without one, and the same gate governs every later promotion — there is no separate, weaker pre-deployment check. |
| **FR26** | Rollback is selecting an earlier promoted version. No reconstruction, no migration. |
| **FR27** | An episode keeps the specification version pinned at its start. Promoting a change MUST NOT alter conversations already running. |
| **FR28** | Every promotion is reviewable, revertable and attributable. |
| **FR29** | Behaviour never mutates silently. There is no continuous automatic learning; evaluation and correction do not change production behaviour without a promotion. |
| **FR95** | The validation suite is **platform-owned, domain-agnostic and derived from the specification**. It is **never authored by the Builder it gates**, and it is never stubbed to pass. Per-business authoring checks may warn; only platform-owned checks may block. Where a business lacks the shape a check assumes, the check adapts or skips rather than failing. *[Narrowed — §14 A5]* |
| **FR96** | Every Core safety check — guard, detector, budget, validator — is positioned before anything that mutates what it measures, and is proven non-vacuous by demonstrating that it fires when the condition it guards is reintroduced. A check that cannot be shown to fail is not evidence of anything. |
| **FR101** | An operator can **revise a promoted specification through the Builder conversation**, producing a new version that passes the same gate and is reviewed and promoted like any other. This is what closes the improvement loop: a divergence item (FR82) is actionable because the Builder is the authoring path. It is deliberately **not** an in-product specification editor — the surface is the same conversation that created the specification, which is why the editor can stay out of V1 without the loop being open-ended. |

### 8.4 Business Knowledge and grounding

| ID | Requirement |
|---|---|
| **FR30** | Knowledge sources are **pinned to versions, not referenced**. Without this, two Agents can differ because of a revised leaflet while their specifications are identical, and a specification diff explains nothing. |
| **FR31** | A business declares precedence among its sources for when they conflict. |
| **FR32** | Every business-authoritative fact — prices, policies, hours, availability, eligibility, what the business sells and promises — MUST be grounded in a declared, version-pinned source. **FR33 enforces this at the level of reference integrity. It is not a claim that meaning is verified.** What is absolutely enforced is that no business-authoritative claim reaches a person carrying an unissued, altered or cross-tenant reference. Whether a validly-cited claim *faithfully represents* its source is measured against a threshold (NFR6), never guaranteed. The honest form of the promise is: the Agent cannot pass off an ungrounded business fact as a grounded one. |
| **FR33** | Every authoritative context item carries a Core-issued provenance reference bound to tenant, source, source version and locator. The Agent can neither mint, alter nor infer one, and a claim naming an unissued, altered or cross-tenant reference is refused before it reaches the person. |
| **FR34** | General domain knowledge may come from the model, MUST be marked as such in evidence, and is enabled or disabled per business as a declared risk. |
| **FR35** | Freshness is declared per read and per capability contract, **never globally**. A read whose result an effect depends on MUST be fresh; conversational reads may tolerate bounded staleness. Freshness is a **property of the read**, not an ordering imposed on the Agent — the Agent still decides when to retrieve (FR38), and the Core must not satisfy this by sequencing a retrieve before an act on the Agent's behalf. |
| **FR36** | External business systems remain authoritative. The platform owns no system of record. |
| **FR37** | Every answer is reconstructible against the exact source versions used to produce it. |

### 8.5 Agent reasoning within the Core boundary

| ID | Requirement |
|---|---|
| **FR38** | The Agent decides: what the person is trying to accomplish; what information is still needed; when to retrieve; which capability to use; whether to act, continue or respond; whether to escalate; how to phrase anything; and how to handle a situation nobody enumerated. |
| **FR39** | The Core never selects the Agent's next step. |
| **FR40** | The Agent emits one of a **closed** set of request kinds, and **every kind is authorized and journaled, reads included**. Closure runs in both directions: a business's capability model is a *grant over the existing kinds*, and nothing a business declares can add one. Widening the Agent's repertoire is a platform release, never onboarding (FR58). The set carries **no precedence and no ordering** among its members. |
| **FR107** | The Agent's loop has an **explicit termination bound** — a budget on work within a turn, enforced by the Core — together with a detector for repetition or stalling whose outcome is a wired handoff rather than a log line. An unbounded reasoning loop is not made safe by good prompting, and this is one of the Core guarantees §7.4 carries forward from the shipped system rather than a new invention. |
| **FR41** | The Agent never contacts anything outside the Core. |
| **FR42** | Five generic guardrails apply to every Agent with zero configuration: do not invent business facts; do not act outside declared authority; do not perform undeclared actions; do not claim success without evidence; escalate when required authority or evidence is unavailable. |
| **FR43** | Any constraint that must hold is enforced by the Core. The specification may also describe it to the Agent, but **no enforcement path may rely on the model respecting what it was told**, and no guarantee in this document rests on prompt text. |
| **FR44** | Guard conditions are evaluated **before goal recognition**, not after it — they are the reason an urgent or unsafe message never has to be understood as a request first. A guard may be evaluated by a model; the verdict binds deterministically with exactly two outcomes: a typed constraint returned to the Agent, or a declared safety halt that **aborts the episode outright**, in which case the ordinary path is abandoned rather than continued. A guard **never composes a reply and never chooses the Agent's next step**. A business configures which guard conditions apply, not what the Agent says when one fires. |
| **FR45** | The Core has exactly two exits: every outcome returns control to the Agent as a typed result, or a declared safety halt terminates the episode with a recorded outcome. There is no third path and no silent degradation. |
| **FR111** | A safety halt MUST NOT leave the requester in silence. The business declares a **terminal notice** for halted episodes, emitted by the Core through the egress port as the episode closes. This is a property of the halt, not of any guard: no guard composes it, it is not selected per guard condition, and it does not vary with what triggered the halt (FR44). A person who was mid-conversation is told it has ended; they are not abandoned. |
| **FR46** | Errors cross boundaries as typed results, never as defaults. A degraded or fallback outcome is always distinguishable from a healthy one **by the caller**, not only in a log line. |
| **FR47** | Escalation has exactly one owner: **the Agent escalates**. Where required authority or evidence is unavailable, the platform returns a typed refusal stating so; it never escalates on the Agent's behalf. A business declares escalation *conditions*, never escalation execution. |
| **FR48** | Where the business's rules are silent, the Agent escalates and the gap is recorded as a specification defect. **Never improvise a rule.** |
| **FR49** | Goals come only from the business's declared set. The Agent may not invent a goal, and there is no decomposition of goals into Agent-generated plans. |
| **FR50** | An episode may carry several related goals and switch between them, with one goal active at a time and both parking and resumption explicit. A customer wanting advice *and* a claim is the normal case, not an edge case. |

### 8.6 Capabilities and extensions

| ID | Requirement |
|---|---|
| **FR51** | Every capability is verb-first and declares a contract: input schema, effects, authority required, confirmation requirement, success evidence, and idempotency scope. A capability with no success-evidence definition is not shippable. |
| **FR52** | Every capability declares its **consequence class** — whether it is reversible, whether it costs money, and whether it reaches a customer. This is what an operator is actually bounding when they say they do not want an Agent contacting the wrong person, and it is visible, not internal. |
| **FR53** | An effect whose contract requires confirmation is not authorized until that confirmation is recorded. |
| **FR109** | Where a capability is state-changing, costs money or reaches a customer (FR52), the **authority under which it is executed must be established, not assumed from the channel**. A sender address is not an identity: an account cannot be mutated on the strength of a message header alone. What constitutes sufficient establishment is declared per business (EX7, EX12) and identity verification is an extension point, not Core semantics — but a capability of this class with no declared basis for authority does not pass the validation suite. |
| **FR54** | Whether a capability is eligible for automatic retry is a visible attribute. An action whose contract cannot define an idempotency key is not eligible. |
| **FR55** | External effects are at-least-once, against a Core-issued idempotency key scoped by tenant and episode which the adapter honours. Retries do not double-book or double-charge, and a genuine effect is never silently suppressed as a duplicate. |
| **FR56** | An external system is reached only as Core contract → adapter → extension. No feature promises a direct connection between the Agent and a third party. |
| **FR57** | Adapter credentials are held at the adapter boundary and resolved per tenant. **No credential value appears in Core state, episode evidence, Agent context or any prompt.** |
| **FR58** | Business configuration never changes Core semantics. A genuinely new semantic capability is a platform release, and the product MUST distinguish *configuring* a capability from *requesting* one. |
| **FR59** | Custom code may be a leaf behind a declared contract. It may **never** be control flow. |
| **FR116** | Variation between businesses resolves at exactly **three levels**, and which level a need lands at is a recorded judgement. **Configuration** is the expected path and covers the great majority of cases. A **supported extension point** takes capability that recurs across businesses but is structurally unlike configuration — a leaf behind a declared contract, such as identity verification, document intake, a derived figure, a validator or a scorer. **Custom implementation** is the exception and never the path. This is the taxonomy FR89 classifies engine leaks against, so it is defined here rather than assumed. |
| **FR97** | Capability and extension code never blocks the request path, and every external client carries its own explicit timeout. A single shared ceiling is not a defence: a blocking call on the request thread voids every timeout that depends on it, which is a fault this project has already paid for once. |

### 8.7 Episode lifecycle and continuity

| ID | Requirement |
|---|---|
| **FR60** | An episode's lifecycle is exactly: active; pending, awaiting a **named** external input; closed. No business sub-states may be added to it — business outcome lives in goals, obligations and the resolution, never in lifecycle. A business may declare a deadline on a named awaited input; **its expiry is an external system event**, which initiates or resumes an episode (FR61) and leaves what to do about it to the Agent. The Core never acts on an expiry, because acting on one would be selecting the Agent's next step. |
| **FR61** | An episode is initiated or resumed **only** by an inbound interaction or an external system event. Within an initiated episode the platform may reply and emit messages. The platform never independently starts an outbound conversation or episode. |
| **FR62** | An unresolved episode can be resumed later with its state, evidence, specification version and relevant context intact. A freeze awaiting a medical note, a hold approaching expiry, a claim waiting on a specialist are ordinary cases. |
| **FR63** | A result arriving after close is recorded as a **late result** and never mutates the resolution. |
| **FR64** | An in-flight episode survives a process failure. Clock, randomness, identifiers, environment and configuration are obtained through recorded means or pinned at episode start. |
| **FR65** | The Core is the sole writer of episode state; concurrent inbound messages on one episode are serialized. |
| **FR66** | There is no cross-episode memory and no cross-episode profiling. The Agent does not remember a customer between conversations. |
| **FR67** | Lifecycle says nothing about whether the business got a good outcome. `pending` is not a failure and `closed` is not a win. |

### 8.8 Resolution and evidence

| ID | Requirement |
|---|---|
| **FR68** | Every resolution carries: which declared goal it concerns; whether that goal was served; under which authority; the evidence supporting it; and a business-defined payload. This envelope is fixed; the enumeration of resolution kinds is deferred and emerges from running real episodes. |
| **FR69** | Escalation MAY be a declared success rather than a failure where the business says so — an episode escalated on an urgency trigger is a correct outcome. |
| **FR70** | Only the Core's execution record may attest that an effect occurred. **The Agent cannot author evidence.** Evidence entries are typed records against a platform-owned schema, never opaque blobs. |
| **FR71** | A resolution asserting an effect without a corresponding Core execution record is invalid. An Agent may never report that something happened without evidence that it did. |
| **FR72** | An action record is evidence that something happened, **not** a resolution. The two must never be conflated, and a single episode routinely produces both. |
| **FR73** | Episode evidence is durable **product data, not operational logs**: turns, retrievals, model decisions, actions, authorities exercised, obligations and waivers, guard verdicts, errors, timings, and **per-episode model calls, tool calls, token counts and cost** — under a stable episode identity. The last group is the record NFR13 and NFR14's instrumentation reads from. |
| **FR74** | Every escalation records its reason class. |
| **FR75** | Evidence is addressable and removable by tenant, by episode and by age, without reshaping the evidence schema. |
| **FR76** | Every **per-episode and per-business** criterion in §10.1 and §10.2 is computable from the episode record **without a human reading a transcript**. The per-project measurements in §10.3 are deliberately not of this kind — classifying an engine leak and judging resolution-model strain are acts of engineering judgement, recorded by a person during the validation programme. |
| **FR102** | Human corrections are captured as first-class records against the episode and the specification version in force, so that corrections per hundred episodes and their **trend** (§10.2) have a source rather than being reconstructed later. |

### 8.9 Divergence and the operator surface

| ID | Requirement |
|---|---|
| **FR77** | Every denial is recorded as exactly one of: a specification defect, where the compiled projections led the Agent to believe it was permitted; a business refusal, where policy correctly denied; or a platform error. |
| **FR78** | Only specification defects enter the specification backlog. The divergence log is the specification's error signal, and it **needs no human transcript review**. |
| **FR108** | A recorded human correction (FR102) is a **first-class divergence source alongside denials**, classified under FR77 and entering the same backlog. Denial classification covers only outcomes the Core **refused**, and the dominant failure mode is the opposite one — an answer that was permitted, confident and **wrong**, which produces no denial and therefore no divergence record. Without corrections as a source, the operator's primary surface is structurally blind to the failure class that matters most. |
| **FR115** | The product MUST sample business refusals for human adjudication, at a rate the business sets, and a refusal found wrong on adjudication enters the backlog as a specification defect. Without this a **wrong refusal is invisible by construction**: a correct denial and an over-strict one are both recorded as a business refusal, only specification defects reach the backlog (FR78), and the person who was wrongly refused does not come back to complain. Left alone that is selection bias with a feedback loop attached — the specification drifts toward strictness and the metrics improve while it happens. |
| **FR79** | The operator's primary surface is the classified divergence list — in substance, *"here is what your specification got wrong."* |
| **FR80** | An operator can open a single episode and see what happened within it. |
| **FR81** | Every failure, refusal or status an operator sees comes from a closed, enumerable vocabulary. |
| **FR82** | A divergence item is actionable toward a specification change, closing the loop from observed behaviour back to reviewed promotion. |
| **FR110** | An operator can **suspend their Agent immediately**, without a promotion and without a deployment, and can suspend its ability to perform effects while leaving it able to respond. A system that sends messages to real customers and cannot be stopped in one action is not operable, whatever its specification says. Suspension is recorded, and episodes in flight when it happens end in a recorded outcome rather than silently. *[Specified — §14 A7]* |

### 8.10 Channel — inbound email and messaging

| ID | Requirement |
|---|---|
| **FR83** | All behavioural requirements in this document are channel-neutral. **The Agent and Core never learn which channel an episode is on.** |
| **FR84** | V1 ships one channel adapter, providing both ingress and egress: **inbound email / messaging**. |
| **FR85** | The adapter is replaceable without touching behaviour. Adding a channel later is adapter work, not re-specification. |
| **FR113** | What the Agent writes must be **appropriate to the channel it is read on**, and the channel adapter owns that shaping — not the Agent, which never learns the channel (FR83). For V1 this means written correspondence rather than conversational fragments: a reply that reads as a message a business would send. Expressive intent itself is business configuration (EX1), and **how the Agent writes is part of what the business's evaluation criteria may judge** (EX16), so that voice is evaluable rather than merely declared. |
| **FR86** | The adapter correlates inbound messages to episode identity, with an explicit join key wherever an episode touches an external system of record. |
| **FR87** | The adapter guards against duplicate and corrected re-sends of the same inbound message, so a resend does not become a second episode or a second effect. Turn handling is **idempotent per logical turn**. |
| **FR98** | Every channel adapter is built against **captured real traffic**, not vendor documentation alone, and every behaviour discovered that way is pinned by a test. Any channel with retries, edits or webhooks reintroduces this problem, so it is an adapter requirement rather than a one-off. |
| **FR114** | The inbound email adapter handles the conditions that make email email, each of which can break episode identity or cause harm: **threading and quoted history** (a reply carries the whole prior conversation and must not be re-read as new input), **additional recipients** (who is party to an episode, and who must not receive its content), **attachments** (accepted as knowledge or refused, never silently ignored), **bounces and delivery failures** (a reply that never arrived is not a served goal), and **automated-sender loops** (an auto-responder on the far end must not produce an unbounded exchange). Each is pinned by a test under FR98. |
| **FR103** | An escalated episode is **delivered to a destination the business declares**, over the V1 channel, carrying the escalation reason class and a link to the episode. Without this, escalation is specified on the Agent's side and arrives nowhere, and no business could be run on V1. The destination is per-business configuration; routing rules, rotas, acknowledgement and response expectations are **not** in V1 (O2). |
| **FR112** | The requester is **told they are corresponding with an automated agent**, in the first message of an episode. The wording is per-business (EX1); whether disclosure happens is not. This is the safe default rather than a researched position — jurisdictional requirements may be stricter and are tracked in O3 — but a V1 that leaves it undecided cannot be put in front of a real customer. |

> **Why this channel.** It is the operator's real inbound queue, and it is the stated source of the real requests the usefulness test needs. Being genuinely asynchronous, it exercises pending episodes and cross-session resumption honestly rather than simulating them. It also carries near-zero turn-latency pressure, which deliberately keeps the latency-as-correctness discipline of the voice project out of V1 — see §9.
>
> **And the honest weakness of that reasoning.** Every justification above is about **fitness for testing the architecture**, not about where the value is. The source material names this exact bias — architectural convenience presenting itself as product judgement — as having already occurred more than once on this project, and it left behind the question that should govern a channel choice: *where does the valuable interaction actually happen?* For small-business inbound, the uncomfortable answer is that it is still substantially phone-led, and the funded competitors are voice-first. This document does not reverse the decision: an asynchronous channel is the right place to prove the platform claim, and voice is a solved problem here waiting behind an adapter (§7.4). But the decision is recorded as **chosen for provability, not for value**, and it is not evidence about where this product eventually belongs. O10 carries it.

### 8.11 Generalisation validation programme

A V1 deliverable, not a post-launch activity. V1 is not complete until these exist.

| ID | Requirement |
|---|---|
| **FR88** | All four exemplar businesses are built through the Builder, by the same path a real operator would take. |
| **FR89** | **Engine leaks** are recorded and classified: *should have been configuration*, *justifies an extension point*, or *genuinely novel*. |
| **FR90** | **Resolution-model strain** is recorded — whether any business needs a resolution the model cannot express. |
| **FR91** | **Setup effort** is recorded per business from the Builder's own burden instrumentation (FR12), and compared across the four in the order they were built. |
| **FR92** | The usefulness test runs against **real** inbound requests, with Agent failures reported separately from blocks caused by the business's own rules or capacity. **At least one of the four businesses must be real end to end** — a real operator, their own material, their own inbound traffic. The other three may run against authored corpora drawn from public enquiries, reviews and published FAQs, and results from those are reported as what they are. A usefulness claim tested entirely against requests the team wrote is not a usefulness claim, and §13.1 already concedes all four specifications are currently constructions. |
| **FR93** | The **validity floor** is recorded: the share of episodes requiring obligations, rules or action rather than plain information. This is a measurement of the test, not a product metric — but if it is near zero, the demonstration proves nothing however good the other numbers look. |
| **FR94** | Two or three conversations with real small-business operators are conducted, as the only available test of the problem statement and of the printed-versus-practised gap. Specifications written without them remain constructions rather than any real business's rules. |

---

## 9. Cross-cutting non-functional requirements

Most of these are fixed by the Architecture Spine and are restated here rather than reinvented. **Where a value is absent, that is stated as absent rather than guessed** — see §10 for why no thresholds appear.

#### 9.1 Integrity and evidence

| # | Area | Requirement | Quantified? |
|---|---|---|---|
| **NFR1** | **Durability** | Every model decision, authorized execution and evidence write is durable. An in-flight episode is recoverable after a process failure | Binary, not numeric |
| **NFR2** | **Effect integrity** | External effects are at-least-once with a Core-issued idempotency key; non-keyable actions are not auto-retried | Qualitative, absolute |
| **NFR3** | **Isolation** | Every episode, specification, knowledge source, provenance reference, idempotency key, evidence record and action request carries a tenant identity. **Any resolution that crosses tenants is rejected, not filtered** — never a quietly empty result | Qualitative, absolute |
| **NFR4** | **Auditability** | Every request kind is authorized and journaled, reads included. Only the Core authors evidence, against a typed schema. Every denial is classified | Complete coverage |
| **NFR5** | **Provenance integrity** | Provenance references are Core-issued, episode-scoped and unforgeable by the Agent. A claim naming an unissued, altered or cross-tenant reference is refused **before it reaches the person**. Absolute, and scoped strictly to *reference validity* — it makes no assertion about meaning, which is NFR6's subject | Qualitative, absolute |
| **NFR6** | **Semantic faithfulness** | Beyond provenance validity, faithfulness is **evaluated against a threshold, never guaranteed**. The product may not promise correctness of meaning | Threshold value **not set** — to be established from the four-business run; instrumented from day one |

#### 9.2 Change, reproducibility and consistency

| # | Area | Requirement | Quantified? |
|---|---|---|---|
| **NFR7** | **Reproducibility** | Specification, compiler and knowledge-source versions are pinned at episode creation and read from episode state thereafter, never live | Qualitative, absolute |
| **NFR8** | **Change safety** | Promoted versions immutable; validation a hard gate; rollback by version selection | Qualitative, absolute |
| **NFR9** | **Consistency** | The Core is the sole writer of episode state; concurrent inbound on one episode is serialized | Qualitative |

#### 9.3 Data, secrets and portability

| # | Area | Requirement | Quantified? |
|---|---|---|---|
| **NFR10** | **Data lifecycle** | A business can state its data-lifecycle requirements, and evidence is addressable and removable by tenant, episode and age. Episodes may hold sensitive and health-adjacent material | Capability required in V1; retention policy and deletion executor **deferred** |
| **NFR11** | **Secret handling** | No credential value appears in Core state, evidence, Agent context, any prompt, or any evidence export | Qualitative, absolute |
| **NFR12** | **Portability** | Changing the model, provider or agent framework MUST NOT alter the architecture. No vendor SDK import, no hardcoded provider or base URL, no branching on provider, no vendor-specific key. Swapping providers is a configuration change | Qualitative, absolute |

#### 9.4 Measurement and operation

| # | Area | Requirement | Quantified? |
|---|---|---|---|
| **NFR13** | **Latency** | **No turn-latency target is set for V1. [ASSUMPTION A1]** The chosen channel is asynchronous, which is taken to *remove* acute dead-air pressure rather than merely defer it — a later synchronous channel would reintroduce it against a system never built under it. Per-turn and per-episode latency are nonetheless instrumented from day one, because the target must come from measurement and because a later channel will reintroduce the constraint | **No number, deliberately** |
| **NFR14** | **Cost** | **No per-episode cost ceiling is set for V1.** Per-episode model and execution cost is instrumented from day one. A visible spend ceiling is a trust feature as much as a commercial one and is noted as an open item | **No number, deliberately** |
| **NFR15** | **Availability, throughput, scale** | Not V1 concerns, and stated as such. The dimension that will grow first is episode volume per business; its cost slope is measured during the four-business run rather than designed for now | Unmeasured; named |
| **NFR16** | **Observability** | One correlation identity per episode, present on every record of that episode's work and reportable by a person who experienced a problem. Evidence vocabulary follows established GenAI telemetry naming where it exists *[Narrowed for V1 — §14 A6]* | Qualitative |
| **NFR17** | **Configuration validity** | Configuration and credentials are validated at startup, not at first use. A health check MUST NOT report healthy on a configuration whose first real request will fail | Binary |
| **NFR18** | **Timestamps** | UTC throughout | Fixed |

---

## 10. Success criteria

**No numeric target appears in this section, by decision.** No baseline exists, the public record on this problem is contaminated, and an invented threshold would later be quoted as though it were evidence. Every criterion is therefore structural or directional — and every one of them MUST be computable from the episode record without a human reading a transcript, which is itself a requirement (FR76) rather than an aspiration.

### 10.1 Per episode

Computable from the record: reached a declared resolution or a legitimate pending state; every business fact traceable to a pinned source; obligations complete before any action; actions taken only through contracts, with confirmation where required and evidence of success recorded; no conclusion drawn outside a declared authority; guards fired when their conditions were met; escalation reason recorded; no policy violation.

### 10.2 Per business

- Share of inbound episodes resolved without a human. *[Specified — §14 A7]*
- Share reaching the intended action — **reported separately** from the share blocked by the business's own rules or capacity, because conflating them makes a business constraint look like an Agent failure.
- Human corrections per hundred episodes, **and whether that falls over time**.

### 10.3 Per project — the minimum generalisation test

| Measurement | The thesis fails if |
|---|---|
| **Engine leaks** — every instance where the Core had to change rather than the business layer, classified per FR89 | Leaks do not fall toward zero from the first business to the fourth |
| **Resolution-model strain** — per FR90 | Any business cannot be expressed, which would mean evaluation cannot be reusable |
| **Setup effort** — per FR91 | Effort does not fall materially across the sequence |

This needs no customers and no market, only real business material, and it should run **before** any commercial validation.

### 10.4 Counter-metrics and anti-gaming guards

These exist because each of the headline numbers above can be made to look good dishonestly.

| Guard | What it prevents |
|---|---|
| Agent failure is reported separately from business-constraint blocks | A business's own policy appearing as an Agent defect, or vice versa |
| The validity floor is recorded (FR93) | A high resolution rate achieved only on plain-information requests, which proves nothing |
| Lifecycle is never read as success | `closed` counted as a win; `pending` counted as a failure. A single episode may resolve well after being pending for days |
| Action evidence is never read as resolution | An applied change and a served goal are two different facts, and one episode produces both |
| Corrections are tracked as a **trend**, not a snapshot | A flattering single measurement standing in for whether the specification is actually improving |
| Setup effort is measured per business across the sequence | Generalisation being claimed from the first business, where all the learning is bespoke |
| Business refusals are sampled for human adjudication (FR115) | **Drift toward strictness.** A wrongly-refused request produces no denial signal and no complaint, so over-strictness is invisible while every other number improves |
| Recorded corrections feed the divergence backlog (FR108) | A confidently wrong but *permitted* answer leaving no trace, which denial classification alone cannot see |

---

## 11. Open items

Carried deliberately. Each states why it is open and what event should reopen it, rather than an invented answer. Ownership follows the epic each one lands in (§12); none is assigned to a person in this document.

| # | Open item | Why it is open | Revisit when |
|---|---|---|---|
| **O1** | Who performs specification review, and with what competence *[Narrowed for V1 — §14 A3]* | The specification must be human-readable and reviewable, but no reviewer role or review verdict is defined anywhere in the sources | Before the first business is promoted |
| **O2** | Escalation **routing** — rotas, multiple recipients, acknowledgement, and any response expectation | Delivery to a single business-declared destination is now specified (FR103), which is enough for V1 to be operable. Everything about *who* beyond one address, and what happens if nobody answers, is not | When a business needs more than one recipient |
| **O3** | The **jurisdictional** requirements on automated-agent disclosure, and whether any channel or territory demands stricter wording or placement than FR112 provides | Disclosure itself is no longer open — FR112 requires it. The source material does contain professional opinions requiring disclosure, and this document's earlier claim that no position existed in any source was wrong. What remains open is the legal specificity, which is not a product judgement | Before a business operates in a second jurisdiction |
| **O4** | The resolution-kind enumeration | Deferred by architecture; it follows from running real episodes. Candidate families exist but are provisional | During the four-business run |
| **O5** | The semantic-faithfulness threshold value (NFR6) | Cannot be set without a baseline | After the four-business run |
| **O6** | A visible per-business spend ceiling (NFR14) | Usage unpredictability is a reported leading cause of abandonment in this market tier, which makes a ceiling a trust feature. No commercial model exists in V1 to attach it to | When commercial packaging is taken up |
| **O7** | The specification field schema, and the field-count discrepancy in the source material | The stress test enumerates fourteen items while asserting thirteen invariant fields, and structural change 6 then splits one of them. This PRD deliberately specifies expressive capability instead (§8.2) | When the Specification epic begins |
| **O8** | Commercial packaging, pricing and tenancy topology | Out of V1 scope. The north-star *hire* framing is not a V1 promise, and nothing in V1 depends on resolving this | After the generalisation claim is tested |
| **O9** | Domain safety packs | The extension point is in V1; no pack is. The dental exemplar carries a mandatory override and the garden centre a liability boundary, but no regulation is named in any source | When a business needs one |
| **O10** | Where the valuable small-business inbound interaction actually happens, and therefore which channel this product belongs on beyond V1 | The V1 channel was chosen for provability rather than value (§8.10), which is legitimate for a validation phase and is not evidence about the product's eventual home. Inbound is still substantially phone-led and competitors are voice-first | After the generalisation claim is tested, and before any channel is built as a commercial bet |
| **O11** | Whether **counterfactual replay** — re-running a closed episode against a later specification version to show what would now happen differently — is a V1 feature | It is close to free given what is already required: immutable versions (FR21), version pinning (FR27), a full episode record (FR73) and an actionable divergence item (FR82). The source material flags it as the one genuinely unoccupied position in the current trust landscape, and it is the most direct answer to "will this change fix it?" Left undecided rather than silently dropped | During E10, where the cost is visible |

**Deferred architecture topics** are listed in §7.3 and are not open items for this document — they belong to the architecture, and every requirement above states a guarantee rather than naming a mechanism.

### 11.1 Assumptions index

Four load-bearing inferences the sources did not confirm. Each is tagged inline where it operates.

| Tag | Assumption | Where it operates | What tests it |
|---|---|---|---|
| **A1** | An asynchronous channel **removes** acute latency pressure rather than deferring it | §8.10, NFR13 | A later synchronous channel, against a system never built under the constraint |
| **A2** | Constructed exemplar specifications are an adequate substitute for real business rules — **for the architecture claim only** | §2, §13.1 | FR92's one real business; FR94's operator conversations |
| **A3** | The buyer and the Builder are commonly the same person, commercially | §2 | Nothing in V1. It is a commercial assumption with no architectural dependency, which is why it is safe to hold untested |
| **A4** | An operator exists who holds the undocumented operational rules **and can articulate them when interviewed** | §2, all of §8.1 | FR94, and FR100's seeded fixture |

A4 is the one that matters. If operators cannot articulate their own tacit rules under interview, the Builder cannot be rescued by better elicitation and the product needs a different premise.

---

## 12. Epics implied by these requirements

Derived from the requirement groups and the Spine's own component boundaries, as the input to epic-and-story breakdown. Ordering below is dependency, **not** a behavioural sequence.

| # | Epic | Covers | Carries the V1 risk? |
|---|---|---|---|
| **E1** | **Business Specification** | The artifact; the EX1–EX17 expression surface; authority classes; obligations versus diagnostic inputs; waiver semantics; cause-versus-fault separability; goals and obligations as typed Core state; sequencing made unexpressible; versioning. The concrete field schema is deferred to here | High — O7 lands here |
| **E2** | **Builder and elicitation** | Conversational adaptive elicitation; interviewing for undocumented rules; contradiction surfacing; defect recording rather than guessing; re-deriving a narrated process into declared areas (FR104); optional pre-filled specification starting points *[superseded for V1 — §14 A1]*; **burden and yield instrumented together** (FR12, FR99); the seeded-business fixture (FR100); conversational revision of a promoted specification (FR101) | **Highest — this is the product risk, and FR100 is what makes it measurable** |
| **E3** | **Validation and promotion** | The single validation-suite gate in front of promotion and deployment, granted-but-always-denied detection, immutable versions, rollback, attributable promotion | Medium |
| **E4** | **Core enforcement** | The closed request taxonomy; authorization; the five generic guardrails; decision authority gating; guards with deterministic binding; two exits and the terminal notice (FR111); typed results; the Agent loop's termination bound and stall detector (FR107); non-vacuous proof of every check (FR96) | High |
| **E5** | **Agent runtime boundary** | The reasoning loop, provider and framework abstraction, tiering expressible but unpinned | Medium |
| **E6** | **Business Knowledge and grounding** | Ingestion, version pinning, source precedence, provenance issuance, the two knowledge tiers, declared freshness | High |
| **E7** | **Capability execution and extensions** | Capability contracts; consequence classes; confirmation gating; **authority established rather than assumed from the channel** (FR109); idempotency; adapters with their own timeouts and off-path execution (FR97); per-tenant credentials | High — FR109 is where an account gets mutated on a forged header if it is got wrong |
| **E8** | **Episode lifecycle and durability** | Three-state lifecycle, pending and resumption, durable steps, version pinning, serialization, late results | Medium |
| **E9** | **Resolution and evidence** | The resolution envelope, typed evidence, the no-evidence-no-claim invariant, episode record, addressability by tenant/episode/age | High |
| **E10** | **Divergence and operator surface** | Denial classification; **recorded corrections as a first-class divergence source** (FR102, FR108), without which the surface is blind to confidently-wrong-but-permitted answers; the divergence list; the single-episode viewer; immediate suspension (FR110); closed outcome vocabulary | High — raised from Medium: FR108 is the difference between an improvement loop and a refusal log |
| **E11** | **Channel adapter — inbound email/messaging** | Ingress and egress; episode correlation and join keys; resend and duplicate guarding; channel-appropriate expression (FR113); escalation delivery (FR103); disclosure (FR112); and the conditions that make email email — threading and quoted history, additional recipients, attachments, bounces, automated-sender loops (FR114) | Medium — raised from Low: FR114 is a list of ways to break episode identity or mail a stranger |
| **E12** | **Generalisation validation programme** | Four businesses built through the Builder; three measurements recorded; the usefulness test with **at least one business real end to end** (FR92); the validity floor; operator conversations (FR94) | **Highest — this is what falsifies the thesis** |

Two epics carry the V1 claim: **E2**, because elicitation is the hard problem, and **E12**, because without it this is a runtime plus an assertion that it can be configured. The **proof gate (§7.5)** sits in front of E4–E9 and is not an epic.

One piece of work has no epic of its own and is called out so it does not fall between them: the **migration assessment in §7.4** — deciding, asset by asset, what is carried over as-is, rebuilt from the concept, or left behind. It is distributed across E3 through E9 rather than owned centrally, and the one thing that must not happen quietly is the fifteen-node pipeline being ported because it exists.

---

## 13. Limitations

Stated in two halves, because a limitations section with an empty operational half was written by someone who reviewed half the system.

### 13.1 Domain and method

- Neither project claim is proven. The specification has been shown to **express** four dissimilar businesses; it has not been shown to **drive behaviour**.
- The four exemplar specifications are constructions, not any real business's rules. The printed-versus-practised gap is the likeliest place all four are wrong, and only a real operator can close it (FR94).
- No quantified pain figure supports the problem statement. The public record is contaminated and no primary operator evidence has been obtained.
- No numeric success threshold exists anywhere in this document, by decision. Acceptance is directional until the four-business run produces a baseline.
- The differentiation claim is narrow by necessity: the declarative-specification paradigm is validated and widely held at the enterprise tier, and no moat is claimed (§4.2).

### 13.2 Operational

- **Dependency failure:** every external system is reached through an adapter, and an adapter failure returns a typed result to the Agent rather than a default. Per-adapter timeout and retry policy is not specified in this document and belongs to E7; non-idempotent capabilities are not auto-retried (FR54).
- **Degraded results:** no fallback may read as success — every degraded outcome is distinguishable by the caller (FR46), and the Core has only two exits (FR45).
- **Concurrency:** the Core is the sole writer of episode state and concurrent inbound on one episode is serialized (FR65). Capability and extension code must not block the request path, and every external client carries its own timeout (FR97) — that much is settled; the concurrency model used to honour it is an implementation decision in E5/E8.
- **Scalability:** the dimension that grows is episode volume per business. Its cost slope is **unmeasured**; it is measured during the four-business run (NFR15). No capacity claim is made.
- **Observability:** one correlation identity per episode, on every record of its work (NFR16). The operator-visible surface in V1 is the divergence list and the episode viewer only — there is no alerting, and no metrics dashboard (§7.2). *[Amended — §14 A2]*
- **Configuration and secrets:** validated at startup, never at first use; a health check must not report healthy on a configuration whose first request will fail (NFR17). No credential value reaches state, evidence, context or a prompt (NFR11).
- **Deployment:** not specified in this document. Multi-tenant hosting is explicitly out of V1 (§7.2) while tenant identity on every record is in (NFR3) — so the isolation guarantee holds regardless of the topology eventually chosen.
- **Durable state:** evidence is product data, durable, and addressable and removable by tenant, episode and age (FR75, NFR10). The retention policy and the deletion executor are **deferred** — the capability may not be foreclosed, but no deletion SLA is promised.

## 14. Amendments after finalization

Recorded 2026-10-15 (A1–A3) and 2026-10-16 (A4–A7); rows are cited as "§14 An", distinct from the assumption tags A1–A4 of §11.1, and "program gate" means a gate of NEXT-PHASE-PLAN §6. Rows A1–A3 record decisions already taken in an approved BMAD run; rows A4–A7 record wording the user approved, and their decisions stay PROPOSED until the user confirms them; no requirement text above was rewritten, and each affected statement carries an inline marker. Status is the decision's own, from its source.

| # | Amendment | Affects | Source | Status |
|---|---|---|---|---|
| A1 | No vertical starter templates in V1. The Builder's only path is conversation plus the operator's material → Business Specification and Business Knowledge. Reconsiderable later purely as an onboarding optimisation. | §4.4, FR8, §8.1 note, §12 E2 | UX `.memlog.md` line 22 `(override)`; EXPERIENCE.md, Prohibitions carried from the sources | APPROVED |
| A2 | A material divergence may ride the declared escalation email path (FR103) when it requires operator attention. Not authorised by this amendment: a generic notification system, a divergence-alerts product, an inbox, a digest, or any notification framework. What makes a divergence material is an upstream attention-policy question and remains open. | §13.2 | UX `.memlog.md` lines 58 `(override)`, 73, 74; EXPERIENCE.md Amendments item 1 and Open Question 3 | APPROVED (materiality OPEN) |
| A3 | In V1 the business operator is the approver: no separate reviewer role, no approval hierarchy. Approval does not determine validity — the blocking validation suite does. Who may approve beyond V1, and with what competence, remains open. | §2 Specification reviewer, FR11, O1 | UX `.memlog.md` line 37; EXPERIENCE.md Amendments item 7 | APPROVED |
| A4 | Material intake. In V1 the Builder accepts plain text, Markdown, PDF with a text layer, DOCX, CSV, XLSX and pasted text. There is no OCR: a PDF without a text layer is reported as "Could not be read. Nothing from it has been used." Size and duration limits are recorded and stated to the operator, never applied silently; partly readable material states which parts were used. Ingestion never blocks a Builder turn. Fetching web pages is deferred until the operator conversations (FR94) show where businesses keep their published FAQs. Unverified premise (program handoff U3, 2026-10-15): that these formats cover what small-business operators hold; FR94 tests it. | FR2, FR117 | EXPERIENCE.md Material intake ("unspecified upstream") and Amendments item 10; user decision 2026-10-16 (program gate D15) | PROPOSED (wording approved by the user 2026-10-16; decision pending) |
| A5 | Validation findings. FR22 governs: platform-owned checks block, and a business's declared criteria warn unless the business declares one blocking. A business-declared blocking criterion can only add a block; it never waives, weakens or overrides a platform check. FR95's "only platform-owned checks may block" is narrowed accordingly; the suite itself stays platform-owned and is never authored by the Builder it gates. Every finding states whether it blocks, its origin (platform check or business-declared criterion), a plain-language statement, the expression area it concerns, and the item where there is one. A check that did not run is not a finding; a check skipped under FR95 is recorded in the validation record, so a skip stays auditable (FR96). | FR22, FR95, FR24 | PRD `.memlog.md` line 53; EXPERIENCE.md Validation result and Amendments item 13; user decision 2026-10-16 (program gate D15) | PROPOSED (wording approved by the user 2026-10-16; decision pending) |
| A6 | Error references. Every unit of work has one correlation identity: an episode, a Builder session, or an operator action (approval, promotion, rollback, suspend, resume). Every platform error the operator sees shows that identity, or a code resolving to exactly one unit of work and its records. In V1 references are shown to the operator only: a requester never sees one, and the business's terminal notice and disclosure wording never carry one. Known limit: a requester can report a problem only through the business, and the V1 operator surface cannot find an interaction that is not an Activity item, so for requesters NFR16's "reportable by a person who experienced a problem" is met only in part. | NFR16 | EXPERIENCE.md "Something on our side failed. Reference: {code}" and Amendments item 17; user decision 2026-10-16 (program gate D15) | PROPOSED (wording approved by the user 2026-10-16; decision pending) |
| A7 | Suspension outcomes. When the operator fully suspends an Agent, every interaction in flight (active or pending) ends in a declared safety halt whose recorded reason is the operator's suspension, and the requester receives the business's terminal notice (FR111); a notice that cannot be delivered is recorded as undelivered. An inbound message that arrives while the Agent is suspended is recorded as an interaction with the outcome "arrived while suspended", receives no reply, is shown to the operator in Activity, and is not answered after resume. Effects-only suspension refuses every effect as a typed result, classified as a business refusal (FR77), while replies continue. Evaluation (FR76, §10.1–10.2): interactions that arrived while suspended stay in the record but are outside the denominators of Agent-quality measures, because the Agent never handled them; every report of those measures states this exclusion and the number excluded, beside the measures, so the exclusion cannot improve a figure unseen. Interactions the suspension halted stay inside the denominators, recorded as halts with the reason operator suspension. | FR110, FR111, FR76, §10.1–10.2 | Architecture Spine AD-26; EXPERIENCE.md Amendments item 20; user decision 2026-10-16 (program gate D14) | PROPOSED (wording approved by the user 2026-10-16; decision pending) |
