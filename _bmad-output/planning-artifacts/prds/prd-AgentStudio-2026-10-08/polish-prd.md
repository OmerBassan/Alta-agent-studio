---
title: "Polish pass — prd-AgentStudio-2026-10-08"
lenses: structure, prose
created: 2026-10-08
scope: "Structure and prose only. No content review, no new requirements, no renumbering of requirement IDs."
---

# Polish findings — Agent Studio PRD

Applied in order: **Structure first, then Prose.** Several prose findings quote text that a
structure finding moves; where that happens the prose finding names the destination.

Requirement IDs are treated as stable. Where a finding recommends a change of position, it is
a **reorder of rows within a table**, never a renumber, and each such finding says so explicitly.

---

## Structure

### S-1 — `FR104` row is split across two physical lines and breaks the table

**Location:** §8.1 table, `FR104` (lines 342–343).

**Current text (two lines, note the newline after `**process**`):**

```
| **FR104** | When an operator narrates a **process**
 — and they will, because that is how people describe their own work — the Builder MUST re-derive it into declared context, policy, capability, authority, goal and obligation, and **persist no ordering**. ...
```

**Recommended replacement** — one physical line:

```
| **FR104** | When an operator narrates a **process** — and they will, because that is how people describe their own work — the Builder MUST re-derive it into declared context, policy, capability, authority, goal and obligation, and **persist no ordering**. The operator may say "first we check the diary, then we take a deposit"; what is recorded is that a deposit is an obligation of a booking goal and that checking availability is a granted capability. Rejection at the validation gate (FR24) is the backstop, not the mechanism: the Builder is where a narrated process stops being a sequence. |
```

**Reason:** a newline inside a GFM table row terminates the table — FR104 and everything after it render as loose text in any conformant renderer.

---

### S-2 — §7.2 restates six of §4.4's rows almost verbatim (highest-value duplication)

**Location:** §4.4 "What this is not" and §7.2 "Out of scope".

**Current duplicated pairs:**

| §4.4 | §7.2 |
|---|---|
| `A vertical product \| Not a booking, appointment, healthcare, sales or FAQ product. Any vertical framing is out` | `Any vertical framing \| Not a booking, appointment, healthcare, sales or FAQ product` |
| `An outbound or proactive system \| An episode is initiated or resumed only by an inbound interaction or an external system event. The platform never independently starts an outbound conversation or episode` | `Platform-initiated outbound conversation \| Architecturally forbidden, not merely descoped` |
| `A system of record \| External business systems stay authoritative` | `Owning any system of record \| External business systems stay authoritative` |
| `An autonomous planner \| ... No decomposition of goals into agent-generated plans` | `Agent-generated planning or goal decomposition \| ` |
| `A memory product \| No general long-term customer memory, no cross-episode profiling` | `Long-term customer memory, cross-episode profiling, proactive outreach \| ` |
| `A self-modifying system \| Behaviour changes are reviewed and promoted, never silently mutated` | `Continuous automatic learning \| Behaviour changes are reviewed and promoted, never silently mutated` |

**Canonical:** §4.4. Those six are *permanent product identity* exclusions, not V1 scoping decisions.

**Recommended replacement** — delete those six rows from §7.2 and insert one row at the top of the §7.2 table in their place:

```
| Everything §4.4 excludes as product identity — vertical framing, platform-initiated outbound, owning a system of record, agent-generated planning, long-term memory and cross-episode profiling, continuous automatic learning | Out permanently rather than out of V1. §4.4 is canonical; this table lists only what is out of **V1** |
```

The §7.2 table then reads: that row, then `Voice`, `Multi-tenant hosting…`, `Domain-specific regulatory packs`, `Metrics dashboard…`, `Integration catalog…` — all five genuinely temporal.

**Reason:** the same six rules are asserted twice in slightly different wording, and the two tables now mean different things (permanent versus V1) while looking identical.

---

### S-3 — §1.5 opens by restating §4.1's novelty list verbatim

**Location:** §1.5, first two sentences.

**Current text:**

> The platform claims no novelty in model-in-charge agents, harnesses, tool calling, declarative agent configuration, or representing business rules as data. All are established practice. The claim this product actually makes, and the one V1 exists to falsify, is narrower:

**Recommended replacement:**

> What is and is not claimed as novel is settled in §4.1 — none of the established patterns there is claimed. The claim this product actually makes, and the one V1 exists to falsify, is narrower than any of them:

