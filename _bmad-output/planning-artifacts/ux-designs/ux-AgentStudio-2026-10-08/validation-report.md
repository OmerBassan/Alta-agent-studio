# Validation Report — Alta Agent Studio (V1)

- **DESIGN.md:** `DESIGN.md`
- **EXPERIENCE.md:** `EXPERIENCE.md`
- **Run at:** 2026-10-10 18:02

## Overall verdict

Before fixes, the rubric judged the spines a clear statement of intent but not yet a clean contract for builders. Several rules lived only in the mocks: the Not-established tint, the focus ring, the mapping from divergence class to rule shape, and the suspended-state copy. The contrast table was wrong. The closed vocabulary was promised but not listed. No surface showed whether the Agent was live, so an empty Activity list read as good news.

The accessibility lens agreed the goals were right but found the specification could not be built to WCAG 2.2 AA as written: no focus style, no accessibility rules for the new panes and collapsible sections, status messages specified for only one surface, and an emergency brake whose result was never announced.

All critical and high findings from both reviewers have been addressed in the spines, as recorded below. The contrast arithmetic was independently recomputed by the facilitator and matched the reviewers. One factual error surfaced during review: PRD FR84 does name inbound email / messaging as the V1 channel, so the spine's claim that the channel was a UX-originated decision was wrong. The decision is unchanged; its provenance is corrected. Remaining open items are either recorded upstream contract gaps or deliberate refinement items.

## Category verdicts (before fixes)

- Flow coverage — thin
- Token completeness — thin
- Component coverage — thin
- State coverage — thin
- Visual reference coverage — adequate
- Bloat & overspecification — adequate
- Inheritance discipline — thin
- Shape fit — adequate

## Findings by severity

### Critical (2)

**[Token completeness]** Not-established tint had no token (DESIGN.md Colors)
The mock used #FBF1E8 with no spine source.
Outcome: Resolved: state-not-established-band '#FBF1E8'.

**[Accessibility]** Suspend's outcome is not announced; resume is styled like Suspend (Suspend, 4.1.3)
Outcome: Resolved: the result is announced and shown in the status line; failure is stated; resume is a secondary action.

### High (14)

**[Flow coverage]** No failure paths in any Key Flow (EXPERIENCE.md Key Flows)
Even failures the spine itself names were missing from the flows.
Outcome: Resolved: each flow now has a 'When it goes wrong' paragraph covering failures the spine already names.

**[Flow coverage]** Judging sampled refusals (FR115) had no surface and no recorded gap (EXPERIENCE.md Amendments)
Divergences from this source need someone to judge them first.
Outcome: Recorded as Amendments item 15. Not designed in V1.

**[Token completeness]** Stated contrast ratios did not match the hex values (DESIGN.md Colors)
Hairline is 1.37:1 (stated 3.0) and border-strong is 3.41:1 (stated 4.6).
Outcome: Resolved: table recomputed for page, raised and sunken. Hairline is decorative only and may never be a control's only edge.

**[Token completeness]** text-quiet on surface-sunken is 4.32:1 (DESIGN.md Colors, key-diff mock)
Below 4.5:1 for small text.
Outcome: Resolved: rule that text-quiet never sits on sunken; text-secondary is used there.

**[Component coverage]** No focus indicator; mocks reused the Changed blue (DESIGN.md Components)
Outcome: Resolved: 2px solid text-body outline, 2px offset, 14.96:1, deliberately not blue.

**[Component coverage]** No spec for actions, including disabled and pending (DESIGN.md Components)
Outcome: Resolved: primary, secondary and suspend actions, disabled with a stated reason, pending with closed-vocabulary text, 44px tall.

**[Component coverage]** Divergence rule shapes undefined and colliding with state shapes (DESIGN.md Shapes)
Solid already meant Changed; double was missing.
Outcome: Resolved: one shape table. Divergence shapes are 4px and 6px-double; state shapes are 2px. The two vocabularies never share a surface.

**[State coverage]** No live, suspended or connected status, so an empty Activity read as good news (EXPERIENCE.md Divergence list)
Outcome: Resolved: an Agent status line is always shown above Activity; the empty state appears only with it. Depends on gaps 4 and 18.

**[Accessibility]** Contrast table wrong; text-quiet fails on sunken (1.4.3, 1.4.11)
Outcome: Resolved, as under Token completeness.

**[Accessibility]** No focus style; mocks use the Changed blue (2.4.7)
Outcome: Resolved: focus indicator defined.

**[Accessibility]** Collapsible sections lack disclosure semantics and hide markers from assistive technology (1.3.1, 4.1.2)
Outcome: Resolved: disclosure buttons report their state, and the accessible name lists contained states; deep links expand the section.

