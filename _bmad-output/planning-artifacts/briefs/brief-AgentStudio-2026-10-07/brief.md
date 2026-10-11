---
title: "Product Brief: Agent Studio"
status: final
created: 2026-10-07
updated: 2026-10-07
---

# Product Brief: Agent Studio

## Executive Summary

Agent Studio is a reusable behavioural agent system for small businesses. Given a short conversation about a business and a few of its own documents, it produces a versioned specification, validates it, and deploys an agent that handles that business's inbound requests. The agent works out what the person is trying to accomplish, obtains what it still needs, grounds every business fact in the business's own material, concludes only what the business has authorised, acts only through declared contracts, escalates what it may not decide, and closes with a structured outcome it can be judged on.

The product is the machinery, not any one agent. A brewery on Tuesday, a dental practice on Saturday, a gym and a garden centre the week after — the same behavioural core each time, with the difference expressed as specification, knowledge, rules, obligations, tools, guard conditions, escalation policy and evaluation criteria.

Two distinct claims are under test:

1. **The architecture claim.** Can one behavioural core handle materially different small-business requests while only the business layer changes?
2. **The usefulness claim.** Does that core resolve a meaningful class of inbound requests well enough that the resulting agents are useful, not merely technically impressive?

A four-business specification stress test (`spec-stress-test.md`) has established that the specification can **express** four businesses sharing no workflow. What it has not established is that it can **drive behaviour** — which is why the behavioural chain below, rather than the data model, is the centre of this brief.

No commercial moat is claimed. The market evidence is recorded under *Market Honesty* and is deliberately not permitted to steer the product toward hunting an unoccupied vertical.

## The Problem

Small businesses answer the same requests endlessly, and the knowledge needed to answer them well already exists — in a price list, a policy, a care guide, a membership agreement, the owner's head. What does not exist is anything that can hold the conversation and act on that material.

Each coping strategy fails specifically. A person answers when they can and misses the rest, concentrating failure after hours and at peak. A web form captures a fraction of what is needed and begins a round of clarifying messages. A scripted chatbot deflects to a link. An answering service takes a message but cannot apply the business's rules. A document-retrieval chatbot answers questions but cannot *do* anything, so every request needing an action still reaches a person.

The underlying problem: **a small business's rules and knowledge are not in a form anything can act on**, so every inbound request consumes human attention from scratch.

## The Generic Interaction Pattern: Request → Resolution

Someone brings a request. The agent carries it to a resolution. The requests differ radically by design:

| Business | A real request | What it stresses |
| --- | --- | --- |
| **Brewery** | "I want to host a 40-person event next month." | Negotiated multi-constraint planning; no slots, no practitioners |
| **Gym** | "I want to freeze my membership for two months." | Account state mutation under policy; recurring commitments |
| **Garden centre** | "This plant I bought is dying. What should I do?" | Diagnostic advice; ambiguous goal; a liability boundary |
| **Dental practice** | "I was told I need a root canal. What happens?" | High-stakes grounding; mandatory override; explanation, not transaction |

These are not one workflow with four skins. The claim is that they share **behaviour**.

## The Behavioural Chain

This is the core of the product. The specification's job is to **constrain each link**, not to describe the data sitting around it.

> **goal → information gathering → reasoning / decision → allowed action → verification → outcome**

| Link | What the specification constrains |
| --- | --- |
| **Goal** | Which goals exist; what completing each one means; what may never become a goal |
| **Information gathering** | The obligations for each goal; what may be asked; what must never be asked |
| **Reasoning / decision** | Which conclusions the agent may draw, under which authority, from which evidence |
| **Allowed action** | Which actions exist, their preconditions, their contracts, and which require explicit confirmation |
| **Verification** | What evidence proves an action succeeded, and what happens when that evidence is absent |
| **Outcome** | Which resolutions are permissible for a goal, and what must be recorded |

**Reasoning is broad; authority is bounded.** The agent may think widely about a request. What it may *conclude*, and what it may *do*, are narrow and declared. That asymmetry is the product's central discipline, and the verification link keeps it honest — an agent may never report that something happened without evidence that it did.

A **guard check** runs ahead of the chain, covered next.

## The Reusable Behavioural Core

Built once, never per business.

