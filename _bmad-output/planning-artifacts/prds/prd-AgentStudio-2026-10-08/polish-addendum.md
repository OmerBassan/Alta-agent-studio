---
title: "Polish pass — addendum.md (structure and prose)"
status: findings
created: 2026-10-08
---

Scope: structure and prose only. No content re-review, no new material, no reopened decisions.

Locations cite the addendum's section labels **as they stand today** (A1/A2/A3). Apply the prose findings first and the renaming/reordering findings (S2, S3) last, or the quoted anchors will have moved.

---

## Structure

### S1 — MD025: two top-level headings

**Location:** lines 1–10 (frontmatter `title:` plus `# Addendum`).

**Current:**

```markdown
---
title: "Addendum — Agent Studio Business-Specific Agent Platform PRD"
status: draft
created: 2026-10-08
updated: 2026-10-08
---

# Addendum

Depth that belongs downstream
```

**Recommended replacement:**

```markdown
---
title: "Addendum — Agent Studio Business-Specific Agent Platform PRD"
status: draft
created: 2026-10-08
updated: 2026-10-08
---

**Addendum to the Agent Studio PRD.** Depth that belongs downstream
```

**Reason:** deleting the H1 and folding its name into the lead keeps one top-level heading (the frontmatter title) and loses nothing — the minimal fix, and it leaves every `##` section at its current depth.

---

### S2 — Section labels A1/A2/A3 collide with the PRD's assumption tags A1–A4

**Location:** all five headings (`## A1.`, `## A2.`, `### A2.1`, `### A2.2`, `### A2.3`, `## A3.`).

**Current:** `## A1. Implementation opportunities in recent model developments` / `## A2. Prior art detail behind the differentiation claim` / `## A3. Brownfield lessons carried forward as knowledge`

**Recommended replacement:** rename the prefix `A` → `AD` throughout: `## AD1.`, `## AD2.`, `### AD2.1`, `### AD2.2`, `### AD2.3`, `## AD3.`

**Reason:** the PRD uses `[ASSUMPTION A1]`–`[A4]` as live inline tags with an index at §11.1; "A1" and "A3" currently name two different things across the pair, and nothing in the PRD cross-references the addendum's labels, so the rename is free.

---

### S3 — Ordering: the three passes are stacked in the order they were written, not in reading order

**Location:** whole-file section order (A1 → A2 → A3).

**Current order:** A1 model developments · A2 prior art / market · A3 brownfield lessons

**Recommended replacement:** move the blocks so the order is

