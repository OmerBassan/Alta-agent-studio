# PRD extraction for UX specification — Agent Studio V1

Sources read in full:
- `_bmad-output/planning-artifacts/prds/prd-AgentStudio-2026-10-08/prd.md` (692 lines, status: final, 2026-10-08)
- `_bmad-output/planning-artifacts/prds/prd-AgentStudio-2026-10-08/addendum.md` (103 lines, status: final, 2026-10-08)

Conventions in this file: `>` blocks and quoted strings are VERBATIM from the source. `[INFERRED]` marks my reasoning. `PRD SILENT` marks a genuine absence. Section refs are the PRD's own (`§8.9`, `FR79`, `EX10`, `O11`, `AD2`…).

---

## 0. Frame the UX must sit inside (read this first)

Product thesis, PRD §1.1, verbatim:

> **Reasoning is broad; authority is bounded.**

> The Agent may think widely about any request a person brings, including situations nobody enumerated in advance. What it may **conclude**, what it may **promise**, and what it may **do** are narrow, declared, and enforced.

> A model-in-charge Agent decides what to do next; a deterministic Core decides what the Agent is permitted to do, executes it, and records what happened.

§1.1, directly constraining the authoring surface:

> The business supplies a **Business Specification** — context, knowledge, policies, capabilities, authorities and boundaries. It does **not** supply a per-business sequence of steps. The platform has no business-level control flow to author, and the authoring surface must make sequencing unexpressible.

V1 objective, §1.2 table, verbatim:

> **V1 objective** | Prove that a short onboarding conversation can produce an Agent that genuinely behaves like a worker for *that* business. | What this PRD scopes.

North-star framing is explicitly NOT a V1 promise (§1.2): "A small business can effectively *hire* and configure an AI worker. | Direction of travel. **Not a V1 commercial promise.**"

§1.2 also binds messaging: "'General-purpose' is the correct description of the architecture and a poor message to a customer. It is **not** the customer-facing differentiator and does not appear in customer-facing positioning."

The V1 product problem, §1.4:

> **Can we make the transition from "this is my business" to "this Agent behaves like someone who works here" short, reliable, and repeatable across materially different businesses?**

Confirmation that voice is out: §7.2 Out of scope — "Voice | A separate, already-proven project. Channel is an adapter". §7.4 lists as "**Not reusable**" "Everything shaped by voice transport and telephony: the vendor adapter and control plane, dead-air filler, the pre-speech sanitizer, the twenty-word spoken-string contract, phone-sales micro-tactics, the tunnel dependency, and the phone-craft reference material".

---

## 1. THE TESTING INTERACTION FOR V1 — the headline finding

### 1.1 Verdict

**PRD SILENT — and this is a hard, deliberate-looking silence, not an oversight of wording.**

There is **no operator-facing test, try-it, preview, simulated inbox, sample-message composer, replay, side-by-side, dry-run, staging or sandbox surface anywhere in either document.** I grepped both documents for: `test-call`, `test call`, `try it`, `preview`, `dry run`, `sandbox`, `simulat*`, `replay`, `rehears*`, `fixture`, `seeded`, `before going live`, `go live`, `go-live`, `deploy`, `smoke`, `try out`, `sample message`, `side-by-side`. Every hit is accounted for below, and none of them is an operator testing interaction.

The PRD's own statement of what the operator gets is exclusive and closes the door:

§7.1 S10, verbatim:

> | S10 | **Operator surface: classified divergence list + single-episode viewer** | The improvement loop, and nothing more. See §8.9 |

§13.2 Observability, verbatim:

> The operator-visible surface in V1 is the divergence list and the episode viewer only — there is no alerting, and no metrics dashboard (§7.2).

§7.2 Out of scope, verbatim:

> | Metrics dashboard, escalation **inbox**, in-product specification **editor** | Out of the V1 operator surface by decision. Note the two narrow things that *are* in: an escalated episode is **delivered** to a declared destination (FR103), and a specification is **revised through the Builder conversation** rather than an editor (FR101). Neither is a console surface |

So the enumerated V1 operator surface is: (a) the Builder conversation, (b) the classified divergence list, (c) the single-episode viewer, (d) immediate suspension (FR110). A pre-go-live test surface is in none of them.

### 1.2 What the PRD puts in the place where a test surface would go

The PRD substitutes an **automated, platform-owned validation suite** for an operator test interaction. This is the only "does it work before it goes live" mechanism in V1.

**FR22** (verbatim):

> There is exactly **one gate**, the **validation suite**, and it stands in front of both promotion and deployment. It comprises platform-owned invariant checks, which block, and the business's own declared criteria, which warn unless the business declares them blocking. A failing validation suite cannot be promoted or deployed. This is a hard gate, not advice.

**FR25** (verbatim):

> A **passing validation suite is the unit of done for a built business** (FR22). No business is deployed without one, and the same gate governs every later promotion — there is no separate, weaker pre-deployment check.

**FR95** (verbatim):

> The validation suite is **platform-owned, domain-agnostic and derived from the specification**. It is **never authored by the Builder it gates**, and it is never stubbed to pass. Per-business authoring checks may warn; only platform-owned checks may block. Where a business lacks the shape a check assumes, the check adapts or skips rather than failing.

**FR23** (verbatim): "Validation MUST detect a capability that is granted but which policy will always deny, and block promotion. A promise made to a customer and then broken is worse than a refusal."

**FR24** (verbatim): "Validation MUST reject sequencing constructs, with a comprehensible reason." — *"with a comprehensible reason" is the PRD's only hint at validation-failure presentation.* [INFERRED] This implies a validation-result screen/state showing per-check verdicts with human-readable reasons, but the PRD never describes one.

**FR20**: "Evaluation criteria live inside the durable specification, not recreated per generation." **EX16**: "Evaluation criteria — what good looks like here | Lives in the durable specification per FR20."

**FR96** (verbatim) — the non-vacuity rule, a *platform engineering* obligation, not an operator one:

> Every Core safety check — guard, detector, budget, validator — is positioned before anything that mutates what it measures, and is proven non-vacuous by demonstrating that it fires when the condition it guards is reintroduced. A check that cannot be shown to fail is not evidence of anything.

**FR11** — the only *human* act in front of go-live (verbatim):

> Human review is a **blocking precondition of promotion**, alongside the validation suite: a specification cannot be promoted without a recorded approval, attributable to a named approver, retained as evidence under FR28. Who may approve, and what competence that requires, is deferred (O1) — but *whether* approval is enforced and recorded is a product decision, and it is yes.

So the V1 pre-go-live sequence the PRD actually commits to is: **validation suite passes (FR22/FR25) + a recorded, attributable human approval of the specification (FR11) → promotion → deployment.** The human act is *reading and approving a specification document*, not *testing a conversation*.

[INFERRED] The reviewable artifact is the lever the PRD leans on instead of a test run: **FR19** — "The specification is human-readable and diffable. It is **neither a generated prompt nor generated code** — otherwise diffing behaviour, asserting over behaviour, reviewing a proposed change, reverting a regression and attributing an outcome to a version are all unavailable." And §8.3's governing metaphor: "specification, evidence, evaluation and deliberate changes behave like version control, and **promotion is a pull request on behaviour**." *So the PRD's model of "testing" is code review of a spec diff, not exercising the Agent.*

### 1.3 The two test-like mechanisms that exist — and why neither is the operator's

Both are **team/validation-programme instruments**, explicitly not an operator surface.

**(a) FR100 — the seeded business fixture** (verbatim):

> Elicitation quality is tested against a **seeded business fixture**: a business whose material is supplied to the Builder with a known set of operational rules deliberately withheld from it, where those rules exist only in the operator's answers. The measure is how many of the withheld rules the Builder recovers, and how many it invents or silently defaults instead. This makes FR3, FR4, FR5 and FR7 falsifiable without requiring a numeric target to be invented, and it is the only way the Builder's hardest requirements become testable at all.

This tests **the Builder's elicitation**, not the Agent's behaviour, and the "operator" in it is a scripted stand-in. It lands in epic **E2**. Not an operator-facing UI.

**(b) FR92 — the usefulness test** (verbatim):

> The usefulness test runs against **real** inbound requests, with Agent failures reported separately from blocks caused by the business's own rules or capacity. **At least one of the four businesses must be real end to end** — a real operator, their own material, their own inbound traffic. The other three may run against authored corpora drawn from public enquiries, reviews and published FAQs, and results from those are reported as what they are. A usefulness claim tested entirely against requests the team wrote is not a usefulness claim, and §13.1 already concedes all four specifications are currently constructions.

Note the phrase **"authored corpora drawn from public enquiries, reviews and published FAQs"** — the closest thing in the PRD to a *scenario set*. But it belongs to the four-business generalisation programme (**E12**, FR88–FR94), run by the team, not by an operator in a UI. §8.11 heading: "A V1 deliverable, not a post-launch activity. V1 is not complete until these exist."

[INFERRED, flagged as the single most important UX question] FR92's corpora and FR100's fixture are *exactly* the raw material a "seeded scenario set" test surface would need, and the PRD builds both without ever giving the operator access to either. Whether the operator gets a seeded-scenario test run is an unasked question in this document.

### 1.4 The nearest adjacent thing the PRD does offer: counterfactual replay — OPEN, undecided

**O11** (verbatim, the whole row):

> | **O11** | Whether **counterfactual replay** — re-running a closed episode against a later specification version to show what would now happen differently — is a V1 feature | It is close to free given what is already required: immutable versions (FR21), version pinning (FR27), a full episode record (FR73) and an actionable divergence item (FR82). The source material flags it as the one genuinely unoccupied position in the current trust landscape, and it is the most direct answer to "will this change fix it?" Left undecided rather than silently dropped | During E10, where the cost is visible |