| Primitive | What it provides |
| --- | --- |
| **Goal set with completion conditions** | Which declared goal is in play and what finishing it means. Not utterance classification |
| **Guard conditions** | Declared conditions that override the ordinary conversational path *before* goal pursuit, and may end the episode regardless of what was asked |
| **Obligation tracking** | What must be established before a given outcome or action is permitted |
| **Diagnostic evidence gathering** | Information that helps the agent reason but is not required for resolution |
| **Grounded claim** | Every business fact carries a source and a knowledge tier |
| **Rule evaluation** | Declared predicates over collected information and live external reads |
| **Decision authority classes** | Separately gated: information the agent may provide; conclusions it may draw under declared authority; state-changing actions |
| **Contracted action** | Propose, validate against contract, confirm, execute, obtain evidence of success |
| **Escalation with reason class** | Handing to a human, with why |
| **Episode lifecycle** | Active, pending and resumable, or closed |
| **Resolution record** | The business outcome, recorded separately from lifecycle and from action evidence |
| **Episode evidence** | A durable structured record: turns, retrievals, decisions, actions, authorities exercised, errors, timings |
| **Evaluation** | Invariant checks plus the business's declared criteria |

### Guard conditions — generic, not domain-specific

Candidate guard families, declared per business: **urgency**, **authorisation failure**, **policy violation**, **unsupported request**, **identity problem**, and any other declared guard.

The primitive is the override capability, not any one domain's use of it. A dental practice's urgency triggers are one instance; an identity failure before an account change is another; a request outside declared scope is a third.

### Three orthogonal dimensions, previously conflated

The stress test showed one enum carrying three unrelated jobs. They separate:

- **Episode lifecycle** — is this interaction `active`, `pending` (awaiting a named external input, with a deadline), or `closed`? Lifecycle says nothing about whether the business got a good outcome.
- **Business resolution** — recorded at close: whether the person's goal was served, on whose authority, and what evidence supports it. A single episode may resolve well after being pending for days.
- **Action evidence** — whether a state change occurred, with its confirmation reference and terms. **An action record is evidence that something happened, not a resolution.** An applied membership freeze produces both, and they are not the same fact.

Resolution families are deliberately **not fixed as a final enum** in this brief. The shape is settled — every resolution carries *whether the goal was served*, *under what authority*, and *on what evidence* — and the enumeration is an architecture decision, made once the runtime model is clear. Candidate families, provisional: *served with information*, *served with action*, *declined under a declared rule*, *handed to a human*.

### Multi-goal, deliberately bounded

An episode may carry several related goals, switch between them, and park one while resolving another. The garden-centre customer wanting both advice and a replacement claim is the normal case, not an edge case.

The bounds, which matter as much as the capability: goals come **only** from the business's declared set; the agent may not invent a goal; one goal is active at a time, with parking and resumption both explicit; and there is **no decomposition of goals into agent-generated plans**. The purpose is conversational robustness, not autonomous planning. This is not a workflow engine.

### Resumable episodes, not customer memory

An unresolved episode can be resumed later with its state, evidence, specification version and relevant context intact. This follows directly from `pending`: a gym freeze awaiting a medical note, a brewery hold approaching expiry, a claim waiting on a specialist are all ordinary cases.

What this is **not**: general long-term customer memory, cross-episode profiling, or platform-initiated outreach. The unit is the episode, and it is resumable — resumption arriving as a further inbound interaction or an external system event, never as outreach the platform decided to start.

### Grounding has two tiers

- **Business-authoritative facts** — prices, policies, hours, availability, eligibility, what this business sells and promises. These **must** be grounded in declared, version-pinned sources. The agent may never invent one.
- **General domain knowledge** — how plants respond to overwatering, what a procedure involves generally. May come from the model, **must be marked as such** in the episode record, and is enabled or disabled per business as a declared risk.

### The guardrail and authority library

A **reusable library of generic behavioural constraints**, part of the core and applying to every agent:

- Do not invent business facts
- Do not act outside declared authority
- Do not perform undeclared actions
- Do not claim an action succeeded without evidence
- Escalate when required authority or evidence is unavailable

**Domain-specific safety or regulatory packs are optional extension points, never core architecture.** A dental practice may load a clinical-boundary pack; a business handling payments may load another. The core library is domain-neutral and sufficient on its own.

## The Business-Specific Specification

Per business, and nothing else:

- **Identity** — what the business is, how it speaks, what it will not say
- **Goals** — supported requests, and what resolving each means
- **Knowledge** — authoritative sources, **version-pinned**, with precedence when they conflict
- **Obligations** — what must be established before each outcome or action
- **Diagnostic inputs** — what helps the agent reason, without being required
- **Rules** — eligibility, pricing, timing, policy, constraints
- **Authorities** — what the agent may conclude, and on whose authority
- **Tools and actions** — what it may do, against which system, under what contract, with what success evidence
- **Guard conditions** — what overrides the ordinary path
- **Escalation policy** — what this business will not let an agent decide
- **Evaluation criteria** — what good looks like here

Knowledge sources are **pinned to versions, not referenced**. Without that, two agents can differ because of a revised leaflet while their specifications are identical, a specification diff explains nothing, and evaluation has no stable evidence base.

### The three-level variation contract

1. **Configuration / specification** handles normal variation — the expected path, covering the great majority of cases.
2. **A supported extension point** handles capability that recurs across businesses but is structurally unlike configuration — a leaf behind a declared contract: identity verification, document intake, derived figures, a domain safety pack, a tool implementation, a validator, a scorer.
3. **Custom implementation** handles genuinely novel capability, and is the exception, never the workflow.

Custom code may be a leaf. It may never be control flow — control flow stays in the specification, where it can be read, diffed, evaluated and reverted.

## The Builder's Role

In scope, deliberately minimal:

> **business conversation + source material → draft specification → validation and self-test → deployable instance**

Human review stays in the loop. The builder need not be an autonomous coding system; it needs to make a new agent fast enough that the generalisation claim is testable. Without it, this is a runtime plus an assertion that it can be configured.

Two consequences, both load-bearing:

**The specification must be a first-class, human-readable, diffable artifact.** Once the builder drafts it, a bad agent has two possible causes — a bad specification or a bad core — and only a reviewable specification lets anyone tell which.

**The builder's hard problem is elicitation, not generation.** The stress test found that the least-documented content is the most safety-critical: prohibitions, guard conditions, escalation thresholds and the operational rules (billing cut-offs, lead times, which exceptions are routinely granted) frequently exist in no document at all. The generic guardrail library covers the floor; everything above it must be extracted, with contradictions surfaced and gaps recorded as specification defects rather than guessed.

## What Makes This Not an FAQ or RAG Chatbot

The discriminator is **obligation**. This agent knows what must be true before a request can resolve, and will not resolve it until those obligations are met or explicitly waived. A document chatbot has no obligations, no authority model, no completion condition and no outcome.

Four things a retrieval chatbot cannot do:

1. **Hold an unfinished request open** — across turns, and across sessions — driving toward what is missing
2. **Refuse with a reason** drawn from the business's own rules, rather than failing to find an answer
3. **Change something in the world** through a bounded, contracted, verified action
4. **Close with a structured resolution** that can be evaluated, counted and audited

And the quality bar that is not a feature: **never state a fact about the business that does not come from the business's own version-pinned material.**

## Success Criteria

**Per episode**, computable from the record without a human reading it: reached a declared resolution or a legitimate pending state; every business fact traceable to a pinned source; obligations complete before any action; actions taken only through contracts, with confirmation where required and **evidence of success recorded**; no conclusion drawn outside a declared authority; guards fired when their conditions were met; escalation reason recorded; no policy violation.

**Per business:** share of inbound episodes resolved without a human; share reaching the intended action — reported separately from the share blocked by the business's own rules or capacity, because conflating them makes a business constraint look like an agent failure; human corrections per hundred episodes, and whether that falls over time.

**Per project:** the generalisation test below.

## The Minimum Generalisation Test

The four stress-test businesses, built in sequence. Three measurements each:

| Measurement | The thesis fails if |
| --- | --- |
| **Engine leaks** — every instance where the core had to change rather than the business layer, classified as *should have been configuration*, *justifies an extension point*, or *genuinely novel* | Leaks do not fall toward zero from the first business to the fourth |
| **Resolution-model strain** — whether any business needs a resolution family the model cannot express | Any business cannot be expressed, which would mean evaluation cannot be reusable |
| **Setup effort** — wall-clock time and number of source artifacts to a passing self-test | Effort does not fall materially across the sequence |

This needs no customers and no market, only real business material. It tests the architecture claim and should run before any commercial validation.

