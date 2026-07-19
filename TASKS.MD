# Alta Agent Studio — Ship List

> 3-day assignment. Every item below earns demo points or is a blocker.
> If it doesn't make the demo better or prevent a crash, it doesn't belong here.
> Last reconciled 2026-07-18 against files on disk + green platform test suite.

## What "Done" Looks Like

User opens browser -> chats with the builder -> builder generates a voice agent -> selftest passes -> orb lights up -> user clicks "Call" -> talks to the agent on a real call.

---

## Must Do (Blockers for Submission)

- [x] **Pre-submission Key Purge & UI Strip**: credentials panel removed from the UI (Download button kept); `/api/agent/env` endpoints remain for owner use via curl.
- [x] **Automated Setup Dashboard**: first-run setup overlay now also takes the OpenAI key (`/api/auth/setup` writes root `.env`; inherited by the voice runtime — no per-agent entry). Subscription mode kept; Vapi-safety note shown.
- [x] **Root README.md**: description + mermaid architecture diagram + 3-step setup.
- [x] `.env.example` **setup**: audited; added `VAPI_PUBLIC_KEY`, `VAPI_ASSISTANT_ID`, `RUNTIME_PORT=8000` (port-clash guard vs app's 8100), `PUBLIC_URL`.
- [x] **Automated launch scripts**: `run.bat` + `run.sh` — venv, pip install, `.env` seed, uvicorn on 8100.
- [x] **Clean** `requirements.txt`: root file with only the 10 packages actually used, pinned to the tested versions.
- [ ] **Repository cleanup**: OWNER — run the PowerShell block Claude provided (`__pycache__`, `.pytest_cache`, old DB, run.log; no `.DS_Store` found).
- [x] `.gitignore`: paths fixed to `builder_platform/`, added `submission_skeleton.txt`, DB sidecars, logs.
- [x] **FastAPI database init**: already satisfied — idempotent `init_db()` at import (app.py:75), works under TestClient too. No change needed.
- [x] **Robust API error handling**: chat stream now emits actionable messages (bad Anthropic key → "re-enter it in setup") instead of raw `repr(exc)`; OpenAI side already degrades to mock, never 500s.
- [ ] **Edit-loop proof**: stale-runtime bug FIXED (pass-marker change now stops the warm runtime so the next call respawns on edited files — app.py `_chat_events`). Remaining: one real Vapi call by owner to confirm end-to-end.

## Should Do (Demo Quality & Polish)

- [x] **DEMO.md**: Reviewer script (describe -> generate -> call -> qualify -> book -> edit -> call again) + 2 cold rehearsals.
- [x] **One pre-built demo agent**: A fully passing agent in `Generated_Agents/` so reviewers can test voice immediately without waiting for a build.
- [x] **Fix "I'd change something" button**: Allow user to directly edit the design text within the tab and submit for final approval.
- [x] **Python logging**: Implement clear logging to output major backend events gracefully (new sessions, agent configs).
- [x] **Codebase restructuring**: Move testing scripts into `tests/` and organize UI/frontend files neatly into `static/`.
- [x] **Agent behavioral rule**: Hardcode a strict rule that if a lead firmly says no, the agent must politely thank them and end the call without nudging.
- [x] **Metadata injection**: Codify the system to inject the lead's metadata directly into the context of the outbound call agent.

## Nice to Do / Later (Deferred or High Risk)

- [ ] **File Upload Pipeline**: Implement "drop file" card in UI strictly restricted to `.txt`/`.md` formats, plus backend storage/context injection.

## Done

- [x] **Tic-tac-toe game**: Integrated into `index.html` as Vanilla JS for zero-risk waiting entertainment.
- [x] `platform/storage/` — SQLite DB layer (schema + manager + tests, 9/9 passing)
- [x] `references/` audit — cleaned CLI->Voice terminology, deleted stale file, expanded principles
- [x] `tasks.md` created
- [x] **Day 1 — Vapi round-trip + real brain**: `platform/vapi_adapter.py` (strict OpenAI SSE +
  ```
  `x-vapi-secret` auth), `runtime.py` (generated-project loader + filler->SSE turn runner),
  `sanitizer.py` (buffered pre-TTS), `tunnel.py` (ngrok) — all tested
  ```
- [x] **Day 2 AM — Builder (Claude Agent SDK)**: `platform/builder.py` (headless wrapper +
  ```
  write-allowlist permission hook + selftest subprocess gate), `builder_selfcheck.py`,
  `ask_protocol.py`; real generations exercised in `workspaces/` (Jul 16–17)
  ```
- [x] **Day 2 PM — Platform server + dynamic agent loading**: `platform/app.py`
  ```
  (`/api/chat`, `/api/agent`, `/api/call`, `/v1` proxy), `runtime_supervisor.py`
  (subprocess-per-agent, restart on regenerate), `vapi_control.py` (PATCH assistant +
  firstMessage rules / blank-opener guard)
  ```
- [x] **Day 3 AM — UI**: `platform/static/index.html` (chat pane, file upload, orb + call
  ```
  button, SSE streaming, runtime status dot — wired to Day-2 endpoints)
  ```
- [x] **Platform test suite green**: `python -m pytest platform/tests/` -> 118 passed