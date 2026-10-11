---
title: "Input Reconciliation — Brief + Brief Addendum vs PRD + PRD Addendum"
created: 2026-10-08
inputs:
  - extract-brief.md
  - extract-addendum.md
outputs_checked:
  - prd.md
  - addendum.md
purpose: "What the source material contained that the outputs silently dropped. Not what was excluded with a stated reason."
---

# Input Reconciliation — what fell through the cracks

**Method.** All four documents read in full. A source item counts as *carried* if the PRD or
its addendum states it, or states a reason for not stating it. It counts as a **gap** only if
it is absent with no acknowledgement — a silent drop. Items the PRD deliberately and visibly
excluded are listed under "Correctly handled" at the end, so the reader can tell the
difference.

**Tally: 49 gaps — 24 high, 13 medium-high, 11 medium, 1 low.** Items are numbered G1-G50;
G21 is numbered for completeness and is *not* a gap. Priority reflects whether losing the item
would damage the build (a requirement is now wrong or unimplementable) or the thinking behind it
(a decision becomes indistinguishable from an omission).

---

## 1. Qualitative and experiential intent the FR structure dropped

The brief's *inferable* experiential intent (extract-brief §12) survived surprisingly well:
"hold an unfinished request open … driving toward what is missing", "refuse with a reason",
"change something in the world", "reasoning is broad; authority is bounded", "never report
that something happened without evidence that it did", and "the normal case, not an edge case"
are all present, several verbatim. The losses are concentrated in the **addendum's** §10
verbatim list and in the *stance* statements — the sentences that say what kind of thing this
is, as opposed to what it does.

### G1 — "It is a primitive set, not a framework" — the product's self-definition — HIGH

The single sharpest character statement in the entire source package, absent from both outputs
(grep: zero hits for "primitive set").

> "the primitive set **refuses** things — **no reasoning unanchored to a declared goal, no
> decision outside an authority class, no claim without a source, no action without a
> contract, no episode without a terminal outcome** — **which means it is a primitive set, not
> a framework**." (extract-addendum §6.4, repeated verbatim in §10)

All five refusals exist in the PRD as scattered requirements (FR49, FR16, FR32, FR56, FR68).
What is gone is the *claim they jointly make*: that refusing is what distinguishes this from a
framework. An FR table can enumerate five prohibitions and still leave a reader thinking the
prohibitions are incidental hardening rather than the identity of the thing.

**Should live:** PRD body, §1.1 Centre of gravity, directly under "Reasoning is broad;
authority is bounded" — the two sentences are the same thought from opposite ends.

### G2 — "Both are subtractive" — the posture of the whole design — HIGH

> "**Both are subtractive** — they remove the model from the critical path for everything it is
> not uniquely good at." (extract-addendum §10, on Principles 1 and 2)

Absent. This is the *feel* of the architecture, and the PRD's model-in-charge framing reads as
its opposite: additive, model-forward. See G22 for the substantive half of this conflict.

**Should live:** PRD addendum, as part of the supersession note G22 requires. If Principle 1 is
genuinely superseded, the subtractive posture must be explicitly retired rather than simply
missing — otherwise nobody can tell whether it was decided against or forgotten.

### G3 — The user's own hard condition: no worse copy — HIGH

> existing competitors must "**not** become an excuse for building a worse copy. **Not an
> acceptable thesis**" (extract-addendum §2.1 R5, §10 — recorded as *user-stated*)

This is the project owner's stated acceptance condition for the whole product, and the reason
an entire candidate ("an AI receptionist that books appointments") was rejected by **hard
condition** rather than by evidence. Neither output contains it. A PRD that loses its owner's
veto condition cannot be checked against it.

**Should live:** PRD body, §5 Falsifiable posture — it is a third falsifier alongside the
architecture and usefulness claims.

### G4 — Breadth-not-niche, stated as the point of the product — HIGH

> "**The user does not need an unsaturated vertical** — the point is that the **same underlying
> product** is useful across many SMB contexts." (extract-addendum §2.2, §10)
> "**a new market category need not be proven**" (R17, §10)

The PRD's §4.3 forbids vertical framing as an *exclusion*, which is the defensive half. The
affirmative half — breadth is the thesis, and nobody owes anyone a proven market — is gone,
and with it the standing permission not to chase a gap in the market.

**Should live:** PRD body, §1.2 (the three framings table already holds "direction of travel"
statements) or §4.2 beside "No moat is claimed."

### G5 — "This principle must not be applied for elegance" — the working ethic — HIGH

