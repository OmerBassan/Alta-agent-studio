---
status: final
updated: 2026-10-10
project: AgentStudio
owns: information architecture, behaviour, states, interactions, accessibility, journeys
peer: DESIGN.md
sources:
  - ../../prds/prd-AgentStudio-2026-10-08/prd.md
  - ../../architecture/architecture-AgentStudio-2026-10-07/ARCHITECTURE-SPINE.md
  - ../../briefs/brief-AgentStudio-2026-10-07/brief.md
---

# EXPERIENCE.md — Alta Agent Studio (V1)

This document owns **how it works**. [DESIGN.md](DESIGN.md) owns **how it looks**. They are peers; neither outranks the other. Visual tokens are referenced here by name as `{path.to.token}` and are defined in DESIGN.md, never here.

Decision provenance lives in `.memlog.md`. Source extracts live in `.working/`.

**Visual references** are in [mockups/](mockups/) and are linked at the sections they illustrate. They are static HTML that shows one or two states per file stacked on a page, so they are not the target layout (see Application layout). **Where a mock and this document disagree, this document wins.**

---

## Foundation

**Form factor.** Responsive web, desktop-first. No native mobile application in V1.

- Desktop-first: the Builder conversation, Understanding, correction, approval.
- Must be fully usable on a phone: Activity, the interaction viewer, and suspend.

**UI system.** None inherited. The preceding voice product is engineering and interaction reference only; it contributes no visual or component language. DESIGN.md originates the visual identity from scratch.

**Theme.** One theme, light only, for V1.

**Locale and connectivity.** English-first, online-only. Internationalisation and offline support are out of V1.

**Stakes.** Design-partner / early access. Real businesses, real customer interactions, so trust, oversight and accessibility are real requirements. V1 is a controlled validation phase, not a self-serve commercial product: there is no funnel, no pricing, no trial, and no compliance, audit or retention surface.

### The locked mental model

> **Conversation is the mechanism. Understanding is the persistent object being formed. Activity is where runtime reality is reviewed.**

Every structural decision in this document derives from that sentence. The product the operator experiences is *hiring and teaching an intelligent worker*, not configuring software.

### The two voices, which are never merged

| Voice | Who speaks | To whom | Who authors it |
|---|---|---|---|
| **Product voice** | The platform and the Builder | The operator | Us. Specified below under Voice and Tone. |
| **Agent voice** | The Agent at runtime | Requesters (customers) | **The operator, per business.** |

PRD **EX1** is explicit that the platform *"deliberately has no default voice and no character of its own — this is a decision, not an omission, and nothing downstream (UX, a later design pass, a starting point under FR8) may invent one."* That prohibition governs the **Agent voice only**. A business that declares nothing in EX1 gets a plainly-written Agent, never a platform persona. Nothing in this document or in DESIGN.md may supply, suggest or default the Agent's voice.

### What is sourced and what was originated here

Most of this document derives from the finalized PRD, Architecture Spine and Product Brief. The V1 channel is sourced: PRD **FR84** reads *"V1 ships one channel adapter, providing both ingress and egress: inbound email / messaging."* (The Product Brief had left the channel open; the PRD settled it.) Two things are not sourced, and are flagged wherever they appear:

1. **Connect your mailbox**: a required surface that no upstream source describes.
2. **Divergence notification by escalation email**: an explicit amendment to PRD §13.2, which states *"there is no alerting."* See Amendments.

---

## Information Architecture

### Two destinations and one mechanism

```
  ┌─────────────────────────────┬─────────────────────────────┐
  │        UNDERSTANDING        │          ACTIVITY           │
  │   what we know about how    │   where behaviour and       │
  │   your business works       │   intent came apart         │
  └─────────────────────────────┴─────────────────────────────┘
                        ▲
            ┌───────────────────────┐
            │   THE CONVERSATION    │
            │  a mechanism, opened  │
            │  from a place — never │
            │  a destination        │
            └───────────────────────┘
```

**Understanding** is the centre of gravity: the Business Specification, the thing the operator owns. **Activity** is the divergence list and its interactions. **The conversation is not a destination** — it opens from wherever the operator is, always carrying that context.

This satisfies PRD **FR101** (correction happens through the Builder conversation, *"deliberately not an in-product specification editor"*) while scoping each correction without any click-to-edit affordance. One mechanism, three entry points: a specification section, a divergence item, an interaction.

There is no further navigation. PRD §7.1 S10 gives the operator *"classified divergence list + single-episode viewer — the improvement loop, and nothing more"*, and §7.2 places the metrics dashboard, the escalation inbox and the in-product specification editor out of V1 by decision.

### How the pieces connect: the Build / Run map

Two places, **Understanding** and **Activity**, joined by one mechanism, **the Builder conversation**. The correction loop is that mechanism, entered from either place.

**Build** happens once, at a desk, before any customer can reach the Agent.

1. The operator opens the workspace and meets one open prompt: *"Tell me about your business and the customer requests you want me to handle."* Supporting material is optional.
2. They talk with the Builder. Beside the conversation, **Understanding** forms: what the Builder currently understands about how the business works. Anything not yet clear is marked **Not established**.
3. Where Understanding is wrong, they say so in their own words. The Builder shows the exact change (before, after, also affected, unchanged) and they confirm it. *This is the correction loop.*
4. When they are ready, the automated validation runs and its findings are shown. They approve the specification version.
5. They connect the mailbox. From this moment the Agent is live and customers can reach it.

**Run** is ongoing, often from a phone.

6. The Agent answers customer email. When it reaches the edge of its authority, it hands the request to a human by email to the declared address. The operator needs no login to act on it.
7. Where the Agent's behaviour and the business's intent came apart, the item appears in **Activity**. A material one may also arrive by that same email path (Amendment 1).
8. The operator opens the item and reads the interaction: what the customer wrote, what the Agent replied, and what in their specification or material that reply was based on.
9. If it was wrong, **This was wrong** opens the Builder conversation with that interaction as context. This is the same correction loop as step 3, and it leads to a new validated, approved, live version.
10. At any point they can suspend the Agent in one action, from the phone as well.

