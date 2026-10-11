# Same-Turn Multi-Model CLI Agent (boilerplate v3)

A config-driven English CLI agent skeleton. It answers **within the same turn**
a question is asked, using a **multi-model chain**: hierarchical intent
detection → LLM answer/reasoning (with an Agentic-RAG subgraph for retrieval
questions) → HITL operator gate on high-stakes flows → deterministic tool →
execution validator → SLM enrichment (or a deterministic bypass) → response
validator. Runs with **zero API keys** in deterministic mock mode, or live
against any OpenAI-compatible endpoint (Mistral, OpenAI, Ollama, …).

Ships with a demo domain ("Acme Outdoors") so it runs out of the box; the
`cli-agent-architect` skill customizes it per client by editing `config.py`,
`tools.py`, and `selftest.py` — the generic engine files rarely change.

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows;  source .venv/bin/activate elsewhere
pip install -r requirements.txt

python selftest.py              # mock-mode invariant checks (must PASS)
```

This project ships no CLIENT-facing shell — it is driven by the host
platform's voice/SSE runtime, which calls `graph.build_pipeline()` per turn
and resets the `graph.TURN_RESET` fields; `selftest.py` is the local scripted
harness. For a quick manual sanity-check with no voice infrastructure at all,
`python agent_sandbox.py` opens a text-chat REPL on the same pipeline. Live
mode: copy `.env.example` → `.env`, set `OPENAI_API_KEY` (+ base URL / tier
models). `SHOW_TRACE=1` prints per-turn routing.

## Architecture

Every user turn runs the whole chain to `END` in one graph invocation; the CLI
(the Shell) re-invokes per message. No node waits mid-turn — that is what makes
answers same-turn.

```
START
  → intent_detect              (INTENT tier)  hierarchical: category → intent + slots
                               tier-0 deterministic gates run FIRST (no model):
                                 pending yes/no confirmation, and the FAST
                                 ROUTER — a mid-slot-fill message that fills a
                                 missing slot skips the INTENT call → think
  → route by intent
       SYSTEM_INTENTS     system (no model)   → validator   (help / restart)
       chitchat                (ANSWER tier)  → validator
       RETRIEVAL_INTENTS  agentic_retrieval (RAG SUBGRAPH, private state)
                              → knowledge     → validator
       KNOWLEDGE_INTENTS  knowledge (ANSWER)  → validator
       goodbye            closing  (ANSWER)   → validator   (ends session)
       compound_request   planner (ANSWER, ONCE: emits plan_steps)
                              → plan_step (no model: bounded walk controller)
                              → think … tool … → plan_step → … done/paused
       any FLOWS intent   think (ANSWER: Think; entity resolvers + validators)
                              → need_info? ask → validator  (remembers pending flow)
                              → confirm?  yes/no question → validator
                              → hitl?     hitl_gate: interrupt() — operator approves
                              → ready?  tool_exec (Act, registry, breaker-guarded)
                                          → execution_validator (Layer 2.5)
                                               failure → failure → validator
                                               ok, enrich=False  → validator (SLM bypass)
                                               ok, enrich=True   → enrichment (ENRICH/SLM)
                                                                 → validator
  → validator (response validator: markdown/ANSI/blocked patterns)  → END
