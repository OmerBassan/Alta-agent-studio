# Step 2 — The Playbook (read before drafting the review-phase script)

The playbook is THE design artifact the client approves — the whole call
scripted the way a sales coach scripts a rep. Plain numbered scenes, no
markdown emphasis, no tables. Each scene: its purpose in one line, the agent's
opening line in quotes, 2-3 realistic replies, and where each routes.

It must cover: the opener; every qualification question; the knowledge
questions likely mid-flow (and the resume line back into the pending
question); each major objection with its approved rebuttal; the CTA/close; a
READ-BACK scene for every captured datum that feeds a write ("That's dana at
acme dot com — right?"); and the failure exits (not interested → polite close;
stuck/angry/asks-for-human → handoff with its one-line recap). Every advertised
exit is a scene, not a hope.

Number the PROACTIVE SPINE explicitly — the scenes the agent DRIVES in order
(opener → discovery → qualify → close) — and mark each other scene as a REACTIVE
overlay (objections, knowledge questions, read-backs, firm-no/handoff). The
spine becomes the executable `CALL_ARC` in step3 (one Stage per spine scene);
the overlays stay reactive and are never stages. An outbound agent that only
answers is a spine that was written but never wired.

## THE OPENER IS CACHED AND INSTANT

The platform speaks `config.py`'s `OPENER` as the call's first words via the
voice transport — zero model calls, ~500ms after pickup. Therefore OPENER must
be:

- a PLAIN STRING LITERAL (no f-string, no concatenation — the platform parses
  it statically),
- ≤20 words, sounding like a human picking up the phone,
- who's calling and why in one breath, ending with ONE question that hands the
  mic to the lead,
- never empty or whitespace-only,
- verbatim identical to the playbook's Scene 1 line.

## The firm-no rule (non-negotiable)

If the lead firmly declines — "not interested", "stop calling", "take me off your
list", "no thank you, we're set" — the agent thanks them warmly in ONE sentence
and ends the call. No rebuttal, no second pitch, no "before you go", no last
question. A firm no routes straight to the close, never back through an objection
scene. Script this exit explicitly; it is a scene, not a hope. (A soft hesitation
or a specific objection — "too expensive", "already have a supplier" — is NOT a
firm no; that still earns its one approved rebuttal. Only a clear refusal ends the
call.)

## Voice writing rules (apply to EVERY line in the playbook)

Written to be SPOKEN: ≤20 words per turn, contractions, complete sentences
(fragments sound broken aloud), no lists/markdown/URLs ("link", not the URL),
numbers and dates in spoken form, acronyms written as pronounced
("business-to-business", never "B2B"). Every turn that expects input ends on
exactly ONE question. Sprinkle short natural acknowledgments ("Got it.",
"Makes sense.") so it never sounds robotic. The pre-TTS sanitizer is a
backstop — text that needs it is a defect.

## Presenting for approval

Present the playbook in chat as plain numbered scenes with quoted lines —
readable prose, zero markdown syntax. End the turn with the `alta:ask` approve
card. Playbook edits are cheap here and expensive after the build — apply a
revision and re-present rather than defending the draft.

Internal only (never shown to the client): a Mermaid `flowchart TD` of the
concrete pipeline goes into the generated project's README. Two minutes, no
polish, no discussion.

On approval: read `skill_steps/step3_contract.md` and
`skill_steps/step4_build.md` together, then build.