**Reason:** §4.1 ("Not claimed: model-in-charge agents, agent harnesses, tool calling, declarative agent configuration, business rules represented as data") is the same list in the same order; Positioning should own it and Vision should point.

---

### S-4 — The "no principle for elegance" rule is asserted in both §1.3 and §4.3

**Location:** §1.3, final paragraph; §4.3, condition 3.

**Current text (§1.3):**

> ...keep prose synthesis off any path a person is waiting on; and never adopt a determinism-for-elegance argument without measuring the path it targets first.

**Recommended replacement (§1.3):**

> ...keep prose synthesis off any path a person is waiting on; and hold to §4.3's third standing condition, which generalises the point past determinism.

**Reason:** §4.3 condition 3 states the rule as a veto with its full test ("Confirm the mechanism it targets exists on the path that matters, and measure that path"); §1.3 states a weaker version of the same rule eighty lines earlier. §4.3 is canonical.

---

### S-5 — FR18 and FR24 both own the validation rejection of sequencing

**Location:** §8.2 `FR18`; §8.3 `FR24`.

**Current text (FR18):**

> The specification MUST NOT be able to express ordering or sequencing. The authoring surface makes sequencing unexpressible, and validation rejects any such construct with a message the operator can act on.

**Recommended replacement (FR18):**

> The specification MUST NOT be able to express ordering or sequencing. The authoring surface makes sequencing unexpressible; validation is the backstop, not the mechanism (FR24).

**Reason:** FR24 ("Validation MUST reject sequencing constructs, with a comprehensible reason") is the canonical validation requirement; FR18's second clause duplicates it, and the phrasing of the operator-facing message differs between the two.

---

### S-6 — FR12 and FR91 define the same measurement twice

**Location:** §8.1 `FR12`; §8.11 `FR91`.

**Current text (FR91):**

> **Setup effort** is recorded per business: wall-clock time and number of source artifacts to a passing validation suite.

**Recommended replacement (FR91):**

> **Setup effort** is recorded per business from the Builder's own burden instrumentation (FR12), and compared across the four in the order they were built.

**Reason:** "wall-clock time and number of source artifacts to a passing validation suite" is FR12's definition word for word; FR91's distinct content is the per-business, across-the-sequence comparison.

---

### S-7 — §10.3 restates FR89, FR90 and FR91's definitions

**Location:** §10.3 table, first cell of each row.

**Current text:**

```
| **Engine leaks** — every instance where the Core had to change rather than the business layer, classified as *should have been configuration*, *justifies an extension point*, or *genuinely novel* | ...
| **Resolution-model strain** — whether any business needs a resolution the model cannot express | ...
| **Setup effort** — wall-clock time and number of source artifacts to a passing validation suite | ...
```

**Recommended replacement:**

```
| **Engine leaks** — every instance where the Core had to change rather than the business layer, classified per FR89 | ...
| **Resolution-model strain** — per FR90 | ...
| **Setup effort** — per FR91 | ...
```

**Reason:** §8.11 owns the definitions as requirements; §10.3 owns the failure conditions. Keeping both halves in both places is what let the classification wording drift once already.

---

### S-8 — §7.4 mentions bounded budgets and the stall detector in two rows

**Location:** §7.4 table, row 1 ("Reusable largely as-is", final sentence) and row 4 ("Deliberately not carried forward", inventory list).

**Current text (row 1, final sentence):**

> Two of these, bounded tool budgets and the stall detector with a wired handoff, are now required rather than merely available (FR107)

**Recommended change:** delete that sentence from row 1 (ending row 1 at `one-core-many-front-doors`), and append to the end of row 4:

> Two items in that inventory — the bounded tool budget and the stall detector with a wired handoff — are now **required** rather than merely available (FR107).

**Reason:** row 4 already carries the inventory those two items belong to; row 1 names them a second time in a list that is otherwise about reusable assets, not required ones.

---

### S-9 — `FR117` interrupts §8.1's arc

**Location:** §8.1 table, `FR117` currently sits between `FR11` and `FR12`.

**Recommended change:** move the `FR117` row so it sits immediately after `FR6`. **This is a row reorder within one table; the ID is unchanged.** The table then reads FR1–FR6, FR117, FR7–FR11, FR12, FR99, FR104, FR100.

**Reason:** FR1–FR11 is the elicitation-to-promotion arc and FR12/FR99/FR100 is the measurement arc; FR117 is about failure outcomes and belongs next to FR6, the other requirement that forbids presenting something incomplete as complete.

