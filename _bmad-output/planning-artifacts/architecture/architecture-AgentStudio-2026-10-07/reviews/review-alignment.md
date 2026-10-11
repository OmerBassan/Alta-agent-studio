# Alignment Review — ARCHITECTURE-SPINE.md vs. the seven settled commitments

**Scope:** the spine document only (`ARCHITECTURE-SPINE.md`, 2026-10-08 draft). No repository code, no git diff, was consulted — the existing LangGraph system is treated as the reference implementation the spine itself names, nothing more.

---

## Verdict

**Directionally conformant and unusually disciplined — but four mechanisms (guard pre-emption, platform-owned escalation, business-configurable guard conditions, and post-refusal control) leave the Core holding next-step authority under non-orchestration vocabulary, and must be closed with explicit outcome vocabularies rather than new structure.**

---

## Conformance table

| # | Commitment | Result |
| --- | --- | --- |
| 1 | Model-in-charge Agent | **PARTLY UPHOLDS** — escalation is assigned to both the Agent and the platform guardrail set |
| 2 | Core constrains, validates, authorizes, executes, observes, persists — does not choose the next step | **PARTLY UPHOLDS** — "guard checks … may pre-empt it" is an unbounded Core-side decision; post-refusal control is unassigned |
| 3 | No business-specific workflow or state machine | **PARTLY UPHOLDS** — business-configurable guard conditions + confirmation requirements are a re-entry vector for precondition-derived orchestration |
| 4 | No novel orchestration mechanism | **PARTLY UPHOLDS** — inline resolution validation is correctly flagged as our own extension in `Deferred`, but presented as settled Core behaviour in two other sections |
| 5 | Specification provides context/policy, not control flow | **PARTLY UPHOLDS** — no rule prohibits ordering constructs in the specification schema; "confirmation requirements" is latent sequence |
| 6 | Provider agnosticism as an architectural boundary | **UPHOLDS** |
| 7 | Durability is infrastructure, not control architecture | **PARTLY UPHOLDS** — AD-12's durable-step decomposition is unqualified as to what step boundaries may *not* be used for |

---

## Findings by severity

### MAJOR-1 — "Guard checks … may pre-empt it" gives the Core unbounded next-step authority (violates 2, weakens 1)

**Spine text (Runtime Interaction):**

> "Guard checks run before the Agent turn and may pre-empt it. Resolution validation runs when the Agent claims an episode is finished: a claimed outcome unsupported by evidence is refused. **Neither mechanism chooses the Agent's next step.**"

The disclaimer is asserted, not established. *Pre-empting a turn* **is** a decision about what happens next: the Core determines that the next thing is not an Agent decision. The sentence after it refutes the sentence before it. The spine nowhere says what a pre-empted turn produces — a canned reply, a refusal handed back to the Agent, an escalation, a closed episode? A builder implementing "may pre-empt" will reasonably write a branch that emits a business-visible response without the model ever reasoning, which is exactly deterministic next-step selection wearing a guardrail's name.

AD-1 provides the right test but never applies it to its own guard mechanism:

> "Before adding any mechanism, apply the test: *does this constrain the Agent, or decide its next step?*"

**Minimal fix.** Replace "may pre-empt it" with a closed outcome vocabulary, as a rule under AD-1 or a new AD:

> A guard has exactly three permitted outcomes: **pass** (the Agent turn proceeds), **annotate** (a typed constraint note is added to the Agent's context and the turn proceeds), or **halt** (the episode stops and is handed to the declared human escalation path, with evidence). A guard may never select, substitute or author a business action, a reply, or a capability invocation. Content-level refusal is returned to the Agent as a typed result; the Agent decides what follows.

This keeps input guardrails (an established harness pattern, so commitment 4 stays satisfied) while removing the discretionary branch.

---

### MAJOR-2 — Escalation is assigned to the Agent and to the platform simultaneously (violates 1, weakens 2)

**Spine text (Delegated column, *Deterministic vs Delegated*):**

> "Whether to act, continue, respond or escalate"

**Spine text (Platform-owned invariant, *Platform-Owned vs Business-Configurable*):**

> "The generic guardrail set: … **escalate when required authority or evidence is unavailable**"

and, in the same table's business-configurable column:

> "Escalation conditions"

Three statements, two owners. If the platform escalates when authority or evidence is unavailable, and businesses declare the conditions under which that happens, then a business-declared predicate evaluated by the Core determines the episode's next step — the precise shape commitment 3 rejects ("precondition-derived orchestration standing in for agent decision-making"). If instead the guardrail is a *prompt-level instruction to the Agent*, then it sits in the specification's advisory layer and AD-3 makes it non-binding, which the table does not say.

Note the aggravating ambiguity: the other four generic guardrails ("do not invent business facts", "do not act outside declared authority", "do not perform undeclared actions", "do not claim success without evidence") are all **prohibitions**, enforceable as refusals. The fifth is an **obligation to act** — categorically different, and the only one in the set that cannot be enforced by denying something.

**Minimal fix.** Split the set explicitly:

> **Enforced prohibitions (Core):** do not act outside declared authority · do not perform undeclared actions · do not claim success without evidence · business-authoritative claims must carry a resolving citation.
> **Advisory directive (specification → Agent, non-binding per AD-3):** escalate when required authority or evidence is unavailable.
> The Core never initiates escalation on a business predicate. Its only unilateral terminal transition is the safety halt of MAJOR-1 (guard halt, or the loop bound of MINOR-3), which routes to the human escalation path and never to a business outcome.

---

### MAJOR-3 — Business-configurable guard conditions are a workflow smuggling route (weakens 3 and 5)

**Spine text (*Platform-Owned vs Business-Configurable*):**

| Platform-owned | Business-configurable |
| --- | --- |
| "Guard mechanism" | "**Which guard conditions apply**" |
| "Authorization enforcement" | "Authority boundaries, **confirmation requirements**" |

Taken with MAJOR-1's pre-emption, a business can declare a set of conditions that pre-empt Agent turns — an onboarding-time, business-specific, condition→action table. That is a state machine written in a different schema. "Confirmation requirements" is the same risk one level down: a requirement that action B be preceded by confirmation A is an *ordering* constraint on the business's control flow, and commitment 5 forbids the specification encoding "A then B then C".

Both are legitimate as **authorization preconditions**; neither is legitimate as **injected sequence**. The difference is entirely in who acts when the precondition is unmet: if the Core refuses and the Agent decides how to proceed, it is a constraint; if the Core inserts the confirmation step, it is orchestration.

**Minimal fix.** Add one clause to AD-2 and mirror it in the table:

> A confirmation requirement is an authority precondition on an action contract, not a step the Core performs. When it is unmet, the Core denies the action with a typed reason naming the missing confirmation and returns it to the Agent. The Core never asks the confirming question, never queues a follow-up action, and never resumes the denied action automatically. Guard conditions are expressible only over episode-invariant facts (specification version, authority grants, episode state, configured limits) — never over business progress, prior actions taken, or unmet business preconditions.

---

### MAJOR-4 — Inline resolution validation appears settled in two sections and provisional in a third (weakens 4)

**Spine text (*Deferred*):**

> "Inline resolution validation as a shipped mechanism | Assertion-based evaluation is standard offline; **enforcing it inline at episode close is our own extension** and is to be validated by the proof gate before being relied upon"

**Spine text (*Deterministic vs Delegated*, Deterministic/Core column, unqualified):**

> "Resolution validation against evidence"

**Spine text (sequence diagram, unqualified):**

> `A->>C: close episode with claimed resolution` / `C->>C: validate resolution against evidence`

The honest acknowledgement in `Deferred` is exactly right for commitment 4 — a self-admitted novel mechanism, gated on a concrete requirement and a proof. But a builder reading the diagram and the Deterministic column will implement it as a committed invariant. Worse, the deferral row does not say what the fallback is if the proof gate rejects it, so there is no defined behaviour for episode close in that branch.

**Minimal fix.** Mark both the diagram step and the table row *(provisional — see Deferred)*, and add to the deferral row: "If the proof gate does not validate inline enforcement, resolution claims are recorded as claims, validated offline against evidence, and surfaced as an evaluation signal; episode close is never blocked."

Related, same commitment: AD-6 is the strong, non-novel half of this and should be cited as the invariant that survives either outcome —

> "Only the Core's execution record may attest that an effect occurred. The Agent cannot author evidence."

---

### MAJOR-5 — Nothing forbids ordering constructs in the specification schema (weakens 5)

AD-1 forbids the **Core** from carrying a workflow. AD-4 governs projection. AD-15 forbids business config changing Core semantics. No rule forbids the **specification artifact** from containing ordering. The spine's protection is indirect — a reader must infer it from AD-1's list of rejected mechanisms, all of which are phrased as Core properties.

**Spine text (AD-4), the nearest thing:**

> "The agent's context, the tool surface offered to the model, and the policy the Core enforces are all **projections compiled from one specification artifact**."

If the one artifact may express sequence, all three projections inherit it, including the Agent's context — where it arrives as prose instructions and is therefore *invisible* to any Core-side audit. This is the quietest available re-entry path for a workflow, and the spine has no guard on it.

**Minimal fix.** Add a rule under AD-4 (or a new AD-17):

> The specification has no ordering constructs. No step lists, no sequences, no next-step or transition fields, no conditional chains, no "then". A specification field whose semantics are "what happens after X" is a schema defect, rejected at Builder validation, in the prose-authored business-context sections as well as the structured ones. The specification declares context, policies, authorities, capability grants and outcome expectations — the Agent derives order.

The Builder-side check is what makes this real; without a validation rule the prohibition is advisory.

---

### MINOR-1 — AD-12's durable-step decomposition is unqualified as to what it may not be used for (weakens 7)

**Spine text (AD-12):**

> "Clock, randomness, identifiers, environment and configuration are obtained through recorded steps or pinned at episode start. **Each model decision, each authorized execution and each evidence write is a durable step.**"

Substantively this is infrastructure discipline and commitment 7 survives — the `Deferred` row is exemplary ("Semantics are fixed … Smallest proven infrastructure that satisfies them wins; the fallback floor is Postgres tables with a unique constraint"). The residual risk is vocabulary: once "step" is a first-class durable object with a shortlisted engine (DBOS) whose programming model expresses *workflows* as composed steps, the step graph is one refactor away from being read as a control graph.

**Minimal fix.** One sentence appended to AD-12:

> Step boundaries are units of recording and recovery only. No step boundary, retry policy, or durability-framework control primitive (workflow composition, step sequencing, compensation ordering) may appear in, or determine, an Agent or Core decision path. Replay reproduces decisions; it never makes them.

---

### MINOR-2 — "Which knowledge sources are authoritative, and precedence" (watch item, 3)

**Spine text (*Platform-Owned vs Business-Configurable*):**

> "Retrieval mechanism | Which knowledge sources are **authoritative, and precedence**"

Legitimate as written — commitment 3 rejects a "universal primitive precedence table", and this is source-conflict resolution for grounding, a different object. Flagged only because the word "precedence" is the rejected mechanism's word, and AD-7's enforced tier gives it teeth. Scope it in place: "precedence resolves conflicts between sources for the same fact; it has no bearing on action selection or ordering."

---

### MINOR-3 — No termination bound on the agent loop, and no named writer for `pending` (blurs 1/2)

**Spine text (AD-13):**

> "One episode has one identity, one lifecycle (`active` / `pending` awaiting a named external input / `closed`)"

The spine never says who transitions an episode to `pending`, nor what bounds the Agent's loop within a turn. Both gaps will be filled by whoever implements first, and the natural implementation — the Core inspecting state and deciding to park the episode — lands in the forbidden category. Minimal fix: "The Agent requests `pending` by naming the external input it awaits; the Core validates that the named input is one a declared capability can deliver and records the transition. The Core transitions an episode unilaterally only on a guard halt or on the configured per-turn decision bound, both of which route to human escalation, never to a business outcome."

---

### MINOR-4 — The runtime diagram shows one action per turn (documentation clarity, 1)

The sequence diagram runs `A->>C: action request` → `C->>A: result or denial` → `A->>C: close episode`, with no loop frame. Read literally it depicts a single-action turn, which understates agent-in-charge iteration and invites a builder to implement a fixed one-tool-per-turn pass. Wrap the request/authorize/execute/result block in a `loop` frame labelled "until the Agent decides to respond, escalate, or close — bounded per MINOR-3".

---

## The specific hunt: does each mechanism constrain, or decide?

Applying AD-1's own test to every mechanism the spine defines.

| Mechanism | Constrains | Decides next step | Assessment |
| --- | --- | --- | --- |
| Contract validation (AD-2) | yes | no | Clean. Refusal is a typed result. |
| Authorization against specification authorities (AD-2) | yes | no | Clean — **provided** denial returns to the Agent (MAJOR-3). |
| Guard checks, pass/annotate | yes | no | Clean. |
| Guard checks, **pre-empt** | — | **yes** | **Violation — MAJOR-1.** |
| Business-configurable **guard conditions** | yes, if invariant-scoped | **yes, if progress-scoped** | **At risk — MAJOR-3.** |
| **Confirmation requirements** | yes, as precondition | **yes, if Core performs the confirmation** | **At risk — MAJOR-3.** |
| Platform escalation obligation | — | **yes** | **Violation — MAJOR-2.** |
| Citation-span resolution (AD-7) | yes | no | Exemplary. Rejects content; never redirects. Honest about the semantic tier being thresholded, not guaranteed. |
| Retrieval via Core (AD-8) | yes | no | Exemplary — "The Agent decides *when* to retrieve; it never retrieves directly." |
| Evidence production (AD-6) | yes | no | Clean. Observation only. |
| Resolution validation against evidence | yes | **ambiguous** — what follows refusal is unassigned | **At risk — MAJOR-1/MAJOR-4.** |
| Authorization-divergence logging (AD-5) | no (it observes) | no | Clean, and a good instinct: divergence is a *signal*, not a correction. |
| Specification projections (AD-4) | yes | **only if the artifact may express order** | **At risk — MAJOR-5.** |
| Episode lifecycle (AD-13) | yes | **ambiguous** — `pending` writer unnamed | **At risk — MINOR-3.** |
| Idempotency keys (AD-10) | yes | no | Clean. |
| Durable steps (AD-12) | yes | no, as written | Clean; needs the fence of MINOR-1. |
| Runtime boundary (AD-14) | yes | no | Clean. |

**Pattern across the failures:** every one of them is a mechanism whose *rejection path is undefined*. Where the spine says what a refusal returns and to whom, it is airtight. Where it says a check "may pre-empt", "requires", or "escalates" without naming the recipient of control afterwards, next-step authority silently defaults to the Core. The single highest-value edit to this document is a global rule: **every Core mechanism must declare its outcome vocabulary, and every outcome other than a safety halt must return control to the Agent as a typed result.** That one sentence closes MAJOR-1, MAJOR-2, MAJOR-3 and the ambiguous half of MAJOR-4 at once.

---

## Can a builder tell "enforces a rule" from "decides what happens next"?

**Mostly yes — the spine is far clearer on this than most documents of its kind.** AD-1's test, AD-2's "on the critical path for every effect and on the critical path for no decision", the Deterministic vs Delegated table, and the closing litmus test together give a builder a usable discriminator, and the Delegated column is correctly populated with judgement ("what the person is trying to accomplish", "how to handle a situation nobody enumerated") rather than mechanics.

**The line is blurry in exactly five places:**

1. **"may pre-empt it"** (Runtime Interaction) — the single blurriest phrase in the document. A builder cannot tell whether a pre-empted turn yields a refusal to the Agent or a Core-authored reply to the customer.
2. **"escalate when required authority or evidence is unavailable"** as a platform-owned guardrail — reads as enforcement, behaves as a decision, and contradicts the Delegated column on the same page.
3. **What follows a refused resolution** — the Core refuses; the document stops. Does the episode reopen, does the Agent get another turn, is there a bound?
4. **"Confirmation requirements"** — indistinguishable from an injected step without the MAJOR-3 clause.
5. **The `pending` transition** — a lifecycle state with no named writer.

Four of the five are one-sentence fixes. None requires new structure, none requires the Core to take on any decision it does not already have, and none touches the settled direction: they narrow the Core's vocabulary rather than widening it. With MAJOR-1 through MAJOR-5 applied, the spine's answer to its own litmus test — *"can a new business be onboarded without generating a business-specific execution graph or state machine, while the Agent still reasons about situations nobody enumerated?"* — becomes defensible from the document alone rather than dependent on the implementer's good instincts.
