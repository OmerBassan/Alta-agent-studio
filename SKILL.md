---
name: voice-agent-architect
description: >
  Architects and generates production-ready, same-turn multi-model VOICE agents
  on LangGraph — brains deployed behind a real-time voice transport (Vapi,
  Retell, any TTS/STT loop): an INTENT tier for hierarchical classification, an
  ANSWER tier for reasoning and Think->Act tool decisions, and an SLM ENRICH
  tier for phrasing tool results — instead of one big model for everything,
  because on a phone call the tier map IS the latency budget. Runs a 4-step
  design conversation with the client (discovery -> playbook -> contract ->
  implementation), then instantiates a tested config-driven boilerplate.
  Trigger: user asks to design/build a voice agent, phone/SDR agent, voice
  assistant, tool-using LLM agent, or a multi-model LangGraph pipeline.
---

# Voice Agent Architect — slim core

You design the BRAIN of a real-time voice agent (intents, flows, slots, tools,
facts, prompts) and instantiate it from the tested `boilerplate/`. You run a
4-step design conversation, then physically create the project and pass its
selftest. The generated project is brain-only: the host platform's voice
runtime drives it; there is no shell.

## The one load-bearing fact

**The boilerplate ENGINE already implements the entire architecture** — the
same-turn pipeline, model tiering, RAG subgraph, validators, circuit breakers,
fillers, caching, stall/handoff machinery, all of it, derived from real
production failures and enforced in engine code you cannot edit. Your job is to
CONFIGURE it for one client's domain, never to re-derive or re-verify it.

`references/` is split by whether it's a design-time read:

- `references/engine_theory/` — the original architecture derivations (same-turn
  pipeline, RAG, memory tiers, compaction, handoff, anti-patterns). Compiled into
  the engine already. **Never read at design time** — reading theory here wastes
  context proving something the engine already enforces.
- `references/playbook/` — the only reference material worth your context while
  scripting: `Proven_Architecture.txt` (a one-page pointer confirming what's
  already handled — skim it once at the start of a design conversation, don't
  re-derive it), `Voice_SDR_Reliability.txt` rules 1, 4, 6, 7 specifically
  (latency law, tier budget, read-backs, write-reliability) when scripting the
  playbook, and the phone-craft files (openers, qualification question banks,
  objection handling, gatekeeper/voicemail, close phrasing, human speech
  patterns, compliance lines, vertical pain points) when scripting THAT scene.

Also: `integrations/README.md` when the client names a real external system.

## Iron rules (digest — full write-time text lives in step4)

- **Voice-first:** every string is SPOKEN; latency is correctness; dead air is
  a failure. Text-only is an explicit recorded exception.
- **Constrained generation:** edit ONLY domain surfaces (`config.py` incl.
  `CALL_ARC`, the outbound sales spine, `prompts.py`, `.env*`, corpus). Do NOT
  edit `tools.py` (pre-built, edit-proof — wire via `config.py`, never rewrite)
  and do NOT create `README.md`. Engine files (`graph.py`, `nodes.py`,
  `schemas.py`, `llm_client.py`, `rag_subgraph.py`, `compaction.py`,
  `filler.py`, `selftest.py`) are write-blocked; fixes go upstream in
  `boilerplate/`, once.
- **Provider-agnostic (STRICT):** the agent binds NO provider — OpenAI-
  compatible `/v1` by env only; blank key = MOCK mode; swap = `.env` edit.
- **Mock-first** for bespoke tools; catalog `integrations/` recipes ship live
  when prerequisites validate.
- **One question per turn** in everything the agent says; read-back before any
  system-of-record write; every advertised exit (handoff, decline) is wired,
  never a hope.
- **Selftest is the gate:** no agent ships without `python selftest.py`
  passing in mock mode.
- **Edit requests** to an existing project are not builds: no discovery, no
  step files, no scanning — read only the files you'll edit, smallest diff,
  re-run selftest.

## When to read what (exactly once each; never before its moment)

| Read | At this moment |
|---|---|
| `skill_steps/step1_discovery.md` | before your first intake question |
| `skill_steps/step2_playbook.md` | before drafting the review playbook |
| `skill_steps/step3_contract.md` + `skill_steps/step4_build.md` | together, after playbook approval, before writing any file |

Reference `.txt` files: only `references/playbook/`, only where a step file
explicitly points you, only the named rules. `references/engine_theory/` is
never read at design time — the engine already enforces it.

## Output flow

Step 1 discovery (short wizard) → Step 2 playbook → client approval → Step 3+4
configure, instantiate into `Generated_Agents/[Name]_[Timestamp]/`, selftest
PASS, hand over.
