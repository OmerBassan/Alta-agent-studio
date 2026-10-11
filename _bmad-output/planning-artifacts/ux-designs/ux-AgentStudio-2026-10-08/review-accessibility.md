# Accessibility review — DESIGN.md, EXPERIENCE.md and the five reference mocks

Reviewer: accessibility. Bar: **WCAG 2.2 AA**, required rather than optional. Scope: `DESIGN.md`, `EXPERIENCE.md`, `mockups/*.html`. No other planning documents were read. Nothing except this file was edited.

## Verdict

The spines have the right accessibility intent. Never colour alone, text-led state markers, a sequential diff, polite live Understanding and a plain Suspend are all there, and the colour palette as written passes AA for text almost everywhere. The specification still can't be built to AA as written. The binding contrast table is computed wrong. No focus indicator is defined. The new pane-and-collapse layout has no keyboard, landmark, disclosure or focus-obscuring rules. Status messages are specified only for Understanding, so Suspend, the diff and validation results all arrive silently for a screen-reader user. None of this needs new product features. It needs about a dozen rules added to the Accessibility Floor and the Application layout section, plus a corrected Colors table.

**Counts:** critical 1 · high 6 · medium 9 · low 8

---

## Contrast arithmetic (check 1)

WCAG relative luminance (sRGB linearised, `L = 0.2126R + 0.7152G + 0.0722B`, ratio `(L1+0.05)/(L2+0.05)`), computed by script. The Not-established tinted band `#FBF1E8` comes from the mocks (`.item.s-not`, e.g. `key-hero.html` line 95).

| Token | Stated in DESIGN.md | page `#F7F4ED` | raised `#FFFDF8` | sunken `#EFEAE0` | Not-est. band `#FBF1E8` |
|---|---|---|---|---|---|
| border.hairline `#D9D2C4` | 3.0:1 | **1.37** | **1.48** | **1.25** | **1.35** |
| border.strong `#8C8372` | 4.6:1 | 3.41 | 3.69 | 3.13 | 3.36 |
| text.body `#221F19` | 16.9:1 | 14.96 | 16.16 | 13.70 | 14.75 |
| text.secondary `#5C5447` | 7.2:1 | 6.79 | 7.34 | 6.22 | 6.70 |
| text.quiet `#756C5C` | 5.0:1 | 4.71 | 5.09 | **4.32** | 4.65 |
| state.established `#3F4A3A` | 8.9:1 | 8.49 | 9.17 | 7.78 | 8.37 |
| state.notEstablished `#7A3A12` | 6.6:1 | 7.83 | 8.46 | 7.17 | 7.72 |
| state.changed `#1E4A6B` | 7.6:1 | 8.51 | 9.19 | 7.80 | 8.39 |
| state.affected `#46637A` | 5.0:1 | 5.75 | 6.21 | 5.27 | 5.67 |
| divergence.platformError `#4A4458` | — | 8.46 | 9.14 | 7.75 | 8.34 |
| action.suspend `#6B2B2B` | 6.9:1 | 9.53 | 10.30 | 8.73 | 9.40 |

Worked example: hairline. L(`#D9D2C4`) ≈ 0.645 and L(`#F7F4ED`) ≈ 0.903, so (0.903+0.05)/(0.645+0.05) = **1.37**, not 3.0. The quiet text on sunken: L(`#756C5C`) ≈ 0.153 and L(`#EFEAE0`) ≈ 0.817, so 0.867/0.203 = **4.32**, which is under 4.5.

Not one of the eleven stated ratios matches the arithmetic. Some are overstated (hairline, strong, body, secondary, quiet, established), and some are understated (notEstablished, changed, affected, suspend). Every state, divergence, diff and Suspend colour passes 4.5:1 on all four surfaces. The failures are **hairline everywhere** and **text.quiet on sunken**. Two other values are marginal: text.quiet sits at 4.65–4.71 on page and on the band, and border.strong is 3.13 on sunken.