This is a **post-hoc** replay of a *real closed* episode against a *later* version — a "did my fix work?" surface, **not** a pre-go-live test. And it is **explicitly undecided for V1**. If the UX wants a testing interaction, O11 is the nearest sanctioned hook and it requires a decision from the user.

### 1.5 What the operator sends / gets / judges / can do with the result

| Question asked | PRD answer |
|---|---|
| What does the operator send to test? | **PRD SILENT** |
| What does the Agent return in a test? | **PRD SILENT** |
| What does the operator judge it against? | Only indirectly: EX16 / FR20 evaluation criteria "what good looks like here" live in the specification; FR22 runs them as *warn-unless-declared-blocking* checks. No judging *interaction* is described. |
| What can they do with the result? | **PRD SILENT** for a test result. For a *production* result there is a full path: divergence item (FR82) → Builder conversation revision (FR101) → same gate (FR22) → review (FR11) → promotion. |
| Simulated inbox? | **PRD SILENT.** The escalation *inbox* is explicitly out of V1 (§7.2); no other inbox-like surface is named. |
| Sample-message composer? | **PRD SILENT** |
| Replayed fixtures? | FR100 fixture exists for the Builder (team-side); episode replay is O11, undecided. |
| Side-by-side? | **PRD SILENT** as a product surface. The only side-by-side in the PRD is §7.5's proof gate: "**one realistic business interaction is implemented end to end** and compared against the existing fifteen-node system on nine axes: architectural simplicity, amount of custom code, number of model calls, latency, control and observability, failure handling, extensibility to a second business, and ease of enforcing business boundaries." That is an internal architecture decision point — "This is a decision point, not an epic." |
| Seeded scenario set? | Only FR100 (team) and FR92's authored corpora (team). Not operator-facing. |

### 1.6 Things in V1 that would *shape* any test surface the UX proposes

- **FR27**: "An episode keeps the specification version pinned at its start. Promoting a change MUST NOT alter conversations already running." [INFERRED] a test run would need its own version pinning and must not be mistakable for a real episode.
- **FR52 / FR53 / FR109**: consequence class (reversible / costs money / reaches a customer), confirmation gating, and authority establishment. [INFERRED] any test that exercises an `effect` must not actually reach a customer or spend money — the PRD gives the vocabulary (FR52) for what a test must stub, but never says a test mode exists.
- **FR110** — suspension, verbatim: "An operator can **suspend their Agent immediately**, without a promotion and without a deployment, and can suspend its ability to perform effects while leaving it able to respond. A system that sends messages to real customers and cannot be stopped in one action is not operable, whatever its specification says. Suspension is recorded, and episodes in flight when it happens end in a recorded outcome rather than silently." — *This is the PRD's only "responds but cannot act" mode, and it is a kill switch, not a test mode.* [INFERRED] it is the closest existing mechanism to a "safe to try" state.
- **FR61** — "An episode is initiated or resumed **only** by an inbound interaction or an external system event." [INFERRED] a test harness that injects a message is formally an inbound interaction; the PRD does not say whether a test injection is permitted or how it is distinguished.
- **FR112** — automated-agent disclosure in the first message of an episode. [INFERRED] would appear in any rendered test reply.

---

## 2. THE BUSINESS SPECIFICATION — real shape and vocabulary

### 2.1 Definition of record

§6 Vocabulary, verbatim:

> | **Business Specification** | The business's declared context, policies, authorities, capability grants and outcome expectations. One artifact |

### 2.2 Structural requirements (§8.2)

Section preamble, verbatim:

> Stated as expressive capability, not as a field schema: the concrete schema is deferred to the Specification and Builder implementation. The specification is **one artifact**, from which the Core compiles everything the runtime uses.

- **FR13**: "The Business Specification is a single artifact. The Agent's context, the capability surface offered to the model, and the policy the Core enforces are all compiled from it. There is no separate prompt, tool list or policy file as an independently authored product object."
- **FR14**: "A business MUST be able to express every area in the **expression surface** below. Each area is separately addressable, separately reviewable, and separately checkable by the validation suite. An area a business leaves empty is a recorded absence, never an implied default." ← *load-bearing for UX: per-area addressability + review + an explicit "recorded absence" state.*
- **FR15**: "The specification MUST distinguish **obligations** — what must be true before an action — from **diagnostic inputs**, which are gathered to support a judgement and have no fixed sufficient set. The term *evidence* is reserved throughout this document for Core-authored records (FR70) and is never used for material the Agent gathers."
- **FR16**: "The specification MUST support **decision authority classes** — at minimum informational, liability-bearing and state-changing — gated separately from one another."
- **FR17**: "The specification MUST be able to permit inferring a **cause** while forbidding determining **fault**. These are different acts with different consequences: an Agent may be authorized to say that overwatering is almost certainly the problem, and simultaneously forbidden from concluding that this constitutes neglect and the claim is therefore denied."
- **FR18**: "The specification MUST NOT be able to express ordering or sequencing. The authoring surface makes sequencing unexpressible; validation is the backstop, not the mechanism (FR24)."
- **FR19**: "The specification is human-readable and diffable. It is **neither a generated prompt nor generated code** — otherwise diffing behaviour, asserting over behaviour, reviewing a proposed change, reverting a regression and attributing an outcome to a version are all unavailable."
- **FR20**: "Evaluation criteria live inside the durable specification, not recreated per generation."
- **FR21**: "The specification is versioned. A promoted version is immutable."
- **FR105**: "The goals in play for an episode, and the obligations outstanding for each, are **typed Core state** — readable by the Agent, asserted by the Core at resolution, and **never only prompt text**. But **holding them is not deciding with them**: the Core never selects which goal is pursued, and never decides what to do about an unmet obligation. A business declares which goals exist and what obligations attach; what to do about an outstanding one is the Agent's to reason about. No requirement in this document may be read as 'if obligation X is unmet, do Y'."
- **FR106**: "Where an obligation is **waived**, the waiver is explicit, attributable to a declared authority, and recorded. An obligation that quietly stops applying is indistinguishable from one that was never enforced."

### 2.3 THE EXPRESSION SURFACE — EX1–EX17, verbatim table (§8.2)

Caption, verbatim: "**The expression surface (FR14).** Seventeen areas, each individually addressable. These are *areas a business must be able to express*, deliberately not field names — the concrete schema belongs to E1 (see O7)."

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

**EX1 is a direct, explicit constraint on the UX work** — quoted again because it names UX: "nothing downstream (UX, a later design pass, a starting point under FR8) may invent one."

### 2.4 Field schema — explicitly NOT specified

**O7** (verbatim):

> | **O7** | The specification field schema, and the field-count discrepancy in the source material | The stress test enumerates fourteen items while asserting thirteen invariant fields, and structural change 6 then splits one of them. This PRD deliberately specifies expressive capability instead (§8.2) | When the Specification epic begins |

§7.3 lists "the concrete specification field schema" among the deferred items. §12 E1: "The concrete field schema is deferred to here | High — O7 lands here".

**So: the review-and-correct surface has seventeen named, individually addressable areas (EX1–EX17) and NO field names below them. PRD SILENT on fields, nesting, cardinality, and on the specification's rendered form (document? outline? cards?).**

### 2.5 Companion artifact: Business Knowledge

§6: "| **Business Knowledge** | Version-pinned authoritative business material, and retrieval over it |". **FR9**: "The Builder produces both the Business Specification and the Business Knowledge artifacts." Two artifacts out of the Builder, one of which (the specification) is "one artifact".

---

## 3. THE BUILDER ONBOARDING CONVERSATION (§8.1)

Section preamble, verbatim:

> The hard problem is **elicitation, not generation**. Generating configuration from a description is engineering; discovering how the business actually operates is the product risk. "Minimal Builder" means minimal burden and interface complexity *for the operator*, never minimal reasoning *by the Builder*.

Mirrored in §7.1 S3: "The Builder, with **deep elicitation** | Minimal burden and UI for the operator; *not* minimal reasoning by the Builder."

§6 vocabulary: "| **Builder** | Conversation and sources → specification and knowledge artifacts → validation → promotion |" ← *the only stated pipeline shape; there are no named phases or steps.*

### 3.1 Opening — FR1, verbatim

> The Builder opens with an open invitation — in substance, *"Tell me about your business and what you want the Agent to handle"* — and never with a form or a fixed question set.

### 3.2 Phases/steps

**PRD SILENT on named phases or steps.** This is emphatic, not accidental — FR3 forbids the fixed structure that phases would imply:

- **FR3**: "The Builder decides adaptively what needs clarification, from what the operator says and what the material contains. It MUST NOT present a fixed questionnaire, and the number of questions asked is a function of what is missing, not of a template."

[INFERRED] The only *ordering-free* progression the PRD supports is coverage over EX1–EX17 (FR14: each "separately addressable, separately reviewable"), plus the §6 Builder arrow (conversation+sources → artifacts → validation → promotion).

### 3.3 Inputs it accepts — FR2, verbatim

> The Builder accepts the business's own material in the formats the operator already has: price lists, terms, policies, care guides, fee guides, published FAQs, prior customer correspondence.

### 3.4 What it probes for — FR4, verbatim (the elicitation target list)

> The Builder MUST actively interview the operator for the safety-critical content that characteristically exists in no document: prohibitions, thresholds, exceptions, authority limits, which exceptions are routinely granted, what must always be escalated, and what must be established before a decision may be made.

**FR7**: "The Builder MUST probe explicitly for the gap between printed policy and practised policy, because that gap is the likeliest place a specification is wrong."

Why, from §3.3 "The documentation gap", verbatim:

> The least-documented content is the most safety-critical: prohibitions, guard conditions, escalation thresholds and the operational rules — billing cut-offs, lead times, which exceptions are routinely granted — frequently exist in no document at all.

