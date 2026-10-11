---
title: "Adversarial Review — Agent Studio PRD V1"
status: review
created: 2026-10-08
target: prd.md (567 lines) + addendum.md
reviewer: adversarial
---

# Adversarial Review — Agent Studio PRD V1

**Scope honoured.** The control model, the Core/Agent split, the absence of a workflow
engine, the deferred policy/durability/retrieval engines and the deliberate absence of
numeric targets are all treated as settled and are not attacked. Nothing below asks for
an invented number. Everything below attacks what the PRD itself chose to assert.

**Overall verdict.** This is a well-disciplined positioning and boundaries document and a
weak build-ready specification. Its intellectual honesty is real but asymmetric: it is
rigorous about what it refuses to claim and vague about what it promises to deliver. Two
structural faults dominate. First, the PRD's error signal (the divergence list) can only
see failures the Core *blocked*, which makes the operator's only surface blind to the
dominant failure mode of a reasoning agent — being confidently wrong inside its authority.
Second, the epic the PRD names as its highest risk (E2, elicitation) is the only major
epic with **no quality criterion anywhere in §10**: the PRD instruments the easy half of
elicitation (burden, FR12) and leaves the risky half (did we actually extract the
undocumented rules) unmeasured and untestable.

Severity key: **critical** = V1 cannot be built or cannot go live as written;
**high** = an implementer will invent product decisions the PRD owns; **medium** = real
gap with a cheap fix; **low** = hygiene.

---

## 1. Is this actually build-ready?

Short answer: the Core/evidence/lifecycle half (FR38–FR76) is close to build-ready — those
requirements are mostly typed, binary and checkable. The Builder half, the validation half
and the grounding-enforcement half are not. Below are the five least buildable
requirements as written, then a list of smaller invention sites.

### F1.1 — FR32 + FR33 + NFR5: grounding enforcement is specified as a gate but is an open research problem, and the gate as written is vacuous. — **critical**

> **FR32** Every business-authoritative fact — prices, policies, hours, availability,
> eligibility, what the business sells and promises — MUST be grounded in a declared,
> version-pinned source. The Agent may never invent one.

> **FR33** … a claim naming an unissued, altered or cross-tenant reference is refused
> before it reaches the person.

These two are not the same requirement, and the PRD reads as though they are. FR33 is
buildable and cheap: it is a referential-integrity check on reference tokens. FR32 is a
hallucination-detection requirement and is not buildable as a gate. The gap between them
is the whole problem: **an Agent that invents a price and cites nothing names no reference,
so FR33 passes it through untouched.** The only failure FR33 catches is a forged token —
which is the least likely way a model gets a price wrong.

An implementer must therefore invent, with no guidance: (a) what a "business-authoritative
fact" is in free prose (is "we're usually pretty flexible about that" a policy claim?);
(b) a claim-extraction step over the drafted reply; (c) a binding step from each extracted
claim to an issued reference; (d) what happens when extraction is uncertain — block the
reply, strip the sentence, or escalate; (e) whether this check is itself a model call,
which would put an unbudgeted model call on the reply path. None of these is an
architecture decision the Spine owns. They are product behaviour.

