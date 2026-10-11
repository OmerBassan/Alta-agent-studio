---
id: SPEC-alta-agent-studio
companions:
  - brownfield.md
  - ../../../CLAUDE.md
  - ../../../ARCHITECTURE.md
  - ../../../DEMO.md
sources:
  - ../../../README.md
  - ../../../SETUP.md
---

> **Canonical contract.** This SPEC and the files in `companions:` are the complete, preservation-validated contract for what to build, test, and validate. Source documents listed in frontmatter are for traceability — consult them only if you need narrative rationale or prose color this contract intentionally omits.

# Alta Agent Studio — Voice Agent Builder Platform

## Why

**A vision to realize.** Building a voice AI SDR today means hand-writing a state machine, a prompt set, a latency strategy, and a test harness — work that locks the capability to whoever can write it. Alta Agent Studio collapses that into a conversation: describe the agent, approve the design, and a complete, selftest-proven LangGraph project exists; say "also ask about budget" and the next call reflects it. The audience is a reviewer who must see the loop close end to end in five minutes, and the operator who afterward owns a portable agent bound to no vendor. The deliverable is the **builder platform** — every agent it produces is a standalone Python project, which is why no single generated agent is worth optimizing beyond proving the platform.

This began as a three-day home assignment; that build shipped and was proven on a real call. It is now an **ongoing project**, and the work is improvement-driven rather than milestone-driven. The standing rule for that work: a named optimization is a hypothesis about this codebase, not a spec — confirm the mechanism it targets exists on the hot path here before implementing it, and never add a model call to the reply path in the name of latency.

## Capabilities

- **CAP-1** — chat-driven generation
  - **intent:** A user describes the agent they want in plain language and receives a complete, standalone voice-agent project without writing code.
  - **success:** From a cold prompt, the guided design conversation (discovery → playbook → contract → build) produces a full copy of `boilerplate/` with domain surfaces written, and `Generated_Agents/<Agent>/` runs on its own.

- **CAP-2** — the selftest gate
  - **intent:** The platform proves a generated agent before anyone can reach it, so an unproven agent is never callable.
  - **success:** `python selftest.py` runs as a subprocess and must exit 0; a failing agent is refused and never served, and the status orb does not light.

- **CAP-3** — natural-language edit loop
  - **intent:** A user states a behavior change in chat and hears it on the next call, with no rebuild ceremony.
  - **success:** After one chat instruction, the builder edits only domain surfaces, re-runs the selftest gate, respawns the runtime subprocess, and the change is audible on the immediately following call.

- **CAP-4** — live voice test call
  - **intent:** A user places a real call to the agent they just built, from the same screen.
  - **success:** One click reaches the agent over Vapi custom-LLM through `POST /v1/chat/completions` with strict OpenAI SSE and `x-vapi-secret` auth; `call.id` maps to a `thread_id` so state holds across turns.

- **CAP-5** — dead-air cover
  - **intent:** The caller never hears silence that reads as a dropped line.
  - **success:** Four mechanisms are in force on every turn — pre-think filler as the first SSE chunk before the graph runs, per-tool filler banks debounced by `FILLER_DELAY_MS`, sentence-chunked replies, and a `RUNTIME_TURN_TIMEOUT_S` ceiling that speaks a short apology.

- **CAP-6** — portable, provider-agnostic output
  - **intent:** The operator can take a generated agent elsewhere and point it at whatever model endpoint they have.
  - **success:** Swapping providers is an `.env` edit with zero code change (`OPENAI_BASE_URL`/`OPENAI_API_KEY` + `AGENT_INTENT/ANSWER/ENRICH_MODEL`); a blank key runs deterministic MOCK mode; the project downloads as a zip.

- **CAP-7** — second surface on one core
  - **intent:** A developer already in Claude Code builds an agent in their own terminal without the web UI.
  - **success:** `/alta-builder:alta-build` drives the same `builder_core.py` functions through a bundled MCP server and guard hook, writing output into the invoker's cwd, with no forked skill or engine content.