Two ratios relevant to focus: the mock focus colour `#1E4A6B` against the filled `.btn` ink `#221F19` is **1.76**, and against `action.suspend` it is **1.12**.

---

## Critical

### C1. Suspend has no specified accessible outcome
- **Location:** EXPERIENCE.md Component Patterns › Suspend (l. 313–317), Accessibility Floor (l. 406–407), Flow 5 (l. 528–533). DESIGN.md Components › Suspend (l. 256). Mock: `key-interaction.html` l. 187 and l. 255.
- **WCAG:** 4.1.3 Status Messages, 4.1.2 Name, Role, Value, 3.2.2 On Input.
- **Problem:** The spines cover how to *reach* Suspend (labelled, keyboard, not behind a gesture). They never say what happens after it is activated. A screen-reader operator who presses the emergency brake gets no specified confirmation that the Agent stopped. The "optionally effects-only" choice (l. 531) has no specified control shape, so it could end up in a menu, a popover or a two-step dialog, and none of those is constrained. The mock gives the resume action, "Let the Agent act again", the same outlined maroon style as Suspend (`key-interaction.html` l. 255 uses `.btn.suspend`). A low-vision user then sees the same brake styling on the opposite action. Flow 5's own climax is "the state is visible", but nothing makes that state *announced*.
- **Fix (spec text to add to Accessibility Floor):** "Activating Suspend, Suspend acting only, or resuming announces the resulting state through a polite status message, in the closed vocabulary (for example 'Suspended. The Agent is not answering or acting.'). Focus stays on the control that was activated. The control's accessible name then reflects the new action. The two suspend scopes are two separately labelled controls, each reachable in one action, never a menu, popover or hover reveal. The resume action never uses `action.suspend` styling." Also state that the persistent suspended-state framing (as in `key-interaction.html` l. 210–214) appears at the top of every Run screen, as text, so the state can be found without searching for it.

---

## High

### H1. The binding contrast table is wrong, and text.quiet fails on sunken in the mocks
- **Location:** DESIGN.md Colors › Surface and text (l. 118–127), State (l. 133–138), Divergence (l. 152), Contrast floor (l. 156: "Every token above meets it"). Mock: `key-diff.html` l. 79 (`.said strong`, "What you said", 12px `--ink3` on `--sunken`) and l. 81 (`.said .by`, 12px).
- **WCAG:** 1.4.3 Contrast (Minimum), 1.4.11 Non-text Contrast.
- **Problem:** See the arithmetic above. `border.hairline` is 1.37:1, not 3.0:1. If it ever forms the only visible edge of an interactive element, such as the composer, a collapse control or a list row, it fails 1.4.11. `text.quiet` is 4.32:1 on `surface.sunken`, and the diff mock already places 12px labels there. Because the table says every token passes, implementers will not re-check.
- **Fix:** Replace the "Contrast" column with computed values, one column per surface (page, raised, sunken, the Not-established band). Add a token for the band (for example `state.notEstablishedBand: #FBF1E8`), because it is currently mock-only. Add these rules: "`border.hairline` is decorative only and is never the sole boundary of an interactive control or the sole carrier of a state. Component boundaries use `border.strong` or darker." Also: "`text.quiet` is not used on `surface.sunken`. Use `text.secondary` there."

