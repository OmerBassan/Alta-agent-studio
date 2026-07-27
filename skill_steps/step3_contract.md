# Step 3 — The Config Contract (read with step4, after playbook approval)

Everything below derives from the approved playbook — never invented at code
time. Plan it silently; do NOT present it to the client (the playbook was the
sign-off).

## config.py plan

- `KNOWLEDGE_INTENTS` + `INTENT_DESCRIPTIONS`: one intent per fact-answerable
  question family, including an explicit DECLINE intent for every plausible-
  but-unsupported ask from discovery.
- `FLOWS`: per flow — tool, `slots`, spoken `slot_prompts`, `confirm=True` (+
  spoken `confirm_template`) on destructive/booking flows, `hitl=True` on money
  movement/deletion, per-slot `validators` (bounds from the catalog entry,
  never a hardcoded limit), `cache_keys` for hard identifiers only.
- `CALL_ARC` (OUTBOUND only; leave empty for an inbound agent): the ordered
  sales spine (opener→discovery→qualify→close) as `Stage`s the engine's
  zero-model director walks so the agent LEADS. One Stage per SPINE scene;
  objections/FAQs stay reactive. Per stage: `objective` (the goal, injected into
  the ANSWER prompt), `flow` POINTING at the qualify flow (never re-author its
  questions — they ARE its `slot_prompts`), `line` (a scripted move for a
  flow-less stage, e.g. the close CTA), `nudge` (the approved steer-back after a
  lead question), `advance_when` (structured only: `flow_complete`/
  `session_fact`/`agent_led_once`/`intent_seen`). EXTRACT every field from the
  playbook; a Stage without a scene is a defect.
- `ENTITY_RESOLVERS`: one per catalog-keyed slot; share its synonym/plural
  logic with the mock extractor (live mode hands the resolver RAW text).
- `FACTS`: the pitch, plans/prices, short stable rebuttals — the only ground
  truth; it never invents beyond this. CRITICAL: extract ALL offers, prices,
  discounts, and free samples from the mission into FACTS. Anything omitted the
  runtime will hallucinate or flatly decline.
- `NEXT_STEP_HINTS`: THE one allowed follow-up sentence per tool.
- Filler banks in the agent's own voice: `FILLERS_BY_TOOL` (3-5 per flow tool),
  `FILLER_DEFAULT`, `FILLER_PLAN_CONTINUE`, `FILLER_THINKING` (4-6 sub-second
  acks — "Hmm.", "Right." — safe ahead of ANY reply, never "Sure!"). End every
  filler with a period, NEVER an ellipsis (the transport buffers un-terminated
  text → dead air).
- `OPENER` per the step2 rule. OUTBOUND: compress the mission's pitch into the
  hook (who's calling + WHY), not bare identity — else the lead is interrogated
  with no context.
- `BLOCKED_PATTERNS` from the boundaries phase; `HANDOFF_TEXT` with its one-line
  recap; mock keywords/extractors mirroring the resolvers.

If the playbook has a create-then-modify need ("cancel that booking"), add the
companion flow whose entity-id slot resolves from `last_action` before asking.

## tools.py plan

Each tool: signature, structured return dict, a `"summary"` sentence. Field
names and ID formats mirror the client's REAL systems (from discovery).
Write-tools are idempotent (a retry never double-books), return typed errors,
and a failed write gets a SPOKEN fallback plus a logged retry — a silently
dropped lead is the worst failure. Secrets (SMTP, API keys) come from `.env`,
never source.

If the client volunteered a corpus: `RETRIEVAL_INTENTS` + `DOCS` with
consumer-vocabulary `aliases`, and ≥3 `RETRIEVAL_PROBES` per intent phrased
from the USER's side (never copied from the doc text).

Model tiers/budgets/timeouts: leave the boilerplate/.env defaults alone (a
stronger ANSWER model follows tone lines more literally — over-steering bites
harder).

prompts.py: tone lines + the spoken-style block, nothing else. The engine now
injects the outbound framing and the current CALL_ARC `objective` into the
ANSWER prompt (ENGAGE-FIRST: answer what the lead said, THEN take one step), so
the tone line only needs the agent's VOICE/personality — do NOT re-add
absolutist "always close" wording (it makes the tier ignore objections and
re-ask slots).
