# Spine Pair Review — Alta Agent Studio (V1)

Reviewer: rubric walker. Inputs: `DESIGN.md`, `EXPERIENCE.md`, `mockups/` (5 files), `.memlog.md` (decisions treated as settled), `.working/extract-prd.md` (spot checks only). Settled context, not flagged: no named personas, light theme only, contract gaps already recorded in EXPERIENCE.md "Amendments and Upstream Gaps".

## Overall verdict

The pair is a strong statement of product intent. The prohibitions, the two voices, the four item states, the three divergence kinds and the gap register are clear, and they follow the memlog closely. It is not yet a clean build contract. The colour section has a "Not established" tint with no token, contrast figures that don't match their own hex values, and no focus indicator. Several rules that builders will need exist only in the mocks: which left rule marks which divergence class, the suspended-state copy, and the focus ring. EXPERIENCE.md promises a closed status vocabulary but never lists it. And no surface tells the operator whether the Agent is live, suspended or reachable, so an empty Activity list looks like good news.

## 1. Flow coverage — thin

Checked: no `sources:` frontmatter, so requirement and journey names came from `.working/extract-prd.md` §8: the inferred journeys Build, Improve, Stop, Receive escalation, Adjudicate a sampled refusal and Connect a starting point. Each journey was matched against the five Key Flows, and each flow was checked for numbered steps, a climax beat and a failure path. Protagonists are role titles plus exemplar businesses by decision, so they were not checked. Build maps to Flow 1, Improve to Flow 2, Stop to Flow 5 and Receive escalation to Flow 4. Connect a starting point was removed by decision (memlog override, templates out of V1).

### Findings

- **high** None of the five flows has a failure path, even where the spine itself names the failure. Flow 1 is missing a material parse failure and a blocking validation finding. Flow 2 is missing push-back on the diff and a blocking finding after the operator confirms. Flow 4 is missing the case where no escalation address has been declared. Flow 5 is missing a suspend that fails or doesn't apply on a phone connection. (EXPERIENCE.md Key Flows, lines 471–533). *Fix:* add one "Failure:" line per flow, written in closed-vocabulary terms, as the examples do.
- **high** "Adjudicate a sampled refusal" (FR115) has no flow and no surface, and it is not in Amendments. The list of divergence sources (line 280) says sampled refusals that were judged wrong arrive in Activity, but nothing says where or how the operator does the judging. The business-set sampling rate also has no place in Understanding. (EXPERIENCE.md Component Patterns › Divergence list). *Fix:* either specify the judging act (for example, a sampled refusal opens in the interaction viewer, where "This was wrong" is the judgement) or record it as an upstream gap.
- **medium** The PRD's "Improve" journey includes "promote (or roll back)" (FR26). The spines give no rollback affordance and don't record its absence. (EXPERIENCE.md Version and lifecycle states). *Fix:* state that rollback is out of V1 or record it as a gap. Today a builder can't tell which.
- **medium** Flow 5 says "one action, optionally effects-only" and "reversible", but never says how the operator chooses effects-only within one action, or describes resuming. The mock shows "Suspended, answering only" copy the spine never states. (EXPERIENCE.md Flow 5, lines 528–533; Suspend, line 315). *Fix:* add the choice mechanism and a resume step; keep the gap 4 note for the data.
- **medium** Flows 2 and 3 use operator-facing words that the Voice and Tone section forbids: "the **episode**" (lines 493, 494, 495, 516), "retrieved the relevant venue information" and "the evaluation case" (line 503). Builders lift flow prose as copy. *Fix:* use "interaction", "used your venue material" and "what good looks like here".

## 2. Token completeness — thin

Checked: every frontmatter token in DESIGN.md, the token tables, every token named in prose, and every colour used in the mocks. Each hex was recomputed with the WCAG relative-luminance formula against `surface.page`, `surface.raised` and `surface.sunken`. Every defined colour token has a hex value.

### Findings