```
  BUILD                                        RUN
  ─────                                        ───
  Conversation ──► Understanding               Customer email ──► Agent reply
        ▲              │                                              │
        │              ▼                                              ▼
        └──── correction loop ◄──── "This was wrong" ◄──── Activity ◄─┘
                       │
                       ▼
          validation ──► approval ──► live version
```

This diagram shows **how the operator moves between surfaces**. It is documentation for the people building the product and must never appear in the product: the authoring surface itself carries no arrows or sequence (see The sequencing prohibition).

### Surface inventory

| Surface | Primary job | Mobile |
|---|---|---|
| Cold-start workspace | Begin. Lightweight framing, nothing else | No |
| Builder conversation | Elicit business behaviour | No |
| Material intake | Add supporting material; show provenance | No |
| Understanding | Review what the Builder understands | Read-only |
| Correction diff | Confirm an exact behavioural change | No |
| Validation result → approval | Gate, then the operator's decision | No |
| Connect mailbox | Go live | No |
| Activity (divergence list) | Find what went wrong | **Yes** |
| Interaction viewer | Understand one interaction | **Yes** |
| Suspend | Stop it now | **Yes** |

### Understanding: five document sections over seventeen expression areas

The Business Specification's expression surface is PRD **EX1–EX17**, each area *"separately addressable, separately reviewable, separately checkable."* The seventeen group into five named document sections with nothing left over and nothing invented:

| Section | Expression areas |
|---|---|
| **Your business** | EX1 identity — what the business is, how it speaks, and what it will not say |
| **What the Agent handles** | EX2 goals and what resolving each means · EX3 what may never become a goal |
| **What it knows** | EX14 authoritative sources and their precedence when they conflict · EX17 data-lifecycle requirements |
| **How it operates** | EX4 what must be established before each outcome · EX5 what helps it reason without being required · EX6 rules — eligibility, pricing, timing, policy, constraints · EX9 guard conditions · EX15 what evidence is required and what happens when it is absent · EX16 what good looks like here |
| **What it may and may not do** | EX7 what it may conclude and on whose authority · EX8 which capabilities are granted and under what contract · EX10 escalation — what this business will not let an Agent decide · EX11 refusal conditions · EX12 what may be asked and what must never be asked · EX13 what it must not infer or do |

EX4 and EX5 are deliberately adjacent: FR15 distinguishes *required* from *merely helpful*, and separating them across sections would destroy that distinction.

Below the seventeen areas there are **no field names**. The PRD defers the schema (O7 → epic E1). This document therefore specifies the *behaviour* of the surface and leaves its fields to the schema work.

### The sequencing prohibition

PRD §1.1 and FR18 are a **positive obligation**, not merely the absence of a flow builder:

> *"The platform has no business-level control flow to author, and the authoring surface must make sequencing unexpressible."*

The five sections are a **document hierarchy**. The reading order is retained; every affordance that would let an operator express or infer order is forbidden:

- no arrows or connectors
- no step numbers
- no progress rail, stepper or breadcrumb of stages
- no "next", "then", "after this", or "continue"
- no percentage, completion meter or checklist
- no visual treatment implying runtime sequence

Hierarchy is carried by typography and spacing alone. The risk this guards against is concrete: rendered with arrows, `Your business → What it handles → What it knows → How it operates → What it may do` reads as the Agent's runtime sequence. It is not. It is the order in which a human most easily comes to understand their own business written down.

---

## Voice and Tone

The **product voice** only. The Agent's voice belongs to the operator (see Foundation).

**Register.** Calm, intelligent, clear, business-oriented. Conversational rather than technical. A capable colleague who has read the material and is trying to understand how the business actually works — never a wizard, never a cheerleader, never a terminal.

**The operator never meets these words as user-facing concepts:**

> agent¹ · prompt · RAG · policy · model · graph · node · workflow · tool · embedding · retrieval · state · schema · episode² · guard condition · contract · obligation · token

¹ "Agent" is unavoidable as the name of the thing being built, and is used *as a noun for the worker*, never as a technical category. ² "Episode" is the internal term; the operator-facing word is **interaction**.

**Say this instead:**

| Instead of | Say |
|---|---|
| prompt / generated prompt | your business specification · what we understand |
| RAG, retrieval, grounding | your own material · your authoritative sources |
| policy, policy engine | your rules |
| evaluation criteria | what good looks like here |
| human-in-the-loop | hand to a human, with why |
| granted tools / capabilities | what it may do |
| model general knowledge | general knowledge, not from your material |
| episode | interaction |
| escalation | handed to a human |

**Copy prohibitions.**

- **No vertical framing.** PRD §4.4: *"Not a booking, appointment, healthcare, sales or FAQ product. Any vertical framing is out."* The interface may not read as a booking tool.
- **Never "general-purpose."** PRD §1.2: it *"is not the customer-facing differentiator and does not appear in customer-facing positioning."*
- **No hiring claim.** The hire-an-AI-worker framing shapes the *experience* but is *"Direction of travel. Not a V1 commercial promise"* (§1.2) and must not appear as a product claim.
- **No market statistics.** The Product Brief addendum records the abandonment, complaint-rate and missed-opportunity figures in circulation as fabricated by a vendor selling the human alternative. None may appear in any copy.
- **No celebration.** Approving a specification version is a decision the operator owns, not an achievement. No confetti, no "You're all set!", no success theatre.

**The closed vocabulary rule.** PRD **FR81**: *"Every failure, refusal or status an operator sees comes from a closed, enumerable vocabulary."* Strings are taken from this list, not written ad hoc per screen. It is the V1 seed list; anything an upstream contract adds (Amendments 4, 5, 13) extends it.

