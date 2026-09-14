# Alta Agent Studio — Project Context

## Mission (home assignment, 3-day build)

A platform where a user **chats with an AI builder** that creates and edits a **voice AI assistant** in natural language. The generated assistant calls leads, qualifies them (BANT), and books meetings. Stack: **Claude Agent SDK** (headless, runs the `voice-agent-architect` skill) + **Vapi** (voice transport, custom-LLM mode) + FastAPI platform + thin web UI with a **test-call button**.

The deliverable is the **builder platform**, not any single agent. Never sink time into optimizing an individual generated agent beyond what proves the platform works.

## Hard rules (do not drift)

- **Voice-only.** There is no terminal shell anywhere in the *product surface a caller or recruiter ever sees*. Generated agents are brain-only Python projects; the platform's voice/SSE runtime drives them for a real call. Every user-facing string is written to be SPOKEN (≤20 words, no markdown/lists/URLs, acronyms in pronounceable form, one question per turn). One deliberate, dev-only exception: `boilerplate/agent_sandbox.py` (an engine file, `python agent_sandbox.py`) is a text-chat REPL for a developer to sanity-check a build without Vapi/ngrok/a browser — it is never client-facing, never wired into the voice/SSE runtime, and does not relax the SPOKEN-string rule (the text it prints is the same `final_response` a call would speak).
- **Latency is correctness.** Dead air on a call is a failure. The cover stack: pre-think filler (`FILLER_THINKING`, first SSE chunk before the graph runs) → per-tool filler banks → sentence-chunked final reply. Never add a model call to the reply path without justifying it against the latency budget.
- **Wholesale isolation (Lovable/v0 paradigm).** A generated agent is a full copy of `boilerplate/` with ONLY the domain surfaces edited (`config.py`, `tools.py`, `prompts.py`, selftest `SCRIPT`/`HOOK_CHECKS`, `.env`, corpus, README). Engine files (`graph.py`, `nodes.py`, `schemas.py`, `llm_client.py`, `rag_subgraph.py`, `compaction.py`, `filler.py`) are copied verbatim and never edited per agent — engine fixes go upstream in `boilerplate/` once.
- **Provider-agnostic LLM (STRICT).** A generated agent binds NO LLM provider. Its only LLM contract is the OpenAI-compatible `/v1` interface, configured entirely by env (`OPENAI_BASE_URL`/`OPENAI_API_KEY` + `AGENT_INTENT/ANSWER/ENRICH_MODEL`). Never import a vendor SDK, hardcode a provider/base-URL in code, branch on provider, or read a vendor-specific key. Model names are env defaults, never literals in logic. Swapping providers is an `.env` edit — zero code change. Blank key = MOCK mode (what the selftest runs). Full rule: SKILL.md Rules of Engagement.
- **Selftest is the gate.** No generated agent ships without `python selftest.py` passing in mock mode.
- **Text needing the pre-TTS sanitizer is a defect.** The sanitizer (`builder_platform/sanitizer.py`) is a backstop, not a license.

## Directory map

| Path | Role | Write policy |
|---|---|---|
| `SKILL.md` | The builder's brain, SLIM core: `voice-agent-architect` (indexes `skill_steps/`; read-schedule table inside) | Edit deliberately; it steers all generations |
| `skill_steps/` | Per-phase skill files (step1_discovery → step4_build), each read EXACTLY ONCE at its moment — the token-diet split of the old monolith | Edit deliberately; budgets are pytest-enforced |
| `boilerplate/` | Tested engine + domain-surface template, copied wholesale per agent | Engine improvements ONLY here, never per agent |
| `references/` | Architecture theory the skill consults | Read-only |
| `integrations/` | Validated copy-adapt recipes (calendar, CRM…) | Read-write catalog; recipes copy-adapted, never imported |
| `builder_platform/` | Vapi adapter (`vapi_adapter.py`, OpenAI-compatible SSE), agent runtime (`runtime.py`), sanitizer, tests; builder/app/UI land here. `builder_core.py` is the shared deterministic engine (paths, write/read policy, instantiate, selftest gate) — single source for both `builder.py` (web platform) and `claude_plugin/` (Claude Code plugin); edit here, never fork | Product code |
| `claude_plugin/` + `.claude-plugin/`, `commands/`, `hooks/` (repo root) | The `/alta-build` Claude Code plugin surface: bundled MCP server + guard hook wrapping the same `builder_core.py` functions, native-terminal UX (no `alta:ask` cards), output lands in the invoker's cwd | Edit `claude_plugin/`; never fork skill/engine content — it reads `SKILL.md`/`boilerplate/`/etc. from the same repo root. The MCP server is declared INLINE in `.claude-plugin/plugin.json`; never add a root `.mcp.json` — that path is also the project-scope MCP location, so this repo (its own plugin root) would load it twice, and the project-scope loader leaves `${CLAUDE_PLUGIN_ROOT}` unsubstituted |
| `Generated_Agents/` | Output directory for skill generations; holds the checked-in example agent | Created by the skill |

## Architecture (proven on a real call, 2026-07-15)

Vapi (custom-LLM) → ngrok → `builder_platform/vapi_adapter.py` (`POST /v1/chat/completions`, strict OpenAI SSE, `x-vapi-secret` auth) → `builder_platform/runtime.py` (loads one generated agent via `sys.path` + `build_pipeline(MemorySaver)`; `call.id → thread_id`; filler→SSE asyncio.Queue with try/finally sentinel + timeout apology; dedupe guard for corrected-transcript re-sends; buffered pre-TTS sanitizer). Subprocess-per-agent: regenerating an agent restarts the runtime process, never re-imports (module-name collision trap).

Known Vapi trap (cost a day): an assistant `firstMessage` of a single space wedges the entire TTS queue silently — the fault lives in Vapi's assistant config, not the stream. Logged in the reasoning journal.

## Verification

- Platform: `python -m pytest builder_platform/tests/` (must stay green).
- Generated agents: their own `selftest.py`, exit 0, enforced after every generation/edit.
- Voice: a real Vapi flight call at the end of every working half-day.

## Plan

The 3-day plan lives at `~/.claude/plans/continue-and-plan-first-resilient-tide.md`; task order in `TASKS.MD`. Current position: Phase 1 cleanup done → next is Day 2 AM, `builder_platform/builder.py` (Agent SDK headless wrapper + write-allowlist permission hook + selftest subprocess gate).