- **critical** The "Not established" **tinted band** has no colour token, although DESIGN.md calls this state "the most important colour decision in the product" and gives it a "dashed bracket + tinted band" (lines 136–140). The mock uses `#FBF1E8`, which is not in the spine. *Fix:* add a token, for example `state.notEstablishedBand: "#FBF1E8"`, with its contrast against `text.body` and `state.notEstablished`.
- **high** The stated contrast ratios don't match the hex values. Recomputed against `surface.page`: `border.hairline` is 1.37 (stated 3.0), `border.strong` 3.41 (stated 4.6), `text.body` 14.96 (stated 16.9), `text.quiet` 4.71 (stated 5.0), `state.notEstablished` 7.83 (stated 6.6), `action.suspend` 9.53 (stated 6.9). This makes the line "every token above meets it" (line 156) false for `border.hairline`. That matters wherever a hairline marks a component boundary or a non-colour cue, such as the collapse controls or the dashed or dotted rules if drawn in hairline. *Fix:* recompute the table, and say which borders are decorative and which mark a UI component boundary under WCAG 1.4.11.
- **high** `text.quiet` on `surface.sunken` is 4.32:1, below the 4.5:1 AA floor for small text. That is the 11–12px metadata label sitting on quoted material. The spine states contrast only "on page". *Fix:* state contrast for each load-bearing pairing (labels on sunken, state colours on the tint band) and darken `text.quiet` or ban that pairing.
- **high** There is no focus indicator token or rule. EXPERIENCE.md requires "a visible focus indicator throughout" (line 401). Every mock uses `outline: 2px solid` in `state.changed` blue, and that choice is recorded nowhere. Reusing the "Changed" colour for focus also collides with a state cue. *Fix:* add a focus token and rule to DESIGN.md, under Colors and Components.
- **medium** Typography has a ten-step scale but no roles. Nothing maps a size to body, pane heading, section heading, item text, small-caps label or diff label, and the frontmatter isn't role objects as the spec expects. The "five identical peer headings" rule depends on this mapping. (DESIGN.md lines 37–43, 166–175). *Fix:* add role tokens (`heading-section`, `label`, `body`, …) that point to scale steps.
- **low** The 50% status dot (line 222) has no defined use or colour. The mock-chrome colours `#E7E2D7` and `#EAE4D8` are untokenised, which is fine if they are chrome only. *Fix:* define the dot's use or remove it.

## 3. Component coverage — thin

Checked: DESIGN.md frontmatter `components` (11 ids), the DESIGN.md Components table (11 rows), EXPERIENCE.md Component Patterns (10 subsections plus the separate Escalation Email section), and component-like names used in IA, Layout, Flows and the mocks.

### Findings

- **high** There is no spec for actions or buttons, although the product hangs on them: Accept, Push back, Approve, Connect, This was wrong, Suspend, Resume, Back, collapse. Only Suspend has a visual rule ("outlined"). The primary and secondary treatment, disabled state (Approve while a blocking finding exists) and pending state are all unspecified. *Fix:* add an "Action" row to DESIGN.md Components and a behavioural row to EXPERIENCE.md.
- **high** The divergence class cues are unspecified and collide with the item-state cues. DESIGN.md says the classes use "solid · double · dashed" left rules (line 254) but never says which class gets which. Shapes (line 238) says dashed, solid and dotted are the *only* shape vocabulary, which leaves out double. A solid left rule already means "Changed". `divergence.specDefect` reuses the `state.notEstablished` hex without explanation, though `businessRefusal` reusing the established green *is* explained. The mapping exists only in `key-activity.html`. *Fix:* state the class-to-rule mapping in DESIGN.md, extend the Shapes vocabulary, and explain or remove the shared hex.
- **medium** Components appear in the prose but have neither spec: the pane heading, the section collapse control with its collapsed-state indicators, the conversation input, and the Connect mailbox surface. Connect mailbox's contents are a recorded gap (Amendment 3), but it still needs a visual and behavioural placeholder row. *Fix:* add rows, marked "pending upstream" where that applies.
- **medium** The "blocking / not blocking" non-colour cue on validation findings is required but not defined (DESIGN.md line 252). *Fix:* name the cue, for example reusing the solid rule plus label.
- **medium** "Item state marker: four states … (· nothing)" (DESIGN.md line 250) conflicts with "every item state … carries a text label" (EXPERIENCE.md line 400). Is "Established" labelled or not? The mocks label it. *Fix:* say explicitly that Established shows its label and no rule.
- **medium** The degraded conditions in State Patterns (safety halt, general knowledge, refused for lack of evidence, consequence class) have behavioural intent but no visual treatment in DESIGN.md Components. *Fix:* add an "Interaction viewer notices" sub-spec.
- **low** The Escalation email's behavioural spec lives in its own section, not under Component Patterns. *Fix:* add a one-line Component Patterns row pointing to it.