| Group | Strings |
|---|---|
| Item states | Established · Not established · Changed · Affected by this change |
| Divergence classes | Your specification got this wrong · Your rules said no · Something on our side failed |
| Agent status | Live, mailbox connected · Suspended, not replying or acting · Suspended, replying but not acting · Not live, mailbox not connected |
| Validation | Checking your specification · Blocking · Not blocking · This version cannot be approved until the blocking finding is resolved · The check could not run. Nothing has changed. |
| Approval | The automated check decided this version is valid. You are approving it to go live. · Conversations already underway will finish on the previous understanding. |
| Interaction viewer | Nothing was refused and nothing failed. · Answered from general knowledge, not from your material. · The Agent said this was done. There is no evidence it happened. · Handed to a human. · Declined under one of your rules. |
| Degraded and failed | Could not be read. Nothing from it has been used. · The Builder could not reply. Nothing has changed. Try again. · This interaction could not be loaded. · Suspend did not apply. The Agent is still live. Try again. · The mailbox is no longer connected. Customers cannot reach the Agent. · Something on our side failed. Reference: {code} |
| Pending | Thinking · Reading your material · Checking your specification · Suspending |
| Empty Activity | Nothing has come apart since {time}. *(always shown with the Agent status line)* |

---

## Component Patterns

Behavioural specifications. Visual specifications for the same components live in DESIGN.md.Components.

### Conversation panel

Opens from a specification section, a divergence item, or an interaction, and always carries that origin as visible context. It is the sole authoring and correction mechanism.

- **Never presents a form or a fixed question set** (FR1), and **must not present a fixed questionnaire** (FR3).
- Asks follow-up questions dynamically where it detects ambiguity or missing business behaviour — notably the gap between written policy and actual practice, which the Product Brief calls the trust failure *"the one that destroys trust fastest."*
- Carries *"minimal burden and UI for the operator; not minimal reasoning by the Builder"* (§7.1 S3). The surface stays simple precisely because the reasoning underneath is not.
- Streaming behaviour is unspecified upstream (the Spine names no streaming decision). Pending.

### Understanding document

Reference: [mockups/key-hero.html](mockups/key-hero.html) (state two is cold start).

A readable, reviewable document — **never a configuration form**. No form fields, no toggles, no dropdowns, no settings rows anywhere in it. Five sections, document hierarchy, no sequencing affordances.

**Live Understanding.** The conversation and Understanding are **co-present**. As the conversation establishes sufficiently grounded information, Understanding updates alongside it.

The surface must make one distinction unmistakable: this is **what the Builder currently understands**, not a specification being continuously edited live. A persistent frame states this. No conversational turn modifies the live version; the pipeline is always `conversation → generated understanding → automated validation → operator approval → live version`.

### Item state marker

Every reviewable item carries exactly one state from the enumerated set in State Patterns. The marker is text-led, never colour-alone (see Accessibility Floor).

### Correction diff

Reference: [mockups/key-diff.html](mockups/key-diff.html) (state one is the diff; state two is the validation result and approval).

The product's most important component. Given a correction stated in the operator's own words, it presents:

1. **Before** — the current wording, verbatim.
2. **After** — the proposed wording, verbatim.
3. **Also affected** — every other item the change touches, named.
4. **Unchanged** — explicitly stated, so the blast radius is bounded and visible.
5. **Accept** / **push back** — push-back returns to the conversation, never to a form.

Accepting produces a new specification version (FR21: versioned, immutable). The diff is plain-language throughout; PRD §8.3 frames the act as *"promotion is a pull request on behaviour"*, but nothing in the operator's view may borrow version-control vocabulary.

### Validation result

One blocking automated gate (FR22: *"exactly one gate, the validation suite"*; FR25: *"no separate, weaker pre-deployment check"*; FR95: platform-owned, never authored by the Builder it gates). Shown **at the approval moment**, not as a separate destination.

The result must distinguish what blocked from what merely warned, in the closed vocabulary. It is the system's verdict on validity; the operator's approval is a separate act.

- **Only actual findings are shown.** Each finding the suite returned is listed, marked **blocking** or **not blocking**, stated in plain operator language, and pointed at the part of Understanding it concerns.
- A blocking finding says plainly that the version cannot be approved until it is resolved. It is resolved through the Builder conversation, never by an override.
- A non-blocking finding is information the operator may act on or accept. It never blocks approval.
- **Nothing hypothetical.** The surface does not describe what *would* have blocked, or checks that did not run, unless a validation-result contract supplies that information. None currently does (Amendments, item 13).

### Approval

The operator is the approver in V1 (no reviewer role, no hierarchy). Recorded and attributable (FR11), and blocking.

The framing must be honest: **approval does not determine validity** — the automated gate does that. The operator approves the resulting specification version. No ceremony is added for its own sake, and the surface must not imply the operator has personally verified the Agent's behaviour.

### Divergence list

Reference: [mockups/key-activity.html](mockups/key-activity.html).

Grouped by the fixed three-class taxonomy (FR77), which must read as visibly different **kinds**, never as severities on one scale:

| Class | Operator-facing framing | Reads as |
|---|---|---|
| Specification defect | *"Your specification got this wrong"* | Actionable. The only class that enters the backlog (FR78) |
| Business refusal | *"Your rules said no"* | **Correct behaviour.** Must not read as a problem, an error or a warning |
| Platform error | *"Something on our side failed"* | **Not the operator's fault**, and the copy must say so |

Three sources feed this list:

1. Classified denials (FR77).
2. **Recorded human corrections** (FR102 / FR108) — the *permitted, confident and wrong* class. Nothing was denied, no detector fired. This source has no automatic entry path and arrives only via the interaction viewer's "This was wrong" action.
3. Sampled refusals adjudicated wrong (FR115), at a rate the business sets.

**V1 shows the minimum needed to recognise an item and open it.** Each item carries:

- its **class**, as one of the three framings above;
- the **interaction label** (see Interaction viewer: email subject and time, with a deterministic fallback);
- the customer's request as written, truncated to a single line.

Nothing else. Explicitly **not** in V1: a severity or priority model, retry eligibility, per-class counts or any other metric, sorting by importance, filters, charts, or a list of all interactions. The list contains **divergences only**. It is not a view of the Agent's work and must not grow into a monitoring dashboard.