---

### S-10 — `FR113` precedes the adapter it assigns ownership to

**Location:** §8.10 table, `FR113` currently sits between `FR83` and `FR84`.

**Recommended change:** move the `FR113` row to immediately after `FR85`. **Row reorder within one table; ID unchanged.** Order becomes FR83, FR84, FR85, FR113, FR86, FR87, FR98, FR114, FR103, FR112.

**Reason:** FR113 assigns shaping to "the channel adapter", which FR84 introduces and FR85 makes replaceable; as written the reader meets the owner before the thing exists.

---

### S-11 — `O9` is out of order at the end of §11

**Location:** §11 table — rows run O1…O8, O10, O11, O9.

**Recommended change:** move the `O9` row to sit between `O8` and `O10`. **Row reorder; ID unchanged.**

**Reason:** a late append left the only numeric break in an otherwise ordered table, and it is the one table in the document where readers navigate by identifier.

---

### S-12 — §9's NFR table is 18 dense rows with no scanning structure

**Location:** §9, single table NFR1–NFR18.

**Recommended change:** split into four tables under `####` subheadings, in the existing numeric order — no NFR moves:

- `#### 9.1 Integrity and evidence` — NFR1–NFR6
- `#### 9.2 Change, reproducibility and consistency` — NFR7–NFR9
- `#### 9.3 Data, secrets and portability` — NFR10–NFR12
- `#### 9.4 Measurement and operation` — NFR13–NFR18

Repeat the header row `| # | Area | Requirement | Quantified? |` and `|---|---|---|---|` in each. The §9 preamble paragraph stays where it is, above 9.1.

**Reason:** the grouping is already latent in the numbering, and this is the only table in the document long enough that a reader loses the column meanings before the end of it. §9 is currently the one top-heavy section with no subsections.

---

### S-13 — FR8 carries an economics argument that does not belong in a table cell

**Location:** §8.1 `FR8`, from "One further guard" to the end of the cell.

**Current text (tail of the cell):**

> One further guard, which is about economics rather than architecture: a per-vertical library was rejected because **its cost scales with the number of verticals**, and a starting point reintroduces that axis if it is allowed to become the thing being maintained. Starting points are therefore seeded *from specifications businesses already wrote* rather than authored per vertical, and a starting point is never a prerequisite for a business type nobody has built yet.

**Recommended change:** end the `FR8` cell after "It is a specification starting point, never a behaviour template." and add this paragraph immediately below the §8.1 table (above §8.2):

> **Why starting points are seeded rather than authored (FR8).** A per-vertical library was rejected on economics, not architecture: its cost scales with the number of verticals, and a starting point reintroduces that axis if it is allowed to become the thing being maintained. Starting points are therefore seeded *from specifications businesses already wrote*, and a starting point is never a prerequisite for a business type nobody has built yet.

**Reason:** FR8 is the longest cell in the document and ends up stating four normative rules plus a rejected-alternative rationale; the rationale is not a requirement and is unreadable in a table cell.

---

### S-14 — §11.1 is separated from §11 by a horizontal rule, unlike every other subsection

**Location:** the `---` on the line immediately before `### 11.1 Assumptions index`.

**Recommended change:** delete that `---` line.

**Reason:** `---` is used throughout as a top-level section separator only; keeping it here makes 11.1 look like a section that was never given a number of its own.

---

### S-15 — §6 defines no entry for **Requester**, a role used normatively

**Location:** §6 vocabulary table.

**Recommended change:** insert after the `Episode` row:

```
| **Requester** | The person who brings an inbound request to the Agent. Known only by role; the platform never initiates contact with them |
```

**Reason:** §6 states "this document uses no others for these concepts", and FR111 and FR112 both impose obligations on "the requester" — the one normative actor the vocabulary of record omits.

---

### S-16 — MD025: two top-level headings

**Location:** frontmatter `title:` (line 2) and the H1 at line 8.

**Recommended minimal fix (preferred, keeps both):** add `.markdownlint.json` beside the document, or extend the repo's existing config, with:

```json
{ "MD025": { "front_matter_title": "" } }
```

**In-document alternative if no config is wanted:** delete line 8 (`# Agent Studio — Business-Specific Agent Platform`) and the blank line after it; the frontmatter title then carries the document name.

**Reason:** the frontmatter title is machine-read by the planning toolchain, so suppressing the rule is cheaper than removing either title.