> "this principle must **not** be applied for elegance. Selection comes from the actual job and
> its failure, latency and business constraints — and **the hot path must be measured first**."
> (extract-addendum §9.1, owner's caveat, explicitly "kept")

Absent (grep: zero hits for "elegance"). This is the project's anti-aestheticism rule and it is
the same discipline the repo's own CLAUDE.md records as a standing rule. Its loss is the
mechanism by which architecture-convenience reasoning re-enters (see G31).

**Should live:** PRD body, §5, as a standing self-check alongside the existing one.

### G6 — Tone is per-business configuration, deliberately not platform brand — MEDIUM-HIGH

The brief's one direct statement of agent voice is a *position*, not a field:

> "**Identity** — what the business is, **how it speaks, what it will not say**"
> (extract-brief §7, §12: "tone is per-business configuration, deliberately not a
> platform-level brand character")

The PRD carries the words — but buried as the first clause of FR14's fifteen-item run-on
sentence, where it reads as a schema field. The *decision* — that the platform has no default
voice and must not acquire one — is unstated. Nothing in either output prevents a later UX pass
from inventing a platform persona, which would silently override every business's identity
declaration.

**Should live:** PRD body — a one-line statement in §8.2 preamble, plus an explicit exclusion
row in §4.3 ("Not a branded assistant").

### G7 — "Recorded rather than written around" — the self-auditing ethic — MEDIUM

> "Recorded rather than written around, and explicitly not permitted to redirect the product."
> (extract-brief §3, on Market Honesty)

The PRD keeps "No moat is claimed" and "not merely technically impressive" — two of the three
representative lines of the brief's working ethic — and drops the third, which is the one that
describes the *method*. It is also the sentence the market-honesty guardrail hangs on (G25).

**Should live:** PRD addendum A2, which currently points at the market evidence with no
disposition rule attached.

### G8 — "Above that boundary, the system becomes a *fork*" — MEDIUM

> "**Customer ownership can extend as far as we can preserve a stable behavioural contract.
> Above that boundary, the system becomes a *fork* rather than an Agent Studio agent.**"
> (extract-addendum §9.4, quoted again in §10 as a character statement)

Absent (grep: zero hits for "fork"). It is both a crisp experiential image and the operative
answer to "how much can a customer change?". The PRD has FR58/FR59 (configuration vs leaf vs
platform release) but no notion that past a point the thing stops being theirs to call an Agent
Studio agent.

**Should live:** PRD body §8.6, one row; the full five-separations reasoning to the PRD addendum.

---

## 2. Load-bearing wording that lost its force in translation

### G9 — The two-causes diagnostic, the actual reason reviewability matters — MEDIUM-HIGH

**Source:**
> "**The specification must be a first-class, human-readable, diffable artifact.** Once the
> builder drafts it, a bad agent has two possible causes — **a bad specification or a bad core
> — and only a reviewable specification lets anyone tell which**." (extract-brief §4)

**PRD (FR19):**
> "The specification is human-readable and diffable. It is **neither a generated prompt nor
> generated code** — otherwise diffing behaviour, asserting over behaviour, reviewing a
> proposed change, reverting a regression and attributing an outcome to a version are all
> unavailable."

The PRD substitutes a list of five lost *capabilities* for the one *diagnostic* that makes them
matter. The source's version is also the thing O1 (who reviews the specification) is actually
about, and it is the premise of the entire divergence-classification scheme in §8.9 — FR77
classifies every denial as spec defect / business refusal / platform error, which is precisely
"two possible causes" generalised to three. Dropping the sentence severs FR19 from FR77.

**Should live:** PRD body, FR19 or the §8.3 preamble.

### G10 — "Control flow lives in the specification" vs "sequencing is unexpressible" — HIGH

**Source (a DECIDED resolution):**
> "**custom code exists as controlled leaves, never as arbitrary control flow.**" Control flow —
> "what the agent asks, in what order, action gates, escalation, completion — lives **in the
> specification only**: interpretable, diffable, assertable, promotable." (extract-addendum §5.2)
> "Control flow stays in the specification, where it can be **read, diffed, evaluated and
> reverted**." (extract-brief §7)

**PRD (FR18):**
> "The specification MUST NOT be able to express ordering or sequencing. The authoring surface
> makes sequencing unexpressible, and validation rejects any such construct."

This is not a flattening, it is a **reversal**, and it is unmarked. The source puts order
("what the agent asks, in what order") in the specification *because that is the only place it
is reviewable*; the PRD forbids the specification from expressing order at all and hands
sequencing to the model (FR38). Both positions are defensible. What is lost is that a decision
was taken the other way, for a stated reason — reviewability of sequence — which the PRD's
model now has no answer for. The PRD keeps FR59 ("custom code … may never be control flow")
from the same source paragraph, which makes the half-carry look accidental rather than chosen.

**Should live:** PRD addendum, as an explicit supersession of the C1 control-flow placement,
naming what replaces reviewable sequence. Related: G22.

### G11 — The pre-emptive gate lost its defining property — HIGH

**Source (structural change 3 of four):**
> "**Add a pre-emptive gate before goal recognition that can abort the episode**" — "Dental
> urgency interception **has no home in an 11-step pattern that starts at 'understand what the
> person wants'**." Any mention of pain, swelling, bleeding, fever or trauma escalates
> immediately "**and the explanation path is abandoned rather than continued**."
> (extract-addendum §6.6, §8.4)
> "Declared conditions that override the ordinary conversational path **before goal pursuit**,
> and **may end the episode regardless of what was asked**." (extract-brief §5)

**PRD (FR44):**
> "Guard conditions may be evaluated by a model; the verdict binds deterministically with closed
> outcomes. A guard **never composes a reply and never chooses the Agent's next step**."

FR44 specifies a guard's *epistemics* and says nothing about its *position* or its *power to
abort*. "Before goal recognition", "aborts the episode", and "the explanation path is abandoned
rather than continued" are all gone. FR96's "positioned before anything that mutates what it
measures" is a generic check-ordering rule, not pre-emption of goal pursuit. The §6 Vocabulary
entry ("may end the episode") is the only residue, and vocabulary is not a requirement.

**Should live:** PRD body, a new FR in §8.5: a guard fires before goal recognition, may
terminate the episode with a recorded outcome regardless of what was asked, and abandons rather
than resumes the path it interrupted. This is one of only four structural changes the stress
test demanded; it is the one least reflected.

### G12 — "Deterministic execution *is* the safety mechanism" — MEDIUM

> "Action safety stops being independent once execution is deterministic, because
> **deterministic execution *is* the safety mechanism**." And the forbidden cell: "fully agentic
> tool selection … **incompatible with bounded actions and deterministic execution; the cell
> that makes safety and evaluation both intractable**." (extract-addendum §3.2, §2.7, §5.5)

The PRD's §4.4 answers the reliability counter-argument with "declared intent with
deterministic, validated execution on the irreversible path" — close, and good. What it drops
is that this is a *structural* claim (safety is not a feature you add; it is what determinism
already is) and the flat prohibition on fully agentic tool selection, which sits in visible
tension with FR38's "the Agent decides … which capability to use."

**Should live:** PRD body §4.4 for the structural claim; the forbidden cell as an explicit row
in §4.3 or a note on FR38 distinguishing *proposing from a granted set* from *selecting tools*.

### G13 — The "Python-in-JSON" anti-goal and the contract proof test — MEDIUM-HIGH

> "**the evaluator asserts over the contract, never over the implementation.**" "This is why the
> schema never grows toward Python-in-JSON: it never expresses computation, only **sequence,
> condition and policy**." Declared anti-goal: "*a gigantic declarative schema representing
> every possible behaviour* — moving complexity from Python into JSON."
> (extract-addendum §5.3, §5.4, §2.7)

FR18 forbids *sequencing* in the schema. Nothing in either output forbids the schema expressing
*computation*, which is the named anti-goal — and FR14's expressive list (rules, eligibility,
pricing, timing, constraints) is exactly where computation creeps in. The proof test — assert
over the contract, never the implementation — has no home either, though FR95/FR96 are about
validation and are its natural neighbours.

**Should live:** PRD body, FR18 extended or a sibling FR; the proof test beside FR95.

### G14 — "Not utterance classification" — MEDIUM

> Capability primitive: "goal set with completion conditions (**Not utterance classification**)"
> (extract-brief §5)
> The morphological collapse behind it: "Given an explicit goal object plus a state machine over
> what the job still needs, intent classification is **redundant** — the structure already knows
> the turn and the gap. Real single axis: *does turn-level direction come from classifying the
> utterance, or from the structure of the unfinished job?*" (extract-addendum §3.2)

The parenthetical is a prohibition carrying a whole analysis behind it. The PRD has FR49 (goals
come only from the declared set) but nothing that says direction comes from the unfinished job
rather than from classifying the turn — and FR38 gives the Agent "what the person is trying to
accomplish" per turn, which is the classification side of that axis.

**Should live:** PRD addendum, with G22's supersession note.

### G15 — "No transaction at all" — why the garden centre is the strongest evidence — LOW

> "'nursery' in brief v1 was **mis-read** as childcare; it is a **plant nursery / garden
> centre**, and the correction **materially strengthens the diversity argument**, because that
> request involves **no transaction at all**." (extract-addendum §1, §2.5 R16)

The PRD's segment table gives the garden centre as "Diagnostic advice; ambiguous goal; a
liability boundary" — true, but it drops the property that makes this business load-bearing for
the generalisation claim: it is the one exemplar with no transaction, and therefore the one that
proves the platform is not a booking product in disguise.

**Should live:** PRD body, §2 segment table, one clause.

---

## 3. Substantive content with no home in either output

Answering the named checklist, in order.

### G16 — The capability primitives list, and "Built once, never per business" — MEDIUM

Source (extract-brief §5): thirteen primitives of the reusable core, framed as "**Built once,
never per business**" — goal set with completion conditions · guard conditions · obligation
tracking · diagnostic evidence gathering · grounded claim · rule evaluation · decision authority
classes · contracted action · escalation with reason class · episode lifecycle · resolution
record · episode evidence · evaluation.

Twelve map onto PRD requirements. Two things are gone:

1. **The framing** — the primitive set as a named, closed inventory built once. Without it,
   §8's FR groups look like a feature list, and nothing states that this inventory is what
   "engine leaks" (FR89) are leaks *of*.
2. **Rule evaluation has no FR**, and specifically its definition: "Declared predicates over
   collected information **and live external reads**." The "live external reads" half is the
   bridge between FR14's rules and FR35's freshness, and it exists in neither.

**Should live:** PRD body — the inventory as a short table in §6 or §8 preamble; rule evaluation
as a requirement in §8.2 or §8.5.

### G17 — The three-level variation contract — HIGH

> 1. "**Configuration / specification** handles normal variation — the expected path, covering
>    the great majority of cases."
> 2. "**A supported extension point** handles capability that recurs across businesses but is
>    structurally unlike configuration — a leaf behind a declared contract: **identity
>    verification, document intake, derived figures, a domain safety pack, a tool
>    implementation, a validator, a scorer**."
> 3. "**Custom implementation** handles genuinely novel capability, and is the exception, never
>    the workflow." The escape hatch "must be **intentional**." (extract-brief §7;
>    extract-addendum §5.1)