**The Agent's status is always shown above the list** in plain words: live with mailbox connected, suspended (fully or actions only), or not live. An empty Activity list therefore never reads as good news on its own: *"Nothing has come apart since {time}"* appears only alongside that status line. *Not live* or *Suspended* above an empty list means nothing is being checked. This status depends on contract gaps 4 and 18.

Items are grouped under the three class framings, newest first within each group. Nothing upstream aggregates or deduplicates, so repeated occurrences of one underlying problem appear as separate items in V1. Grouping them is recorded as an open refinement, not solved by inventing a classification.

### Interaction viewer

Reference: [mockups/key-interaction.html](mockups/key-interaction.html).

*Internally this is an "episode". The operator-facing word is **interaction**.*

It is opened **only from an item in Activity**. It is not a monitoring view, and there is no list of all interactions.

It answers one question in the operator's terms: **what did the customer ask, what did the Agent reply, and what was that reply based on?** It has three parts and one action:

1. **The customer's email**: the inbound message thread, verbatim.
2. **The Agent's reply**: verbatim. Where the Agent did not reply itself, a plain statement that the request was handed to a human or declined under one of the business's rules.
3. **What this reply was based on**: the parts of the operator's own specification and material the Agent relied on, quoted and linked to where they live in Understanding. Where the reply drew on general knowledge rather than the business's material, the viewer says so. Where the Agent reported doing something, such as a booking or a change, the viewer states whether there is evidence that it actually happened.
4. **This was wrong**: opens the Builder conversation with this interaction as context. It is the same mechanism as every other correction; there is no second workflow. **Suspend** is also reachable from here.

**No generated explanations.** Every word in the viewer is either recorded material (emails, replies, quoted rules and sources) or a fixed sentence from the closed vocabulary filled in with recorded data. No model is called to summarise, explain or justify an interaction after the fact. Such an explanation would cost a model call per view, and could state reasons that did not occur.

**The internal record is not the layout.** The record holds a resolution envelope (goal, served, authority, evidence, payload) and much more (FR73). That structure feeds parts 2 and 3 but never appears as headings, labels or sections. The Architecture Spine also forbids reading the step sequence as a permitted order, so the viewer shows no pipeline, progress diagram or ordered trace.

**Interaction label.** No title or summary is stored, and none is generated. The label is the **email subject plus the received date and time**. Where there is no subject, the deterministic fallback is **"Customer email · {received date and time}"**. Whether the stored record keeps the subject is unconfirmed (Amendments, item 14).

### Suspend

One action (FR110), including effects-only suspension. Reachable on mobile. Reversible.

- **Suspend** stops the Agent replying and acting, in one press, with no confirmation step. An emergency brake that asks a question first is two actions.
- **Stop actions only** is a separate, adjacent action for effects-only suspension: the Agent keeps replying but can no longer act.
- The result is announced as a status message and shown in the Agent status line (*Suspended, not replying or acting* or *Suspended, replying but not acting*).
- If suspension does not apply, the operator is told plainly (*"Suspend did not apply. The Agent is still live. Try again."*). A suspend that silently failed is the worst failure this product can have.
- **Let the Agent act again** resumes. It is a secondary action and never looks like Suspend.

> **Upstream contract gap.** The Architecture Spine models no persistent suspended state and contains no agent status enum at all. This document states the operator-visible need; it does not invent the field. Raise with architecture before implementation.

### Material intake

Add supporting material, optionally, inside the cold-start surface and later from Understanding.

The operator must understand **what material was ingested and its provenance** — the Spine carries `(tenant, source, source version, locator)`, and sources are version-pinned (FR30). Because uploaded material may contain sensitive business or customer information, provenance is shown at that level and no further: **no compliance dashboard and no regulatory controls in V1.**

Accepted formats, size limits and ingestion duration are unspecified upstream. Pending.

---

## State Patterns

### Specification item states — the enumerated set

| State | Meaning | Rendering rule |
|---|---|---|
| **Established** | Settled and in force | Default |
| **Not established** | A **recorded absence** (FR14: *"a recorded absence, never an implied default"*) | **First-class and visually distinct.** Never rendered as empty, as blank, as a default value, or as "no" |
| **Changed** | Differs from the live version | Shown with its before/after available |
| **Affected by this change** | Knock-on from another change | Named in the diff's "also affected" |

**"Not established" is the most dangerous state in the product to render badly.** An absence that reads as a benign value is the failure mode that costs most: it looks like good news and nothing alerts. It must be legible as *"we have not established this"* and never as *"this is off"*.

**Governance.** "Not established" stays visible throughout the conversation and may pull it forward, but it must **never** become a progress bar, a checklist, or an implied completion target. A finite set of boxes to tick would reintroduce exactly the fixed questionnaire FR3 forbids.

### Degraded and uncertain states the UI is obliged to show

The Architecture Spine requires that errors cross boundaries as typed results, never as defaults. Each of the following must be visibly distinguishable from a healthy result **by the operator**, not merely in a log line:

| Condition | Must read as |
|---|---|
| Specification defect | Yours to fix |
| Business refusal | Your rules working correctly — **not a problem** |
| Platform error | Not your fault |
| Safety halt | A distinct terminal state with its recorded outcome |
| Answer drawn from general knowledge | **Marked as not from your material** (per-business switch, FR34, declared as a risk) |
| Claim refused for invalid or cross-tenant provenance | Refused before it reached the person |
| Resolution refused for lack of evidence | *"The Agent said it booked it"* is not *"it is booked"* |
| Required authority or evidence unavailable | Handed to a human, with why |
| Non-retryable failed effect | Needs a human, stated in plain words in the interaction where it occurred. Retry eligibility (FR54) is shown there, never as a field in the Activity list |
| Consequence class of an action | **Visible, not internal** (FR52) |

