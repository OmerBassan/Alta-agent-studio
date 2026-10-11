---
title: "Agent Studio — Brief Addendum (supporting evidence and reasoning)"
status: compiled
created: 2026-10-07
updated: 2026-10-07
---

# Agent Studio — Brief Addendum

Companion to `brief.md`. The brief states conclusions; this file holds the evidence, the
rejected alternatives and the reasoning behind them. It deliberately does not restate the
brief. Compiled from two sources only: `.memlog.md` (this brief's decision log, 65 entries,
2026-10-07) and `../../../brainstorming/brainstorm-agent-studio-product-architecture-2026-10-06/convergence.md`
(the prior session's 9-section convergence document, itself derived from that memlog at 91 entries; a 92nd synthesis entry was appended afterwards).

**Label discipline**, carried from both sources and preserved:

| Label | Meaning |
| --- | --- |
| **FACT** | Verified by reading the repository or a cited document; several cite file:line |
| **INTERPRETATION** | A defensible reading of those facts; not proven |
| **HYPOTHESIS** | An unproven bet |
| **VERIFIED** | Confirmed in a primary or near-primary source named in the memlog |
| **INFERRED** | Assembled by the researcher from indirect evidence |
| **UNVERIFIED** | Explicitly could not be confirmed; load-bearing where marked |

Where a figure is vendor marketing, the caveat travels with the figure. Figures are
reproduced exactly as the memlog records them; nothing is rounded or re-expressed.

---

## 1. Market evidence

Three research strands, all run by subagents over the web on **2026-10-07**. Strand 1:
the appointment-intake landscape, API feasibility, economics, channel and compliance.
Strand 2: the two alternative candidate jobs (inbound lead qualification, legal client
intake). Strand 3: the hinge question — whether the incumbents' shipped AI features are
actually adopted.

### 1.1 The appointment-intake landscape and the TrueLark/Weave acquisition

The headline finding is that the proposed product already existed under another name.

**TrueLark** — described as an "AI virtual receptionist for appointment-based SMBs,
scheduling/rescheduling/inquiries via SMS and web chat", which the memlog records as
*verbatim the proposal*. Acquired by **Weave (NYSE:WEAV)** for **$35M**, announced
**2025-05-05**, closed **2025-05-20**. Now sold as **Weave AI Receptionist**, integrating
**Dentrix / Eaglesoft / Open Dental**. TrueLark's verticals were dental, medical/aesthetics,
salon/spa, fitness.

Incumbents have already shipped text AI booking in **4 of 6** target verticals:

| Vendor | Vertical | Shipped capability | Pricing as recorded |
| --- | --- | --- | --- |
| **ServiceTitan** | Trades | Virtual Agent Inbound SMS — classifies booking intent, converses, checks capacity, books autonomously; GA US + Canada | not recorded |
| **Mindbody Messenger[ai]** | Salon/spa | Conversational booking over SMS / web chat / Facebook, since the **2019 Bowtie acquisition** | published **$99–199/location/month** |
| **Weave / TrueLark** | Dental, medical, med-spa | AI Receptionist (see above) | not recorded |
| **Zenoti** | Salon, med-spa | Voice-first; **text unverified** | not recorded |
| **Podium AI Employee** | Home services | AI employee | **$399–599/mo** core |
| **Boulevard** | Salon | **Not yet shipped** | — |
| **Jane App** | Physio/allied health | 2026 AI work is **scribe/charting, not booking** | — |

### 1.2 Per-vertical booking-API feasibility

This strand kills the horizontal thesis independently of competition: the write path to the
calendar is not uniformly available.

| Vertical | System of record / path | Status |
| --- | --- | --- |
| Dental | **NexHealth Synchronizer** — unified read/write across **Dentrix G6.2+ / Eaglesoft / Open Dental**, **8000+ locations** | CLEAN but **gated behind the Partner Program**; commercial terms **UNVERIFIED and load-bearing** |
| Dental | **Open Dental** own API | CLEAN |
| Physio | **Cliniko** — self-serve dev portal, Available Time + appointment write | CLEAN |
| Trades | **ServiceTitan** dev portal | CLEAN, but ServiceTitan now **competes directly** |
| Salon/spa | **Fresha** (largest by salon count) | **NO write API**; read-only BI connector only |
| Salon/spa | **Mindbody** | Gated partner program + **metered Consumer Bookings approx $15/location + $2.50 per appointment booked** (third-party figure, not vendor-published) |
| Allied health | **Jane App** | **No official public API** |
| Veterinary | **ezyVet/IDEXX, Cornerstone, Covetrus** — all major vet PMS | Partner-gated and **UNVERIFIED**; **Vetstoria** already occupies the booking-integration slot across **30+ PMSs** |
| Generic | **Square Appointments** | Write requires the merchant on **Plus/Premium**; approx **6 countries** |

### 1.3 Economics, with the vendor-marketing caveats

- The AI text layer is **already priced at $99–199/location/month**, bundled inside software
  the business already pays **$400–600/month** for. That is the ceiling, and it is set by
  incumbents who bundle.
- Human comparables: answering services **$100–400/mo** (overage **$0.75–1.50/min**);
  virtual receptionists **$165–2100/mo**.
- **Unusable — vendor marketing.** 411 Locals "37.8% answered"; AMBS "$126k/yr lost". Both
  are vendor-published category stats with no independent basis and must not be cited.
- **Most defensible independent-ish figure: CallRail, Jan-2025, over 1.1M leads** — missed-call
  rates **32% healthcare, 28% legal, 14% home services, 9% real estate**. Caveat recorded in
  the memlog: this is *far below the 62% the category sells on*, i.e. the industry's headline
  missed-call number is inflated by roughly a factor of two against the best available data.
  CallRail is itself a vendor, hence "independent-**ish**".
- No-shows: **~23% meta across 105 studies**; dental **15–20%**, vet **10–12%**.
- **No independent per-vertical appointment-value dataset was found.** Any per-booking value
  used downstream is therefore an assumption, not a finding.
- Human services are **converting to AI, not being chosen over it**: Smith.ai sells both from
  one vendor — AI-first free/25 calls up to **$800/500 calls ($1.60–2.00 per call)** vs
  human-first **$300/30 up to $2100/300 ($7–10 per call)**, a **4–5x price gap for the same
  job**. Ruby stays human at **$250/50min to $1725/500min**. Counter-signal: **Mindbody sells
  a cheaper "Messenger" tier that strips the AI front desk out** — a de-adoption path shipped
  as a SKU.
- Consumer acceptance, **vendor-run survey (Zenoti's own)**: **55% of salon and 71% of medspa
  clients** comfortable with an AI receptionist — so **~45% of salon clients are not**.

### 1.4 Channel and compliance

- US contact preference: **text 33%, email 28%, web chat 21%, phone 18%** — **SMS-vendor
  research**, so directionally self-serving. The countervailing fact: inbound to these
  businesses is still **phone-led**, which is why **every funded competitor is voice-first**
  with text as the second channel.
- Region forks GTM: **US/UK/CA/AU/N-Europe are SMS-primary**; **WhatsApp dominates
  LatAm/S-Europe/India/MEA**.
- **US A2P 10DLC is mandatory**: brand **$46 one-time**; campaign **$15 one-time + $10/mo**
  (Agents & Franchises **$30/mo**); carrier surcharges per segment. **2026 tightening**
  includes **EIN ≥15 days**, carrier-verifiable opt-in URLs, and **Reseller ID mandatory when
  registering on behalf of another entity**. Consequence: per-tenant onboarding friction that
  bundled incumbents absorb and a solo developer would not.
- **WhatsApp**: per-message pricing since **2025-07-01**; from **2026-02-16** Meta charges
  "AI Providers" **$0.0691/message** for non-template messages (**Italy first**). The
  definition of "AI Provider" is loose — recorded as tail risk.

### 1.5 Lead qualification (candidate 2): saturated and partly discredited

- **Salesforce acquired Qualified (Piper)**, the purest-play inbound specialist, for
  **$1.2B**, closed **April 2026** — **VERIFIED in Salesforce FY2026 10-Q**.
- Bundled everywhere, all outcome-priced: **Intercom Fin for Sales at $9.99 per qualified
  lead**; **HubSpot Breeze ~$0.50/resolution**; **Agentforce ~$2/conversation**.
- **CRM APIs are all self-serve and open** (HubSpot, Pipedrive incl. Lite tier, Salesforce,
  Zoho) — so integration is **no moat** in this category, the inverse of the booking case.
- Category trust damaged: **TechCrunch 2025-03-24** verified that **11x** displayed
  non-customer logos (**ZoomInfo denied and threatened legal action**); **~$14M claimed ARR
  vs ~$3M surviving contracts**; an employee cited **70–80% inbound churn**; CEO stepped down
  **~May 2025**.
- Not dead, though: funding continued (**Artisan $25M, Regie $30M**) — saturated and
  consolidating rather than collapsing.

### 1.6 Legal client intake (candidate 3): saturated eight weeks before this brief

- **Clio launched "Grow AI" inside Clio Grow on 2026-08-20.** Capability as recorded: AI
  agents on **phone + email + website chat, 24/7**; answer questions; capture contact and case
  details; **assess leads against the firm's criteria (case type, location, conflicts)**;
  score against the firm's **own historical case outcomes**; **book qualified leads into
  consultations**; auto-follow-up on stalled inquiries. Priced **$25 per converted lead**,
  nothing if no conversion, spend caps available.
- That is the proposed product, shipped by the vendor that owns distribution *and* the data.
- Integration is worse than in booking: **Clio's API is partner-gated by application** and
  Clio is now a direct competitor; **MyCase deliberately restricts its API**. The two systems
  most needed are the two least open.
- **Regulatory constraints — not a hard blocker, but they impose product requirements.** All
  three opinions were read via **secondary summaries; the opinions were not fetched
  first-hand** (an explicit evidence gap):
  - **Alabama Formal Op. 2026-01** — a chatbot giving specific legal advice without an "I am
    not an attorney" disclaimer and without attorney review may be **UPL**; the deploying
    lawyer is liable (Rules 5.5, 5.3, 8.4).
  - **Oregon Op. 2026-208** — permitted if the lawyer stays competent, **supervises the vendor
    as a nonlawyer assistant** (Rule 5.3), discloses nonlawyer status, protects
    prospective-client confidences.
  - **Florida Op. 24-1** — disclose AI; the lawyer owns everything the bot says; the bot must
    screen conflicts and avoid contacting represented parties.
  - Derived requirements: AI disclosure on every channel; **collect-and-screen only, no
    advice**; conflicts check before substantive intake; Rule 1.18 confidentiality implying the
    vendor is contractually a supervised nonlawyer assistant with **no training on client
    data**.

### 1.7 Attach rate and adoption — the one surviving gap, then closed

Strand 1 named exactly one place an opportunity could still hide: **attach rate, activation
and churn for the incumbent AI features were UNVERIFIED**. Strand 3 was run against that
hinge, and **"shipped-but-dark" is FALSE**:

| Source | Figure |
| --- | --- |
| **ServiceTitan Q2 FY2027 (2026-09-09)** | virtual agent **revenue and call volume each more than doubled sequentially**; the 10-K calls Virtual Agents "**in early adoption**" |
| **Weave Q1 FY2026** | "**more than 50% of locations use at least one embedded AI feature**" + **300% increase in AI interactions** |
| **Weave Q2** | **70M AI interactions, +165%**; **14.5M calls analyzed**; **810K unscheduled opportunities** |

Caveat recorded with the Weave figure: **"at least one embedded AI feature" is vague** — it
spans missed-call text-back and transcription, **not the receptionist**. And: **no vendor
discloses an attach rate for the booking feature specifically, and none discloses a
disable/abandonment metric.** The honest reading is "these features are ON and GROWING",
not a measured booking-feature attach rate.

**Shipped-and-FENCED, not shipped-and-dark.** Both public vendors fence the agent to
**overflow and after-hours by default** and expand "incrementally" — management's own words.
ServiceTitan's CFO: *"many customers start with overflow and after hours... now we also have
customers that opt to let VA handle incrementally more and more volume."* INTERPRETATION
recorded in the memlog: operators enable it in the window where a mistake costs least; that
fencing is **a trust deficit expressed as configuration**.

### 1.8 Trust-feature audit of the five candidate differentiators

Run because the fencing finding suggested trust, not capability, was the gap.

| Candidate differentiator | Status |
| --- | --- |
| (a) per-conversation review | **Shipped** — ServiceTitan virtual agent scorecards + call summaries |
| (b) approval-before-commit | **Shipped as Weave's DEFAULT** for most verticals: "let AI Receptionist capture appointment requests, then let your team review and schedule" |
| (c) rule authoring | **Shipped** — ServiceTitan: job types bookable per business unit, custom dispatch fees, escalation rules, KB upload, custom follow-up questions |
| (d) **counterfactual replay** — show how a rule change would have altered past conversations | **ABSENT from every vendor examined** — the only unoccupied cell |
| (e) longitudinal quality | **Shipped** — ServiceTitan, plus a supervision **Command Center** announced at Pantheon 2026: "one way for your team to supervise all the agents, configure them, monitor their performance" |

Mindbody / Zenoti / Podium / PetDesk: **no public evidence either way, leaning thin.**

**The real moat is not conversation quality or explainability — it is write access to the
calendar with live capacity.** ServiceTitan has "Adaptive Capacity"; **Weave's AI Receptionist
books directly only into qualified dental PMSs, every other vertical is CAPTURE-ONLY.**
ServiceTitan reports a **70% booking rate including capacity constraints vs 90% excluding
them** — the dominant failure is that *the calendar had nothing to offer*, a business-rules
and capacity problem, **not comprehension**. No amount of rule transparency fixes it.

### 1.9 Integrity warning: the abandonment statistics are fabricated — and the mechanism

**This is the most reusable lesson in the file.**

The AI-receptionist query space is contaminated by vendor SEO spam **including fabricated
statistics**. The documented instance: a **Swiss Monkey** page titled *"AI Virtual Receptionist
for Dental Office Reddit Reviews"* asserts **"60% of practices receive patient complaints
within the first month"** and **"40% abandon AI systems within three months"** — with **no
citations, no thread links, and two unverifiable handles**.

**The mechanism: Swiss Monkey sells remote human dental front-office staffing — the product
those statistics argue for.** The abandonment narrative that would justify building this exact
product is being **manufactured by the competitors of AI receptionists**, dressed as
user-voice evidence ("Reddit reviews") precisely because user-voice evidence is what a
researcher goes looking for and cannot easily check.

Generalised rule implied: when a statistic is the exact number needed to justify a purchase,
check who sells the alternative before citing it; and treat a page that *claims* to summarise
a primary community corpus, without linking a single thread, as fabricated until a thread is
produced.

Compounding gap: **Reddit was blocked to the researcher**, so **no primary operator-voice
corpus was obtainable at all.** Any section on failure taxonomy rests on no reliable public
data and **must not be treated as evidence**.

### 1.10 Residual unverified items

| Item | Why it matters |
| --- | --- |
| **NexHealth Partner Program commercial terms** | The most load-bearing unknown on the dental path |
| Whether **TrueLark's SMS/web-chat booking survived the Weave integration intact** | Decides whether the "verbatim the proposal" product is still on the market in that form |
| **Jane / Boulevard / Zenoti / vet-PMS official API terms** | All partner-gated or unpublished |
| **Booking-feature-specific attach rate and any disable/abandonment metric** | No vendor discloses either |
| Mindbody / Zenoti / Podium / PetDesk trust features | No public evidence either way |

---

## 2. The structural finding on system-of-record bundling

The brief states this in one line. The argument in full:

**The observation (3 for 3).** Every narrow inbound conversational job examined has been
bundled by the vendor that owns the **system of record**:

| Job | System-of-record owner that bundled it |
| --- | --- |
| Appointment intake | ServiceTitan; Mindbody; Weave (via TrueLark, $35M) |
| Inbound lead qualification | Salesforce (via Qualified, $1.2B); HubSpot; Intercom |
| Legal client intake | Clio (Grow AI, 2026-08-20) |

**Why this is structural, not coincidental** (four distinct mechanisms, each independently
sufficient to disadvantage a third party):

1. **It controls the write API** — and can gate a third party's access to it. Observed
   directly: NexHealth Partner Program gating, Mindbody partner program plus metering, Fresha
   having no write API at all, Clio partner-gating its API *while being the competitor*,
   MyCase deliberately restricting.
2. **It owns distribution** — the feature arrives as a toggle inside software the business
   already pays for, against a third party that must acquire each location.
3. **It owns the historical outcome data** needed to score (Clio scores leads against the
   firm's own historical case outcomes).
4. **It can price on outcome, because it alone observes the outcome.** All three incumbents
   do: **$25/converted lead** (Clio), **$9.99/qualified lead** (Intercom Fin for Sales),
   **~$2/conversation** (Agentforce).

**Confirmation of a prior finding.** This empirically confirms *strike 1* from the
brainstorming session against candidate C2 ("every plausible incumbent already ships inbound
triage *and* owns the system of record"). The brainstorming session reached it by reasoning;
the research reached it by observation, in three unrelated categories.

**The positioning implication, stated plainly.** The convergence document's thesis positioned
Agent Studio as *"the conversational intelligence and execution layer above the customer's
systems, joined to them by a key"* (convergence §1) — and the supporting decision made
external systems authoritative on purpose (convergence §3, supporting decision 1). The
research finding is that **the intelligence layer on top of someone else's system of record is
precisely the position the system-of-record owner bundles away.** The architecture decision was
right for the reasons given; it is simply not a commercial position.

**The second-order implication for the architecture, not the market.** Outcome pricing
*requires measuring outcomes*, which requires the **join key and the evidence loop** — exactly
the expensive seam the brainstorming session had already identified (Seam 1, §3.2 below). So
the research both **confirms the architecture insight was right** and shows that outcome pricing is
**structurally easier for whoever owns the system of record**: a third party without the join
key cannot price that way at all.

**Where this left the candidate.** COACH VERDICT, recorded: the trust wedge as framed is
**mostly occupied and closing** — (a)(c)(e) shipped by ServiceTitan, (b) is Weave's shipping
default, and only **(d) counterfactual replay** is unoccupied, which has value only when
attached to a calendar with **live-capacity write access** — precisely the incumbent moat a
solo developer cannot cross. **Appointment intake is closed as a commercial opportunity.**
Requirements 1–4 (real problem, real user, technical depth, measurable outcome) remain fully
available — which is why the project continued rather than stopping.

---

## 3. Architecture material carried from the brainstorming session

Source: `convergence.md`. Labels are that document's own.

### 3.1 The two principles

**Principle 1 — Deterministic-first, LLM escalation. (DECIDED as a principle.)**
Deterministic logic runs first; the LLM is invoked where deterministic logic cannot
confidently resolve. Corollaries drawn in session: do not spend a model call generating a
reply you already know after a successful tool call (template the known reply, LLM as
fallback); do not classify every turn if the job structure already supplies direction.
**Caveat attached by the owner and kept:** this principle must **not** be applied for
elegance. Selection comes from the actual job and its failure, latency and business
constraints — and **the hot path must be measured first** (convergence §8.4).

**Principle 2 — The agent proposes, authoritative systems dispose. (DECIDED as a principle.)**
The LLM decides *what it wants to do* and emits a structured action proposal; it never
controls execution. Execution is deterministic, bounded, validated against a declared
contract, and gated where consequences require it.

Supporting decisions behind them, all DECIDED: external systems remain authoritative
(recorded as "the most consequential inversion of the session"); freshness is declared per
read / per tool contract, never globally; reads that gate a side effect must be fresh;
conversational/contextual reads may tolerate bounded staleness; evidence is durable (runtime
evidence is product data, not operational logs); the specification is versioned; evaluation
and correction do not silently mutate production behaviour; behaviour changes are reviewable,
promotable and revertable; custom code exists as controlled leaves, never as arbitrary control
flow; generated code is no longer assumed necessary; customer ownership and runtime ownership
are separate concepts.

**The four-artifact split** that the non-silent-mutation decision produced:

| Artifact | Holds | Mutability |
| --- | --- | --- |
| **Specification** | Intended behaviour | Changed only by deliberate, reviewed promotion |
| **Evidence** | What actually happened (episodes, traces, outcomes) | Append-only |
| **Evaluation** | What we judged to be wrong, and why | Append-only, versioned per agent version |
| **Deliberate changes** | What we chose to promote into the spec | Reviewable, revertable, attributable |

INTERPRETATION attached: these four have the shape of version control — spec = checked-in
state, evidence = the working tree, promotion = **a pull request on behaviour**. This collapses
two subsystems into one: the product's job is **not to measure conversational quality
objectively** (quality is irreducibly contested) but to make **disagreement cheap to express
and fast to propagate** — substantially lighter to build, because it never has to define
"good" in general, only what was wrong *here*.

### 3.2 The three seams that are expensive to retrofit

The governing V1 rule (HYPOTHESIS, accepted as a working discipline): **build the narrowest
valuable case, but refuse anything that structurally forecloses the hard case.** The test is
not "is it hard" but **cheap vs prohibitively expensive to retrofit**. Adaptive probing,
transactional tool semantics, persistent case lifecycle and hybrid retrieval are all
**additive later**. Exactly three things are not.

**Seam 1 — Episode evidence + identity (episode ID and external join key).**
Why retrofit is prohibitively expensive: **un-recorded episodes are gone forever**; there is
no backfill for a conversation that was never written down. Worse, the evidence has **two
tiers with different plumbing** — *interaction-quality* signals are dense, immediate,
computable from the episode alone, and mostly deterministic assertions requiring no judge;
*hard outcomes* are sparse, delayed, and arrive from outside (CRM, ticketing, calendar). The
consequence nobody lists: **every episode needs a join key into the operator's system of
record**, or "later downstream outcome" is permanently unobtainable. Minting an episode ID and
carrying a join key costs almost nothing up front and is brutal afterwards, because the
historical episodes that would have taught you something cannot be re-joined.

**Seam 2 — Versioned specification (not a generated prompt, not generated code).**
Why retrofit is prohibitively expensive: if intended behaviour lives as prose inside generated
Python, then **diffing behaviour, asserting over behaviour, reviewing a proposed change,
reverting a regression, and attributing an outcome to a version are all unavailable**.
Introducing versioning later requires reconstructing the intended behaviour of every past
agent from code that has already drifted — and **every evaluation record collected before the
spec existed has nothing stable to be *about***. Evaluation criteria in particular must live
inside the durable spec rather than being recreated per generation.
*Related trap (INTERPRETATION):* the "generated agents are disposable" model has an unstated
precondition — **nobody ever edits the generated output**. The moment a developer tweaks a
generated `prompts.py`/`tools.py` in place, regeneration destroys the work and the compiler
model collapses into a one-shot scaffolder. This requires either airtight round-tripping or a
"generated code is read-only, all changes go upstream" contract **with teeth**.

**Seam 3 — The external-system boundary.** Four coupled commitments: external state is
authoritative; freshness is declared, not assumed; tools are reached through declared
contracts; reads are classified by consequence.
Why retrofit is prohibitively expensive: the **authority question determines where truth
lives**, and therefore what the agent is allowed to assume between turns. A system built
assuming agent-owned state has its invariants, caching, error handling and latency profile all
written against that assumption; **inverting authority later rewrites the data layer, the tool
layer and the reply path simultaneously**. Freshness-per-contract cannot be added as a flag to
tools that were never classified by consequence.
*INTERPRETATION with latency teeth:* because the agent holds no authoritative state, decisions
must be made against **freshly read** external state, so **external tool I/O may dominate the
reply path rather than sequential LLM calls** — which means the whole "where does intelligence
live / reduce LLM calls" thread rests on an **unmeasured premise**, and observability must
precede optimisation.

These three bind as architecture constraints **even before the product is chosen**. They are
what could be committed to while the use case was still open.

### 3.3 Resolution of the three contradictions

**C1 — Leaf vs control flow.** Resolution (DECIDED): **custom code exists as controlled
leaves, never as arbitrary control flow.** Control flow — what the agent asks, in what order,
action gates, escalation, completion — lives **in the specification only**: interpretable,
diffable, assertable, promotable. Leaves — tool implementations, field validators, formatters,
scorers, auth adapters — may be **arbitrary code behind a declared contract** (signature,
pre/post conditions, failure modes, latency budget). **Proof test: the evaluator asserts over
the contract, never over the implementation.** This is why the schema never grows toward
Python-in-JSON: it never expresses computation, only **sequence, condition and policy**. The
declared anti-goal is *a gigantic declarative schema representing every possible behaviour* —
moving complexity from Python into JSON. The escape hatch must be **intentional**, with three
levels conceptually preserved: **configuration → supported extension point → custom
implementation**.

**C2 — The ownership boundary, and forking.** Resolution (DECIDED): **customer ownership and
runtime ownership are separate concepts.** Five separations were attempted — by artifact, by
space, by time, by scale, by customer condition. The resolution that held:

> **Customer ownership can extend as far as we can preserve a stable behavioural contract.
> Above that boundary, the system becomes a *fork* rather than an Agent Studio agent.**

The gradient behind it: modify the control-flow spec → still evaluable, because the spec is
structured. Modify leaf code → still evaluable, via the contract. **Modify the runtime → we
lose the ability to reason about what the system is doing.** Current favoured boundary
(explicitly not final): the customer owns the agent definition + their data + the deployment
choice; Agent Studio owns the core runtime and the evolution of behaviour; extensions are
customer-controlled leaves behind stable contracts; every behaviour change is versioned and
promotable rather than silently learned. Noted as worth keeping because it was **derived from a
constraint, not chosen by preference**. The residual: the **architectural** contradiction
dissolved, the **commercial** one (ownership) did not.

Attached to C2, the **generated-code triage**: of **twelve** claimed advantages of generated
code, only **1 (customer ownership/portability), 4 (enterprise trust story), 5 (deployment
into the customer's VPC) and 12 (offline/self-hosted execution)** genuinely require an
artifact — **and all four are the same property**. The other eight break down three ways:
**compensations for not having a good enough shared runtime** (2, 3, 10 → the leaf contract;
6, 11 → deployment/supervision; 7 → versioned specs + runtime-compatibility versioning), one that
**converts into a tracing requirement** (8: "show me the code that ran" → deterministic spec +
runtime version + episode trace), and one that is **theoretical, not current** (9: performance /
specialisation).
**Orthogonality warning carried verbatim:** *"no generated application code" and "one process
serves everyone" are orthogonal concerns and must not be coupled.* A shared interpreter is an
**execution-model** question; isolated instances, workers, containers and customer deployments
are a **deployment-topology** question. Nothing in the session proved multi-tenancy, and
nothing about adopting a shared runtime requires it.

**C3 — Separation by consequence class.** Resolution (DECIDED, four coupled decisions):
freshness is declared **per read / per tool contract, never globally**; **reads that gate a
side effect must be fresh** — stale means double-booking, a real-world failure, a refund;
**conversational/contextual reads may tolerate bounded staleness** — being wrong costs a
sentence. The structural payoff: side-effect-gating reads **happen once, near the end of an
episode, not on every turn**, and that is what makes the latency budget honest. The same move
as the leaf contract (C1) applied to **data instead of code**: the property is declared at the
boundary rather than assumed globally. The claim is explicitly flagged for measurement — if
side-effect-gating reads turn out to occur per turn, the latency budget is not honest and the
freshness model needs rework.

### 3.4 The morphology

**Source correction.** The brainstorming session's `.memlog.md` *does* exist, at
`_bmad-output/brainstorming/brainstorm-agent-studio-product-architecture-2026-10-06/.memlog.md`
(92 entries, 40,514 bytes). It is a dotfile and was initially missed. The full axis table below is
restored from it.

The Morphological Analysis produced **32 independent decision axes**, each with its option
range including the degenerate end. The option ranges matter as much as the axis names, because
the degenerate option is what makes an assumption visible.

| # | Axis | Option range |
| --- | --- | --- |
| 1 | Conversation state | full durable / session-checkpointer / minimal structured / stateless |
| 2 | Turn segmentation | explicit client turns / deterministic boundary / model-based boundary / streaming-continuous |
| 3 | Intent determination | dedicated LLM / classifier / embedding similarity / deterministic rules / **implicit — none** |
| 4 | Goal representation | explicit goal object / structured state machine / inferred from context / none |
| 5 | Information collection | fixed slots / dynamic schema / conversational extraction / implicit extraction / none |
| 6 | Ambiguity resolution | deterministic clarification rules / confidence threshold / LLM clarification / ask human / best-effort assumption |
| 7 | Conversation policy | fixed state machine / declarative policy / LLM policy selection / open-ended LLM |
| 8 | Response generation | templates / tool-constrained LLM / freeform LLM / two-tier template-plus-fallback |
| 9 | Knowledge retrieval | none / deterministic lookup / lexical BM25 / dense / hybrid / external knowledge API |
| 10 | Knowledge authority | embedded snapshot / versioned internal store / external source of truth / external plus bounded cache |
| 11 | Action selection | deterministic rules / structured LLM proposal / planner / fully agentic tool selection |
| 12 | Tool execution | synchronous direct / queued / event-driven / human approval / no tools |
| 13 | Tool failure handling | retry / deterministic fallback / alternate source / ask user / escalate / fail closed |
| 14 | External state authority | agent-owned / shared / external SoR / external plus cache / external plus event feed |
| 15 | Freshness model | always fresh / bounded TTL / version-ETag validation / event-driven / stale with explicit policy |
| 16 | Action safety | unrestricted / allowlisted tools / schema validation / policy gate / human approval / no autonomous action |
| 17 | Escalation | none / deterministic conditions / confidence threshold / policy-driven / human-in-the-loop |
| 18 | Episode identity | session id / conversation id / external entity id / generated episode id plus external join key |
| 19 | Evidence capture | transcript only / structured turn events / tool-retrieval-decision traces / full episode event log |
| 20 | Observability | logs / metrics / traces / structured episode telemetry / all |
| 21 | Evaluation target | response quality / task completion / policy compliance / action correctness / external business outcome / human judgement |
| 22 | Evaluation timing | synchronous per turn / end of episode / asynchronous batch / delayed external outcome |
| 23 | Feedback source | automated evaluator / user feedback / operator review / external outcome / combinations |
| 24 | Specification management | prompt-config only / versioned spec / versioned spec plus eval suite / versioned spec plus reviewable behaviour changes |
| 25 | Behaviour promotion | automatic / threshold-automatic / human approval / review workflow |
| 26 | Memory | none / short-term conversation / structured customer memory / external CRM memory / retrieved historical episodes |
| 27 | Personalisation | none / deterministic fields / retrieved customer context / LLM-generated |
| 28 | Model strategy | one general LLM / specialised per stage / cost tiering / deterministic-first with LLM fallback |
| 29 | Execution topology | single process / graph-state machine / event-driven components / external workflow engine |
| 30 | Failure boundary | fail conversation / retry locally / degrade capability / escalate / continue without action |
| 31 | Configuration boundary | prompts only / prompts plus schemas / declarative agent specification / code-plugin extension |
| 32 | Generated artifact | generated runtime code / generated configuration / compiled graph-config / **none — shared runtime interprets spec** |

**Four collapses — axes that are not independent.** The session's most useful morphological
finding was that several axes are dependent variables:

| Collapse | Finding |
| --- | --- |
| **Axes 3, 4, 7 are one axis** | Intent determination, goal representation and conversation policy are near-collinear. Given an explicit goal object plus a state machine over what the job still needs, intent classification is **redundant** — the structure already knows the turn and the gap. The real single axis: *does turn-level direction come from classifying the utterance, or from the structure of the unfinished job?* |
| **Axis 8 is downstream of axis 5** | Response generation is largely determined by information collection. With fixed slots the next utterance is a function of what is missing, so a template suffices; freeform generation earns its keep only where the next utterance is not determined by the gap |
| **Axis 15 depends on 14; axis 16 partly on 11** | Freshness is meaningless under agent-owned state and mandatory under external authority — a dependent variable. Action safety stops being independent once execution is deterministic, because deterministic execution *is* the safety mechanism |
| **Axes 18, 21, 23 are one commitment** | If "external business outcome" is an evaluation target, episode identity is *forced* to generated-episode-id-plus-external-join-key. Not a choice — an implication, and one already accepted |

**Six counterintuitive combinations collapsed into two principles.** Combinations 1, 2 and 6
(no explicit intent plus implicit task state; deterministic response with LLM fallback;
deterministic-first with LLM escalation) are one move: **deterministic-first, LLM on escalation**.
Combinations 3, 4 and 5 (external authority plus bounded cache plus explicit freshness policy;
structured action proposal with deterministic execution; versioned spec plus episode evidence
plus human promotion) are one move: **the agent proposes, something authoritative disposes**.
Both are subtractive — they remove the model from the critical path for everything it is not
uniquely good at.

**Cells that should stay empty, and why:**

| Axis | Leave empty | Reason |
| --- | --- | --- |
| Turn segmentation | model-based boundary, streaming-continuous | In text, turns are discrete client messages. The whole axis is a voice artifact |
| Evaluation timing | synchronous per turn | Never put measurement on the reply path to learn what a recorded episode yields afterwards |
| Behaviour promotion | automatic, threshold-automatic | Silent learning was rejected. Empty **on purpose**, documented |
| Personalisation | LLM-generated | Buys warmth, costs a call, adds variance to a reply otherwise controlled |
| Execution topology | external workflow engine | Becoming a workflow platform was explicitly refused |
| Action selection | fully agentic tool selection | Incompatible with bounded actions and deterministic execution; the cell that makes safety and evaluation both intractable |

What `convergence.md` additionally preserves on cell states, usable downstream:

| Axis named in convergence.md | Cell state as recorded |
| --- | --- |
| **Interest alignment** (aligned vs misaligned) | *"Alignment, not domain, is the axis on which the conversational engine actually differs."* C1 misaligned; C2/C3 aligned and near-twins |
| **Freshness / consequence class of a read** | Collapsed into Seam 3: declared per read, two cells — side-effect-gating (must be fresh) and conversational (bounded-stale) |
| **Failure boundary** | A declared axis — the reason the `failure` node survives the narrowing |
| **Turn segmentation** (barge-in, interruption, endpointing, corrected-transcript dedupe) | **Entire axis removed** by text-first — the cells cease to exist rather than being abstracted |
| **Knowledge authority** | Explicitly **not decided**: embedded snapshot / versioned internal store / external source of truth / external + bounded cache |
| **Retrieval mechanism** | Explicitly **not decided**: deterministic lookup / lexical / dense / hybrid / external knowledge API |
| **LLM / model strategy** | Explicitly **not decided**: one general model / specialised per stage / cost tiering / deterministic-first with LLM fallback. Principle 1 fixes the *posture*, not the call-site topology, which is blocked on measurement |
| **Execution model** vs **deployment topology** | Deliberately kept **orthogonal** (see the C2 orthogonality warning); coupling them is the recorded error to avoid |
| **Deployment ownership** | Five separations explored (artifact, space, time, scale, customer condition); **conditional ownership by customer segment** is the most commercially plausible and is unvalidated |

The two cells the session explicitly marks as **must stay empty**: *arbitrary control flow in
custom code* (C1 — it destroys evaluability) and *a declarative schema that expresses
computation* (the "Python-in-JSON" anti-goal). One further cell is **blocked, not empty**:
deletion of `intent_detect`, which is gated on measurement.

---

## 4. The current implementation

All FACT rows below are cited to a file or line in `convergence.md`, which verified them
against the repository. INTERPRETATION rows are that document's readings of those facts.

### 4.1 The graph

**FACT (verified in `boilerplate/graph.py:188-239`):** the real graph is **not** a four-stage
Intent → Think → Tool → Enrich pipeline — that was a conceptual summary. `build_pipeline`
registers **fifteen** nodes:

`intent_detect`, `knowledge`, `agentic_retrieval`, `chitchat`, `closing`, `system`, `planner`,
`plan_step`, `think`, `hitl_gate`, `tool_exec`, `execution_validator`, `failure`,
`enrichment`, `validator`

with **six** conditional routers — `route_by_intent`, `route_after_planner`,
`route_after_plan_step`, `route_after_think`, `route_after_hitl`, `route_after_execution` —
and compiles with **`MemorySaver` by default**.

### 4.2 LLM call sites and file-size distribution

**FACT:** `boilerplate/nodes.py` is **1776 lines** — roughly **22% of the 8229-line
engine+platform tree**, and about **twice the next-largest file**. It contains **six direct
LLM call sites**: `INTENT_MODEL` ×1, `ANSWER_MODEL` ×4, `ENRICH_MODEL` ×1.
`boilerplate/rag_subgraph.py` adds **two more** (8 total). `rag_subgraph.py` (**164 lines**)
and `filler.py` (**90 lines**) are among the **thinnest** files in the tree.

**INTERPRETATION:** the subsystems the emerging architecture wants to **promote** (retrieval as
a subsystem, evaluation as a first-class concern) are currently the **smallest** files, while
the monolith the narrowing wants to **shrink** is the **largest**. The right question was never
"is Intent → Think → Tool → Enrich correct" — that is a caricature — but **which of the fifteen
nodes survive the narrowing**.

### 4.3 Durable storage, and the open circuit

**FACT (verified in `builder_platform/storage/schema.sql`):** durable storage is **two SQLite
tables** —

| Table | Columns as recorded |
| --- | --- |
| `sessions` | `session_id`, `created_at`, `last_active`, `active` |
| `built_agents` | `agent_name`, `project_path`, `system_prompt`, `selftest_status`, timestamps |

**What it does not record:** there is **no table capable of recording a conversation, a turn, a
tool call, an outcome or a latency.**

**FACT:** runtime conversation state is **`MemorySaver`** (`boilerplate/graph.py:239`);
`builder_platform/runtime.py:137` states that state is carried across turns *"without us
persisting the transcript"*; **durable checkpointing is left as an unexercised option**
(`graph.py:50` region).

**INTERPRETATION:** **build-time facts are durable, run-time facts are ephemeral.**
`selftest_status` is a **build-time** quality gate standing in for a **run-time** quality
signal. The improvement loop — builder and operator as one continuous product loop — currently
has **zero substrate; the circuit is physically open.** This is exactly Seam 1.

### 4.4 Per-node classification under the narrowing

Narrowing assumptions: text-first, inbound, aligned-interest, deterministic-first,
agent-proposes/systems-dispose. **All rows are INTERPRETATION.** The convergence document
states explicitly that this section **is not a refactor plan**: it is a prediction recorded so
it can be checked later, and **no node is to be deleted on its authority.**

| Node | Verdict | Reasoning |
| --- | --- | --- |
| `planner` | **Likely deleted** | Compound multi-step planning is an outbound / complex-sales affordance; aligned-interest intake is single-goal |
| `plan_step` | **Likely deleted** | Same; also the source of the graph's one sanctioned loop |
| `enrichment` | **Likely deleted — the clearest single casualty of Principle 1** | Spending an SLM call to phrase a tool result is exactly the call deterministic-first replaces with a template |
| `intent_detect` | **NEEDS MEASUREMENT before deciding** | Direction largely comes from job structure, so it collapses toward a small on-task / off-task / done discriminator — but cutting it is a measurement decision, not an aesthetic one. **Do not delete before measuring** |
| `chitchat` | **Likely simplified** | Becomes a deterministic/template path |
| `system` | **Likely simplified** | Reduced surface under a narrower job |
| `validator` | **Likely simplified** | In text the pre-TTS sanitizer concern vanishes; what remains is policy and schema validation |
| `hitl_gate` | **Likely simplified — relocated in kind** | Becomes "confirmation before a side effect", which is a **tool-contract property**, not a graph node |
| `knowledge` | **Likely survives** | Inbound callers ask things |
| `closing` | **Likely survives — more important** | Episode completion and structured disposition become central |
| `tool_exec` | **Likely survives — strengthened** | Must carry idempotency and transactional semantics; degree is use-case dependent (maximal for appointment intake) |
| `failure` | **Likely survives** | The failure boundary is a declared axis |
| `execution_validator` | **PROMOTED** | Becomes the **contract assertion point** — where the evaluator makes its claims, per the C1 leaf-contract resolution |
| `agentic_retrieval` | **RELOCATED** | Survives as a **subsystem pulled out of the agent flow**, not as a node inside it |
| *(overall)* | **Use-case dependent** | `tool_exec` hardening, `hitl_gate` shape, and the evaluation counterweights all vary by chosen case |

### 4.5 Voice-specific machinery removed outright by text-first

**FACT (these files exist and are voice-specific):** `boilerplate/filler.py` (pre-think
filler + per-tool filler banks); **sentence-chunking of the final reply**;
`builder_platform/sanitizer.py` (pre-TTS backstop); `builder_platform/vapi_adapter.py`;
`builder_platform/vapi_control.py`; `builder_platform/tunnel.py`; and **the entire
turn-segmentation axis** — barge-in, interruption, endpointing, corrected-transcript dedupe.

**INTERPRETATION:** these are **not** "modality-specific logic leaking into the core" — they
are concerns that **cease to exist** in text. **Nothing has to be abstracted; they are simply
out of scope.**

### 4.6 The reuse question this leaves open

Open question 9 of convergence §7, unanswered: **is the existing voice boilerplate genuinely
reusable after stripping the modality-specific machinery?** The named experiment: produce a
text-only cut following §4.4 — delete the voice machinery and `planner`/`plan_step`/
`enrichment`, keep the rest — then measure the resulting line count of `nodes.py` and whether
the selftest still passes. **Falsifier:** if what remains is still a 1000+ line monolith with
coupling that resists the subsystem split, "evolve rather than discard" is falsified and a
clean reimplementation is the cheaper path.

---

## 5. Rejected alternatives and course corrections

The section a future reader should read first, so that nothing here gets re-proposed.

### 5.1 The four competing job-to-be-done statements

| Framing | Status and one-line reason |
| --- | --- |
| **C2 — Service/request qualification** (the owner's *original* top rank) | **Rejected on three independent strikes:** every plausible incumbent (Zendesk, Intercom, Freshdesk, ServiceNow) already ships inbound triage **and** owns the system of record; the buyer (support/ops) is a **cost centre** while C1/C3 sell to revenue centres; and it **maximises the hardest unresolved contradiction** — enterprise runtime-ownership demand — whereas C3 nearly dissolves it. Its real risk was also the worst shape: **persistent case lifecycle** (unresolved requests across sessions, status pushed from external systems, proactive follow-up, continuing after human handoff) is product-shaped and open-ended, not bounded |
| **C1 — Lead qualification** | **Rejected as a *primary* boilerplate** on two grounds: it is a **misaligned-interest** conversation needing adaptive probing, evasion handling and scepticism toward self-reported facts — which refuses to be configuration; and its **evaluation observability is the worst** — false negatives are invisible, a wrongly disqualified good lead is gone and emits no signal. Later also **rejected commercially** (§5.3) |
| **C3 — Appointment intake** | Promoted to **leading hypothesis** (difficulty architectural and bounded; failures visible within days; revenue-centre buyer with near-zero runtime-ownership demand; the incumbent owns the *calendar*, not the inbound conversation). **Explicitly never selected.** Then **closed as a commercial opportunity** by the 2026-10-07 research (§1, §2) |
| **"An AI receptionist that books appointments"** | **Rejected by hard condition**, user-stated: commoditised, and existing competitors must **not** become an excuse for building a worse copy. Not an acceptable thesis |

Two findings from this comparison were ruled to **survive regardless of which case is chosen**:

1. **The lead-qualification evaluation trap** (INTERPRETATION, and it generalises). Where
   false negatives are invisible, an outcome-driven improvement loop **rewards drift toward
   strictness**: conversion among passed leads rises while total revenue falls. Selection bias
   with a feedback loop attached, self-reinforcing. Counterweights — holdouts, forced random
   pass-through, human adjudication of rejections — are required for C1 and not for C2/C3.
   Consequence: **the evaluation architecture is use-case-specific even where the execution
   architecture is not.** Any case whose negative decisions destroy their own evidence
   inherits this trap, so **a candidate with no feasible counterweight must not be chosen** —
   its improvement loop actively degrades the business.
2. **The interest-alignment fault line.** Alignment, not domain, is the axis on which the
   conversational engine actually differs.

### 5.2 The compiler framing

The "generated agents are disposable, the builder is a compiler" framing was **not rejected
outright, but it was demoted and conditioned**:

- **Generated code is no longer assumed necessary** (DECIDED as a stance; the fork itself
  **not** finally decided).
- Of its **twelve** claimed advantages, only four are genuine and they are **one property**
  (see §3.3, C2 triage).
- **The compiler model has an unstated precondition — nobody ever edits the generated
  output.** One in-place tweak to a generated `prompts.py`/`tools.py` and regeneration destroys
  the work; the compiler collapses into a **one-shot scaffolder**. Holding the framing requires
  either airtight round-tripping or a read-only-generated-code contract **with teeth**.
- Evidence that would **keep** generated code: a target segment that *refuses* a hosted runtime
  for reasons spec-level ownership does not satisfy, **observed in an actual procurement
  conversation**; a real recurring customer requirement no leaf and no extension point can
  express; an actual incident where spec-version + runtime-compatibility-version proved
  insufficient; evidence that artifact-level debugging materially beats spec + runtime
  version + episode trace on real incidents.
- Evidence that would **replace** it: spec-level ownership satisfying the actual buyer,
  confirmed in conversation; episode traces + spec version + runtime version reconstructing
  past behaviour well enough to debug real failures; observed (not predicted) variation fitting
  a limited configuration surface plus leaves; and the regeneration-destroys-local-edits trap
  continuing to bite.

### 5.3 The three use-case candidates, and why each fell

| Candidate | Where it fell |
| --- | --- |
| **Appointment intake** | Occupied end to end (TrueLark/$35M/Weave, ServiceTitan, Mindbody since 2019, Podium, Zenoti); write-API access gated or absent in most verticals; price ceiling already set at $99–199/location/month inside $400–600 software; the real moat is **live-capacity calendar write access**, not conversation quality; and the trust wedge is **mostly occupied** — only counterfactual replay is unoccupied and it is worthless without that calendar write access |
| **Inbound lead qualification** | **Saturated and partly discredited.** Salesforce/Qualified **$1.2B** closed April 2026; bundled by Intercom, HubSpot, Agentforce at outcome prices; **CRM APIs all self-serve and open so integration is no moat at all**; category trust damaged by the verified **11x** misrepresentation. Already independently rejected on architecture grounds (misaligned interests + invisible false negatives, §5.1) |
| **Legal client intake** | **Saturated eight weeks before the brief.** **Clio Grow AI, 2026-08-20**, is the proposed product shipped by the vendor owning distribution and the outcome data, at **$25 per converted lead**; and the two systems most needed — Clio, MyCase — are **the two least open**. Plus hard product requirements from bar opinions (disclosure on every channel, collect-and-screen only, conflicts check before substantive intake, vendor as supervised nonlawyer assistant with no training on client data) |

Also noted and never researched: **internal operations** — one of the user's three *original*
candidate classes from the brainstorming session, flagged by a subagent as "an unexamined third
option". It is not rejected; it is **unexamined**.

### 5.4 The physio/Cliniko recommendation — made and withdrawn

**WITHDRAWN, by user course correction, coach accepted.** The research correctly killed "build
another vertical AI receptionist/booking product" — which the user **never wanted** — but the
coach then wrongly concluded "therefore build a physio booking agent on Cliniko",
**optimising for API accessibility and producing exactly the narrow vertical product the user
was avoiding.**

The correction, stated as a standing rule: research must answer *"is there a broad SMB class of
problems where a reusable conversational-agent architecture creates meaningful value"*, **not**
*"which vertical has the easiest public API"*. **The user does not need an unsaturated
vertical** — the point is that the **same underlying product** is useful across many SMB
contexts.

This is the **third occurrence of the same bias**, and the memlog names it as such: text-first
had itself been decided on **internal engineering grounds** (reusable boilerplate,
config-driven, avoid voice machinery) — the same architecture-convenience bias already caught
twice in the brainstorming session (ranking candidates by architectural cleanliness; and
"technically impressive implies valuable"). Recorded consequence: **text-first vs voice was
reopened** as a DECIDED item, on the grounds that it may have been architecture-driven rather
than product-driven. It was **not automatically reversed** — phone-heavy inbound volume does
not by itself make voice correct. The governing replacement question: **for the specific
problem eventually chosen, where does the valuable interaction actually happen?** *Inbound (vs
outbound) remained decided throughout.*

### 5.5 The per-vertical prohibition library — proposed, then replaced

**Proposed** (stress-test required change 8): *the builder needs a **prohibition and escalation
library per business category***. Motivation, which still stands and is the most
safety-relevant finding of the stress test: **the prohibition list and urgency triggers are the
least documented and most critical content of a specification.** For the dental practice they
exist **in no document at all** — they are tacit professional/regulatory knowledge. Eliciting
*"what must your agent never do"* by open question **will produce a dangerously short list.**

**Replaced by:** a **generic, domain-neutral guardrail library in the core** (do not invent
business facts; do not act outside declared authority; do not perform undeclared actions; do
not claim an action succeeded without evidence; escalate when required authority or evidence is
unavailable) **plus optional domain packs as extension points, never core architecture** — and
with **no packs in V1**. Reason: a per-category library makes vertical knowledge a core
dependency, reintroducing the vertical framing the project had just rejected, and it scales as
the number of categories rather than as the architecture.

### 5.6 Other corrections applied in sequence

| Correction | Reason |
| --- | --- |
| Fixed disposition set **answered \| action taken \| escalated \| out of scope** | **Too appointment-specific.** Replaced by: every episode terminates in a **structured, evaluable business outcome**, with exact outcomes varying per business inside a **constrained outcome model** |
| First constrained outcome model: **fulfilled \| committed \| informed \| deferred \| refused** | **fulfilled/committed did not separate cleanly** and **deferred was carrying three unrelated meanings.** Replaced (structural change 1) by **resolved_informational \| resolved_actioned \| refused \| escalated(reason class) \| PENDING** |
| **"Capacity blocked" as a platform invariant** | It is a **booking example**, not a platform invariant |
| **"Non-FAQ share" as a product metric** | It is a **proof/evaluation concept**, not a universal product metric |
| **The builder is out of scope** (the coach's cut) | **Reversed by the user.** The ability to rapidly create a new business-specific agent is **central to the thesis** — without it, this is a generic runtime plus an assertion that it can be configured. Minimal version suffices: business conversation + source material → draft specification → validate/self-test → deploy, human review in the loop |
| **Coach to present branches** | **Reversed:** the coach is to **lead** the product-definition process |
| **"nursery" read as childcare** (brief v1) | **Mis-read.** It is a **plant nursery / garden centre** (the dying-plant request). The correction **materially strengthens the diversity argument**, because that request involves **no transaction at all** |
| **Market research steering the product** | Standing instruction: do **not** let it drag back toward "find an empty vertical"; a new market category need not be proven |

### 5.7 The coach's incorrect "cross-session out of scope" boundary

**COACH SELF-CORRECTION, recorded: *"anything spanning sessions is out of scope" was WRONG*, as
the user suspected.** Three of the four stress-test examples **require** cross-session
continuation — the gym freeze awaits a medical note, the brewery hold expires, the garden-centre
claim waits on the horticulturist. **Anything that defers or awaits a document is inherently
multi-session, and that is most of the interesting behaviour.**

The diagnosis of *why* the error happened is the reusable part: **the absence of a `pending`
outcome kind from the coach's first model is what hid the finding.** A missing enum member
silently defined a capability out of existence. Cross-session continuation was then reclassified
as **IN scope and non-structural** — it *follows from* `pending` rather than needing its own
mechanism.

### 5.8 Two insights that forced structural changes

**The sharpest new finding (garden centre): inferring a CAUSE and determining FAULT are
different acts with different consequences.** The agent may say *"daily watering is almost
certainly the problem"* (grounded care advice) but may **not** conclude *"therefore this is
neglect, which is excluded, claim denied"* — that is a **liability determination made on its own
authority**. **Nothing in the prior model distinguished them.** This is what forces **decision
authority classes** (informational / liability-bearing / state-changing, separately gated).

**The pre-emptive gate.** Dental urgency interception **has no home in an 11-step pattern that
starts at "understand what the person wants"** — hence a gate that runs **before** goal
recognition and can abort the episode.

### 5.9 The stress-test verdict, and its honest limit

**VERDICT: B — the abstraction needs changes before architecture.**

- **Not C** (abstraction wrong): all **13 schema fields were invariant** across four businesses
  **sharing no workflow**; every substantive difference was configuration; **no case required
  custom implementation**; and the primitive set **refuses** things — no reasoning unanchored to
  a declared goal, no decision outside an authority class, no claim without a source, no action
  without a contract, no episode without a terminal outcome — **which means it is a primitive
  set, not a framework**.
- **Not A** (ready as-is): **four of the eight required changes are structural.**

The eight required changes: **structural** — (1) replace the resolution model; (2) support
**multi-goal episodes and goal switching** (the garden-centre customer has two goals, may not
know which, and the second is conditional on the first); (3) add a **pre-emptive gate** before
goal recognition that can abort the episode; (4) add **decision authority classes**.
**Non-structural** — (5) cross-session continuation is IN scope; (6) split "information needed"
into **obligations** (must be true before an action) and **diagnostic evidence** (gathered to
support a judgement, no fixed sufficient set); (7) **version-pin knowledge sources**, else two
agents differ by leaflet revision and a spec diff shows nothing; (8) the prohibition library
(since replaced — §5.5).

**HONEST LIMIT of the exercise, recorded verbatim in substance:** it validates that the schema
can **EXPRESS** four dissimilar businesses. It does **not** validate that an agent built from
such a spec **BEHAVES** well, nor that the specs are **correct** — **they are the coach's
constructions, not any real business's rules.** The **practised-vs-printed-policy gap** is the
likeliest place all four are wrong, **and only a real operator can close it.**

---

## 6. Open unknowns requiring primary evidence

No further desk research settles any of these. Each row names what would.

| # | Unknown | What would settle it |
| --- | --- | --- |
| 1 | **The practised-vs-printed-policy gap** — whether a business's real rules match its documents. The likeliest place all four stress-test specs are wrong | **2–3 conversations with real small-business operators**, asking them to describe their actual rules and comparing against their printed material. Named in the brief as the only test of the problem statement |
| 2 | **Whether the specification can DRIVE behaviour**, not merely express it | Build the four generalisation businesses in sequence and record the three measurements: **engine leaks** (fail if they do not fall toward zero from business 1 to 4), **resolution-model strain** (fail if any business needs a family the model cannot express), **setup effort** in wall-clock and source-artifact count (fail if it does not fall materially). Needs no customers — only real business material |
| 3 | **Whether operators can name an observable failure** | Ask the operators *"how would you know the agent did a bad job?"* and record the answer **verbatim, without prompting**. If they cannot name one, the evidence→evaluation→promotion loop has no customer-side signal and must be rebuilt around our own assertions only |
| 4 | **Whether variation is configuration or a DSL in disguise** | Ask operators to describe their intake rules; attempt each in the draft schema; **count rules needing a new schema concept vs a new leaf**. More than ~1 new schema concept per customer means the config surface is growing into the forbidden DSL |
| 5 | **Whether `intent_detect` earns its LLM call** | Measure, on real episodes, **how often its classification changes the route** versus what job structure alone would have chosen. The one explicitly blocked deletion in the classification |
| 6 | **Whether external I/O or LLM calls dominate the reply path** | Instrument per-turn end-to-end latency broken into: LLM time per call site (the **6 in `nodes.py` + 2 in `rag_subgraph.py`**), external tool I/O per call, retrieval time, framework overhead — emitted as **structured episode telemetry, not logs**. If external I/O dominates, cutting `intent_detect` or `enrichment` buys nothing and the work belongs at the data/caching layer |
| 7 | **Whether side-effect-gating reads really happen once per episode** | Tag every external read with its **consequence class** and measure how many of each occur per episode and **where in the episode they land**. If they occur per turn, the latency budget is not honest and the freshness model needs rework |
| 8 | **Whether tier-1 evidence needs a judge** | Define the **5 interaction-quality assertions** (required info collected; correct tool use; correct retrieval/evidence; correct escalation; policy compliance) and assert them over **~20 scripted episodes at the `execution_validator` contract point**. If fewer than 4 of 5 can be asserted deterministically from the episode alone, the "no judge needed" interpretation is wrong and evaluation gets much more expensive |
| 9 | **Whether a joined episode is cheap** | Run the narrowest end-to-end episode against one real external system: conversation → structured action proposal → deterministic execution → confirmation → an episode record carrying an **episode ID and the external join key**. One happy path. If that cannot be produced cheaply, **Seam 1 is harder than assumed and must be scheduled, not assumed free** |
| 10 | **Whether the existing boilerplate is reusable after the voice strip** | Produce the text-only cut and measure the resulting `nodes.py` line count and whether the selftest still passes (§4.6) |
| 11 | **Whether the target buyer requires runtime ownership** | Ask directly: *would you accept a hosted runtime holding your conversation data?* A clear yes keeps the C2 contradiction dormant and settles the generated-code fork for V1 in favour of a shared runtime. A refusal **for reasons spec-level ownership does not satisfy**, observed in a real procurement conversation, reopens it |
| 12 | **Cost to serve per episode** | Count per episode: turns, LLM calls, tool calls, tokens, cost; store on the episode record. First real unit-economics number, replacing a guess |
| 13 | **The residual market unknowns of §1.10** | **NexHealth Partner Program commercial terms** (the single most load-bearing one on the dental path), whether TrueLark's SMS/web-chat booking survived the Weave integration, and Jane/Boulevard/Zenoti/vet-PMS API terms — all require **a partner-program application or a vendor conversation**, not more searching |
| 14 | **Operator-voice failure data** | **Reddit was blocked to the researcher and no primary operator corpus was obtainable**; the public record is actively contaminated by fabricated abandonment statistics (§1.9). Only **direct operator conversation** produces this, and nothing in the public record may be substituted for it |
