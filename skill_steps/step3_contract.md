# Step 3 — The Config Contract (read with step4, after playbook approval)

All of this derives from the approved playbook — never invented at code time.
Plan silently; do NOT present it (the playbook was the sign-off).

## config.py plan

- `KNOWLEDGE_INTENTS` + `INTENT_DESCRIPTIONS`: one intent per fact-answerable
  question family, plus an explicit DECLINE intent for every plausible-but-
  unsupported ask from discovery.
- `FLOWS`: per flow — tool, `slots`, spoken `slot_prompts`, `confirm=True` (+
  `confirm_template`) on destructive/booking flows, `hitl=True` on money
  movement/deletion, per-slot `validators` (bounds from the catalog entry, never
  hardcoded), `cache_keys` for hard identifiers only.
- `CALL_ARC` (OUTBOUND only; empty for inbound): the spine
  (opener→discovery→qualify→close) as `Stage`s the zero-model director walks so
  the agent LEADS. One Stage per SPINE scene; objections/FAQs stay reactive. Per
  stage: `objective` (goal, injected into the ANSWER prompt), `flow` POINTING at
  the qualify flow (never re-author its questions — they ARE its `slot_prompts`),
  `line` (scripted move for a flow-less stage), `nudge` (steer-back after a lead
  question), `advance_when` (structured only: `flow_complete`/`session_fact`/
  `agent_led_once`/`intent_seen`). EXTRACT every field; a Stage without a scene
  is a defect.
- Objections (OUTBOUND; EXTRACT from the playbook's rebuttal table):
  `OBJECTION_INTENTS` (each ALSO a `KNOWLEDGE_INTENT`, so rebuttals stay
  grounded), `OBJECTION_TOPICS` (intent → spoken noun, "the price"),
  `OBJECTION_ISOLATE_TEMPLATE` (one `{topic}` question, asked once per call).
  The engine supplies Acknowledge + Pivot; a firm no is `goodbye`, never an
  objection. `TIEDOWNS` (3-6 words, each a question) + `TIEDOWN_EVERY_N_TURNS`
  (2-3; 0=off) — appended only to statement-ending turns. Field-level rules live
  in the `[CUSTOMIZE]` blocks in config.py; read them there, not here.
- `ENTITY_RESOLVERS`: one per catalog-keyed slot; share its synonym/plural
  logic with the mock extractor (live mode hands the resolver RAW text).
- `FACTS`: pitch, plans/prices, short stable rebuttals — the only ground truth.
  CRITICAL: extract ALL offers, prices, discounts, and free samples from the
  mission; anything omitted the runtime hallucinates or flatly declines.
- `NEXT_STEP_HINTS`: THE one allowed follow-up sentence per tool.
- Filler banks in the agent's voice: `FILLERS_BY_TOOL` (3-5 per flow tool),
  `FILLER_DEFAULT`, `FILLER_PLAN_CONTINUE`, `FILLER_THINKING` (4-6 sub-second
  acks — "Hmm.", "Right." — never "Sure!"). End every filler with a period,
  NEVER an ellipsis (un-terminated text buffers → dead air).
- `OPENER` per the step2 rule. OUTBOUND: compress the pitch into the hook (who's
  calling + WHY), not bare identity — else the lead is interrogated blind.
- `BLOCKED_PATTERNS` from the boundaries phase; `HANDOFF_TEXT` with its one-line
  recap; mock keywords/extractors mirroring the resolvers.

Create-then-modify need ("cancel that booking")? Add the companion flow whose
entity-id slot resolves from `last_action` before asking.

## tools.py plan

Each tool: signature, structured return dict, a `"summary"` sentence. Field
names/ID formats mirror the client's REAL systems. Write-tools are idempotent
(a retry never double-books), return typed errors, and a failed write gets a
SPOKEN fallback plus a logged retry. Secrets come from `.env`, never source.

Corpus volunteered? `RETRIEVAL_INTENTS` + `DOCS` with consumer-vocabulary
`aliases`, ≥3 `RETRIEVAL_PROBES` per intent phrased from the USER's side.

Model tiers/budgets/timeouts: leave the .env defaults alone (a stronger ANSWER
model follows tone lines more literally — over-steering bites harder).

prompts.py: tone lines + the spoken-style block, nothing else. The engine
injects the outbound framing, the CALL_ARC `objective`, and the objection
Acknowledge rule (ENGAGE-FIRST: answer the lead, THEN take one step), so the
tone line only needs VOICE/personality — do NOT re-add absolutist "always
close" wording (the tier then ignores objections and re-asks slots).
