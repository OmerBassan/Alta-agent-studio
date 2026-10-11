# Agent Studio — Convergence Document

**Session:** brainstorm-agent-studio-product-architecture-2026-10-06
**Source of record:** `.memlog.md` (91 time-ordered entries; techniques run in order: Job to Be Done → Assumption Reversal → Morphological Analysis → TRIZ Contradiction)
**Status of this document:** input to a Product Brief. It is not a spec, not a roadmap, and not a refactor plan.

### Label discipline

Every load-bearing claim below carries exactly one label. The distinction was a session rule and is preserved deliberately.

| Label | Meaning |
|---|---|
| **FACT** | Verified by reading the repository (this session or the brainstorming session; several cite file:line) |
| **INTERPRETATION** | An architectural reading of those facts — defensible, not proven |
| **HYPOTHESIS** | A product bet. Unproven. May be wrong. |
| **DECIDED** | Actually settled during the session, by the owner |

No HYPOTHESIS in this document is to be read as a DECIDED. Where a line of reasoning is strong but unvalidated it is labelled **STRONG DIRECTION** and is explicitly *not* a decision.

---

## 1. Product thesis

What Agent Studio should currently be believed to be: **a system for turning one specific, repeatable, commercially valuable class of inbound text conversation into a reliable agent — where the conversation itself carries the intelligence (understanding the person, handling ambiguity, deciding what information is still missing, what to retrieve, when to act), the agent reasons against declared criteria, uses knowledge and a bounded set of tools, and either takes a narrow authorized action or routes the case correctly; and where every episode leaves durable evidence that feeds evaluation, human correction, and *deliberate, versioned, reviewable* changes to the agent's specification.** It is explicitly not an agent generator, not a generic workflow or process-automation platform, and not a system of record. The customer's existing systems stay authoritative; Agent Studio is the conversational intelligence and execution layer above them, joined to them by a key.

The class of conversation is still open. That is the single largest hole in the thesis and the reason this session converged rather than continued.

### Status table

| Element | Status |
|---|---|
| Text-first (not voice) | **DECIDED** |
| Inbound (not outbound) | **DECIDED** |
| Conversational agent as the interaction model | **DECIDED** |
| A narrow repeatable business job, not a generic agent platform | **STRONG DIRECTION** (not decided) |
| Configuration/specification as the primary variation mechanism | **STRONG DIRECTION** (not decided) |
| The specific first use case | **NOT DECIDED** |

Two supporting DECIDED items that constrain the above: sales-vs-non-sales remains open (it was explicitly left open when text-first/inbound were decided); and "shared execution architecture" was redefined to mean *a small set of stable primitives* (conversation state, structured decision/action, knowledge retrieval, bounded tools, policy, evaluation) rather than one rigid conversation workflow.

---

## 2. Candidate use cases

Three candidates, all inside the same family: *inbound text conversations that qualify a person or a request and move it to a concrete next state.* Shared pattern: understand → collect information → reason against criteria → use knowledge/tools → produce a structured disposition or execute the next action.

### 2.1 Comparison

| Dimension | C1 — Lead qualification | C2 — Service/request qualification | C3 — Appointment intake |
|---|---|---|---|
| **Buyer** | Sales / revenue leadership (mid-market) | Support, ops, service management (often enterprise) | Owner-operator or practice/clinic manager (SMB) |
| **Business value** | More qualified pipeline, less SDR time on unqualified volume | Faster triage, less human handling per request, consistency | Booked appointments that would otherwise be missed; direct revenue per booking |
| **Incumbent pressure** | CRM-adjacent tooling and a crowded SDR-automation market | **Highest**: Zendesk, Intercom, Freshdesk, ServiceNow all already ship inbound triage *and* own the system of record | Booking/scheduling software owns the calendar, but the inbound conversational front door is comparatively weakly served |
| **Conversational complexity** | **Adversarial / misaligned interests.** Needs probe → challenge uncertainty → verify → reconsider → qualify | Aligned interests. Agent can ask and be answered | Aligned interests. Agent can ask and be answered |
| **Action / tool requirements** | Mostly a structured disposition + CRM write | Create/route/update a ticket or case | **Transactional**: availability consistency, confirmation before side effect, idempotency, retries, double-booking races, multi-step transactions |
| **External system dependency** | CRM (lead/opportunity records) | Ticketing / ITSM — which the incumbent also owns | Calendar/booking system, sometimes practice-management software |
| **Evaluation observability** | **Worst.** False negatives are invisible: a wrongly disqualified good lead is gone and emits no signal | Good: disposition correctness and routing correctness are checkable; downstream resolution arrives from the ticketing system | **Best.** Failures surface within about a week: no-show, complaint, reschedule, double-booking |
| **Runtime-ownership implications (C2 contradiction severity)** | Mild — mid-market, some security review | **Maximum** — enterprise procurement, compliance, data residency, SSO; self-hosting pressure | **Near zero** — SMB, no VPC, no security review; hosted is a *feature*, not a concession |
| **Biggest architectural/product risk** | The adversarial loop refuses to be configuration: needs execution support for adaptive probing and uncertainty management, *and* a different evaluation architecture (see 2.3) | **Persistent case lifecycle**: unresolved requests across sessions, status changes pushed from the external system, proactive follow-up, continuing after human handoff — a durable case/entity state model plus event-driven lifecycle, not conversational memory | Transactional tool-execution layer with real semantics; the conversation stays configurable, the execution infrastructure gets meaningfully harder |
| **Biggest unresolved commercial question** | Will a revenue team trust an agent to *reject* leads at all, given that the cost of a false negative is invisible to them and to us? | Is there budget beside the incumbent that already owns the workflow *and* the data, for a cost-centre buyer? | Is the per-booking value high enough, and the conversation repeatable enough across businesses, to be configuration rather than per-customer work? |