The PRD has level 1 (FR14, FR58) and level 3 (FR59). **Level 2 is missing as a contract.**
"Extension" exists as vocabulary and in FR56, but as an *adapter to an external system*, not as
the middle tier for recurring-but-unconfigurable capability — and FR58's "a genuinely new
semantic capability is a platform release" reads as collapsing level 2 into level 3-or-release.
The seven named extension-point examples appear nowhere. This is the governing answer to "what
varies per business", it is what FR89's classification (*should have been configuration* /
*justifies an extension point* / *genuinely novel*) is classifying *against*, and it is the
subject of a named falsifier (G28). FR89 currently classifies leaks against a taxonomy the PRD
never defines.

**Should live:** PRD body, §8.6, as a three-row table — it is cheap and it makes FR89 legible.

### G18 — The eleven specification surfaces, collapsed into one unaddressable sentence — MEDIUM-HIGH

Source (extract-brief §7) lists eleven named surfaces — Identity · Goals · Knowledge ·
Obligations · Diagnostic inputs · Rules · Authorities · Tools and actions · Guard conditions ·
Escalation policy · Evaluation criteria — each with a one-line gloss, framed as "**Per business,
and nothing else**."

FR14 contains all eleven and four more, as a **single fifteen-clause run-on sentence**. Nothing
is strictly lost in content, and the PRD's reason for not committing to a schema (O7) is sound.
But the surfaces lose their *names*, so no downstream story, test or architecture document can
cite one; and the "and nothing else" closure — the statement that this list is exhaustive — is
gone, which is the half that makes FR58 ("business configuration never changes Core semantics")
enforceable.

**Should live:** PRD body, FR14 rewritten as a named-row table with the closure statement
retained. This does not pre-empt O7: naming the surfaces is not fixing the field schema.

### G19 — Guard condition families — HIGH

> Candidate generic families: "**urgency**, **authorisation failure**, **policy violation**,
> **unsupported request**, **identity problem**, and any other declared guard." — "**The
> primitive is the override capability, not any one domain's use of it.**" (extract-brief §5)

Zero of the five families appear in either output. This matters more than a missing enum
normally would, because the per-vertical prohibition library was *rejected* (G34) on the grounds
that vertical knowledge must not enter the core — which leaves the generic families as the only
V1 answer to the stress test's "most safety-relevant finding". The PRD drops the replacement
while keeping the rejection.

Note the families are explicitly *candidate*, like the resolution enumeration — so the PRD's
pattern of carrying the envelope and deferring the enumeration applies cleanly here and was
simply not applied.

**Should live:** PRD body §8.5 beside FR44, carried as candidate families with the primitive
("the override capability, not any one domain's use of it") stated as the requirement.

### G20 — The four-artifact model, minus its mutability rules — MEDIUM

| Artifact | Holds | Mutability (source) |
|---|---|---|
| Specification | Intended behaviour | "Changed only by deliberate, reviewed promotion" |
| Evidence | "What actually happened (episodes, traces, outcomes)" | **Append-only** |
| Evaluation | "What we judged to be wrong, and why" | **"Append-only, versioned per agent version"** |
| Deliberate changes | "What we chose to promote into the spec" | "Reviewable, revertable, attributable" |

(extract-addendum §6.1)

The PRD's §8.3 preamble names all four in a clause and keeps the two best lines ("promotion is
a pull request on behaviour"; "make disagreement cheap to express and fast to propagate") — this
is one of the better carries in the document. What is dropped is the **mutability column**:
evidence append-only has no requirement (FR70-FR75 specify authorship and addressability, never
immutability), and **evaluation append-only, versioned per agent version** has no requirement at
all — FR20 only says criteria live in the spec. Without it, "attributing an outcome to a
version" (FR19's own justification) is unimplementable.

**Should live:** PRD body, §8.3 as a four-row table; the append-only properties as FRs in §8.8.

### G21 — The two claims under test — **no gap**

Carried in full in §5 with falsifiers, and the express/drive-behaviour distinction is repeated
throughout. One of the strongest parts of the translation.

### G22 — "Deterministic-first, LLM-on-escalation" — a DECIDED principle silently reversed — HIGH (highest)

**Source — a decided principle, with corollaries, a caveat and a derivation:**
> "**Principle 1 — Deterministic-first, LLM escalation (DECIDED as a principle).** Deterministic
> logic runs first; the LLM is invoked where deterministic logic cannot confidently resolve."
> Corollaries: "do not spend a model call generating a reply you already know after a successful
> tool call (template the known reply, LLM as fallback); **do not classify every turn if the job
> structure already supplies direction**." (extract-addendum §9.1)
> Derived from collapsing six counterintuitive combinations into two principles, "**Both are
> subtractive**". (extract-addendum §3.2)
> Also in the brief, as an open architecture question: "The **deterministic-first,
> LLM-on-escalation** principle has to become a concrete boundary." (extract-brief §11, which
> flags the tension explicitly: "in some tension with the PRD's 'Agent decides what to do.'
> **Worth resolving explicitly in the PRD.**")