### H2. No focus indicator is defined, and the mock one is the `state.changed` colour
- **Location:** DESIGN.md has no focus token or rule anywhere (Colors, Elevation & Depth l. 220–230, Components). EXPERIENCE.md l. 401 requires "a visible focus indicator throughout" but delegates visuals to DESIGN.md. Mocks: `a:focus-visible{outline:2px solid var(--chg);outline-offset:2px}` in every file (e.g. `key-activity.html` l. 53). It covers only `a` and `.btn`.
- **WCAG:** 2.4.7 Focus Visible, 1.4.11 Non-text Contrast. 2.4.13 is AAA but advisory.
- **Problem:** Ledger has no shadow and no radius, so the focus ring is the *only* focus device, and it is not specified. The mock ring is `#1E4A6B`, the exact colour of the Changed state, and it is a solid line. A solid blue line is exactly the Changed cue (solid left rule plus underline), so a focused Established item can read as Changed. The ring is also 1.76:1 against the filled ink button and 1.12:1 against the Suspend outline. It is visible only because of the 2px offset, which no document requires. Buttons, collapse controls, scroll panes and the composer get no rule at all.
- **Fix:** Add a `focus` token and rule to DESIGN.md: "Focus is a 2px solid `text.body` (`#221F19`) outline with a 2px offset, plus a 1px `surface.raised` inner ring where the element is filled. It is used on every focusable element, including buttons, disclosure controls, scrollable panes and the composer. It is at least 3:1 against every surface (14.96:1 on page). It never uses a state or divergence colour, and it is never removed without a replacement."

### H3. Collapsed Understanding sections: disclosure semantics and AT exposure of the hidden markers are unspecified
- **Location:** EXPERIENCE.md Responsive & Platform › Application layout (l. 436). DESIGN.md Layout › Application layout (l. 212). EXPERIENCE.md Accessibility Floor (l. 402: "reach every 'Not established' item"). No mock shows a collapse control.
- **WCAG:** 4.1.2 Name, Role, Value, 1.3.1 Info and Relationships, 2.1.1 Keyboard.
- **Problem:** The spine says a collapsed heading "still shows" Not established / Changed / Affected. That wording is visual. If the summary is drawn as an icon, a pseudo-element or text outside the control's name, a screen-reader user who hears "How it operates, collapsed" never learns that a recorded absence sits inside it. That is the failure the product says is most dangerous (EXPERIENCE.md l. 340). Collapsing also conflicts with l. 402, because collapsed content cannot be reached until it is expanded. Nothing says how expand state is announced.
- **Fix:** Add to Application layout: "Each section heading (a real `h3` inside the pane's heading outline) contains one native `button` with `aria-expanded` and `aria-controls`. The button's accessible name is the section name plus, as text, each state present inside: for example 'How it operates — holds Not established and Changed items'. It names the states only, with no counts, so it cannot read as a completion meter. The same text is visible beside the heading. Collapsed content uses `hidden`, not off-screen positioning. The collapse control is at least 24×24 CSS px." Also amend l. 402 to say that a screen-reader user can reach every Not established item, *expanding a section where needed, with the section's collapsed name already telling them it is there.*

### H4. Independently scrollable panes are not specified as keyboard-scrollable regions
- **Location:** EXPERIENCE.md Application layout (l. 435, l. 438). DESIGN.md l. 212. Mock: `key-activity.html` l. 76 (`.pane{overflow-y:auto}`) and l. 172/209 (`<section class="pane" aria-label=…>`, with no `tabindex`).
- **WCAG:** 2.1.1 Keyboard, 1.3.1, 2.4.1 Bypass Blocks, 2.4.6 Headings and Labels.
- **Problem:** A pane that scrolls independently and holds long non-focusable text can't be scrolled by keyboard in browsers that don't make scroll containers focusable (Safari, older Chromium). Examples are the interaction detail pane (verbatim email, reply, quotes) and the Understanding pane. Nothing defines landmarks, a skip mechanism between panes, or a heading outline. The mocks use `<p class="panehead">` for pane headings (`key-activity.html` l. 173, `key-hero.html` l. 422), so there is no heading to navigate by. There is no `main` landmark, and the current place in the nav is shown with a `<b>` instead of `aria-current="page"` (`key-hero.html` l. 417).
- **Fix:** Add to Application layout: "Each pane is a labelled region (`section` with `aria-labelledby` pointing at its pane heading, which is an `h2`). The pane is focusable (`tabindex="0"`) so arrow keys and Page Up/Down scroll it, and it shows the focus ring. Both panes sit inside one `main`. The Understanding / Activity switch is a `nav` with `aria-current="page"`. Heading outline: one `h1` for the place, `h2` for each pane, `h3` for each Understanding section, divergence class group and interaction part. Moving between panes needs no more than one Tab past the pane's own controls, or uses a skip link."

