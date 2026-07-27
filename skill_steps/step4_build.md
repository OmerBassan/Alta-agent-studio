# Step 4 — Build (read with step3; then write files)

## Sequence

1. **Instantiate** via the `instantiate_boilerplate` tool only (give the
   agent's name). Never copy files yourself. The platform also creates the
   project's `.env` for the operator to fill.
2. **Customize** — BATCH edits (`MultiEdit`) to save tokens. SILENT EDITING: no
   text response with an edit call, just the call. Read ONLY the files you edit,
   then edit ONLY these domain surfaces: `config.py` (intents, FLOWS, FACTS,
   fillers, `CALL_ARC` + `SUMMARY_TEMPLATE`), `prompts.py` (tone + spoken-style
   block), corpus files. DO NOT edit `tools.py` or create `README.md` — tools
   are pre-built and edit-proof; wire the playbook onto them via `config.py`
   flows. Uploaded knowledge auto-loads into DOCS (retrieval) — a FAQ that must
   answer from it has to be a RETRIEVAL_INTENT.
   **NEVER edit `selftest.py`** — it is fixed and DOMAIN-AGNOSTIC: it derives
   every check from your `config.py` (intents, flows, keywords, facts, arc) and
   adapts automatically. Writes to it are blocked; there is no test to author.
   If the client provided `test_details`, create a `.test_variables.json` file
   containing those details as a flat JSON dictionary.
   Engine files (`graph.py`, `nodes.py`, `schemas.py`, `llm_client.py`,
   `rag_subgraph.py`, `compaction.py`, `filler.py`) are copied verbatim and
   write-blocked — never read them, never edit them; engine fixes go upstream
   in `boilerplate/`, once. The proactive director is engine code you drive with
   `CALL_ARC`, never edit.
3. **Voice style pass** — every user-audible string (OPENER, HELP/STALL/HANDOFF
   text, slot prompts, confirm templates, NEXT_STEP_HINTS, enrich templates, all
   filler banks, every `Stage.line`/`Stage.nudge`) obeys the step2 voice rules
   (spoken, ≤20 words, one question, no lists/markdown/URLs, acronyms as
   pronounced). Inject the same constraints as a spoken-style block into the
   ANSWER system prompt.
4. **Selftest gate** — run the `run_selftest` tool ONCE at the end of the
   build (it takes no arguments). It runs the fixed, config-derived test in mock
   mode. On FAIL: the failure names a specific config problem (a keyword that
   routes wrong, a knowledge intent with no answer, a missing escalation
   keyword, a `CALL_ARC` stage pointing at an unknown flow) — fix that ONE thing
   in `config.py`/`prompts.py` and rerun. Never edit `selftest.py` to pass. If
   it fails at the limit, report it WITHOUT the words 'selftest'/'boilerplate'/
   'codebase' (filtered → your message is hidden) — say 'validation checks';
   never fake success. On PASS the backend unlocks the button.
5. **Seal credentials** — `.gitignore` covers `.env`; if this build stores auth
   elsewhere, append that path too.

## Live-call triage (read before touching a model tier)

A bad flight call — missing pitch, an invented offer, a tone that forgets the
call direction, or an agent that WON'T LEAD — is a CONTENT gap until proven
otherwise, never a capability gap. A stronger `AGENT_ANSWER_MODEL` raises
fidelity to what `prompts.py`/`config.py` SAY, not what's true — it executes the
same gap more fluently (a hallucinated offer just reads as more convincing).
Before touching `.env` model tiers, check in order:

1. **Missing pitch** — is the hook actually in `OPENER`, or did a brevity pass
   strip it to bare identity?
2. **Invented detail** — was the fact injected into the node that answered?
   `build_think_system`'s DETOUR sees only `config.FACTS`; ungrounded → invents.
3. **Won't lead / stuck reactive** — is `CALL_ARC` present and correctly
   ORDERED? An empty or mis-ordered arc is why the agent waits to be asked; a
   bigger model cannot invent an agenda that isn't in config.

Only with correct scripting AND repeated evidence of a REASONING failure given
correct grounding does Voice_SDR_Reliability Rule 4's "escalate ANSWER only on
flight-test evidence" apply — never for a missing fact, pitch, or arc.

## Write-time laws (these bind every file you write)

- **Provider-agnostic, STRICT:** the agent binds NO LLM provider — only the
  OpenAI-compatible `/v1` interface via env. Never import a vendor SDK, hardcode
  a base URL, branch on provider, or read a vendor key. Blank key ⇒ MOCK mode
  (what the selftest runs); swapping providers is an `.env` edit, zero code.
- **Secrets live in `.env`, never source** (SMTP creds, API keys). A tool with
  no creds set runs mock, so the selftest stays green.
- **Pre-built tools are edit-proof:** every project inherits `send_email`,
  `book_appointment`, and friends. To book or email, wire the existing tool via
  a `config.py` flow — never write, delete, or modify a tool definition.
- **Fillers are canned** — design-time bank only, never a runtime model call.
  `FILLER_THINKING` tokens are sub-second and safe ahead of any reply; every
  filler ends with a period, never an ellipsis.
- **Enrichment never asks questions** and never offers anything absent from the
  tool JSON; the only follow-up is the `NEXT_STEP_HINTS` sentence.
- **Detours don't kill flows:** a mid-flow question preserves the pending slot
  and ends with a deterministic resume line.
- **Refused slots are engine-handled:** a decline stores `config.SLOT_REFUSED`
  (`"<declined>"`); never re-asked. Wired tools branch on it, never treat it as
  a real value.
- **The arc leads; reactive nodes serve it:** the director advances `CALL_ARC`
  only when the lead hasn't taken the floor (firm-no, objection, question, or an
  in-flight flow all stand it down) — never script the agenda into prompts.
- **English-only by default;** other languages are an explicit, tested add-on.
- **OPENER** per the step2 rule: plain literal, ≤20 words, one question —
  spoken at pickup, zero model calls.

Done means: selftest PASS + every surface passed the voice style pass. Close
with the single line the platform brief mandates — no summary.