> And beneath it, the gap between each business's **printed** policy and its **practised** one. A Builder that ingests documents and stops has captured the safe part and missed the dangerous part.

### 3.5 Ambiguity, contradiction and gaps — the handling rules

- **FR5**: "The Builder MUST surface contradictions — between two sources, and between a source and what the operator says — rather than silently selecting one." ← *implies a contradiction-presentation interaction. UX-bearing. The PRD does not say how it is presented or resolved.*
- **FR6**: "Where business behaviour is unknown or ambiguous and the operator cannot resolve it, the Builder MUST record a specification defect. It MUST NOT invent a default. **Never improvise a rule.**"
- **FR48** (runtime twin): "Where the business's rules are silent, the Agent escalates and the gap is recorded as a specification defect. **Never improvise a rule.**"
- **FR14**: "An area a business leaves empty is a recorded absence, never an implied default."
- **FR104** — narrated process re-derivation, verbatim:

> When an operator narrates a **process** — and they will, because that is how people describe their own work — the Builder MUST re-derive it into declared context, policy, capability, authority, goal and obligation, and **persist no ordering**. The operator may say "first we check the diary, then we take a deposit"; what is recorded is that a deposit is an obligation of a booking goal and that checking availability is a granted capability. Rejection at the validation gate (FR24) is the backstop, not the mechanism: the Builder is where a narrated process stops being a sequence.

- **FR117** — Builder failure visibility, verbatim:

> Builder-side failures are **distinguishable outcomes, never silent ones**, on the same rule as FR46: a source that cannot be read, a session abandoned part-way, and a newly supplied source that contradicts an already-promoted specification each produce a stated outcome the operator can see. A half-elicited specification is never presented as a complete one.

*FR117 names three concrete UX states: unreadable source; abandoned-part-way session; new source contradicting a promoted specification. And one prohibition: never present a half-elicited specification as complete.*

### 3.6 What it produces

**FR9**: "The Builder produces both the Business Specification and the Business Knowledge artifacts."
**FR10**: "The Builder is itself agent-driven. The platform's Agent nature is visible on the Builder side, not only at runtime."

### 3.7 Stopping condition / completeness notion

The only stated stopping condition is the gate, not a conversational judgement:

- **FR25**: "A **passing validation suite is the unit of done for a built business** (FR22)."
- **FR12**: "The Builder instruments its own burden: wall-clock time to a passing validation suite, and the number of source artifacts required. Both are recorded per business." ← *"time to a passing validation suite" is the de facto completion metric.*
- **FR11**: recorded, attributable human approval is a blocking precondition of promotion.
- **FR117**: "A half-elicited specification is never presented as a complete one." ← *implies a completeness indicator exists; its form is* **PRD SILENT**.

No turn count, no question budget, no "coverage %" is named. **PRD SILENT on how the operator or the Builder knows the conversation is done, other than the suite passing.**

### 3.8 Builder instrumentation the UI may need to show

- **FR12** (burden): wall-clock time to a passing validation suite; number of source artifacts required.
- **FR99** (yield), verbatim:

> The Builder instruments its own **yield**, not only its burden: how much business behaviour was recovered that the supplied material did not contain — the prohibitions, thresholds, exceptions, authority limits and always-escalate cases obtained by interview (FR4), the contradictions surfaced (FR5), and the specification defects recorded rather than guessed (FR6). **Burden and yield are reported together and neither is read alone.** Burden measured by itself rewards a Builder that asks less, which is the opposite of the product.

*"Burden and yield are reported together and neither is read alone" is a presentation constraint, though §7.2 puts any metrics dashboard out of V1. [INFERRED] these are reported in the validation programme, not necessarily to the operator — the PRD does not say who reads them.*

### 3.9 Revision through the Builder — FR101, verbatim

> An operator can **revise a promoted specification through the Builder conversation**, producing a new version that passes the same gate and is reviewed and promoted like any other. This is what closes the improvement loop: a divergence item (FR82) is actionable because the Builder is the authoring path. It is deliberately **not** an in-product specification editor — the surface is the same conversation that created the specification, which is why the editor can stay out of V1 without the loop being open-ended.

**This is the single most important UX constraint on the review-and-correct surface: there is NO editor. Correction happens in conversation.**

---

## 4. DIVERGENCE AND THE OPERATOR SURFACE (§8.9) + EPISODE

### 4.1 Episode — definition of record

§6, verbatim:

> | **Episode** | One unit of interaction. One identity, one tenant, one lifecycle, one evidence record, and one join key where it touches an external system of record |

Lifecycle, **FR60** verbatim:

> An episode's lifecycle is exactly: active; pending, awaiting a **named** external input; closed. No business sub-states may be added to it — business outcome lives in goals, obligations and the resolution, never in lifecycle. A business may declare a deadline on a named awaited input; **its expiry is an external system event**, which initiates or resumes an episode (FR61) and leaves what to do about it to the Agent. The Core never acts on an expiry, because acting on one would be selecting the Agent's next step.

Three lifecycle states only: `active`, `pending` (awaiting a *named* external input), `closed`.

- **FR61**: "An episode is initiated or resumed **only** by an inbound interaction or an external system event. Within an initiated episode the platform may reply and emit messages. The platform never independently starts an outbound conversation or episode."
- **FR62**: "An unresolved episode can be resumed later with its state, evidence, specification version and relevant context intact. A freeze awaiting a medical note, a hold approaching expiry, a claim waiting on a specialist are ordinary cases."
- **FR63**: "A result arriving after close is recorded as a **late result** and never mutates the resolution."
- **FR64**: "An in-flight episode survives a process failure. Clock, randomness, identifiers, environment and configuration are obtained through recorded means or pinned at episode start."
- **FR65**: "The Core is the sole writer of episode state; concurrent inbound messages on one episode are serialized."
- **FR66**: "There is no cross-episode memory and no cross-episode profiling. The Agent does not remember a customer between conversations."
- **FR67**: "Lifecycle says nothing about whether the business got a good outcome. `pending` is not a failure and `closed` is not a win." (echoed in §10.4 counter-metrics: "Lifecycle is never read as success")
- **FR50**: "An episode may carry several related goals and switch between them, with one goal active at a time and both parking and resumption explicit. A customer wanting advice *and* a claim is the normal case, not an edge case." (§7.1 S5: "Bounded multi-goal episodes | Explicit parking and resumption")
- **FR27**: "An episode keeps the specification version pinned at its start."
- **FR86**: "The adapter correlates inbound messages to episode identity, with an explicit join key wherever an episode touches an external system of record."
- **NFR16**: "One correlation identity per episode, present on every record of that episode's work and reportable by a person who experienced a problem."

### 4.2 What is in the episode record — FR73, verbatim (the episode viewer's data source)

> Episode evidence is durable **product data, not operational logs**: turns, retrievals, model decisions, actions, authorities exercised, obligations and waivers, guard verdicts, errors, timings, and **per-episode model calls, tool calls, token counts and cost** — under a stable episode identity. The last group is the record NFR13 and NFR14's instrumentation reads from.

Enumerated record contents: **turns · retrievals · model decisions · actions · authorities exercised · obligations and waivers · guard verdicts · errors · timings · model calls · tool calls · token counts · cost**.

Evidence rules: **FR70** "Only the Core's execution record may attest that an effect occurred. **The Agent cannot author evidence.** Evidence entries are typed records against a platform-owned schema, never opaque blobs." · **FR72** "An action record is evidence that something happened, **not** a resolution. The two must never be conflated, and a single episode routinely produces both." · **FR75** "Evidence is addressable and removable by tenant, by episode and by age."

Resolution envelope, **FR68** verbatim:

> Every resolution carries: which declared goal it concerns; whether that goal was served; under which authority; the evidence supporting it; and a business-defined payload. This envelope is fixed; the enumeration of resolution kinds is deferred and emerges from running real episodes.

Resolution kinds enumeration: **deferred** (O4 — "During the four-business run"). **FR71**: "A resolution asserting an effect without a corresponding Core execution record is invalid." **FR69**: "Escalation MAY be a declared success rather than a failure where the business says so — an episode escalated on an urgency trigger is a correct outcome."

### 4.3 Divergence — definition, detection, classification

The PRD never gives "divergence" its own §6 vocabulary row. It is defined operationally by FR77/FR78 and extended by FR108/FR115.

**FR77 — the classification (verbatim):**

> Every denial is recorded as exactly one of: a specification defect, where the compiled projections led the Agent to believe it was permitted; a business refusal, where policy correctly denied; or a platform error.

**Three classes: `specification defect` · `business refusal` · `platform error`.**

**FR78** (verbatim): "Only specification defects enter the specification backlog. The divergence log is the specification's error signal, and it **needs no human transcript review**."

**FR108 — the second source (verbatim):**

> A recorded human correction (FR102) is a **first-class divergence source alongside denials**, classified under FR77 and entering the same backlog. Denial classification covers only outcomes the Core **refused**, and the dominant failure mode is the opposite one — an answer that was permitted, confident and **wrong**, which produces no denial and therefore no divergence record. Without corrections as a source, the operator's primary surface is structurally blind to the failure class that matters most.

**FR102** (verbatim): "Human corrections are captured as first-class records against the episode and the specification version in force, so that corrections per hundred episodes and their **trend** (§10.2) have a source rather than being reconstructed later."

**FR115 — sampled adjudication (verbatim):**

> The product MUST sample business refusals for human adjudication, at a rate the business sets, and a refusal found wrong on adjudication enters the backlog as a specification defect. Without this a **wrong refusal is invisible by construction**: a correct denial and an over-strict one are both recorded as a business refusal, only specification defects reach the backlog (FR78), and the person who was wrongly refused does not come back to complain. Left alone that is selection bias with a feedback loop attached — the specification drifts toward strictness and the metrics improve while it happens.