## Constraints

- **Voice-only.** Every user-facing string is written to be SPOKEN: ≤20 words, no markdown, lists, or URLs, acronyms in pronounceable form, one question per turn. `boilerplate/agent_sandbox.py` is the single dev-only text REPL and does not relax this.
- **Latency is correctness.** Dead air is a failure, not a performance nit. No model call joins the reply path without being justified against the latency budget.
- **Wholesale isolation (Lovable/v0 paradigm).** A generated agent is a full copy of `boilerplate/` with only domain surfaces edited (`config.py`, `tools.py`, `prompts.py`, selftest `SCRIPT`/`HOOK_CHECKS`, `.env`, corpus, README). Engine files are copied verbatim; engine fixes go upstream in `boilerplate/` once, never per agent.
- **Provider-agnostic STRICT.** A generated agent binds no LLM provider: no vendor SDK import, no hardcoded provider or base URL, no branching on provider, no vendor-specific key. Model names are env defaults, never literals in logic.
- **The selftest is the gate.** No generated agent ships without `python selftest.py` passing in mock mode.
- **Deterministic director.** The call agenda is a cursor over `CALL_ARC`, advanced only by machine-checkable predicates (`flow_complete`, `session_fact`, `agent_led_once`, `intent_seen`). Routing costs zero tokens and zero model calls; the advance is monotonic and bounded by arc length.
- **Text needing the pre-TTS sanitizer is a defect** upstream, not a licensed shortcut.
- **Subprocess-per-agent.** Regenerating an agent restarts the runtime process and never re-imports, because module-name collision is a live trap.
- **One shared core.** `builder_core.py` is the single source for both `builder.py` and `claude_plugin/`; it is never forked.
- **Conversational budgets are CI gates, not prose.** `MAX_REPLY_WORDS = 20` is counted by code before emission, and five preflight checks (voice, objection, persona, call-arc, tie-down) fail the build rather than advise.

## Non-goals

- Optimizing any single generated agent beyond what proves the platform works.
- Any terminal or shell surface in the product a caller or reviewer ever sees.
- Hosted multi-tenant deployment — the platform runs locally from one `.env`.
- Vendor-specific features in generated agents, even where a provider offers something better than the OpenAI-compatible `/v1` surface.

## Success signal

A reviewer runs DEMO.md Path B cold: they describe an agent in chat, approve the design, watch the selftest pass and the orb light, click **Call**, and hear the agent open, ask one qualifying question per turn, and route or close. They then type one change in chat and hear it on the next call. No code is written by the reviewer at any point, and the agent they built is theirs to download.

## Assumptions

- The spec records a system already built and proven on a real call (2026-07-15), not work to be done. It was derived from the shipped docs plus the repo as it stands, with every suite green: 183 tests in `builder_platform/tests/`, 195 including `claude_plugin/tests/`.
- `Generated_Agents/BassanBrewerySDR/` is the checked-in demo artifact DEMO.md Path A depends on, not a work product to improve.
- Improvement work is ranked by measurement, not by technique name. Since no latency or token instrumentation exists yet (no timing on any model call; `vapi_adapter.py:200` hardcodes `usage` to zeros), the first increment is the measurement layer and every later ranking is provisional until it reports.

## Open Questions

- Should the uncommitted `_speak_value` fix in `boilerplate/nodes.py` get its regression test and be committed before the improvement work starts?
- Does streaming model tokens through to TTS (rather than sentence-chunking a finished `final_response`) justify its risk to the deterministic appenders — the tie-down, the director nudge, and the `MAX_REPLY_WORDS` count that all currently operate on complete text?
- Is a persisted lead/call store (SQLite or Postgres, replacing per-call JSON flushes) in scope, given the non-goal of hosted multi-tenant deployment?
