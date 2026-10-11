# Spine Reconciliation — PRD vs. finalized Architecture Spine

Source of truth: `extract-spine.md` (prepared extract of `ARCHITECTURE-SPINE.md`, FINAL).
Target: `prd.md` (status: draft, 2026-10-08).
Scope of this review: constraint compliance (A1.1–A10.4), workflow-regression check (EXTRA 3, F1–F11), vocabulary compliance (section C) and the thirteen deferrals (section B). Prose, structure and product judgement are explicitly **not** reviewed here.

**Headline.** No critical findings. Zero outright violations of A1.1–A10.4. The PRD is unusually disciplined against the workflow-regression trap: F1–F11 are all either explicitly guarded or absent. Twelve findings are recorded, almost all of the "wording admits a reading the Spine forbids" or "Spine guard not carried forward" class, plus two genuine gaps (F9 elicitation decomposition; the unbounded Agent loop).

---

## Part 1 — Constraint compliance (A1.1 – A10.4)

Verdict key: **H** honoured · **HQ** honoured with qualification (finding) · **S** silent with a product consequence (finding) · **V** violated (critical).

| # | Verdict | Where the PRD honours it | Note |
|---|---|---|---|
| A1.1 | H | §1.1, §4.3 ("A workflow engine"), §8 preamble ("None describes a sequence"), FR18, FR24, FR39 | Stated four independent times, including as a standing per-requirement self-check. Strongest compliance in the document. |
| A1.2 | H | FR38 (near-verbatim delegation list), FR47 (business declares escalation *conditions*, never execution) | FR38 reproduces all nine delegated decisions including "whether to escalate" and "how to handle a situation nobody enumerated". |
| A1.3 | H | FR47 | Includes the typed-refusal half and the "never escalates on the Agent's behalf" half. §11/O2 correctly books the receiving side as unspecified rather than inventing platform-side escalation. |
| A1.4 | H | §5 (litmus quoted verbatim as the acceptance criterion), §8 preamble, §10.3 | The litmus test is used as the architecture acceptance criterion and the generalisation measurements (§10.3) are expressible against it. |
| A2.1 | HQ | FR40 (closed set, "every kind is authorized and journaled, reads included"), FR58 (new semantics = platform release) | **Finding 1.** The PRD never enumerates the seven kinds (`retrieve`, `read`, `effect`, `clarify`, `respond`, `escalate`, `suspend`). This is defensible F8 hygiene — naming seven kinds in a table invites ordering them — but the product consequence "the capability model is a grant over these seven kinds" is therefore not stated, and `clarify`, `respond` and `suspend` appear nowhere in the PRD. `suspend` is implied only obliquely by FR60's `pending`. |
| A2.2 | H | FR41, FR56 | FR56 reproduces "Core contract → adapter → extension" and adds the product-level prohibition on advertising a direct Agent↔third-party connection. |
| A2.3 | H | FR58 | Explicitly requires the product to distinguish *configuring* a capability from *requesting* one. |
| A2.4 | H | FR51 (all six declared fields + verb-first + "a capability with no success-evidence definition is not shippable") | Complete. |
| A2.5 | H | FR54 | Retryability as a visible attribute, and the non-keyable exclusion. |
| A3.1 | H | FR53; confirmation requirement as a contract field in FR51; business-configurability via FR14 | Confirmation as a recorded, Core-enforced gate is stated exactly. |
| A3.2 | H | FR43 (verbatim, plus "no guarantee in this document rests on prompt text") | The added clause binds the PRD itself, which is stronger than the Spine requires. |
| A3.3 | H | FR14 ("what the Agent may conclude and on whose authority", "what it will not let an Agent decide"), FR16, FR51 | Enforcement is nowhere offered as configurable; FR95 reinforces (only platform-owned checks may block). |
| A3.4 | H | FR42 (all five guardrails verbatim, "zero configuration"); §7.2 + O9 keep domain safety packs as an optional, unbuilt extension point | Baseline trust story intact. |
| A3.5 | H | FR23 (detect granted-but-always-denied, block promotion, with AD-4's "worse than a refusal" rationale) | Verbatim-grade. |
| A4.1 | H | FR70, FR71, FR72 | FR72 (an action record is evidence, not a resolution) is an addition that strengthens AD-6 rather than bending it. |
| A4.2 | H | FR33 | All four binding components, unforgeability, and "refused before it reaches the person". |
| A4.3 | H | FR34 | Per-business enable/disable stated as "a declared risk"; marked in evidence. |
| A4.4 | H | NFR6, §13.1 | "evaluated against a threshold, never guaranteed" reproduced; §10 sets no number and says why. Nothing in the document over-promises correctness of meaning. |
| A4.5 | H | FR38 ("when to retrieve"), FR41, FR30, FR37 | Source-version granularity in FR30; reconstructibility in FR37. |
| A5.1 | H | FR77, FR78, FR79, FR82, E10 | The divergence list is the operator's *primary* surface, and "needs no human transcript review" is reproduced and re-asserted in FR76. |
| A5.2 | H | NFR16 | Deliberately says "established GenAI telemetry naming" rather than pinning OpenTelemetry by name — correct, since EXTRA 2 tells the PRD not to restate the stack. |
| A5.3 | H | FR20, FR95, S8 | FR95 ("platform-owned, domain-agnostic, never authored by the Builder it gates") is the sharpest statement of this constraint in either document. |
| A5.4 | H | FR81 | "closed, enumerable vocabulary" for every failure, refusal or status an operator sees. |
| A6.1 | H | FR45 | "exactly two exits … no third path and no silent degradation". |
| A6.2 | HQ | FR44 (verbatim-grade: never composes a reply, never chooses the next step; business configures *which* conditions, not what the Agent says) | **Finding 2 (highest-value in part 1).** FR44 is correct, but two other places pull against it: (a) §6's vocabulary entry defines a guard condition as "A declared condition that **overrides the ordinary conversational path** and may end the episode" — dropping both closed outcomes and substituting path-control language the Spine does not grant a guard; (b) §7.4 lists "the **structured-verdict-then-deterministic-text pattern**" among assets "Reusable largely as-is". Applied to a guard, a structured verdict that emits deterministic text *is* a guard composing a reply — precisely AD-21's prohibition. The reuse inventory carries that pattern forward without stating where it may and may not be applied. |
| A6.3 | H | FR46, NFR2, §13.2 | "distinguishable by the caller, not only in a log line" — exceeds the Spine's wording in the right direction. |
| A6.4 | H | FR55, NFR2 | At-least-once, Core-issued tenant+episode-scoped key, adapter honours it, and the "never silently suppressed as a duplicate" half. |
| A6.5 | H | FR63 | Late result named as a first-class recorded condition. |
| A6.6 | HQ | FR60, FR67, §10.4 ("Lifecycle is never read as success") | **Finding 3.** FR60 adds a construct the Spine does not contain: "pending, awaiting a named external input **with a deadline**". AD-13 fixes `pending` as awaiting a *named* external input and says nothing about a deadline. A deadline is an undeclared fourth fact about the lifecycle and carries a latent orchestration implication — *something* must act when it expires, and nothing in the PRD says who. If the Core acts on expiry, the Core has selected the next step (A1.1). Either delete the deadline or state that expiry produces a typed result to the Agent (FR45's first exit) and nothing else. |
| A6.7 | H | FR64, NFR1 | Clock/randomness/identifiers/environment/configuration via recorded means or pinned at episode start, and crash survival. |
| A7.1 | H | NFR3 | "rejected, not filtered — never a quietly empty result", with the full seven-record enumeration. |
| A7.2 | H | FR66, §4.3, §7.2 | Stated as a negative requirement in three places, exactly as B7 asks. |
| A7.3 | H | FR57, NFR11 | NFR11 adds "or any evidence export" — a correct extension of AD-24's product consequence. |
| A7.4 | H | FR75, NFR10, §13.2 | Addressable/removable by tenant, episode and age without reshaping the schema; "sensitive and health-adjacent material" acknowledged. |
| A7.5 | H | FR14 (final clause: "and its data-lifecycle requirements"), NFR10 | Captured in the authoring surface from V1, independent of the deferred executor. |
| A8.1 | H | FR21, FR22, FR26, NFR8 | Immutability, hard gate ("not advice"), rollback by selection ("no reconstruction, no migration"). |
| A8.2 | H | FR27, NFR7 | "Promoting a change MUST NOT alter conversations already running" — stated in the product, as A8.2 demands. |
| A8.3 | H | FR13 | One artifact; context, capability surface and policy all compiled from it; no independently authored prompt/tool-list/policy object. |
| A8.4 | H | FR18, FR24 | Both halves: unexpressible in the authoring surface *and* rejected by validation with an actionable message. |
| A8.5 | H | §6 Builder entry (verbatim four stages), FR9, FR11 | Compiling, enforcing and executing are nowhere Builder features. FR12 (burden instrumentation) is measurement of the Builder, not a fifth stage. |
| A9.1 | H | FR83, FR85, §8.10 preamble | "The Agent and Core never learn which channel an episode is on" verbatim; behavioural FRs are written channel-neutrally (spot-checked across §8.5–§8.8: none names a channel). |
| A9.2 | H | FR61, §4.3, §7.2 ("Architecturally forbidden, not merely descoped") | Includes the egress-within-an-initiated-episode carve-out. |
| A9.3 | H | FR84, S9 | V1 channel is inbound email/messaging — text, consistent with the Spine's declared scope. Voice explicitly out (§7.2). |
| A10.1 | S | Partially: FR15, FR49, FR50, FR68; §6 "Goal / obligation" | **Finding 4 (part 1's main gap).** The Spine's defining property of goals and obligations is that they are **typed Core state — readable by the Agent, asserted by the Core at resolution — "never only prompt text"**. The PRD never states this. §6 defines goal/obligation purely semantically ("What an episode is for, and what must be established before it can resolve"), and no requirement asserts that they are typed state rather than specification prose. FR43's general prompt-text prohibition covers it only by inference. Two product consequences are consequently missing: (a) the "dashboard-grade" surface of what a conversation is for and what is still outstanding — the V1 operator surface (FR79, FR80) is the divergence list and episode viewer only, with no outstanding-obligation view; (b) the Core's assertion of obligations *at resolution* as an enforcement point is implied by §10.1 and §3.2 but never required. Recommend an explicit FR: goals in play and obligations outstanding are typed Core state, readable by the Agent and asserted by the Core at resolution. |
| A10.2 | H | FR38, FR49; no "if unmet then do Y" rule appears anywhere | Honoured in substance — see F6 for the wording risk and the missing guard sentence. |
| A10.3 | H | FR68 | All five envelope fields plus the business-defined payload; §10 and E9 are written against them. |
| A10.4 | H | FR71 (guarantee, no timing claimed), §7.3 (inline validation listed as deferred), §10.1 (post-hoc computation) | Correctly worded as the guarantee and not the mechanism, exactly as A10.4 and B13 instruct. |

**Counts (47 constraints):** honoured **43** · honoured with qualification **3** (A2.1, A6.2, A6.6) · silent with a product consequence **1** (A10.1) · **violated 0**.

---

## Part 2 — Workflow-regression check (F1 – F11)

Per-site verdict. **CLEAN** = the PRD did not fall into the trap. **CLEAN / RISK** = not fallen into, but wording or a carried-forward asset admits the forbidden reading. **GAP** = the trap is not entered but the Spine's own guard against it is not carried forward, and the omission has a product consequence.

### F1 — AD-1's prohibition list read as a menu · **CLEAN**

No re-litigation anywhere. §4.3 converts the prohibition into a product boundary — "No business-level step sequences, transitions or control flow anywhere — not in the product, not in the specification, not in these requirements" — and §6 reproduces the forbidden vocabulary. Nothing in the PRD proposes "a little precedence table".

*Minor note, not a finding:* the PRD adopts the **onboarding** litmus test (§5) as its self-check but not AD-1's **per-mechanism** filter — "does this constrain the Agent, or decide its next step?". The extract recommends that sentence as the PRD's own filter, and it is the one tool that would resolve findings 4, 6 and 7 at authoring time. Adding it to §5 costs one line.

### F2 — durable steps read as a permitted order · **CLEAN**

The PRD nowhere describes "step 1 … step 2", and nowhere treats the step sequence as an ordering. "Durable step" appears only in its durability sense (NFR1 "Every model decision, authorized execution and evidence write is durable"; FR64; E8 "durable steps"). The word "step" otherwise appears only in Spine-sanctioned phrases ("the Agent's next step" — FR39, FR44, §6) or under negation: §1.1 "does not supply a per-business sequence of steps"; §4.3 "No business-level step sequences"; §7.4 "Each becomes a Core service, **none becomes a step**".

*Observation:* AD-12's guard sentence — "Step boundaries are a durability concern only; nothing may read the step sequence as a permitted order" — is not reproduced. Nothing in the PRD needs it today, but E8's charter ("durable steps") is where a story author would next read the sequence as an order, so it is worth one line in E8.

### F3 — business sub-states hung off the three-state lifecycle · **CLEAN (strongest guard in the document)**

FR60 forbids it in terms: "No business sub-states may be added to it — business outcome lives in goals, obligations and the resolution, never in lifecycle." Reinforced three further times: FR67 ("Lifecycle says nothing about whether the business got a good outcome. `pending` is not a failure and `closed` is not a win"); §10.4's anti-gaming guard ("Lifecycle is never read as success"); FR68/FR72 keeping outcome in the resolution envelope. No "qualified", "booked" or "awaiting docs" state appears anywhere. The four exemplar businesses (§2) are described by *request*, not by state.

The single addition to the lifecycle is FR60's "with a deadline" — recorded as Finding 3 under A6.6, since it adds a fact to `pending` rather than a business sub-state.

### F4 — the Runtime Interaction sequence diagram transcribed into PRD flows · **CLEAN**

No sequence, flow or `alt`-shaped branch is transcribed anywhere. The one place the PRD could have leaked an ordering — §12's epic table — pre-empts it explicitly: "Ordering below is dependency, **not** a behavioural sequence." The Builder's four stages (§6, A8.5) are a Spine-defined artifact lifecycle, not a business flow, and are reproduced verbatim rather than elaborated into steps.

### F5 — "when X is detected, reply with Y" · **CLEAN / RISK**

No requirement instructs a guard to compose a reply. FR44 forbids it directly and is the controlling requirement. Three risk sites, in descending order:

1. **§6 vocabulary — "Guard condition | A declared condition that overrides the ordinary conversational path and may end the episode."** This is the real exposure. The Spine's guard has exactly two outcomes — a typed constraint returned to the Agent, or a declared safety halt — and "overrides the ordinary conversational path" names neither, while importing path-control language AD-21 denies a guard ("never chooses the Agent's next step"). The vocabulary table therefore contradicts FR44, which it is meant to define. A story author reading §6 alone would build a router. Replace the definition with the Spine's closed outcomes.
2. **FR14 — "what overrides the ordinary conversational path"**, inside the expressive-capability list. The same phrase, now in the *authoring* surface, which makes it an F9 exposure too: an operator told they may declare "what overrides the ordinary conversational path" is being invited to describe a diversion, not a condition. FR44's own wording — "which guard conditions apply" — is the compliant phrasing.
3. **O9 — "The dental exemplar carries a mandatory override"**, and FR69's "an episode escalated on an urgency trigger". Both are coinages of trigger→behaviour shape. FR69 survives because the actor is the Agent and the subject is resolution *classification*, not reply composition. "Mandatory override" is defined nowhere in the PRD and should be re-expressed either as a guard condition plus a declared safety halt, or as an escalation condition.

### F6 — outstanding obligations turned into gating rules · **CLEAN / RISK, and the missing-guard case**

The PRD does **not** contain a rule of the form "if obligation unmet, do Y". The decision stays with the Agent: FR38 gives it "what information is still needed" and "whether to act, continue or respond"; FR49 forbids Agent-invented goals and goal decomposition; nothing anywhere tells the Agent or the Core what to do about an unmet obligation. No BANT-shaped qualification sequence appears, and the §2 segment set is deliberately anti-vertical ("These are not one workflow with four skins").

The risk is one inference deep, and concentrated in four phrasings:

- FR15: obligations are "**what must be true before an action**".
- §6: "what must be established **before it can resolve**".
- §10.1 (per-episode success criterion): "**obligations complete before any action**".
- §3.2: the Agent "knows what must be true before a request can resolve, and **will not resolve it until those obligations are met or explicitly waived**", and must "hold an unfinished request open … **driving toward what is missing**".

Read as *authorization* — the Core denies an effect whose contract's obligations are unsatisfied and returns a typed result — all four are compliant: they constrain the Agent, which F4's own guard permits ("an authorization branch inside the Core"), and §3.2's "will not resolve" is exactly AD-19's "asserted by the Core at resolution". Read as *precondition-derived orchestration* — the Core computing what is missing and driving the conversation toward it — they are the thing AD-1 bans by name. **The PRD never says which reading governs, and it does not carry AD-19's disambiguating sentence: "Holding them is not deciding with them: the Core never selects which goal is pursued or what to do about an unmet obligation."** That sentence belongs in §8.5 or alongside FR15. "Explicitly waived" (§3.2) is a second undefined term in the same sentence — who waives, and is a waiver a recorded object? — and compounds the ambiguity.

This is the single highest-value edit available in part 2: the PRD is substantively clean here and one sentence away from being unambiguously clean.

### F7 — resolution validation at close read as a terminal state with exit criteria · **CLEAN**

FR71 states the invariant (a resolution asserting an effect with no Core execution record is invalid) without claiming timing, and no requirement has validation select a recovery path. §7.3 lists "inline resolution validation as a shipped mechanism" among the deferrals, and §10.1 computes the criteria from the record post-hoc, so neither B13 nor F7 is breached. FR45/FR46 supply the typed-result return path generically.

### F8 — ordering or precedence imposed among the request kinds · **CLEAN / RISK**

No precedence table, and — see A2.1 — the PRD does not even enumerate the seven kinds, which removes the temptation structurally. Nothing says "clarify before effect" or "always retrieve first".

One risk site: **FR35** — "Freshness is declared per read and per capability contract, never globally. **A read that gates a side effect** MUST be fresh; conversational reads may tolerate bounded staleness." This is the only place in the PRD that states a relation between two request kinds, and it uses the word "gates". It is defensible: it is a *freshness property* conditional on a capability contract having declared a read as a precondition of its authorization, not an instruction that a read must precede an effect. But note that FR35 is **PRD-originated** — no constraint in extract section A requires it — and that a story author could implement "a read that gates a side effect" as a Core-sequenced retrieve-then-act, which is precondition-derived orchestration. Recommend re-anchoring FR35 to the capability contract: a contract may declare a freshness requirement on the evidence an effect depends on; it may not declare that a read precede it.

### F9 — the authoring surface quietly permitting a process description · **GAP (genuine, and the most actionable finding in this review)**

The artifact-level defences are complete and well stated: FR18 (sequencing unexpressible, validation rejects it with an actionable message), FR24 (validation rejects sequencing constructs with a comprehensible reason), FR8 (pre-filled starting points "MUST contain no behavioural sequence of any kind" and "MUST NOT be the source of agent behaviour"), FR19 (human-readable and diffable, "neither a generated prompt nor generated code"), §1.1 ("the authoring surface must make sequencing unexpressible").

What is missing is the **elicitation-side** half, which is where F9 actually bites. The Builder's remit is to get the operator to "describe how their business actually operates" (§1.4) via an open invitation (FR1) and adaptive interviewing (FR3, FR4, FR7). An operator asked how their business operates will narrate a process — "first I check the diary, then I quote them, then if they haven't paid in 14 days I chase" — because that is how operational knowledge is held. The PRD requires the Builder to surface contradictions (FR5) and to record a defect rather than invent a default (FR6), but **no requirement obliges the Builder to decompose a narrated process into context, policy, capability, authority, goal and obligation, and to persist none of its order.** The only backstop is FR18/FR24 rejecting sequencing at validation — i.e. the operator discovers at the gate that what they described cannot be expressed, with no requirement that the Builder has already re-derived it. That is an authoring UX that can quietly become a flow builder in its transcript-to-artifact step, which is F9 verbatim.

Compounding it: FR14's "what overrides the ordinary conversational path" (see F5) is the one item in the expressive-capability list phrased as a diversion rather than a condition.

Recommend one new FR in §8.1: where the operator describes a process, the Builder MUST re-derive it into declarative elements — context, rules, authorities, capability grants, goals, obligations, outcome expectations — surface the re-derivation to the operator for confirmation, and persist no ordering. This is also the requirement that makes FR18 reachable rather than merely enforced.

### F10 — requirements traceable to the old system's pipeline nodes without re-derivation · **CLEAN / RISK, with one gap**

§7.4 does this work explicitly and better than the extract requires. The fifteen-node pipeline is named "**Deliberately not carried forward**", with the correct diagnosis ("a hand-rolled agent loop with the agency removed, where the Core decides the next step") and the correct conversion rule: "What that system actually earned is an **inventory of Core guarantees** … Each becomes a Core service, **none becomes a step**." Spot-checking the inventory against the requirements, the re-derivations hold:

| Carried-forward asset | Re-derived as | Verdict |
|---|---|---|
| Deterministic post-execution validator | FR96 (safety check positioned before what it measures; proven non-vacuous) | Re-derived as a Core property, not a stage |
| Human-authorization interrupt | FR53 (confirmation recorded before an effect is authorized) | Re-derived as authorization |
| Off-thread tool execution | FR97 (capability code never blocks the request path; per-client timeouts) | Re-derived as a constraint |
| Degraded path distinguishable from success | FR46, FR45, §13.2 | Re-derived as a typed-result guarantee |
| Output check before anything reaches a person | FR33 (invalid provenance refused before it reaches the person) | Re-derived as provenance enforcement |
| Ship-gate-as-subprocess / selftest | FR22, FR25 | Re-derived as the validation gate |
| Typed tool-result contract | FR46, FR51 | Re-derived |
| One-core-many-front-doors | FR83–FR85 (channel adapters) | Re-derived |

Two items in the inventory are **not** re-derived, and both matter:

1. **"The structured-verdict-then-deterministic-text pattern" is listed as "Reusable largely as-is"** while FR44 forbids exactly that shape for guards. As a pattern for rendering, say, a typed refusal to an operator surface it is harmless; applied to a guard it is AD-21's prohibition in code. The reuse table states no boundary. (Also Finding 2 under A6.2.)
2. **"Bounded tool budgets" and "a stall detector with a wired handoff"** are named as Core guarantees the old system earned, and "budget" is named inside FR96, but **no requirement establishes either**. Consequently **nothing in the PRD gives the Agent loop a termination bound** — not §8.5, not E4, not E5. The Spine does not supply one either (it is not an A-constraint), so this is a PRD-level gap rather than a Spine divergence, but it is the one Core guarantee the old system demonstrably earned that the PRD drops. A stall detector in particular must be introduced carefully if introduced at all: "when stalled, hand off" is F5-shaped unless the detector returns a typed constraint and the Agent escalates (FR47).

No requirement anywhere is traceable to a node *name*, and no vertical flow (lead → qualify → book) survives: the §2 segment set was chosen to break exactly that shape, and §4.3 rules out every vertical framing of it.

### F11 — the litmus test used as the self-check · **CLEAN**

Quoted verbatim in §5 and applied as a standing per-requirement self-check in the §8 preamble ("the standing self-check from §5 applies to every one of them"), with §5's falsifiability table stating what would falsify each claim. This is one of the two sanctioned uses of the banned vocabulary.

**F-site summary:** F1 clean · F2 clean · F3 clean · F4 clean · **F5 clean/risk** · **F6 clean/risk + missing guard** · F7 clean · **F8 clean/risk** · **F9 gap** · **F10 clean/risk + gap** · F11 clean.

---

## Part 3 — Vocabulary compliance

### 3a. Banned vocabulary

Banned affirmative use: workflow, state machine, business transition graph, workflow language, primitive precedence table, execution graph, stage, node, "AgentSpec".

| Term | Occurrences | Verdict |
|---|---|---|
| workflow | §2 ("These are not one workflow with four skins"), §4.3 ("A workflow engine" — the *Not* column), §5 (litmus quotation), §6 (forbidden list) | **Compliant.** Every use is exclusionary, which §6 permits ("Where this document must refer to them, it does so only to exclude them"). Two sites beyond the two the review brief anticipates, both plainly negative. |
| state machine | §5 (litmus quotation), §6 (forbidden list) | Compliant. FR60 forbids business sub-states without using the term. |
| execution graph | §5 (litmus quotation), §6 (forbidden list) | Compliant. |
| business transition graph / workflow language / primitive precedence table | §6 forbidden list only (first two); third absent entirely | Compliant. |
| stage | **No occurrence.** §6's Builder entry uses arrows, not "stage" | Compliant — notable discipline, since A8.5's own gloss says "stages". |
| node | §6 (forbidden list); §7.4 ("the fixed **fifteen-node** pipeline") | **Compliant.** The §7.4 use names the legacy system in the passage that rejects it ("Deliberately not carried forward"). A third site beyond the brief's two, but exclusionary. |
| "AgentSpec" | **No occurrence.** "Business Specification" throughout | Compliant, including the Spine's unstated reason (name collision). |

No banned term is used affirmatively anywhere. "Pipeline" (not itself banned) appears only in §7.4's rejection of the old one.

### 3b. Drift — Spine terms used with a different meaning

| # | Term | Spine definition | PRD usage | Severity |
|---|---|---|---|---|
| D1 | **Guard** | "The verdict is enforced deterministically and its outcomes are **closed**: return a typed constraint to the Agent, or trigger a declared safety halt. A guard never composes a reply and never chooses the Agent's next step." | §6: "A declared condition that **overrides the ordinary conversational path** and may end the episode." FR14: "what overrides the ordinary conversational path." | **High.** Both closed outcomes dropped and replaced with path-control language. §6 contradicts FR44, which states the constraint correctly. Fix §6 and FR14 to the Spine's two outcomes. |
| D2 | **Goal / obligation** | "**typed Core state** — readable by the Agent, asserted by the Core at resolution. They are never only prompt text." | §6: "What an episode is for, and what must be established before it can resolve." No requirement states they are typed Core state. | **High.** Same finding as A10.1. The term's load-bearing property is absent from its definition. |
| D3 | **Evidence** | "typed records against a platform-owned schema", authored only by the Core | FR15 introduces "**diagnostic evidence**, which is gathered to support a judgement and has no fixed sufficient set" — conversationally gathered material, not Core-authored | **Medium.** A coinage that attaches the Spine's most tightly protected term to material its definition excludes. FR70's "the Agent cannot author evidence" and FR15's "diagnostic evidence" are one glossary away from contradicting each other. Rename to "diagnostic input" or "diagnostic basis". |
| D4 | **Validation suite** | The gate promotion must pass (AD-23) | FR22 uses "validation suite" correctly. FR25 introduces "**self-test**" — "Each business passes a self-test before deployment. A passing self-test is the unit of done" — and FR12/FR91 measure "time to a passing self-test" | **Medium.** Either "self-test" is a coined synonym for the validation suite (then use one term) or it is a second, undefined gate (then it needs a definition and a stated relationship to FR22). The term is inherited from the voice project's `selftest.py`, which is where the ambiguity comes from. |
| D5 | **Divergence log** | "The divergence log is the specification's error signal" | FR78 "divergence log" (correct); FR79, S10, E10 "classified divergence **list**" | **Low.** Reads as log = record, list = operator surface over it. Acceptable; say so once. |
| D6 | **Episode** | "one identity, one tenant, one lifecycle, one evidence record, **and one join key where it touches an external system of record**" | §6 drops the join key; FR86 states it separately | **Low.** No meaning change. |
| D7 | **`spec_defect` / `business_refusal` / `platform_error`** | Code identifiers | FR77 renders them as prose ("a specification defect", "a business refusal", "a platform error") | **None — correct.** Deliberate de-identifiering, consistent with the PRD's guarantee-not-mechanism rule. The three classes map exactly, and `spec_defect`'s gloss ("the compiled projections led the Agent to believe it was permitted") is reproduced faithfully. |

### 3c. Coinages introduced where the Spine has no term

Not drift, but new vocabulary a downstream reader meets with no Spine anchor: **decision authority classes** (FR16, S1 — refines "authority boundaries": informational / liability-bearing / state-changing), **consequence class** (FR52 — reversible / costs money / reaches a customer), **engine leaks** (FR89, §10.3), **validity floor** (FR93), **resolution-model strain** (FR90), **the two knowledge tiers** (S6, E6 — maps cleanly onto authoritative source vs. general domain knowledge), **mandatory override** (O9 — undefined; see F5), **explicitly waived** (§3.2 — undefined; see F6), **logical turn** (FR87 — channel-level, necessary). All are compatible with the Spine; the two undefined ones (mandatory override, explicitly waived) should be defined or removed.

The Spine's own term **Harness** is not used; **Core** is used throughout, which is the Spine's primary term. No issue.

---

## Part 4 — The thirteen deferrals (extract section B)

| # | Topic | Status in the PRD | Verdict |
|---|---|---|---|
| B1 | Resolution-kind enumeration | FR68 ("the enumeration of resolution kinds is deferred and emerges from running real episodes"), O4, §7.3 | **Left deferred.** Requirements written against the five-field envelope, as instructed. |
| B2 | Policy engine technology | §7.3 lists it; **no engine named anywhere** | Left deferred. |
| B3 | Durability engine | §7.3; NFR1 states recoverability as a guarantee; no engine, no Postgres, no DBOS | Left deferred. |
| B4 | Model routing and tiering | §7.3; E5 "tiering expressible but unpinned"; NFR12; §7.4's caution that a stronger model "increases fidelity to what the prompts say, never to what is true" | Left deferred; **no model or provider pinned**. |
| B5 | Retrieval architecture | §7.3; FR30–FR37 state grounding, pinning, precedence and reconstructibility only | Left deferred; no technique named. |
| B6 | **V1 channel** | **DECIDED: FR84 / S9 — inbound email/messaging**, with the rationale in §8.10 and all behaviour written channel-neutrally (FR83) | **Expected and correct** — explicitly assigned to the PRD by B6. |
| B7 | Long-term memory semantics | FR66, §4.3, §7.2 | Left deferred, correctly as a negative requirement. |
| B8 | Tenancy deployment model | §7.2, O8, §13.2 ("the isolation guarantee holds regardless of the topology eventually chosen") | Left open; the AD-17 guarantee is stated independently of topology, exactly as B8 asks. |
| B9 | Marketplace / extension distribution | §7.2 ("The adapter contract is the forward-compatible seam; distribution is later product work") | Left deferred, with the seam named. |
| B10 | Concrete specification field schema | §8.2 preamble, FR14 (expressive capability, no field names), O7 (including the fourteen-vs-thirteen discrepancy, left unresolved) | Left deferred. |
| B11 | Context assembly | §7.3 | **Left deferred, with one soft note:** §7.4 lists "deterministic context compaction" among assets "Reusable largely as-is", which leans on a deferred area. It is stated as a reuse posture rather than a requirement, and no FR mandates a compaction strategy, so this is not a decision — but it is the one place the PRD expresses a preference inside a deferral. |
| B12 | Retention policy / deletion executor | NFR10, FR75, §13.2 ("the capability may not be foreclosed, but no deletion SLA is promised") | Left deferred; capture and addressability correctly pulled forward to V1. |
| B13 | Inline resolution validation as a shipped mechanism | §7.3; FR71 phrased as the guarantee with no timing; §10.1 post-hoc | Left deferred, worded exactly as B13 instructs. |
| — | Model and provider (deliberately unpinned) | NFR12; no vendor named | Left unpinned. |

**No deferred topic was accidentally decided.** The only decision is B6, which was assigned to the PRD.

---

## Findings index

Critical: **none**.

1. **A2.1 / F8** — the seven request kinds are never enumerated; `clarify`, `respond` and `suspend` appear nowhere. Defensible as F8 hygiene; the "grant over seven kinds" consequence is left unstated.
2. **A6.2 / D1 / F5** — §6's guard-condition definition ("overrides the ordinary conversational path") drops the Spine's two closed outcomes and contradicts FR44. Highest-value single-line fix.
3. **A6.2 / F10** — §7.4 carries "the structured-verdict-then-deterministic-text pattern" forward as "reusable largely as-is" with no boundary; applied to a guard it is AD-21's prohibition.
4. **A6.6 / F3** — FR60 adds "with a deadline" to `pending`, which the Spine does not contain and which leaves expiry-handling unowned.
5. **A10.1 / D2** — goals and obligations are never stated to be typed Core state asserted by the Core at resolution; the inspectable outstanding-obligation surface that follows from it is absent from the V1 operator surface.
6. **F6** — AD-19's guard sentence ("Holding them is not deciding with them…") is not carried forward, leaving FR15 / §10.1 / §3.2's "before an action" phrasing open to a precondition-orchestration reading. "Explicitly waived" (§3.2) is undefined.
7. **F8** — FR35's "a read that gates a side effect" is the PRD's only inter-kind relation and is PRD-originated; re-anchor it to the capability contract's freshness requirement.
8. **F9** — no requirement obliges the Builder to re-derive a narrated process into declarative elements; FR18/FR24 reject sequencing only at the gate. The one genuine authoring-surface gap.
9. **F9 / F5** — FR14's "what overrides the ordinary conversational path" phrases an authoring item as a diversion rather than a condition.
10. **F10** — "bounded tool budget" and "stall detector with wired handoff" are named as earned Core guarantees but established by no requirement; the Agent loop has no stated termination bound anywhere in the PRD.
11. **D3 / D4** — "diagnostic evidence" collides with the Spine's protected "Evidence"; "self-test" (FR25) is either an unlabelled synonym for the validation suite or an undefined second gate.
12. **F1 (note)** — AD-1's per-mechanism filter ("does this constrain the Agent, or decide its next step?") is not adopted; it is the one tool that resolves findings 4, 6 and 7 at authoring time.

Recorded as strengths, not findings: A1.1 is defended four independent times; F3 is guarded four times; §7.4's conversion of the fifteen-node inventory into Core guarantees is more rigorous than the extract requires; FR43 binds the PRD itself ("no guarantee in this document rests on prompt text"); FR95 and FR96 state A5.3 and check non-vacuity more sharply than the Spine does.