*FR115 is UX-bearing and under-described: it implies (a) an operator-settable sampling rate control, and (b) an adjudication interaction where a human judges a sampled refusal right or wrong. Neither is described.* **PRD SILENT on the adjudication UI and on where the sampling rate is set.**

**So there are THREE divergence sources:** denials classified under FR77; recorded human corrections (FR102/FR108); adjudicated-wrong business refusals (FR115). All funnel into one **specification backlog**.

### 4.4 Divergence record fields

**PRD SILENT on an explicit field list for a divergence record.** What is derivable:

| Field | Source | Status |
|---|---|---|
| Class — one of `specification defect` / `business refusal` / `platform error` | FR77 | VERBATIM |
| Source — denial / human correction / adjudicated refusal | FR77, FR108, FR115 | VERBATIM (as sources, not as a named field) |
| Episode reference | FR102 ("against the episode"), FR80 | VERBATIM |
| Specification version in force | FR102 ("and the specification version in force") | VERBATIM |
| Backlog membership | FR78 (only specification defects) | VERBATIM |
| Actionability toward a specification change | FR82 | VERBATIM |
| Reason/status drawn from a closed vocabulary | FR81 | VERBATIM |
| Escalation reason class (for escalations) | FR74 "Every escalation records its reason class." | VERBATIM |
| Correlation identity | NFR16 | VERBATIM |
| [INFERRED] timestamp, tenant | NFR3 (tenant identity on every record), NFR18 (UTC throughout) | INFERRED as applying |
| Title/summary/severity/assignee/state (open→fixed) | — | **PRD SILENT** |

### 4.5 What the operator sees and does — the four FRs that define the surface

- **FR79** (verbatim): "The operator's primary surface is the classified divergence list — in substance, *'here is what your specification got wrong.'*"
- **FR80** (verbatim): "An operator can open a single episode and see what happened within it."
- **FR81** (verbatim): "Every failure, refusal or status an operator sees comes from a closed, enumerable vocabulary."
- **FR82** (verbatim): "A divergence item is actionable toward a specification change, closing the loop from observed behaviour back to reviewed promotion."
- **FR110** (verbatim, quoted in full in §1.6 above): immediate suspension, plus effects-only suspension.

The loop, assembled: **divergence list (FR79) → open episode (FR80) → act on item (FR82) → Builder conversation revision (FR101) → validation suite (FR22) → human approval (FR11) → promotion (FR28) → new version (FR21), with rollback by version selection (FR26).**

§7.1 S10 bounds it: "The improvement loop, and nothing more."

**PRD SILENT on:** list filtering/sorting/grouping, item detail view, how an item is marked resolved, whether the list shows counts or trends (metrics dashboard is out, §7.2), notification of a new divergence item, and the episode viewer's layout.

---

## 5. AUTHORITY / BOUNDARIES / ESCALATION / CONFIRMATION

### 5.1 The closed request-kind set — §6, verbatim

> | **Request kind** | One of the closed set the Agent may emit: `retrieve`, `read`, `effect`, `clarify`, `respond`, `escalate`, `suspend`. Every kind is authorized and journaled, reads included. The set carries no precedence and no order, and no business may add to it (FR40) |

**Seven kinds: `retrieve` · `read` · `effect` · `clarify` · `respond` · `escalate` · `suspend`.**

**FR40** (verbatim): "The Agent emits one of a **closed** set of request kinds, and **every kind is authorized and journaled, reads included**. Closure runs in both directions: a business's capability model is a *grant over the existing kinds*, and nothing a business declares can add one. Widening the Agent's repertoire is a platform release, never onboarding (FR58). The set carries **no precedence and no ordering** among its members."

### 5.2 Decision authority classes — named tiers

**FR16**: "**decision authority classes** — at minimum informational, liability-bearing and state-changing — gated separately from one another."

**Three named classes: `informational` · `liability-bearing` · `state-changing`.** ("at minimum" — the set is open upward.) Carried in the specification by **EX7** ("What the Agent may conclude, and on whose authority").

### 5.3 Consequence class — the operator's real dial

**FR52** (verbatim):

> Every capability declares its **consequence class** — whether it is reversible, whether it costs money, and whether it reaches a customer. This is what an operator is actually bounding when they say they do not want an Agent contacting the wrong person, and it is visible, not internal.

**Three consequence axes: reversible? · costs money? · reaches a customer?** — and the PRD says **"it is visible, not internal"**, which is an explicit visibility requirement on the UI.

### 5.4 Capability contract — FR51, verbatim

> Every capability is verb-first and declares a contract: input schema, effects, authority required, confirmation requirement, success evidence, and idempotency scope. A capability with no success-evidence definition is not shippable.

Six contract elements: **input schema · effects · authority required · confirmation requirement · success evidence · idempotency scope**. (§6: "| **Capability** | A verb-first declared action with a contract: input schema, effects, authority required, confirmation requirement, success evidence, idempotency scope |")

### 5.5 Confirmation gates

- **FR53**: "An effect whose contract requires confirmation is not authorized until that confirmation is recorded."
- **FR109** (verbatim): "Where a capability is state-changing, costs money or reaches a customer (FR52), the **authority under which it is executed must be established, not assumed from the channel**. A sender address is not an identity: an account cannot be mutated on the strength of a message header alone. What constitutes sufficient establishment is declared per business (EX7, EX12) and identity verification is an extension point, not Core semantics — but a capability of this class with no declared basis for authority does not pass the validation suite."
- **FR54**: "Whether a capability is eligible for automatic retry is a visible attribute. An action whose contract cannot define an idempotency key is not eligible." ← *"visible attribute" — another explicit visibility requirement.*
- **FR55**: at-least-once with a Core-issued idempotency key; "Retries do not double-book or double-charge, and a genuine effect is never silently suppressed as a duplicate."
- §7.4 lists "the human-authorization interrupt" as reusable largely as-is from the voice system. [INFERRED] this is the mechanism behind FR53's confirmation.

*Note: FR53's "confirmation" is a contract-level requirement; the PRD never says WHO confirms (the requester? the operator?) or through what surface.* **PRD SILENT on the confirmation actor and surface.** [INFERRED] Given FR110's effects-only suspension and FR103's escalation delivery, a confirmation could plausibly be an operator act — but the PRD does not say so, and §7.2 puts an escalation inbox out of V1.

### 5.6 Escalation

- §6: "| **Escalation** | The Agent's decision to hand off, under conditions the business declares. One of the request kinds |"
- **FR47** (verbatim): "Escalation has exactly one owner: **the Agent escalates**. Where required authority or evidence is unavailable, the platform returns a typed refusal stating so; it never escalates on the Agent's behalf. A business declares escalation *conditions*, never escalation execution."
- **FR48**: "Where the business's rules are silent, the Agent escalates and the gap is recorded as a specification defect. **Never improvise a rule.**"
- **FR69**: escalation may be a declared success.
- **FR74**: "Every escalation records its reason class."
- **FR103** (verbatim) — the delivery surface: "An escalated episode is **delivered to a destination the business declares**, over the V1 channel, carrying the escalation reason class and a link to the episode. Without this, escalation is specified on the Agent's side and arrives nowhere, and no business could be run on V1. The destination is per-business configuration; routing rules, rotas, acknowledgement and response expectations are **not** in V1 (O2)."
- **EX10**: "Escalation conditions — **what this business will not let an Agent decide** | The operator's authority dial, in the operator's own words" ← *EX10's note is the best single sentence for an authority-setting UI.*
- §2 role: "| **Escalation recipient** | Where a handed-off episode lands. Destination, notification and response expectation are an open item (§11). |"
- **O2** (verbatim): "Escalation **routing** — rotas, multiple recipients, acknowledgement, and any response expectation | Delivery to a single business-declared destination is now specified (FR103), which is enough for V1 to be operable. Everything about *who* beyond one address, and what happens if nobody answers, is not | When a business needs more than one recipient"

**So in V1 escalation leaves the product as an email to one declared address carrying a reason class and an episode link. There is no in-product escalation inbox (§7.2).**

### 5.7 Guard conditions — deterministic binding, two outcomes

§6, verbatim:

> | **Guard condition** | A declared condition evaluated before the Agent's turn, whose verdict binds deterministically with exactly two outcomes: a typed constraint returned to the Agent, or a declared safety halt. A guard never composes a reply and never chooses the Agent's next step (FR44) |

**FR44** (verbatim): "Guard conditions are evaluated **before goal recognition**, not after it — they are the reason an urgent or unsafe message never has to be understood as a request first. A guard may be evaluated by a model; the verdict binds deterministically with exactly two outcomes: a typed constraint returned to the Agent, or a declared safety halt that **aborts the episode outright**, in which case the ordinary path is abandoned rather than continued. A guard **never composes a reply and never chooses the Agent's next step**. A business configures which guard conditions apply, not what the Agent says when one fires."

### 5.8 Safety halt and the terminal notice

§6: "| **Safety halt** | One of the Core's exactly two exits: the episode terminates with a recorded outcome, rather than control returning to the Agent (FR45) |"

**FR45**: "The Core has exactly two exits: every outcome returns control to the Agent as a typed result, or a declared safety halt terminates the episode with a recorded outcome. There is no third path and no silent degradation."

**FR111** (verbatim) — a business-declared, UX-relevant string:

> A safety halt MUST NOT leave the requester in silence. The business declares a **terminal notice** for halted episodes, emitted by the Core through the egress port as the episode closes. This is a property of the halt, not of any guard: no guard composes it, it is not selected per guard condition, and it does not vary with what triggered the halt (FR44). A person who was mid-conversation is told it has ended; they are not abandoned.

