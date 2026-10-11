---
name: Alta Agent Studio — Ledger
description: Visual identity for the V1 builder platform where a business operator teaches an Agent how the business works and reviews what it understood. Light theme only. Foundation direction "Ledger", the printed record.
status: final
updated: 2026-10-10
project: AgentStudio
peer: EXPERIENCE.md
sources:
  - ../../prds/prd-AgentStudio-2026-10-08/prd.md
  - ../../architecture/architecture-AgentStudio-2026-10-07/ARCHITECTURE-SPINE.md
  - ../../briefs/brief-AgentStudio-2026-10-07/brief.md
colors:
  surface-page: '#F7F4ED'
  surface-raised: '#FFFDF8'
  surface-sunken: '#EFEAE0'
  border-hairline: '#D9D2C4'
  border-strong: '#8C8372'
  text-body: '#221F19'
  text-secondary: '#5C5447'
  text-quiet: '#756C5C'
  state-established: '#3F4A3A'
  state-not-established: '#7A3A12'
  state-not-established-band: '#FBF1E8'
  state-changed: '#1E4A6B'
  state-affected: '#46637A'
  divergence-spec-defect: '#7A3A12'
  divergence-business-refusal: '#3F4A3A'
  divergence-platform-error: '#4A4458'
  diff-before: '#5C5447'
  diff-after: '#221F19'
  attention-escalation: '#1E4A6B'
  action-suspend: '#6B2B2B'
  focus-ring: '#221F19'
typography:
  page-title:
    fontFamily: 'Georgia, "Iowan Old Style", "Times New Roman", Times, serif'
    fontSize: 23px
    fontWeight: '700'
    lineHeight: '1.25'
  section-heading:
    fontFamily: 'Georgia, "Iowan Old Style", "Times New Roman", Times, serif'
    fontSize: 19px
    fontWeight: '700'
    lineHeight: '1.35'
  document-body:
    fontFamily: 'Georgia, "Iowan Old Style", "Times New Roman", Times, serif'
    fontSize: 17px
    fontWeight: '400'
    lineHeight: '1.75'
  pane-heading:
    fontFamily: '"Segoe UI", system-ui, -apple-system, Helvetica, Arial, sans-serif'
    fontSize: 13px
    fontWeight: '700'
    lineHeight: '1.4'
    letterSpacing: 0.1em
  label:
    fontFamily: '"Segoe UI", system-ui, -apple-system, Helvetica, Arial, sans-serif'
    fontSize: 12px
    fontWeight: '700'
    lineHeight: '1.4'
    letterSpacing: 0.12em
  meta:
    fontFamily: '"Segoe UI", system-ui, -apple-system, Helvetica, Arial, sans-serif'
    fontSize: 13px
    fontWeight: '400'
    lineHeight: '1.5'
  action:
    fontFamily: '"Segoe UI", system-ui, -apple-system, Helvetica, Arial, sans-serif'
    fontSize: 15px
    fontWeight: '700'
    lineHeight: '1.2'
rounded:
  DEFAULT: 0px
spacing:
  '1': 4px
  '2': 8px
  '3': 12px
  '4': 16px
  '5': 24px
  '6': 32px
  '7': 48px
  gutter-mobile: 16px
  target-min: 24px
  target-action: 44px
components:
  action-primary:
    background: '{colors.text-body}'
    foreground: '{colors.surface-raised}'
    radius: '{rounded.DEFAULT}'
    typography: '{typography.action}'
    minHeight: '{spacing.target-action}'
  action-secondary:
    background: transparent
    foreground: '{colors.text-body}'
    border: '1px solid {colors.border-strong}'
    radius: '{rounded.DEFAULT}'
    typography: '{typography.action}'
    minHeight: '{spacing.target-action}'
  action-suspend:
    background: transparent
    foreground: '{colors.action-suspend}'
    border: '2px solid {colors.action-suspend}'
    radius: '{rounded.DEFAULT}'
    typography: '{typography.action}'
    minHeight: '{spacing.target-action}'
  focus-indicator:
    outline: '2px solid {colors.focus-ring}'
    offset: 2px
  state-marker:
    typography: '{typography.label}'
  not-established-item:
    background: '{colors.state-not-established-band}'
    foreground: '{colors.text-body}'
    label: '{colors.state-not-established}'
  pane-heading:
    typography: '{typography.pane-heading}'
    foreground: '{colors.text-secondary}'
    rule: '1px solid {colors.border-hairline}'
