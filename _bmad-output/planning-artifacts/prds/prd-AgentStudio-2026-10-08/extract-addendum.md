---
title: "Extract — Brief Addendum (for PRD prd-AgentStudio-2026-10-08)"
source: "_bmad-output/planning-artifacts/briefs/brief-AgentStudio-2026-10-07/addendum.md (859 lines, 68KB, read in full)"
created: 2026-10-08
---

# Extract: Brief Addendum

Organized under the twelve requested headings. Direct quotes are marked with quotation
marks or blockquotes; everything else is a faithful condensation. The addendum carries its
own **label discipline**, preserved here where it is load-bearing:

| Label | Meaning (addendum's own definition) |
| --- | --- |
| FACT | "Verified by reading the repository or a cited document; several cite file:line" |
| INTERPRETATION | "A defensible reading of those facts; not proven" |
| HYPOTHESIS | "An unproven bet" |
| VERIFIED | "Confirmed in a primary or near-primary source named in the memlog" |
| INFERRED | "Assembled by the researcher from indirect evidence" |
| UNVERIFIED | "Explicitly could not be confirmed; load-bearing where marked" |

The addendum states its own provenance: compiled from exactly two sources — the brief's
`.memlog.md` (65 entries, 2026-10-07) and the prior brainstorming session's
`convergence.md` (9 sections, derived from a 92-entry memlog).

**Scope note for the PRD author.** The addendum is an *evidence and rejection* document.
It is rich on rejected alternatives, architecture seams, market evidence and open
unknowns. It is **thin or silent** on: named personas, pricing/business model for the NEW
product line, a capability catalog, and the onboarding journey. Those gaps are recorded
explicitly under their headings below rather than padded.

---

## 1. Personas in depth

**Finding: the addendum contains no persona section and no named personas.** There are no
names, no jobs-to-be-done write-ups, no fears/success definitions. What it carries instead
is *buyer-class* and *operator-class* reasoning, which is the only persona-adjacent
material available:

- **Buyer centre matters more than buyer title.** The C2 rejection turns partly on this:
  the buyer for service/request qualification is "support/ops", a **cost centre**, "while
  C1/C3 sell to revenue centres". Revenue-centre buyers were treated as structurally
  preferable.
- **Runtime-ownership demand varies by buyer class.** C2 "maximises the hardest unresolved
  contradiction — enterprise runtime-ownership demand — whereas C3 nearly dissolves it".
  Appointment intake was credited with a "revenue-centre buyer with near-zero
  runtime-ownership demand".
- **The operator is the unvalidated actor.** The entire stress test's honest limit is that
  the specs "are the coach's constructions, not any real business's rules", and the
  **practised-vs-printed-policy gap** "is the likeliest place all four are wrong, **and
  only a real operator can close it**."
- **The operator's own failure vocabulary is an open unknown.** Open unknown 3: ask
  operators *"how would you know the agent did a bad job?"* and record the answer
  "**verbatim, without prompting**". If they cannot name one, "the
  evidence→evaluation→promotion loop has no customer-side signal and must be rebuilt
  around our own assertions only."
- **Consumer-side (end caller) acceptance, vendor-run survey (Zenoti's own):** "55% of
  salon and 71% of medspa clients" comfortable with an AI receptionist — "so ~45% of salon
  clients are not."
- **Four stress-test businesses** stand in for the business-persona diversity (they share
  no workflow): a **dental practice**, a **gym** (membership freeze awaiting a medical
  note), a **brewery** (a hold that expires), and a **garden centre / plant nursery** (the
  dying-plant claim). Note the recorded correction: "nursery" in brief v1 was "**mis-read**"
  as childcare; it is a "**plant nursery / garden centre**", and the correction
  "**materially strengthens the diversity argument**, because that request involves **no
  transaction at all**."

**PRD implication:** personas must be authored fresh for the PRD; the addendum supplies
only the constraint that persona work is *blocked on primary operator conversation* (2–3
real operators, per open unknown 1).

---

## 2. Rejected alternatives and the reason each was rejected

One entry per rejection. **⚠ NON-OBVIOUS** flags a rejection whose reason a reader of the
finished product would not infer.

### 2.1 Job-to-be-done candidates

| # | Rejected | Reason, as recorded |
| --- | --- | --- |
| R1 | **C2 — Service/request qualification** (the owner's *original* top rank) | "**Rejected on three independent strikes:** every plausible incumbent (Zendesk, Intercom, Freshdesk, ServiceNow) already ships inbound triage **and** owns the system of record; the buyer (support/ops) is a **cost centre** while C1/C3 sell to revenue centres; and it **maximises the hardest unresolved contradiction** — enterprise runtime-ownership demand". Plus its risk shape: "**persistent case lifecycle** … is product-shaped and open-ended, not bounded". ⚠ NON-OBVIOUS (the "cost centre" and "runtime-ownership" strikes are invisible from the product) |
| R2 | **C1 — Lead qualification, as a *primary* boilerplate** | Two architecture grounds: it is a "**misaligned-interest** conversation needing adaptive probing, evasion handling and scepticism toward self-reported facts — which **refuses to be configuration**"; and "its **evaluation observability is the worst** — false negatives are invisible, a wrongly disqualified good lead is gone and emits no signal." ⚠ NON-OBVIOUS (the invisible-false-negative argument is the load-bearing one) |
| R3 | **C1 — Lead qualification, commercially** | "Saturated and partly discredited." Salesforce/Qualified **$1.2B** closed April 2026; bundled by Intercom/HubSpot/Agentforce at outcome prices; "**CRM APIs all self-serve and open so integration is no moat at all**"; category trust damaged by the verified 11x misrepresentation |
| R4 | **C3 — Appointment intake** (had been promoted to *leading hypothesis*, "**explicitly never selected**") | "**Closed as a commercial opportunity.**" Occupied end-to-end (TrueLark/$35M/Weave, ServiceTitan, Mindbody since 2019, Podium, Zenoti); write-API gated or absent in most verticals; price ceiling already $99–199/location/month inside $400–600 software; "the real moat is **live-capacity calendar write access**, not conversation quality"; the trust wedge is "mostly occupied" with only counterfactual replay unoccupied "and it is worthless without that calendar write access" |
| R5 | **"An AI receptionist that books appointments"** | "**Rejected by hard condition**, user-stated: commoditised, and existing competitors must **not** become an excuse for building a worse copy. Not an acceptable thesis" |
| R6 | **Legal client intake** | "**Saturated eight weeks before the brief.** **Clio Grow AI, 2026-08-20**, is the proposed product shipped by the vendor owning distribution and the outcome data, at **$25 per converted lead**; and the two systems most needed — Clio, MyCase — are **the two least open**" + bar-opinion product requirements |
| — | **Internal operations** | **NOT rejected — unexamined.** "one of the user's three *original* candidate classes from the brainstorming session, flagged by a subagent as 'an unexamined third option'. It is not rejected; it is **unexamined**." ⚠ The only live untested candidate class |

### 2.2 The physio/Cliniko recommendation — made and withdrawn

**R7. WITHDRAWN by user course correction, coach accepted.** "The research correctly killed
'build another vertical AI receptionist/booking product' — which the user **never wanted** —
but the coach then wrongly concluded 'therefore build a physio booking agent on Cliniko',
**optimising for API accessibility and producing exactly the narrow vertical product the user
was avoiding.**"

Standing rule produced: research must answer *"is there a broad SMB class of problems where a
reusable conversational-agent architecture creates meaningful value"*, **not** *"which vertical
has the easiest public API"*. "**The user does not need an unsaturated vertical** — the point is
that the **same underlying product** is useful across many SMB contexts."

⚠ NON-OBVIOUS and the single most important rejection for this PRD: it is recorded as "the
**third occurrence of the same bias**" — architecture-convenience masquerading as product
judgment. The prior two: ranking candidates by architectural cleanliness, and "technically
impressive implies valuable". **Consequence: text-first vs voice was REOPENED** as a DECIDED
item, "on the grounds that it may have been architecture-driven rather than product-driven. It
was **not automatically reversed** — phone-heavy inbound volume does not by itself make voice
correct." Governing replacement question: "**for the specific problem eventually chosen, where
does the valuable interaction actually happen?**" *Inbound (vs outbound) remained decided
throughout.*

### 2.3 The per-vertical prohibition library — proposed then replaced

**R8.** *Proposed* (stress-test required change 8): "the builder needs a **prohibition and
escalation library per business category**". Motivation that **still stands** and is called
"the most safety-relevant finding of the stress test": "the prohibition list and urgency
triggers are the **least documented and most critical** content of a specification." For the
dental practice they exist "**in no document at all** — they are tacit professional/regulatory
knowledge. Eliciting *'what must your agent never do'* by open question **will produce a
dangerously short list.**"

*Replaced by:* "a **generic, domain-neutral guardrail library in the core** … **plus optional
domain packs as extension points, never core architecture** — and with **no packs in V1**."
Reason: "a per-category library makes vertical knowledge a core dependency, reintroducing the
vertical framing the project had just rejected, and it scales as the number of categories
rather than as the architecture." ⚠ NON-OBVIOUS (the scaling-axis argument).

### 2.4 The compiler framing — demoted and conditioned, not rejected

**R9.** "Generated code is no longer assumed necessary (DECIDED as a stance; the fork itself
**not** finally decided)." Of twelve claimed advantages of generated code, **only four are
genuine and they are one property** (see §3.2). And: "**The compiler model has an unstated
precondition — nobody ever edits the generated output.** One in-place tweak to a generated
`prompts.py`/`tools.py` and regeneration destroys the work; the compiler collapses into a
**one-shot scaffolder**." Holding it requires "either airtight round-tripping or a
read-only-generated-code contract **with teeth**." ⚠ NON-OBVIOUS.

Falsification conditions are recorded both ways:
- Evidence that would **keep** generated code: a target segment that *refuses* a hosted runtime
  for reasons spec-level ownership does not satisfy, "**observed in an actual procurement
  conversation**"; a recurring customer requirement no leaf/extension point can express; an
  incident where spec-version + runtime-compatibility-version proved insufficient; evidence
  artifact-level debugging materially beats spec + runtime version + episode trace on real
  incidents.
- Evidence that would **replace** it: spec-level ownership satisfying the actual buyer
  (confirmed in conversation); episode traces + spec version + runtime version reconstructing
  past behaviour well enough to debug real failures; observed (not predicted) variation fitting
  a limited config surface plus leaves; "the regeneration-destroys-local-edits trap continuing
  to bite."

### 2.5 Coach/model corrections applied in sequence (each a rejection of a prior formulation)

| # | Rejected formulation | Reason |
| --- | --- | --- |
| R10 | Fixed disposition set **answered \| action taken \| escalated \| out of scope** | "**Too appointment-specific.**" Replaced by: "every episode terminates in a **structured, evaluable business outcome**, with exact outcomes varying per business inside a **constrained outcome model**" |
| R11 | First constrained outcome model **fulfilled \| committed \| informed \| deferred \| refused** | "**fulfilled/committed did not separate cleanly** and **deferred was carrying three unrelated meanings.**" Replaced by **resolved_informational \| resolved_actioned \| refused \| escalated(reason class) \| PENDING** |
| R12 | **"Capacity blocked" as a platform invariant** | "It is a **booking example**, not a platform invariant" |
| R13 | **"Non-FAQ share" as a product metric** | "It is a **proof/evaluation concept**, not a universal product metric" |
| R14 | **"The builder is out of scope"** (the coach's cut) | "**Reversed by the user.** The ability to rapidly create a new business-specific agent is **central to the thesis** — without it, this is a generic runtime plus an assertion that it can be configured." ⚠ NON-OBVIOUS and directly load-bearing for the PRD's scope |
| R15 | **Coach to present branches** | "**Reversed:** the coach is to **lead** the product-definition process" |
| R16 | **"nursery" as childcare** | Mis-read; it is a plant nursery / garden centre; correction strengthens the diversity argument because the request "involves **no transaction at all**" |
| R17 | **Market research steering the product** | Standing instruction: "do **not** let it drag back toward 'find an empty vertical'; **a new market category need not be proven**" |
| R18 | **"Anything spanning sessions is out of scope"** (coach's boundary) | **"WRONG, as the user suspected."** Three of four stress-test examples *require* cross-session continuation (gym freeze awaiting a medical note; brewery hold expiring; garden-centre claim awaiting the horticulturist). "**Anything that defers or awaits a document is inherently multi-session, and that is most of the interesting behaviour.**" Diagnosis, recorded as the reusable part: "**the absence of a `pending` outcome kind from the coach's first model is what hid the finding.** A missing enum member silently defined a capability out of existence." Reclassified **IN scope and non-structural** — it "*follows from* `pending` rather than needing its own mechanism." ⚠ NON-OBVIOUS |

### 2.6 Positioning rejection (structural, §2 of the addendum)

**R19.** The convergence thesis — Agent Studio as "*the conversational intelligence and
execution layer above the customer's systems, joined to them by a key*" — survives as
architecture but **not as a commercial position**: "**the intelligence layer on top of someone
else's system of record is precisely the position the system-of-record owner bundles away.**
The architecture decision was right for the reasons given; **it is simply not a commercial
position.**" ⚠ NON-OBVIOUS and the deepest rejection in the file.

### 2.7 Cells the morphology says must stay empty (rejections at axis level)

| Axis | Leave empty | Reason, quoted |
| --- | --- | --- |
| Turn segmentation | model-based boundary, streaming-continuous | "In text, turns are discrete client messages. The whole axis is a voice artifact" |
| Evaluation timing | synchronous per turn | "Never put measurement on the reply path to learn what a recorded episode yields afterwards" |
| Behaviour promotion | automatic, threshold-automatic | "Silent learning was rejected. Empty **on purpose**, documented" |
| Personalisation | LLM-generated | "Buys warmth, costs a call, adds variance to a reply otherwise controlled" |
| Execution topology | external workflow engine | "Becoming a workflow platform was explicitly refused" |
| Action selection | fully agentic tool selection | "Incompatible with bounded actions and deterministic execution; the cell that makes safety and evaluation both intractable" |

Two further must-stay-empty cells: "**arbitrary control flow in custom code**" (destroys
evaluability) and "**a declarative schema that expresses computation**" (the "Python-in-JSON"
anti-goal). One cell is "**blocked, not empty**": deletion of `intent_detect`, "gated on
measurement."

---

## 3. Options-considered matrices / trade-off tables

### 3.1 The 32-axis morphological analysis (reproduced in substance)

The addendum restores the full axis table from the brainstorming memlog, noting "the option
ranges matter as much as the axis names, because the degenerate option is what makes an
assumption visible."

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

### 3.2 The four collapses — axes that are not independent

> "The session's most useful morphological finding was that several axes are dependent
> variables."

| Collapse | Finding, quoted/condensed |
| --- | --- |
| **Axes 3, 4, 7 are one axis** | Intent determination, goal representation and conversation policy are "near-collinear. Given an explicit goal object plus a state machine over what the job still needs, intent classification is **redundant** — the structure already knows the turn and the gap." Real single axis: "*does turn-level direction come from classifying the utterance, or from the structure of the unfinished job?*" |
| **Axis 8 is downstream of axis 5** | "Response generation is largely determined by information collection. With fixed slots the next utterance is a function of what is missing, so a template suffices; freeform generation earns its keep only where the next utterance is not determined by the gap" |
| **Axis 15 depends on 14; axis 16 partly on 11** | "Freshness is meaningless under agent-owned state and mandatory under external authority — a dependent variable. Action safety stops being independent once execution is deterministic, because **deterministic execution *is* the safety mechanism**" |
| **Axes 18, 21, 23 are one commitment** | "If 'external business outcome' is an evaluation target, episode identity is *forced* to generated-episode-id-plus-external-join-key. **Not a choice — an implication**, and one already accepted" |

**Six counterintuitive combinations collapsed into two principles.** Combinations 1, 2, 6 (no
explicit intent + implicit task state; deterministic response with LLM fallback;
deterministic-first with LLM escalation) = "**deterministic-first, LLM on escalation**."
Combinations 3, 4, 5 (external authority + bounded cache + explicit freshness policy;
structured action proposal with deterministic execution; versioned spec + episode evidence +
human promotion) = "**the agent proposes, something authoritative disposes**." "Both are
subtractive — they remove the model from the critical path for everything it is not uniquely
good at."

### 3.3 Cell states explicitly NOT decided (the open design space)

| Axis | State as recorded |
| --- | --- |
| **Knowledge authority** | "Explicitly **not decided**: embedded snapshot / versioned internal store / external source of truth / external + bounded cache" |
| **Retrieval mechanism** | "Explicitly **not decided**: deterministic lookup / lexical / dense / hybrid / external knowledge API" |
| **LLM / model strategy** | "Explicitly **not decided** … Principle 1 fixes the *posture*, not the call-site topology, which is **blocked on measurement**" |
| **Execution model vs deployment topology** | "Deliberately kept **orthogonal**; coupling them is the recorded error to avoid" |
| **Deployment ownership** | "Five separations explored (artifact, space, time, scale, customer condition); **conditional ownership by customer segment** is the most commercially plausible and is **unvalidated**" |
| **Interest alignment** (aligned vs misaligned) | "*Alignment, not domain, is the axis on which the conversational engine actually differs.*" C1 misaligned; C2/C3 aligned and near-twins |
| **Failure boundary** | "A declared axis — the reason the `failure` node survives the narrowing" |
| **Turn segmentation** | "**Entire axis removed** by text-first — the cells cease to exist rather than being abstracted" (but see R7: text-first itself reopened) |

### 3.4 The trust-feature audit of five candidate differentiators

| Candidate differentiator | Status |
| --- | --- |
| (a) per-conversation review | **Shipped** — ServiceTitan virtual agent scorecards + call summaries |
| (b) approval-before-commit | "**Shipped as Weave's DEFAULT** for most verticals: 'let AI Receptionist capture appointment requests, then let your team review and schedule'" |
| (c) rule authoring | **Shipped** — ServiceTitan: job types bookable per business unit, custom dispatch fees, escalation rules, KB upload, custom follow-up questions |
| (d) **counterfactual replay** (show how a rule change would have altered past conversations) | "**ABSENT from every vendor examined** — the only unoccupied cell" |
| (e) longitudinal quality | **Shipped** — ServiceTitan + a supervision "Command Center" announced at Pantheon 2026: "one way for your team to supervise all the agents, configure them, monitor their performance" |

Mindbody / Zenoti / Podium / PetDesk: "no public evidence either way, **leaning thin**."

### 3.5 The generated-code twelve-advantage triage

Of twelve claimed advantages, only **1 (customer ownership/portability), 4 (enterprise trust
story), 5 (deployment into the customer's VPC), 12 (offline/self-hosted execution)** genuinely
require an artifact — "**and all four are the same property**." The other eight break down
three ways: "**compensations for not having a good enough shared runtime** (2, 3, 10 → the leaf
contract; 6, 11 → deployment/supervision; 7 → versioned specs + runtime-compatibility
versioning)", one that "**converts into a tracing requirement** (8: 'show me the code that ran'
→ deterministic spec + runtime version + episode trace)", and one "**theoretical, not current**
(9: performance / specialisation)."

**Orthogonality warning, carried verbatim:** *"no generated application code" and "one process
serves everyone" are orthogonal concerns and must not be coupled.* "A shared interpreter is an
**execution-model** question; isolated instances, workers, containers and customer deployments
are a **deployment-topology** question. **Nothing in the session proved multi-tenancy**, and
nothing about adopting a shared runtime requires it."

### 3.6 Per-node classification of the current 15-node graph (all INTERPRETATION)

Narrowing assumptions: text-first, inbound, aligned-interest, deterministic-first,
agent-proposes/systems-dispose. The source "states explicitly that this section **is not a
refactor plan**: it is a prediction recorded so it can be checked later, and **no node is to be
deleted on its authority.**"

| Node | Verdict | Reasoning |
| --- | --- | --- |
| `planner` | Likely deleted | "Compound multi-step planning is an outbound / complex-sales affordance; aligned-interest intake is single-goal" |
| `plan_step` | Likely deleted | Same; "also the source of the graph's one sanctioned loop" |
| `enrichment` | "**Likely deleted — the clearest single casualty of Principle 1**" | "Spending an SLM call to phrase a tool result is exactly the call deterministic-first replaces with a template" |
| `intent_detect` | "**NEEDS MEASUREMENT before deciding**" | Collapses toward a small on-task / off-task / done discriminator, "but cutting it is a measurement decision, not an aesthetic one. **Do not delete before measuring**" |
| `chitchat` | Likely simplified | Becomes a deterministic/template path |
| `system` | Likely simplified | Reduced surface under a narrower job |
| `validator` | Likely simplified | "In text the pre-TTS sanitizer concern vanishes; what remains is policy and schema validation" |
| `hitl_gate` | "Likely simplified — relocated in kind" | "Becomes 'confirmation before a side effect', which is a **tool-contract property**, not a graph node" |
| `knowledge` | Likely survives | "Inbound callers ask things" |
| `closing` | "Likely survives — more important" | "Episode completion and structured disposition become central" |
| `tool_exec` | "Likely survives — strengthened" | "Must carry idempotency and transactional semantics" |
| `failure` | Likely survives | "The failure boundary is a declared axis" |
| `execution_validator` | "**PROMOTED**" | "Becomes the **contract assertion point** — where the evaluator makes its claims, per the C1 leaf-contract resolution" |
| `agentic_retrieval` | "**RELOCATED**" | "Survives as a **subsystem pulled out of the agent flow**, not as a node inside it" |

---

## 4. Market, sizing, pricing, business-model content

All three research strands were run by subagents over the web on **2026-10-07**.

### 4.1 The headline finding

"**The proposed product already existed under another name.**" **TrueLark** — "AI virtual
receptionist for appointment-based SMBs, scheduling/rescheduling/inquiries via SMS and web
chat", which the memlog records as "*verbatim the proposal*" — acquired by **Weave (NYSE:WEAV)
for $35M**, announced 2025-05-05, closed 2025-05-20; now **Weave AI Receptionist**, integrating
Dentrix / Eaglesoft / Open Dental. TrueLark verticals: dental, medical/aesthetics, salon/spa,
fitness.

Incumbents had already shipped text AI booking in **4 of 6** target verticals:

| Vendor | Vertical | Shipped capability | Pricing as recorded |
| --- | --- | --- | --- |
| ServiceTitan | Trades | Virtual Agent Inbound SMS — classifies booking intent, converses, checks capacity, books autonomously; GA US + Canada | not recorded |
| Mindbody Messenger[ai] | Salon/spa | Conversational booking over SMS / web chat / Facebook, since the **2019 Bowtie acquisition** | published **$99–199/location/month** |
| Weave / TrueLark | Dental, medical, med-spa | AI Receptionist | not recorded |
| Zenoti | Salon, med-spa | Voice-first; **text unverified** | not recorded |
| Podium AI Employee | Home services | AI employee | **$399–599/mo** core |
| Boulevard | Salon | **Not yet shipped** | — |
| Jane App | Physio/allied health | 2026 AI work is **scribe/charting, not booking** | — |

### 4.2 Per-vertical booking-API feasibility (kills the horizontal thesis independently of competition)

| Vertical | System of record / path | Status |
| --- | --- | --- |
| Dental | **NexHealth Synchronizer** — unified read/write across Dentrix G6.2+ / Eaglesoft / Open Dental, **8000+ locations** | CLEAN but **gated behind the Partner Program**; commercial terms **UNVERIFIED and load-bearing** |
| Dental | Open Dental own API | CLEAN |
| Physio | **Cliniko** — self-serve dev portal, Available Time + appointment write | CLEAN |
| Trades | ServiceTitan dev portal | CLEAN, but ServiceTitan "now **competes directly**" |
| Salon/spa | **Fresha** (largest by salon count) | "**NO write API**; read-only BI connector only" |
| Salon/spa | **Mindbody** | Gated partner program + "**metered Consumer Bookings approx $15/location + $2.50 per appointment booked**" (third-party figure, not vendor-published) |
| Allied health | **Jane App** | "**No official public API**" |
| Veterinary | ezyVet/IDEXX, Cornerstone, Covetrus | Partner-gated, **UNVERIFIED**; "**Vetstoria** already occupies the booking-integration slot across **30+ PMSs**" |
| Generic | Square Appointments | "Write requires the merchant on **Plus/Premium**; approx **6 countries**" |

### 4.3 Economics, with vendor-marketing caveats attached

- "The AI text layer is **already priced at $99–199/location/month**, bundled inside software
  the business already pays **$400–600/month** for. **That is the ceiling, and it is set by
  incumbents who bundle.**"
- Human comparables: answering services **$100–400/mo** (overage **$0.75–1.50/min**); virtual
  receptionists **$165–2100/mo**.
- **Unusable — vendor marketing:** 411 Locals "37.8% answered"; AMBS "$126k/yr lost". "Both are
  vendor-published category stats with no independent basis and **must not be cited**."
- "**Most defensible independent-ish figure: CallRail, Jan-2025, over 1.1M leads**" —
  missed-call rates **32% healthcare, 28% legal, 14% home services, 9% real estate**. Caveat:
  "this is *far below the 62% the category sells on*, i.e. the industry's headline missed-call
  number is **inflated by roughly a factor of two** against the best available data. CallRail
  is itself a vendor, hence 'independent-**ish**'."
- No-shows: "**~23% meta across 105 studies**; dental 15–20%, vet 10–12%."
- "**No independent per-vertical appointment-value dataset was found.** Any per-booking value
  used downstream is therefore an assumption, not a finding."
- "Human services are **converting to AI, not being chosen over it**": Smith.ai sells both —
  AI-first free/25 calls up to **$800/500 calls ($1.60–2.00 per call)** vs human-first
  **$300/30 up to $2100/300 ($7–10 per call)** — "a **4–5x price gap for the same job**". Ruby
  stays human at $250/50min to $1725/500min. **Counter-signal:** "**Mindbody sells a cheaper
  'Messenger' tier that strips the AI front desk out** — a de-adoption path shipped as a SKU."
- Consumer acceptance (Zenoti's own survey): 55% salon / 71% medspa comfortable → "~45% of
  salon clients are not."

### 4.4 Channel and compliance (GTM-shaping)

- US contact preference: "**text 33%, email 28%, web chat 21%, phone 18%** — **SMS-vendor
  research**, so directionally self-serving. **The countervailing fact: inbound to these
  businesses is still phone-led**, which is why **every funded competitor is voice-first** with
  text as the second channel."
- "Region forks GTM: **US/UK/CA/AU/N-Europe are SMS-primary**; **WhatsApp dominates
  LatAm/S-Europe/India/MEA**."
- "**US A2P 10DLC is mandatory**: brand **$46 one-time**; campaign **$15 one-time + $10/mo**
  (Agents & Franchises **$30/mo**); carrier surcharges per segment. **2026 tightening** includes
  **EIN ≥15 days**, carrier-verifiable opt-in URLs, and **Reseller ID mandatory when registering
  on behalf of another entity**. Consequence: **per-tenant onboarding friction that bundled
  incumbents absorb and a solo developer would not.**"
- "**WhatsApp**: per-message pricing since 2025-07-01; from **2026-02-16** Meta charges 'AI
  Providers' **$0.0691/message** for non-template messages (**Italy first**). The definition of
  'AI Provider' is loose — recorded as **tail risk**."

### 4.5 Adjacent-category consolidation and outcome pricing

- **Salesforce acquired Qualified (Piper) for $1.2B**, closed April 2026 — "**VERIFIED in
  Salesforce FY2026 10-Q**."
- Outcome pricing is the incumbent norm: **Intercom Fin for Sales $9.99 per qualified lead**;
  **HubSpot Breeze ~$0.50/resolution**; **Agentforce ~$2/conversation**; **Clio Grow AI $25 per
  converted lead** (nothing if no conversion, spend caps available).
- "**CRM APIs are all self-serve and open** (HubSpot, Pipedrive incl. Lite tier, Salesforce,
  Zoho) — so integration is **no moat** in this category, the inverse of the booking case."
- Category trust damage: "**TechCrunch 2025-03-24** verified that **11x** displayed non-customer
  logos (**ZoomInfo denied and threatened legal action**); **~$14M claimed ARR vs ~$3M surviving
  contracts**; an employee cited **70–80% inbound churn**; CEO stepped down ~May 2025." Still:
  "funding continued (**Artisan $25M, Regie $30M**) — saturated and consolidating rather than
  collapsing."

### 4.6 Adoption: "shipped-but-dark" is FALSE, but "shipped-and-FENCED"

| Source | Figure |
| --- | --- |
| ServiceTitan Q2 FY2027 (2026-09-09) | "virtual agent **revenue and call volume each more than doubled sequentially**"; the 10-K calls Virtual Agents "**in early adoption**" |
| Weave Q1 FY2026 | "**more than 50% of locations use at least one embedded AI feature**" + **300% increase in AI interactions** |
| Weave Q2 | **70M AI interactions, +165%**; **14.5M calls analyzed**; **810K unscheduled opportunities** |

Caveats: "'at least one embedded AI feature' is **vague** — it spans missed-call text-back and
transcription, **not the receptionist**"; and "**no vendor discloses an attach rate for the
booking feature specifically, and none discloses a disable/abandonment metric.**"

"**Shipped-and-FENCED, not shipped-and-dark.** Both public vendors fence the agent to
**overflow and after-hours by default** and expand 'incrementally' — management's own words."
ServiceTitan's CFO: *"many customers start with overflow and after hours... now we also have
customers that opt to let VA handle incrementally more and more volume."* INTERPRETATION:
"operators enable it in the window where a mistake costs least; **that fencing is a trust
deficit expressed as configuration**."

### 4.7 The real moat

"**The real moat is not conversation quality or explainability — it is write access to the
calendar with live capacity.**" ServiceTitan has "Adaptive Capacity"; "**Weave's AI Receptionist
books directly only into qualified dental PMSs, every other vertical is CAPTURE-ONLY.**"
ServiceTitan reports "a **70% booking rate including capacity constraints vs 90% excluding
them**" — "the dominant failure is that *the calendar had nothing to offer*, a business-rules
and capacity problem, **not comprehension**. No amount of rule transparency fixes it."

### 4.8 The structural finding on system-of-record bundling (3 for 3)

| Job | System-of-record owner that bundled it |
| --- | --- |
| Appointment intake | ServiceTitan; Mindbody; Weave (via TrueLark, $35M) |
| Inbound lead qualification | Salesforce (via Qualified, $1.2B); HubSpot; Intercom |
| Legal client intake | Clio (Grow AI, 2026-08-20) |

Four independently sufficient mechanisms: (1) "**It controls the write API** — and can gate a
third party's access to it"; (2) "**It owns distribution** — the feature arrives as a toggle
inside software the business already pays for"; (3) "**It owns the historical outcome data**
needed to score"; (4) "**It can price on outcome, because it alone observes the outcome.**"

Second-order architecture implication: "Outcome pricing *requires measuring outcomes*, which
requires the **join key and the evidence loop**… outcome pricing is **structurally easier for
whoever owns the system of record**: **a third party without the join key cannot price that way
at all.**"

### 4.9 Research-integrity warning — "the most reusable lesson in the file"

"The AI-receptionist query space is contaminated by vendor SEO spam **including fabricated
statistics**." Documented instance: a **Swiss Monkey** page titled *"AI Virtual Receptionist for
Dental Office Reddit Reviews"* asserting "**60% of practices receive patient complaints within
the first month**" and "**40% abandon AI systems within three months**" — "with **no citations,
no thread links, and two unverifiable handles**."

"**The mechanism: Swiss Monkey sells remote human dental front-office staffing — the product
those statistics argue for.** The abandonment narrative that would justify building this exact
product is being **manufactured by the competitors of AI receptionists**, dressed as user-voice
evidence ('Reddit reviews') precisely because user-voice evidence is what a researcher goes
looking for and cannot easily check."

Generalised rule: "when a statistic is the exact number needed to justify a purchase, check who
sells the alternative before citing it; and treat a page that *claims* to summarise a primary
community corpus, without linking a single thread, as **fabricated until a thread is
produced**." Compounding gap: "**Reddit was blocked to the researcher**, so **no primary
operator-voice corpus was obtainable at all.** Any section on failure taxonomy rests on no
reliable public data and **must not be treated as evidence**."

### 4.10 Business model for the NEW product line

**Not present.** The addendum contains no pricing, packaging or business-model proposal for the
channel-independent business-specific Agent platform. All pricing content is competitor
pricing. The nearest thing to a business-model constraint is §4.8's conclusion that outcome
pricing is unavailable to a non-SoR-owner, and §4.3's ceiling finding. Also recorded as a
standing instruction (R17): "**a new market category need not be proven**."

---

## 5. Capability catalog

The addendum has no formal capability catalog. What it enumerates:

**Tools/actions named (from the dental stress-test spec, the one spec partially reproduced in
the addendum's sibling file and referenced here):** `get_patient_leaflet(procedure)`,
`get_fee_band(procedure, nhs_or_private)`, `verify_patient(identifier)`,
`check_availability(appointment_type)` — fresh read, `book_appointment(...)` — write with
confirmation before execution, `flag_urgent_to_practice(...)`. *(Enumerated in
`spec-stress-test.md`; the addendum references the spec rather than reprinting it.)*

**Integrations contemplated** (all from the market strand, all as *systems of record* rather
than as a roadmap): NexHealth Synchronizer, Open Dental, Cliniko, ServiceTitan, Fresha,
Mindbody, Jane App, ezyVet/IDEXX/Cornerstone/Covetrus, Square Appointments, HubSpot, Pipedrive,
Salesforce, Zoho, Clio, MyCase. Channels: SMS (A2P 10DLC), WhatsApp, web chat, email, phone.

**How capabilities are granted or bounded — the governing rules:**

1. **Three-level escape hatch, conceptually preserved:** "**configuration → supported extension
   point → custom implementation**." The escape hatch "must be **intentional**."
2. **C1 resolution (DECIDED): "custom code exists as controlled leaves, never as arbitrary
   control flow."** Control flow — "what the agent asks, in what order, action gates,
   escalation, completion — lives **in the specification only**: interpretable, diffable,
   assertable, promotable." Leaves — "tool implementations, field validators, formatters,
   scorers, auth adapters" — "may be **arbitrary code behind a declared contract** (signature,
   pre/post conditions, failure modes, latency budget)."
3. **Proof test, verbatim:** "**the evaluator asserts over the contract, never over the
   implementation.**" "This is why the schema never grows toward Python-in-JSON: it never
   expresses computation, only **sequence, condition and policy**."
4. **Declared anti-goal:** "*a gigantic declarative schema representing every possible
   behaviour* — moving complexity from Python into JSON."
5. **Action safety is structural, not a feature:** "Action safety stops being independent once
   execution is deterministic, because **deterministic execution *is* the safety mechanism**."
   And the empty cell: "fully agentic tool selection" is "**incompatible with bounded actions
   and deterministic execution**."
6. **Tools reached through declared contracts; reads classified by consequence** (Seam 3).
7. **`tool_exec` must carry idempotency and transactional semantics**; "degree is use-case
   dependent".
8. **Confirmation before a side effect is a tool-contract property, not a graph node**
   (`hitl_gate` relocation).
9. **Generic, domain-neutral guardrail library in the core** (the replacement for the rejected
   per-vertical library): "do not invent business facts; do not act outside declared authority;
   do not perform undeclared actions; do not claim an action succeeded without evidence;
   escalate when required authority or evidence is unavailable" — "**plus optional domain packs
   as extension points, never core architecture** — and with **no packs in V1**."
10. **Decision authority classes** (structural change 4): **informational / liability-bearing /
    state-changing, separately gated.**

---

## 6. Business Specification content

This is the core product object. Everything the addendum says about it:

### 6.1 The Specification is one of four artifacts, and is the only mutable-by-review one

| Artifact | Holds | Mutability |
| --- | --- | --- |
| **Specification** | Intended behaviour | "Changed only by deliberate, reviewed promotion" |
| **Evidence** | "What actually happened (episodes, traces, outcomes)" | Append-only |
| **Evaluation** | "What we judged to be wrong, and why" | "Append-only, versioned per agent version" |
| **Deliberate changes** | "What we chose to promote into the spec" | "Reviewable, revertable, attributable" |

INTERPRETATION attached, and it is a product thesis in itself: "these four have the shape of
version control — spec = checked-in state, evidence = the working tree, promotion = **a pull
request on behaviour**. This collapses two subsystems into one: **the product's job is not to
measure conversational quality objectively** (quality is irreducibly contested) **but to make
disagreement cheap to express and fast to propagate** — substantially lighter to build, because
it never has to define 'good' in general, only what was wrong *here*."

### 6.2 The specification is NOT a prompt and NOT generated code (Seam 2)

"**Seam 2 — Versioned specification (not a generated prompt, not generated code).**" Why
retrofit is prohibitively expensive: "if intended behaviour lives as prose inside generated
Python, then **diffing behaviour, asserting over behaviour, reviewing a proposed change,
reverting a regression, and attributing an outcome to a version are all unavailable**.
Introducing versioning later requires reconstructing the intended behaviour of every past agent
from code that has already drifted — and **every evaluation record collected before the spec
existed has nothing stable to be *about***. **Evaluation criteria in particular must live inside
the durable spec rather than being recreated per generation.**"

### 6.3 The spec's shape: thirteen invariant fields

**The strongest empirical result in the whole brief package:** "**all 13 schema fields were
invariant** across four businesses **sharing no workflow**; every substantive difference was
configuration; **no case required custom implementation**."

The addendum names the two fields "that felt most likely to be vertical-specific" and were
"load-bearing everywhere": **questions permitted** and **must not infer or do**.

The full thirteen are enumerated in the sibling file
`brief-AgentStudio-2026-10-07/spec-stress-test.md` (the addendum references rather than
reprints them). As written there for the dental case, the field set is: **authoritative
sources · rules and policies · questions permitted · decisions permitted · actions available ·
escalation conditions · refusal conditions · evidence recorded · successful completion · must
not infer or do · information needed · goal(s) · deliberate failure case**. *(PRD author: pull
the canonical list from `spec-stress-test.md`, not from this extract.)*

Notable shape details visible in the quoted dental spec: authoritative sources are
**versioned** ("practice-approved patient information leaflets, versioned") and some are marked
**external and authoritative** ("appointment availability *(external, authoritative)*"); actions
carry their consequence class inline ("`check_availability(appointment_type)` — fresh read ·
`book_appointment(...)` — write, confirmation before execution"); evidence recorded includes "a
**grounding citation for every clinical-sounding sentence**"; and successful completion admits
escalation as success ("the episode was escalated on an urgency trigger, **which is a success
and not a failure**").

### 6.4 What the primitive set REFUSES — the argument that it is a primitive set, not a framework

Quoted: "the primitive set **refuses** things — **no reasoning unanchored to a declared goal,
no decision outside an authority class, no claim without a source, no action without a
contract, no episode without a terminal outcome** — **which means it is a primitive set, not a
framework**."

### 6.5 The resolution / outcome model (twice revised)

Current (structural change 1): **`resolved_informational` | `resolved_actioned` | `refused` |
`escalated(reason class)` | `PENDING`**.

History and reasons (also in §2.5): the first fixed disposition set (answered | action taken |
escalated | out of scope) was "too appointment-specific"; the first constrained outcome model
(fulfilled | committed | informed | deferred | refused) failed because "fulfilled/committed did
not separate cleanly" and "deferred was carrying three unrelated meanings." The governing rule
that survived: "every episode terminates in a **structured, evaluable business outcome**, with
exact outcomes varying per business inside a **constrained outcome model**."

`PENDING` is load-bearing beyond resolution: its absence "**is what hid the finding**" that
cross-session continuation is in scope, and with it present, cross-session continuation
"*follows from* `pending` rather than needing its own mechanism."

### 6.6 The four structural changes the spec still needs (stress-test verdict B)

**VERDICT: B — "the abstraction needs changes before architecture."** Not C (abstraction wrong)
because of the 13-field invariance; not A (ready as-is) because "**four of the eight required
changes are structural**."

**Structural:**
1. **Replace the resolution model** (done — see §6.5).
2. **Support multi-goal episodes and goal switching** — "the garden-centre customer has two
   goals, may not know which, and the second is conditional on the first."
3. **Add a pre-emptive gate before goal recognition that can abort the episode** — "Dental
   urgency interception **has no home in an 11-step pattern that starts at 'understand what the
   person wants'**."
4. **Add decision authority classes** (informational / liability-bearing / state-changing,
   separately gated).

**Non-structural:**
5. Cross-session continuation is IN scope.
6. **Split "information needed" into two kinds** — "**obligations** (must be true before an
   action) and **diagnostic evidence** (gathered to support a judgement, **no fixed sufficient
   set**)."
7. **Version-pin knowledge sources** — "else two agents differ by leaflet revision and **a spec
   diff shows nothing**."
8. The prohibition library (since replaced — §2.3).

### 6.7 The sharpest new finding: cause vs fault

> "**inferring a CAUSE and determining FAULT are different acts with different consequences.**"

The garden-centre case: the agent may say *"daily watering is almost certainly the problem"*
(grounded care advice) but may **not** conclude *"therefore this is neglect, which is excluded,
claim denied"* — "that is a **liability determination made on its own authority**. **Nothing in
the prior model distinguished them.** This is what forces **decision authority classes**."

### 6.8 Other spec-level commitments (all DECIDED)

- "external systems remain authoritative (recorded as '**the most consequential inversion of
  the session**')"
- "freshness is declared per read / per tool contract, **never globally**"; "reads that gate a
  side effect **must be fresh**"; "conversational/contextual reads may tolerate bounded
  staleness"
- "evidence is durable (**runtime evidence is product data, not operational logs**)"
- "the specification is versioned"
- "evaluation and correction **do not silently mutate production behaviour**"
- "behaviour changes are **reviewable, promotable and revertable**"
- "custom code exists as controlled leaves, never as arbitrary control flow"
- "generated code is no longer assumed necessary"
- "**customer ownership and runtime ownership are separate concepts**"

### 6.9 The honest limit of all spec validation to date

Recorded verbatim in substance: "it validates that the schema can **EXPRESS** four dissimilar
businesses. It does **not** validate that an agent built from such a spec **BEHAVES** well, nor
that the specs are **correct** — **they are the coach's constructions, not any real business's
rules.** The **practised-vs-printed-policy gap** is the likeliest place all four are wrong,
**and only a real operator can close it.**"

---

## 7. Onboarding depth

**Thin in the addendum; what exists is load-bearing and short.**

The one full statement of the onboarding journey comes from the reversal of the coach's
out-of-scope cut (R14):

> "The ability to rapidly create a new business-specific agent is **central to the thesis** —
> without it, this is a generic runtime plus an assertion that it can be configured. **Minimal
> version suffices: business conversation + source material → draft specification →
> validate/self-test → deploy, human review in the loop.**"

That is the contemplated journey in full: four stages plus a human review gate.

**Named friction points:**

1. **The hardest content to elicit is the prohibition list.** "The prohibition list and urgency
   triggers are the **least documented and most critical** content of a specification." For the
   dental practice they exist "**in no document at all** — they are tacit
   professional/regulatory knowledge." And decisively: "Eliciting *'what must your agent never
   do'* **by open question will produce a dangerously short list.**" The implication for
   onboarding design is that this field cannot be collected by asking an open question — yet the
   per-category library that would have solved it was rejected (R8), leaving the generic core
   guardrails plus elicitation design as the only answer in V1.
2. **The practised-vs-printed-policy gap.** Source material (printed policy) may not match the
   business's real rules; this is "the likeliest place all four [stress-test specs] are wrong."
   Onboarding that ingests documents alone inherits this error.
3. **Knowledge sources must be version-pinned at onboarding** (non-structural change 7), "else
   two agents differ by leaflet revision and **a spec diff shows nothing**."
4. **Per-tenant channel registration friction** (if SMS is a channel): A2P 10DLC brand/campaign
   registration, EIN ≥15 days, carrier-verifiable opt-in URLs, Reseller ID when registering on
   behalf of another entity — "**per-tenant onboarding friction that bundled incumbents absorb
   and a solo developer would not.**"

**Automated vs asked:** the addendum does not resolve this split. The nearest measurable
commitment is open unknown 2's third measurement: "**setup effort** in wall-clock and
source-artifact count (**fail if it does not fall materially**)" across four businesses built in
sequence. Open unknown 4 bounds the ask side: "**more than ~1 new schema concept per customer
means the config surface is growing into the forbidden DSL.**"

---

## 8. Trust, safety, authorization, approval and escalation (product level)

1. **Trust, not capability, is the market gap — and it shows up as configuration.** The
   fencing finding: incumbents default the agent to "**overflow and after-hours**" and expand
   "incrementally". INTERPRETATION: "operators enable it in the window where a mistake costs
   least; **that fencing is a trust deficit expressed as configuration**." Direct product
   implication: a platform asking a business to hand an Agent its real work must earn the
   un-fencing.
2. **Approval-before-commit is table stakes, not a differentiator** — it is "**Weave's
   DEFAULT** for most verticals". Per-conversation review, rule authoring and longitudinal
   quality are also all shipped. **Only counterfactual replay is unoccupied** — "show how a rule
   change would have altered past conversations" — and in the booking context it was judged
   worthless without calendar write access. In a channel-independent platform that caveat does
   not obviously carry, which makes (d) the one trust feature worth re-examining for this PRD.
3. **Decision authority classes** (structural change 4): **informational / liability-bearing /
   state-changing, separately gated.** Forced by the cause-vs-fault finding (§6.7): the Agent
   may infer a cause but may not make a liability determination on its own authority.
4. **The pre-emptive gate** (structural change 3): a gate that runs **before** goal recognition
   and "**can abort the episode**". Motivated by dental urgency interception: any mention of
   pain, swelling, bleeding, fever or trauma escalates immediately "**and the explanation path
   is abandoned rather than continued**."
5. **Escalation as success.** "the episode was escalated on an urgency trigger, **which is a
   success and not a failure**."
6. **The core guardrails** (domain-neutral, in core, no domain packs in V1): "do not invent
   business facts; do not act outside declared authority; do not perform undeclared actions; do
   not claim an action succeeded without evidence; escalate when required authority or evidence
   is unavailable."
7. **Principle 2 — "the agent proposes, authoritative systems dispose" (DECIDED).** "The LLM
   decides *what it wants to do* and emits a structured action proposal; **it never controls
   execution.** Execution is deterministic, bounded, validated against a declared contract, and
   gated where consequences require it."
8. **Silent learning is rejected.** "Behaviour promotion: automatic, threshold-automatic —
   **empty on purpose, documented**." "Evaluation and correction do not silently mutate
   production behaviour."
9. **Confirmation before a side effect is a tool-contract property**, not a graph node.
10. **The evaluation trap that is a safety issue** (and generalises beyond C1): "Where false
    negatives are invisible, an outcome-driven improvement loop **rewards drift toward
    strictness**: conversion among passed leads rises while total revenue falls. **Selection
    bias with a feedback loop attached, self-reinforcing.**" Counterweights — "holdouts, forced
    random pass-through, human adjudication of rejections". Consequence, stated as a rule:
    "**the evaluation architecture is use-case-specific even where the execution architecture is
    not**", and "**a candidate with no feasible counterweight must not be chosen** — its
    improvement loop actively degrades the business."
11. **Regulatory pattern (from legal intake; generalises to any regulated vertical the platform
    serves).** Three bar opinions, all read "**via secondary summaries; the opinions were not
    fetched first-hand**" (explicit evidence gap): **Alabama Formal Op. 2026-01** (a chatbot
    giving specific legal advice without an "I am not an attorney" disclaimer and without
    attorney review may be **UPL**; the deploying lawyer is liable); **Oregon Op. 2026-208**
    (permitted if the lawyer stays competent and "**supervises the vendor as a nonlawyer
    assistant**", discloses nonlawyer status, protects prospective-client confidences);
    **Florida Op. 24-1** (disclose AI; the lawyer owns everything the bot says; the bot must
    screen conflicts and avoid contacting represented parties). Derived product requirements:
    "AI disclosure on every channel; **collect-and-screen only, no advice**; conflicts check
    before substantive intake; … **the vendor is contractually a supervised nonlawyer assistant
    with no training on client data**."
12. **Consumer non-acceptance is a design input:** "~45% of salon clients are **not**
    comfortable with an AI receptionist."

---

## 9. Mechanism / technical-how decisions — **ADDENDUM-DESTINED**

> Everything in this section belongs in the PRD's own addendum, not its body.

### 9.1 The two principles

**Principle 1 — Deterministic-first, LLM escalation (DECIDED as a principle).** "Deterministic
logic runs first; the LLM is invoked where deterministic logic cannot confidently resolve."
Corollaries: "do not spend a model call generating a reply you already know after a successful
tool call (template the known reply, LLM as fallback); do not classify every turn if the job
structure already supplies direction." **Caveat attached by the owner and kept:** "this
principle must **not** be applied for elegance. Selection comes from the actual job and its
failure, latency and business constraints — and **the hot path must be measured first**."

**Principle 2 — The agent proposes, authoritative systems dispose (DECIDED as a principle).**
See §8.7.

### 9.2 The three seams that are expensive to retrofit

Governing V1 rule (HYPOTHESIS, accepted as working discipline): "**build the narrowest valuable
case, but refuse anything that structurally forecloses the hard case.**" The test is "not 'is it
hard' but **cheap vs prohibitively expensive to retrofit**." Additive later and therefore *not*
seams: adaptive probing, transactional tool semantics, persistent case lifecycle, hybrid
retrieval. "Exactly three things are not."

**Seam 1 — Episode evidence + identity (episode ID and external join key).** "**Un-recorded
episodes are gone forever**; there is no backfill for a conversation that was never written
down." The evidence has "**two tiers with different plumbing**": *interaction-quality* signals
are "dense, immediate, computable from the episode alone, and mostly deterministic assertions
requiring no judge"; *hard outcomes* are "sparse, delayed, and arrive from outside (CRM,
ticketing, calendar)." "The consequence nobody lists: **every episode needs a join key into the
operator's system of record**, or 'later downstream outcome' is permanently unobtainable."

**Seam 2 — Versioned specification.** See §6.2. Related trap (INTERPRETATION): the
generated-agents-are-disposable model's unstated precondition (§2.4).

**Seam 3 — The external-system boundary.** Four coupled commitments: "external state is
authoritative; freshness is declared, not assumed; tools are reached through declared contracts;
reads are classified by consequence." Why retrofit is prohibitive: "the **authority question
determines where truth lives**, and therefore what the agent is allowed to assume between
turns… **inverting authority later rewrites the data layer, the tool layer and the reply path
simultaneously**. Freshness-per-contract cannot be added as a flag to tools that were never
classified by consequence."

**INTERPRETATION with latency teeth, and it undercuts the whole latency thread:** "because the
agent holds no authoritative state, decisions must be made against **freshly read** external
state, so **external tool I/O may dominate the reply path rather than sequential LLM calls** —
which means the whole 'where does intelligence live / reduce LLM calls' thread rests on an
**unmeasured premise**, and **observability must precede optimisation**."

"These three bind as architecture constraints **even before the product is chosen**."

### 9.3 C3 — separation by consequence class (DECIDED, four coupled decisions)

Freshness declared per read/per tool contract, never globally; "reads that gate a side effect
must be fresh — **stale means double-booking, a real-world failure, a refund**";
conversational/contextual reads may tolerate bounded staleness — "being wrong **costs a
sentence**." The structural payoff: "side-effect-gating reads **happen once, near the end of an
episode, not on every turn**, and **that is what makes the latency budget honest**." Flagged
for measurement: "if side-effect-gating reads turn out to occur per turn, the latency budget is
not honest and the freshness model needs rework." Framed as "the same move as the leaf contract
(C1) applied to **data instead of code**."

### 9.4 C2 — the ownership boundary, and forking

Resolution (DECIDED): "**customer ownership and runtime ownership are separate concepts.**" Five
separations were attempted — by artifact, by space, by time, by scale, by customer condition.
The one that held, quoted verbatim:

> "**Customer ownership can extend as far as we can preserve a stable behavioural contract.
> Above that boundary, the system becomes a *fork* rather than an Agent Studio agent.**"

The gradient behind it: "modify the control-flow spec → still evaluable, because the spec is
structured. Modify leaf code → still evaluable, via the contract. **Modify the runtime → we
lose the ability to reason about what the system is doing.**" Current favoured boundary
("explicitly not final"): "the customer owns the agent definition + their data + the deployment
choice; Agent Studio owns the core runtime and the evolution of behaviour; extensions are
customer-controlled leaves behind stable contracts; every behaviour change is versioned and
promotable rather than silently learned." Kept because it was "**derived from a constraint, not
chosen by preference**." The residual: "the **architectural** contradiction dissolved, the
**commercial** one (ownership) did not."

### 9.5 Current implementation facts (all cited to repo in the source)

- **The graph is 15 nodes, not 4 stages.** FACT, verified at `boilerplate/graph.py:188-239`:
  `intent_detect`, `knowledge`, `agentic_retrieval`, `chitchat`, `closing`, `system`, `planner`,
  `plan_step`, `think`, `hitl_gate`, `tool_exec`, `execution_validator`, `failure`,
  `enrichment`, `validator`; six conditional routers (`route_by_intent`,
  `route_after_planner`, `route_after_plan_step`, `route_after_think`, `route_after_hitl`,
  `route_after_execution`); compiles with **MemorySaver by default**. "The four-stage Intent →
  Think → Tool → Enrich pipeline … **was a conceptual summary**."
- **Size/call-site distribution.** `boilerplate/nodes.py` is **1776 lines** — "roughly **22% of
  the 8229-line engine+platform tree**, and about **twice the next-largest file**" — with **six
  direct LLM call sites** (`INTENT_MODEL` ×1, `ANSWER_MODEL` ×4, `ENRICH_MODEL` ×1);
  `rag_subgraph.py` adds two (**8 total**). `rag_subgraph.py` (164 lines) and `filler.py` (90
  lines) are "among the **thinnest** files."
  INTERPRETATION: "the subsystems the emerging architecture wants to **promote** (retrieval as a
  subsystem, evaluation as a first-class concern) are currently the **smallest** files, while
  the monolith the narrowing wants to **shrink** is the **largest**. The right question was
  never 'is Intent → Think → Tool → Enrich correct' — that is a caricature — but **which of the
  fifteen nodes survive the narrowing**."
- **Durable storage is two SQLite tables** (FACT, `builder_platform/storage/schema.sql`):
  `sessions` (`session_id`, `created_at`, `last_active`, `active`) and `built_agents`
  (`agent_name`, `project_path`, `system_prompt`, `selftest_status`, timestamps). "**There is no
  table capable of recording a conversation, a turn, a tool call, an outcome or a latency.**"
  Runtime conversation state is **MemorySaver** (`graph.py:239`); `runtime.py:137` states state
  is carried across turns "*without us persisting the transcript*"; "durable checkpointing is
  left as an **unexercised option**."
  INTERPRETATION, the sharpest line in the section: "**build-time facts are durable, run-time
  facts are ephemeral.** `selftest_status` is a **build-time** quality gate standing in for a
  **run-time** quality signal. The improvement loop — builder and operator as one continuous
  product loop — currently has **zero substrate; the circuit is physically open.** **This is
  exactly Seam 1.**"

---

## 10. Qualitative / experiential intent — VERBATIM

The addendum carries no tone/voice/character section (no persona voice, no copy guidelines). The
only experiential and character statements present are these, quoted exactly:

- On what the product is for: "the product's job is **not to measure conversational quality
  objectively** (quality is irreducibly contested) but to make **disagreement cheap to express
  and fast to propagate**"
- On the spec-as-version-control feel: "spec = checked-in state, evidence = the working tree,
  promotion = **a pull request on behaviour**"
- On refusal as character: "the primitive set **refuses** things — no reasoning unanchored to a
  declared goal, no decision outside an authority class, no claim without a source, no action
  without a contract, no episode without a terminal outcome — **which means it is a primitive
  set, not a framework**"
- On the posture of both principles: "**Both are subtractive** — they remove the model from the
  critical path for everything it is not uniquely good at."
- On escalation: "the episode was escalated on an urgency trigger, **which is a success and not
  a failure**"
- On the thesis the builder serves: "The ability to rapidly create a new business-specific agent
  is **central to the thesis** — without it, this is a generic runtime plus an assertion that it
  can be configured."
- On the ownership boundary: "**Above that boundary, the system becomes a *fork* rather than an
  Agent Studio agent.**"
- On what is not wanted, user-stated hard condition: existing competitors must "**not** become
  an excuse for building a worse copy"
- On breadth over niche: "**The user does not need an unsaturated vertical** — the point is that
  the **same underlying product** is useful across many SMB contexts."
- On market framing: "**a new market category need not be proven**"
- On discipline: "this principle must **not** be applied for elegance"
- On predictions: this section "**is not a refactor plan**: it is a prediction recorded so it
  can be checked later, and **no node is to be deleted on its authority**"
- On the pre-emptive gate's motivation: urgency interception "**has no home in an 11-step
  pattern that starts at 'understand what the person wants'**"
- On fencing: "that fencing is **a trust deficit expressed as configuration**"

---

## 11. Relationship to the existing voice Agent Studio — reuse, migration, continuity

### 11.1 What text-first removes outright

FACT — these files/concerns are voice-specific: `boilerplate/filler.py` (pre-think filler +
per-tool filler banks); **sentence-chunking of the final reply**;
`builder_platform/sanitizer.py` (pre-TTS backstop); `builder_platform/vapi_adapter.py`;
`builder_platform/vapi_control.py`; `builder_platform/tunnel.py`; "**and the entire
turn-segmentation axis** — barge-in, interruption, endpointing, corrected-transcript dedupe."

INTERPRETATION, and it is the key continuity claim: "these are **not** 'modality-specific logic
leaking into the core' — they are concerns that **cease to exist** in text. **Nothing has to be
abstracted; they are simply out of scope.**"

### 11.2 The reuse question is OPEN, with a named experiment and a named falsifier

Open question 9 of convergence §7, unanswered: "**is the existing voice boilerplate genuinely
reusable after stripping the modality-specific machinery?**"

Named experiment: "produce a text-only cut following §4.4 — delete the voice machinery and
`planner`/`plan_step`/`enrichment`, keep the rest — then measure the resulting line count of
`nodes.py` and whether the selftest still passes."

**Falsifier, quoted:** "if what remains is still a **1000+ line monolith** with coupling that
resists the subsystem split, '**evolve rather than discard**' is **falsified and a clean
reimplementation is the cheaper path**."

### 11.3 But text-first itself is REOPENED

Critical for continuity planning: text-first "had itself been decided on **internal engineering
grounds** (reusable boilerplate, config-driven, avoid voice machinery) — the same
architecture-convenience bias already caught twice." Consequence: "**text-first vs voice was
reopened** as a DECIDED item… It was **not automatically reversed** — phone-heavy inbound volume
does not by itself make voice correct." Governing question: "**for the specific problem
eventually chosen, where does the valuable interaction actually happen?**" *Inbound vs outbound
remained decided throughout (inbound).*

Market pressure on the same point: "inbound to these businesses is still **phone-led**, which is
why **every funded competitor is voice-first** with text as the second channel."

### 11.4 Continuity of the engine's good parts

- `execution_validator` is **PROMOTED** to "the contract assertion point" — the existing engine
  already has the node the new architecture needs.
- `agentic_retrieval` is **RELOCATED** — survives as a subsystem outside the agent flow.
- `tool_exec` survives **strengthened** (idempotency, transactional semantics).
- `failure` survives because the failure boundary is a declared axis.
- `hitl_gate` survives **in kind**, relocated into the tool contract.
- The **builder** survives and is central (R14), reduced to: "business conversation + source
  material → draft specification → validate/self-test → deploy, human review in the loop."
- What does **not** carry over: the build-time-only durability model (`built_agents`,
  `selftest_status`) — "the circuit is physically open" and Seam 1 must be built.

---

## 12. Open questions and explicitly deferred topics

### 12.1 The fourteen open unknowns requiring primary evidence ("No further desk research settles any of these")

| # | Unknown | What would settle it |
| --- | --- | --- |
| 1 | **The practised-vs-printed-policy gap** — "whether a business's real rules match its documents. The likeliest place all four stress-test specs are wrong" | "**2–3 conversations with real small-business operators**", comparing described rules against printed material. "Named in the brief as **the only test of the problem statement**" |
| 2 | **Whether the specification can DRIVE behaviour, not merely express it** | Build the four generalisation businesses in sequence; record three measurements: **engine leaks** ("fail if they do not fall toward zero from business 1 to 4"), **resolution-model strain** ("fail if any business needs a family the model cannot express"), **setup effort** in wall-clock and source-artifact count ("fail if it does not fall materially"). "Needs no customers — only real business material" |
| 3 | **Whether operators can name an observable failure** | Ask "*how would you know the agent did a bad job?*" and record "**verbatim, without prompting**". If not, "the evidence→evaluation→promotion loop has no customer-side signal and must be rebuilt around our own assertions only" |
| 4 | **Whether variation is configuration or a DSL in disguise** | Attempt each operator-described rule in the draft schema; "**count rules needing a new schema concept vs a new leaf**. More than ~1 new schema concept per customer means the config surface is growing into the forbidden DSL" |
| 5 | **Whether `intent_detect` earns its LLM call** | Measure on real episodes "how often its classification **changes the route** versus what job structure alone would have chosen. **The one explicitly blocked deletion**" |
| 6 | **Whether external I/O or LLM calls dominate the reply path** | Instrument per-turn end-to-end latency split into LLM time per call site (6 in `nodes.py` + 2 in `rag_subgraph.py`), external tool I/O per call, retrieval time, framework overhead — "emitted as **structured episode telemetry, not logs**. If external I/O dominates, **cutting `intent_detect` or `enrichment` buys nothing** and the work belongs at the data/caching layer" |
| 7 | **Whether side-effect-gating reads really happen once per episode** | Tag every external read with its consequence class; measure count and position in the episode. "If they occur per turn, the latency budget is not honest and the freshness model needs rework" |
| 8 | **Whether tier-1 evidence needs a judge** | Define the **5 interaction-quality assertions** (required info collected; correct tool use; correct retrieval/evidence; correct escalation; policy compliance) and assert them over "**~20 scripted episodes at the `execution_validator` contract point**. If fewer than 4 of 5 can be asserted deterministically from the episode alone, the 'no judge needed' interpretation is wrong and **evaluation gets much more expensive**" |
| 9 | **Whether a joined episode is cheap** | One happy path end-to-end against one real external system: "conversation → structured action proposal → deterministic execution → confirmation → an episode record carrying an **episode ID and the external join key**. If that cannot be produced cheaply, **Seam 1 is harder than assumed and must be scheduled, not assumed free**" |
| 10 | **Whether the existing boilerplate is reusable after the voice strip** | The text-only cut: `nodes.py` line count + selftest pass (§11.2) |
| 11 | **Whether the target buyer requires runtime ownership** | Ask directly: "*would you accept a hosted runtime holding your conversation data?* A clear yes keeps the C2 contradiction dormant and **settles the generated-code fork for V1 in favour of a shared runtime**. A refusal **for reasons spec-level ownership does not satisfy**, observed in a real procurement conversation, reopens it" |
| 12 | **Cost to serve per episode** | "Count per episode: turns, LLM calls, tool calls, tokens, cost; store on the episode record. **First real unit-economics number, replacing a guess**" |
| 13 | **Residual market unknowns** | NexHealth Partner Program commercial terms ("the single most load-bearing one on the dental path"), whether TrueLark's SMS/web-chat booking survived the Weave integration, Jane/Boulevard/Zenoti/vet-PMS API terms — "all require **a partner-program application or a vendor conversation**, not more searching" |
| 14 | **Operator-voice failure data** | "**Reddit was blocked to the researcher and no primary operator corpus was obtainable**; the public record is actively contaminated by fabricated abandonment statistics. Only **direct operator conversation** produces this, and **nothing in the public record may be substituted for it**" |

### 12.2 Explicitly deferred / not decided

- **Knowledge authority** — not decided (embedded snapshot / versioned internal store / external
  SoT / external + bounded cache).
- **Retrieval mechanism** — not decided (deterministic lookup / lexical / dense / hybrid /
  external knowledge API).
- **LLM / model strategy** — not decided; "Principle 1 fixes the *posture*, not the call-site
  topology, which is **blocked on measurement**."
- **The generated-code fork** — "the fork itself **not** finally decided"; keep/replace
  evidence conditions recorded (§2.4).
- **Deployment ownership** — "**conditional ownership by customer segment** is the most
  commercially plausible and is **unvalidated**."
- **Multi-tenancy** — "**Nothing in the session proved multi-tenancy**", and execution model
  must stay orthogonal to deployment topology.
- **Text-first vs voice** — reopened (§11.3).
- **The chosen use case** — all three researched candidates closed; **internal operations is
  unexamined, not rejected**.
- **Domain guardrail packs** — extension points, "**no packs in V1**."
- **`intent_detect` deletion** — "blocked, not empty"; gated on measurement.
- **The commercial ownership contradiction** — "the architectural contradiction dissolved, the
  **commercial** one (ownership) did not."
- **Residual UNVERIFIED market items** (§4.2, §12.1 row 13), and the bar opinions read only via
  secondary summaries.

---

## Gaps in the addendum relative to the PRD's needs

Stated plainly so the PRD author does not go looking:

1. **No personas.** No names, no JTBD, no fears. Blocked on open unknown 1.
2. **No business model or pricing for the new product line.** Only competitor pricing, plus the
   finding that outcome pricing is structurally unavailable to a non-SoR owner.
3. **No capability catalog.** Only the bounding rules (configuration → extension point → custom
   leaf; contract-asserted; no agentic tool selection) and incidental tool names.
4. **Onboarding is one sentence plus four friction points.** The journey design is unbuilt.
5. **The 13 spec fields are referenced, not enumerated** — canonical list lives in
  `brief-AgentStudio-2026-10-07/spec-stress-test.md`.
6. **Tone/voice/character content is essentially absent** — §10 is everything there is.