---

### S-17 — MD036: emphasis used as a heading

**Location:** line 10.

**Current text:**

```
**Product Requirements Document · V1**
```

**Recommended replacement:**

```
Product Requirements Document · V1
```

**Reason:** dropping the emphasis clears MD036 without inventing an H2 subtitle or disturbing the §1 numbering; the line reads identically as a subtitle under the H1.

---

## Prose

### P-1 — §3.4 hedges in a document that does not hedge

**Location:** §3.4, first sentence.

**Current text:**

> ...and that is close to a choice rather than an omission:

**Recommended replacement:**

> ...and that is a choice rather than an omission:

**Reason:** "close to a" is the only softening qualifier in a paragraph whose whole point is to state the evidence position flatly.

---

### P-2 — "obtainable" breaks a phrase used identically twice elsewhere

**Location:** §3.4.

**Current text:**

> while **no primary operator evidence has been obtainable**

**Recommended replacement:**

> while **no primary operator evidence has been obtained**

**Reason:** §2 and §13.1 both say "has been obtained"; "obtainable" additionally asserts impossibility rather than absence, which is a different and stronger claim.

---

### P-3 — §1.2 repeats "collapse" inside one sentence

**Location:** §1.2, first paragraph.

**Current text:**

> These are routinely collapsed, and collapsing them produces either an over-promising PRD or an under-ambitious one.

**Recommended replacement:**

> These are routinely collapsed, which produces either an over-promising PRD or an under-ambitious one.

**Reason:** the repetition adds no emphasis and the sentence is shorter without it.

---

### P-4 — FR40 uses "kind" four times in three sentences

**Location:** §8.5 `FR40`.

**Current text:**

> The Agent emits one of a **closed** set of request kinds, and **every kind is authorized and journaled, reads included**. The set is closed in both directions: a business's capability model is a *grant over the existing kinds*, and no business can introduce a new kind — "a new kind of thing the Agent can do" is a platform release, never onboarding (FR58). The set carries **no precedence and no ordering** among its members.

**Recommended replacement:**

> The Agent emits one of a **closed** set of request kinds, and **every kind is authorized and journaled, reads included**. Closure runs in both directions: a business's capability model is a *grant over the existing kinds*, and nothing a business declares can add one. Widening the Agent's repertoire is a platform release, never onboarding (FR58). The set carries **no precedence and no ordering** among its members.

**Reason:** the word carries the requirement, so repeating it five times in a row blurs rather than reinforces it; splitting the long middle sentence also separates the two distinct rules it was carrying.

---

### P-5 — FR32's central sentence is three claims in one clause chain

**Location:** §8.4 `FR32`, second sentence.

**Current text:**

> **This is a requirement on the system, enforced by FR33 at the level of reference integrity, and it is not a claim that meaning is verified.**

**Recommended replacement:**

> **FR33 enforces this at the level of reference integrity. It is not a claim that meaning is verified.**

**Reason:** the original buries the enforcing requirement in an apposition and then negates something that was never asserted in the same breath; two sentences say both things cleanly.

---

### P-6 — FR108 buries its requirement behind two sentences of diagnosis

**Location:** §8.9 `FR108`.

**Current text:**

> Denial classification (FR77) covers only outcomes the Core **refused**. The dominant failure mode is the opposite one — an answer that was permitted, confident and **wrong** — and it produces no denial and therefore no divergence record. A recorded human correction (FR102) is therefore a **first-class divergence source alongside denials**, classified the same way and entering the same backlog. Without this the operator's primary surface is structurally blind to the failure class that matters most.

**Recommended replacement:**

> A recorded human correction (FR102) is a **first-class divergence source alongside denials**, classified under FR77 and entering the same backlog. Denial classification covers only outcomes the Core **refused**, and the dominant failure mode is the opposite one — an answer that was permitted, confident and **wrong**, which produces no denial and therefore no divergence record. Without corrections as a source, the operator's primary surface is structurally blind to the failure class that matters most.

**Reason:** the requirement was the third sentence; a reader scanning first clauses saw a restatement of FR77 instead.

---

### P-7 — FR115 has the same buried-requirement shape

**Location:** §8.9 `FR115`.

**Current text:**

> A **wrong refusal is invisible by construction**: a correct denial and an over-strict one are both recorded as a business refusal, only specification defects reach the backlog (FR78), and the person who was wrongly refused does not come back to complain. Left alone this is selection bias with a feedback loop attached — the specification drifts toward strictness and the metrics improve while it happens. The product MUST therefore sample business refusals for human adjudication, at a rate the business sets, and a refusal found wrong on adjudication enters the backlog as a specification defect.