---

# DESIGN.md — Alta Agent Studio (V1)

This document owns **how it looks**. [EXPERIENCE.md](EXPERIENCE.md) owns **how it works**. They are peers. Both outrank every mock: where a mock and this document disagree, this document wins.

## Status

The **visual foundation is Ledger**, chosen from four rendered directions ([mockups/direction-ledger.html](mockups/direction-ledger.html)). Key screens built on it: [key-hero](mockups/key-hero.html), [key-interaction](mockups/key-interaction.html), [key-diff](mockups/key-diff.html), [key-activity](mockups/key-activity.html).

Ledger's typography, colour, hierarchy and visual language are the foundation and are not hybridised. Two **UX** ideas come from the Almanac direction ([.working/direction-almanac.html](.working/direction-almanac.html), kept as the audit trail) and are expressed in Ledger's language: a clearer account of what the Agent did and where it went wrong, and a stronger correction diff.

Selecting the visual foundation does not declare the UX finished. Open refinement items are listed at the end.

---

## Brand & Style

### What this product is

A platform where a business operator teaches an Agent how their business actually works, in conversation, and reviews what it understood before it ever reaches a customer.

### The required feeling

> **simple · calm · intelligent · trustworthy · business-oriented · conversational rather than technical**

These are the product's trust argument expressed visually, not stylistic preferences. An operator is being asked to let software answer their customers. Visual calm is how the product earns the right to ask.

### Ledger's register

**The printed record.** A document an operator would read and sign, not an application they would operate. Warm paper, editorial serif, hairline rules in place of cards, no shadow, square corners. The visual language makes one claim: *this is your business, written down.*

The trade-off accepted: less fits on screen, and the calm leaves little headroom for an urgent moment. Suspend, platform errors and escalation therefore carry the strongest rule weights in the system (see Components).

### What it must never look like

A workflow or node editor, a developer IDE or AI playground, a configuration form or settings console, a chat-with-your-documents product, a CRM, a chatbot builder, an automation platform, or a booking, healthcare, sales or FAQ tool. The reasons and the full prohibition list are canonical in **EXPERIENCE.md · Inspiration & Anti-patterns**.

### Product voice

Calm, intelligent, clear, business-oriented. Vocabulary rules and the closed status vocabulary are canonical in **EXPERIENCE.md · Voice and Tone**.

### The Agent's voice is not ours to design

PRD **EX1**: the platform *"deliberately has no default voice and no character of its own … nothing downstream (**UX, a later design pass**, a starting point under FR8) may invent one."* That names this document. **DESIGN.md may not supply, suggest, illustrate or default the Agent's customer-facing voice or character.** No persona, mascot, avatar, assistant face, name or personality cue anywhere in the visual language.

---

## Colors

Light theme only for V1, so there is one token set and no `prefers-color-scheme` block.

### Contrast — computed, binding

Ratios are WCAG 2.x relative-luminance contrast, computed from the hex values against each surface. **Text needs 4.5:1. UI component boundaries and large text need 3:1.**

| Token | on page | on raised | on sunken | Use |
|---|---|---|---|---|
| `{colors.text-body}` | 14.96 | 16.16 | 13.70 | Body text, focus ring |
| `{colors.text-secondary}` | 6.79 | 7.34 | 6.22 | Secondary text, pane headings |
| `{colors.text-quiet}` | 4.71 | 5.09 | **4.32, fails** | Metadata. **Never on `surface-sunken`**; use `text-secondary` there |
| `{colors.state-established}` | 8.49 | 9.17 | 7.78 | State label |
| `{colors.state-not-established}` | 7.83 | 8.46 | 7.17 | State label; 7.72 on its own band |
| `{colors.state-changed}` | 8.51 | 9.19 | 7.80 | State label |
| `{colors.state-affected}` | 5.75 | 6.21 | 5.27 | State label |
| `{colors.divergence-platform-error}` | 8.46 | 9.14 | 7.75 | Class label |
| `{colors.action-suspend}` | 9.53 | 10.30 | 8.73 | Suspend label and border |
| `{colors.border-strong}` | 3.41 | 3.69 | 3.13 | **The only border allowed to define a control's edge** |
| `{colors.border-hairline}` | 1.37 | 1.48 | 1.25 | **Decorative separators only. Fails 3:1** |

