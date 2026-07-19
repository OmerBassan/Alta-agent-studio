# Step 3 — The Config Contract (read with step4, after playbook approval)

Everything below derives from the approved playbook — never invented at code
time. Plan it silently; do NOT present it to the client (they approved the
playbook; that was the sign-off).

## config.py plan

- `KNOWLEDGE_INTENTS` + `INTENT_DESCRIPTIONS`: one intent per fact-answerable
  question family, including an explicit DECLINE intent for every plausible-
  but-unsupported ask from discovery.
- `FLOWS`: per flow — tool, `slots`, spoken `slot_prompts`, `confirm=True` (+
  spoken `confirm_template`) on destructive/booking flows, `hitl=True` on money
  movement/deletion, per-slot `validators` (bounds from the catalog entry,
  never a hardcoded limit), `cache_keys` for hard identifiers only.
- `ENTITY_RESOLVERS`: one per catalog-keyed slot; share its synonym/plural
  logic with the mock extractor (live mode hands the resolver RAW text).
- `FACTS`: the pitch, plans/prices, and short stable rebuttals — the agent's
  only ground truth; it never invents beyond this.
- `NEXT_STEP_HINTS`: THE one allowed follow-up sentence per tool.
- Filler banks, all in the agent's own spoken voice: `FILLERS_BY_TOOL` (3-5 per
  flow tool), `FILLER_DEFAULT`, `FILLER_PLAN_CONTINUE`, and `FILLER_THINKING`
  (4-6 sub-second acknowledgments — "Hmm…", "Right." — safe ahead of ANY reply
  type, never "Sure!").
- `OPENER` per the step2 rule (plain literal, ≤20 words, ends with a question).
- `BLOCKED_PATTERNS` from the boundaries phase; `HANDOFF_TEXT` with its
  one-line recap; mock keywords/extractors mirroring the resolvers.

If the playbook has a create-then-modify need ("cancel that booking"), add the
companion flow whose entity-id slot resolves from `last_action` before asking.

## tools.py plan

Each tool: signature, structured return dict, and a `"summary"` sentence.
Field names and ID formats mirror the client's REAL systems (from discovery).
Write-tools are idempotent (a retry never double-books), return typed errors,
and a failed write gets a SPOKEN fallback plus a logged retry — a silently
dropped lead is the worst failure.

If the client volunteered a corpus: `RETRIEVAL_INTENTS` + `DOCS` with
consumer-vocabulary `aliases`, and ≥3 `RETRIEVAL_PROBES` per intent phrased
from the USER's side (never copied from the doc text).

Model tiers, budgets, timeouts: **leave the boilerplate/.env defaults alone.**
prompts.py: tone lines only, plus the spoken-style block. Nothing else.