```

**Model tiers** (env vars; may all point at one model):

| Tier | Env var | Role |
|------|---------|------|
| Intent | `AGENT_INTENT_MODEL` | cheap/fast classification + slot extraction |
| Answer | `AGENT_ANSWER_MODEL` | direct answers **and** Think→Act reasoning |
| Enrich | `AGENT_ENRICH_MODEL` | SLM: phrase tool results warmly (only when a tool ran) |

**Architectural invariants** (enforced by `selftest.py`):
- `chitchat` is a first-class intent — small talk can never be forced into a
  premature goodbye; only explicit closings exit.
- Hierarchical routing: intents live in four macro categories (ANSWER / FLOW /
  COMPOUND / SYSTEM); SYSTEM intents (help, restart) are deterministic, and
  restart is the one explicit abandonment that clears pending state, the
  session cache, and any plan.
- Tool-backed flows use Think→Act: the reasoning tier emits a **cold structured
  payload** (`{"tool", "args"}`); only `tools.TOOL_REGISTRY` executes
  side-effects. One tool per flow — a single Think→Act hop; loops are the
  bounded RAG subgraph and the deterministic plan-step walk (below).
- Plan-and-Execute: a compound utterance ("look up order X and then refund
  it") routes to the `planner`, which calls the ANSWER model **once** and is
  clamped in code (unknown actions dropped, truncated to `MAX_PLAN_STEPS`).
  The `plan_step` controller then walks the steps deterministically through
  the ordinary think→act machinery — pausing at slot asks / confirm gates /
  HITL interrupts and resuming next turn; a failed step, decline, or denial
  aborts the remainder while still reporting what completed.
- Functional session cache: after a successful tool run, `Flow.cache_keys`
  fields are merged into `session_facts` (code-level whitelist merge, no
  model) and injected into prompts as a `KNOWN FACTS` line — so identifiers
  are never re-asked, and a later plan step auto-fills its slots from an
  earlier step's output.
- Multi-turn slot-fill: a missing slot sets `pending_intent`/`pending_slots`
  (carried by the checkpointer); a continuation guard keeps bare slot answers
  ("downtown at 3pm") inside the pending flow. Entity resolvers ground
  referential values ("any branch") against the catalog; validators normalize
  units/bounds — nothing unresolved reaches a tool.
- Fast router (tier-0 gate, `FAST_ROUTER_ENABLED`): mid slot-fill, a message
  that deterministically fills a missing slot (extractor hit surviving its
  resolver/validator, no other-intent keyword, no negation) bypasses the
  INTENT-tier model entirely and routes straight to Think — the model tiering
  is unchanged; every doubt falls through to the normal INTENT call.
  `SHOW_TRACE=1` shows the bypass as `fast=True`.
- Interrupt archive (depth 1, `paused_flow`): a second tool flow interrupting
  a pending one PARKS the pending flow (intent + collected slots) instead of
  clobbering it. The interrupting flow's completion appends a ONE-SHOT resume
  offer (`PAUSED_RESUME_TEXT`); a bare slot answer or re-entry by name
  restores the parked flow without re-asking collected slots. Never a stack —
  the newest interruption wins; restart/goodbye clear the archive.
- Retrieval questions run the Agentic-RAG subgraph (`rag_subgraph.py`): a
  private-state retrieve→grade→rewrite loop returning exactly one key
  (`retrieved_context`); empty retrieval yields an honest "I don't have that."
- The Think prompt gets the **current date injected** so "tomorrow" resolves
  correctly.
- Every live model call degrades to its deterministic mock fallback on error —
  a turn never crashes the session. Failed tools route through the execution
  validator to a graceful failure reply that keeps the flow retryable.
- Safety rails: a per-turn tool budget (`MAX_TOOL_CALLS_PER_TURN`), a plan
  ceiling (`MAX_PLAN_STEPS`, keep it ≤ the tool budget), and
  flows declaring the `liability` property suspend via `interrupt()` for an
  **operator approval** before executing; the operator's
  `Command(resume={"approved": ..., "offer_id": ...})` must name the offer the
  interrupt showed. No operator console ships, and approvals are in-process:
  they do not survive a restart (see `authz.py`).
- `Flow(enrich=False)` bypasses the SLM: the execution validator phrases the
  result deterministically (summary + hint) — the low-latency fast path.
- `validator` (response validator) is the only door to the user: strips
  markdown/ANSI and applies `config.BLOCKED_PATTERNS` (demo: invented prices).

## Files

| File | Role | Edit per client? |
|------|------|------------------|
| `config.py` | domain: intents (hierarchical), flows (confirm/hitl/enrich/cache_keys), facts, RAG corpus + retriever, entity resolvers, safety constants, mock heuristics, guardrails | **YES — main surface** |
| `tools.py` | deterministic tool registry (mock-first) + MCP adapter | **YES** |
| `selftest.py` | scripted invariant checks | **YES (the script)** |
| `prompts.py` | prompt builders (domain flows in via config) | tone only |
| `graph.py` / `nodes.py` / `schemas.py` | the engine: state machine + nodes | rarely |
| `rag_subgraph.py` | Agentic-RAG loop (private state, bounded) | rarely |
| `llm_client.py` | multi-tier OpenAI-compatible client + JSON-mode fallback | no |
| `filler.py` | filler channel: canned pre-answer acknowledgments over a frontend-agnostic sink | no (bank lives in config) |
| `agent_sandbox.py` | text-chat REPL on the same pipeline — dev-only, never wired into the voice/SSE runtime | no |

## Swapping in real tools

Each function in `tools.py` returns a structured dict with a `"summary"`
sentence. Replace the body with a real API/DB call, keep the signature and the
`summary` contract — nothing else in the graph changes. Gate live side-effects
behind an env flag if you need a safe demo mode.

To use tools from an MCP server instead, connect an `mcp.ClientSession` and
`await tools.register_mcp_tools(session)` at startup — the wrapped tools land
in the same registry with the same contract, and `config.FLOWS` references
them by name exactly like local tools.

## Fillers & adding a voice frontend

While a slow tool runs, the agent emits a short canned acknowledgment ("Let me
pull up that order…") from the `config.FILLERS_BY_TOOL` bank — display-only
(never in model context), debounced past `FILLER_DELAY_MS`, and off-switchable
to the legacy dot-spinner via `FILLER_ENABLED=0`. These cross a frontend-agnostic
sink (`filler.py`), which is the seam a voice frontend plugs into: a Vapi/Retell
custom-LLM SSE adapter sets its own queue as the sink and yields each filler (and
the final reply) as OpenAI-format chunks — the graph, nodes, and config are
unchanged. Set `FILLER_DELAY_MS=0` for voice so the gap is always covered. See
`references/Filler_Channel.txt`.

## Swapping in a real retriever

`config.RETRIEVER` is a keyword-overlap mock over `config.DOCS`. Replace the
function body with a LOCAL vector index query — FAISS or SQLite-vss
(in-process, Python-native, no server, no credentials) — that returns the same
`[{"id", "title", "text", "score"}]` shape; the RAG subgraph and the knowledge
prompt are unchanged. Reach for a hosted vector DB only when the corpus or
team genuinely demands it (`references/Agentic_RAG_Explained.txt` rule 7).
The loop runs under two shipped ceilings: `RAG_MAX_ITERATIONS=1` and a
`RAG_TIMEOUT_SECONDS=2.0` wall clock (timeout -> one deterministic
single-hop retrieve, never a retry).