**For the usefulness claim**, a different test: take each business's *real* inbound requests — public enquiries, reviews, published FAQs, an operator's own inbox — and measure the share reaching a correct resolution without a human, with agent failures reported separately from business-constraint blocks. The share of episodes requiring obligations, rules or action rather than plain information is a measurement of this test, not a product metric — but if it is near zero, the demonstration proves nothing however good the other numbers look.

## Scope

**In, for the first version:**

- The reusable behavioural core, complete, including guard conditions, authority classes, obligations, contracted actions with verification, and the generic guardrail library
- The business specification model: human-readable, diffable, versioned, with version-pinned knowledge
- Episode lifecycle with pending and resumable episodes, separated from resolution and from action evidence
- Bounded multi-goal episodes with explicit parking and resumption
- The minimal builder: conversation and sources → draft specification → validation and self-test → deploy
- Grounded retrieval with the two-tier distinction enforced and recorded
- Durable structured episode evidence with stable episode identity
- Invariant evaluation checks plus per-business criteria
- The four generalisation businesses, with all three measurements recorded

**Out, explicitly:**

- Any vertical framing. Not a booking, appointment, healthcare, sales or FAQ product
- Platform-initiated outbound conversation. An episode is initiated or resumed only by an inbound interaction or an external system event; within such an episode the platform may reply and emit messages; it never independently starts an outbound conversation or episode
- Voice — a separate, already-proven project. Channel is an adapter; one channel ships for V1 and the core never learns which it is on
- Owning any system of record. External business systems stay authoritative
- Agent-generated planning or goal decomposition
- Long-term customer memory, cross-episode profiling, proactive outreach
- Continuous automatic learning. Behaviour changes are reviewed and promoted, never silently mutated
- Multi-tenant hosting, billing, onboarding automation, commercial packaging
- Domain-specific regulatory packs in V1 — the extension point exists; the packs do not

## Market Honesty

Recorded rather than written around, and explicitly not permitted to redirect the product:

- Every narrow inbound conversational job examined is already bundled by whoever owns the relevant system of record: appointment intake (ServiceTitan, Mindbody, Weave via the $35M TrueLark acquisition), lead qualification (Salesforce via the $1.2B Qualified acquisition, HubSpot, Intercom), legal intake (Clio Grow AI, launched 2026-08-20).
- The structural reason: the system-of-record owner controls the write API, owns distribution, holds the outcome data, and can price on outcome because it alone observes the outcome.
- Those incumbent features are adopted and growing, not shipped-and-dark — though both public vendors fence their agents to overflow and after-hours by default and expand "incrementally."
- Bundling has set the price: $99–199 per location per month inside software costing $400–600, or outcome pricing at $25 per converted lead.
- **No moat is claimed.** This is a technically substantial system built against a real problem. Commercial potential is unproven and probably modest for a solo builder, and the project is not justified by it.
- The public record here is contaminated — at least one vendor selling human staffing publishes fabricated AI-abandonment statistics — and no primary operator evidence was obtainable. **Two or three conversations with real small-business operators remain the only test of the problem statement, and of the gap between each business's printed policy and its practised one.** Nothing here substitutes for them.

## Open Architecture Questions

Product exploration is closed. These are the next stage:

| Question | Why it is architectural |
| --- | --- |
| **How should the runtime interpret the specification?** | Decides the generated-code versus shared-interpreter question, which the reviewable-specification requirement and the four-business cadence both pressure |
| **Where do deterministic primitives end and model-driven behaviour begin?** | The deterministic-first, LLM-on-escalation principle has to become a concrete boundary |
| **How are authority, evidence, state, tools and evaluation represented?** | Determines whether rules are declarative data or executable leaves, which decides who can author them and whether evaluation can reason about them |
| **What is configuration, what is an extension point, what is custom?** | The variation contract needs a mechanism, not just a policy |
| **The final resolution enumeration** | Deliberately deferred here; it follows from the runtime model |
| **Behaviour when the business's rules are silent** | Proposed: escalate, and record the gap as a specification defect. Never improvise a rule |
| **Retrieval architecture, model strategy, the V1 channel** | Grounding, tiering and channel-independence are requirements; the implementations are not decided |

---

*Derived from the brainstorming session of 2026-10-06/07 (`convergence.md`), three market-research strands of 2026-10-07, and the four-business specification stress test (`spec-stress-test.md`). Supporting depth in `addendum.md`. Full decision trail in `.memlog.md`.*