*One terminal notice per business, invariant across halt causes. [INFERRED] this is a single authored string in the specification — a concrete authoring field the UX can rely on, and one of very few.*

### 5.9 The five zero-config guardrails — FR42, verbatim

> Five generic guardrails apply to every Agent with zero configuration: do not invent business facts; do not act outside declared authority; do not perform undeclared actions; do not claim success without evidence; escalate when required authority or evidence is unavailable.

### 5.10 Enforcement, not prompting — FR43, FR39, FR41, FR107

- **FR43**: "Any constraint that must hold is enforced by the Core. The specification may also describe it to the Agent, but **no enforcement path may rely on the model respecting what it was told**, and no guarantee in this document rests on prompt text."
- §7.4 caution on FR43: "**a stronger model increases fidelity to what the prompts say, never to what is true.**"
- **FR39**: "The Core never selects the Agent's next step."
- **FR41**: "The Agent never contacts anything outside the Core."
- **FR107**: "The Agent's loop has an **explicit termination bound** — a budget on work within a turn, enforced by the Core — together with a detector for repetition or stalling whose outcome is a wired handoff rather than a log line."
- **FR46**: "Errors cross boundaries as typed results, never as defaults. A degraded or fallback outcome is always distinguishable from a healthy one **by the caller**, not only in a log line."

### 5.11 Refusal and prohibition surfaces in the specification

**EX3** what may never become a goal · **EX11** refusal conditions · **EX12** what may be asked / must never be asked · **EX13** what the Agent must not infer or do · **EX1** what it will not say · **FR17** cause-not-fault. Note the PRD's own emphasis: EX12 and EX13 are each "Load-bearing in every exemplar business."

### 5.12 Three levels of variation — FR116, verbatim

> Variation between businesses resolves at exactly **three levels**, and which level a need lands at is a recorded judgement. **Configuration** is the expected path and covers the great majority of cases. A **supported extension point** takes capability that recurs across businesses but is structurally unlike configuration — a leaf behind a declared contract, such as identity verification, document intake, a derived figure, a validator or a scorer. **Custom implementation** is the exception and never the path. This is the taxonomy FR89 classifies engine leaks against, so it is defined here rather than assumed.

**FR58**: "Business configuration never changes Core semantics. A genuinely new semantic capability is a platform release, and the product MUST distinguish *configuring* a capability from *requesting* one." ← [INFERRED] implies a "request a capability" affordance distinct from configuring one; **PRD SILENT on its form.**

**FR59**: "Custom code may be a leaf behind a declared contract. It may **never** be control flow."

---

## 6. TEMPLATES / STARTING POINTS

**FR8** (verbatim, the whole requirement):

> The Builder MAY offer optional pre-filled Business Specification starting points (for example "dental practice", "gym") that seed terminology, candidate requests, questions worth asking and policies worth considering. Such a starting point: MUST be optional; MUST be fully editable; MUST contain no behavioural sequence of any kind; and MUST NOT be the source of agent behaviour. It is a specification starting point, never a behaviour template.

Four seeded contents: **terminology · candidate requests · questions worth asking · policies worth considering.**
Four constraints: **optional · fully editable · no behavioural sequence · not the source of agent behaviour.**

Note `MAY`, not `MUST` — FR8 is the only MAY-level requirement in §8.1.

Rationale, §8.1 closing note (verbatim):

> **Why starting points are seeded rather than authored (FR8).** A per-vertical library was rejected on economics, not architecture: its cost scales with the number of verticals, and a starting point reintroduces that axis if it is allowed to become the thing being maintained. Starting points are therefore seeded *from specifications businesses already wrote*, and a starting point is never a prerequisite for a business type nobody has built yet.

§4.4, verbatim: "| **A template library of behaviour** | Pre-filled Business Specifications are in scope as onboarding accelerators (FR8). Template-*defined behaviour* is not |"

EX1 again, naming the constraint on starting points: "nothing downstream (UX, a later design pass, a starting point under FR8) may invent one [a platform voice/persona]."

**PRD SILENT on:** how a starting point is chosen (a picker? offered by the Builder in conversation?), how many exist at launch, whether the operator sees that a starting point was used, and how "fully editable" is achieved given FR101's no-editor rule. *That last tension is a real conflict the UX must resolve: FR8 says "MUST be fully editable" while FR101 says there is deliberately no in-product specification editor.* [INFERRED] editing must happen through the Builder conversation.

---

## 7. PERSONAS AND NAMED PROTAGONISTS

### 7.1 There are NO named personas. This is explicit and deliberate.

§2, verbatim:

> **Primary Builder user: the Business Operator.** A role archetype, deliberately not a named persona — no primary operator evidence has been obtained yet, and inventing a persona would manufacture confidence the research does not support.

> The Business Operator is the owner-operator, or the person responsible for customer-facing operations. The defining characteristic is **not** company size, headcount or revenue:

> They possess the business's actual operational knowledge, including the rules that exist in no document.

**[ASSUMPTION A4]**, verbatim: "Such a person exists, is reachable, and can articulate those rules when interviewed. The entire Builder thesis rests on it, and FR94 exists to test it."

**[ASSUMPTION A3]**, verbatim: "That person is frequently also the buyer. ... The product may assume this commercially; it must **not** encode `buyer = builder` as an architectural requirement, and nothing in the authoring model may depend on it."

*A downstream UX journey MUST use the role name "**Business Operator**" and MUST NOT invent a personal name — inventing one directly contradicts §2's stated reasoning.*

### 7.2 The four named roles (§2, verbatim)

| Role | Relationship to the product |
|---|---|
| **Business Operator** (primary Builder user) | Owner-operator, or the person responsible for customer-facing operations. Possesses the business's actual operational knowledge, including the rules that exist in no document. Frequently also the buyer (A3). |
| **Requester** | "The person who brings an inbound request to the Agent. Known only by role; the platform never initiates contact with them." (also §6) |
| **Specification reviewer** | "Whoever reads and approves a specification before promotion. Human review stays in the loop; the competence required is an open item (§11)." (O1) |
| **Escalation recipient** | "Where a handed-off episode lands. Destination, notification and response expectation are an open item (§11)." (O2) |

Plus, implied but not drawn as a role: the **adjudicator** of sampled business refusals (FR115), and the **named approver** of FR11. [INFERRED] the approver is the Specification reviewer; the PRD does not explicitly equate them. **PRD SILENT on whether the Business Operator, the Specification reviewer and the FR115 adjudicator are the same person in V1.**

**O1** (verbatim): "Who performs specification review, and with what competence | The specification must be human-readable and reviewable, but no reviewer role or review verdict is defined anywhere in the sources | Before the first business is promoted" ← *"no review verdict is defined" — the approve/reject interaction is undesigned.*

### 7.3 The four exemplar businesses — named protagonists of the generalisation test

§2, verbatim, including the quoted aside:

> **The four exemplar businesses.** They carry the generalisation test, chosen for deliberate anti-vertical diversity — *"These are not one workflow with four skins."*

| Business | The real request | What it stresses |
|---|---|---|
| Brewery | "I want to host a 40-person event next month." | Negotiated multi-constraint planning; no slots, no practitioners |
| Gym | "I want to freeze my membership for two months." | Account state mutation under policy; recurring commitments |
| Garden centre | "This plant I bought is dying. What should I do?" | Diagnostic advice; ambiguous goal; a liability boundary |
| Dental practice | "I was told I need a root canal. What happens?" | High-stakes grounding; mandatory override; explanation, not transaction |

§2 caveat, verbatim: "These four demonstrate that the specification can **express** materially different businesses. They are **not** evidence that it can **drive behaviour**. That distinction is load-bearing throughout this document. **[ASSUMPTION A2]** These specifications are constructions, not any real business's rules (§13.1)."

**These four verbatim request strings are the best available scenario material for UX journeys and for any mock content.** Related: FR8's two named starting-point examples are "dental practice" and "gym"; §11 O9 notes "The dental exemplar carries a mandatory override and the garden centre a liability boundary."

FR17's worked example is garden-centre: "an Agent may be authorized to say that overwatering is almost certainly the problem, and simultaneously forbidden from concluding that this constitutes neglect and the claim is therefore denied." FR62's examples: "A freeze awaiting a medical note, a hold approaching expiry, a claim waiting on a specialist are ordinary cases." FR104's example: "first we check the diary, then we take a deposit."

---

## 8. NAMED USER FLOWS / JOURNEYS / USE CASES

**The PRD names no user flows or journeys as such, and has no user-story or use-case section.** §8 preamble, verbatim: "Requirement IDs are globally numbered and stable. Each describes an outcome or a constraint. **None describes a sequence** — the standing self-check from §5 applies to every one of them."

§12, verbatim: "Ordering below is dependency, **not** a behavioural sequence."

This is the forbidden-vocabulary rule biting (§6): "**Forbidden vocabulary**, because each one smuggles the rejected model back in: *workflow, state machine, business transition graph, workflow language, execution graph, stage, node*." ← *The UX must be careful: a *user* journey is not a *business* control flow, but the PRD's language discipline is aggressive and downstream docs should say so explicitly.*

The two *product-pipeline* progressions the PRD does state, both verbatim and both safe to build journeys from:

1. §6 Builder: "Conversation and sources → specification and knowledge artifacts → validation → promotion"
2. §6 Extension/FR56: "Core contract → adapter → extension"

[INFERRED] journeys the requirements imply, each assembled from cited FRs (none is a PRD-named flow):

