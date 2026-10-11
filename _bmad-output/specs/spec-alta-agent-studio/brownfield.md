# Brownfield notes — what exists, and what may be touched

Read before changing anything. This system is built and verified; the write policy below is enforced by tests and by project rule, not convention.

## Verification state (observed 2026-10-06)

| Command | Result |
|---|---|
| `python -m pytest builder_platform/tests/` | **183 passed** |
| `python -m pytest builder_platform/tests/ claude_plugin/tests/` | **195 passed** |
| `cd Generated_Agents/<Agent> && python selftest.py` | per-agent gate, must exit 0 |

`ARCHITECTURE.md` still states 161 platform tests. The count is stale, not the claim.

## Write policy by directory

| Path | Role | May an implementer edit it? |
|---|---|---|
| `boilerplate/` engine — `graph.py`, `nodes.py`, `schemas.py`, `llm_client.py`, `rag_subgraph.py`, `compaction.py`, `filler.py` | copied verbatim into every generated agent | Yes, **but only here** — never in a generated copy. One fix, upstream, once. |
| `boilerplate/` domain surfaces — `config.py`, `tools.py`, `prompts.py`, `selftest.py` | the template the builder rewrites per agent | Yes; these are what generation overwrites downstream. |
| `boilerplate/agent_sandbox.py` | dev-only text REPL (`python agent_sandbox.py`) | Yes. Never wire it into the voice/SSE runtime; it is not client-facing and does not relax the SPOKEN rule. |
| `SKILL.md`, `skill_steps/step1_discovery.md` … `step4_build.md` | the builder's brain; slim core plus per-phase files each read exactly once | Deliberately only — byte budgets are pytest-enforced and it steers all generations. |
| `builder_platform/` | product code: `app.py`, `builder.py`, `builder_core.py`, `runtime.py`, `runtime_supervisor.py`, `vapi_adapter.py`, `vapi_control.py`, `sanitizer.py`, `tunnel.py`, `env_bootstrap.py`, `ask_protocol.py`, `builder_selfcheck.py` | Yes. `builder_core.py` is shared with the plugin — edit here, never fork. |
| `claude_plugin/` + `.claude-plugin/`, `commands/`, `hooks/` | the `/alta-builder:alta-build` surface: MCP server plus guard hook over the same core | Yes, the plugin glue. Never fork skill or engine content; it reads them from this repo root. |
| `references/` (`engine_theory/`, `playbook/`) | architecture theory the skill consults | Read-only. |
| `integrations/` (`google_calendar_booking.md`, `gmail_send_email.md`, `tavily_search.md`, `_TEMPLATE.md`) | validated copy-adapt recipes | Read-write catalog. Recipes are copy-adapted into an agent, never imported. |
| `Generated_Agents/BassanBrewerySDR/` | the checked-in demo agent DEMO.md Path A calls | Treat as a fixed artifact. Not a work product to improve. |

## Operating prerequisites

- **Python 3.11+** on `PATH`.
- **Claude Code** installed and on `PATH` — the builder drives Claude through it via the Agent SDK, in both auth modes.
- **Builder auth has two modes**: `ANTHROPIC_API_KEY` set bills that key (portable, for a shared deploy); left blank, it uses the machine's Claude subscription login (zero-config). Detected and logged at startup.
- **ngrok is required for a live call only** (`ngrok http 8000`), so Vapi can reach the machine. The whole build and selftest flow works without it.
- **One `.env` at the repo root** is loaded by `builder_platform/env_bootstrap.py` and inherited by every subprocess — builder, platform API, and voice runtime all read that single file. The run script seeds it from `.env.example`; the setup screen fills it in.
- **Vapi ships pre-provisioned** with restricted demo credentials in the reviewed submission, so a reviewer needs no Vapi account. Not needed to build or selftest.
- **All keys blank still works**: the entire pipeline runs in deterministic mock mode, which is what the selftest exercises.

## Traps already paid for

- **Vapi `firstMessage` of a single space** silently wedges the entire TTS queue. The fault is in Vapi's assistant config, not the stream. A platform test pins that a blank `firstMessage` is never shipped. Cost: a day.
- **Module-name collision.** Two generated agents cannot be imported into one process; the runtime is subprocess-per-agent for this reason. Regeneration restarts the process.
- **Blocking sync tool on the event loop.** A raw `smtplib`/`requests` call does not merely slow a turn — it freezes the loop, so the filler queue stalls *and* the dead-air ceiling can never fire. `tool_exec_node` offloads sync tools with `asyncio.to_thread`.
- **Both director gates must pass on an empty `CALL_ARC`**, which is what keeps the inbound boilerplate green while the engine stays under test.

## Uncommitted work in the tree

`boilerplate/nodes.py` carries +21 lines, uncommitted: `_speak_value()` plus its use in `_confirm_question()`. It detects a raw ISO-8601 slot value and renders it as a spoken phrase ("Tuesday, July 14 at 3 PM") before `confirm_template.format()` sees it, so a booking tool can keep machine-format datetimes without the confirm question speaking one.

It is an engine-file change in the right place (upstream in `boilerplate/`, not in a generated agent) and the suites are green with it, but **no regression test accompanies it**, which the project's own quality bar requires for a fix.