**The uncertainty ceiling.** The Spine states that semantic faithfulness beyond provenance validity is *"evaluated against a threshold, never guaranteed."* The product may therefore never promise the Agent is never wrong. It may promise only that the Agent never cites a source it was not given, and never reports that something happened without evidence that it did. All copy must hold that line.

### Failure and in-between states

Each of these is distinguishable from success by the operator, in closed-vocabulary words (Voice and Tone):

| Situation | What the operator sees |
|---|---|
| A Builder turn fails or times out | *The Builder could not reply. Nothing has changed.* The operator's message is kept and can be sent again |
| Material cannot be read | *Could not be read. Nothing from it has been used.* |
| Validation could not run (as opposed to finding a problem) | *The check could not run. Nothing has changed.* Approval stays unavailable |
| Approval or version creation fails | The previous live version stays live, and the operator is told so plainly. Nothing half-applies |
| Suspend fails | *Suspend did not apply. The Agent is still live.* Retry is offered |
| An interaction is still in progress (waiting on the customer or an external system) | Shown as still in progress, never as resolved |
| An interaction record cannot be loaded | *This interaction could not be loaded.* |
| The mailbox disconnects after go-live | The Agent status line changes to *The mailbox is no longer connected. Customers cannot reach the Agent.* |
| Any platform error | *Something on our side failed.* plus a **reference code** the operator can quote, per NFR16's correlation identity *"reportable by a person who experienced a problem"* |

### Version and lifecycle states

A specification version moves `draft → validated → approved → live`. Promoted versions cannot be edited in place, and in-flight interactions keep the version they started on, reading the specification *"never live."*

> **This produces a wait the UI must explain, not spin on.** After an approved correction goes live, interactions already underway finish on the previous understanding. That is a state to describe in plain language at the approval moment. Its duration is unbounded and unmodelled upstream.

> **Upstream contract gap.** This lifecycle is the operator-visible need; the Spine does not model these states as an enum. Raise with architecture.

**Rollback is not designed.** The PRD's improve journey includes *"promote (or roll back)"* (FR26). No rollback action is specified here; it is recorded as Amendments item 16 rather than decided in UX.

### Timing

No latency budget, timeout, retry count or streaming decision exists anywhere upstream — the Spine defers latency as *"measured, not designed up front."* Consequently this document specifies *which* operations need a progress or pending treatment, and not their durations:

- **Validation suite** — blocking, duration unknown. Needs a genuine pending state, not a guessed estimate.
- **Material ingestion** — duration unknown. Needs progress and a distinct parse-failure state.
- **Builder turn** — plausibly seconds, not sub-second. Needs a thinking state.
- **Propagation after go-live** — unbounded. Explained in words, never a spinner.

---

## Interaction Primitives

- **Correction is conversational; confirmation is exact.** The operator states a correction in their own words. The system responds with a precise, bounded before/after. Natural language in, verified change out. This pairing is the product.
- **One mechanism, many entry points.** Every correction — from a specification section, a divergence item, or an interaction — opens the same conversation with the origin as context. Never a second workflow.
- **Context travels; selection does not edit.** Opening the conversation from an item scopes the correction without granting any edit affordance over that item.
- **Nothing is live until the mailbox is connected.** Connecting the mailbox is the go-live act and the only moment the Agent becomes reachable by customers. It is never a prerequisite for authoring or validation.
- **No destructive action without a visible, bounded blast radius.** The diff's "also affected" and "unchanged" lists exist for this.
- **Motion communicates state only** — processing, progress, transition. No decorative animation. Calm, not flashy.
- **The operator is never asked to understand the architecture.** No surface may require knowledge of agents as a category, prompts, graphs, tools, retrieval, policies or model configuration.

---

## Accessibility Floor

Behavioural requirements. Contrast and other visual requirements live in DESIGN.md.

Treated as a real requirement, not polish. Target **WCAG 2.2 AA**.

- **Never colour alone.** Every item state, every divergence class and every degraded state carries a text label. The three divergence classes are different *kinds*, and the distinction must survive both monochrome rendering and colour-vision deficiency.
- **Keyboard-complete.** Every flow — conversation, review, correction, diff confirmation, approval, suspend — is operable by keyboard alone, with a visible focus indicator throughout and no keyboard trap.
- **Understanding is a document to assistive technology too.** Real heading structure for the five sections, in reading order. Item states exposed as text, not as decoration. A screen reader user must be able to navigate section to section and reach every "Not established" item.
- **Live Understanding updates are announced politely.** Content arriving beside an active conversation is announced without stealing focus and without interrupting the operator mid-sentence. Focus never jumps to newly-arrived understanding.
- **The diff is readable sequentially.** Before, after, also-affected and unchanged are comprehensible read linearly, not only by visual comparison. Changes are not conveyed by position or colour alone.
- **Motion respects `prefers-reduced-motion`.** All state-communicating motion has a static equivalent that conveys the same state.
- **Targets and reach.** Mobile Activity, interaction viewer and suspend meet AA target sizing. Suspend is reachable without precision.
- **Suspend is never behind a gesture, a hover or a long-press.** The emergency brake is a plain, labelled, keyboard-reachable action.
- **Errors are identified in text** and describe what to do, in the closed vocabulary.
- **Focus is always visible and never hidden.** The focus indicator is defined in DESIGN.md (Components · Focus indicator). Sticky pane headings, the sticky mobile top bar and the pinned conversation input reserve their height with scroll padding, so a focused element is never fully covered (WCAG 2.4.11).
- **Panes are labelled regions.** Each independently scrollable pane is a named region whose pane heading is a real heading. Each pane can be reached and scrolled by keyboard. Moving focus between panes is possible without passing through every item in the other pane.
- **Collapsible sections are disclosure buttons.** Each Understanding section heading contains a button that reports whether it is expanded. A collapsed section's accessible name includes which of Not established, Changed and Affected by this change it contains, so nothing is hidden from assistive technology. Following a link to an item inside a collapsed section expands that section and moves focus to the item.
- **Status messages are announced without moving focus** (WCAG 4.1.3) for: a Builder reply arriving, new Understanding content, the diff becoming ready, validation pending and its result, material finished or failed, suspend applied or failed, and resume applied.
- **Focus returns to where the operator came from.** Closing the interaction viewer returns focus to its Activity item. Accepting or pushing back on a diff returns focus to the conversation input.
- **Target sizes.** Every target is at least 24 by 24 CSS px (WCAG 2.5.8). Suspend, Stop actions only, and every primary and secondary action are at least 44 px tall.
- **Reflow and text size.** Every surface works at 320 CSS px wide without horizontal scrolling, in either orientation, and with text enlarged to 200%.
- **Signing in and connecting the mailbox** must not depend on a cognitive function test such as recalling or transcribing a code without assistance (WCAG 3.3.8), whichever mechanism the upstream contract chooses.
- **The escalation email is accessible as email** — meaningful plain-text alternative, readable without images or CSS, no meaning carried by colour.