| [INFERRED] journey | Assembled from |
|---|---|
| **Build a business** — open invitation → supply material → adaptive interview → contradictions surfaced → defects recorded → specification + knowledge produced → validation suite → human approval → promotion → deployment | FR1, FR2, FR3, FR4, FR5, FR6, FR7, FR9, FR104, FR117, FR22, FR25, FR11, FR28 |
| **Improve a business** — divergence list → open episode → act on item → revise via Builder conversation → same gate → review → promote (or roll back) | FR79, FR80, FR82, FR101, FR22, FR11, FR28, FR26 |
| **Stop the Agent** — immediate suspension, or effects-only suspension | FR110 |
| **Receive an escalation** — delivered to a declared destination with reason class + episode link | FR103, FR74 |
| **Adjudicate a sampled refusal** — sample at a business-set rate → judge → wrong ones become specification defects | FR115 |
| **Connect a starting point** — optionally seed a specification | FR8 |

---

## 9. FUNCTIONAL REQUIREMENTS THAT IMPLY A SCREEN, STATE OR INTERACTION

Grouped by the surface they land on. Quotes above; this is the index.

### 9.1 Builder conversation surface
| FR | What it implies |
|---|---|
| **FR1** | An open-invitation entry state; explicitly *not* a form or fixed question set |
| **FR2** | Source upload/attach accepting the operator's existing formats (price lists, terms, policies, care guides, fee guides, published FAQs, prior correspondence) |
| **FR3** | Adaptive questioning; no questionnaire UI; variable question count |
| **FR4** | Interview prompts for undocumented safety-critical content |
| **FR5** | A contradiction-surfacing interaction (source vs source; source vs operator) |
| **FR6** | A "specification defect recorded" state instead of a default |
| **FR7** | Printed-vs-practised probing |
| **FR8** | Optional starting-point selection/seeding; must be fully editable |
| **FR9** | Two produced artifacts visible |
| **FR10** | The Builder is visibly agent-driven |
| **FR101** | Revision of a promoted specification *in conversation*; no editor |
| **FR104** | Narrated-process re-derivation, visible to the operator [INFERRED: the operator should see their sequence become declared areas, or FR104 is invisible] |
| **FR117** | Three named failure states: unreadable source; abandoned-part-way session; new source contradicting a promoted specification. Plus: never show a half-elicited specification as complete |
| **FR12 / FR99** | Burden and yield instrumentation, "reported together and neither is read alone" |
| **FR100** | Seeded-fixture evaluation harness (team-side) |

### 9.2 Specification review / promotion surface
| FR | What it implies |
|---|---|
| **FR13** | One artifact view |
| **FR14** | Seventeen separately addressable, separately reviewable areas; an explicit "recorded absence" state per area |
| **FR15 / FR105 / FR106** | Obligations vs diagnostic inputs shown distinctly; goals+obligations as typed state; explicit, attributable, recorded waivers |
| **FR16 / EX7** | Authority classes gated separately — informational, liability-bearing, state-changing |
| **FR17 / EX13** | Cause-permitted / fault-forbidden expressible |
| **FR18 / FR24** | Sequencing unexpressible in the authoring surface; validation rejects it "with a comprehensible reason" |
| **FR19** | Human-readable, diffable rendering; a diff view |
| **FR21 / FR26 / FR27 / FR28** | Version list, immutability, rollback by selecting an earlier promoted version, attribution |
| **FR22 / FR23 / FR25 / FR95** | A validation-suite result state: blocking platform checks vs warning business criteria; granted-but-always-denied detection |
| **FR11** | A recorded, attributable approval act by a named approver — blocking |
| **FR29** | "Behaviour never mutates silently" — no silent-change surface |
| **FR30 / FR31 / EX14** | Knowledge sources pinned to versions; declared precedence between conflicting sources |
| **FR34** | General domain knowledge enabled/disabled per business as a declared risk — a per-business toggle |
| **FR35** | Freshness declared per read and per capability contract, never globally |
| **FR51 / FR52 / FR54 / FR109** | Capability contract authoring; consequence class "visible, not internal"; retry eligibility a "visible attribute"; a declared basis for authority or the suite fails |
| **FR58** | Distinguish *configuring* a capability from *requesting* one |
| **FR103** | Per-business escalation destination configuration |
| **FR111** | The business-declared terminal notice (one authored string) |
| **FR112** | Per-business disclosure wording |
| **FR114** | Per-business attachment policy (accepted as knowledge or refused) [INFERRED from "accepted as knowledge or refused, never silently ignored"] |
| **FR115** | A business-set refusal sampling rate |
| **EX17 / NFR10** | Data-lifecycle requirements captured |

### 9.3 Operator run surface
| FR | What it implies |
|---|---|
| **FR79** | The classified divergence list — primary surface |
| **FR80** | Single-episode viewer |
| **FR81** | Closed, enumerable vocabulary for every failure, refusal and status shown |
| **FR82** | Divergence item → specification change action |
| **FR77 / FR108 / FR115** | Three-way classification; corrections as a divergence source; refusal adjudication |
| **FR102** | Human corrections captured as first-class records |
| **FR110** | Immediate suspension, and effects-only suspension, in one action |
| **FR73** | The episode record's content: turns, retrievals, model decisions, actions, authorities exercised, obligations and waivers, guard verdicts, errors, timings, model calls, tool calls, token counts, cost |
| **FR68 / FR69 / FR70 / FR71 / FR72** | Resolution envelope shown; escalation possibly a success; evidence vs resolution never conflated |
| **FR60 / FR62 / FR63 / FR67** | Three lifecycle states; resumption; late results; lifecycle is not a success signal |
| **FR50** | Multi-goal episodes with explicit parking and resumption |
| **FR74** | Escalation reason class |
| **FR46** | Degraded outcomes distinguishable by the caller |
| **FR75 / NFR10** | Evidence addressable and removable by tenant, episode, age |
| **NFR16** | Correlation identity "reportable by a person who experienced a problem" |

### 9.4 Requester-facing (email) surface
| FR | What it implies |
|---|---|
| **FR112** | Automated-agent disclosure in the first message of an episode |
| **FR111** | Terminal notice on a halted episode |
| **FR113** | Channel-appropriate written correspondence |
| **FR103** | The escalation email to the declared destination |
| **FR114** | Threading/quoted history, additional recipients, attachments, bounces, auto-responder loops |

---

## 10. EXPLICIT UX/UI STATEMENTS, CONSTRAINTS AND NON-GOALS

**These are the hard rails. Every one is verbatim.**

1. §1.1 — "The platform has no business-level control flow to author, and **the authoring surface must make sequencing unexpressible**." (also FR18)
2. §7.1 S3 — "The Builder, with **deep elicitation** | **Minimal burden and UI for the operator**; *not* minimal reasoning by the Builder."
3. §7.1 S10 — "**Operator surface: classified divergence list + single-episode viewer** | **The improvement loop, and nothing more.**"
4. §13.2 — "The operator-visible surface in V1 is the divergence list and the episode viewer only — **there is no alerting, and no metrics dashboard**."
5. §7.2 — "Metrics dashboard, escalation **inbox**, in-product specification **editor** | **Out of the V1 operator surface by decision.** ... Neither is a console surface"
6. **EX1 names UX directly** — "**The platform deliberately has no default voice and no character of its own** — this is a decision, not an omission, and **nothing downstream (UX, a later design pass, a starting point under FR8) may invent one**. A business that says nothing here gets a plainly-written agent, not a platform persona"
7. **FR1** — "never with a form or a fixed question set"
8. **FR3** — "It MUST NOT present a fixed questionnaire"
9. **FR101** — "deliberately **not** an in-product specification editor"
10. **FR81** — "Every failure, refusal or status an operator sees comes from a closed, enumerable vocabulary."
11. **FR52** — consequence class "is **visible, not internal**"
12. **FR54** — retry eligibility "is a **visible attribute**"
13. **FR19** — "human-readable and diffable ... **neither a generated prompt nor generated code**"
14. **FR46** — "A degraded or fallback outcome is always distinguishable from a healthy one **by the caller**, not only in a log line."
15. **FR117** — "A half-elicited specification is never presented as a complete one."
16. **FR99** — "**Burden and yield are reported together and neither is read alone.**"
17. **FR110** — "cannot be stopped in one action is not operable" → suspension is a one-action control
18. **FR24** — validation rejects sequencing "with a comprehensible reason"
19. **FR11 / O1** — approval is recorded and attributable to a named approver; the verdict vocabulary is undefined
20. §1.2 — "'General-purpose' ... **is not the customer-facing differentiator and does not appear in customer-facing positioning**" ← a copy/messaging constraint
21. §6 — forbidden vocabulary: "*workflow, state machine, business transition graph, workflow language, execution graph, stage, node*"
22. §4.4 — "**An outbound or proactive system** | An episode is initiated or resumed only by an inbound interaction or an external system event. The platform never independently starts an outbound conversation or episode" ← no "send a campaign" affordance may exist
23. §4.4 — "**A memory product** | No general long-term customer memory, no cross-episode profiling" ← no customer profile screen
24. §4.4 — "**A self-modifying system** | Behaviour changes are reviewed and promoted, never silently mutated"
25. §4.4 — "**A vertical product** | Not a booking, appointment, healthcare, sales or FAQ product. **Any vertical framing is out**" ← the UI may not look like a booking tool
26. **FR83** — "**The Agent and Core never learn which channel an episode is on.**" [INFERRED] a channel indicator belongs to the adapter/episode record, not to behaviour
27. **FR113** — "For V1 this means **written correspondence rather than conversational fragments**: a reply that reads as a message a business would send." ← the reply-composition tone rule, and the direct V1 replacement for the voice project's twenty-word spoken-string contract
28. **NFR13** — "No turn-latency target is set for V1" — no latency affordance needed [INFERRED]

---

## 11. CHANNEL AND INTEGRATION SURFACE

### 11.1 The one channel

