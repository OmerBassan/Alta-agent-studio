---
title: "Product Extract — Brief: Agent Studio (2026-10-07)"
source: "_bmad-output/planning-artifacts/briefs/brief-AgentStudio-2026-10-07/brief.md"
purpose: "Product-level extraction feeding prd-AgentStudio-2026-10-08. Not architecture extraction."
created: 2026-10-08
---

# Product Extract — Brief: Agent Studio

Source read in full: `_bmad-output/planning-artifacts/briefs/brief-AgentStudio-2026-10-07/brief.md` (259 lines, status `final`).
Sibling files in the brief folder NOT in scope for this extract and therefore unread: `addendum.md` ("Supporting depth"), `spec-stress-test.md` (the four-business specification stress test). Both are cited by the brief as load-bearing evidence; several gaps noted below may be answered there.

A note on framing: the brief is written in the vocabulary of a **reusable behavioural core + per-business specification**, not in the vocabulary of "hiring an Agent." The PRD's product thesis ("easy for a small business to HIRE and configure") is **compatible with but not stated in** the brief — the brief's own framing is architectural-behavioural, and its explicit positioning is "The product is the machinery, not any one agent." Where the PRD's framing goes beyond the brief, that is flagged as a gap rather than silently harmonised.

---

## 1. Who it is for

**Stated target market:** "a reusable behavioural agent system for **small businesses**."

**Segments, by exemplar only.** The brief names four businesses that function as the working segment set and the generalisation test subjects:

> "A brewery on Tuesday, a dental practice on Saturday, a gym and a garden centre the week after — the same behavioural core each time."

| Business | The named real request | What it stresses |
| --- | --- | --- |
| Brewery | "I want to host a 40-person event next month." | "Negotiated multi-constraint planning; no slots, no practitioners" |
| Gym | "I want to freeze my membership for two months." | "Account state mutation under policy; recurring commitments" |
| Garden centre | "This plant I bought is dying. What should I do?" | "Diagnostic advice; ambiguous goal; a liability boundary" |
| Dental practice | "I was told I need a root canal. What happens?" | "High-stakes grounding; mandatory override; explanation, not transaction" |

The segment logic is **deliberate anti-vertical diversity**: "These are not one workflow with four skins."

**Who the end requester is:** referred to generically and only in role terms — "Someone brings a request"; "a person"; "the garden-centre customer"; "inbound requests." No demographic, no named end-user persona.