---

## Responsive & Platform

| Surface | Desktop | Mobile |
|---|---|---|
| Cold start, conversation | Full | Not supported in V1 |
| Understanding | Full, co-present with conversation | **Read-only.** Sections collapse to a single column, reading order preserved |
| Correction diff, validation, approval | Full | Not supported in V1 |
| Connect mailbox | Full | Not supported in V1 |
| Activity | Full | **Full fidelity** |
| Interaction viewer | Full | **Full fidelity** |
| Suspend | Full | **Full fidelity** |

The split is deliberate: authoring and approval are deliberate sit-down work, while finding out something went wrong and stopping it are *"I am on the floor and something needs me"* work. The Product Brief describes this operator as *"one events manager often on the floor"*, *"one horticulturist"*, with the rules living partly in the owner's head.

On mobile, Understanding is readable but not correctable; the correction conversation is a desktop act. No horizontal page scroll at phone width.

### Application layout

Reference: [mockups/key-hero.html](mockups/key-hero.html) (Build panes), [mockups/key-activity.html](mockups/key-activity.html) (Run panes, desktop and phone).

The key-screen mocks stack several states into one long page because they are static HTML. **That stacking is not the target layout.** The application keeps Ledger's document-like visual language and organises it into panes.

- **Build, desktop.** Two panes side by side, each **independently scrollable**, each with a clear, persistent pane heading: **Conversation** and **What the Builder currently understands**. Scrolling one never moves the other. The conversation's input stays in view.
- **Understanding sections are collapsible.** The operator can collapse any of the five sections. A collapsed section still shows, beside its heading, whether it contains anything **Not established**, **Changed** or **Affected by this change**, so collapsing never hides an absence or a pending change. No section is collapsed by default on first view. The collapse control is identical on all five sections and carries no order, number or progress.
- **Correction diff.** Opens in the Conversation pane, beside Understanding, so the operator sees the change and the document it changes at the same time. Affected items in Understanding are marked while the diff is open.
- **Run, desktop.** Activity is a list pane, with the open interaction in a detail pane beside it. Each scrolls independently.
- **Run, mobile.** Activity is a full-screen list. Opening an item replaces it with the interaction full-screen, with a plain back action. Suspend is reachable from both without scrolling to find it.
- **One state per screen.** The application shows the current state of a surface, not a gallery of states.

**Density is a real refinement item, not only a mock artifact.** Ledger is roomy by design (17px body, 1.75 line height, long measure). That is what makes Understanding read as a document, and it also costs space in daily and weekly use. Panes and collapsing recover much of it; whether the type scale itself tightens for working surfaces is left open in DESIGN.md.

---

## The Escalation Email

**A designed surface with no screen**, and plausibly the most-read string in the product.

Escalation is delivered as an email to an address the operator declares (FR103; one address, required for operability). The escalation **inbox is out of V1 by decision** (§7.2), so the operator's entire experience of an escalation happens in their own email client. The email must therefore be actionable without logging in.

It must let the operator understand:

1. **What request triggered this** — the customer and what they asked for.
2. **Why the Agent could not safely resolve it** — in business language. *"Handed to a human, with why."*
3. **The relevant business context and evidence** — what the Agent established, and under what authority.
4. **What, if anything, the human needs to do.**
5. **A link to the interaction**, which FR103 requires (*"carrying the escalation reason class and a link to the episode"*). The email is actionable without following it. Following the link requires the operator to be signed in; a signed-out operator signs in and then lands on that interaction.

Written in the product voice, in the closed vocabulary, with no vertical framing and no technical terms. An escalation is *"a success and not a failure"*, and the email must not read as an error report or an apology.

**Amendment, flagged:** this email path may also carry a **material** divergence when one genuinely requires operator attention. No new notification system, digest, inbox or dashboard is built. See Amendments.

**Materiality is not a UX concern.** What makes a divergence material is an upstream system attention-policy decision. This document defines **how a material divergence is surfaced**, not how materiality is calculated. No severity score, threshold control, priority ranking or new classification model is introduced here to support the amendment, and none may be added downstream in its name.

---

## Key Flows

Role titles only, per PRD §2: *"A role archetype, deliberately not a named persona… inventing a persona would manufacture confidence the research does not support."* The Product Brief confirms no operator has yet been interviewed. The four exemplar businesses below are narrative scenarios; any first name is an obvious fictional device, never a research finding.

### Flow 1 — Cold start to first live version

An operator at a **garden centre** has been handed a workspace. No funnel, no welcome screen, no templates, no "step 1 of 5."

1. The first surface is the workspace itself, framed lightly in place: *"Tell me about your business and the customer requests you want me to handle."* Material may be added here as optional supporting context.
2. They describe the business in their own words. Beside the conversation, **Understanding begins to form** — framed as what the Builder currently understands, not as a live specification.
3. The Builder asks follow-ups where it detects ambiguity or missing business behaviour: how requests are normally handled, the exceptions, the thresholds, what staff may not do, what needs confirmation, what escalates, and where written policy and actual practice diverge.
4. They add their price list and planting guides. Provenance is shown; where sources conflict, precedence is established rather than assumed.
5. **Not established** items remain visible across all five sections. They pull the conversation forward. They are not a checklist and there is no completion target.
6. The operator reads Understanding as a document and corrects it conversationally, using the same correction mechanism that later serves divergences. The mechanism is reusable and belongs to no single flow.
7. **Climax.** The operator sees a coherent representation of how their business actually works — including its boundaries — and recognises it as accurate enough to approve.

   The beat is **recognition of the whole**, not arrival at any particular section. The five groups are document hierarchy, never stages, and nothing in this flow may be built as though reaching the last of them were a milestone.