Two rules follow from the table:

- **A hairline may never be the only visible edge of anything interactive** (WCAG 1.4.11). Controls use `border-strong`, a filled background, or the label itself.
- **`text-quiet` never sits on `surface-sunken`.** The operator's quoted words and the customer's email sit on sunken; their metadata uses `text-secondary`.

### Surfaces

| Token | Value | Role |
|---|---|---|
| `{colors.surface-page}` | `#F7F4ED` | Warm paper, the ground |
| `{colors.surface-raised}` | `#FFFDF8` | The conversation sheet |
| `{colors.surface-sunken}` | `#EFEAE0` | Quoted material: the operator's words, the customer's email, quoted rules |

### State

Every state carries a **text label and a non-colour cue**. Colour reinforces; it is never the signal.

| State | Label colour | Non-colour cue |
|---|---|---|
| **Established** | `{colors.state-established}` | Label only. No rule |
| **Not established** | `{colors.state-not-established}` | **Dashed bracket around the item, on the `{colors.state-not-established-band}` tint** |
| **Changed** | `{colors.state-changed}` | Solid 2px left rule, plus underline on the changed words |
| **Affected by this change** | `{colors.state-affected}` | Dotted 2px left rule, plus italic |

*Not established* is the most important colour decision in the product. Boxed, tinted and labelled, a recorded absence can never read as empty, off, defaulted or "no".

### Divergence, diff and action

| Token | Value | Note |
|---|---|---|
| `{colors.divergence-spec-defect}` | `#7A3A12` | The operator's to fix |
| `{colors.divergence-business-refusal}` | `#3F4A3A` | **Deliberately the same ink-green as Established.** "Your rules said no" is the guardrails working and must not read as an error |
| `{colors.divergence-platform-error}` | `#4A4458` | Not the operator's fault |
| `{colors.diff-before}` | `#5C5447` | Marked by its label, **never by strike-through** |
| `{colors.diff-after}` | `#221F19` | Full body colour and weight |
| `{colors.attention-escalation}` | `#1E4A6B` | Serious without alarm |
| `{colors.action-suspend}` | `#6B2B2B` | **Outlined, never filled.** Unmistakable without reading as deletion |
| `{colors.focus-ring}` | `#221F19` | See Components · Focus indicator |

The three divergence classes are different kinds, not severities, and are never placed on one colour ramp.

---

## Typography

Serif carries the document; sans carries labels, metadata, actions and pane headings. Two weights only, 400 and 700.

| Role | Token | Setting | Used for |
|---|---|---|---|
| Page title | `{typography.page-title}` | Serif 23 / 1.25, 700 | The single title of a view |
| Section heading | `{typography.section-heading}` | Serif 19 / 1.35, 700 | The five Understanding sections; the parts of the interaction viewer |
| Document body | `{typography.document-body}` | Serif 17 / 1.75, 400 | Understanding items, conversation, quoted email, diff wording |
| Pane heading | `{typography.pane-heading}` | Sans 13 / 1.4, 700, tracked .1em | "Conversation", "What the Builder currently understands", "Activity" |
| Label | `{typography.label}` | Sans 12 / 1.4, 700, tracked .12em, small caps | State labels, class labels, Before / After, Blocking / Not blocking |
| Meta | `{typography.meta}` | Sans 13 / 1.5, 400 | Interaction labels, timestamps, provenance lines |
| Action | `{typography.action}` | Sans 15 / 1.2, 700 | Every button and action |