### H5. Status messages exist only for Understanding updates: the diff, validation, the Builder's reply and ingestion are silent
- **Location:** EXPERIENCE.md Accessibility Floor (l. 403 covers only live Understanding). Component Patterns › Correction diff (l. 233–245). Validation result (l. 247–256). State Patterns › Timing (l. 371–378). Application layout (l. 437: the diff opens in the Conversation pane, and "affected items in Understanding are marked while the diff is open").
- **WCAG:** 4.1.3 Status Messages, 2.4.3 Focus Order, 3.2.2.
- **Problem:** The Builder turn's thinking state, the arrival of the Builder's reply, the diff appearing in the Conversation pane, the "affected" marks appearing in the other pane, the validation pending state, its result (including a *blocking* finding) and a material parse failure all change the screen with no announcement specified. The diff is the product's most important component (l. 237). A screen-reader operator needs to learn that it has arrived and where it is, without losing their place in the composer. The l. 403 rule also doesn't say how updates are batched. Per-item polite announcements during a fast turn will flood the speech queue.
- **Fix:** Add to Accessibility Floor:
  1. "The conversation is a `role="log"` region. A new Builder turn is announced politely once it completes, not token by token. The thinking state is a polite status in text. It is never a looping visual alone."
  2. "Live Understanding updates produce one polite announcement per Builder turn, naming the sections changed. They never announce per item. Focus never moves."
  3. "When a diff arrives, a polite status says 'The exact change is ready to read', and the diff's heading is a skip target. Focus moves to the diff only if the operator is not in the composer. Accept and Push back follow the diff in reading order. Items marked affected in Understanding get the text label 'Affected by this change' in the DOM, not only a rule."
  4. "Validation pending is a polite status with `aria-busy` on the results region and no progress estimate. When results arrive, a status states whether anything blocks (for example 'The check returned one finding. It is not blocking.'). Focus moves to the results heading only if the operator started the check and focus is still on the triggering control."
  5. "Material parse failure is announced as a status with the failure text."

### H6. Sticky pane headings, the sticky mobile top bar and the in-view composer can fully obscure focus
- **Location:** EXPERIENCE.md l. 435 ("persistent pane heading", "the conversation's input stays in view"), l. 439 ("Suspend is reachable … without scrolling"). Mock: `key-activity.html` l. 78 (`.panehead{position:sticky;top:0}`, about 64px tall with the Suspend button inside) and l. 127 (`.mtop{position:sticky}`). There is no `scroll-padding`.
- **WCAG:** 2.4.11 Focus Not Obscured (Minimum), which is new at AA in 2.2.
- **Problem:** When an operator tabs backwards through the Activity list or Understanding items, browsers scroll the focused element to the top edge of the scroller, under the sticky header. A 44px list row under a 64px pane header is *entirely* hidden, and that fails 2.4.11. On mobile the sticky top bar holding Suspend does the same. A pinned composer can hide items when tabbing forward at the bottom of the conversation.
- **Fix:** Add to Application layout: "Every scroll container with a sticky header or footer sets `scroll-padding-top` / `scroll-padding-bottom` at least equal to that header or footer's rendered height, re-measured on resize and text zoom. No sticky element may fully cover a focused element. Sticky headers hold one line of content at 200% text size, or stop being sticky beyond that."

---

## Medium

### M1. Blocking vs not-blocking has no defined non-colour cue, and the mock reuses Not established's cue
- **Location:** DESIGN.md Components › Validation result (l. 252: "plus a non-colour cue", unspecified). Mock: `key-diff.html` l. 112–115 (`.flag.warn` draws "Not blocking" in `#7A3A12` with a dashed border and `[ ]` brackets, which is exactly the Not established marker).
- **WCAG:** 1.4.1 Use of Color (passes on the text label), 1.3.1.
- **Problem:** The label carries meaning, so 1.4.1 is met. But the one shape a user has learned to mean "recorded absence" now also means "not blocking". The blocking cue is never shown.
- **Fix:** In DESIGN.md, define distinct cues: for example **Blocking** gets a 2px solid `border.strong`-or-darker box and weight 700, and **Not blocking** gets the plain label with no box. State that validation cues never reuse a state marker's shape or colour. Each finding is a list item under a heading such as "Blocking" or "Not blocking", so the grouping is also structural.