**Recommended replacement:**

> The product MUST sample business refusals for human adjudication, at a rate the business sets, and a refusal found wrong on adjudication enters the backlog as a specification defect. Without this a **wrong refusal is invisible by construction**: a correct denial and an over-strict one are both recorded as a business refusal, only specification defects reach the backlog (FR78), and the person who was wrongly refused does not come back to complain. Left alone that is selection bias with a feedback loop attached — the specification drifts toward strictness and the metrics improve while it happens.

**Reason:** the MUST was last; FR115 and FR108 are adjacent rows with the same inverted shape, which makes the whole section read as commentary.

---

### P-8 — FR116 states three definitions inside one sentence

**Location:** §8.6 `FR116`.

**Current text:**

> Variation between businesses resolves at exactly **three levels**, and which level a need lands at is a recorded judgement: **configuration**, the expected path covering the great majority of cases; a **supported extension point**, for capability that recurs across businesses but is structurally unlike configuration — a leaf behind a declared contract, such as identity verification, document intake, a derived figure, a validator or a scorer; and **custom implementation**, which is the exception and never the path. This is the taxonomy FR89 classifies engine leaks against, so it must be defined here rather than assumed.

**Recommended replacement:**

> Variation between businesses resolves at exactly **three levels**, and which level a need lands at is a recorded judgement. **Configuration** is the expected path and covers the great majority of cases. A **supported extension point** takes capability that recurs across businesses but is structurally unlike configuration — a leaf behind a declared contract, such as identity verification, document intake, a derived figure, a validator or a scorer. **Custom implementation** is the exception and never the path. This is the taxonomy FR89 classifies engine leaks against, so it is defined here rather than assumed.

**Reason:** the semicolon chain carries a nested em-dash definition and no longer parses on one read; "must be defined here" also describes the document's own duty rather than the product's.

---

### P-9 — §7.4 row 1 runs a semicolon list into an embedded exception

**Location:** §7.4 table, row 1 ("Reusable largely as-is").

**Current text (the relevant stretch):**

> ...the human-authorization interrupt; off-thread tool execution (FR97); the structured-verdict-then-deterministic-text pattern — **bounded by FR44**: it may render a Core-owned notice such as the terminal notice of FR111, and may never become a guard that composes the Agent's reply; the validated integrations catalog; one-core-many-front-doors.

**Recommended replacement:**

> ...the human-authorization interrupt; off-thread tool execution (FR97); the structured-verdict-then-deterministic-text pattern; the validated integrations catalog; one-core-many-front-doors. One of these is bounded: the structured-verdict-then-deterministic-text pattern may render a Core-owned notice such as the terminal notice of FR111, and may never become a guard that composes the Agent's reply (FR44).

**Reason:** the exception was spliced into the middle of a semicolon list, so the two list items after it read as part of the exception.

---

### P-10 — NFR5's final clause restates the clause before it

**Location:** §9, `NFR5`.

**Current text:**

> ...scoped strictly to *reference validity* — it makes no assertion about meaning, which is NFR6's subject. The two are not in tension because they govern different properties

**Recommended replacement:**

> ...scoped strictly to *reference validity* — it makes no assertion about meaning, which is NFR6's subject

**Reason:** "they govern different properties" is the sentence immediately preceding it, restated as reassurance.

---

### P-11 — FR73's closing sentence defends itself instead of requiring anything

**Location:** §8.8 `FR73`, final sentence.

**Current text:**

> The last group is not an afterthought: NFR13 and NFR14 mandate latency and cost instrumentation, and this is the record they read from.

**Recommended replacement:**

> The last group is the record NFR13 and NFR14's instrumentation reads from.

**Reason:** "is not an afterthought" argues with an imagined reader; the cross-reference is the content.

---

### P-12 — §4.3's preamble ends on a statement about documents

**Location:** §4.3, preamble.

**Current text:**

> Stated as conditions rather than opinions, because each one is a veto that can reject an otherwise attractive direction, and a document that loses them cannot be checked against them.

**Recommended replacement:**

> Stated as conditions rather than opinions, because each one is a veto that can reject an otherwise attractive direction.

**Reason:** the trailing clause gives a reason for writing anything down at all, and the same move appears in §13's preamble where it does real work.