8. They ask to go live. The blocking validation suite runs, and its result is shown at the approval moment.
9. They approve the specification version. No celebration.
10. **They connect the mailbox.** Only now is the Agent reachable by a customer. Before this moment it was being authored and reviewed; after it, it is working.

**When it goes wrong.** Material that cannot be read is listed as such and nothing from it is used. A failed Builder turn keeps the operator's words for resending. A blocking finding keeps approval unavailable and points at the part of Understanding concerned; it is resolved in conversation. If the check cannot run, nothing changes. If the mailbox cannot be connected, the Agent stays not live and says so.

### Flow 2 — Divergence to a new live version

The canonical correction loop, authored by the operator. A **brewery**.

1. In **Activity**, the operator sees that a customer was told they could book a private event for forty people on a Saturday evening.
2. They open the item and read the **interaction**.
3. The interaction shows the customer's email, the Agent's yes, and what the reply was based on: the private-events rule and the venue material. The Agent had what it needed and concluded the request was permitted. **No platform error. No escalation.** The business simply does not allow private events during Saturday evening service.
4. They open the correction conversation **directly from that interaction** with **This was wrong**, and say it plainly:
   > *"We don't take private events on Saturday evenings. Those hours are always regular service, even when we have capacity."*
5. The Builder presents the exact proposed change:

   **Before** — *Private events may be accepted when capacity and availability allow.*

   **After** — *Private events may be accepted when capacity and availability allow, except during Saturday evening service.*

   Then **what else is affected** (the event-booking rule, and what good looks like here for event requests) and what is **unchanged**.
6. The operator confirms.
7. A new specification version is produced. The blocking validation runs. The operator approves.
8. **Climax.** Resolution is **not** the moment the Builder says *"got it."* It is the moment the operator sees the exact behavioural change, sees its impact, confirms it, and a new validated live version exists. The beat to design for:
   > **"Yes. That is exactly the rule I meant, and I can see what changed."**
9. The approval moment states, in plain language, that conversations already underway will finish on the previous understanding.

**When it goes wrong.** If the Builder's proposed change is not what they meant, they push back and the conversation continues; nothing changes until they accept. If validation blocks the new version, the previous version stays live. If version creation fails, the previous version stays live and the operator is told.

### Flow 3 — Permitted, confident, and wrong

The flow where the thesis lives, and the one no detector can start. A **dental practice**.

1. Nothing was denied. No rule refused. No platform fault. The Agent was permitted, confident, and wrong.
2. The operator reads an interaction and recognises it: *that is not how we work.*
3. They use **This was wrong** on the interaction, which opens the **same** correction mechanism with the interaction as context. There is no second workflow.
4. **Climax.** The correction is recorded as a divergence the system could not have found on its own (FR102 / FR108). This is the path by which the human remains the ultimate judge of whether the Agent is behaving like someone who works in that business — and it is the reason the interaction viewer exists at all.

**When it goes wrong.** If the interaction cannot be loaded, the operator is told so, and the Activity item stays in place to try again.

### Flow 4 — An escalation arrives

A **gym**. Almost entirely outside the product.

1. A request reaches the end of the Agent's authority — what this business will not let an Agent decide.
2. The Agent hands it to a human **with why**, and does not improvise. An escalation here is a success, not a failure.
3. An **email arrives** at the declared address. See The Escalation Email.
4. **Climax.** The operator handles it as a human, in their own email client, without logging in. The product's only job in this flow is that the email was good enough to act on.

**When it goes wrong.** An escalation needs a declared address to go anywhere; FR103 makes one required for operability, and where in the flow it is declared is Open Question 4. A bounced or undeliverable escalation email is unspecified upstream (Amendments item 19).

### Flow 5 — Suspend

1. Something is wrong and the operator wants it to stop now. They may be on their phone.
2. They press **Suspend**: one press stops the Agent replying and acting. If they only want it to stop acting while it keeps answering, they press **Stop actions only** instead.
3. **Climax.** It stops. The status line says so in words, the change is announced, and **Let the Agent act again** is available.
4. The correction that follows goes through the same correction loop as any other.

**When it goes wrong.** If suspension does not apply, the operator is told *"Suspend did not apply. The Agent is still live."* and can try again. It never fails silently.

---

## Inspiration & Anti-patterns

### What this must not feel like

Stated by the operator, and reinforced by the sources:

> a workflow editor · a node or graph builder · a developer IDE · a giant configuration form · a generic "chat with your documents" product · an automation platform · a BPMN editor · an AI playground for developers · a CRM · a generic chatbot builder

### Prohibitions carried from the sources

| Forbidden | Source |
|---|---|
| Any affordance for expressing sequence, order or branching | §1.1, FR18 — *"must make sequencing unexpressible"* |
| A form, a fixed question set, or a questionnaire in elicitation | FR1, FR3 |
| An in-product specification editor | FR101, §7.2 |
| A metrics dashboard | §7.2, §13.2 |
| An escalation inbox | §7.2 |
| Any outbound or proactive affordance — campaign, follow-up, nudge, "send" | AD-22, §4.4 |
| A customer profile or memory screen | §4.4 — *"no general long-term customer memory, no cross-episode profiling"* |
| A system-of-record framing | FR36, §4.4 — external business systems stay authoritative |
| Any vertical framing — booking, appointment, healthcare, sales, FAQ | §4.4 |
| Reading the episode step sequence as a permitted order | Architecture Spine |
| A publish-anyway override on the validation gate | FR22, FR25 |
| Editing a promoted version in place | Architecture Spine |
| Vertical starter templates | Product decision, V1 |