### M2. Keyboard-completeness list omits the Run surfaces and the new controls
- **Location:** EXPERIENCE.md Accessibility Floor (l. 401).
- **WCAG:** 2.1.1, 2.1.2, 2.4.3.
- **Problem:** The list names conversation, review, correction, diff confirmation, approval and suspend. It leaves out Activity, the interaction viewer, the "Where this lives in Understanding" links, collapse controls, pane scrolling, material intake (file picking) and Connect mailbox. Those include the surfaces the product says must be fully usable on a phone.
- **Fix:** Rewrite as "Every surface in the Surface inventory, and every control in Application layout, is operable by keyboard alone…" and name the additions explicitly.

### M3. Returning focus after navigation, and deep links into collapsed Understanding
- **Location:** EXPERIENCE.md Application layout (l. 439, the mobile "plain back action"). Interaction viewer (l. 304, quotes linked to Understanding). Mock: `key-activity.html` l. 240, `key-interaction.html` l. 169.
- **WCAG:** 2.4.3 Focus Order, 2.4.4.
- **Problem:** On mobile, back from an interaction has no specified focus target, so the operator lands at the top of the list again. On desktop, selecting a list item has no specified focus behaviour for the detail pane. "Where this lives in Understanding" can point into a collapsed section, or into read-only Understanding on a phone, and nothing says the target is expanded and focused.
- **Fix:** "Back returns focus to the list item that was opened. Opening an item on desktop leaves focus on the item and announces the detail pane politely, or moves focus to the interaction heading if it opens full-screen. A link into Understanding expands the target section and moves focus to the quoted item, which carries `tabindex="-1"`."

### M4. Small tracked small-caps labels carry state, and 200% text resize is not addressed
- **Location:** DESIGN.md Typography (l. 172–174, l. 183: "remain legible at 11px"). Mocks: `.st` at 11.5px with `.09em` tracking, `.panelhead` at 11px with `.16em` in `--ink3` at 4.71:1.
- **WCAG:** 1.4.4 Resize Text, 1.4.12 Text Spacing, 1.4.3.
- **Problem:** 11px uppercase sans with 0.16em tracking in a 4.7:1 grey passes the letter of AA, but it is the weakest text in the product and it carries pane identity and metadata. The state labels are fine in colour (5.75:1 or more) but tiny. The type scale is in px, and nothing requires layouts to survive 200% text or user text-spacing overrides. The mocks would break at that size: `white-space:nowrap` on Suspend (`key-activity.html` l. 82) and `width:max-content` on the affected label (`key-diff.html` l. 96).
- **Fix:** In DESIGN.md: "The floor for any text that carries state or identity is 12px, rendered in `text.secondary` or a state colour, never `text.quiet`. Express the scale in `rem`. Layouts are verified at 200% text size and under the 1.4.12 spacing overrides with no loss of content: no `nowrap` on labelled controls, no `max-content` on labels."

### M5. Mobile Suspend placement is specified for the list but not shown for the viewer, and the mock contradicts the spine
- **Location:** EXPERIENCE.md l. 439 ("Suspend is reachable from both without scrolling"). DESIGN.md l. 216. Mock: `key-interaction.html` l. 185–189 puts Suspend after the full email, reply and sources. No phone state of the viewer exists. `key-activity.html` shows only the list on the phone.
- **WCAG:** 2.5.8 (met in the list mock at about 47px tall), plus the spine's own reach rule.
- **Fix:** State the mechanism in EXPERIENCE.md: "On mobile, Suspend sits in the same top bar on the Activity list and on the interaction viewer, at least 44×44 CSS px, and is first in focus order after the place heading." Then add a phone viewer state to the mock set, or note that the desktop mock's bottom placement is not the mobile layout.

