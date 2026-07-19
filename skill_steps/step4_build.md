# Step 4 — Build (read with step3; then write files)

## Sequence

1. **Instantiate** via the `instantiate_boilerplate` tool only (give the
   agent's name). Never copy files yourself. The platform also creates the
   project's `.env` for the operator to fill.
2. **Customize** — read ONLY the files you will edit, then edit ONLY these
   domain surfaces: `config.py`, `tools.py`, `prompts.py` (tone + spoken-style
   block), `selftest.py`'s `SCRIPT`/`HOOK_CHECKS`, `README.md`, corpus files.
   If the client provided `test_details`, create a `.test_variables.json` file containing
   those details as a flat JSON dictionary.
   Engine files (`graph.py`, `nodes.py`, `schemas.py`, `llm_client.py`,
   `rag_subgraph.py`, `compaction.py`, `filler.py`) are copied verbatim and
   write-blocked — never read them, never edit them; engine fixes go upstream
   in `boilerplate/`, once.
3. **Voice style pass** — every user-audible string (OPENER, HELP/STALL/
   HANDOFF text, slot prompts, confirm templates, NEXT_STEP_HINTS, enrich
   templates, ALL filler banks) obeys the step2 voice rules: spoken, ≤20 words,
   complete sentences, no lists/markdown/URLs, acronyms as pronounced, one
   question per turn. Inject the same constraints as a spoken-style block into
   the generated ANSWER system prompt.
4. **Selftest gate** — run the `run_selftest` tool ONCE at the end of the
   build. `SCRIPT` replays the playbook's happy path; `HOOK_CHECKS` exercise
   every resolver and bounds validator with RAW live-style values (plurals,
   synonyms, absurd quantities — mock extractors pre-normalize, so the script
   alone proves nothing about resolvers). On FAIL: fix the ONE named failure
   and rerun — the platform allows a single rerun; if it still fails, tell the
   client plainly what failed and stop.
5. **Seal credentials** — `.gitignore` already covers `.env` and common
   credential artifacts; if this build stores auth anywhere else, append that
   exact path before handing over.

## Write-time laws (full text — these bind every file you write)

- **Provider-agnostic, STRICT:** the agent binds NO LLM provider. Its only
  contract is the OpenAI-compatible `/v1` interface via env
  (`OPENAI_BASE_URL`/`OPENAI_API_KEY`, `AGENT_INTENT/ANSWER/ENRICH_MODEL`).
  Never import a vendor SDK, hardcode a base URL, branch on provider, or read
  a vendor key. Model names are env defaults, never literals in logic. Blank
  key ⇒ deterministic MOCK mode (what the selftest runs). Swapping providers
  is an `.env` edit with zero code change — if a design needs a code change to
  swap, the design is wrong.
- **Pre-built Email Tool:** Every project automatically inherits an edit-proof `send_email` tool in `tools.py` that sends real emails. If the design requires booking a meeting or sending an email, DO NOT write a new tool. Simply wire the existing `send_email` tool into the agent's logic (via `config.py` flows) and inform the agent it has the ability to send emails. Never delete or modify the `send_email` definition in `tools.py`.
- **Fillers are canned:** every filler comes from the design-time bank — never
  a runtime model call. `FILLER_THINKING` tokens are sub-second and safe ahead
  of any reply type.
- **Enrichment never asks questions** and never offers anything absent from
  the tool's JSON; the only follow-up is the `NEXT_STEP_HINTS` sentence.
- **Detours don't kill flows:** a mid-flow question preserves the pending slot
  and ends with a deterministic resume line.
- **Refused slots are engine-handled:** a lead's decline stores
  `config.SLOT_REFUSED` (`"<declined>"`) in the slot — never re-asked. Tools you
  write must branch on that sentinel (proceed gracefully or say what's
  possible without it), never treat it as a real value.
- **English-only by default;** other languages are an explicit, tested add-on.
- **OPENER** per the step2 rule: plain string literal, ≤20 words, human
  phone-pickup tone, ends with one question, never empty — it is spoken at
  pickup by the platform with zero model calls.
- Catalog promotion is disabled in the platform — skip it.

Done means: selftest PASS + every surface passed the voice style pass. Close
with the single line the platform brief mandates — no summary.
