# Alta Agent Studio — Setup

A platform where you chat with an **AI builder** that designs, generates, and
tests a **voice AI agent** in natural language. The generated agent qualifies
leads and books meetings over a real phone/web call (Vapi).

---

## Fastest path — one command

### Prerequisites

- **Python 3.11+** on your `PATH`.
- **[Claude Code](https://claude.com/claude-code)** installed and on your `PATH`
  — the AI builder drives Claude through it (via the Claude Agent SDK). Required
  for both auth modes below.

That's all you need to build and test agents. Vapi (voice) and an OpenAI key are
optional and covered below.

### Run

1. **Launch** — one command does venv + install + `.env` seed + start server:

   ```bash
   run.bat        # Windows
   ./run.sh       # macOS / Linux
   ```

2. **Open** <http://localhost:8100>. In the first-run setup screen, paste:
   - your **Anthropic API key** — *or* click to use this machine's existing
     Claude subscription/login (no key needed), and
   - *(optional)* an **OpenAI API key** so the generated agent has a live brain.
     Leave it blank to run the agent in deterministic **mock mode**.

   Keys are written only to the local `.env` — never committed. That is the
   entire setup; no file editing required.

3. **Build & call** — describe the agent you want, approve the design, wait for
   the selftest to pass (the orb lights up), then click **Call** and talk to it.
   Ask for a change in chat ("also ask about budget") and the next call reflects
   it.

> **Try it in under a minute:** a pre-built agent ships ready to call. Set the
> session id (top bar) to `BassanBrewerySDR` and click **Call** — no build
> needed. See [DEMO.md](DEMO.md) for the full reviewer script.

---

## What each key does

All configuration lives in a single `.env` at the repo root (the run script
seeds it from [.env.example](.env.example); the setup screen fills it in). Every
component — builder, builder_platform API, Vapi voice runtime — loads this one file via
`builder_platform/env_bootstrap.py`, and every subprocess inherits it.

| Variable | Needed for | Notes |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | the AI builder | **Two modes.** Set it → bills to that API key (portable, best for a shared deploy). Leave blank → uses this machine's Claude subscription/login (zero-config). Detected and logged at startup. |
| `OPENAI_API_KEY` (+ `OPENAI_BASE_URL`) | a **live** generated agent | The agent is **provider-agnostic** — any OpenAI-compatible `/v1` endpoint (OpenAI, Mistral, Groq, Together, OpenRouter, local vLLM/Ollama). **Blank = MOCK mode**, which is what the selftest runs. |
| `VAPI_*` (`SERVER_SECRET`, `PRIVATE_KEY`, `PUBLIC_KEY`, `ASSISTANT_ID`) | a real test **call** | Ship **pre-provisioned** with restricted demo credentials in the reviewed submission — reviewers need no Vapi account. Not needed to build or selftest. |

You can build and verify an agent with **all keys blank** — the whole pipeline
runs in deterministic mock mode.

---

## Verify

```bash
python -m pytest builder_platform/tests/   # builder_platform: builder policy, API, env, runtime, sanitizer
```

Every generated agent also ships its own `selftest.py`, which the builder runs
automatically after each generation/edit and gates the **Call** button on.

---

## Advanced / manual (no run script)

The run script is just a wrapper. To do it by hand, or to run headless:

```bash
# manual env + deps
python -m venv .venv && . .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                            # then edit keys directly, if not using the setup screen

# start the platform
cd builder_platform && python -m uvicorn app:app --port 8100

# prove the builder headless (Sonnet), no UI
python builder_selfcheck.py            # scripted design -> generate -> selftest PASS
python builder_selfcheck.py --smoke    # two cheap turns (auth + skill-load check)
```

Serving a generated agent to Vapi for a live call is normally automatic — the
**Call** button spawns the voice runtime and points the Vapi assistant at this
machine. To drive it manually:

```bash
cd builder_platform
AGENT_DIR=../Generated_Agents/BassanBrewerySDR uvicorn vapi_adapter:app --port 8000
ngrok http 8000    # set the https URL as your Vapi assistant's Custom LLM endpoint
```

---

## Architecture at a glance

```
 you ── chat ──▶ builder_platform/app.py ──▶ builder.py ── (Claude Agent SDK, Sonnet) ──▶ voice-agent-architect skill
                                                │                                          │ generates
                                                │                                          ▼
                                                │                              Generated_Agents/ or workspaces/<agent>/
                                                │                                          │ selftest gate
 caller ── phone ──▶ Vapi ── SSE ──▶ vapi_adapter.py ──▶ runtime.py ── drives ──▶ the generated agent's LangGraph
```

The builder can **only** edit a generated agent's domain files (`config.py`,
`tools.py`, `prompts.py`, selftest script); engine files are enforced read-only
by a permission hook. Full architecture rules in [CLAUDE.md](CLAUDE.md); the
diagram version is in [README.md](README.md).