### M6. Target sizes are stated as "AA sizing" with no number, and some controls are unsized
- **Location:** DESIGN.md l. 216. EXPERIENCE.md l. 406.
- **WCAG:** 2.5.8 Target Size (Minimum).
- **Problem:** No minimum is written down. Collapse controls, the mobile back action and "Where this lives in Understanding" (13px inline-block links, about 23px line box, `key-interaction.html` l. 96) have no size rule. Activity rows already meet 44px (`key-activity.html` l. 94).
- **Fix:** "All targets are at least 24×24 CSS px (2.5.8). On mobile, Suspend, the back action, Activity rows and This was wrong are at least 44×44. Standalone links are block-level with at least 24px height."

### M7. The escalation email lacks concrete accessible-email rules and has no reference rendering
- **Location:** EXPERIENCE.md The Escalation Email (l. 446–463), Accessibility Floor (l. 409). DESIGN.md Components (l. 258).
- **WCAG:** 1.3.1, 1.4.1, 2.4.4, 3.1.1 (applied by analogy to HTML email).
- **Problem:** "Plain-text alternative, readable without CSS, no colour meaning" is right but incomplete. Nothing covers `lang`, semantic structure, link wording, layout tables, or how email clients that force dark mode invert `attention.escalation` (`#1E4A6B` on a dark ground drops well under 4.5:1). The four required parts (l. 454–457) have no specified order or headings. No mock exists to check.
- **Fix:** Add: "Sent as `multipart/alternative` with an equivalent `text/plain` part. The HTML part declares `lang="en"`, uses real headings for the four parts in the l. 454–457 order, uses no layout tables (or `role="presentation"` on any that remain), contains no images (or decorative images only, with `alt=""`), and has link text that names the destination. The subject line front-loads the reason it was handed to a human. Colours are declared for light and dark client schemes, or the email uses no background colour, so client inversion keeps 4.5:1." Add a static reference rendering to the mocks.

### M8. Understanding pane and conversation lack defined landmark and labelling for the composer
- **Location:** EXPERIENCE.md Conversation panel (l. 210–217). Mock: `key-hero.html` l. 443, where the composer is shown as italic placeholder text in `--ink3`.
- **WCAG:** 3.3.2 Labels or Instructions, 1.3.1, 2.5.3 Label in Name.
- **Problem:** If the composer's only label is its placeholder, it disappears on input. Nothing specifies the composer's accessible name, a send control, or Enter-vs-Shift+Enter behaviour (a keyboard trap risk for multiline input).
- **Fix:** "The composer is a labelled multiline text field. It has a visible label or a persistent visible name, and the placeholder is never the only label. Submission uses a labelled button and a documented key, and Tab always leaves the field."

### M9. Accessible authentication for sign-in and Connect mailbox is unaddressed
- **Location:** EXPERIENCE.md Surface inventory (Connect mailbox, l. 128). Amendments item 3 (l. 583).
- **WCAG:** 3.3.8 Accessible Authentication (Minimum), new at AA in 2.2.
- **Fix:** Add one line to Accessibility Floor: "Sign-in and mailbox connection require no cognitive function test: paste and password managers work, and no puzzle CAPTCHA is used." This constrains the surface without designing it.

---

## Low

### L1. The `.st.not` `[ ]` brackets and the Activity "Open ·" prefix are CSS-generated content
- `key-hero.html` l. 102–103 and `key-activity.html` l. 101. Screen readers may read "left bracket Not established right bracket", or miss "Open". Spec rule: "Meaning-bearing text is in the DOM. Decorative brackets are `aria-hidden`." `aria-current="true"` on the open item is correct and should be written into the spec. (1.3.1)

### L2. Actions are drawn as `<a href="#">`
- Accept, Push back, Approve, This was wrong and Suspend in every mock. Spec rule: "Actions that change state are `button` elements. Links navigate." (4.1.2)