---

### P-13 — §5's closing line is padding

**Location:** §5, final line.

**Current text:**

> A smaller document with falsifiable acceptance criteria is preferred over a confident-looking one that assumes the hard part is solved.

**Recommended change:** delete the line.

**Reason:** it states a preference about documents rather than a posture about the product, and the section's own table plus the acceptance blockquote above it already establish the posture — this is the one place in §5 that asserts nothing checkable.

---

### P-14 — The A4 assumption is a sentence fragment

**Location:** §2.

**Current text:**

> **[ASSUMPTION A4]** That such a person exists, is reachable, and can articulate those rules when interviewed.

**Recommended replacement:**

> **[ASSUMPTION A4]** Such a person exists, is reachable, and can articulate those rules when interviewed.

**Reason:** the leading "That" leaves the clause dependent on the preceding blockquote, so the assumption never reaches a main verb; A1–A3 are all stated as full sentences.

---

### P-15 — The A2 assumption chains three clauses

**Location:** §2, final paragraph.

**Current text:**

> **[ASSUMPTION A2]** §13.1 concedes these specifications are constructions rather than any real business's rules; treating them as an adequate substitute is defensible for the *architecture* claim and explicitly not for the *usefulness* claim, which is why FR92 requires one real business.

**Recommended replacement:**

> **[ASSUMPTION A2]** These specifications are constructions, not any real business's rules (§13.1). Treating them as an adequate substitute is defensible for the *architecture* claim and explicitly not for the *usefulness* claim, which is why FR92 requires one real business.

**Reason:** the original opens on a cross-reference rather than the assumption, and the cross-reference is doing the work of a parenthesis.

---

### P-16 — "Working segment set" is terminology residue

**Location:** §2, the bolded lead-in to the four-business table.

**Current text:**

> **Working segment set.** Four businesses carry the generalisation test, chosen for deliberate anti-vertical diversity

**Recommended replacement:**

> **The four exemplar businesses.** They carry the generalisation test, chosen for deliberate anti-vertical diversity

**Reason:** §8.11, §12 (E12) and §13.1 all call these the exemplar businesses; "segment" is the only survival of the pre-unification vocabulary and reads as market segmentation, which §4.3 condition 2 explicitly rejects.

---

### P-17 — Mixed `-ise`/`-ize` on "authorize"

**Location:** §4.5 and §8.2 `FR17`.

**Current text (§4.5):**

> ...are constrained, authorised, verified and recorded deterministically

**Recommended replacement (§4.5):**

> ...are constrained, authorized, verified and recorded deterministically

**Current text (FR17):**

> an Agent may be authorised to say that overwatering is almost certainly the problem

**Recommended replacement (FR17):**

> an Agent may be authorized to say that overwatering is almost certainly the problem

**Reason:** "authorized" appears six times (FR40, FR45, FR53, FR58, NFR4, §6) and "authorization" three; these two are the only `-ised` spellings, and the term is a defined one in §6.

---

### P-18 — §13.1's differentiation bullet restates §4.2 without citing it

**Location:** §13.1, final bullet.

**Current text:**

> The differentiation claim is narrow by necessity: the declarative-specification paradigm is validated and widely held at the enterprise tier, and no moat is claimed.

**Recommended replacement:**

> The differentiation claim is narrow by necessity: the declarative-specification paradigm is validated and widely held at the enterprise tier, and no moat is claimed (§4.2).

**Reason:** §13 cites a source for every other limitation it summarises; this is the one bullet that re-asserts a §4.2 conclusion as if it were new.

---

## Noted and deliberately left alone

Recorded so they are not re-flagged on a later pass:

- **NFRs restating FRs** (NFR4/FR70, NFR2/FR55, NFR9/FR65, NFR11/FR57). §9's preamble declares the restatement — "restated here rather than reinvented" — so these are a stated convention, not duplication.
- **§6 vocabulary restating requirement text** (`Evidence`, `Safety halt`, `Guard condition`). A vocabulary of record is expected to quote the requirement it defines, and each row already cites the FR.
- **"Never improvise a rule." in both FR6 and FR48.** Same sentence, different actors — Builder-side and runtime-side — and the echo is the point.
- **§1.1's "the authoring surface must make sequencing unexpressible" against FR18.** §1.1 is the thesis statement and FR18 the requirement; if a cross-reference is wanted, append `(FR18)` to the §1.1 sentence, but the repetition is load-bearing there.