| New | Title (unchanged) | Supports |
|---|---|---|
| **AD1** | Prior art detail behind the differentiation claim (+ AD1.1–AD1.3, today's A2.1–A2.3) | PRD §4 |
| **AD2** | Brownfield lessons carried forward as knowledge (today's A3) | PRD §7.4 |
| **AD3** | Implementation opportunities in recent model developments (+ AD3.1, AD3.2) | PRD §7.3, §5 |

**Reason:** the addendum then follows the PRD's own reading order, and the most speculative material (model developments, explicitly "not a commitment") stops being the first thing a reader meets. Pure block move — no body text changes beyond the heading numbers.

---

### S4 — A1's subsections are unnumbered while A2's are numbered

**Location:** lines 20 and 32.

**Current:**

```markdown
### Cheap high-volume inference changes a cost assumption, not an architecture
...
### Not every intelligent decision needs the full Agent loop
```

**Recommended replacement (with S2/S3 applied):**

```markdown
### AD3.1 Cheap high-volume inference changes a cost assumption, not an architecture
...
### AD3.2 Not every intelligent decision needs the full Agent loop
```

**Reason:** every other H3 in the file is numbered; unnumbered siblings make the section uncitable and look like a different document.

---

### S5 — A2 opener does not name the PRD sections it defers to

**Location:** line 55.

**Current:** `The PRD names the prior art and states the narrowed claim.`

**Recommended replacement:** `The PRD names the prior art (§4.2) and states the narrowed claim (§4.1).`

**Reason:** this file's whole function is to be the downstream half of a pair; the pointer should resolve without a search.

---

### S6 — A2.1 restates what is now a standing condition in PRD §4.3

**Location:** lines 68–72.

**Current:**

```markdown
The evidence in `extract-landscape.md` and summarised above is recorded under an explicit condition, and the condition is as binding as the evidence:

> Market evidence is **recorded rather than written around, and is explicitly not permitted to redirect the product** — in particular, not toward hunting an unoccupied vertical.

This matters because the strongest finding in that material (vertical agents outperforming horizontal ones, and being what passes audit) points directly at the move the product refuses to make. The resolution already in the PRD is to sell the outcome while keeping one engine behind it, and to treat "general-purpose" as an internal architecture claim. Anyone revisiting the market evidence later should read it with this rule attached, or they will re-derive a vertical product from it.
```

**Recommended replacement:**

```markdown
The rule governing this evidence lives in the PRD, as the second of the three standing conditions (§4.3): market evidence is recorded and is not permitted to steer the product toward hunting an empty niche.

What belongs here is why that condition was needed. The strongest finding in the material — vertical agents outperforming horizontal ones, and being what passes audit — points directly at the move the product refuses to make (§4.4), and the resolution is the one already in §1.2: sell the outcome, keep one engine behind it, treat "general-purpose" as an internal architecture claim. Anyone revisiting this evidence later must read it with the condition attached, or they will re-derive a vertical product from it.
```

**Reason:** the rule moved into the PRD body during review; the addendum should hold the rationale and defer on the rule, not carry a second copy that can drift.

---

### S7 — A3's first lesson restates PRD §4.3 condition 3

**Location:** line 94, final sentence.

**Current:** `The rule that survives: before committing to any named technique, confirm the mechanism it targets exists on the hot path. This applies to this PRD too — it is why §7.3 captures guarantees and names no mechanisms.`

**Recommended replacement:** `This is the evidence behind the third standing condition in the PRD (§4.3): a named technique is a hypothesis about this system, and the mechanism it targets must be confirmed on the path that matters before anything is committed. It is also why §7.3 states guarantees and names no mechanisms.`

**Reason:** the rule is now a PRD condition; the addendum's unique contribution is the three-of-four evidence, so it should supply that and point at the rule's home.

---

### S8 — A3's second lesson is now largely PRD §1.3

**Location:** line 96.

**Current:**

```markdown
**Never add a model call to the reply path in the name of latency.** The latency-safe generalisation is to harvest the structured output the system already produces and push prose synthesis off the hot path. The principle carries; the voice-specific twenty-word form of it does not. Note that the arithmetic genuinely flips for V1: on an asynchronous channel a few hundred milliseconds of extra round trip is free, so carrying the zero-model determinism thesis forward would be inheriting a constraint whose justification has been removed. Any future synchronous channel re-imports a weaker version of it.
```

**Recommended replacement:**

```markdown
**Never pay a model call to restate output the system already has.** The durable lever is to harvest the structured record produced by work already done and keep prose synthesis off any path a person is waiting on. The lever carries; the voice-specific twenty-word spoken form of it does not. The PRD settles the rest of this: §1.3 names the superseded principle, states why the asynchronous channel removes the arithmetic that justified it, and keeps the limit that survives.
```

**Reason:** PRD §1.3 (new) now carries the superseded-principle argument and the synchronous-channel caveat almost verbatim; duplicating it here risks the two copies diverging on the one point the PRD deliberately reversed.

---

### S9 — A1 asserts a latency premise the PRD has since retired

**Location:** line 26.

**Current:** `This does **not** license adding model calls freely. The engineering discipline carried over from the shipped voice project still applies — a model call on a reply path must justify itself against the latency budget. What changes is the cost argument, not the latency argument.`

**Recommended replacement:** `This does **not** license adding model calls freely. The limit that survives from the shipped voice project is the one the PRD states in §1.3: cost and latency are not licences, and no model call is added to a path a person is waiting on without measuring that path. What changes is the cost argument, not that limit.`

**Reason:** "the latency budget" is the voice budget, which §1.3 and NFR13 retire for V1 — as A3 itself says — so the addendum currently contradicts both the PRD and its own later section.

---

### S10 — A1's closing cautions restate FR44 and FR39 instead of citing them

**Location:** line 49.

**Current:** `Two cautions that keep this from becoming the rejected model by another route. A typed decision call used to pick the Agent's next step *is* deterministic next-action selection, which the architecture forbids — such a call may constrain or classify, never sequence. And a guard evaluated by a model still binds deterministically: the verdict's outcomes stay closed, and a guard never composes a reply.`

**Recommended replacement:** `Two cautions keep this from becoming the rejected model by another route. A typed decision call used to pick the Agent's next step is deterministic next-action selection, which FR39 forbids — such a call may constrain or classify, never sequence. And a model-evaluated guard is still bound by FR44: two closed outcomes, and never a composed reply.`

**Reason:** both constraints are requirements of record; citing them keeps one copy authoritative and shortens the paragraph.

---

### S11 — A2.3 says "the two tiers" where the PRD names them

**Location:** line 86.

**Current:** `FR76 has since been narrowed to the two tiers where that is actually true, which is the correction that probe would have produced.`

**Recommended replacement:** `FR76 has since been narrowed to the per-episode and per-business criteria (§10.1, §10.2), where that is actually true — the correction that probe would have produced.`

**Reason:** "the two tiers" is unresolvable without opening the PRD, and "tier" is used elsewhere in both documents for knowledge tiers and model tiers.

---

### S12 — A3's closing block is an inventory, not a lesson

**Location:** line 110.

**Current:** `**Gaps in the shipped system that are deliberately not inherited:** no instrumentation on any model call; no correlation identity outside the voice path; minimal persistence; single-tenant by stated non-goal.`

**Recommended replacement:** `**What is deliberately not inherited.** Four gaps in the shipped system: no instrumentation on any model call; no correlation identity outside the voice path; minimal persistence; single-tenant by stated non-goal. The PRD closes the first two as day-one Core capabilities (NFR13, NFR14, NFR16).`

**Reason:** every other block in A3 is a rule in bold followed by its evidence; this one is a list, and labelling it as such stops it reading like a failed lesson.

---

### S13 — "proof implementation" is not the PRD's term

**Location:** line 47.

**Current:** `Both developments are carried as **candidates for the later model and runtime strategy, and for the proof implementation** — nothing more.`

**Recommended replacement:** `Both developments are carried as **candidates for the later model and runtime strategy, and for the proof gate (§7.5)** — nothing more.`

**Reason:** the PRD's vocabulary of record for that milestone is "the proof gate"; a second name for it invites a reader to look for a third artifact.

---

### S14 — Recommended final outline

For checking the applied result:

```
(frontmatter title, no H1)
lead paragraph
## AD1. Prior art detail behind the differentiation claim
### AD1.1 The disposition rule that must travel with the market evidence
### AD1.2 The deepest rejection: the intelligence layer on someone else's record
### AD1.3 Cheap falsifiers that were available and not used
## AD2. Brownfield lessons carried forward as knowledge
## AD3. Implementation opportunities in recent model developments
### AD3.1 Cheap high-volume inference changes a cost assumption, not an architecture
### AD3.2 Not every intelligent decision needs the full Agent loop
```

**Reason:** one numbering scheme, one heading depth per level, PRD reading order, and no label that collides with an assumption tag.

**Cross-reference audit result:** every `FR`, `NFR`, `O`, `E` and `§` reference currently in the file resolves against `prd.md` as it stands (FR36, FR46, FR76, FR86, FR95–FR98, NFR12, NFR13, NFR14, NFR17, O6, O8, E12, §6, §7.3, §7.4). No broken targets. The findings above add missing pointers (§1.2, §1.3, §4.1, §4.2, §4.3, §4.4, §7.5, §10.1, §10.2, FR39, FR44, NFR16) rather than correcting wrong ones.

---

## Prose

### P1 — Tangled opening list

**Location:** line 22.

**Current:** `Low-cost, high-throughput model tiers aimed at classification, repetitive tasks, real-time support and agent/subagent workloads materially change the economics of lightweight model calls.`

**Recommended replacement:** `Low-cost, high-throughput model tiers — aimed at classification, repetitive tasks and subagent workloads — change the economics of lightweight model calls.`

**Reason:** a four-item list between subject and verb buries the claim, and "materially" is doing nothing.

---

### P2 — "The consequence is a negative one"

**Location:** line 24.

**Current:** `The consequence is a negative one, which is why it matters: it removes the incentive to **over-engineer deterministic substitutes purely to avoid inference cost**.`

**Recommended replacement:** `The consequence is a subtraction, which is why it matters: it removes the incentive to **over-engineer deterministic substitutes purely to avoid inference cost**.`

**Reason:** "a negative one" reads as a judgement on the development; "a subtraction" says what is meant.

---

### P3 — Sourcing note repeats its own frame three times

**Location:** line 30.

**Current:** `One note on sourcing: the specific model generation and its published positioning were supplied by the project owner and are taken as given here. They are not independently verified in this document, and nothing in the PRD depends on them — the PRD names no model by design, so the claim is load-bearing for cost planning only.`

**Recommended replacement:** `One note on sourcing: the specific model generation and its published positioning were supplied by the project owner, are taken as given, and are not independently verified. Nothing depends on them — the PRD names no model by design — so the claim is load-bearing for cost planning only.`

**Reason:** "in this document" / "the PRD" / "the PRD" in two sentences; one statement of scope is enough.

---

### P4 — "pattern" three times in one sentence

**Location:** line 34.

**Current:** `Typed, narrowly-scoped decision models — the pattern behind recent focused-decision APIs and typed decision-model libraries — reinforce a useful implementation pattern: some narrow questions can be delegated to a very small typed decision call instead of invoking a full agent reasoning loop.`

**Recommended replacement:** `Typed, narrowly-scoped decision models — the shape behind recent focused-decision APIs and typed decision-model libraries — make one implementation option concrete: a narrow question can be delegated to a small typed decision call instead of a full Agent reasoning loop.`

**Reason:** "pattern" twice and "narrow" twice inside one sentence; "reinforce a useful implementation pattern" is padding around the actual claim.

---

### P5 — Four one-word bullets

**Location:** lines 36–42.

**Current:**

```markdown
Plausible later applications:

- lightweight classification
- semantic guard conditions
- routing
- prioritisation
```

**Recommended replacement:**

```markdown
Plausible later applications: lightweight classification, semantic guard conditions, routing, prioritisation.
```

**Reason:** a bulleted list of single words costs four lines and a paragraph break to carry one sentence.

---

### P6 — "decide between them"

**Location:** line 47.

**Current:** `The PRD's own instrumentation-first stance (NFR13, NFR14) is what will decide between them, because the strategy is measured rather than designed.`

**Recommended replacement:** `The PRD's instrumentation-first stance (NFR13, NFR14) is what will decide whether either is adopted, because the strategy is measured rather than designed.`

**Reason:** the two developments are not alternatives, so "between them" states a choice that does not exist.

---

### P7 — The rejection paragraph's closing sentence is overloaded

**Location:** line 78, final sentence.

**Current:** `Each of those is a mechanism, not a preference, and together they mean the intelligence layer is precisely the position the record-owner bundles away — it is the first thing they build, and they build it with advantages that cannot be competed away by being better at it.`

**Recommended replacement:** `Each of those is a mechanism, not a preference. Together they make the intelligence layer the first thing the record-owner builds, with advantages no third party can offset by being better at it.`

**Reason:** one sentence carrying three clauses and two uses of "away"; splitting it keeps the force and loses the tangle.

---

### P8 — "as a modesty"

**Location:** line 82.

**Current:** `This is also the reason the PRD states plainly that external business systems remain authoritative (FR36) rather than treating that as a modesty: owning no system of record is a deliberate position whose costs are known.`

**Recommended replacement:** `This is also why the PRD states plainly that external business systems remain authoritative (FR36) rather than as a note of modesty: owning no system of record is a deliberate position whose costs are known.`

**Reason:** "a modesty" is not a noun the register supports, and "states ... rather than treating that as" is a mismatched pair.

---

### P9 — Lesson 1's evidence sentence

**Location:** line 94, second sentence.

**Current:** `Three of four textbook context-and-latency techniques turned out to have no target in that engine at all, or rested on false premises about its shape; one real lever existed.`

**Recommended replacement:** `Of four textbook context-and-latency techniques, three had no target in that engine or rested on false premises about its shape; one was a real lever.`

**Reason:** "turned out to have ... at all, or rested on" strains the parallel, and "one real lever existed" trails the sentence.

---

### P10 — "A separate case found"

**Location:** line 94, third sentence.

**Current:** `A separate case found an asked-for trigger that was structurally impossible to fire.`

**Recommended replacement:** `In a separate case, a requested trigger turned out to be structurally impossible to fire.`

**Reason:** a case does not find anything, and "asked-for" is awkward where "requested" is exact.

---

### P11 — Lesson 3's evidence is one sentence too long

**Location:** line 98, second sentence.

**Current:** `Two logged instances: an empty-but-set environment variable caused every model tier to fail while a mock fallback served plausible deterministic text under a banner claiming live operation — the verification had checked the mode *label*, not a completion; and a fabrication guard presented an honest-sounding decline that masked three stacked retrieval faults.`

**Recommended replacement:** `Two logged instances. An empty-but-set environment variable made every model tier fail while a mock fallback served plausible deterministic text under a banner claiming live operation — the verification had checked the mode *label*, not a completion. And a fabrication guard presented an honest-sounding decline that masked three stacked retrieval faults.`

**Reason:** a colon, a dash and a semicolon in one sentence; three sentences carry the same two instances without the reader holding the structure.

---

### P12 — Lesson 5 says the gate was disabled twice

**Location:** line 104, first evidence sentence.

**Current:** `A ship gate coupled to one domain forced the builder into a rewrite loop, and the prior reaction had been to stub the gate to always pass — the gate was disabled to stop the pain, which is the worst possible outcome and the direct reason for FR95.`

**Recommended replacement:** `A ship gate coupled to one domain forced the builder into a rewrite loop, and the reaction was to stub the gate so it always passed — the check was disabled to stop the pain, which is the worst available outcome and the direct reason for FR95.`

**Reason:** "stub the gate to always pass" and "the gate was disabled" state the same fact in consecutive clauses; naming the second one "the check" keeps the emphasis without the echo.

---

### P13 — Lesson 8 reads as a win, not a lesson

**Location:** line 108.

**Current:** `**Provider agnosticism is enforceable, and it bought two concrete things:** a credential-free continuous-integration gate, because a blank key yields mock mode; and genuine artifact portability. Both are worth preserving, and NFR12 does.`

**Recommended replacement:** `**Provider agnosticism is enforceable, and enforcing it pays twice:** a credential-free continuous-integration gate, because a blank key yields mock mode, and genuine artifact portability. NFR12 preserves both.`

**Reason:** every other block states a rule with a consequence; "it bought two concrete things ... both are worth preserving, and NFR12 does" ends on a dangling verb.

---

### P14 — "assumed rather than trusted"

**Location:** line 110, final sentence.

**Current:** `Documentation and test drift is a live risk in that repository and should be assumed rather than trusted.`

**Recommended replacement:** `Documentation and tests in that repository have drifted before; treat them as claims to verify, not as ground truth.`

**Reason:** the subject is a compound noun that reads as a verb ("test drift is"), and "assumed rather than trusted" inverts what the reader is being told to do.

---

### P15 — "hot path" and "reply path" against the PRD's vocabulary

**Location:** line 94 (`exists on the hot path`), line 96 (`push prose synthesis off the hot path`), line 26 and line 96 (`reply path`).

**Current:** `...confirm the mechanism it targets exists on the hot path.` / `...push prose synthesis off the hot path.` / `a model call on a reply path...` / `**Never add a model call to the reply path in the name of latency.**`

**Recommended replacement:** use the PRD's terms — `the path that matters` (§4.3), `a path a person is waiting on` (§1.3), or `the request path` (FR97). The replacement strings in S7, S8 and S9 already carry this change; if those are not applied, substitute `the hot path` → `the request path` and `the reply path` → `a path a person is waiting on` in place.

**Reason:** three names for one concept across two documents; the PRD's wording is the vocabulary of record and the addendum is the subordinate file.