**PRD:**
> "A model-in-charge Agent decides what to do next" (§1.1, declared "settled and not re-opened
> by this document")
> FR38: "The Agent decides: what the person is trying to accomplish; what information is still
> needed; **when to retrieve**; **which capability to use**; whether to act, continue or respond;
> whether to escalate; **how to phrase anything**."

FR38 hands the model precisely the three decisions Principle 1's corollaries reserved for
deterministic logic. Principle 2 ("the agent proposes, authoritative systems dispose") *is*
carried — it is the PRD's Core boundary, well preserved. Principle 1 is not carried, not
mentioned, and not retired. The PRD addendum A1 circles it ("Not every intelligent decision
needs the full Agent loop", plus two cautions) but frames it as a forward *opportunity* rather
than as a prior decision now overridden.

The brief's own extract instructed the PRD author to resolve this tension explicitly. It is not
resolved, not carried as an open item, and the reversal is invisible. Three consequences are
live: the cost argument in A1 is doing the work Principle 1's caveat forbade ("must not be
applied for elegance … the hot path must be measured first" — G5); the measurements that were
supposed to settle the boundary are missing (G28); and §1.1's "settled elsewhere" defers to
ARCHITECTURE-SPINE.md without stating that the spine's control model supersedes a recorded
principle.

**Should live:** PRD addendum, a named supersession section: Principle 1 as recorded, what
replaced it, and on what grounds. If the spine genuinely settled it, say so and cite it — the
cost of not saying so is that the next reader cannot tell a decision from an omission.

### G23 — The four structural changes: three carried, one partial — HIGH (for #3)

| # | Structural change (source) | PRD |
|---|---|---|
| 1 | Replace the resolution model | **Carried.** FR68 keeps the envelope; O4 defers the enumeration, consistent with the brief's own deferral |
| 2 | Support multi-goal episodes and goal switching | **Carried.** FR50, FR49 |
| 3 | **A pre-emptive gate before goal recognition that can abort the episode** | **Partial — the defining properties are gone.** See G11 |
| 4 | Decision authority classes, separately gated | **Carried well.** FR16, plus FR17 which preserves the cause-vs-fault finding sharply |

Non-structural change 6 (obligations vs diagnostic evidence) → FR15, carried. Change 7
(version-pinning) → FR30, carried with its reason. Change 5 (cross-session continuation) →
FR62, carried — but see G24 for its diagnosis.

### G24 — "A missing enum member silently defined a capability out of existence" — HIGH

> "**the absence of a `pending` outcome kind from the coach's first model is what hid the
> finding** [that cross-session continuation is in scope]. **A missing enum member silently
> defined a capability out of existence.**" (extract-addendum §2.5 R18, §6.5)

The *conclusion* is carried (FR62). The *diagnosis* — the most reusable methodological lesson in
the addendum — is not. It is directly live: **O4 defers the resolution-kind enumeration**, which
is the exact class of decision that caused the error last time. A deferred enum with no warning
attached is the same trap, re-armed.

**Should live:** PRD body, attached to O4 as its revisit rationale.

### G25 — The market-honesty guardrail — HIGH

> "The market evidence is recorded under *Market Honesty* and is deliberately **not permitted to
> steer the product toward hunting an unoccupied vertical**." / "Recorded rather than written
> around, and **explicitly not permitted to redirect the product**." (extract-brief §3)
> Standing instruction R17: "do **not** let it drag back toward 'find an empty vertical'."
> (extract-addendum §2.5)

Absent from both outputs (grep: zero for "Market Honesty", "unoccupied", "hunting"). The PRD
addendum A2 does the opposite of what the guardrail requires: it *carries the market evidence
forward* — "the arguments that most threaten the thesis, including the **vertical-beats-
horizontal evidence**" — and attaches **no disposition rule**. The evidence most likely to
redirect the product is preserved; the instruction forbidding it from doing so is not. This is
the single highest-consequence non-qualitative gap, because the guardrail exists precisely to
survive into the next document.

**Should live:** PRD addendum A2, as its opening rule. One sentence.

### G26 — The real moat, and what it implies about the usefulness claim — MEDIUM

> "**The real moat is not conversation quality or explainability — it is write access to the
> calendar with live capacity.**" ServiceTitan: "a **70% booking rate including capacity
> constraints vs 90% excluding them**" — "the dominant failure is that *the calendar had nothing
> to offer*, a business-rules and capacity problem, **not comprehension**. **No amount of rule
> transparency fixes it.**" (extract-addendum §4.7)

Absent. It is the best available external evidence bearing on the usefulness claim, and it cuts
against the product's centre of gravity: a 20-point gap attributable to capacity, not
understanding. The PRD's §10.2 does report "blocked by the business's own rules or capacity"
separately — the right instrument — but never states the prior that this category is where most
of the loss lives.

**Should live:** PRD addendum (market reasoning), cross-referenced from §10.2.

### G27 — Counterfactual replay: the one unoccupied trust cell, flagged for re-examination — HIGH

The source audits five candidate trust differentiators and finds four already shipped by
incumbents:

| Candidate | Status (source) |
|---|---|
| per-conversation review | Shipped (ServiceTitan scorecards) |
| approval-before-commit | "**Shipped as Weave's DEFAULT** for most verticals" |
| rule authoring | Shipped (ServiceTitan) |
| **counterfactual replay** — "show how a rule change would have altered past conversations" | "**ABSENT from every vendor examined — the only unoccupied cell**" |
| longitudinal quality | Shipped (supervision "Command Center") |

And then instructs the PRD author directly:

> "in the booking context it was judged worthless without calendar write access. **In a
> channel-independent platform that caveat does not obviously carry, which makes (d) the one
> trust feature worth re-examining for this PRD.**" (extract-addendum §8.2, §3.4)

Absent (grep: zero for "counterfactual"). An explicit "re-examine this in the PRD" was dropped.
It is also *nearly built*: the PRD already has immutable spec versions (FR21), durable episode
evidence (FR73), episode-pinned versions (FR27) and a divergence loop (§8.9) — counterfactual
replay is the obvious composition of those four, and §8.9's FR82 stops one step short of it.

Equally dropped is the companion finding that **approval-before-commit is table stakes, not a
differentiator** — the PRD's FR53 presents confirmation gating as a product strength with no
note that it is a competitor's default.

**Should live:** PRD body — a decision in §7.2 (explicitly out, with a reason) or an open item.
Silence is the one unacceptable outcome for something the source flagged for decision.

### G28 — The named falsifiers and measurements that were supposed to settle open questions — HIGH

The addendum records fourteen open unknowns, each with "what would settle it". The PRD's §8.11
programme carries three measurements (FR89-FR91) and the usefulness test (FR92-FR93) — a good
carry of open unknown 2. **Six further named, cheap, falsifiable measurements have no home:**

| Source unknown | The named test, quoted | Which PRD claim it tests |
|---|---|---|
| 4 — config or a DSL in disguise | "**count rules needing a new schema concept vs a new leaf**. More than ~1 new schema concept per customer means the config surface is growing into the forbidden DSL" | FR14, FR18, G17 — the three-level contract |
| 5 — does `intent_detect` earn its LLM call | measure "how often its classification **changes the route** versus what job structure alone would have chosen. **The one explicitly blocked deletion**" | FR38, G22 |
| 6 — I/O or LLM calls dominate the reply path | per-turn latency split by call site, "**emitted as structured episode telemetry, not logs**. If external I/O dominates, cutting [model calls] buys nothing and the work belongs at the data/caching layer" | NFR13 |
| 7 — do side-effect-gating reads happen once per episode | "Tag every external read with its consequence class; measure count and position. **If they occur per turn, the latency budget is not honest and the freshness model needs rework**" | FR35 |
| 8 — does tier-1 evidence need a judge | define the **five interaction-quality assertions** and assert them over "**~20 scripted episodes**… **If fewer than 4 of 5 can be asserted deterministically from the episode alone, the 'no judge needed' interpretation is wrong and evaluation gets much more expensive**" | **FR76** |
| 9 — is a joined episode cheap | one happy path end-to-end carrying "an **episode ID and the external join key**. If that cannot be produced cheaply, **Seam 1 is harder than assumed and must be scheduled, not assumed free**" | FR86, FR73 |

Unknown 8 is the sharpest loss: the PRD's **FR76 converts an interpretation into a requirement**
("every success criterion … computable from the episode record without a human reading a
transcript") while dropping the test that was supposed to establish whether it holds, and the
stated consequence if it does not. §10's entire no-human-review posture rests on it.

**Should live:** PRD body §8.11 (the programme is already a V1 deliverable — these are four more
rows), or the PRD addendum as an evaluation-planning section. Unknown 8's five assertions belong
beside FR76 as its acceptance test.

### G29 — Operator conversations: the second question was dropped — HIGH

FR94 mandates "two or three conversations with real small-business operators" and specifies one
probe (printed vs practised). The source specifies **two**, and the second has a stated
consequence for the whole operator surface:

> Open unknown 3: ask operators *"**how would you know the agent did a bad job?**"* and record
> the answer "**verbatim, without prompting**". If they cannot name one, "**the
> evidence→evaluation→promotion loop has no customer-side signal and must be rebuilt around our
> own assertions only.**" (extract-addendum §1, §12.1)

That is a falsifier for §8.9 in its entirety — FR77-FR82 assume the operator can recognise a
specification defect when shown one. One sentence in FR94 preserves it.

**Should live:** PRD body, FR94.

### G30 — The three seams, and the open circuit — MEDIUM-HIGH

> Governing V1 rule: "**build the narrowest valuable case, but refuse anything that structurally
> forecloses the hard case.**" The test is "not 'is it hard' but **cheap vs prohibitively
> expensive to retrofit**." "Exactly three things are not [additive]." … "These three bind as
> architecture constraints **even before the product is chosen**." (extract-addendum §9.2)
> Seam 1 evidence + identity: "**Un-recorded episodes are gone forever**; there is no backfill
> for a conversation that was never written down." Plus the two evidence tiers, and "**every
> episode needs a join key into the operator's system of record**, or 'later downstream outcome'
> is permanently unobtainable."
> And the diagnosis of the shipped system: "**build-time facts are durable, run-time facts are
> ephemeral.** `selftest_status` is a **build-time** quality gate standing in for a **run-time**
> quality signal… the improvement loop has **zero substrate; the circuit is physically open.**"

The PRD carries the *outcomes* (FR73 durable evidence, FR86 join key, §7.4 on missing
instrumentation) but not the seam framing, the retrofit test, or the selftest-as-proxy warning.
That last one is live: **FR25 makes "a passing self-test the unit of done for a built
business"** — re-enshrining exactly the build-time proxy the source identified as the open
circuit. The PRD also adds the run-time loop (§8.9), so this is probably fine in substance; but
nothing in the PRD notices the overlap, so nobody will check that FR25 is not again standing in
for a run-time signal.

Also absent: the **two evidence tiers** (interaction-quality — dense, immediate, deterministic;
hard outcomes — sparse, delayed, arriving from outside), which is the structure FR92's "real
inbound requests" measurement depends on.

**Should live:** PRD addendum for the seam framing and the retrofit test; PRD body for the two
evidence tiers (§8.8) and a note on FR25.

---

## 4. Rejected alternatives whose rationale is preserved nowhere

The addendum extract carries nineteen rejections (R1-R19) plus six must-stay-empty morphology
cells. **The PRD preserves the rationale of three** (R13 → FR93; R14 → §12; R12 → §10.2's
capacity clause). The rest are listed here. Flagged ⚠ where the source itself marked the reason
non-obvious.

### G31 — R7, the physio/Cliniko withdrawal, and the reopening of text-first — HIGH (highest)

> "The research correctly killed 'build another vertical AI receptionist/booking product' —
> which the user **never wanted** — but the coach then wrongly concluded 'therefore build a
> physio booking agent on Cliniko', **optimising for API accessibility and producing exactly the
> narrow vertical product the user was avoiding.**" Recorded as "**the third occurrence of the
> same bias**" — architecture-convenience masquerading as product judgment. Standing rule:
> research must answer "is there a broad SMB class of problems where a reusable conversational-
> agent architecture creates meaningful value", not "which vertical has the easiest public API".
> **Consequence: "text-first vs voice was REOPENED** as a DECIDED item, on the grounds that it
> may have been architecture-driven rather than product-driven. It was **not automatically
> reversed**." Governing replacement question: "**for the specific problem eventually chosen,
> where does the valuable interaction actually happen?**" (extract-addendum §2.2, §11.3)
> Market pressure on the same point: "inbound to these businesses is still **phone-led**, which
> is why **every funded competitor is voice-first** with text as the second channel."

⚠ NON-OBVIOUS, and the source calls it "the single most important rejection for this PRD".
Neither output mentions it. The PRD then selects its V1 channel (FR84, inbound email/messaging)
and justifies it in §8.10 on these grounds:

> "It is the operator's real inbound queue… Being genuinely asynchronous, it exercises pending
> episodes and cross-session resumption honestly… It also carries near-zero turn-latency
> pressure, which deliberately keeps the latency-as-correctness discipline of the voice project
> out of V1."

Two of those three reasons are *test-fitness and engineering-convenience* reasons — which is the
structure of the bias the standing rule was written to catch, now on its fourth occurrence and
with the rule that would have caught it absent from the document. The replacement question
("where does the valuable interaction actually happen?") is never asked, and the countervailing
fact (inbound is phone-led; every funded competitor is voice-first) is nowhere. The decision may
still be right — V1 is a validation phase and a channel is an adapter (FR85) — but it is
currently unexamined against the one rule written to examine it.

**Should live:** PRD body, §8.10 — the channel choice re-justified against "where does the
valuable interaction happen", with the phone-led counter-fact stated and answered. The bias
history belongs in the PRD addendum as a standing rule.

### G32 — R19, the positioning rejection — "the deepest rejection in the file" — HIGH

> The convergence thesis — Agent Studio as "the conversational intelligence and execution layer
> above the customer's systems, joined to them by a key" — survives as architecture but **not as
> a commercial position**: "**the intelligence layer on top of someone else's system of record
> is precisely the position the system-of-record owner bundles away.** The architecture decision
> was right for the reasons given; **it is simply not a commercial position.**"
> Four independently sufficient mechanisms: "it controls the write API — and can gate a third
> party's access to it"; "it owns distribution — the feature arrives as a toggle inside software
> the business already pays for"; "it owns the historical outcome data needed to score"; "it can
> price on outcome, because it alone observes the outcome."
> Corollary: "outcome pricing is **structurally easier for whoever owns the system of record**:
> **a third party without the join key cannot price that way at all.**"
> (extract-addendum §2.6, §4.8) ⚠ NON-OBVIOUS

The PRD keeps the architecture (FR36, external systems authoritative) and keeps "No moat is
claimed", and defers commercial packaging to O8. What is gone is the *specific* finding that
**this exact architectural position is the one structurally bundled away**, with its four
mechanisms. Consequences: O8 ("commercial packaging, pricing and tenancy topology … revisit
after the generalisation claim is tested") will be revisited by someone who no longer knows that
the obvious pricing model is structurally unavailable; and O6 (a visible per-business spend
ceiling) sits next to a dropped finding about why outcome pricing cannot be the alternative.

**Should live:** PRD addendum A2; the pricing corollary cross-referenced from O6 and O8.

### G33 — R1/R2/R4/R6, the use-case rejections — MEDIUM

Four candidate jobs were examined and closed, and the PRD never says a use case was chosen or
that alternatives were considered:

- **R1 — service/request qualification** (the owner's *original* top rank): "**Rejected on three
  independent strikes**" — incumbents own the system of record; "the buyer (support/ops) is a
  **cost centre** while C1/C3 sell to revenue centres"; and it "**maximises the hardest
  unresolved contradiction** — enterprise runtime-ownership demand". ⚠ the cost-centre and
  runtime-ownership strikes are invisible from the finished product.
- **R2 — lead qualification, architecturally**: a "**misaligned-interest** conversation needing
  adaptive probing, evasion handling and scepticism toward self-reported facts — **which refuses
  to be configuration**"; and "its **evaluation observability is the worst** — false negatives
  are invisible". ⚠ the source names the second as the load-bearing one. See G35.
- **R4 — appointment intake** ("had been promoted to leading hypothesis, **explicitly never
  selected**"): "**Closed as a commercial opportunity**" — see G26.
- **R6 — legal client intake**: "**Saturated eight weeks before the brief**" (Clio Grow AI,
  2026-08-20) and "the two systems most needed — Clio, MyCase — are **the two least open**."

Also: **"Internal operations" is NOT rejected — it is unexamined.** "flagged by a subagent as
'an unexamined third option'. It is not rejected; it is **unexamined**" — "**the only live
untested candidate class**." The PRD assumes inbound customer requests throughout and never
records that a live alternative class exists.

The interest-alignment finding behind R2 generalises and is the most portable of these:
"***Alignment, not domain, is the axis on which the conversational engine actually differs.***"
The PRD's anti-vertical stance is correct, but the axis that replaces domain is gone — which
matters, because every exemplar in §2 is aligned-interest, and the PRD nowhere states that
misaligned-interest conversations are out of the architecture's claim.

**Should live:** PRD addendum — a short rejected-candidates table; the alignment axis in the PRD
body (§2 or §4.3), since it bounds the generalisation claim.

### G34 — R8, the per-vertical prohibition library, and the scaling-axis reason — MEDIUM-HIGH

> *Proposed:* "the builder needs a **prohibition and escalation library per business category**",
> motivated by what the source calls "**the most safety-relevant finding of the stress test**":
> "the prohibition list and urgency triggers are the **least documented and most critical**
> content of a specification"; for the dental practice they exist "**in no document at all**";
> "Eliciting *'what must your agent never do'* by open question **will produce a dangerously
> short list.**"
> *Replaced by:* "a **generic, domain-neutral guardrail library in the core** … plus optional
> domain packs as extension points, never core architecture — and with **no packs in V1**."
> *Reason:* "a per-category library makes vertical knowledge a **core dependency**, reintroducing
> the vertical framing the project had just rejected, and **it scales as the number of categories
> rather than as the architecture**." (extract-addendum §2.3) ⚠ NON-OBVIOUS

The PRD keeps the motivation (§3.3, FR4) and both halves of the replacement (FR42; packs out per
§7.2 and O9). It drops **the reason** — and the reason is live, because **FR8 reintroduces the
shape**:

> FR8: "The Builder MAY offer optional pre-filled Business Specification starting points (for
> example 'dental practice', 'gym') that seed terminology, candidate requests, **questions worth
> asking and policies worth considering**."

FR8's guards are all about *behavioural sequence* ("MUST contain no behavioural sequence of any
kind"; "never a behaviour template"). None of them is about *vertical knowledge becoming a core
dependency that scales as the number of categories*, which is what R8 was rejected for. FR8 may
well be fine — a Builder-side, optional, editable seed is not a core dependency — but the test
it needs to pass is missing from the document, so nobody will apply it.

**Should live:** PRD body, as a guard clause on FR8 citing the scaling-axis test; the rejection
itself in the PRD addendum.

### G35 — R2's evaluation trap: invisible false negatives and drift toward strictness — HIGH

> "Where false negatives are invisible, an outcome-driven improvement loop **rewards drift toward
> strictness**: conversion among passed leads rises while total revenue falls. **Selection bias
> with a feedback loop attached, self-reinforcing.**" Counterweights — "**holdouts, forced random
> pass-through, human adjudication of rejections**". Stated as a rule: "**the evaluation
> architecture is use-case-specific even where the execution architecture is not**", and "**a
> candidate with no feasible counterweight must not be chosen** — its improvement loop actively
> degrades the business." (extract-addendum §8.10)

Recorded as generalising beyond the rejected candidate, and it applies squarely to the PRD's own
improvement loop: **FR78 — "Only specification defects enter the specification backlog"** — means
a refusal that *should* have been a resolution produces no signal, because it was classified a
business refusal and closed. The loop learns from permissions it got wrong and never from
refusals it got wrong. §10.4's anti-gaming table has six guards and not this one; none of the
three counterweights appears in either output.

**Should live:** PRD body — §10.4 as a seventh guard, and an FR in §8.9 requiring that
correct-looking refusals be sampled or adjudicated. This is the most consequential single
rejection-rationale loss for the build, because the loop it affects is already specified.

### G36 — R5, "an AI receptionist that books appointments", rejected by hard condition — HIGH

Covered as G3; recorded here as a rejection so the mapping is complete. The rejection *and* its
authority (user-stated hard condition, not evidence) are both absent.

### G37 — R9, the compiler framing: the argument, the trap, and the open fork — MEDIUM-HIGH

> "Of twelve claimed advantages of generated code, only **1 (customer ownership/portability), 4
> (enterprise trust story), 5 (deployment into the customer's VPC), 12 (offline/self-hosted
> execution)** genuinely require an artifact — **and all four are the same property.**"
> "**The compiler model has an unstated precondition — nobody ever edits the generated output.**
> One in-place tweak… and regeneration destroys the work; the compiler collapses into a
> **one-shot scaffolder**." Holding it requires "either airtight round-tripping or a
> read-only-generated-code contract **with teeth**." ⚠ NON-OBVIOUS
> **Orthogonality warning, carried verbatim in the source:** "'no generated application code' and
> 'one process serves everyone' are **orthogonal concerns and must not be coupled**… **Nothing in
> the session proved multi-tenancy**, and nothing about adopting a shared runtime requires it."
> Plus explicit keep/replace evidence conditions, both directions. (extract-addendum §2.4, §3.5)

The PRD carries the *conclusion* (FR19: neither a generated prompt nor generated code) and none
of the argument. The fork is listed in the source as "**not finally decided**"; the PRD has no
open item for it, so a decided-looking FR19 now stands where the source had a live fork with
recorded falsification conditions on both sides.

The orthogonality warning is the most practically dangerous loss: §7.4 declares "**process-level
isolation between deployed Agents is permanent**" (a deployment-topology commitment) in the same
document where §7.2 puts multi-tenant hosting out of scope and NFR3 puts tenant identity in.
Those three are consistent *if* execution model and deployment topology stay orthogonal — which
is exactly the discipline the dropped warning names.

**Should live:** PRD addendum — the triage, the precondition trap, the keep/replace conditions,
and the orthogonality warning. The fork as an open item (O-series) in the PRD body.

### G38 — R10/R11, the resolution-model history — MEDIUM-HIGH

> R10: fixed disposition set **answered | action taken | escalated | out of scope** — "**Too
> appointment-specific.**"
> R11: first constrained outcome model **fulfilled | committed | informed | deferred | refused** —
> "**fulfilled/committed did not separate cleanly** and **deferred was carrying three unrelated
> meanings.**" (extract-addendum §2.5, §6.5)

Two enumerations were tried and failed for two specific, nameable reasons. O4 defers the
enumeration and says only "candidate families exist but are provisional". The next person to
propose an enumeration will re-propose "deferred", because the reason it failed is recorded
nowhere they will look. Combined with G24 (a missing enum member hid a whole capability), O4 is
currently the least-defended deferral in the document.

**Should live:** PRD body, attached to O4; three lines.

### G39 — The morphology's must-stay-empty cells — MEDIUM-HIGH as a set

Six cells the source says must stay empty, "empty **on purpose**, documented" (extract-addendum
§2.7), plus two more:

| Cell | Reason, quoted | In PRD? |
|---|---|---|
| external workflow engine | "Becoming a workflow platform was explicitly refused" | **Yes** — §4.3 |
| automatic / threshold-automatic behaviour promotion | "Silent learning was rejected" | **Yes** — FR29 |
| arbitrary control flow in custom code | destroys evaluability | **Yes** — FR59 |
| model-based turn boundary / streaming-continuous | "The whole axis is a voice artifact" | n/a — channel |
| **fully agentic tool selection** | "**Incompatible with bounded actions and deterministic execution; the cell that makes safety and evaluation both intractable**" | **No** — and in tension with FR38 |
| **synchronous per-turn evaluation** | "**Never put measurement on the reply path** to learn what a recorded episode yields afterwards" | **No** |
| **LLM-generated personalisation** | "**Buys warmth, costs a call, adds variance to a reply otherwise controlled**" | Partly — FR66 covers cross-episode memory, not reply-level variance |
| **a declarative schema that expresses computation** | the "Python-in-JSON" anti-goal | **No** — see G13 |

Four cheap one-line prohibitions, each with its reason, absent. Each is the kind of thing
reintroduced by a well-meaning later contributor precisely because no document forbids it.

**Should live:** PRD body, §4.3 as additional rows — the table already exists and is the right
shape.

### G40 — The regulatory pattern, and an open item that asserts a silence the sources do not have — HIGH

> Three bar opinions, all read "**via secondary summaries; the opinions were not fetched
> first-hand**" (explicit evidence gap): **Alabama Formal Op. 2026-01** (a chatbot giving
> specific advice without an "I am not an attorney" disclaimer and without review may be UPL; the
> deploying professional is liable); **Oregon Op. 2026-208** (permitted if the professional stays
> competent and "**supervises the vendor as a nonlawyer assistant**", discloses nonlawyer status,
> protects prospective-client confidences); **Florida Op. 24-1** (disclose AI; the professional
> owns everything the bot says; the bot must screen conflicts and avoid contacting represented
> parties). Derived product requirements: "**AI disclosure on every channel**; collect-and-screen
> only, no advice; conflicts check before substantive intake; the vendor is contractually a
> supervised nonlawyer assistant with no training on client data."
> Also: "~**45% of salon clients are not** comfortable with an AI receptionist" — recorded as "a
> design input". (extract-addendum §8.11, §8.12, §4.3)

The PRD's **O3 states: "No identity-disclosure position exists in any source."** That is
incorrect. Three cited opinions in the source material all require AI disclosure, one derives
"AI disclosure on every channel" as a product requirement, and a consumer-acceptance figure is
explicitly flagged as a design input. An open item that asserts a silence which the sources do
not have is worse than a gap: it tells the next reader not to go looking.

The *caveat* must travel with the content — the opinions were read via secondary summaries, which
is why they are evidence for a position rather than a legal conclusion.

**Should live:** PRD body — O3 corrected to state that the sources *do* point one way (disclose),
with the secondary-summary caveat; the regulatory pattern and the consumer figure in the PRD
addendum, cross-referenced from O9.

### G41 — Research-integrity rule, and the one defensible number — MEDIUM

> "when a statistic is the exact number needed to justify a purchase, **check who sells the
> alternative before citing it**; and treat a page that *claims* to summarise a primary community
> corpus, without linking a single thread, as **fabricated until a thread is produced**." Called
> "**the most reusable lesson in the file**." Mechanism: "**Swiss Monkey sells remote human dental
> front-office staffing — the product those statistics argue for.**"
> "**Most defensible independent-ish figure: CallRail, Jan-2025, over 1.1M leads**" — missed-call
> rates **32% healthcare, 28% legal, 14% home services, 9% real estate** — "**far below the 62%
> the category sells on**, i.e. the industry's headline missed-call number is **inflated by
> roughly a factor of two**." (extract-addendum §4.3, §4.9)

The PRD's §3.4 carries the *instance* ("at least one vendor selling human staffing publishes
fabricated AI-abandonment statistics") and drops the *rule*. It also drops the one caveated,
usable figure — while asserting "No quantified pain figure appears in this document by choice."
That is marginally overstated: a defensible-with-caveats figure exists and was not used. Stating
that would be stronger than implying none exists.

**Should live:** PRD addendum A2 for the rule; §3.4 adjusted to say a caveated figure exists and
why it is still not quoted as a target.

---

## 5. Flagged tensions the PRD neither resolved nor carried

The brief named five tensions explicitly for the PRD author (extract-brief §11). **Three are
handled well**, and that deserves recording:

- *Minimal builder vs elicitation being the hard problem* — **resolved**, cleanly: §8.1's
  "minimal burden and interface complexity *for the operator*, never minimal reasoning *by the
  Builder*", plus FR4-FR7 and E2 marked "Highest — this is the product risk".
- *Specification readable vs who reads it* — **carried as O1** with a revisit condition.
- *V1 includes its own proof* — **resolved**: S11, FR88-FR94, E12 marked "Highest". The brief
  warned this "should not be quietly dropped as 'not product'"; it was not.

The remaining two, plus five from the addendum:

### G42 — Broad reasoning vs deterministic-first — HIGH

The brief's tension #2, named and handed to the PRD to resolve. Neither resolved nor carried.
Full treatment at G22.

### G43 — Market honesty vs building anyway — HIGH

The brief's tension #4: it "records that every narrow inbound job is bundled by system-of-record
owners with structural advantages, claims no moat, and proceeds — with an explicit rule against
letting that evidence redirect the product." The PRD keeps the *proceeding* and the *no moat*,
drops the rule (G25) and the structural finding (G32). The tension is not resolved — it is
dissolved by removing one side of it.

### G44 — The residual commercial contradiction — MEDIUM-HIGH

> "the **architectural** contradiction dissolved, the **commercial** one (ownership) did not."
> Resolution that did hold: "**customer ownership and runtime ownership are separate concepts.**"
> Current favoured boundary, "**explicitly not final**": "the customer owns the agent definition +
> their data + the deployment choice; Agent Studio owns the core runtime and the evolution of
> behaviour; extensions are customer-controlled leaves behind stable contracts." Kept because it
> was "**derived from a constraint, not chosen by preference**." (extract-addendum §9.4)

The PRD has O8 (commercial packaging deferred) but never names the residual contradiction, never
states the ownership separation, and never carries the boundary (see also G8). The settling test
also has no home: open unknown 11 — "ask directly: *would you accept a hosted runtime holding
your conversation data?* A clear yes keeps the contradiction dormant and **settles the
generated-code fork for V1**." That is a third question for FR94's operator conversations, and
it would settle G37's open fork for free.

**Should live:** PRD body — the ownership separation in §6 vocabulary; the question added to
FR94. PRD addendum for the boundary gradient.

### G45 — The latency thread rests on an unmeasured premise — HIGH

> "because the agent holds no authoritative state, decisions must be made against **freshly read**
> external state, so **external tool I/O may dominate the reply path rather than sequential LLM
> calls** — which means the whole 'where does intelligence live / reduce LLM calls' thread rests
> on an **unmeasured premise**, and **observability must precede optimisation**."
> And the payoff that makes the budget work: "side-effect-gating reads **happen once, near the end
> of an episode, not on every turn**, and **that is what makes the latency budget honest**."
> Flagged: "**if side-effect-gating reads turn out to occur per turn, the latency budget is not
> honest and the freshness model needs rework.**" (extract-addendum §9.2, §9.3)

NFR13 (no latency target, instrument from day one) is broadly consistent and well reasoned. What
is dropped is the *reason* — and with it, the named condition under which **FR35's freshness
model fails**. FR35 declares freshness per read and per contract; nothing in the PRD states the
assumption that makes it affordable (gating reads cluster at episode end) or the measurement
that tests it. §8.10 also justifies the channel choice partly on removing latency pressure,
which makes this the measurement least likely to get run.

**Should live:** PRD body — the premise as a note on FR35, the measurement as a row in §8.11.

### G46 — Reuse of the shipped engine: a named cheap experiment, replaced by a verdict — MEDIUM-HIGH

> Open question, **unanswered**: "**is the existing voice boilerplate genuinely reusable after
> stripping the modality-specific machinery?**" Named experiment: "produce a text-only cut… then
> measure the resulting line count of `nodes.py` and whether the selftest still passes."
> **Falsifier:** "if what remains is still a **1000+ line monolith** with coupling that resists
> the subsystem split, '**evolve rather than discard**' is **falsified and a clean
> reimplementation is the cheaper path**."
> And on the per-node predictions: this "**is not a refactor plan**: it is a **prediction recorded
> so it can be checked later**, and **no node is to be deleted on its authority.**"
> (extract-addendum §3.6, §11.2)

The PRD's §7.4 instead issues a confident four-posture verdict — reusable as-is / concept
transfers / not reusable / **"deliberately not carried forward: the fixed fifteen-node
pipeline"** — without running the experiment, citing it, or noting that the source explicitly
forbade acting on the predictions' authority. The verdict may be right and §7.4 is otherwise one
of the document's strongest sections. But a cheap, named, falsifiable test was available and was
replaced by a judgement, and the instruction not to do that is the thing that got dropped.

**Should live:** PRD body — §7.4 noting the experiment as the confirmation step; or an open item.

### G47 — Per-tenant channel registration friction — MEDIUM-HIGH

> "**US A2P 10DLC is mandatory**: brand **$46 one-time**; campaign **$15 one-time + $10/mo**…
> **2026 tightening** includes **EIN ≥15 days**, carrier-verifiable opt-in URLs, and **Reseller ID
> mandatory when registering on behalf of another entity**. Consequence: **per-tenant onboarding
> friction that bundled incumbents absorb and a solo developer would not.**"
> "Region forks GTM: **US/UK/CA/AU/N-Europe are SMS-primary**; **WhatsApp dominates
> LatAm/S-Europe/India/MEA**." WhatsApp: from 2026-02-16 Meta charges "AI Providers"
> **$0.0691/message** for non-template messages — "recorded as **tail risk**."
> Listed as onboarding friction point 4. (extract-addendum §4.4, §7)

The PRD selects "**inbound email / messaging**" as the V1 channel (S9, FR84) and says nothing
about per-tenant channel registration. If "messaging" includes SMS, this is a costed, dated,
mandatory onboarding step landing directly on FR91's setup-effort measurement and on E11
(currently rated "Low" risk). If it means email only, saying so removes the exposure in one
clause. Either way the silence is the problem.

**Should live:** PRD body — scope the word "messaging" in FR84, and name the registration
friction in §8.10 or as an open item.

### G48 — Per-episode unit economics: the evidence record omits the fields — MEDIUM-HIGH

> Open unknown 12: "**Count per episode: turns, LLM calls, tool calls, tokens, cost; store on the
> episode record. First real unit-economics number, replacing a guess.**" (extract-addendum §12.1)

NFR14 instruments cost and §7.4 mentions "latency, tokens, cost" in prose — but **FR73**, the
requirement that defines what an episode record holds, lists "turns, retrievals, decisions,
actions, authorities exercised, errors and timings" and omits **LLM calls, tool calls, tokens and
cost**. The requirement that would make NFR14 implementable does not contain the fields NFR14
needs. This is the one gap in this report that is a plain defect rather than a lost idea.

**Should live:** PRD body, FR73 — four words.

### G49 — Consumer non-acceptance as a design input — MEDIUM

> "Consumer-side (end caller) acceptance, **vendor-run survey (Zenoti's own)**: '55% of salon and
> 71% of medspa clients' comfortable with an AI receptionist — **so ~45% of salon clients are
> not**." Listed as item 12: "**Consumer non-acceptance is a design input.**"
> (extract-addendum §1, §8.12)

Absent. It is the only requester-side evidence in the whole package, and the brief separately
flags that *no* requester-side satisfaction metric exists anywhere (extract-brief §9 GAPS). The
PRD's §10 is entirely episode-record-computable by design — a defensible choice — but it is made
without noting that roughly two in five requesters may not want to be talking to the thing at
all, which bears on O3 and on FR92's "real inbound requests".

**Should live:** PRD addendum (with the vendor-survey caveat attached), cross-referenced from O3.

### G50 — "Shipped-and-fenced": trust as a configuration artifact — MEDIUM

> "**Shipped-and-FENCED, not shipped-and-dark.** Both public vendors fence the agent to
> **overflow and after-hours by default** and expand 'incrementally' — management's own words."
> INTERPRETATION: "operators enable it in the window where a mistake costs least; **that fencing
> is a trust deficit expressed as configuration**." Direct product implication recorded in the
> source: "a platform asking a business to hand an Agent its real work **must earn the
> un-fencing**." The brief calls it "the one latent wedge the brief surfaces without claiming."
> (extract-addendum §4.6, §8.1; extract-brief §3)

Absent from both outputs. It is the sharpest available characterisation of what the operator
actually buys, it is a quotable experiential line, and the brief names it as the one latent
wedge. The PRD's §4.4 answers a *reliability* counter-argument; this is the *adoption* version of
the same point, and it names the thing V1 would have to earn.

**Should live:** PRD body §4.4 or §2 (the Business Operator's relationship to the product); the
evidence in the PRD addendum.

---

## Correctly handled — recorded so gaps are distinguishable from decisions

So that this report is not read as a complaint, these source items were carried accurately, or
excluded with a stated reason:

- The brief's problem statement, root cause, five coping-strategy failure modes and the
  obligation discriminator — carried near-verbatim (§3).
- The four-things-a-retrieval-chatbot-cannot-do list — verbatim (§3.2).
- Both claims under test, with falsification conditions (§5) — one of the best carries.
- The three generalisation measurements, the usefulness test, and the **validity floor** as a
  test concept rather than a product metric (FR93) — honours R13 exactly.
- All six of the brief's counter-metrics and anti-gaming guards (§10.4), including the
  agent-failure-vs-business-constraint separation *with its reason*.
- Zero numeric targets, with the reason stated rather than the omission hidden (§10 preamble).
- "No primary operator evidence obtainable" + the contaminated public record + the operator
  conversations as an outstanding action rather than an open question (§3.4, FR94).
- Cause vs fault, preserved sharply and with its example (FR17) — the stress test's sharpest new
  finding, intact.
- Obligations vs diagnostic evidence (FR15); authority classes (FR16); version-pinning *with its
  reason* (FR30); the two knowledge tiers (FR32, FR34); the three orthogonal dimensions —
  lifecycle, resolution, action evidence — kept distinct and non-conflatable (FR60, FR67, FR72).
- Principle 2 ("the agent proposes, authoritative systems dispose") — carried as the Core
  boundary throughout §8.5, and strengthened (FR45's two exits, FR46's caller-visible
  degradation).
- "Never improvise a rule" (FR6, FR48); escalation as declared success (FR69); the five generic
  guardrails verbatim (FR42).
- The builder's reversal into scope, with the user's sentence intact (§12: "without it this is a
  runtime plus an assertion that it can be configured").
- The anti-positioning set (§4.3), extended with the template-library row the brief did not
  have — correctly flagged in extract-brief as the PRD's own addition.
- Deliberate deferrals listed as deferrals (§7.3) rather than silently omitted, and the open
  items (§11) each given a revisit condition.
- Provider agnosticism preserved as a hard boundary in both documents, including against the PRD
  addendum's own cost argument.