**Labels carry state meaning, so their floor is 12px.** The 11px label size used in the mocks is withdrawn. Labels are real text in the page, never CSS-generated content.

### Typography does structural work

The authoring surface may contain no steppers, numbers, rails or arrows, so type and space carry the structure that chrome normally would:

- The **five Understanding sections are peers**: identical `section-heading` treatment, with no weighting, numbering or styling that implies order or that the last one is a destination.
- The **correction diff reads as prose**: no monospace for business rules. Before and after are told apart by label and weight, never by strike-through or position alone.
- **Text resizes to 200%** without loss of content or function. Pane layouts reflow to a single column before text is clipped.

---

## Layout & Spacing

| Token | Value |
|---|---|
| `{spacing.1}` to `{spacing.7}` | 4 · 8 · 12 · 16 · 24 · 32 · 48 px |
| `{spacing.gutter-mobile}` | 16px |
| `{spacing.target-min}` | 24px, the WCAG 2.5.8 floor for any target |
| `{spacing.target-action}` | 44px, for Suspend and every primary or secondary action |

### Hairlines, not cards

Structure comes from `border-hairline` rules and whitespace. **No cards, no filled panels, no containers.** Panelling the specification would make it read as an application, which is what the anti-configuration-form rule exists to prevent.

### Application layout

Ledger's document language is organised into **independently scrollable panes with persistent pane headings**: Conversation beside *What the Builder currently understands* while building, and the Activity list beside the open interaction while running. A pane heading is a `pane-heading` label above a hairline. Sticky pane headings, the sticky mobile top bar and the pinned conversation input reserve their height with `scroll-padding`, so a focused element is never hidden beneath them (WCAG 2.4.11). Behaviour is canonical in **EXPERIENCE.md · Application layout**.

### The sequencing prohibition is a layout rule

No arrows, connectors, step numbers, progress rails, steppers, stage breadcrumbs, percentages, completion meters or checklists, as decoration or as navigation (PRD §1.1 / FR18). Canonical statement: **EXPERIENCE.md · The sequencing prohibition**.

### Responsive

Desktop-first. At phone widths and down to 320 CSS px: single column, reading order preserved, `{spacing.gutter-mobile}` side gutter, no horizontal scroll. Both orientations are supported.

---

## Elevation & Depth

**No shadow.** Depth is expressed by surface tone and rule weight, never by lift:

- `surface-raised` separates the conversation sheet from the page.
- `surface-sunken` holds quoted material.
- `border-strong` carries emphasis where a shadow would otherwise be reached for.

A moment that demands separation, such as the diff asking for a decision, earns it through rule weight and whitespace. **Do not reintroduce shadow for it.**

---

## Shapes

**Square throughout:** `{rounded.DEFAULT}` is 0. The product has no curved shapes and no status dots; the round dots in the mocks are browser-window chrome only.

The system's whole shape vocabulary exists to carry meaning without colour. Every shape below is paired with a text label.

| Shape | Meaning | Where it appears |
|---|---|---|
| Dashed bracket on a tinted band | Not established | Understanding, the diff |
| Solid 2px left rule + underline | Changed | Understanding, the diff |
| Dotted 2px left rule + italic | Affected by this change | Understanding, the diff |
| Solid 4px left rule | Your specification got this wrong | Activity, interaction viewer |
| Double left rule, 6px overall | Your rules said no | Activity, interaction viewer |
| Dashed 4px left rule | Something on our side failed | Activity, interaction viewer |
| 2px full border in `text-body` | Blocking validation finding | Validation result |
| No border, label only | Not blocking validation finding | Validation result |
| 2px outline, 2px offset, `focus-ring` | Keyboard focus | Everywhere |

**The state shapes and the divergence shapes never appear on the same surface.** State shapes appear only where specification items are reviewed (Understanding and the diff). Divergence shapes appear only in Activity and the interaction viewer. When the interaction viewer quotes a specification rule, it quotes it as plain quoted material with no state shape. The double rule is 6px overall so its two lines stay distinguishable at phone width.

---

## Components

