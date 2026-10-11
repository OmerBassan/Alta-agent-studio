---
title: "Addendum — Agent Studio Business-Specific Agent Platform PRD"
status: final
created: 2026-10-08
updated: 2026-10-08
---

**Addendum to the Agent Studio PRD.** Depth that belongs downstream — to architecture, solution design, UX specification or evaluation planning — rather than in the PRD body. Nothing here is a product commitment unless the PRD says so.

---

## AD1. Prior art detail behind the differentiation claim

The PRD names the prior art (§4.2) and states the narrowed claim (§4.1). The fuller market reasoning behind that narrowing is retained in `extract-landscape.md` in this workspace, including:

- the full competitor inventory across small-business agent-builder platforms, automation engines with agents bolted on, vertical agents, cloud and lab assistant platforms, and developer frameworks;
- evidence on the configuration-paradigm question, and why the broad version of the differentiation claim is defeatable with a single link;
- the conventional 2026 trust-surface set that buyers now expect as table stakes;
- small-business adoption friction evidence: cost, knowledge gaps, trust, integration friction, and the finding that a large majority of non-adopting small businesses report seeing no applicable use case;
- pricing norms, per-resolution anchors, and the finding that usage and credit unpredictability is a leading churn driver in the small-business tier;
- the arguments that most threaten the thesis, including the vertical-beats-horizontal evidence and the drift of agent frameworks back toward graph execution.

These inform positioning and go-to-market rather than V1 requirements, which is why they are here and not in the PRD.

### AD1.1 The disposition rule that must travel with the market evidence

The rule governing this evidence lives in the PRD, as the second of the three standing conditions (§4.3): market evidence is recorded and is not permitted to steer the product toward hunting an empty niche.

What belongs here is why that condition was needed. The strongest finding in the material — vertical agents outperforming horizontal ones, and being what passes audit — points directly at the move the product refuses to make (§4.4), and the resolution is the one already in §1.2: sell the outcome, keep one engine behind it, treat "general-purpose" as an internal architecture claim. Anyone revisiting this evidence later must read it with the condition attached, or they will re-derive a vertical product from it.

### AD1.2 The deepest rejection: the intelligence layer on someone else's record

Recorded because two open items — commercial packaging and a spend ceiling (O6, O8) — will otherwise be revisited by someone who no longer knows why this door is shut.

A tempting position for this product is the **intelligence layer sitting on top of systems of record it does not own**. It was rejected, and the reasoning is structural rather than competitive: the owner of the system of record controls the write API, owns the distribution, holds the outcome data, and can price on outcome *because it alone observes the outcome*.

Each of those is a mechanism, not a preference. Together they make the intelligence layer the first thing the record-owner builds, with advantages no third party can offset by being better at it.

The corollary bears directly on pricing: **a third party without the join key cannot price on outcome at all**, because it cannot independently see whether the outcome occurred. That is why the PRD's episodes carry an explicit join key where they touch an external system of record (FR86, §6), and why outcome-based pricing is not assumed anywhere in O6 or O8.

This is also why the PRD states plainly that external business systems remain authoritative (FR36) rather than as a note of modesty: owning no system of record is a deliberate position whose costs are known.

### AD1.3 Cheap falsifiers that were available and not used

The source material named several low-cost tests capable of falsifying parts of the thesis before much is built — small probes rather than programmes. They are recorded here because the PRD's validation programme (E12) is substantial and slow by comparison, and because at least one of them tests something the PRD instead **promoted to a requirement without testing**: that every success criterion worth having is computable from an episode record without a person reading it. FR76 has since been narrowed to the per-episode and per-business criteria (§10.1, §10.2), where that is actually true — the correction that probe would have produced. Anyone planning E12 should look for the cheap version of each measurement first.

---

## AD2. Brownfield lessons carried forward as knowledge

From the shipped voice system. Each cost real debugging time. The PRD's §7.4 states the reuse posture and four of these produced requirements directly (FR95–FR98); the rest are recorded here because they are engineering discipline rather than product requirements, and because the reasoning is worth more than the conclusion.

**A named optimization is a hypothesis about the codebase, not a specification.** Of four textbook context-and-latency techniques, three had no target in that engine or rested on false premises about its shape; one was a real lever. In a separate case, a requested trigger turned out to be structurally impossible to fire. This is the evidence behind the third standing condition in the PRD (§4.3): a named technique is a hypothesis about this system, and the mechanism it targets must be confirmed on the path that matters before anything is committed. It is also why §7.3 states guarantees and names no mechanisms.

**Never pay a model call to restate output the system already has.** The durable lever is to harvest the structured record produced by work already done and keep prose synthesis off any path a person is waiting on. The lever carries; the voice-specific twenty-word spoken form of it does not. The PRD settles the rest of this: §1.3 names the superseded principle, states why the asynchronous channel removes the arithmetic that justified it, and keeps the limit that survives.