**Fix.** Split the requirement explicitly. Keep FR33 as the deterministic unforgeability
gate. Replace FR32's enforcement framing with two separate requirements: an authoring-side
obligation (the specification declares which claim classes are grounding-required) and an
evaluation-side obligation (ungrounded authoritative claims are *detected and counted* in
evidence, with the detector's own false-negative rate a named unknown). Then state plainly
in §13.1 that V1 cannot prevent an invented fact, only detect and measure a subset of them.
That is still a defensible product. Pretending FR32 is a gate is not.

### F1.2 — FR23: "granted but always denied" detection is presented as a hard gate over a deliberately unspecified policy representation. — **high**

> **FR23** Validation MUST detect a capability that is granted but which policy will always
> deny, and block promotion.

As written this is a static satisfiability question: does there exist any reachable state
in which this capability's authority and confirmation predicates are all satisfiable? That
is decidable only if the policy predicates are a decidable fragment. The PRD deliberately
declines to say what they are (§7.3 defers both the policy engine and the field schema),
and FR14 lists business rules in natural-business language ("which exceptions are routinely
granted"). An implementer has to invent the predicate language *in order to satisfy a
validation requirement*, which inverts the dependency the PRD claims to have avoided.

Worse, "always" is unqualified. Always under every obligation state? Always for every
requester? Always given the business's declared precedence between conflicting sources
(FR31)? Each reading is a different, differently hard, checker.

**Fix.** Downgrade to a bounded, honest form: validation MUST detect the decidable subset —
a capability whose required authority class is granted to no declared authority, or whose
required obligations reference an obligation the specification does not define — and report
anything outside that subset as a warning rather than claiming a universal gate. Name the
general case as undecidable in the requirement so nobody builds against the strong reading.

### F1.3 — FR18 + FR24: "sequencing is unexpressible" has no definition of a sequencing construct in a natural-language artifact. — **high**

> **FR18** The specification MUST NOT be able to express ordering or sequencing. The
> authoring surface makes sequencing unexpressible, and validation rejects any such
> construct with a message the operator can act on.

This is trivially satisfiable in a structured schema (no `next`, no `then`, no edges) and
unsatisfiable in prose. The PRD requires the artifact to be human-readable (FR19) and
authored conversationally by a non-engineer (FR1, FR3) whose natural description of their
business is *inherently sequential*: "first we check the deposit, then we hold the date,
and we only confirm once catering comes back." Under FR18 the compiler must reject that;
under FR6 the Builder may not invent a default; under FR3 it must decide adaptively what
to clarify. The PRD never says which wins, and it never says whether a prose rule that
*implies* an order is a construct or merely a description.

An implementer must invent: the detector (lexical? model-based? schema-only?), the scope
(does a rule that says "a deposit must be recorded before a date is held" count — it is an
obligation, and obligations are explicitly legitimate under FR15), and the operator-facing
rewrite guidance, which is the actual product work and is not mentioned anywhere.

**Fix.** State the discriminator as a requirement, in the Spine's own terms: a construct
that declares *what must be true before* an outcome is an obligation and is permitted; a
construct that declares *what happens next* is sequencing and is rejected. Then require the
Builder to perform the obligation rewrite conversationally, as an FR, because that rewrite
is the single most common thing an operator will need help with and currently nobody owns it.

### F1.4 — FR14: one requirement carrying sixteen expressive capabilities, over a schema the PRD defers. — **high**

FR14 is a single table cell containing sixteen semicolon-separated capabilities, several of
which are entire subsystems ("what the Agent may conclude and on whose authority", "its
authoritative sources and their precedence", "its data-lifecycle requirements"). O7
simultaneously records that the source material cannot agree on the field count. An
implementer cannot build against FR14; they can only re-derive it, which means the PRD has
deferred E1's hardest content to whoever opens E1 and called it a requirement.

This also breaks traceability in the direction that matters: there is no way to say FR14 is
*partially* met, and no way for a story to claim it. Sixteen capabilities will become
sixteen stories regardless, authored by someone with less context than the PRD author had.

**Fix.** Split FR14 into one requirement per expressive capability (FR14a–FR14p is fine;
the PRD's own ID scheme tolerates it). Keeping the schema deferred is correct; keeping the
*expressive surface* unenumerated as sixteen clauses in one cell is not — the enumeration
is exactly what the PRD said it would contribute in place of the schema.

### F1.5 — FR3 + FR4 + FR5 + FR7: four requirements that specify an intention and nothing an implementer can build or a tester can run. — **critical**

Treated in depth in §2. In build-readiness terms: none of the four defines a coverage
model, a stopping rule, an input contract, an output artifact, or a pass condition. FR3's
"a function of what is missing" presumes a computable notion of *missing*, which requires
the schema that O7 defers — so the Builder's core loop depends on a deferral the PRD
classified as harmless.

### Smaller invention sites

- **F1.6 — FR40 names a closed set of request kinds and the PRD never enumerates it.** — **high**
  §6 ("Vocabulary of record") omits it although the spine extract carries all seven verbatim
  (`retrieve`, `read`, `effect`, `clarify`, `respond`, `escalate`, `suspend`). Every
  authorization, journaling and divergence requirement is defined over a set the document
  does not contain. **Fix:** add the seven to §6.
- **F1.7 — FR81's "closed, enumerable vocabulary" is never enumerated, and no FR says who owns or extends it.** — **high**
  A closed vocabulary with no list and no amendment procedure will be opened by the first
  story that needs a status. **Fix:** require the list to exist as a versioned platform
  artifact, and require additions to be a platform release (which FR58 already establishes
  as a pattern).
- **F1.8 — The "specification defect" object has three producers (FR6, FR48, FR77/FR78) and no definition.** — **high**
  No schema, no writer/reader/lifecycle, no closure semantics, no statement of whether a
  Builder-time defect (FR6) and a runtime `spec_defect` (FR77) are the same type in the
  same backlog. They are the spine of the improvement loop. **Fix:** one FR defining the
  defect record and its lifecycle, explicitly stating whether the two origins unify.
- **F1.9 — FR25 self-test vs FR22 validation suite: two gates, undefined relation.** — **critical**
  FR22 gates promotion on "the specification's validation suite"; FR25 says "a passing
  self-test is the unit of done"; FR12 and FR91 make *time to a passing self-test* the
  headline burden metric. If these are the same artifact the document should use one name;
  if they are different, the project's primary generalisation measurement (FR91) is
  calibrated against the weaker of the two gates. **Fix:** define both or collapse to one.
  Critical because setup effort is one of three falsification measurements in §10.3.
- **F1.10 — FR62's "relevant context intact"** — **medium**
  *Relevant* is undefined and is exactly the deferred context-assembly question (§7.3), so
  resumption fidelity has no acceptance condition. **Fix:** state the guarantee as "no
  context item present before suspension is silently absent after resumption, or its
  absence is recorded" — a checkable form.

FR60's pending state also carries "a deadline" with no requirement for what happens when it
expires; that is F3.4 below, where it does more damage.

---

## 2. Is the hardest thing in the product adequately specified?

**No. This is the central failure of the document.** The PRD states the risk correctly,
assigns it to the right epic, and then specifies it at a level that would be appropriate
for a low-risk epic. Twelve requirements sounds proportionate until you read them: FR1,
FR2, FR8, FR9, FR10, FR11 and FR12 are structural or procedural and are genuinely
buildable; FR6 is a prohibition; **FR3, FR4, FR5 and FR7 — the four that carry the actual
risk — are intentions written in the imperative voice.** The epic the PRD calls
"Highest — this is the product risk" has four requirements of substance, zero acceptance
criteria in §10, and no test methodology anywhere in the document.

### F2.1 — Elicitation quality appears in no success criterion. The PRD measures the burden of elicitation and not its correctness. — **critical**

§10.1 is per-episode runtime correctness. §10.2 is per-business runtime outcomes. §10.3 is
engine leaks, resolution strain and setup effort. FR12 and FR91 measure wall-clock time
and artifact count. **Nothing anywhere measures whether the Builder actually extracted the
business's undocumented rules** — which §1.4 identifies as "the hard part, and it is where
V1 invests", and §8.1 as "the product risk".

The consequence is that the V1 programme can pass in full while the hard problem remains
untested. A Builder that asks three questions, ingests the price list, writes a plausible
specification and passes the self-test scores *better* on every instrumented metric than a
Builder that interviews properly — FR12 rewards speed and FR91 rewards fewer artifacts.
**As instrumented, the PRD's incentives point away from its own thesis.**

**Fix.** Add a per-business elicitation criterion to §10, computable and directional:
hidden-rule recall measured against a withheld ground-truth rule set (see F2.2), the count
of specification defects recorded at Builder time (FR6) versus those discovered later at
runtime (FR77), and the count of contradictions surfaced (FR5) versus those found
afterwards. The last two are already free — the records exist. The ratio of *defects found
during elicitation* to *defects found in production* is the single best available proxy for
elicitation quality and it costs nothing to compute.

### F2.2 — There is no test harness requirement for the Builder, and the four requirements are untestable without one. — **critical**

Asked directly: how would anyone test FR3, FR4, FR5, FR7? Today, they cannot. There is no
notion of a ground truth for what *should* have been elicited, so there is no pass
condition. Observing a real operator conversation gives you an anecdote; FR94's two or
three conversations give you two or three anecdotes.

The missing mechanism is cheap and standard: **a simulated-operator test fixture with a
hidden rulebook.** For each exemplar business, author a rulebook containing documented
content *and* a withheld set of undocumented rules (thresholds, prohibitions, routinely
granted exceptions, one printed-versus-practised contradiction, one deliberately
unanswerable question). Drive a model-played operator that will answer truthfully *only
when asked* and will volunteer nothing. Then every one of the four becomes measurable:

- **FR3** — question count and the share of asked questions that targeted a genuinely
  missing item, against a fixed-questionnaire baseline run on the same rulebook. The
  requirement "the number of questions asked is a function of what is missing, not of a
  template" is directly falsifiable this way: vary the rulebook's gaps, and the question
  count must move. That experiment is currently nowhere in the document and would be the
  single most valuable thing in E2.
- **FR4** — recall over the withheld undocumented rules, by category (prohibition,
  threshold, exception, authority limit, always-escalate).
- **FR5** — did the planted printed-versus-practised contradiction get surfaced, and was it
  surfaced *as a contradiction* rather than silently resolved — which is what FR5 actually
  forbids and what nothing currently checks.
- **FR6/FR7** — did the deliberately unanswerable item become a recorded defect rather than
  an invented default. This is a binary test and the most important one in the suite,
  because an invented default is the failure that reaches a customer.

**Fix.** Add an FR requiring the elicitation test fixture with withheld ground truth, and
add it to E2's scope. Without it E2 has no unit of done and the "highest risk" label is
decorative. Note the limit honestly in §13: a model-played operator is not an operator, so
the fixture measures the Builder's *interviewing behaviour*, not the thesis — FR94 remains
the only thing touching the thesis, and F4.2 argues it is too thin for that.

### F2.3 — What an implementer must invent, per requirement. — **high**

- **FR3** requires a representation of *what is missing*, i.e. a coverage model over the
  specification's expressive surface — which is the deferred schema (O7). It also requires
  a stopping rule. The PRD gives neither, so the first implementation will be a hidden
  checklist, which is a fixed questionnaire with a conversational veneer — the exact thing
  FR3 forbids, arrived at by the only available route. **This is the most likely way E2
  fails, and the PRD does not warn against it.** Fix: require the coverage model to be
  derived from the specification's own declared-but-unresolved items (so it adapts with the
  schema), and require the question budget to be bounded with the bound recorded.
- **FR4** names seven content categories and no elicitation strategy, no prioritisation
  when the operator tires, and no behaviour when the operator refuses or does not engage —
  FR6 covers "cannot resolve" but not "will not answer", which is the common case for a
  busy owner.
- **FR5** does not scope contradiction detection: across two documents? across document
  and utterance? within one document? Semantic, or only direct value conflict (two
  different prices for the same item)? At what granularity in a scanned PDF fee guide?
  The cheap, buildable version — conflicting *values* for the same declared field, plus
  source-versus-utterance conflict on an extracted value — should be named as the V1 scope,
  with general semantic contradiction detection excluded. As written, an implementer either
  over-builds or quietly ships the trivial version and claims FR5.
- **FR7** has no definition of the thing it probes. "The gap between printed and practised
  policy" is a research finding stated as prose in §3.3 and never turned into a structure.
  The buildable form: for each rule extracted from a document source, require the Builder
  to ask whether it is enforced as written, and record the answer as a first-class
  attribute of the rule (as-written / routinely waived / waived under conditions / dead
  letter). That turns FR7 from an aspiration into a field and a loop with a termination
  condition, and it makes the gap *auditable in the specification diff* — which is the whole
  point of FR19 and is currently unavailable for the most dangerous content in the artifact.

### F2.4 — FR11 defines a review requirement with no verdict, no artifact and no reviewer. — **high**

> **FR11** A human reviews the drafted specification before it may be promoted.

Combined with O1 ("Who performs specification review, and with what competence"), nothing
in V1 defines what review produces. FR28 requires every promotion to be "reviewable,
revertable and attributable" — attributable to whom, on what record? There is no review
verdict object, no sign-off evidence, no requirement that the reviewer saw the diff, and no
surface to review in (§7.2 puts the specification editor out of V1). FR11 is currently
satisfied by someone saying "looks fine" in a chat window.

**Fix.** Require a review record as an evidence-class object (reviewer identity, the
specification version diff reviewed, verdict, timestamp) as the promotion precondition.
That is a day of work, it makes FR28 true, and it converts O1 from a hole into a staffing
question.

---

## 3. Attack the V1 cut

A plausible week, run against the four exemplars, taking only what the PRD commits to.

**Monday 08:00.** The brewery's inbox receives 23 overnight messages. The adapter (FR84)
creates episodes. Fourteen resolve. The operator sees a divergence list (FR79) with two
items and an episode viewer (FR80). **She cannot see the other twelve episodes.** There is
no episode list, no search, no filter, no inbox view of any kind. FR80 lets her open "a
single episode" — identified how? No requirement produces an episode identifier anywhere
she can see.

> **F3.1 — No episode list, search or operator-visible identifier; the episode viewer has
> no index.** — **critical.** Almost certainly an oversight rather than a decision: §7.2
> descopes a *metrics dashboard*, which an episode index is not. **Fix:** an FR for an
> episode list filterable by lifecycle state, with the correlation identity NFR16 already
> mandates exposed on it.

**Monday 10:00.** A guard condition fires on a dental enquiry mentioning facial swelling —
the exemplar's mandatory override. FR44: the guard "never composes a reply". FR45: a
declared safety halt "terminates the episode with a recorded outcome". **No requirement
says the person who emailed is told anything.** The halt is recorded; the patient receives
silence. Nothing in §8.10's channel requirements obliges an egress message on a halt, and
FR44 forbids the guard from writing one while FR45 ends the episode before the Agent gets
another turn.

> **F3.2 — A safety halt leaves the requester with silence.** — **critical.** This is a
> correctness bug in the requirement set, not a missing nicety, and it lands on the
> highest-stakes exemplar in the set. **Fix:** an FR requiring every episode-terminating
> outcome to produce a declared outbound message through the channel adapter, with the
> message drawn from the specification's declared halt text — which keeps FR44 intact,
> because the specification wrote it, not the guard.

**Monday 14:00.** A gym member emails "freeze my membership for two months" from an address
the system has never seen. The Agent has a state-changing capability (FR16, FR52) and a
policy that permits a freeze. **No requirement anywhere establishes that the sender is the
member.** Authority classes gate *the Agent*; nothing authenticates *the requester*. FR86
correlates messages to episodes, FR87 dedupes resends, and that is the whole of identity in
this document. An email address in a From header is a claim, not an identity.

> **F3.3 — No requester identity verification before a state-changing effect.** —
> **critical.** The gym exemplar mutates an account on the strength of an unverified header.
> **Fix:** an FR allowing a capability contract to require verified requester identity, with
> verification as a Core-authorized step carrying its own evidence, and a state-changing
> effect unauthorized without it where demanded.

**Tuesday.** A brewery episode goes `pending` awaiting a catering confirmation, deadline
Friday (FR60). Friday passes. **Nothing happens.** No FR defines deadline expiry: no
timeout outcome, no notification, no transition, no record. The operator cannot see pending
episodes (F3.1), so the enquiry is lost silently and the customer concludes the brewery
ignored them.

> **F3.4 — Pending-episode deadline expiry is undefined.** — **high.** FR60 introduces a
> deadline and no requirement consumes it. **Fix:** an FR for expiry producing a recorded
> outcome and a reply within the already-initiated episode, which FR61 explicitly permits
> ("Within an initiated episode the platform may reply and emit messages").

**Wednesday.** A garden-centre episode escalates on a liability boundary — correct
behaviour, which FR69 even allows to count as success. **It goes nowhere.** FR47 ends at
"the Agent escalates"; the escalation inbox is out of scope (§7.2); O2 records destination,
notification and response expectation as unresolved. V1 can escalate and cannot hand off.

> **F3.5 — Escalation has no destination. O2 is a scope hole, not an acceptable open
> item.** — **critical.**

On the question asked directly, three reasons O2 does not qualify as an open item. First,
its own revisit condition — "Before the first business goes live" — falls *inside* V1,
because FR92 requires the usefulness test to run against real inbound requests; V1 cannot
complete without resolving it, and an open item whose deadline precedes V1 completion is
scope. Second, escalation is not a peripheral path: it is the declared behaviour whenever
rules are silent (FR48), authority is lacking (FR42), or a guard constrains (FR44) — on four
exemplars chosen for mandatory overrides and liability boundaries, escalation is a *primary*
path and plausibly the most common non-trivial outcome. Third, §7.2 does not merely defer
the receiving surface, it puts it out of scope *by decision*, which means nobody is
scheduled to resolve O2 at all. **Fix:** pull the minimum receiving behaviour into V1 — an
escalation is delivered through the existing channel adapter to a declared destination
address carrying the episode reference, the handoff is itself a recorded effect with
evidence, and failure to deliver is a platform error rather than silence. That is small.
Its absence is not.

**Thursday.** The divergence list shows three `spec_defect` items (FR77, FR78). The
operator reads "here is what your specification got wrong" (FR79) and wants to fix it.
**There is no editor** (§7.2) and no promotion surface. FR82 says a divergence item "is
actionable toward a specification change, closing the loop from observed behaviour back to
reviewed promotion" — the loop the PRD claims to close has no mechanism in V1. In practice
the vendor's engineers edit a file.

> **F3.6 — The improvement loop requires a surface V1 descopes; effort is therefore
> measured on vendor labour.** — **critical.** The consequence the PRD does not
> acknowledge: if specification changes are made by the vendor, FR91's "setup effort"
> measures *vendor* labour, and §1.3's claim that the transition is "short, reliable, and
> repeatable" is being tested on the wrong person. **Fix:** let a divergence item open a
> Builder conversation. The Builder is already an authoring surface; reusing it costs
> almost nothing and is on-thesis. Otherwise say plainly that in V1 the loop is closed by
> the vendor.

**Friday.** The brewery Agent has been quoting a stale hire fee all week — grounded in a
pinned source that was superseded, so FR32 and FR33 are both satisfied and nothing was
denied. **No divergence item exists**, because divergence is a classification of *denials*
(FR77). Three customers were told the wrong price and the operator's primary surface shows
nothing.

> **F3.7 — Divergence sees only denials and is structurally blind to confidently-wrong
> permitted behaviour.** — **critical.** This is the structural critique of the V1 cut. The
> dominant failure mode of a reasoning agent is not being blocked; it is being permitted and
> wrong — wrong advice, wrong intent reading, an answer where an escalation was warranted
> but nothing denied it. §10.2's "human corrections per hundred episodes" is the one
> criterion that would catch it, and it has no capture mechanism (F5.2). **Fix:** either
> add a sampled-review path (which costs the "no transcript review" claim and is worth it)
> or make the human-intervention event a recorded object so corrections become the second
> error signal alongside denials.

**Also absent from the whole week: any way to stop.**

> **F3.8 — No kill switch, no pause, no operator-reachable rollback.** — **critical.** V1
> sends email to real customers on behalf of four businesses and contains no stop control.
> FR26 makes rollback "selecting an earlier promoted version" with no surface to select it
> in. Nothing lets an operator halt a misbehaving Agent. A system that can email customers
> and cannot be stopped by its operator is not shippable, and this is precisely the operator
> fear §4.4 claims to have answered. **Fix:** one global pause per business plus a
> per-episode takeover, both on the episode surface that F3.1 already requires.

**Can a real business be run on this?** No — not because the cut is too small, but because
three of the missing pieces are not dashboard conveniences: a handoff destination (F3.5), a
stop control (F3.8) and a reply path (F3.2, F5.2). Add those three plus the episode index,
and the answer becomes yes with effort. All four are small, and none of them is a metrics
dashboard, an escalation inbox or a specification editor in the sense §7.2 descoped.

---

## 4. Attack the validation programme

**Verdict: FR88–FR94 can all pass while the thesis remains untested, and one of the seven
cannot be executed as written.** The programme is genuine engineering validation of the
*architecture* claim and close to self-congratulatory on the *usefulness* claim — which is
the one §5 marks "Untested".

### F4.1 — FR92 is not executable as specified. — **critical**

> **FR92** The usefulness test runs against each business's **real** inbound requests, with
> Agent failures reported separately from blocks caused by the business's own rules or
> capacity.

The four businesses are constructions. §13.1: "The four exemplar specifications are
constructions, not any real business's rules." A construction has no inbox. Therefore either
(a) the requests are authored by the team, which makes the usefulness test a test of the
team's imagination and a close relative of evaluating on your own training set, or (b) real
inbound requests are obtained from a real business — in which case FR88's "by the same path
a real operator would take" must also be run *with that operator*, and FR94's two or three
conversations stop being research colour and become the critical path of the entire
programme. The PRD does not choose. An implementer will choose (a), because it is the only
option that fits the schedule, and the usefulness claim will be declared tested against a
corpus the testers wrote.

**Fix.** Choose explicitly. The cheapest honest version: one of the four businesses must be
real — a real operator, their real documents, their real inbox for a bounded window — and
the other three stay constructions carrying only the architecture claim. Then state in §10
that the usefulness claim is tested at n=1 and the architecture claim at n=4. That is a
much weaker-sounding programme and a much stronger one.

### F4.2 — FR94 is specified as an activity, not a result, and nothing depends on its findings. — **high**

> **FR94** Two or three conversations with real small-business operators are conducted, as
> the only available test of the problem statement and of the printed-versus-practised gap.

No protocol, no required output artifact, no requirement that what is learned is applied to
the four specifications, and no condition under which the findings change anything. As
written, FR94 is satisfied by having had two phone calls. The PRD asserts these
conversations "close that gap" and gives them no mechanism to close it.

**Fix.** Require the output: per conversation, a recorded list of the operator's
undocumented rules and at least one identified printed-versus-practised divergence; a
revision pass applying them to the corresponding exemplar specification; and a recorded
answer to the question that would falsify §3.1 — *do you actually have rules you have never
written down, and would you state them to a system that will then enforce them?* If the
answer is no across all three, the problem statement is wrong and the programme must say so.
Also name the obvious limit: operators who agree to talk are a self-selected sample of the
AI-curious, and §3.4's own landscape evidence says most non-adopters "see no applicable use
case" — the people whose answer matters most are the ones who will not take the call.

### F4.3 — The three generalisation measurements are self-graded, unordered and confounded. — **high**

- **FR89 engine leaks** are classified as *should have been configuration* / *justifies an
  extension point* / *genuinely novel* by the same people who want the leak count to fall.
  "Genuinely novel" is an unfalsifiable escape hatch: every leak can be classified into it,
  and §10.3's failure condition ("leaks do not fall toward zero") then becomes unreachable.
- **The build order is chosen by the team and is not pre-registered.** §10.3 fails the
  thesis only if leaks and effort fail to fall from the first business to the fourth — a
  shape produced by building the hardest business first and the easiest last, and the team
  controls the order. The dental exemplar (mandatory override, high-stakes grounding) is
  plainly hardest; the garden centre (advice, no state mutation) plainly easiest.
- **FR91 setup effort is confounded by operator learning.** The same person builds all four
  and gets better at using the Builder. That slope is a learning curve, not generalisation,
  and §10.4 lists six counter-metrics without listing this confound.

**Fix.** Pre-register the build order with the hardest business last and the rationale
recorded before the first build. Have leak classification adjudicated by someone who did not
write the fix, and require every *genuinely novel* classification to carry a written
justification of why no configuration surface could have carried it. For FR91, record a
second, less gameable effort measure alongside wall-clock — number of clarifying exchanges,
and defects outstanding at self-test pass — and add the learning-curve confound to §10.4 as
a seventh counter-metric. Consider having a *different person* build the fourth business;
that single change does more for the generalisation claim than the other three measurements
combined.

### F4.4 — FR93's validity floor has no floor, and is read after the numbers it guards. — **medium**

> **FR93** … if it is near zero, the demonstration proves nothing however good the other
> numbers look.

Correct and unactionable: "near zero" is not a threshold, and the no-numbers decision
genuinely applies. But the *structure* is fixable without inventing a number: require the
validity floor to be computed and published **before** the resolution rates are read, and
require every per-business resolution figure to be reported only alongside it. A guard
evaluated after the headline number is not a guard.

### F4.5 — What the programme does not test at all. — **high**

Nothing in FR88–FR94 tests: elicitation quality (F2.1); whether an operator *unaided* can
produce a true specification, since the builders are the authors; whether requesters
*accept* the resolutions they receive; whether the operator can run the improvement loop
without the vendor (F3.6); or cost per episode, which is instrumented (NFR14) and absent
from every criterion in §10. Five of the six things a buyer would ask about sit outside the
programme that is supposed to falsify the product. **Fix:** at minimum add requester
re-contact-after-close and cost per episode as recorded per-business measurements — both are
computable from the episode record, so they satisfy FR76 for free.

---

## 5. Contradictions

### F5.1 — The improvement loop is required and its mechanism is out of scope. — **critical**

> **FR82** A divergence item is actionable toward a specification change, closing the loop
> from observed behaviour back to reviewed promotion.

> **§7.2** Metrics dashboard, escalation inbox, **in-product specification editor** — Out of
> the V1 operator surface by decision.

FR28 ("Every promotion is reviewable, revertable and attributable") and FR11 ("A human
reviews the drafted specification before it may be promoted") sit against the same cut. The
PRD commits to a closed loop and descopes the only surface that closes it. **Fix:** scope a
minimal editor by reusing the Builder (F3.6), or state plainly that in V1 the loop is closed
by the vendor — and then fix §10.3's interpretation accordingly.

### F5.2 — §10 requires criteria §8 provides no way to record, against a requirement that says all of them are recordable. — **critical**

> **FR76** Every success criterion in §10 is computable from the episode record **without a
> human reading a transcript**.

> **§10.2** Human corrections per hundred episodes, **and whether that falls over time**.

> **§10.1** … guards fired when their conditions were met …

Three failures in one. (i) *Human corrections* require a recorded human intervention event;
no FR creates one, and the operator surface is read-only, so corrections happen outside the
system — in the operator's own mailbox — and are invisible to the record. (ii) *Share of
inbound episodes resolved without a human* (§10.2) has the same dependency. (iii) *Guards
fired when their conditions were met* requires knowing when a condition was met and the
guard did **not** fire — a false-negative rate, not computable from the record by
construction; it needs labelled ground truth. FR76 is therefore false as stated for at
least three of §10's criteria, and FR76 is the requirement the whole no-transcript-review
posture rests on. **Fix:** add an FR for a recorded human-intervention event (takeover,
correction, override) as typed evidence; and restate the guard criterion as what is actually
computable — guards that fired, with their inputs retained so false negatives can be
*sampled* later — while admitting in §13.1 that guard recall is unmeasured in V1.

### F5.3 — The document both guarantees and disclaims grounding. — **high**

> **NFR5** … An invalid claim is refused **before it reaches the person** | Qualitative,
> absolute

> **NFR6** … faithfulness is **evaluated against a threshold, never guaranteed**. The
> product may not promise correctness of meaning

Two rows of the same table, one absolute and one explicitly non-guaranteeing, over the same
surface. They are reconcilable — NFR5 is reference integrity, NFR6 is meaning — but the PRD
never says so, and FR32's "The Agent may never invent one" sits on the absolute side of a
line it cannot hold (F1.1). A reader leaves with a grounding guarantee the system does not
have. **Fix:** one sentence in §9 distinguishing reference validity (absolute, enforced)
from semantic faithfulness (measured, not guaranteed), and align FR32 to the second.

### F5.4 — Escalation is a declared success and has no destination. — **critical**

> **FR69** Escalation MAY be a declared success rather than a failure where the business
> says so — an episode escalated on an urgency trigger is a correct outcome.

> **§7.2** … escalation inbox … Out of the V1 operator surface by decision.

> **O2** Where an escalated episode lands — destination, notification, response expectation
> … **Revisit when:** Before the first business goes live.

Analysed at F3.5. Quoted here because the three statements are mutually unsatisfiable inside
V1: a *success* outcome whose receiving surface is descoped and whose definition is deferred
past a date falling inside V1's own completion condition (S11, FR92).

### F5.5 — "Not V1 concerns" vs running four businesses on real inbound mail. — **high**

> **NFR15** Availability, throughput, scale — **Not V1 concerns, and stated as such.**

> **FR92** The usefulness test runs against each business's **real** inbound requests…

If real requests from real people are being answered, availability is a V1 concern the day a
customer's email goes unanswered because a process was down. FR64 gives crash recovery — the
durability half; nothing covers the ingress half, where a down adapter silently drops the
queue and the operator has no surface that would show it (F3.1). **Fix:** scope availability
honestly as "best-effort, with every ingress failure recorded and surfaced to the operator"
— a requirement, not a number, so the no-numbers decision survives.

### F5.6 — "Never a form or a fixed question set" vs pre-filled starting points that seed the questions. — **medium**

> **FR1** The Builder opens with an open invitation … and **never with a form or a fixed
> question set.**

> **FR8** The Builder MAY offer optional pre-filled Business Specification starting points
> … that seed terminology, candidate requests, **questions worth asking** and policies worth
> considering.

A vertical starting point that seeds the questions is a fixed question set with provenance.
FR8's guards are all about *behaviour* ("no behavioural sequence", "never the source of agent
behaviour") and say nothing about the elicitation path — which is where the harm actually is,
since a seeded question list is the most likely origin of the hidden checklist that F2.3
identifies as E2's main failure mode. **Fix:** add to FR8 that a starting point may not fix
the elicitation path, and require question selection to be gap-driven even when a starting
point is used — then test it by running the same rulebook with and without the starting
point and comparing the questions asked (F2.2).

### F5.7 — Requester disclosure is an open item, and the V1 requirement that needs it is in scope. — **high**

> **O3** Whether the requester is told they are talking to an Agent, and how … **Revisit
> when:** Before the first business goes live.

FR92 requires real inbound requests from real people. O3 must be resolved before FR92 can
run, and O3 concedes "Jurisdiction may decide it rather than product" — a possible *legal*
precondition on a V1 deliverable, in an exemplar set containing a dental practice. Same
structural defect as O2: an open item gating an in-scope requirement. **Fix:** make the
disclosure position a V1 requirement with a default (disclose, in the first outbound message
of every episode) and let jurisdictional variation be configuration.

### F5.8 — §12 risk-weights the epic that measures, not the epics that leak. — **medium**

> **§12** Two epics carry the V1 claim: **E2**, because elicitation is the hard problem, and
> **E12**, because without it this is a runtime plus an assertion that it can be configured.

§5's architecture claim is falsified by engine leaks — and leaks occur in E4, E6, E7, E8 and
E9, each rated High or Medium. E12 *records* leaks; it does not produce them. Weighting the
epics by where the measurement lives rather than where the risk lives will misallocate the
review attention the PRD is otherwise careful about. **Fix:** state that E12 measures a risk
distributed across E4–E9, so those epics inherit a measurement obligation rather than a
reporting one.

### F5.9 — FR19's diffability asserted over a representation O7 defers. — **low**

FR19 requires the specification to be human-readable and diffable and "neither a generated
prompt nor generated code"; O7 defers the field schema entirely. Diffability is a property
of a representation, so FR19 asserts a quality of an artifact whose form is undefined.
**Fix:** record in E1 that diffability, reviewability and revertability are acceptance
criteria *on the schema decision*, so O7 cannot be resolved with a representation that loses
them.

---

## 6. What the FR tables silently dropped

### F6.1 — The proof gate is gone. — **high**

The architecture spine makes it a named decision point — "Before the whole runtime is
committed to this architecture, one realistic business interaction is implemented end to
end", compared against the existing system on named axes (architectural simplicity, custom
code, model calls, latency, control and observability, failure handling, extensibility to a
second business, ease of enforcing business boundaries) — and the spine extract explicitly
flags it as "a gate/milestone, not an epic — but **PRD-visible as a V1 decision point**".

It appears nowhere in prd.md: no scope line, no FR, no epic, no open item, and no entry in
the decision log recording that it was dropped. The document therefore commits to twelve
epics with no first checkpoint, which is the opposite of its own falsifiable posture — a
PRD that is scrupulous about not assuming the hard part is solved has removed the one gate
that tests whether it is. **Fix:** restore the proof gate as a V1 milestone ahead of E4–E9,
with its comparison axes, and state what happens if it fails.

### F6.2 — Brownfield reuse and migration are claimed in prose and unrequirmented. — **medium**

The scope note calls the shipped voice project "a source of reusable assets, and a set of
brownfield constraints", and the spine names the existing system "the reference
implementation and migration source". No FR, epic or scope line mentions reuse, migration or
retirement; E5 implies a fresh runtime. Either reuse is real and belongs in scope, or it is
not and the scope note is flattering an existing asset. **Fix:** one scope line stating what
is reused (the pre-send sanitizer, the selftest-as-gate discipline, adapter patterns) and
what is re-derived — or drop the claim.

### F6.3 — Nothing specifies how the Agent writes. The most customer-visible quality of an email product has no requirement. — **high**

FR14's "how it speaks and what it will not say" is the entire treatment of voice and
register, buried in a sixteen-clause cell, with no FR on tone fidelity, no evaluation of it,
and no mention in §10. For an inbound-email product this is the first thing a customer judges
and the first thing an operator rejects the system over: **a reply that is correct, grounded,
evidenced and reads like a robot is a product failure that every criterion in §10 scores as
a success.** Email has its own register — length, salutation, signature, quoting, threading,
one topic per reply — and none of it appears. The shipped voice project enforced a hard
register discipline and learned that a pre-send sanitizer is a backstop, not a licence; that
lesson did not survive into this document. **Fix:** an FR requiring the specification to
declare a register and a prohibited-language set; an FR requiring the channel adapter to
enforce channel-appropriate form *and to record when it had to intervene*; and one
directional criterion in §10.2 on operator rejection of drafted replies.

### F6.4 — Email reality is almost entirely unspecified. — **high**

§8.10 has five requirements: channel-neutrality, one adapter, replaceability, correlation,
resend guarding. Everything else about the channel the PRD deliberately chose is missing:
attachments inbound and outbound (FR2 accepts the operator's documents, but nothing covers a
requester's attached receipt or a photo of a dying plant — which is literally exemplar
three's request), subject lines, quoted history and signature blocks as context noise, CC
and multiple recipients, forwarded threads, auto-responders and out-of-office loops (a mail
loop is the classic way an email agent costs money all weekend), spam and abuse, bounce
handling, and sender identity (F3.3). **Fix:** scope these explicitly, even as exclusions.
An adapter that cannot read the photo attached to "this plant is dying" cannot run exemplar
three — and nobody noticed, because §12 rates the channel epic **Low** risk. That rating is
itself a finding.

### F6.5 — No FR for the faithfulness evaluator that NFR6 and O5 both depend on. — **medium**

NFR6 says faithfulness is "evaluated against a threshold" and "instrumented from day one";
O5 defers the threshold value until after the four-business run. Nothing requires the
*evaluator* to exist — no FR, no epic scope line, no evidence type. A threshold cannot be
set after the run either, because nothing will have measured anything. **Fix:** an FR
requiring per-reply faithfulness scoring recorded as evidence, with the method named as an
implementation choice and its own error rate recorded alongside.

### F6.6 — §3.2's second discriminator never becomes a requirement. — **medium**

> **Refuse with a reason** drawn from the business's own rules, rather than failing to find
> an answer.

FR77 classifies denials for the *operator*; FR81 closes the vocabulary of what the *operator*
sees. Nothing requires the **requester** to receive a reason drawn from the business's rules.
One of the four things the PRD says a retrieval chatbot cannot do is unrequirmented — and a
refusal is the most common non-trivial outcome of a deliberately bounded agent. **Fix:** an
FR requiring a business refusal to be communicated with its declared reason, and the reason's
source recorded.

### F6.7 — FR52's consequence class is "visible" on no surface. — **medium**

> **FR52** … This is what an operator is actually bounding when they say they do not want an
> Agent contacting the wrong person, and it is **visible, not internal**.

Visible where? No operator surface shows capability grants or consequence classes, and the
specification editor is out of scope. §4.4's answer to the reliability counter-argument —
the PRD's response to its own loudest objection — rests on a visibility V1 does not deliver.
**Fix:** require consequence classes to be rendered in the specification review surface that
F2.4 already needs to exist.

### F6.8 — FR12 instruments burden too narrowly. — **low**

Wall-clock time and artifact count only. Not: questions answered, sessions required,
abandonment, or whether the operator needed help. §1.3 makes "short" one of three
load-bearing words and FR12 measures the easiest proxy for it.

### F6.9 — NFR11 forbids credentials in "any evidence export" and no export exists. — **low**

An export is referenced only inside a prohibition and required by nothing, while FR75's
addressability and any real audit use imply one. **Fix:** scope the export or drop the
clause.

---

## 7. The one question that matters most

**If V1 is built exactly as specified and everything passes, the thing still unknown is the
only thing V1 was for: whether a real operator, unaided, can produce a specification that is
true about their business.**

Everything the programme measures is downstream of that, and every measurement is taken on
specifications the builders wrote. FR88 says the four are built "by the same path a real
operator would take" — by people who designed the path, know what the Builder listens for,
and know what the Core will enforce. That is not the same path; it is the same path walked by
someone holding the map. A fully green programme would prove that **the platform can be
configured by its authors to behave correctly on requests its authors wrote.** A real and
necessary engineering result. Not the thesis in §1.4.

Five specific unknowns survive a green V1:

1. **Elicitation recall.** No criterion measures whether the Builder extracted the
   undocumented rules (F2.1). The product's stated highest risk exits V1 with no number and
   no pass condition attached to it.
2. **Whether an operator will tell a system the truth.** §3.3's printed-versus-practised gap
   presumes the operator will state the rule they have never written down — to software, in
   writing, with the enforcement consequence FR43 then makes real. An operator who routinely
   waives a fee has a reason not to declare it. Nothing in V1 tests willingness, and
   willingness is a precondition for the entire thesis.
3. **Whether requesters accept the resolutions.** §10 counts resolution share, action share
   and corrections — all vendor-side views. Nothing counts re-contact after close,
   complaints, mid-episode abandonment, or a resolution the customer rejected. Every number
   can be hit by four businesses whose customers hated it.
4. **Whether the operator can run the loop.** With no editor and no promotion surface (F3.6),
   the improvement loop is exercised by the vendor, so "repeatable" is measured on vendor
   effort. The second, third and fourth business may cost less *for the builders* and no less
   for an operator — and the latter is what §1.3 claims.
5. **What it costs.** Instrumented (NFR14), absent from every criterion in §10. A platform
   resolving 60% of inbound requests at a price this tier will not pay has falsified the
   usefulness claim with no metric registering it. The landscape work the addendum cites says
   usage unpredictability is a leading churn driver in exactly this tier, and O6 defers the
   ceiling to commercial packaging — so cost exits V1 as uninterpreted instrumentation.

**The cheapest structural fix to all five.** Make one of the four businesses real end to end:
a real operator doing their own elicitation on their own documents against their own inbox for
a bounded window, with hidden-rule recall, requester re-contact rate and cost per episode
recorded, and with the operator — not the vendor — closing at least one divergence item. One
real case tests all five unknowns. Four constructed ones test none of them. Which is why
§13.1's admission that the exemplars "are constructions, not any real business's rules" is the
most important sentence in the document, and the one its validation programme does least
about.

---

## Finding index

| ID | Finding | Severity |
|---|---|---|
| F1.1 | Grounding enforcement: FR32 unbuildable as a gate, FR33 vacuous against invented facts | critical |
| F1.2 | FR23 granted-but-always-denied is a satisfiability check over an undefined predicate language | high |
| F1.3 | FR18/FR24 sequencing-unexpressible has no definition of a sequencing construct in prose | high |
| F1.4 | FR14 is sixteen subsystems in one cell over a deferred schema | high |
| F1.5 | FR3/4/5/7 specify intentions, not buildable behaviour | critical |
| F1.6 | FR40's closed request-kind set is never enumerated in the PRD | high |
| F1.7 | FR81's closed vocabulary is never enumerated and has no owner | high |
| F1.8 | "Specification defect" has three producers and no definition | high |
| F1.9 | FR25 self-test vs FR22 validation suite — relation undefined, and FR91 calibrates on it | critical |
| F1.10 | FR62 "relevant context intact" has no acceptance condition | medium |
| F2.1 | Elicitation quality appears in no success criterion; instrumentation rewards shallow elicitation | critical |
| F2.2 | No Builder test harness; FR3/4/5/7 untestable without withheld ground truth | critical |
| F2.3 | Per-requirement invention sites; the hidden-checklist failure mode is unwarned | high |
| F2.4 | FR11 review has no verdict, artifact, reviewer or surface | high |
| F3.1 | No episode list, search or operator-visible identifier | critical |
| F3.2 | A safety halt leaves the requester with silence | critical |
| F3.3 | No requester identity verification before a state-changing effect | critical |
| F3.4 | Pending-episode deadline expiry is undefined | high |
| F3.5 | Escalation has no destination; O2 is a scope hole, not an open item | critical |
| F3.6 | The improvement loop requires a surface V1 descopes; effort measured on vendor labour | critical |
| F3.7 | Divergence sees only denials — blind to confidently-wrong permitted behaviour | critical |
| F3.8 | No kill switch, pause or operator-reachable rollback | critical |
| F4.1 | FR92's "real inbound requests" cannot exist for constructed businesses | critical |
| F4.2 | FR94 is an activity with no required output and no dependency on its findings | high |
| F4.3 | The three measurements are self-graded, unordered and learning-curve confounded | high |
| F4.4 | FR93's validity floor is read after the numbers it guards | medium |
| F4.5 | Programme tests neither elicitation, unaided operators, requester acceptance, nor cost | high |
| F5.1 | FR82 loop vs §7.2 no editor | critical |
| F5.2 | FR76 vs §10.2 human corrections and §10.1 guard recall | critical |
| F5.3 | NFR5 absolute vs NFR6 never-guaranteed over the same surface | high |
| F5.4 | FR69 escalation-as-success vs §7.2 and O2 | critical |
| F5.5 | NFR15 "not V1 concerns" vs FR92 real inbound mail | high |
| F5.6 | FR1 no fixed question set vs FR8 seeded questions | medium |
| F5.7 | O3 disclosure gates FR92, which is in V1 scope | high |
| F5.8 | §12 risk-weights the epic that measures, not the epics that leak | medium |
| F5.9 | FR19 diffability asserted over a deferred representation | low |
| F6.1 | The proof gate is absent from the PRD entirely | high |
| F6.2 | Brownfield reuse and migration claimed in prose, unrequirmented | medium |
| F6.3 | No requirement for how the Agent writes — voice, register, email form | high |
| F6.4 | Email reality unspecified: attachments, threads, loops, CC, bounces, abuse | high |
| F6.5 | No FR for the faithfulness evaluator NFR6 and O5 depend on | medium |
| F6.6 | §3.2's "refuse with a reason" never reaches the requester as a requirement | medium |
| F6.7 | FR52 consequence class is "visible" on no surface | medium |
| F6.8 | FR12 instruments burden too narrowly | low |
| F6.9 | NFR11 forbids credentials in an evidence export nothing requires | low |

**Counts.** critical 15 · high 18 · medium 9 · low 3 · **total 45**

**Build-ready?** §8.5 through §8.8 largely are. §8.1, §8.3, §8.9 and §8.10 are not, and
§8.11 contains one requirement that cannot be executed. The five fixes that change the most,
in order:

1. Specify the Builder test fixture with withheld ground truth, and add an elicitation-quality
   criterion to §10 (F2.2, F2.1).
2. Make one exemplar business real end to end (F4.1, §7).
3. Restore the receiving half of escalation, an episode index, and a pause control (F3.5,
   F3.1, F3.8) — plus an outbound message on safety halt (F3.2).
4. Split FR32 from FR33 and state what V1 cannot prevent (F1.1).
5. Add a recorded human-intervention event so §10's own criteria become computable (F5.2).