## 4. State coverage — thin

Checked: every surface in the inventory against empty, cold-load, pending, error, offline and permission states as they apply. Online-only, single operator and no roles are taken as given.

### Findings

- **high** FR81's closed vocabulary is promised but never written. "Status and failure strings are enumerated in State Patterns below" (line 202), but State Patterns gives only intents ("Must read as …"). Memlog line 53 requires an enumerated lexicon. The only real strings ("Suspended, answering only", "Your rules said no") are scattered through the mocks and the class table. *Fix:* add a State Patterns table with one row per state or failure and its exact string.
- **high** Nothing shows whether the Agent is live, suspended or reachable, so an empty Activity reads as good news. The spine has no empty state for Activity, and no surface shows live, suspended, which version is live, or mailbox connected. Flow 5 says "the state is visible" but not where. A suspended Agent, an unconnected mailbox and a quiet week all render as the same empty list. Gaps 4 and 5 record the *data* contract, not this surface. *Fix:* specify Activity's empty state and an always-visible Agent status line in the Run panes. That line can depend on gaps 4 and 5, but it must be specified.
- **medium** These failure states are missing: a Builder turn that fails or times out; validation that can't run (a platform error during the gate, as distinct from a blocking finding); approval or version creation failing; and a suspend request that fails on mobile. The last matters most: a suspend that silently didn't apply is the worst case for an emergency brake. *Fix:* add rows to State Patterns.
- **medium** States are missing for an interaction that is still in progress (async email, parked goals under FR50 and FR60), for one whose record can't be loaded, and for a mailbox that disconnects after go-live. Amendment 3 covers what the connect screen shows, not how a later disconnection appears. *Fix:* add rows, or record them as gaps.
- **medium** A platform error has no reference the operator can report. NFR16 asks for a correlation identity "reportable by a person who experienced a problem". The "Something on our side failed" framing gives the operator nothing to quote, and this isn't recorded as a gap. *Fix:* add a reference string to the platform-error state, or record it as a gap.
- **medium** The escalation email doesn't mention FR103's required "link to the episode", and doesn't settle how that link fits with "actionable without logging in". *Fix:* state whether the email links to the interaction viewer, and what an operator sees if they are signed out.

## 5. Visual reference coverage — adequate

Checked: the `mockups/` files `direction-ledger`, `key-hero`, `key-interaction`, `key-diff` and `key-activity` (`imports/` is empty, and there is no `wireframes/`). All five are linked from DESIGN.md Status. The four key screens are also linked in EXPERIENCE.md at the matching sections. The statement that the spines win on conflict is present, in three places.

### Findings

- **medium** The mocks carry rules that the spines don't: the class-to-left-rule mapping, the focus outline, the `#FBF1E8` tint, and the suspended-state viewer copy (memlog renderer resolution 4 "stands", but no spine states it). Downstream readers will treat these as spec, with no spine text to win over them. *Fix:* move each of them into the spines, as listed in §2, §3 and §4.
- **low** DESIGN.md links the mocks only in Status, not at the Components rows they illustrate. *Fix:* add inline references on the Correction diff, Interaction viewer and Divergence list rows.
- **low** The statement that the spines win on conflict appears three times (DESIGN.md lines 53 and 57, EXPERIENCE.md line 15). *Fix:* keep one statement per file.