### 2.2 Ranking — HYPOTHESIS, not a decision

Two rankings exist in the session and both are preserved.

**The owner's original ranking (HYPOTHESIS):** C2 service/request qualification > C3 appointment intake > C1 lead qualification. Rationale: the shared pattern is cleanest in C2; C1's adversarial nature and selection-biased evaluation make it a poor primary boilerplate; C3's transactional execution is real work. Thesis attached to it: *an inbound conversational agent that understands a person's request, gathers the information required to handle it, determines what should happen next, and either takes a bounded action or routes it correctly.*

The owner immediately challenged his own ranking: *is service/request qualification actually a sufficiently valuable product, or are we converging on it mainly because it fits our desired architecture?*

**Three independent strikes against C2** then landed, each from a different technique:

1. **Market / JTBD** — every plausible incumbent already ships inbound triage *and* owns the system of record. C2 sells into the tightest budget, against the party that owns the workflow.
2. **Buyer type** — support/ops is a **cost centre**. C3 and C1 sell to **revenue/profit centres**.
3. **C2 contradiction severity** — runtime-ownership demand is near zero for SMB appointment intake, mild for mid-market lead qual, maximum for enterprise support/ops. **The candidate ranked first maximises the hardest unresolved contradiction in the architecture; the candidate ranked second nearly dissolves it.**

**HYPOTHESIS (the leading one, explicitly unvalidated): the ranking is inverted at the top — appointment intake (C3) is the stronger first use case.** Why it leads:

- Its difficulty is **architectural and bounded** (transactional tool execution), not **product-shaped and open-ended** (persistent case lifecycle + event feeds + incumbent displacement).
- Its failures are **visible within days**, which is exactly what an evidence-driven improvement loop needs in order to function at all.
- Its buyer is a revenue centre and makes no runtime-ownership demand, so the C2 ownership contradiction (section 3) stays dormant in V1.
- The incumbent owns the *calendar*, not the *inbound conversation*; the join key into the calendar is a narrow, well-defined integration rather than a claim on the system of record.

What has **not** happened: no customer conversation, no pricing signal, no measurement of how much appointment-intake conversation varies between businesses, no validation that per-booking value supports a product. **Appointment intake has NOT been selected.** It is the current best bet pending the evidence in section 8.

### 2.3 Two findings that must survive regardless of which case is chosen

**The lead-qualification evaluation trap (INTERPRETATION, and it generalises).** In qualification, false negatives are invisible — a disqualified good lead is gone and emits no signal. An outcome-driven improvement loop therefore **rewards drift toward strictness**: conversion among passed leads rises while total revenue falls. This is selection bias with a feedback loop attached, and it is self-reinforcing. Counterweights (holdouts, forced random pass-through, human adjudication of rejections) are required for C1 and not for C2/C3. Consequence: **the evaluation architecture is use-case-specific even where the execution architecture is not.** Any case whose negative decisions destroy their own evidence inherits this trap.

**The interest-alignment fault line (INTERPRETATION).** C1 is a *misaligned-interest* conversation — the person wants to look valuable, the business wants to filter — so it needs persuasion, evasion handling, and skepticism toward self-reported facts. C2 and C3 are *aligned-interest*: the agent can ask and expect a truthful answer. C2 and C3 are near-twins; C1 is a different animal wearing the same pattern. Alignment, not domain, is the axis on which the conversational engine actually differs.

---

## 3. Decisions and architectural principles

### Principle 1 — Deterministic-first, LLM escalation