The visual specification of each component. Behaviour is canonical in **EXPERIENCE.md · Component Patterns** and governs any disagreement about what a component does. Frontmatter ids map to rows here: `action-*` → Actions, `focus-indicator` → Focus indicator, `state-marker` and `not-established-item` → Item state marker, `pane-heading` → Pane heading.

| Component | Visual specification |
|---|---|
| **Actions** | Three kinds, all square, in `{typography.action}`, at least `{spacing.target-action}` tall. **Primary** (Accept, Approve, Connect mailbox): `text-body` fill with a `surface-raised` label (16.16:1); at most one per view. **Secondary** (Push back, This was wrong, Back, Let the Agent act again): transparent, `text-body` label, 1px `border-strong` edge. **Suspend**: transparent, `action-suspend` label, 2px `action-suspend` edge, never filled. **Disabled**: the label stays `text-secondary` and the border becomes dashed `border-strong`, with a plain sentence beside it saying why it is unavailable; opacity is never the only signal. **Pending**: the label is replaced by its closed-vocabulary pending text and the action cannot be pressed again. Actions are real buttons, never links styled as buttons. |
| **Focus indicator** | A 2px solid `focus-ring` outline with a 2px offset on every focusable element, 14.96:1 against the page. Deliberately not blue, so it can never be confused with the Changed marker. Never removed, never colour-only. |
| **Pane heading** | `{typography.pane-heading}` in `text-secondary` above a hairline. Sticky within its pane, under the scroll-padding rule above. |
| **Section collapse control** | The whole Understanding section heading row is the control, with a square plus or minus glyph at least 24px. When collapsed, the row also shows, in `label` type, which of **Not established**, **Changed** and **Affected by this change** the section contains, each with its shape at reduced size. Identical on all five sections; no number, order or progress. |
| **Conversation panel** | `surface-raised` sheet in `document-body` type. The operator's own words sit on `surface-sunken`. The thinking state is one line of closed-vocabulary text that pulses no faster than once every two seconds, and is static under reduced motion. When opened from an item, the origin is shown above the conversation as a `meta` line. |
| **Conversation input** | A multi-line text area with a visible label and a 1px `border-strong` edge, pinned to the bottom of the Conversation pane. The pane's `scroll-padding-bottom` reserves its height. |
| **Understanding document** | `surface-page`. Five peer sections in `section-heading`, with hairlines between them. A persistent `meta` line under the pane heading says this is what the Builder currently understands, not a live-editing surface. Reference: [key-hero](mockups/key-hero.html). |
| **Item state marker** | A `{typography.label}` text label plus the state's shape from Shapes. All four states are labelled, Established included. |
| **Correction diff** | Almanac's clarity in Ledger's language. Before, After, Also affected and Unchanged as prose, each headed by a `label`. Before is in `diff-before` and is **never struck through**; After is in `diff-after`. Readable top to bottom without visual comparison. Separated by rule weight and whitespace, not shadow. Reference: [key-diff](mockups/key-diff.html). |
| **Validation result** | Shown at the approval moment. Lists only the findings the suite returned: a blocking one sits inside a 2px `text-body` border with a **Blocking** label; a non-blocking one has a **Not blocking** label and no border. Pending is a closed-vocabulary sentence with no progress estimate. |
| **Approval** | A decision the operator owns: one primary action and a plain sentence that the automated check, not the operator, determined validity. **No celebration, confetti or success colour.** |
| **Agent status line** | A `meta` line under the Activity pane heading that states the Agent's status in words: *Live, mailbox connected*; *Suspended, not replying or acting*; *Suspended, replying but not acting*; *Not live, mailbox not connected*. Suspended states use the `action-suspend` colour **and** the words. |
| **Divergence list** | Grouped under the three class framings. Each group heading and item carries its class shape from Shapes and its class label. An item shows only the class, the interaction label in `meta`, and a one-line request. **No counts, severity marks, retry badges, charts or filters.** Reference: [key-activity](mockups/key-activity.html). |
| **Interaction viewer** | Almanac's explanatory clarity in Ledger's language. Three parts, each headed in `section-heading`: the customer's email (verbatim, on `surface-sunken`); the Agent's reply (verbatim); and *What this reply was based on* (quoted rules and material on `surface-sunken`, each with a `meta` link to where it lives in Understanding). Then **This was wrong** as a secondary action. The internal record's structure never appears as headings. No pipeline, progress diagram or ordered trace. Reference: [key-interaction](mockups/key-interaction.html). |
| **Degraded notice** | A closed-vocabulary sentence in `document-body`, preceded by a `label`, inside a 1px `border-strong` box. Used for an answer from general knowledge, a reported action without evidence, a safety halt, a request that needs a human, and a platform error. A platform error also shows its reference code in `meta`. |
| **Suspend** | An `action-suspend` action that stops the Agent replying and acting in one press, with no confirmation step. **Stop actions only** sits beside it as a secondary action for effects-only suspension. On mobile both sit in the sticky top bar of the Activity list and the interaction viewer. Once suspended, the Agent status line changes. Resume ("Let the Agent act again") is a **secondary** action and is never styled like Suspend. |
| **Material intake** | A list of ingested sources, each with name, version and a `meta` provenance line. A parse failure uses the degraded notice: *"Could not be read. Nothing from it has been used."* |
| **Connect mailbox** | One primary action and a plain sentence that connecting makes the Agent reachable by customers. Nothing further is specified, because the provider and authorisation flow are an upstream gap. |
| **Escalation email** | Plain HTML email with a complete plain-text part, readable with images and CSS off, with no meaning carried by colour. `attention-escalation` is used only for the heading rule, where styles render. |