## 6. Bloat & overspecification — adequate

### Findings

- **medium** EXPERIENCE.md restates its sources at length: PRD quotes on most paragraphs, "The lesson that outranks the rest", "The thesis, expressed indirectly", and Product Brief quotes in Responsive. EXPERIENCE.md prose should carry no editorial voice. The citations are useful; the narrative isn't. *Fix:* keep the FR IDs and cut the narrative paragraphs to rules.
- **low** The "must never look like" list and the sequencing prohibition are written out in both spines (DESIGN.md lines 86–96 and 202–204; EXPERIENCE.md lines 149–164 and 539–561). *Fix:* make one canonical copy and have the other spine point to it.

## 7. Inheritance discipline — thin

### Findings

- **medium** The channel provenance claim is factually wrong. EXPERIENCE.md says all three upstream documents "leave the channel open" (lines 53 and 582), but PRD FR84 reads *"V1 ships one channel adapter … inbound email / messaging"* (extract-prd §11.1). The *decision* stands and isn't reopened here. The claim that it originated in UX is the error. *Fix:* reword it as "confirmed by PRD FR84; the Brief left it open".
- **medium** The glossary drifts. The state is named "Affected by this change" in EXPERIENCE.md but "Affected" in DESIGN.md's token and Layout. Internal "episode" leaks into the flows (§1 above). The DESIGN frontmatter's component ids (`conversation`, `stateMarker`, …) aren't mapped to the table names ("Conversation panel", "Item state marker"). *Fix:* give one canonical name per state and component, and add a mapping between ids and names.
- **low** EXPERIENCE.md says it references tokens as `{path.to.token}` (line 11) but contains none. State rules point to DESIGN.md only in prose. *Fix:* reference `{colors.state.notEstablished}` and similar tokens at the State Patterns rows, or drop the claim.

## 8. Shape fit — adequate

### Findings

- **medium** DESIGN.md's frontmatter doesn't follow `design-md-spec.md`. It has no `name` or `description`. `colors` is nested where the spec expects flat kebab-case keys. `typography` isn't role objects. `rounded` is a scalar `0` where the spec expects a scale object. `components` is a list of ids, not a map of component tokens. Downstream token tooling won't resolve it. *Fix:* convert it to the spec shape (for example `state-not-established`, `rounded: {DEFAULT: 0px}`, component token maps).
- **low** DESIGN.md puts an invented "Status" section before Brand & Style; the canonical order is otherwise kept, and "Open refinement items" earns its place. EXPERIENCE.md places Key Flows before Inspiration & Anti-patterns, unlike the examples. The invented sections (The Escalation Email, Amendments and Upstream Gaps, Open Questions) earn their place. *Fix:* fold Status into Brand & Style, or accept it as is.

## Mechanical notes

- No `sources:` frontmatter in either spine. Add the paths to the PRD, the Architecture Spine and the Product Brief.
- DESIGN.md frontmatter is missing `name` and `description`, and its token shapes differ from the spec (see §8).
- Contrast table values are recomputed in §2. Only `border.hairline` and `border.strong` actually fall below the floor the table claims, and `text.quiet` fails on `surface.sunken`.
- No Mermaid is used. The ASCII diagrams in EXPERIENCE.md IA render correctly, and the spine explicitly says they must not appear in the product.
- The link to `.working/direction-almanac.html` from DESIGN.md resolves, but it points into a scratch folder. That is fine as an audit trail; note it if `.working/` is pruned.
- `mockups/key-interaction.html` is the renamed `.working/key-episode.html`, which matches the memlog rename. The memlog event on line 70 says 11 Amendments, and the spine now has 14. That is consistent with later entries.
- Open Question 2 is struck through and marked resolved, which is consistent with the memlog override on line 87.

**Finding counts:** critical 1 · high 9 · medium 17 · low 7.