**FR84** (verbatim): "V1 ships one channel adapter, providing both ingress and egress: **inbound email / messaging**."
§7.1 S9: "**One channel adapter: inbound email / messaging** | Behaviour written channel-neutrally."
**FR85**: "The adapter is replaceable without touching behaviour. Adding a channel later is adapter work, not re-specification."
**FR83**: "All behavioural requirements in this document are channel-neutral. **The Agent and Core never learn which channel an episode is on.**"

### 11.2 Email-specific conditions — FR114, verbatim (UX-bearing)

> The inbound email adapter handles the conditions that make email email, each of which can break episode identity or cause harm: **threading and quoted history** (a reply carries the whole prior conversation and must not be re-read as new input), **additional recipients** (who is party to an episode, and who must not receive its content), **attachments** (accepted as knowledge or refused, never silently ignored), **bounces and delivery failures** (a reply that never arrived is not a served goal), and **automated-sender loops** (an auto-responder on the far end must not produce an unbounded exchange). Each is pinned by a test under FR98.

Also **FR86** (episode correlation + join key), **FR87** ("guards against duplicate and corrected re-sends ... Turn handling is **idempotent per logical turn**"), **FR98** ("built against **captured real traffic**, not vendor documentation alone").

### 11.3 Why this channel, and the recorded doubt (§8.10 blockquote, verbatim)

> **Why this channel.** It is the operator's real inbound queue, and it is the stated source of the real requests the usefulness test needs. Being genuinely asynchronous, it exercises pending episodes and cross-session resumption honestly rather than simulating them. It also carries near-zero turn-latency pressure, which deliberately keeps the latency-as-correctness discipline of the voice project out of V1 — see §9.
>
> **And the honest weakness of that reasoning.** Every justification above is about **fitness for testing the architecture**, not about where the value is. ... For small-business inbound, the uncomfortable answer is that it is still substantially phone-led, and the funded competitors are voice-first. This document does not reverse the decision ... But the decision is recorded as **chosen for provability, not for value** ... O10 carries it.

*Note the phrase "rather than simulating them" — the PRD's stance is that the real async channel replaces simulation. [INFERRED] this is the closest thing to a reason why no simulated-inbox test surface was specified, and it is reasoning about the validation programme rather than about the operator.*

### 11.4 External systems the Agent touches

- **FR56**: "An external system is reached only as Core contract → adapter → extension. No feature promises a direct connection between the Agent and a third party."
- **FR36**: "External business systems remain authoritative. The platform owns no system of record." (§4.4: "**A system of record** | External business systems stay authoritative")
- **FR57**: "Adapter credentials are held at the adapter boundary and resolved per tenant. **No credential value appears in Core state, episode evidence, Agent context or any prompt.**" (NFR11 adds "or any evidence export")
- **NFR17**: "Configuration and credentials are validated at startup, not at first use. A health check MUST NOT report healthy on a configuration whose first real request will fail."
- **FR116** names the recurring extension-point examples: "identity verification, document intake, a derived figure, a validator or a scorer."
- **FR109**: "identity verification is an extension point, not Core semantics"
- §7.2: "Integration catalog or extension marketplace | The adapter contract is the forward-compatible seam; distribution is later product work" — **out of V1**

### 11.5 What the operator must connect / authorize and therefore see

**NO named integration is required in V1.** No CRM, calendar, booking system, payment provider or ticketing system is named as a V1 connection. The only concrete things an operator must supply or configure:

| Thing | FR | Status |
|---|---|---|
| Their business material / sources | FR2 | Required |
| Source precedence | FR31, EX14 | Required when sources conflict |
| General-domain-knowledge on/off as a declared risk | FR34 | Per business |
| An escalation destination (one address) | FR103, O2 | Required for operability |
| Disclosure wording | FR112, EX1 | Per business |
| The terminal notice | FR111 | Per business |
| A refusal sampling rate | FR115 | Business sets it |
| Granted capabilities + their contracts | EX8, FR51 | Per business |
| Data-lifecycle requirements | EX17, NFR10 | Captured in V1 |
| Per-tenant adapter credentials | FR57 | Wherever a capability reaches an external system |

**PRD SILENT on:** the email mailbox/inbox connection and authorization itself. FR84 ships an inbound email adapter, but nothing says how an operator connects their mailbox, which provider, whether OAuth is involved, or what they see while doing it. **This is a required-but-unspecified onboarding screen.** [INFERRED] FR57 (per-tenant adapter credentials) and NFR17 (validated at startup) are the only hooks.

---

## 12. SUCCESS METRICS / KPIs / ACCEPTANCE CRITERIA THE UI MUST SUPPORT

§10 preamble, verbatim:

> **No numeric target appears in this section, by decision.** No baseline exists, the public record on this problem is contaminated, and an invented threshold would later be quoted as though it were evidence. Every criterion is therefore structural or directional — and every one of them MUST be computable from the episode record without a human reading a transcript, which is itself a requirement (FR76) rather than an aspiration.

### 12.1 Per episode (§10.1, verbatim)

> Computable from the record: reached a declared resolution or a legitimate pending state; every business fact traceable to a pinned source; obligations complete before any action; actions taken only through contracts, with confirmation where required and evidence of success recorded; no conclusion drawn outside a declared authority; guards fired when their conditions were met; escalation reason recorded; no policy violation.

[INFERRED] this is effectively the checklist an episode viewer could render per episode — eight computable properties.

### 12.2 Per business (§10.2, verbatim)

> - Share of inbound episodes resolved without a human.
> - Share reaching the intended action — **reported separately** from the share blocked by the business's own rules or capacity, because conflating them makes a business constraint look like an Agent failure.
> - Human corrections per hundred episodes, **and whether that falls over time**.

*Important tension: these are per-business metrics, but §7.2 and §13.2 put a metrics dashboard out of V1. [INFERRED] they are computed and reported outside the operator UI in V1.*

### 12.3 Per project (§10.3, verbatim table) — the generalisation test

| Measurement | The thesis fails if |
|---|---|
| **Engine leaks** — every instance where the Core had to change rather than the business layer, classified per FR89 | Leaks do not fall toward zero from the first business to the fourth |
| **Resolution-model strain** — per FR90 | Any business cannot be expressed, which would mean evaluation cannot be reusable |
| **Setup effort** — per FR91 | Effort does not fall materially across the sequence |

**FR89** (verbatim): "**Engine leaks** are recorded and classified: *should have been configuration*, *justifies an extension point*, or *genuinely novel*."
**FR90**: "**Resolution-model strain** is recorded — whether any business needs a resolution the model cannot express."
**FR91**: "**Setup effort** is recorded per business from the Builder's own burden instrumentation (FR12), and compared across the four in the order they were built."
**FR93**: "The **validity floor** is recorded: the share of episodes requiring obligations, rules or action rather than plain information. This is a measurement of the test, not a product metric — but if it is near zero, the demonstration proves nothing however good the other numbers look."
**FR94**: "Two or three conversations with real small-business operators are conducted, as the only available test of the problem statement and of the printed-versus-practised gap."

**FR76** (verbatim) — the computability boundary, narrowed:

> Every **per-episode and per-business** criterion in §10.1 and §10.2 is computable from the episode record **without a human reading a transcript**. The per-project measurements in §10.3 are deliberately not of this kind — classifying an engine leak and judging resolution-model strain are acts of engineering judgement, recorded by a person during the validation programme.

### 12.4 Counter-metrics (§10.4, verbatim table) — anti-gaming guards the UI must not break

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

**These are direct UI prohibitions.** Any status badge that colours `closed` green and `pending` amber violates "Lifecycle is never read as success". Any single place that shows "resolved without a human" next to "blocked" without separating Agent failure from business-constraint blocks violates guard 1.

### 12.5 Acceptance criterion for the whole architecture (§5, verbatim)

> **Can a new business be onboarded without generating a business-specific execution graph or state machine, while the Agent still reasons about situations nobody enumerated?** Yes means an agent platform. No means a workflow engine with a model attached.

### 12.6 The falsification table (§5, verbatim, abridged to the two claims)

> | **Architecture claim** — one Agent system handles materially different small-business requests while only the business layer changes | Partially tested. ... | Engine changes do not fall toward zero across the four businesses; or setup effort does not fall materially across the sequence |
> | **Usefulness claim** — the resulting Agents resolve a meaningful class of real inbound requests well enough to be useful, not merely technically impressive | Untested | A low share of real inbound requests reaching a correct resolution without a human; or a high share of requests needing only plain information, which would make a good result prove nothing |

---

## 13. ADDENDUM — WHAT IT REVISES, OVERRIDES OR CONTRADICTS

### 13.1 Its own status line (addendum header, verbatim)

> **Addendum to the Agent Studio PRD.** Depth that belongs downstream — to architecture, solution design, UX specification or evaluation planning — rather than in the PRD body. **Nothing here is a product commitment unless the PRD says so.**

**The addendum names UX specification as one of its downstream audiences, so it is in scope for this work — but it commits to nothing.**

### 13.2 ⚠️ FLAG — the one genuine revision, and it bears on §12

**AD1.3** (verbatim, emphasis in source):

> The source material named several low-cost tests capable of falsifying parts of the thesis before much is built — small probes rather than programmes. They are recorded here because the PRD's validation programme (E12) is substantial and slow by comparison, and because at least one of them tests something the PRD instead **promoted to a requirement without testing**: that every success criterion worth having is computable from an episode record without a person reading it. **FR76 has since been narrowed to the per-episode and per-business criteria (§10.1, §10.2), where that is actually true** — the correction that probe would have produced. Anyone planning E12 should look for the cheap version of each measurement first.

**Status: this revision is already reflected in the PRD body** — FR76 as published already reads "Every **per-episode and per-business** criterion". So AD1.3 documents a *completed* narrowing rather than an outstanding override. No conflict remains. Flagging it because it is the only place the addendum says the PRD was wrong.