**The business side is referenced three ways**, all in passing, never as a drawn persona:
- "the owner's head" (as a location of undocumented knowledge)
- "an operator's own inbox" (as a source of real test requests)
- "**Two or three conversations with real small-business operators remain the only test of the problem statement**"
- "Human review stays in the loop" (the builder's reviewer) and "whether that falls over time" re: "human corrections per hundred episodes"

### GAPS — item 1
- **SILENT: definition of "small business."** No headcount, revenue, location-count or ticket-volume threshold anywhere. The only indirect sizing signal is competitive pricing framing: "$99–199 **per location** per month inside software costing $400–600" — implying a per-location SMB with existing vertical software.
- **SILENT: named personas.** No persona has a name, a day, a job title, or a goal statement. Closest thing to a user role set is {requester, owner/operator, reviewer-of-specification, human escalation target} — all implied, none defined.
- **SILENT: buyer vs user distinction.** Never drawn. The brief does not say who pays, who configures, who reviews the specification, or whether these are the same person. Given "Multi-tenant hosting, billing, onboarding automation, commercial packaging" are explicitly OUT of V1, the brief arguably has no buyer yet by design.
- **SILENT: geography, language, regulatory jurisdiction.**

---

## 2. Problem and pain

**The problem statement, verbatim:**

> "Small businesses answer the same requests endlessly, and the knowledge needed to answer them well already exists — in a price list, a policy, a care guide, a membership agreement, the owner's head. What does not exist is anything that can hold the conversation and act on that material."

**The root-cause formulation (bolded in source):**

> "**a small business's rules and knowledge are not in a form anything can act on**, so every inbound request consumes human attention from scratch."

**Why each existing coping strategy fails — "Each coping strategy fails specifically":**

> "A person answers when they can and misses the rest, concentrating failure after hours and at peak. A web form captures a fraction of what is needed and begins a round of clarifying messages. A scripted chatbot deflects to a link. An answering service takes a message but cannot apply the business's rules. A document-retrieval chatbot answers questions but cannot *do* anything, so every request needing an action still reaches a person."

Note the pattern: five named alternatives, each with a **distinct** failure mode (coverage / completeness / deflection / no rule application / no action). This maps cleanly to a PRD "why existing options fail" table.

**A second pain, discovered rather than assumed** — the documentation gap:

> "the least-documented content is the most safety-critical: prohibitions, guard conditions, escalation thresholds and the operational rules (billing cut-offs, lead times, which exceptions are routinely granted) frequently exist in no document at all."

And the related operator-truth pain: "the gap between each business's printed policy and its practised one."

### GAPS — item 2
- **SILENT: any quantified pain.** No missed-call rate, no response-time data, no lost-revenue figure, no hours-per-week. This is deliberate and stated: "The public record here is contaminated — at least one vendor selling human staffing publishes **fabricated** AI-abandonment statistics — and **no primary operator evidence was obtainable**." The brief refuses to quantify rather than failing to.
- **SILENT: episode/request volume per business.** Nothing on how many inbound requests a target business handles, which is the natural denominator for every "share of episodes" metric in Success Criteria.

---

## 3. Product thesis / positioning / differentiation

**The thesis, closest single statement:**

> "The product is the machinery, not any one agent."

**The full product sentence (Executive Summary):**

> "Given a short conversation about a business and a few of its own documents, it produces a versioned specification, validates it, and deploys an agent that handles that business's inbound requests. The agent works out what the person is trying to accomplish, obtains what it still needs, grounds every business fact in the business's own material, concludes only what the business has authorised, acts only through declared contracts, escalates what it may not decide, and closes with a structured outcome it can be judged on."

**The central discipline — the single most quotable positioning line:**

> "**Reasoning is broad; authority is bounded.** The agent may think widely about a request. What it may *conclude*, and what it may *do*, are narrow and declared. That asymmetry is the product's central discipline, and the verification link keeps it honest — an agent may never report that something happened without evidence that it did."

This is the brief's own rendering of the control model the PRD states as "Agent decides what to do; Core constrains, validates, authorizes, executes, observes, persists." **It is consistent**, with one nuance the PRD framing can lose: the brief bounds not only *action* but *conclusion* — "Which conclusions the agent may draw, under which authority, from which evidence."

**Two claims explicitly under test** (the brief treats the product as a hypothesis, not a plan):

> "1. **The architecture claim.** Can one behavioural core handle materially different small-business requests while only the business layer changes?
> 2. **The usefulness claim.** Does that core resolve a meaningful class of inbound requests well enough that the resulting agents are useful, not merely technically impressive?"

Current evidence status, stated plainly: "A four-business specification stress test ... has established that the specification can **express** four businesses sharing no workflow. What it has not established is that it can **drive behaviour**."

**Differentiation — the discriminator is a single word:**

> "The discriminator is **obligation**. This agent knows what must be true before a request can resolve, and will not resolve it until those obligations are met or explicitly waived. A document chatbot has no obligations, no authority model, no completion condition and no outcome."

**"Four things a retrieval chatbot cannot do"** (verbatim list):
1. "**Hold an unfinished request open** — across turns, and across sessions — driving toward what is missing"
2. "**Refuse with a reason** drawn from the business's own rules, rather than failing to find an answer"
3. "**Change something in the world** through a bounded, contracted, verified action"
4. "**Close with a structured resolution** that can be evaluated, counted and audited"

**The quality bar stated as positioning, not feature:**

> "And the quality bar that is not a feature: **never state a fact about the business that does not come from the business's own version-pinned material.**"

### Anti-positioning — what it refuses to be (all verbatim)

- "**This is not a workflow engine.**"
- "Not a booking, appointment, healthcare, sales or FAQ product" — and more broadly, OUT: "**Any vertical framing.**"
- "What this is **not**: general long-term customer memory, cross-episode profiling, or platform-initiated outreach."
- "The purpose is conversational robustness, **not autonomous planning**." / "there is **no decomposition of goals into agent-generated plans**"
- "**Domain-specific safety or regulatory packs are optional extension points, never core architecture.**"
- "Custom code may be a leaf. It may **never** be control flow."
- Not a system of record: "Owning any system of record. External business systems stay authoritative."
- Not continuously self-modifying: "Continuous automatic learning. Behaviour changes are reviewed and promoted, never silently mutated."
- Not a template library — implied by the anti-vertical and the anti-workflow stance, but note: **the phrase "template library" does not appear in the brief.** The PRD's third anti-position is an extension.

### Competitor framing ("Market Honesty" — unusually candid, must not be softened)

> "Every narrow inbound conversational job examined is already bundled by whoever owns the relevant system of record: appointment intake (ServiceTitan, Mindbody, Weave via the $35M TrueLark acquisition), lead qualification (Salesforce via the $1.2B Qualified acquisition, HubSpot, Intercom), legal intake (Clio Grow AI, launched 2026-08-20)."

> "The structural reason: the system-of-record owner controls the write API, owns distribution, holds the outcome data, and can price on outcome because it alone observes the outcome."

> "Those incumbent features are adopted and growing, not shipped-and-dark — though both public vendors fence their agents to overflow and after-hours by default and expand 'incrementally.'"

> "Bundling has set the price: $99–199 per location per month inside software costing $400–600, or outcome pricing at $25 per converted lead."

> "**No moat is claimed.** This is a technically substantial system built against a real problem. Commercial potential is unproven and probably modest for a solo builder, and the project is not justified by it."

Critically, the market section carries a **guardrail on the PRD itself**: "The market evidence is recorded under *Market Honesty* and is deliberately **not permitted to steer the product toward hunting an unoccupied vertical**." / "Recorded rather than written around, and explicitly not permitted to redirect the product."

The incumbents' self-limiting default ("fenced to overflow and after-hours") is the one latent wedge the brief surfaces without claiming.

---

## 4. The Builder / onboarding experience

**The whole builder, as one arrow (verbatim, blockquoted in source):**

> **business conversation + source material → draft specification → validation and self-test → deployable instance**

Scope posture: "**In scope, deliberately minimal.**"

**What the business provides:** "a short conversation about a business and a few of its own documents." Named source types elsewhere: "a price list, a policy, a care guide, a membership agreement, the owner's head"; and for the usefulness test "public enquiries, reviews, published FAQs, an operator's own inbox."

**What it produces:** a **versioned, human-readable, diffable specification**, then a validated, self-tested, deployed instance.

> "**The specification must be a first-class, human-readable, diffable artifact.** Once the builder drafts it, a bad agent has two possible causes — a bad specification or a bad core — and only a reviewable specification lets anyone tell which."

**Human review is in the loop, and the builder is deliberately not ambitious:**

> "Human review stays in the loop. The builder need not be an autonomous coding system; it needs to make a new agent fast enough that the generalisation claim is testable. Without it, this is a runtime plus an assertion that it can be configured."

**The builder's hard problem — stated as the central product risk of this surface:**

> "**The builder's hard problem is elicitation, not generation.**"
> "The generic guardrail library covers the floor; everything above it must be extracted, with **contradictions surfaced and gaps recorded as specification defects rather than guessed.**"

This gives the onboarding experience a defined behavioural stance: it **interrogates**, it **surfaces contradiction**, and it **records a gap as a defect** rather than inventing a default. (See also Open Questions: "Behaviour when the business's rules are silent — Proposed: escalate, and record the gap as a specification defect. **Never improvise a rule.**")

**The gate:** "validation and self-test" — a "passing self-test" is the stated unit of done for a built business.

### Time-to-value
- **No absolute time-to-value is stated.** What exists instead is a **relative** criterion: "**Setup effort** — wall-clock time and number of source artifacts to a passing self-test," failing if "Effort does not fall materially across the sequence" of four businesses. The brief commits to *measuring and reducing* setup effort, not to a number.
- Also relative: "fast enough that the generalisation claim is testable."

### GAPS — item 4
- **SILENT: what the builder experience feels like.** No UI, no screens, no number of questions, no session length, no who-sits-in-the-chair. "A short conversation" is the entire experiential description.
- **SILENT: who does the human review**, with what competence, and what a review verdict does.
- **SILENT: editing after launch via the builder** — whether re-specification is a conversation, a diff review, or a file edit. The specification is required to be diffable, but no re-build/re-deploy loop is described.
- **SILENT: any acceptance/preview step** where the owner tries the agent before it goes live.

---

## 5. What a business-specific Agent can DO

**The generic interaction pattern, named:** "**Request → Resolution**" — "Someone brings a request. The agent carries it to a resolution."

**The behavioural chain (the core of the product, verbatim blockquote):**

> **goal → information gathering → reasoning / decision → allowed action → verification → outcome**

With what the specification constrains at each link:

| Link | Constraint (verbatim) |
| --- | --- |
| Goal | "Which goals exist; what completing each one means; what may never become a goal" |
| Information gathering | "The obligations for each goal; what may be asked; what must never be asked" |
| Reasoning / decision | "Which conclusions the agent may draw, under which authority, from which evidence" |
| Allowed action | "Which actions exist, their preconditions, their contracts, and which require explicit confirmation" |
| Verification | "What evidence proves an action succeeded, and what happens when that evidence is absent" |
| Outcome | "Which resolutions are permissible for a goal, and what must be recorded" |

"The specification's job is to **constrain each link**, not to describe the data sitting around it." — this is the brief's direct support for the PRD's "Business Specification supplies context/policies/capabilities/boundaries, NOT a per-business execution graph."

**Capability primitives of the reusable core** ("Built once, never per business"): goal set with completion conditions ("Not utterance classification"); guard conditions; obligation tracking; diagnostic evidence gathering; grounded claim; rule evaluation ("Declared predicates over collected information **and live external reads**"); decision authority classes; contracted action ("Propose, validate against contract, confirm, execute, obtain evidence of success"); escalation with reason class; episode lifecycle; resolution record; episode evidence; evaluation.

**Four example tasks it must handle** — the brewery 40-person event, the gym two-month freeze, the dying plant, the root-canal explanation (table in item 1). Note the deliberate spread: one negotiation, one state mutation, one diagnosis, one explanation.

**Multi-goal competence, bounded:**

> "An episode may carry several related goals, switch between them, and park one while resolving another. The garden-centre customer wanting both advice and a replacement claim is **the normal case, not an edge case**."

> "The bounds, which matter as much as the capability: goals come **only** from the business's declared set; the agent may not invent a goal; one goal is active at a time, with parking and resumption both explicit; and there is **no decomposition of goals into agent-generated plans**."

**Resumability:**

> "An unresolved episode can be resumed later with its state, evidence, specification version and relevant context intact." — "a gym freeze awaiting a medical note, a brewery hold approaching expiry, a claim waiting on a specialist are all ordinary cases."
> "resumption arriving as a further inbound interaction or an external system event, **never as outreach the platform decided to start**."

### Boundaries of competence (the honest limits)

**Two knowledge tiers:**
- "**Business-authoritative facts** — prices, policies, hours, availability, eligibility, what this business sells and promises. These **must** be grounded in declared, version-pinned sources. The agent may never invent one."
- "**General domain knowledge** — how plants respond to overwatering, what a procedure involves generally. May come from the model, **must be marked as such** in the episode record, and is enabled or disabled per business as a declared risk."

**The guardrail and authority library** — "A **reusable library of generic behavioural constraints**, part of the core and applying to every agent":
> - "Do not invent business facts
> - Do not act outside declared authority
> - Do not perform undeclared actions
> - Do not claim an action succeeded without evidence
> - Escalate when required authority or evidence is unavailable"

**Guard conditions override everything before goal pursuit:** "Declared conditions that override the ordinary conversational path *before* goal pursuit, and may end the episode regardless of what was asked." Candidate generic families: "**urgency**, **authorisation failure**, **policy violation**, **unsupported request**, **identity problem**, and any other declared guard." — "The primitive is the override capability, not any one domain's use of it."

**Three orthogonal dimensions that must not be conflated** (the stress test found one enum doing three jobs):
- Episode lifecycle: `active` / `pending` ("awaiting a named external input, with a deadline") / `closed`. "Lifecycle says nothing about whether the business got a good outcome."
- Business resolution: "recorded at close: whether the person's goal was served, on whose authority, and what evidence supports it."
- Action evidence: "**An action record is evidence that something happened, not a resolution.**"

---

## 6. The end-user Agent experience

**Who talks to the Agent:** the inbound requester — "Someone brings a request." Always inbound, never solicited.

**Channel — the single most load-bearing product statement here:**

> "Voice — a separate, already-proven project. **Channel is an adapter; one channel ships for V1 and the core never learns which it is on.**"

Channel-independence is therefore a *requirement*; the channel itself is undecided and listed as an open architecture question: "Retrieval architecture, model strategy, **the V1 channel** ... the implementations are not decided."

**Initiation rule, stated as hard scope:**

> "Platform-initiated outbound conversation. An episode is initiated or resumed only by an inbound interaction or an external system event; within such an episode the platform may reply and emit messages; it never independently starts an outbound conversation or episode."

**What the interaction is like, as far as stated:** multi-turn and cross-session ("Hold an unfinished request open — across turns, and across sessions — driving toward what is missing"); it asks for what is missing within declared limits ("what may be asked; what must never be asked"); it confirms before certain actions ("which require explicit confirmation"); it can refuse with a reason from the business's own rules; it can hand off to a human with a reason class; it closes with a resolution.

### GAPS — item 6
- **SILENT: the V1 channel identity.** Open question.
- **SILENT: conversational experience design.** No turn latency target, no response style, no greeting, no identity disclosure ("is the customer told it is an AI?"), no handoff experience from the requester's side, no what-the-requester-sees when an episode goes `pending` or is resumed days later.
- **SILENT: authentication/identity from the requester's side**, beyond "identity problem" existing as a guard family and "identity verification" as an extension point.
- **SILENT: accessibility, language, localisation.**

---

## 7. What business owners configure / manage post-launch

**What a business supplies — "Per business, and nothing else"** (the eleven specification surfaces, verbatim):

> - "**Identity** — what the business is, how it speaks, what it will not say
> - **Goals** — supported requests, and what resolving each means
> - **Knowledge** — authoritative sources, **version-pinned**, with precedence when they conflict
> - **Obligations** — what must be established before each outcome or action
> - **Diagnostic inputs** — what helps the agent reason, without being required
> - **Rules** — eligibility, pricing, timing, policy, constraints
> - **Authorities** — what the agent may conclude, and on whose authority
> - **Tools and actions** — what it may do, against which system, under what contract, with what success evidence
> - **Guard conditions** — what overrides the ordinary path
> - **Escalation policy** — what this business will not let an agent decide
> - **Evaluation criteria** — what good looks like here"

Note "Escalation policy — **what this business will not let an agent decide**" — the owner's authority dial, stated in the owner's own voice.

**Version pinning as an owner-facing discipline:**

> "Knowledge sources are **pinned to versions, not referenced**. Without that, two agents can differ because of a revised leaflet while their specifications are identical, a specification diff explains nothing, and evaluation has no stable evidence base."

**The three-level variation contract** (how change gets made at all):
1. "**Configuration / specification** handles normal variation — the expected path, covering the great majority of cases."
2. "**A supported extension point** handles capability that recurs across businesses but is structurally unlike configuration — a leaf behind a declared contract: identity verification, document intake, derived figures, a domain safety pack, a tool implementation, a validator, a scorer."
3. "**Custom implementation** handles genuinely novel capability, and is the exception, never the workflow."

**Change control:** "Behaviour changes are reviewed and promoted, never silently mutated." Control flow "stays in the specification, where it can be **read, diffed, evaluated and reverted**."

**Observability from the owner's seat — the episode record:**

> "**Episode evidence** | A durable structured record: turns, retrievals, decisions, actions, authorities exercised, errors, timings"

Plus "stable episode identity," "escalation reason recorded," and per-business metrics (item 9). Evaluation is "Invariant checks plus the business's declared criteria."

**Approvals:** two mechanisms exist — per-action "explicit confirmation" (requester-facing) and escalation policy (human-facing). 

### GAPS — item 7
- **SILENT: the owner's interface.** No dashboard, console, inbox, alerting, review queue, or report is described. "A durable structured record" and "computable from the record without a human reading it" are the only artefacts — notably framed as machine-readable, with no stated human view.
- **SILENT: the escalation receiving end.** Where a handed-off episode lands, who is notified, how, with what SLA.
- **SILENT: who may edit the specification post-launch**, how a change is promoted (the word "promoted" appears with no mechanism), and whether revert is self-service.
- **SILENT: multi-user / roles / permissions on the owner side** — consistent with multi-tenancy being out of V1.

---

## 8. V1 scope signals

**In, for the first version (verbatim list):**

> - "The reusable behavioural core, complete, including guard conditions, authority classes, obligations, contracted actions with verification, and the generic guardrail library
> - The business specification model: human-readable, diffable, versioned, with version-pinned knowledge
> - Episode lifecycle with pending and resumable episodes, separated from resolution and from action evidence
> - Bounded multi-goal episodes with explicit parking and resumption
> - The minimal builder: conversation and sources → draft specification → validation and self-test → deploy
> - Grounded retrieval with the two-tier distinction enforced and recorded
> - Durable structured episode evidence with stable episode identity
> - Invariant evaluation checks plus per-business criteria
> - The four generalisation businesses, with all three measurements recorded"

**Out, explicitly (verbatim list):**

> - "Any vertical framing. Not a booking, appointment, healthcare, sales or FAQ product
> - Platform-initiated outbound conversation. [...] it never independently starts an outbound conversation or episode
> - Voice — a separate, already-proven project. Channel is an adapter; one channel ships for V1 and the core never learns which it is on
> - Owning any system of record. External business systems stay authoritative
> - Agent-generated planning or goal decomposition
> - Long-term customer memory, cross-episode profiling, proactive outreach
> - Continuous automatic learning. Behaviour changes are reviewed and promoted, never silently mutated
> - Multi-tenant hosting, billing, onboarding automation, commercial packaging
> - Domain-specific regulatory packs in V1 — the extension point exists; the packs do not"

**Deferred rather than excluded:**
- "**Resolution families are deliberately not fixed as a final enum in this brief.** The shape is settled — every resolution carries *whether the goal was served*, *under what authority*, and *on what evidence* — and the enumeration is an architecture decision, made once the runtime model is clear. Candidate families, provisional: *served with information*, *served with action*, *declined under a declared rule*, *handed to a human*."
- Guard families are likewise "Candidate guard families, declared per business."
- "Product exploration is closed" — the seven open items in item 11 are explicitly next-stage architecture, not open scope.

**Note a scope tension worth carrying into the PRD:** V1 includes "the four generalisation businesses, with all three measurements recorded" — i.e. the V1 deliverable is **the system plus its own proof**, which is an unusual shape for a PRD scope line and should not be quietly dropped as "not product."

---

## 9. Success criteria / metrics / measurable outcomes

**Per episode** — "computable from the record without a human reading it" (verbatim):

> "reached a declared resolution or a legitimate pending state; every business fact traceable to a pinned source; obligations complete before any action; actions taken only through contracts, with confirmation where required and **evidence of success recorded**; no conclusion drawn outside a declared authority; guards fired when their conditions were met; escalation reason recorded; no policy violation."

**Per business:**

> "share of inbound episodes resolved without a human; share reaching the intended action — **reported separately from the share blocked by the business's own rules or capacity, because conflating them makes a business constraint look like an agent failure**; human corrections per hundred episodes, and whether that falls over time."

**Per project — the Minimum Generalisation Test**, with explicit falsification conditions:

| Measurement (verbatim) | "The thesis fails if" |
| --- | --- |
| "**Engine leaks** — every instance where the core had to change rather than the business layer, classified as *should have been configuration*, *justifies an extension point*, or *genuinely novel*" | "Leaks do not fall toward zero from the first business to the fourth" |
| "**Resolution-model strain** — whether any business needs a resolution family the model cannot express" | "Any business cannot be expressed, which would mean evaluation cannot be reusable" |
| "**Setup effort** — wall-clock time and number of source artifacts to a passing self-test" | "Effort does not fall materially across the sequence" |

> "This needs no customers and no market, only real business material. It tests the architecture claim and **should run before any commercial validation**."

**The usefulness test, separately:**

> "take each business's *real* inbound requests — public enquiries, reviews, published FAQs, an operator's own inbox — and measure the share reaching a correct resolution without a human, with agent failures reported separately from business-constraint blocks."

### Counter-metrics and anti-gaming guards (important; easy to lose in an FR table)
- **Separation of agent failure from business constraint** — stated twice, with the reason given both times.
- **A validity floor, explicitly not a product metric:** "The share of episodes requiring obligations, rules or action rather than plain information is a measurement of this test, not a product metric — but **if it is near zero, the demonstration proves nothing however good the other numbers look.**" (i.e. a high resolution rate achieved only on information-only requests is a failed demonstration.)
- **Lifecycle must not be read as success:** "Lifecycle says nothing about whether the business got a good outcome"; "A single episode may resolve well after being pending for days." (So `pending` is not a failure, and `closed` is not a win.)
- **Action evidence must not be read as resolution:** "An applied membership freeze produces both, and they are not the same fact."
- **Trend, not snapshot:** "human corrections per hundred episodes, **and whether that falls over time**."

### GAPS — item 9
- **SILENT: every numeric target.** Not one threshold, baseline or goal value appears — no target resolution share, no acceptable correction rate, no setup-time target. All criteria are structural or directional.
- **SILENT: requester-side satisfaction** of any kind (CSAT, sentiment, abandonment). Every metric is computed from the episode record; none asks the person how it went.
- **SILENT: cost or unit-economics metrics.**

---

## 10. Constraints and non-functional expectations (product level)

**Trust / truthfulness — the hardest constraint in the brief, stated three ways:**
- "**never state a fact about the business that does not come from the business's own version-pinned material.**"
- "an agent may never report that something happened without evidence that it did."
- "The agent may never invent one [a business-authoritative fact]."

**Safety / authority:** the five-line guardrail library (item 5) applies to every agent; escalation is mandatory "when required authority or evidence is unavailable"; guard conditions can "end the episode regardless of what was asked"; "Behaviour when the business's rules are silent — Proposed: escalate... **Never improvise a rule.**"

**Auditability / governance:** "A durable structured record: turns, retrievals, decisions, actions, authorities exercised, errors, timings," with "stable episode identity"; general-model knowledge "**must be marked as such** in the episode record"; version-pinned knowledge so "a specification diff" explains behaviour change; specification is "read, diffed, evaluated and reverted."

**Data governance:** "Owning any system of record" is out — "**External business systems stay authoritative.**" Out also: "Long-term customer memory, cross-episode profiling." Durability is in: episodes persist and resume "with its state, evidence, specification version and relevant context intact."

**Change safety:** "Behaviour changes are reviewed and promoted, never silently mutated." "Custom code may be a leaf. It may never be control flow."

**Architectural constraint with product consequence:** "the core never learns which [channel] it is on."

**Compliance:** addressed only as a deferred extension point — "A dental practice may load a clinical-boundary pack; a business handling payments may load another," with "Domain-specific regulatory packs in V1 — the extension point exists; the packs do not." The dental case is flagged as carrying "mandatory override," and the garden centre as carrying "a liability boundary," but no regulation is named.

### GAPS — item 10
- **SILENT: latency.** No response-time budget, no dead-air requirement, no turn-latency target. Notable because the repo's shipped voice project treats latency as correctness — but voice is explicitly out of scope here, and the brief inherits none of that discipline. If the PRD wants a latency NFR it must originate it.
- **SILENT: cost.** No per-episode cost ceiling, no token budget, no model-spend constraint. (The only cost figures in the brief are competitors' prices.)
- **SILENT: availability, throughput, concurrency, scale.** No uptime target, no episodes-per-minute, no concurrent-episode expectation.
- **SILENT: PII handling, retention periods, deletion, residency, consent** — despite durable records of customer conversations being core, and despite a dental practice being business #4.
- **SILENT: security** — authn/authz for tool execution beyond "declared contract," secret handling, tenant isolation (consistent with multi-tenancy out).
- **SILENT: named compliance regimes** (GDPR, HIPAA, PCI) — none appear.

---

## 11. Open questions, assumptions, unresolved tensions (the brief's own flags)

**"Open Architecture Questions"** — prefaced "Product exploration is closed. These are the next stage." (verbatim):

| Question | "Why it is architectural" |
| --- | --- |
| "How should the runtime interpret the specification?" | "Decides the generated-code versus shared-interpreter question, which the reviewable-specification requirement and the four-business cadence both pressure" |
| "Where do deterministic primitives end and model-driven behaviour begin?" | "The deterministic-first, LLM-on-escalation principle has to become a concrete boundary" |
| "How are authority, evidence, state, tools and evaluation represented?" | "Determines whether rules are declarative data or executable leaves, which decides who can author them and whether evaluation can reason about them" |
| "What is configuration, what is an extension point, what is custom?" | "The variation contract needs a mechanism, not just a policy" |
| "The final resolution enumeration" | "Deliberately deferred here; it follows from the runtime model" |
| "Behaviour when the business's rules are silent" | "Proposed: escalate, and record the gap as a specification defect. Never improvise a rule" |
| "Retrieval architecture, model strategy, the V1 channel" | "Grounding, tiering and channel-independence are requirements; the implementations are not decided" |

Note "**deterministic-first, LLM-on-escalation**" — a stated principle appearing only here, with no elaboration, and in some tension with the PRD's "Agent decides what to do." Worth resolving explicitly in the PRD.

**Unproven claims the brief itself flags:**
- "What it has not established is that it can **drive behaviour**" (the stress test proved expressibility only).
- Both the architecture claim and the usefulness claim are "under test."
- "Commercial potential is unproven and probably modest for a solo builder, and the project is not justified by it."

**Evidence gaps the brief flags:**
- "no primary operator evidence was obtainable"; "The public record here is contaminated."
- "**Two or three conversations with real small-business operators remain the only test of the problem statement, and of the gap between each business's printed policy and its practised one.** Nothing here substitutes for them." — an outstanding research action, not a question.

**Unresolved tensions worth naming for the PRD:**
1. **Minimal builder vs. elicitation being the hard problem.** The builder is scoped "deliberately minimal" while the brief simultaneously says its hard problem (extracting undocumented prohibitions, thresholds, practised-vs-printed rules) is the safety-critical one. Those two statements pull apart.
2. **Broad reasoning vs. deterministic-first.** "The agent may think widely" vs. "deterministic-first, LLM-on-escalation."
3. **Specification as readable artefact vs. who reads it.** It must be human-readable and diffable, yet no human reviewer persona or review surface exists.
4. **Market honesty vs. building anyway.** The brief records that every narrow inbound job is bundled by system-of-record owners with structural advantages, claims no moat, and proceeds — with an explicit rule against letting that evidence redirect the product.
5. **V1 includes its own proof.** Four businesses + three measurements are in V1 scope, blurring product scope and validation programme.

---

## 12. Qualitative / experiential intent

This is the thinnest of the twelve items and the gap is material: **the brief has an unmistakable voice but states almost no intended product voice.**

**The one direct statement of agent voice** — a single specification field:

> "**Identity** — what the business is, **how it speaks, what it will not say**"

i.e. tone is per-business configuration, deliberately not a platform-level brand character. Nothing in the brief tells us what the platform's own default voice is, or what a well-tuned agent sounds like.

**Experiential intent inferable from behaviour statements** (kept verbatim, since the feel lives in the wording):
- Persistent and purposeful rather than deflecting: "**Hold an unfinished request open** — across turns, and across sessions — **driving toward what is missing**."
- Honest refusal as a feature of character: "**Refuse with a reason** drawn from the business's own rules, rather than failing to find an answer."
- Consequential, not advisory: "**Change something in the world** through a bounded, contracted, verified action."
- Accountable by design: closes "with a structured outcome **it can be judged on**."
- Confident thinking, humble authority: "**Reasoning is broad; authority is bounded.**"
- Never bluffing: "an agent may never report that something happened without evidence that it did."
- Normalising the messy case rather than treating it as an edge: "The garden-centre customer wanting both advice and a replacement claim is **the normal case, not an edge case**."

**The brief's own brand character — worth preserving in PRD tone**, since it is the project's working ethic: anti-hype, falsifiable, self-auditing. Representative: "**No moat is claimed.**" / "Recorded rather than written around." / "This is a technically substantial system built against a real problem." / "resolve a meaningful class of inbound requests well enough that the resulting agents are useful, **not merely technically impressive**." / "Without it, this is a runtime plus an assertion that it can be configured."

### GAPS — item 12
- **SILENT: any "it should feel like X" statement.** None exists. No metaphor for the product (no "like hiring a…", no "like a new employee"), which is notable given the PRD's "easy to HIRE" thesis — that metaphor is the PRD's, not the brief's.
- **SILENT: platform-level default tone**, persona naming, humour, formality, verbosity.
- **SILENT: the builder conversation's feel** — whether it is an interview, a wizard, a consultant. Only "a short conversation."
- **SILENT: visual/brand identity entirely.**

---

## Summary of silences (consolidated)

| # | Item | Status |
| --- | --- | --- |
| 1 | Who it is for | Partial — segments by exemplar; **no "small business" definition, no named personas, no buyer/user split** |
| 2 | Problem and pain | Strong qualitatively; **no quantified pain, by stated choice (contaminated sources)** |
| 3 | Thesis / positioning / anti-positioning | Strong; "template library" anti-position absent; PRD's "hire" framing not in brief |
| 4 | Builder / onboarding | Process defined; **experience, UI, reviewer and absolute time-to-value absent** |
| 5 | Agent capability | Strong — the brief's centre of gravity |
| 6 | End-user experience | Rules defined; **channel undecided, conversational UX absent** |
| 7 | Owner post-launch controls | Configuration surfaces strong; **no owner-facing interface, no escalation destination, no promote/revert mechanism** |
| 8 | V1 scope | Strong — explicit in/out lists plus named deferrals |
| 9 | Metrics | Strong structurally, with real counter-metrics; **zero numeric targets, no requester satisfaction, no cost** |
| 10 | Constraints / NFRs | Trust, safety, audit, governance strong; **latency, cost, scale, availability, PII/retention, security, named compliance all absent** |
| 11 | Open questions | Strong and explicit (seven architectural + flagged evidence gaps) |
| 12 | Qualitative / experiential intent | **Weakest** — tone is per-business config only; no platform voice, no feel statement, no metaphor |