### The lesson that outranks the rest

From the brownfield record, AD2: *"the verification had checked the mode **label**, not a completion."* A surface that reassures without verifying anything is worse than no surface. This is the reason V1 ships **no operator-facing test playground**: confidence comes from the blocking validation suite and from the correction loop, not from a sandbox that would let an operator feel certain on no evidence.

### The thesis, expressed indirectly

> **Reasoning is broad; authority is bounded.**

This is never stated as a technical concept. It is experienced: the operator gives business context, knowledge, rules, capabilities and boundaries, and receives an Agent that behaves like someone who works in that business. The product's job, per the Product Brief, is *"not to measure conversational quality objectively… but to make disagreement cheap to express and fast to propagate."*

---

## Amendments and Upstream Gaps

Raise each with the owning document before implementation.

| # | Item | Against | Status |
|---|---|---|---|
| 1 | **A material divergence may ride the existing declared escalation email path when it requires operator attention.** That is the whole of it. PRD §13.2 states *"there is no alerting."* Explicitly **not** authorised by this amendment: a generic notification system, a divergence-alerts product, an inbox, a digest, or any notification framework. Materiality itself is an upstream attention-policy decision, not a UX one. | PRD §13.2 | **Explicit amendment.** A product decision taken in this UX discussion, not a reading of the existing PRD. |
| 2 | **Email / inbound messaging as the V1 channel.** | PRD FR84 | **Sourced.** FR84 ships one inbound email / messaging adapter. An earlier draft wrongly called this a UX-originated decision; the decision is unchanged. |
| 3 | **Connect-your-mailbox surface.** Required for operability; no upstream source describes it. Provider, authorisation model and what the operator sees are all unspecified. | PRD silent | **Originated here.** Needs a source owner. |
| 4 | **Persistent suspended state.** FR110 gives a one-action suspend; the Spine models no suspended state and no agent status enum. | Architecture Spine | **Contract gap.** Not invented here. |
| 5 | **Specification version lifecycle** as operator-visible states. | Architecture Spine | **Contract gap.** |
| 6 | **Specification field schema.** EX1–EX17 are named; nothing below them is. Deferred to epic E1. | PRD O7 | **Deferred upstream.** This document specifies behaviour, not fields. |
| 7 | **The approval act's relationship to validity.** O1: *"no reviewer role or review verdict is defined anywhere in the sources."* Resolved here as: the operator is the approver, and approval does not determine validity. | PRD O1 | **Resolved here.** Confirm upstream. |
| 8 | **Counterfactual replay (O11)** — re-running a closed interaction against a later version. Undecided for V1 and not designed here. | PRD O11 | **Open upstream.** |
| 9 | **Latency, timeouts, streaming.** No budget or decision exists; the Spine defers them as *"measured, not designed up front."* Pending states are specified here without durations. | Architecture Spine | **Deferred upstream.** |
| 10 | **Material intake limits** — accepted formats, size, ingestion duration, failure taxonomy. | PRD silent | **Open.** |
| 11 | **Divergence item fields.** Not specified upstream. | PRD silent | **Resolved for V1** as the minimum in Component Patterns: class, interaction label, one-line request. No severity, retry eligibility, metrics or filters. Grouping repeated occurrences of one problem remains open. |
| 12 | **Linking a reply to the specification item it relied on.** The interaction viewer quotes the parts of the specification a reply was based on. The Spine records provenance for *sources* as `(tenant, source, source version, locator)`. Whether *specification items* are addressable the same way, and recorded per decision, is unconfirmed. | Architecture Spine | **Contract gap.** Without it the viewer can quote source material but not the specification rule. |
| 13 | **Validation result shape.** The UI lists blocking and non-blocking findings, each pointing at the part of Understanding it concerns. No contract defines a finding's fields or its link to a specification area. | PRD FR22 / FR95 | **Contract gap.** |
| 14 | **Email subject and received time in the interaction record.** The interaction label uses them. The Spine lists channel identity as not stored; whether the subject survives into the record is unconfirmed. | Architecture Spine | **Contract gap.** The deterministic fallback still needs the received time. |
| 15 | **Judging sampled refusals** (FR115): who decides that a sampled refusal was wrong, and on which surface. No surface is designed for it in V1. | PRD FR115 | **Gap.** Divergences from this source appear in Activity once judged; the judging act is unplaced. |
| 16 | **Rollback** (FR26: *"promote (or roll back)"*). No rollback action is designed. | PRD FR26 | **Gap.** Not decided here. |
| 17 | **Platform error reference.** The UI shows a reference code with every platform error, per NFR16. Its format and how it reaches the UI are unspecified. | PRD NFR16 | **Contract gap.** |
| 18 | **Mailbox connection status after go-live**, including disconnection, for the Agent status line. | Architecture Spine | **Contract gap.** Related to items 3 and 4. |
| 19 | **Undeliverable escalation email.** What happens, and what the operator sees, when the escalation email bounces. | PRD FR103 / FR114 | **Gap.** |

---

## Open Questions

1. Does the Builder conversation stream its response, and does Understanding update per turn or on a grounding threshold? No upstream streaming decision exists.
2. ~~What composes an interaction's label?~~ **Resolved:** email subject plus received date and time, with the deterministic fallback "Customer email · {received date and time}". No generated summaries. Depends on Amendments item 14.
3. How is a **material** divergence distinguished from an ordinary one for the purposes of Amendment 1? **Deliberately left open.** This is an upstream system attention-policy question, and the threshold should not be guessed or approximated with a UX control. The UX defines surfacing only.
4. Does the operator declare the escalation address during authoring, or at mailbox connection? It is *required for operability* but unplaced in the flow.
5. Three Product Brief research questions remain unanswered and bear directly on this design, most sharply: *"how would you know the Agent did a bad job?"* If operators cannot answer it, Activity has no customer-side signal to surface. No operator has been interviewed.