**UX consequence:** §10.3's three per-project measurements are **explicitly NOT auto-computable** and are "recorded by a person during the validation programme". Do not design a surface that purports to compute them.

### 13.3 ⚠️ FLAG — AD3 could be misread as licensing model calls. It does not.

**AD3 header** (verbatim): "**Status: implementation and evaluation opportunities only. Not product requirements, not architectural commitments.**"

**AD3** (verbatim): "The PRD body names no model, no provider and no vendor API. **Provider agnosticism is a hard boundary** ... That rule is unaffected by everything below."

**AD3.1** (verbatim): "This does **not** license adding model calls freely. The limit that survives from the shipped voice project is the one the PRD states in §1.3: cost and latency are not licences, and no model call is added to a path a person is waiting on without measuring that path. What changes is the cost argument, not that limit." And: "**Multi-model routing and tiering remain an implementation and evaluation question.**"

**AD3.2** (verbatim): "Not every intelligent decision needs the full Agent loop." With two cautions: "A typed decision call used to pick the Agent's next step is deterministic next-action selection, which FR39 forbids — such a call may constrain or classify, never sequence. And a model-evaluated guard is still bound by FR44: two closed outcomes, and never a composed reply."

Closing (verbatim): "Both developments are carried as **candidates for the later model and runtime strategy, and for the proof gate (§7.5)** — nothing more. Neither is a product dependency, neither appears in the PRD body, and **neither may be cited as satisfying a requirement**."

Sourcing caveat (verbatim, AD3.1): "the specific model generation and its published positioning were supplied by the project owner, are taken as given, and are not independently verified."

**No UX consequence. Nothing here changes a requirement.**

### 13.4 AD1 — positioning depth, no override

**AD1**: the full competitor inventory, configuration-paradigm evidence, "the conventional 2026 trust-surface set that buyers now expect as table stakes", small-business adoption friction (cost, knowledge gaps, trust, integration friction, "the finding that a large majority of non-adopting small businesses report seeing no applicable use case"), pricing norms and per-resolution anchors, usage/credit unpredictability as a leading churn driver, and the vertical-beats-horizontal counter-evidence. "These inform positioning and go-to-market rather than V1 requirements, which is why they are here and not in the PRD." Detail lives in `extract-landscape.md`, not in the addendum.

[INFERRED, flagged for the UX] "the conventional 2026 trust-surface set that buyers now expect as table stakes" is named but **not enumerated** in the addendum. If the UX wants a trust-surface inventory it must read `extract-landscape.md`. I did not read it — it is outside my brief.

**AD1.1**: "market evidence is recorded and is not permitted to steer the product toward hunting an empty niche ... Anyone revisiting this evidence later must read it with the condition attached, or they will re-derive a vertical product from it."

**AD1.2** — the rejected position, relevant to any UI that would look like a system of record: "A tempting position for this product is the **intelligence layer sitting on top of systems of record it does not own**. It was rejected ... the owner of the system of record controls the write API, owns the distribution, holds the outcome data, and can price on outcome *because it alone observes the outcome*." And: "**a third party without the join key cannot price on outcome at all** ... That is why the PRD's episodes carry an explicit join key where they touch an external system of record (FR86, §6)."

### 13.5 AD2 — brownfield lessons, two with direct UX force

**AD2** (verbatim, the relevant lesson): "**A graceful fallback that looks like success is the most expensive bug class there is.** Two logged instances. An empty-but-set environment variable made every model tier fail while a mock fallback served plausible deterministic text under a banner claiming live operation — **the verification had checked the mode *label*, not a completion.** And a fabrication guard presented an honest-sounding decline that masked three stacked retrieval faults. This is the origin of FR46 and NFR17, and the reason a health check must prove a real request rather than inspect configuration."

**This is the strongest argument in either document for a real operator-facing test interaction, and it is also a warning about how to build one: a test that checks a label rather than a completion is worse than no test.** [INFERRED] a "your Agent is ready" indicator derived from configuration rather than from an actual exercised reply is precisely the logged failure mode.

Also from AD2: "**Config-driven generation fails in two specific ways.** A ship gate coupled to one domain forced the builder into a rewrite loop, and the reaction was to stub the gate so it always passed — the check was disabled to stop the pain, which is the worst available outcome and the direct reason for FR95." [INFERRED, UX-relevant] a validation gate that is painful to satisfy gets bypassed; the validation-failure presentation (FR24's "comprehensible reason") is therefore a product-risk surface, not a cosmetic one.

And: "**What is deliberately not inherited.** Four gaps in the shipped system: no instrumentation on any model call; no correlation identity outside the voice path; minimal persistence; single-tenant by stated non-goal. ... Documentation and tests in that repository have drifted before; treat them as claims to verify, not as ground truth."

**No addendum item contradicts the PRD body.** The only correction (AD1.3 / FR76) is already absorbed.

---

## 14. CONSOLIDATED "PRD SILENT" REGISTER

Ranked by how much it blocks the UX spine.

| # | Silent on | Why it blocks | Nearest hook in the PRD |
|---|---|---|---|
| **S-1** | **The entire pre-go-live testing interaction.** No test/try/preview/simulate/replay/sample-send surface exists. What the operator sends, what comes back, what they judge, what they do with it — all absent. | This is the UX's primary assigned subject and the PRD gives nothing to build on | FR22/FR25 (automated suite), FR11 (human approval of a *document*), O11 (counterfactual replay, **undecided**), FR100 (team fixture), FR92 (team corpora), FR110 (effects-only suspension) |
| **S-2** | **The specification's rendered form and field schema.** EX1–EX17 are named; nothing below them is. Also: how seventeen areas are navigated, how a "recorded absence" (FR14) looks, how a diff (FR19) is presented, and how FR8's "fully editable" reconciles with FR101's no-editor rule. | The review-and-correct surface is the second assigned subject and has no concrete shape | FR14 (separately addressable/reviewable), FR19 (readable+diffable), §8.3 ("promotion is a pull request on behaviour"), **O7** (schema deferred to E1) |
| **S-3** | **The approval interaction (FR11 / O1).** O1 states plainly "no reviewer role or review verdict is defined anywhere in the sources." No approve/reject/request-changes vocabulary, no reviewer identity model, no relationship between Business Operator / Specification reviewer / FR115 adjudicator. | Promotion is blocked on an act nobody has designed | FR11, FR28, O1 |
| **S-4** | **Mailbox connection and authorization.** FR84 ships an inbound email adapter; nothing says how an operator connects their mailbox or what they see doing it. | A required onboarding screen with no requirements | FR57 (per-tenant adapter credentials), NFR17 (validated at startup) |
| **S-5** | **Divergence record fields and item lifecycle.** No title/summary/severity/state/assignee; no "mark resolved"; no list filtering, grouping or sorting; no notification. | The primary operator surface (FR79) is one sentence | FR77 (class), FR102 (episode + spec version), FR81 (closed vocabulary), FR82 (actionable) |
| **S-6** | **The refusal-adjudication interaction (FR115)** and where the business sets its sampling rate. | A MUST-level requirement with no surface | FR115, FR78 |
| **S-7** | **Episode viewer layout.** FR73 lists thirteen record categories; FR80 is one sentence. No hierarchy, no transcript-vs-evidence treatment, nothing on how the §10.1 per-episode criteria are shown. | A named V1 surface | FR73, FR80, §10.1 |
| **S-8** | **Who confirms an FR53 confirmation**, and through what surface. Requester? Operator? | Confirmation gating is central to the authority model | FR53, FR109, §7.4 "the human-authorization interrupt" |
| **S-9** | **Starting-point selection (FR8).** How offered, how many, whether the operator sees one was used. | FR8 is the only onboarding accelerator | FR8, §8.1 closing note |
| **S-10** | **Where burden/yield (FR12/FR99) and the §10.2 per-business metrics are seen**, given the dashboard is out of V1. | A reported metric with no reader | FR12, FR99, §10.2, §7.2 |
| **S-11** | **Contradiction resolution (FR5) and narrated-process re-derivation (FR104) as interactions.** Both MUST be surfaced; neither has a form. | Two of the Builder's distinguishing behaviours | FR5, FR104, FR117 |
| **S-12** | **Visual/brand/tone of the product itself.** EX1 forbids a platform *agent* persona; it says nothing about the *platform's* own interface voice. | [INFERRED] DESIGN.md has no stated constraint except §1.2's messaging rule and §4.4's no-vertical-framing rule | EX1, §1.2, §4.4 |

---

## 15. VOCABULARY TO CARRY FORWARD VERBATIM

Use these words; the PRD uses no others for these concepts (§6).

**Agent · Core · Business Specification · Business Knowledge · Builder · Episode · Requester · Request kind · Safety halt · Capability · Goal / obligation · Resolution · Evidence · Provenance reference · Escalation · Guard condition · Promotion · Extension · Business Operator · Specification reviewer · Escalation recipient · divergence · specification defect · business refusal · platform error · specification backlog · validation suite · consequence class · decision authority class · terminal notice · diagnostic inputs · waiver · late result · engine leak · validity floor · expression surface**

Request kinds: `retrieve` `read` `effect` `clarify` `respond` `escalate` `suspend`
Lifecycle states: `active` `pending` `closed`
Authority classes: `informational` `liability-bearing` `state-changing`
Consequence axes: reversible? costs money? reaches a customer?
Denial classes: `specification defect` `business refusal` `platform error`
Engine-leak classes: `should have been configuration` `justifies an extension point` `genuinely novel`
Variation levels: `configuration` `supported extension point` `custom implementation`

**FORBIDDEN (§6):** *workflow · state machine · business transition graph · workflow language · execution graph · stage · node*