**A graceful fallback that looks like success is the most expensive bug class there is.** Two logged instances. An empty-but-set environment variable made every model tier fail while a mock fallback served plausible deterministic text under a banner claiming live operation — the verification had checked the mode *label*, not a completion. And a fabrication guard presented an honest-sounding decline that masked three stacked retrieval faults. This is the origin of FR46 and NFR17, and the reason a health check must prove a real request rather than inspect configuration.

**On a single-threaded event loop, one blocking synchronous call voids every timeout that depends on it.** A network call with no timeout of its own froze the loop, so the global dead-air ceiling could never fire — a fault displaced entirely from its symptom. This is FR97.

**Transport ground truth comes from captured traffic, not vendor documentation.** The two most expensive traps in the shipped system were both undocumented vendor behaviours: a single space in one configuration field silently wedged an entire output queue, and the vendor resent corrected transcripts against the same identity, so the runtime had to be idempotent per logical turn or it double-processed. This is FR98.

**Config-driven generation fails in two specific ways.** A ship gate coupled to one domain forced the builder into a rewrite loop, and the reaction was to stub the gate so it always passed — the check was disabled to stop the pain, which is the worst available outcome and the direct reason for FR95. Separately, a shared declarative registry applied unscoped across every context, so one entry silently answered unrelated ones: any shared registry in a generated artifact must be scoped to its owner.

**Deterministic appenders and detectors have ordering constraints that tests will not find.** A rotating text bank appended *before* a stall fingerprint gave byte-identical replies a different hash each turn, silently disabling the detector while the escalation path of last resort still reported healthy. Found by reading ordering, not by a failing test, and verified by reintroducing the bug. This is FR96.

**Provider agnosticism is enforceable, and enforcing it pays twice:** a credential-free continuous-integration gate, because a blank key yields mock mode, and genuine artifact portability. NFR12 preserves both.

**What is deliberately not inherited.** Four gaps in the shipped system: no instrumentation on any model call; no correlation identity outside the voice path; minimal persistence; single-tenant by stated non-goal. The PRD closes the first two as day-one Core capabilities (NFR13, NFR14, NFR16). Multi-tenancy is net-new work rather than a port. Documentation and tests in that repository have drifted before; treat them as claims to verify, not as ground truth.

---

## AD3. Implementation opportunities in recent model developments

**Status: implementation and evaluation opportunities only. Not product requirements, not architectural commitments.** Recorded here so the reasoning is not lost, and so no one later mistakes a cost observation for a design decision.

The PRD body names no model, no provider and no vendor API. **Provider agnosticism is a hard boundary**: the platform binds no LLM vendor, and swapping providers must remain a configuration change rather than a code change. That rule is unaffected by everything below.

### AD3.1 Cheap high-volume inference changes a cost assumption, not an architecture

Low-cost, high-throughput model tiers — aimed at classification, repetitive tasks and subagent workloads — change the economics of lightweight model calls.

The consequence is a subtraction, which is why it matters: it removes the incentive to **over-engineer deterministic substitutes purely to avoid inference cost**. Model-based reasoning during Builder elicitation, and during routine Agent execution, becomes defensible on cost grounds where it previously was not.

This does **not** license adding model calls freely. The limit that survives from the shipped voice project is the one the PRD states in §1.3: cost and latency are not licences, and no model call is added to a path a person is waiting on without measuring that path. What changes is the cost argument, not that limit.

**Multi-model routing and tiering remain an implementation and evaluation question.** The architecture must be able to *express* tiering across capability classes; which tier serves which class is measured, not designed up front, and is not a V1 product requirement.

> One note on sourcing: the specific model generation and its published positioning were supplied by the project owner, are taken as given, and are not independently verified. Nothing depends on them — the PRD names no model by design — so the claim is load-bearing for cost planning only.

### AD3.2 Not every intelligent decision needs the full Agent loop

Typed, narrowly-scoped decision models — the shape behind recent focused-decision APIs and typed decision-model libraries — make one implementation option concrete: a narrow question can be delegated to a small typed decision call instead of a full Agent reasoning loop.

Plausible later applications: lightweight classification, semantic guard conditions, routing, prioritisation.

**No specific vendor API or library becomes an architectural dependency.** Any such mechanism sits behind the platform's own runtime boundary, like every other provider concern. The durable takeaway is conceptual:

> Not every intelligent decision needs the full Agent loop.

Two cautions keep this from becoming the rejected model by another route. A typed decision call used to pick the Agent's next step is deterministic next-action selection, which FR39 forbids — such a call may constrain or classify, never sequence. And a model-evaluated guard is still bound by FR44: two closed outcomes, and never a composed reply.

**Where these belong.** Both developments are carried as **candidates for the later model and runtime strategy, and for the proof gate (§7.5)** — nothing more. Neither is a product dependency, neither appears in the PRD body, and neither may be cited as satisfying a requirement. The PRD's instrumentation-first stance (NFR13, NFR14) is what will decide whether either is adopted, because the strategy is measured rather than designed.
