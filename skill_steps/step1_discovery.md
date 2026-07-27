# Step 1 — Discovery (read before your first intake question)

Extract the agent's MISSION from the client. 
STRICT TURN SEQUENCE (You must follow this exact order):
Turn 1: Your VERY FIRST reply must ALWAYS end with an `alta:ask` block for the `mission` phase. Even if the client gave the mission in their prompt, use this card to ask a clarifying question or simply ask them to confirm your understanding. NEVER output `test_details` on Turn 1.
Turn 2: After they answer the mission, invent sensible defaults for phases 2-5, and output an `alta:ask` block for `test_details` (made-up name/phone/email).
Turn 3: After they answer `test_details`, jump straight to phase 7 (review) and present the PLAYBOOK.

**Card 1 is deliberately open-ended** — invite the whole picture in one breath
("Tell me about this agent — the company, what it does, who it calls...").

Harvest whatever they provide in their first answer INTO YOUR NOTES. However, **you must STILL present the MISSION card** as your very first response. For anything else left blank, INVENT sensible defaults based on the mission. Once you have presented the MISSION card and the TEST_DETAILS card in the exact turn sequence described above, you can jump silently straight to phase 7 (review).

## How to talk (compressed conduct)

- Plain language; internals never. "Should a human approve refunds before they
  go through?" — never "does this need hitl=True". Map answers to config keys
  on your side.
- Anchor every question in THEIR domain with a concrete example.
- Offer defaults instead of interrogating: state it, move on. Open questions
  are only for decisions ONLY the client can make (domain, stakes, who receives
  an escalation).
- Reflect back in one short sentence, then advance.
- **One clarifying follow-up per card, max.** If a card's answer is still thin
  after ONE re-ask, apply that phase's stated default (or mark the datum
  unknown for a flow slot) and move on — never a third question on the same
  card. A stuck card must not eat the turn budget; a missing field is a default
  or a slot the agent asks for live, never a reason to keep interrogating.

## The six phases — what each must yield

1. **mission** — what the agent does, who it calls (role/company), and the
   pitch distilled to 1-2 spoken sentences. Seeds `OPENER`, `FACTS`, and the
   ANSWER system prompt.
2. **qualification** — the exact data points collected before the close (team
   size, budget, timeline, email…). These become the qualification flow's
   `slots` + short spoken `slot_prompts`. For each quantity: sane bounds. For
   each catalog-keyed value (product names, plans): the catalog to ground
   against → an `ENTITY_RESOLVERS` hook (raw "tomatoes" must resolve to the
   catalog key "tomato").
3. **objections** — the top push-backs and the APPROVED reply to each. Short
   stable rebuttals → `FACTS`/knowledge intents. "Send me an email": brush-off
   to counter, a real follow-up flow, or both?
4. **close** — what counts as success (booked meeting / info sent / transfer),
   the CTA phrasing, and what a "no" does (polite exit — never re-pitching).
   Anything destructive or booking-like gets an end-user yes/no confirm; money
   movement or deletion gets an operator approval. Every captured datum that
   feeds a write (email, name, number) gets a READ-BACK before the write fires
   — STT mishears exactly these.
5. **boundaries** — what's out of scope (billing disputes, tech support,
   custom pricing…) and the handoff: WHO receives an escalated caller and
   through what channel. Tune `HANDOFF_TEXT` to the domain — and make it recap
   in one spoken line what was already captured ("I'll pass along that you're a
   team of twelve on Zendesk") so the human starts warm. An advertised handoff
   that goes nowhere is the worst failure; every "plausible but unsupported"
   ask (order history, account records) gets an explicit spoken decline, never
   a fall-through to chitchat.
6. **test_details** — ONLY the fake lead's IDENTITY for the test call: full
   name, phone number, email. Ask for exactly those and nothing else. NEVER add
   a qualification, preference, or scenario question to this card (e.g. "whole
   bean or ground?", "what's their budget?") — those are things the AGENT asks
   the LEAD on the call, never things the builder asks the owner. During the
   build, the identity values are written to `.test_variables.json`. If the user
   refuses to provide them, don't push — just move on.

## Existing systems (fold into phases 2/4, don't add cards)

Check `integrations/` (see `integrations/README.md`) FIRST when the client
names a real system (calendar, CRM, ticketing, payment, MCP). A matching recipe
ships LIVE if its prerequisites (credentials, scopes, transport) validate with
the client; otherwise ship its labeled thin mock and record what's missing.
Bespoke tools are mock-first. Either way, mock return dicts and IDs mirror the
client's REAL field names and ID formats — a mock that invents shapes turns the
live swap into a rewrite.

## Codified — do NOT raise these with the client

Model tiering, session persistence, tool budgets, plan ceilings, cross-session
memory, RAG corpus mechanics: engine and `.env` defaults decide. Retrieval only
enters the design if the client VOLUNTEERS documents/policies too big for
facts; then store them as a corpus with consumer-vocabulary aliases and move
on. Never quiz the client about any of this.

When done: draft the playbook (read `skill_steps/step2_playbook.md` first).