**DECIDED as a principle.** Deterministic logic runs first; the LLM is invoked where deterministic logic cannot confidently resolve. Corollaries drawn in session: do not spend a model call generating a reply you already know after a successful tool call (template the known reply, LLM as fallback); do not classify every turn if the job structure already supplies direction.

Caveat attached by the owner and kept: this principle must not be applied for elegance. Selection comes from the actual job and its failure, latency and business constraints — and the hot path must be measured first (section 8.4).

### Principle 2 — The agent proposes, authoritative systems dispose

**DECIDED as a principle.** The LLM decides *what it wants to do* and emits a structured action proposal; it never controls execution. Execution is deterministic, bounded, validated against a declared contract, and gated where consequences require it.

### Supporting decisions

1. **External systems remain authoritative where appropriate.** *(DECIDED — the most consequential inversion of the session.)* Agent Studio stops assuming it must own the system of record. Customers, tickets, appointments and leads stay authoritative in the customer's existing systems. Flow: Agent Studio conversation → action/event → existing system of record → outcome → back into Agent Studio evaluation. Positioning follows: an intelligence layer on systems businesses already have, not another business system.
2. **Freshness is declared per read / per tool contract, never globally.** *(DECIDED.)* The same move as the leaf contract (point 9), applied to data instead of code.
3. **Reads that gate a side effect must be fresh.** *(DECIDED.)* Stale means double-booking, a real-world failure, a refund. These reads sit on the critical path — and they happen once, near the end of an episode, not on every turn. This is what makes the latency budget honest.
4. **Conversational/contextual reads may tolerate bounded staleness.** *(DECIDED.)* Reads that only shape the conversation may be stale within a declared bound; being wrong costs a sentence.
5. **Evidence is durable.** *(DECIDED.)* Runtime evidence — episodes, turns, tool calls and results, retrieved evidence, decisions, errors, latency, token/cost, outcomes, human feedback — is product data, not operational logs. Un-recorded episodes are gone forever.
6. **The specification is versioned.** *(DECIDED.)* The durable asset is a structured, versioned specification (goals, constraints, stages, policies, behaviors, required fields, criteria, allowed actions, escalation rules, knowledge config, **and evaluation criteria**), not prompt text living inside generated code.
7. **Evaluation and correction do not silently mutate production behavior.** *(DECIDED, and this changed the owner's thinking mid-session.)* The specification must not be an ever-growing historical record of every exception. Four separate artifacts instead (see 3.A). The loop is: run → observe → identify disagreement → create evidence and evaluation → **deliberately** change the specification. Not: run → spec gets bigger automatically.
8. **Behavior changes are reviewable, promotable and revertable.** *(DECIDED.)* Lifecycle: specification → runtime evidence → evaluation/correction → proposed behavior change → review/promotion → new specification version. Purpose: changes are attributable and reversible, rather than the agent silently "learning". Continuous improvement must never mean the customer's running agent changes itself from our observations — that is a bad trust model. Hosted: promotion by us or an agreed policy. Self-hosted: promotion by them. **The loop survives a change of deployment ownership.**
9. **Custom code exists as controlled leaves, never as arbitrary control flow.** *(DECIDED — the resolution of contradiction C1.)* Control flow — what the agent asks, in what order, action gates, escalation, completion — lives in the specification only: interpretable, diffable, assertable, promotable. Leaves — tool implementations, field validators, formatters, scorers, auth adapters — may be arbitrary code behind a *declared contract* (signature, pre/post conditions, failure modes, latency budget). Proof test: **the evaluator asserts over the contract, never over the implementation.** This is why the schema never grows toward Python-in-JSON: it never expresses computation, only sequence, condition and policy. The declared anti-goal is a gigantic declarative schema representing every possible behavior — moving complexity from Python into JSON. The escape hatch must be *intentional*, with three levels conceptually preserved: configuration → supported extension point → custom implementation.
10. **Generated code is no longer assumed necessary.** *(DECIDED as a stance; the fork itself is NOT finally decided — see section 6.)*
11. **Customer ownership and runtime ownership are separate concepts.** *(DECIDED.)* Five separations were attempted (by artifact, by space, by time, by scale, by customer condition). The resolution: *customer ownership can extend as far as we can preserve a stable behavioral contract; above that boundary the system becomes a **fork** rather than an Agent Studio agent.* Modify the control-flow spec → still evaluable, because the spec is structured. Modify leaf code → still evaluable, via the contract. Modify the runtime → we lose the ability to reason about what the system is doing. **Current favored boundary (explicitly not final):** the customer owns the agent definition + their data + the deployment choice; Agent Studio owns the core runtime and the evolution of behavior; extensions are customer-controlled leaves behind stable contracts; every behavior change is versioned and promotable rather than silently learned.

### 3.A The four-artifact split

| Artifact | Holds | Mutability |
|---|---|---|
| **Specification** | Intended behavior | Changed only by deliberate, reviewed promotion |
| **Evidence** | What actually happened (episodes, traces, outcomes) | Append-only |
| **Evaluation** | What we judged to be wrong, and why | Append-only, versioned per agent version |
| **Deliberate changes** | What we chose to promote into the spec | Reviewable, revertable, attributable |

**INTERPRETATION:** these four have the shape of version control. Spec = checked-in state. Evidence = the working tree. Promotion = a pull request **on behavior**, reviewable and revertable. This suggests a review queue of candidate specification changes derived from failed episodes — and it collapses two subsystems into one: the product's job is not to *measure* conversational quality objectively (quality is irreducibly contested) but to make **disagreement cheap to express and fast to propagate**. That is substantially lighter to build than objective scoring, because it never has to define "good" in general — only what was wrong *here*.

### 3.B Derived product boundary

> Customer ownership can extend as far as we can preserve a stable behavioral contract. Above that boundary, the system becomes a fork rather than an Agent Studio agent.

This boundary was **derived from a constraint, not chosen by preference** — which is why it is worth keeping.

---

## 4. The three architectural seams that are expensive to retrofit

The V1 rule (HYPOTHESIS, accepted as a working discipline): **build the narrowest valuable case, but refuse anything that structurally forecloses the hard case.** The test is not "is it hard" but **cheap vs. prohibitively expensive to retrofit**. Adaptive probing, transactional tool semantics, persistent case lifecycle and hybrid retrieval are all *additive later*. Exactly three things are not.

### Seam 1 — Episode evidence + identity (episode ID and external join key)

**FACT:** durable storage today is two SQLite tables — `sessions` (session_id, created_at, last_active, active) and `built_agents` (agent_name, project_path, system_prompt, selftest_status, timestamps), verified in `builder_platform/storage/schema.sql`. There is no table capable of recording a conversation, a turn, a tool call, an outcome or a latency. Runtime conversation state is `MemorySaver` (`boilerplate/graph.py:239`); `builder_platform/runtime.py:137` states that state is carried across turns *"without us persisting the transcript"*; durable checkpointing is left as an unexercised option (`graph.py:50` region).

**INTERPRETATION:** build-time facts are durable, run-time facts are ephemeral. `selftest_status` is a **build-time** quality gate standing in for a **run-time** quality signal. The improvement loop the owner finds most interesting (builder and operator as one continuous product loop) currently has zero substrate — the circuit is physically open.

**Why retrofit is prohibitively expensive:** un-recorded episodes are gone forever. There is no backfill for a conversation that was never written down. Worse, the evidence has two tiers with different plumbing: *interaction-quality* signals are dense, immediate, computable from the episode alone, and mostly deterministic assertions requiring no judge; *hard outcomes* are sparse, delayed, and arrive from outside (CRM, ticketing, calendar). The consequence nobody lists: **every episode needs a join key into the operator's system of record**, or "later downstream outcome" is permanently unobtainable. Minting an episode ID and carrying an external join key costs almost nothing up front and is brutal afterwards, because the historical episodes that would have taught you something cannot be re-joined.

### Seam 2 — Versioned specification (not a generated prompt or generated code)

**Why retrofit is prohibitively expensive:** if intended behavior lives as prose inside generated Python, then diffing behavior, asserting over behavior, reviewing a proposed change, reverting a regression, and attributing an outcome to a version are all unavailable. Introducing versioning later requires reconstructing the intended behavior of every past agent from code that has already drifted — and every evaluation record collected before the spec existed has nothing stable to be *about*. Evaluation criteria in particular must live inside the durable spec rather than being recreated per generation.

**Related trap (INTERPRETATION):** the "generated agents are disposable" model has an unstated precondition — **nobody ever edits the generated output**. The moment a developer tweaks a generated `prompts.py`/`tools.py` in place, regeneration destroys the work and the compiler model collapses into a one-shot scaffolder. This requires either airtight round-tripping or a "generated code is read-only, all changes go upstream" contract *with teeth*.

### Seam 3 — The external-system boundary

Four coupled commitments: external state is authoritative; freshness is declared, not assumed; tools are reached through declared contracts; and reads are classified by consequence — side-effect-gating reads must be fresh, conversational reads may be bounded-stale.

**Why retrofit is prohibitively expensive:** the authority question determines where truth lives, and therefore what the agent is allowed to assume between turns. A system built assuming agent-owned state has its invariants, its caching, its error handling and its latency profile all written against that assumption; inverting authority later rewrites the data layer, the tool layer and the reply path simultaneously. Freshness-per-contract cannot be added as a flag to tools that were never classified by consequence.

**INTERPRETATION with latency teeth:** because the agent holds no authoritative state, decisions must be made against *freshly read* external state. External tool I/O may therefore dominate the reply path rather than sequential LLM calls. This means the "where does intelligence live / reduce LLM calls" thread rests on an **unmeasured premise**, and observability must precede optimization (section 8.4).

**These three seams bind as architecture constraints even before the product is chosen.** They are what may be committed to while the use case is still open.

---

## 5. What happened to the current architecture

**FACT (verified in `boilerplate/graph.py:188-239`):** the real graph is not a four-stage Intent → Think → Tool → Enrich pipeline. That was a conceptual summary. `build_pipeline` registers **fifteen** nodes — `intent_detect`, `knowledge`, `agentic_retrieval`, `chitchat`, `closing`, `system`, `planner`, `plan_step`, `think`, `hitl_gate`, `tool_exec`, `execution_validator`, `failure`, `enrichment`, `validator` — with **six** conditional routers (`route_by_intent`, `route_after_planner`, `route_after_plan_step`, `route_after_think`, `route_after_hitl`, `route_after_execution`) and compiles with `MemorySaver` by default.

**FACT:** `boilerplate/nodes.py` is 1776 lines — roughly 22% of the 8229-line engine+platform tree and about twice the next-largest file. It contains six direct LLM call sites (`INTENT_MODEL` ×1, `ANSWER_MODEL` ×4, `ENRICH_MODEL` ×1); `boilerplate/rag_subgraph.py` adds two more. `rag_subgraph.py` (164 lines) and `filler.py` (90 lines) are among the thinnest files in the tree.

**INTERPRETATION:** the subsystems that the emerging architecture wants to *promote* (retrieval as a subsystem, evaluation as a first-class concern) are currently the smallest files, while the monolith that the narrowing wants to *shrink* is the largest. The right question was never "is Intent → Think → Tool → Enrich correct" — that is a caricature — but **which of the fifteen nodes survive the narrowing to text-first inbound qualification.** The owner expects some to disappear entirely.

### Classification under the narrowing (text-first, inbound, aligned-interest, deterministic-first, agent-proposes/systems-dispose)

All rows are **INTERPRETATION**.

| Node | Verdict | Reasoning |
|---|---|---|
| `planner` | **Likely deleted** | Compound multi-step planning is an outbound / complex-sales affordance; aligned-interest intake is single-goal |
| `plan_step` | **Likely deleted** | Same; also the source of the graph's one sanctioned loop |
| `enrichment` | **Likely deleted — the clearest single casualty of Principle 1** | Spending an SLM call to phrase a tool result is exactly the call deterministic-first replaces with a template |
| `intent_detect` | **Needs measurement before deciding** | Direction largely comes from job structure, so it collapses toward a small on-task / off-task / done discriminator — but cutting it is a measurement decision, not an aesthetic one. Do not delete before measuring |
| `chitchat` | **Likely simplified** | Becomes a deterministic/template path |
| `system` | **Likely simplified** | Reduced surface under a narrower job |
| `validator` | **Likely simplified** | In text the pre-TTS sanitizer concern vanishes; what remains is policy and schema validation |
| `hitl_gate` | **Likely simplified — relocated in kind** | Becomes "confirmation before a side effect", which is a **tool-contract property**, not a graph node |
| `knowledge` | **Likely survives** | Inbound callers ask things |
| `closing` | **Likely survives — more important** | Episode completion and structured disposition become central |
| `tool_exec` | **Likely survives — strengthened** | Must carry idempotency and transactional semantics (use-case dependent in degree: maximal for appointment intake) |
| `failure` | **Likely survives** | The failure boundary is a declared axis |
| `execution_validator` | **PROMOTED** | Becomes the **contract assertion point** — the place the evaluator makes its claims, per the leaf-contract resolution |
| `agentic_retrieval` | **Relocated** | Survives as a **subsystem pulled out of the agent flow**, not as a node inside it |
| *(use-case dependent overall)* | `tool_exec` hardening, `hitl_gate` shape, and the evaluation counterweights all vary by chosen case |

### Voice-specific machinery removed outright by text-first

**FACT (files exist and are voice-specific):** `boilerplate/filler.py` (pre-think filler + per-tool filler banks), sentence-chunking of the final reply, `builder_platform/sanitizer.py` (pre-TTS backstop), `builder_platform/vapi_adapter.py`, `builder_platform/vapi_control.py`, `builder_platform/tunnel.py` — and the **entire turn-segmentation axis** (barge-in, interruption, endpointing, corrected-transcript dedupe).

**INTERPRETATION:** this confirms the modality thread. These are not "modality-specific logic leaking into the core" — they are concerns that **cease to exist** in text. Nothing has to be abstracted; they are simply out of scope.

**This section is not a refactor plan.** It is a prediction of what the narrowing implies, recorded so the prediction can be checked later. No node is to be deleted on the authority of this document, and `intent_detect` in particular is explicitly blocked on measurement.

---

## 6. Generated code decision

**NOT FINALLY DECIDED.** What is recorded is a conclusion about the *state of the evidence*, in the owner's own framing:

> Generated code is **not obviously load-bearing**, but it carries real properties around ownership, extensibility, deployment, isolation and escape hatches. The live question is whether those can be preserved with a versioned specification + shared execution **without reintroducing the complexity we removed.**

Its genuine advantages are mainly **customer ownership**, **deployment flexibility**, and certain **escape-hatch properties** — and those may be achievable instead through a versioned specification, controlled extension points, and a separation of deployment from runtime.

### Triage of the twelve claimed advantages

The owner's own key distinction: some are genuine product advantages; others are **compensations for not having a good enough shared runtime.**

| # | Claimed advantage | Verdict |
|---|---|---|
| 1 | Customer ownership and portability | **Genuine artifact requirement** — but it is the same property as 4, 5, 12 |
| 2 | Escape hatch for the weird case | **Compensation** — delivered by the leaf contract with no code generation |
| 3 | Deep customization without expanding the core schema | **Compensation** — same leaf contract |
| 4 | Easier enterprise trust story | **Genuine** — same property as 1 |
| 5 | Deployment into the customer's environment / VPC | **Genuine** — same property as 1 |
| 6 | Isolation (process / runtime / dependency) | **Compensation** — a deployment and supervision concern, never about generated application code |
| 7 | Independent versioning and rollback | **Compensation** — obtainable from versioned specs plus runtime-compatibility versioning |
| 8 | Debugging at artifact level ("show me the code that ran") | **Converts into a tracing requirement** — deterministic spec + runtime version + episode trace |
| 9 | Performance / specialization | **Theoretical**, not current |
| 10 | Dependency flexibility | **Compensation** — leaf contract |
| 11 | Failure containment of a pathological agent | **Compensation** — deployment/supervision |
| 12 | Offline / self-hosted execution | **Genuine** — same property as 1 |

**Result:** of twelve claimed advantages, only **1, 4, 5 and 12** genuinely require an artifact — and all four are the *same* property. The architectural contradiction therefore dissolves, and what remains is a **product/commercial contradiction about ownership**, addressed in section 3 point 11 and still open in section 7.

### What evidence would justify KEEPING generated code

- A target customer segment that **refuses** a hosted runtime for reasons that spec-level ownership does not satisfy (data residency, compliance attestation, air-gapped operation) — observed in an actual procurement conversation, not assumed.
- A real customer requirement that the leaf contract cannot express, that a supported extension point cannot express either, and that recurs across more than one customer.
- A demonstrated need to pin an entire runtime+code version where spec-version + runtime-compatibility-version proves insufficient in practice (i.e. an actual incident where the weaker guarantee failed).
- Evidence that artifact-level debugging materially beats a spec + runtime-version + episode trace on real production incidents.

### What evidence would justify REPLACING it with a shared/interpreted runtime

- Spec-level ownership (inspect, version, diff, export, run elsewhere) satisfies the ownership question for the actual target buyer, confirmed in conversation.
- Episode traces plus spec version plus runtime version reconstruct past behavior well enough to debug real failures.
- Variation between customers in the chosen use case fits a deliberately limited configuration surface plus leaf extensions, observed over several deployments rather than predicted.
- The regeneration-destroys-local-edits trap keeps biting: evidence that the generated output *is* being edited in place proves the compiler model is not holding and the artifact is not actually read-only.

### Orthogonality warning

**"No generated application code" and "one process serves everyone" are orthogonal concerns and must not be coupled.** A shared interpreter is an **execution model** question. Isolated instances, workers, containers and customer deployments are a **deployment topology** question. Nothing in this session proved multi-tenancy, and nothing about adopting a shared runtime requires it.

---

## 7. The biggest unresolved questions

Ranked by what must be **learned** next, not by intellectual interest. The session's closing judgment was that the project is **not idea-starved, it is evidence-starved.**

| # | Question | Why it ranks here |
|---|---|---|
| **1** | **Which conversational job has enough business value, repeatability and measurable outcome to justify building a specialized Agent Studio around it?** | Everything downstream — evaluation architecture, tool semantics, config surface, buyer, pricing — is a function of this answer. It is the one question this session deliberately refused to settle |
| 2 | Will customers actually pay for it? | The most dangerous unflagged assumption of the session was that a technically impressive and reusable product will *necessarily* have enough business value. Inverted: the boilerplate is not the deliverable — it is a **cost reduction on delivering the real thing** |
| 3 | Is the outcome sufficiently measurable, given delayed and ambiguous outcomes? | Determines whether the improvement loop is a product feature or a demo. Also where the invisible-false-negative trap lives |
| 4 | How much does the job vary between businesses? | Decides whether "configuration-first" is a real strategy or wishful thinking |
| 5 | Can that variation be expressed as configuration **without a giant DSL**? | The declared anti-goal is moving complexity from Python into JSON. The leaf-contract resolution is the proposed answer and is untested |
| 6 | How much external integration is actually required? | Determines the real cost per deployment and whether the join key is cheap or a project |
| 7 | What latency does the real external hot path introduce? | External-read latency may dominate LLM latency. Until measured, every "where does intelligence live" decision is guesswork |
| 8 | Does the target customer need self-hosting / runtime ownership? | This is the residual C2 contradiction. If yes, the generated-code fork reopens; if no, it stays dormant |
| 9 | Is the existing voice boilerplate genuinely reusable after stripping modality-specific machinery? | The "evolve rather than discard" assumption is untested against the 15-node classification in section 5 |

---

## 8. Evidence plan

**This is the most important section.** The project is evidence-starved, not idea-starved. "We should research this" is not an item. Every item below names an artifact, a measurement, a count, or a specific instrumented thing, and is the **smallest** observation that could change the team's mind.

### 8.1 Desk research / market evidence

| Targets Q | Experiment | What would change our mind |
|---|---|---|
| 1, 2 | Build a one-page comparison of inbound-conversation capability already shipped by the incumbents named in the session (Zendesk, Intercom, Freshdesk, ServiceNow for C2; the top 3 booking/scheduling vendors in one chosen vertical for C3). Record, per vendor: does it already own the conversation? does it own the system of record? is the capability bundled or an upsell? | If a C3 incumbent already ships inbound conversational intake *and* owns the calendar, C3 loses its main advantage over C2 and the ranking hypothesis collapses |
| 2 | For one C3 vertical, collect the **published** price of a missed/booked appointment: no-show rate, average appointment value, and what businesses already pay per booking to third parties (aggregators, answering services). One page of sourced numbers | If per-booking economics cannot support a software price point, C3 is out regardless of architecture fit |
| 1, 4 | Collect **5–10 real inbound intake transcripts or scripts** for the candidate job (public answering-service scripts, vendor demo flows, published intake forms). Diff them field-by-field and stage-by-stage | If the required-field sets and stage sequences diverge wildly across 5 businesses in the *same* vertical, "configuration-first" is falsified early and cheaply |
| 8 | Check the published security/compliance posture of 5 representative target buyers in the chosen segment (do they run SaaS? do they require SOC2, a DPA, data residency?) | Evidence of hard self-hosting requirements reopens the generated-code fork before any code is written |

### 8.2 Customer conversations

| Targets Q | Experiment | What would change our mind |
|---|---|---|
| 1, 2 | **8 conversations** with operators in the single highest-ranked candidate vertical (owner/practice manager for C3). Fixed script, three questions: who handles inbound requests today and for how many hours a week; what happens to the ones you miss; what do you pay today to not miss them | Fewer than 3 of 8 able to name a current spend or a current person-cost = the job is not painful enough to buy. That kills the candidate |
| 1, 3 | In the same 8, ask: **how would you know the agent did a bad job?** Record their answer verbatim, without prompting | If operators cannot name an observable failure, the evidence→evaluation→promotion loop has no customer-side signal and must be rebuilt around our own assertions only |
| 4, 5 | Ask 5 of the 8 to describe their intake rules, then attempt to express each one in the draft specification schema. Count the ones that need a new schema concept vs. a new leaf | More than ~1 new schema concept per customer means the config surface will grow into the forbidden DSL |
| 6 | Ask the same 5: which system must be written to, and **can an outside system write to it** (API available? who controls access?). Record the exact system name and integration path | If writing to the system of record requires per-customer bespoke work, deployment cost per customer dominates, and the "intelligence layer on existing systems" positioning gets much more expensive |
| 8 | Ask directly: would you accept a hosted runtime holding your conversation data? | A clear yes from the target segment keeps the C2 contradiction dormant and settles section 6 in favour of a shared runtime for V1 |

### 8.3 Prototype evidence

| Targets Q | Experiment | What would change our mind |
|---|---|---|
| 5 | Write the **specification artifact for exactly 2 different businesses** in the chosen job — by hand, no runtime. Diff the two specs. Count: fields shared, fields differing, control-flow constructs needed, leaves needed | If the diff is mostly *control flow* rather than *data and policy*, the spec is heading for Python-in-JSON and the leaf-contract resolution has failed |
| 9 | Take `boilerplate/` and produce a text-only cut following section 5's classification: delete the voice machinery and `planner`/`plan_step`/`enrichment`, keep the rest. Measure the resulting line count of `nodes.py` and whether the selftest still passes | If what remains is still a 1000+ line monolith with coupling that resists the subsystem split, "evolve rather than discard" is falsified and a clean reimplementation is the cheaper path |
| 1, 3 | Run the narrowest end-to-end episode on one real external system (one calendar account): conversation → structured action proposal → deterministic execution → confirmation → an episode record carrying an episode ID and the external join key. One happy path only | If a single joined episode cannot be produced end to end cheaply, Seam 1 is harder than assumed and must be scheduled, not assumed free |
| 3 | Define the **5 interaction-quality assertions** for the chosen job (required info collected; correct tool use; correct retrieval/evidence; correct escalation; policy compliance) and assert them over ~20 scripted episodes at the `execution_validator` contract point | If fewer than 4 of 5 can be asserted deterministically from the episode alone, the "no judge needed for tier-1 evidence" interpretation is wrong and evaluation gets much more expensive |
| 3 | For whichever candidate is chosen, write down the **invisible-failure test**: can a wrong *negative* decision be detected at all? If not, specify the counterweight (holdout rate, forced random pass-through, human adjudication of N rejections/week) before any loop is built | A candidate with no feasible counterweight must not be chosen, because its improvement loop actively degrades the business |

### 8.4 Runtime measurement — instrument before optimizing

**DECIDED in session: instrument the actual hot path BEFORE deciding where intelligence lives or optimizing the LLM path.** Freshness and external-read latency are architecture, not an integration detail. The reasoning: because external systems stay authoritative, side-effect-gating decisions must read fresh external state, and **external read latency may dominate LLM latency.** Every conclusion about collapsing nodes or reducing model calls is unfounded until this is measured.

| Targets Q | Instrument | Decision it unblocks |
|---|---|---|
| 7 | Per-turn end-to-end latency broken down into: LLM time per call site (the 6 in `nodes.py` + 2 in `rag_subgraph.py`), external tool I/O per call, retrieval time, framework overhead. Emit as structured episode telemetry, not logs | Whether the optimization target is model calls at all. If external I/O dominates, cutting `intent_detect` or `enrichment` buys nothing and the work belongs at the data/caching layer |
| 7, 3 | Tag every external read with its **consequence class** (side-effect-gating vs. conversational) and measure how many of each occur per episode, and where in the episode they land | Validates the claim that side-effect-gating reads happen once near the end rather than every turn. If they occur per turn, the latency budget is not honest and the freshness model needs rework |
| 1 (indirectly) | Count per episode: turns, LLM calls, tool calls, tokens, cost. Store on the episode record | Gives the first real unit-economics number, which feeds the "will they pay" question with actual cost-to-serve rather than a guess |
| 9 | Measure `intent_detect`'s actual contribution: how often does its classification change the route, on real episodes, versus what job structure alone would have chosen? | The one explicitly blocked deletion in section 5. This measurement is the gate |

---

## 9. Explicit non-decisions

Deliberately **not** decided in this session:

1. **Appointment intake is not selected.** It is the leading hypothesis for the first use case, supported by three independent strikes against the previously top-ranked candidate, and validated by nothing.
2. **Sales vs. non-sales is not completely closed.** Text-first and inbound were decided; this was explicitly left open alongside them.
3. **Generated code vs. interpreted shared runtime is not finally decided.** The architectural contradiction dissolved; the commercial one (ownership) did not. Evidence criteria for both directions are in section 6.
4. **The exact retrieval architecture is not decided.** Retrieval is to become a subsystem rather than an in-flow node; whether it is deterministic lookup, lexical, dense, hybrid, or an external knowledge API is open, as is knowledge authority (embedded snapshot / versioned internal store / external source of truth / external + bounded cache).
5. **The exact LLM/model strategy is not decided.** One general model, specialized per stage, cost tiering, or deterministic-first with LLM fallback — Principle 1 states the *posture*, not the call-site topology, and the topology is blocked on 8.4.
6. **The exact graph / state-machine architecture is not decided.** Section 5 is a prediction, not a plan. No node deletion is authorized by this document, and `intent_detect` is explicitly blocked on measurement.
7. **The self-hosting vs. hosted deployment model is not decided.** Five separations of ownership were explored (artifact, space, time, scale, customer condition); conditional ownership by customer segment remains the most commercially plausible and is unvalidated.

Also still open, carried forward verbatim: *is the residual ownership contradiction acceptable for the customers we target, or does the target customer fundamentally require runtime ownership?*

**Purpose of this document:** to leave a clean position — decided things decided, strong directions marked as directions, bets marked as bets, and the next evidence named concretely — from which a Product Brief can start.