### L3. Duplicate labelling
- `key-hero.html` l. 447–449 repeats "What the Builder currently understands" as the pane heading *and* as the frame label. `key-interaction.html` l. 143 puts an `aria-label` on `section`s that already contain an identical `h3`. Use `aria-labelledby` and keep one visible heading.

### L4. Active-place and step-free nav semantics
- The `.places` nav marks the current place by bold plus underline only (the underline is `border.strong`, 3.41:1). Add `aria-current="page"`. (1.3.1, 1.4.1 is met through weight)

### L5. Truncated one-line request on Activity rows
- `key-activity.html` l. 99 (`nowrap` plus ellipsis). This is acceptable because the full text is in the viewer and in the accessible name, but the spec should say "truncation is visual only. The full request is exposed to assistive technology, and the row is never the only place it appears."

### L6. The Business-refusal double rule degrades at small sizes
- `4px double` renders as two 1px lines, which reads as solid on low-density screens and at mobile widths. DESIGN.md open item 3 already flags this. Keep the group heading text as the guaranteed cue, and test the double rule on an actual phone.

### L7. Reduced motion is stated but not scoped
- DESIGN.md Motion (l. 262) and EXPERIENCE.md l. 405 are correct, and no mock animates (no `animation` or `transition` found). Add: "Pane auto-scroll, collapse/expand and the arrival of Understanding updates use no smooth scrolling or transition under `prefers-reduced-motion: reduce`. Any pending indicator that would animate for more than 5 seconds can be paused or is static (2.2.2)." The validation pending duration is unbounded (l. 375).

### L8. Orientation and reflow at 320 are implied, not stated
- DESIGN.md l. 216 requires "no horizontal page scroll". Make it explicit: "Reflows at 320 CSS px (1.4.10) and works in both orientations (1.3.4)." The mocks mostly comply. `key-activity.html` collapses to one column at 760px and below, and `key-diff.html` stacks rows at 900px and below.

---

## Colour independence (check 2), summary

| Signal | Text label | Non-colour cue | Verdict |
|---|---|---|---|
| Established | Yes | None by design (default) | OK: the absence of a cue is the cue, and the label carries it |
| Not established | Yes | Dashed bracket, tinted band, `[ ]` | OK. Mock brackets are CSS-generated (L1) |
| Changed | Yes | Solid left rule, underline | OK, but collides with the mock focus ring (H2) |
| Affected by this change | Yes | Dotted rule, italic | OK. Must also be text in Understanding while a diff is open (H5 item 3) |
| Spec defect / Business refusal / Platform error | Yes (group heading and viewer framing) | Solid / double / dashed left rule | OK. Double rule weak at small sizes (L6) |
| Blocking / Not blocking | Yes | **Undefined.** The mock borrows Not established's cue | M1 |
| Suspended state | Yes (mock framing) | Double maroon rule | OK visually. Announcement missing (C1) |

## Mock-versus-spine contradictions (check 10)

1. `text.quiet` on `surface.sunken` at 4.32:1 (`key-diff.html` l. 79, l. 81) breaks DESIGN.md's contrast floor (H1).
2. The focus ring uses `state.changed` and covers only `a` / `.btn` (all mocks), against EXPERIENCE.md l. 401 "throughout" (H2).
3. Pane headings are `<p>`, against "real heading structure" (EXPERIENCE.md l. 402) (H4).
4. Scroll panes are not focusable and sticky headers have no scroll padding (`key-activity.html` l. 76–78) (H4, H6).
5. "Not blocking" reuses the Not established marker (`key-diff.html` l. 113) (M1).
6. Interaction viewer Suspend sits at the bottom with no phone state (`key-interaction.html` l. 185–189), against l. 439 (M5).
7. Resume is styled as Suspend (`key-interaction.html` l. 255) (C1).
8. State-changing actions are links (L2).
9. No mock shows a collapse control, so H3 can't be checked against an illustration.