### Motion

**Restrained, and only to communicate state:** processing, progress, transition. No decorative animation. Everything animated has a static equivalent that conveys the same state under `prefers-reduced-motion: reduce`. That covers the thinking pulse, collapse and expand, pane transitions on mobile, and the arrival of new Understanding items.

---

## Do's and Don'ts

### Do

- Let the Understanding document look like something an operator would read carefully and recognise as *their* business.
- Make `Not established` impossible to mistake for *nothing here* or *this is off*.
- Keep the three divergence classes reading as different kinds, not degrees of badness.
- Carry structure in type, space and hairline rules, since the chrome that would normally do it is forbidden.
- Let the approval moment feel like a decision, not an achievement.
- Spend the scarce emphasis (`border-strong`, weight 700, the suspend outline) on the moments that need it.

### Don't

- Don't invent a voice, character, persona, mascot or avatar for the Agent.
- Don't add arrows, numbers, steppers, rails, percentages or checklists to the authoring surface.
- Don't render the specification as fields, toggles, dropdowns or settings rows.
- Don't add shadow, radius or cards because a moment feels flat.
- Don't let a hairline be the only edge of a control, or put `text-quiet` on `surface-sunken`.
- Don't style a business refusal as an error.
- Don't put a pipeline or progress diagram in the interaction viewer.
- Don't strike through the before-wording in a diff.
- Don't signal any state by colour alone, and don't use the Changed blue for focus.
- Don't celebrate, and don't reassure beyond what was actually verified.

---

## Open refinement items

1. **Density for everyday and weekly use.** A real refinement item, not a mock artifact. Panes and collapsible sections recover much of the space. Whether working surfaces (Activity, the interaction viewer) tighten the type scale or line height below the 17px / 1.75 document setting is undecided. Any tightening must keep AA contrast and target sizes, and must not turn Understanding into a dense table.
2. **Urgency headroom.** Ledger's calm leaves little range above the baseline. Suspend, platform errors and escalation carry the strongest rules in the system but need checking in situ.
3. **Divergence class shapes at phone width.** Defined above, with a 6px double rule; to be checked on real devices.
4. **Repeated divergences on the Activity list** at real volume. Nothing upstream deduplicates, so repeated occurrences of one problem appear as separate items in V1. How they group is untested and must not be solved with a severity or metric model.
5. **The mocks predate this revision** in four places: they use the Changed blue for focus, 11px labels, `text-quiet` on sunken in key-diff, and no Agent status line. This document wins; the mocks are illustrations.