**[Accessibility]** Scrollable panes not keyboard-scrollable and unlabelled (2.1.1, 1.3.1)
Outcome: Resolved: panes are named regions with real headings and are keyboard-scrollable.

**[Accessibility]** Status messages missing for diff, validation, Builder replies and ingestion (4.1.3)
Outcome: Resolved: a list of announced status messages in the Accessibility Floor.

**[Accessibility]** Sticky headers can hide focus (2.4.11)
Outcome: Resolved: scroll-padding required for every sticky element.

### Medium (18)

**[Flow coverage]** Rollback (FR26) neither designed nor recorded as absent (Version and lifecycle states)
Outcome: Recorded as Amendments item 16.

**[Flow coverage]** Effects-only suspend and resume undescribed (Flow 5, Suspend)
Outcome: Resolved: Suspend is one press with no confirmation; Stop actions only sits beside it; resume is a secondary action; results are announced.

**[Flow coverage]** Flows used 'episode', 'retrieved' and 'evaluation case' (Flows 2 and 3)
Outcome: Resolved: replaced with interaction, the reply's basis, and 'what good looks like here'.

**[Token completeness]** Typography had a scale but no roles (DESIGN.md Typography)
Outcome: Resolved: seven role objects (page-title, section-heading, document-body, pane-heading, label, meta, action). Label floor raised to 12px.

**[Component coverage]** Blocking vs not-blocking cue undefined (Validation result)
Outcome: Resolved: 2px full border plus a Blocking label, versus a Not blocking label with no border.

**[Component coverage]** Established labelled or not was ambiguous (Item state marker)
Outcome: Resolved: all four states are labelled.

**[Component coverage]** Degraded conditions had no visual treatment (DESIGN.md Components)
Outcome: Resolved: Degraded notice component.

**[State coverage]** Missing failure states: Builder turn, validation could not run, approval failed, suspend failed (State Patterns)
Outcome: Resolved: new Failure and in-between states table.

**[State coverage]** Missing in-progress, unloadable record and mailbox disconnection states (State Patterns)
Outcome: Resolved in the same table; mailbox status is recorded as gap 18.

**[State coverage]** No platform-error reference (NFR16) (State Patterns)
Outcome: Resolved: a reference code is shown with every platform error. Its format is gap 17.

**[State coverage]** Escalation email omitted FR103's link to the interaction (The Escalation Email)
Outcome: Resolved: the link is included; the email stays actionable without it; the link requires sign-in.

**[Visual reference coverage]** Mocks carried rules the spines did not (mockups/)
Outcome: Resolved: the tint, focus, shape mapping and suspend copy are now in the spines. DESIGN.md refinement item 5 lists where the mocks now lag.

**[Bloat & overspecification]** Long source restatement in EXPERIENCE.md (Throughout)
Outcome: Deferred: partly reduced (DESIGN.md now points to canonical lists instead of repeating them). EXPERIENCE.md quotes are kept as traceability for this pass.

**[Inheritance discipline]** Channel provenance claim was factually wrong (EXPERIENCE.md Foundation, Amendment 2)
PRD FR84 names inbound email / messaging.
Outcome: Resolved: provenance corrected; the decision is unchanged.

**[Inheritance discipline]** Glossary drift (Affected, episode, component ids) (Both spines)
Outcome: Resolved: full state names, interaction everywhere operator-facing, and an id-to-component mapping in DESIGN.md.

**[Shape fit]** DESIGN.md frontmatter not spec-shaped (DESIGN.md frontmatter)
Outcome: Resolved: name, description and sources added; flat kebab-case colors; typography role objects; rounded and spacing scales; components object.

**[Accessibility]** Target sizes unnumbered; 200% text, reflow at 320 and accessible sign-in unaddressed (2.5.8, 1.4.4, 1.4.10, 3.3.8)
Outcome: Resolved: 24px floor, 44px actions, 320px reflow, 200% text and 3.3.8 stated.

**[Accessibility]** Focus return after navigation unspecified (2.4.3)
Outcome: Resolved.

### Low (1)

**[Accessibility]** Remaining low findings (CSS-generated content, links styled as buttons, double rule at small size, and others) (review-accessibility.md)
Outcome: Mostly resolved in the spines (labels are real text, actions are real buttons, the double rule is 6px). The mocks still show some of them; spines win.

## Mechanical notes

- Both spines now carry sources: frontmatter pointing at the PRD, Architecture Spine and Product Brief.
- Each spine states once that it outranks the mocks.
- The mocks in mockups/ predate this revision in four ways: focus colour, 11px labels, text-quiet on sunken in key-diff, and no Agent status line. DESIGN.md refinement item 5 records this.
- Contrast figures were recomputed by the facilitator with the WCAG relative-luminance formula, and matched both reviewers.

## Reviewer files

- `review-rubric.md`
- `review-accessibility.md`
