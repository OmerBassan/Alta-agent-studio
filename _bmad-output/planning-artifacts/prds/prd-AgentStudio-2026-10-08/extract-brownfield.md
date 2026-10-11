# Brownfield extract — for the forward-looking AgentStudio PRD

**Extracted:** 2026-10-08 · **Repo:** `C:\Users\Omer Bassan\Desktop\Projects\AgentStudio` (branch `main`, HEAD `a0a0ca8`)

**Framing.** The shipped system is **Alta Agent Studio** — a chat-driven builder that generates *voice* AI SDR agents on a fixed LangGraph pipeline, driven by Vapi. The PRD being written targets a **channel-independent, business-specific AI Agent platform** whose settled execution model is *"the Agent decides what to do; the Core constrains, validates, authorizes, executes, observes, persists."* That model is **not** the model of the shipped system: the shipped system's central architectural thesis is the opposite — *the Core decides and the model only phrases*. This extract therefore separates genuinely portable Core machinery from the voice/determinism thesis that must not be carried over by inertia.

Sources read in full: `_bmad-output/specs/spec-alta-agent-studio/SPEC.md`, `.../brownfield.md`, `CLAUDE.md`, `ARCHITECTURE.md`. Codebase surveyed by listing + targeted grep (`builder_platform/`, `boilerplate/`, `claude_plugin/`, `skill_steps/`, `SKILL.md`, `integrations/`, `references/`). Lessons cross-read from `~/.claude/reasoning-log/` (13 Alta-relevant entries).

---

## 1. WHAT ALREADY EXISTS

### 1.1 Headline evidence

| Evidence | Value |
|---|---|
| `python -m pytest builder_platform/tests/` | **183 tests** (counted by test-function tally across 13 files; matches `brownfield.md`) |
| + `claude_plugin/tests/` | **195 tests** (12 plugin tests: 7 guard-hook, 5 MCP-server) |
| Per-agent gate | `python selftest.py` in forced MOCK mode, must exit 0; ~7s on fresh boilerplate, 120s wrapper timeout, max 2 runs per session |
| Real-world proof | A live Vapi phone call, end-to-end, 2026-07-15 (cited in `CLAUDE.md` and SPEC) |
| Code volume | ~8.7k lines of Python across platform + boilerplate + plugin; `boilerplate/nodes.py` alone is 1,776 lines / 92 KB, `boilerplate/config.py` 905 lines / 50 KB |
| Checked-in demo artifact | `Generated_Agents/BassanBrewerySDR/` (frozen; DEMO.md Path A) |

### 1.2 The builder (platform) layer — `builder_platform/`

| Component | Lines | What it does | Evidence |
|---|---|---|---|
| `builder_core.py` | 276 | **The deterministic shared engine.** Pure path/policy: `write_denial` / `read_denial` (allowlist + engine-file protection), `sanitize_project_name`, `discover_project` / `locate_active_project` / `find_enclosing_project`, `instantiate_project` (wholesale `copytree`), `run_selftest_gate` (subprocess, forced blank keys = MOCK, timeout, output tail), and a **surface-hash PASS marker** (`_SELFTEST_SURFACE` = config/tools/prompts/selftest → sha256 → `.selftest_passed.json`) so a restart-reattached session trusts a prior pass. Framework-agnostic by construction: knows nothing of SDK/FastAPI/MCP. | `test_builder_core.py` (10 tests) + exercised by both front doors |
| `builder.py` | 494 | Headless **Claude Agent SDK** session running the `voice-agent-architect` skill. `SKILL.md` is *injected into the system prompt* (deliberately NOT skill auto-discovery — avoids a duplicated-bundle drift trap). Privileged ops exposed as SDK-MCP tools. Per-session workspace isolation, turn ceiling. | `test_builder.py` (13) |
| `app.py` | 844 | FastAPI platform API: `/api/chat` (SSE stream of builder turn events), `/api/call`, `/api/warm`, `/api/agent` (+ `/env`, `/knowledge` CRUD, `/download` zip), `/api/auth/{status,setup,logout}`, `/health`, session delete. Call endpoint **refuses unless selftest PASSed**. | `test_app.py` (25) |
| `runtime.py` | 437 | Loads ONE generated agent via `sys.path` + `build_pipeline(MemorySaver)`; normalizes a Vapi custom-LLM POST into a `VapiTurn` (payload shape confirmed from `vapi_raw_capture.jsonl`, not docs); `call.id → thread_id`; filler→SSE `asyncio.Queue` with try/finally sentinel + wall-clock apology; `turn_fingerprint` dedupe for corrected-transcript re-sends; lead-fact injection from 4 candidate Vapi metadata paths; end-of-call record flush. | `test_runtime.py` (17), `test_call_path.py` (27) |
| `vapi_adapter.py` | 201 | OpenAI-compatible `POST /v1/chat/completions` with strict SSE framing (`data: …\n\n`, `finish_reason:"stop"`, `[DONE]`), `x-vapi-secret` auth, `BRAIN_MODE=live|skeleton`, brain preloaded at startup (lazy first load cost ~4s = dead air). `usage` hardcoded to zeros. | `test_vapi_adapter.py` (5) |
| `vapi_control.py` | 212 | Vapi REST control plane: point the assistant's `custom-llm` model `url` at this machine's tunnel + a preflight that blocks a silently-dead call. Ground truth probed against the live account, including "a custom-llm model cannot carry `model.secret`". | covered in `test_app.py` / `test_call_path.py` |
| `runtime_supervisor.py` | 201 | Subprocess-per-agent supervisor; single active agent, one port, start/stop/status, death detection. | `test_runtime.py` |
| `tunnel.py` | 246 | Public-URL discovery: `PUBLIC_URL` override → adopt a running ngrok agent API tunnel → fail loudly. Does not manage the ngrok process. | — |
| `sanitizer.py` | 79 | Buffered, stateful pre-TTS scrubber (markdown/bullets/URLs/newlines), releases only to the last whitespace boundary so split tokens can't dodge the regex. | `test_sanitizer.py` (7) |
| `env_bootstrap.py` | 89 | Single credential ingress: one repo-root `.env` → `os.environ`, inherited by every subprocess. Documented precedence. | `test_env_bootstrap.py` (6) |
| `ask_protocol.py` | 73 | Python mirror of the `alta:ask` fenced-JSON wizard-card protocol in `static/index.html`; malformed → degrade to ordinary chat. | `test_ask_protocol.py` (10) |
| `storage/` | ~250 | Zero-dependency SQLite (`schema.sql`: `sessions`, `built_agents` with `selftest_status`), `db_manager.py`, WAL mode. | `test_storage.py` (9) |
| `static/index.html` | 78 KB | The entire web UI, single file: builder chat, wizard cards, status orb, test-call button, env/knowledge editors. | exercised via `test_app.py` |
| `builder_selfcheck.py` | 187 | Standalone real-LLM proof of the builder with no UI (`--smoke` and full scripted design conversation). | — |
| `test_efficiency_round.py` / `test_engine_invariants.py` | — | 20 + 12 tests pinning skill-file byte budgets, turn ceilings, selftest-run caps, blank-`firstMessage` prohibition, engine invariants. | — |

### 1.3 The generated-agent engine — `boilerplate/`

A **fixed 15-node LangGraph pipeline** (`graph.py`, 250 lines) copied verbatim per agent:
`intent_detect → [route] → {system | agentic_retrieval→knowledge | chitchat | closing | planner→plan_step | think → hitl_gate → tool_exec → execution_validator → failure|enrichment|bypass} → validator → END`.

| Engine file | Lines | Capability |
|---|---|---|
| `nodes.py` | 1,776 | All node bodies + ~15 deterministic in-node gates: fast router (deterministic slot fill skips a model call), confirmation gates, paused-flow depth-1 archive, plan controller, **circuit breaker** (`MAX_TOOL_CALLS_PER_TURN`), `asyncio.to_thread` sync-tool offload, **execution_validator (Layer 2.5)**, enrichment templater, `_director` / `_objection_gate` / `_tiedown` / stall detector / `_update_summary` / `build_call_record`, exit filter (`validator_node`) |
| `schemas.py` | 278 | Five Pydantic contracts only (anti-sprawl rule): `IntentResult`, `ThinkDecision`, `PlanStep`/`PlanResult`, `EnrichVerdict`, plus the `AgentState` TypedDict with `add_messages` reducer and a documented `TURN_RESET` set |
| `llm_client.py` | 166 | Three env-bound model roles (INTENT/ANSWER/ENRICH), OpenAI-compatible `/v1` only, 30s hard timeout, blank key ⇒ MOCK mode | `test_llm_client_timeout.py` (2) |
| `rag_subgraph.py` | 164 | Agentic RAG as a *compiled subgraph with a private state namespace*; retrieve→grade→rewrite→finalize, bounded by `RAG_MAX_ITERATIONS`; parent copies back exactly one key |
| `compaction.py` | 154 | Deterministic, zero-model Compress-Cache-Retrieve over large tool results; errors/rare-status/anchors never dropped; never raises |
| `filler.py` | 90 | Filler-bank selection for latency cover |
| `selftest.py` | 640 | **Domain-agnostic, config-derived gate**: engine preflights (voice, objection, persona, call-arc, tie-down, context-budget, summary) + a config-derived smoke walk asserting *structure*, never reply strings; adapts-or-skips on shapes a domain lacks |
| `config.py` (domain surface) | 905 | ~90 declarative knobs: `FLOWS`/`Flow`, `Stage`/`CALL_ARC`, `INTENT_*`, `SLOT_EXTRACTORS`, `ENTITY_RESOLVERS`, `SUMMARY_TEMPLATE`, filler banks, `BLOCKED_PATTERNS`, `MAX_REPLY_WORDS`, every budget as an env-overridable constant |
| `tools.py`, `prompts.py`, `agent_sandbox.py` | 198/191/78 | Mock-first tool registry with `summary`-bearing dict contract; prompt builders; dev-only text REPL |

### 1.4 The generation paradigm — `SKILL.md`, `skill_steps/`, `integrations/`, `references/`

- `SKILL.md` (89 lines, slim core) + four **read-exactly-once** phase files: `step1_discovery` → `step2_playbook` → `step3_contract` + `step4_build` (token-diet split of a former monolith; **byte budgets are pytest-enforced**).
- `integrations/` — the one read-**write** catalog: 3 validated copy-adapt recipes (`google_calendar_booking`, `gmail_send_email`, `tavily_search`) + `_TEMPLATE.md`, with an explicit **Detect → Validate prerequisites → Implement live** lifecycle and a "the mock is not the product" rule.
- `references/` — read-only theory, split into `engine_theory/` (11 files, explicitly *never* read at design time) and `playbook/` (10 phone-craft files, read selectively per scene).

### 1.5 The second front door — `claude_plugin/` + root `.claude-plugin/`, `commands/`, `hooks/`

`/alta-builder:alta-build` — a bundled stdio **MCP server** (`mcp_server.py`, 102 lines, exposes exactly `instantiate_boilerplate` and `run_selftest`, both straight calls into `builder_core`) plus a **PreToolUse guard hook** (`guard_engine_files.py`) enforcing the same write policy in a native terminal session. Declared **inline in `plugin.json`**; every tool takes an explicit `workspace_dir` because a stdio server's cwd is fixed at spawn. 12 tests. **This is the proof that one deterministic core can serve two completely different front doors with zero forked logic** — the single most transferable structural result in the repo.

---

## 2. WHAT IS REUSABLE FOR THE NEW PLATFORM

Legend: **(a) direct** — reusable as-is or near-as-is · **(b) rebuild** — the concept transfers, the code is channel- or thesis-coupled · **(c) not reusable** — voice/Vapi-specific.

### 2.1 Direct reuse (a)

| Asset | Verdict | One-line justification |
|---|---|---|
| `builder_core.py` | **(a) direct** | Pure path/policy with zero channel, SDK or voice coupling — the write/read allowlist, instantiate, selftest-gate-as-subprocess and surface-hash PASS marker are exactly the "Core constrains + authorizes + persists" primitives the new model needs. |
| The **selftest-gate-as-ship-gate** mechanism | **(a) direct** | "Nothing unproven is reachable" is channel-independent; only the *contents* of the checks are voice-specific. |
| Domain-agnostic, **config-derived** test design | **(a) direct** | The 2026-07-20 lesson (a domain-coupled test forces the builder into a rewrite loop) is a hard constraint on any generative platform, independent of channel. |
| `env_bootstrap.py` + one-`.env` credential ingress | **(a) direct** | Single documented-precedence ingress inherited by subprocesses; no voice coupling. |
| Provider-agnostic `llm_client.py` contract (3 env-bound roles, `/v1` only, blank key ⇒ MOCK) | **(a) direct** | Vendor-neutrality by env is a product property, not a channel property; MOCK mode is what makes a credential-free CI gate possible at all. |
| `compaction.py` (CCR over tool results) | **(a) direct** | Deterministic, zero-model, never-raises, error-exempt — a Core observability/cost primitive usable under any execution model. |
| `execution_validator_node` **concept** (Layer 2.5: deterministic post-execution verdict) | **(a) direct** | Maps one-to-one onto "Core validates"; it is already decoupled from the model that chose the action. |
| Circuit breaker (`MAX_TOOL_CALLS_PER_TURN`) + bounded-loop discipline | **(a) direct** | "Core constrains" needs exactly this, and it becomes *more* important once an agent, not a graph, chooses the next action. |
| `hitl_gate_node` / LangGraph `interrupt()` + `Command(resume=…)` pattern | **(a) direct** | "Core authorizes" in working form; already shell-agnostic by design (the Shell surfaces the interrupt). |
| `asyncio.to_thread` sync-tool offload + per-client `timeout=` | **(a) direct** | A correctness rule about single-threaded async, not about voice — see §3.4. |
| `EnrichVerdict` pattern (model returns a *structured verdict*, a deterministic templater writes the text, every fact verified against source) | **(a) direct** | The cleanest "Core validates the Agent's output before it reaches a human" primitive in the repo, and provably necessary (free rephrasing reopened anti-pattern #9). |
| `integrations/` catalog + Detect→Validate→Implement-live lifecycle | **(a) direct** | A tool/connector catalog with a real prerequisites gate is exactly what a business-specific agent platform needs; recipes are prose, so they port. |
| Dual front door: shared core + SDK-MCP tools + plugin MCP server + PreToolUse guard hook | **(a) direct** | Proven pattern for "one Core, many surfaces"; the guard hook is a working model of Core-enforced policy over an agent that can write files. |
| `storage/` SQLite layer | **(a) direct**, but thin | Only two tables (sessions, built_agents); correct and tested, but a near-trivial starting point — reuse the shape, expect to outgrow it. |
| `ask_protocol.py` (structured fenced-JSON cards, malformed ⇒ graceful degrade) | **(a) direct** | A channel-independent way to get structured interaction out of a chat stream without parsing prose. |

### 2.2 Reusable in concept, needs rebuilding (b)

| Asset | Verdict | One-line justification |
|---|---|---|
| **`graph.py` — the fixed 15-node pipeline** | **(b) rebuild, and the concept itself is the mismatch** | See §2.4: the code is excellent and the shape is wrong for "Agent decides"; what survives is the *inventory of guarantees*, not the graph. |
| `CALL_ARC` / `Stage` / `_director` (deterministic agenda cursor) | **(b) rebuild** | The idea "a goal needs a stored cursor, not prompt tone" is a genuine insight worth carrying; a hardcoded sales arc advanced by zero-model predicates is the Core deciding what to do next, which the new model assigns to the Agent. |
| `AgentState` TypedDict + `TURN_RESET` turn contract | **(b) rebuild** | The *discipline* (every field has writer/reader/lifecycle; transient vs. durable is explicit; reducers declared) is exactly right; the field set is voice-turn- and flow-specific. |
| `Flow` / slots / `SLOT_EXTRACTORS` / `ENTITY_RESOLVERS` | **(b) rebuild** | Typed argument collection with deterministic resolvers before execution is a Core validation primitive; the *flow* framing presumes a fixed pipeline, and extractors are known to leak across flows (see §3.7). |
| `rag_subgraph.py` | **(b) rebuild** | Encapsulated-loop-with-private-state is the right pattern and the retriever is config-injected, but the corpus model is a tiny in-process keyword retriever — not a business knowledge base. |
| `config.py` as the single declarative surface | **(b) rebuild** | 905 lines / 90 knobs of "configure the engine" is the right instinct (config over code) but is the inverse of an agent-decides platform, where configuration describes *policy and authority*, not routing. |
| `SKILL.md` + `skill_steps/` + the 4-phase design conversation | **(b) rebuild** | The *mechanics* (slim core, read-exactly-once phase files, pytest-enforced byte budgets, injected-not-discovered skill) transfer verbatim as a technique; every word of content is voice-SDR domain. |
| **Wholesale isolation** (full copy of a template, only domain surfaces editable, engine files write-blocked) | **(b) rebuild** | The paradigm is the single best product decision in the repo and should be kept; what gets copied is a different artifact, so the `ENGINE_FILES` set and surface list are all new. |
| `builder.py` headless-SDK builder | **(b) rebuild** | Session/workspace/turn-ceiling machinery and the prompt-injection decision port; the system prompt, tool set and flow are voice-build-specific. |
| `app.py` platform API + `static/index.html` | **(b) rebuild** | Endpoint skeleton (chat SSE, agent status, env/knowledge, download, health) is a reasonable template; a 78 KB single-file UI and a call button are not a product UI for a channel-independent platform. |
| `runtime_supervisor.py` (subprocess-per-agent) | **(b) rebuild** | The *isolation reason* is permanent (§3.3) but "one agent, one port, single active" is explicitly acknowledged demo debt and will not survive multi-agent/multi-channel. |
| `selftest.py` preflight *contents* | **(b) rebuild** | Two-layer design (engine preflights + config-derived smoke walk asserting structure) ports directly; voice/objection/persona/call-arc/tie-down checks do not. |
| `build_call_record` / `SUMMARY_TEMPLATE` (zero-model structured record harvested from work already done, prose synthesized off the hot path) | **(b) rebuild** | Excellent latency-safe-observability principle; the record's schema is a sales call. |
| `builder_selfcheck.py` | **(b) rebuild** | A scripted, real-LLM, UI-free proof of the builder is worth keeping as a category of test; the script is a voice design conversation. |

### 2.3 Voice-specific, NOT reusable (c)

| Asset | Verdict | One-line justification |
|---|---|---|
| `vapi_adapter.py` | **(c)** | Vapi custom-LLM SSE contract and `x-vapi-secret` auth — one transport, discarded with it. |
| `vapi_control.py` | **(c)** | Vapi REST assistant patching; pure vendor control plane. |
| `runtime.py` Vapi turn parsing (`VapiTurn`, lead-fact paths, barge-in dedupe) | **(c)** | Entirely shaped by one vendor's payload quirks — though the *dedupe-against-corrected-resends* idea is a transferable idempotency lesson (§3.6). |
| `filler.py` + `FILLER_*` banks + `FILLER_DELAY_MS` + pre-think filler | **(c)** | Dead-air cover exists only because a phone line cannot be silent; a text/email/ticket channel has no analogue. |
| `sanitizer.py` | **(c)** | Pre-TTS markdown/URL stripping is anti-value on a text channel, where markdown and links are the deliverable. |
| `MAX_REPLY_WORDS = 20`, SPOKEN-string rule, `OPENER`, `voice_budget_preflight` | **(c)** | The ≤20-word/no-markdown/one-question-per-turn contract is the voice channel's constraint and will actively damage other channels. |
| `_tiedown`, `_objection_gate`, `OBJECTION_*`, `TIEDOWNS`, `CLOSING_QUESTIONS` | **(c)** | Phone-sales micro-tactics; also derived from the "turn-taking, one question per turn" invariant that other channels don't have. |
| `tunnel.py` / ngrok dependency | **(c)** | Exists only so a cloud telephony vendor can reach a laptop. |
| `references/playbook/` (10 files) | **(c)** | Cold-call openers, gatekeeper scripts, voicemail, compliance lines — phone craft. |
| `references/engine_theory/` (11 files) | **(c)** as reference material | Derivations of the voice same-turn pipeline; retained value is historical, and the repo's own rule already says never read them at design time. |
| `agent_sandbox.py` | **(c)** | A dev REPL whose only purpose is to sanity-check a voice build without Vapi. |
| `Generated_Agents/BassanBrewerySDR/` | **(c)** | A frozen demo artifact, explicitly not a work product. |

### 2.4 The structural mismatch, stated plainly

**`boilerplate/graph.py` + `nodes.py` is a fixed execution graph, and that is a conceptual mismatch with the new product's settled model — even though the code is good.**

The old system's architecture document opens by *rejecting* "let the model decide the next move each turn" and quantifies the win: the director costs **0 tokens, 0 calls, ~0 ms**, versus +1 round-trip and +200–800 ms for an LLM-routed graph. Every subsequent decision compounds that thesis: routing is a `route_by_intent` lookup over config tuples; the agenda is a monotonic cursor over `CALL_ARC`; the ENRICH tier is forbidden from writing prose; the planner is called **exactly once** and execution is then fully deterministic; the parent graph is **loop-free** by invariant, with two sanctioned exceptions. The locus of decision is the Core, and the model is a constrained phrasing and classification device.

The new model inverts the locus: the Agent decides; the Core constrains, validates, authorizes, executes, observes, persists. Consequences for the PRD:

1. **Do not port the graph.** `intent_detect → route → think → tool_exec` is a hand-rolled, config-driven agent loop with the agency removed. Under the new model the agent loop is the Agent's, and the graph's 15 nodes mostly dissolve.
2. **Port the guarantees, not the topology.** What `graph.py`/`nodes.py` actually *earned* is an inventory of Core guarantees that remain mandatory under any execution model: a bounded tool budget, a deterministic post-execution validator, a typed-tool-result contract, a human-authorization interrupt, a repetition/stall detector with a wired handoff, a degraded-result path distinguishable from success, an output filter before anything reaches a human, and durable-state/turn-contract discipline. Each is a Core service in the new architecture, not a node.
3. **Expect the latency arithmetic to flip.** ARCHITECTURE.md's whole case against agent-decided routing is a *voice* latency budget. On text, email, ticketing or async channels, a +200–800 ms round trip is free. Carrying the zero-model determinism thesis into a channel-independent product would be inheriting a constraint whose justification has been removed — but note the inverse too: any synchronous-chat channel re-imports a (weaker) version of it.
4. **The one piece of the director worth keeping is the *insight*, not the mechanism.** From the 2026-07-22 entry: a goal an agent must *advance* needs a first-class representation in state; prose and prompt tone cannot guarantee it. Under "Agent decides" that becomes *the Core persists and exposes goal/progress state the Agent reads and updates*, rather than a cursor the Core advances behind the Agent's back.

---

## 3. BROWNFIELD CONSTRAINTS AND HARD-WON LESSONS

Carry these forward as **knowledge**. Each cost real debugging time and is logged in `~/.claude/reasoning-log/`.

### 3.1 A named optimization is a hypothesis about the codebase, not a spec
`2026-07-23_context-latency-asks-must-be-audited-against-engine-shape.md`: three of four textbook "context/latency" techniques (strategic placement, lazy tool schemas, JIT knowledge) had **no target** in this engine or rested on false premises — `llm_client` has no `tools=` parameter at all, and RAG was already retrieval-gated. The one real lever was a hardcoded 20-turn history window. Reinforced by `2026-07-29`: an *asked-for trigger* can be structurally impossible ("agent speaks too long" cannot occur under enforced turn-taking). **PRD rule: before committing to any named technique, grep for the mechanism it targets and confirm it exists on the hot path.** This is already repo law (`CLAUDE.md`, SPEC §Why).

### 3.2 Never add a model call to the reply path in the name of latency
A per-turn LLM summarization "compaction" was rejected for exactly this reason. The latency-safe alternative generalizes: **harvest the structured output the system already produces for free, and push prose synthesis off the hot path** (`_update_summary` zero-model per turn; `build_call_record` once at call end). Carry the principle; retire the ≤20-word voice version of it.

### 3.3 Module-name collision forces process isolation — the agent-isolation constraint is permanent
Every generated agent defines top-level `config`, `graph`, `tools`. Importing two into one process silently serves the **first** agent's brain forever. Hence subprocess-per-agent, and regeneration *restarts* rather than re-imports. Any new platform that hosts multiple generated agents must solve isolation at the process/container level from day one — and must do better than the shipped single-active-agent, single-port arrangement, which is acknowledged demo debt.

### 3.4 On a single-threaded event loop, a blocking sync call voids every `await`-based timeout
`2026-07-22_sync-tool-on-event-loop-defeats-dead-air-ceiling.md` (W2, displaced fault): a `smtplib.SMTP_SSL` with no `timeout=` froze the loop, so the 45s dead-air ceiling **could never fire**. Fix: `asyncio.to_thread` for sync callables plus an explicit `timeout=` on every network client. **Universal rule for a tool-executing Core: user-supplied/integration tool code must run off the loop thread, and every external client needs its own timeout — "we have a global timeout" is not a defense.**

### 3.5 A graceful fallback that looks like success is the most expensive bug class
`2026-07-15_empty-env-var-breaks-openai-sdk.md` (W5, docs lied): the `openai` SDK re-reads `OPENAI_BASE_URL` from the environment even when passed `base_url=None`, so `OPENAI_BASE_URL=` (empty-but-set) in `.env` produced a protocol-less URL and **every LLM tier failed** — while the graph's mock fallback served plausible deterministic text under a `LIVE (OpenAI)` banner. Verification had checked the *mode label*, not a completion. Paired with `2026-07-13_context-starved-microprompts-behind-honest-decline.md`, where an "honest decline" fabrication guard masked three stacked RAG faults. **PRD rule: every degraded path must be distinguishable from success by the caller, not just in a log line — and health checks must prove a real request, never a config label.**

### 3.6 Transport ground truth comes from captured traffic, not vendor docs
The two most expensive traps were both vendor behavior absent from the docs: a Vapi assistant `firstMessage` of **a single space silently wedges the entire TTS queue** (cost: a day; now pinned by a platform test), and Vapi **resends/corrects the full transcript** on the same `call.id`, so a runtime must be **idempotent per logical turn** (`turn_fingerprint` dedupe) or it double-processes. Also: a custom-llm model cannot carry `model.secret`; auth arrives in a header instead. **Generalize: for every channel adapter, capture real traffic, pin the quirk with a test, and make turn handling idempotent — any channel with retries, edits or webhooks re-imports this problem.**

### 3.7 Config-driven generation fails in two specific ways: coupled gates and unscoped globals
- `2026-07-20_domain-coupled-selftest-forces-builder-rewrite-loop.md` (W2/W3): a demo-coupled `selftest.py` forced the builder to rewrite 36 turns of assertions per domain; a single wrong assertion looped the build to ~10 minutes, and the prior reaction had been to **stub the gate to always-pass** — the gate was disabled to stop the pain. Fix: make the gate domain-agnostic, config-derived, and *write-blocked*; demote per-domain authoring checks to warnings; **adapt-or-skip** on shapes a domain lacks.
- `2026-09-07_call-arc-multi-slot-flow-mock-mode-pitfalls.md` (W1): `SLOT_EXTRACTORS` are applied **unscoped across every flow**, so one slot's extractor silently answered unrelated slots; and a one-shot-per-stage director move made a stall check mathematically unsatisfiable.
**PRD rule: any shared declarative registry in a generated artifact must be scoped to its owner, and the ship gate must never be authored by the generator it gates.**

### 3.8 Deterministic appenders and detectors have ordering constraints that tests won't find
`2026-07-29`: a rotating tie-down bank appended *before* the stall fingerprint gave byte-identical replies a different hash every turn, **silently disabling the stall detector** — the escalation path of last resort still ran and still reported healthy. Found by reading node ordering, not by a failing test; the fix was verified non-vacuous by reintroducing the bug. Compare `2026-10-06_new-assertions-pass-without-exercising-their-property.md`. **PRD rule: any Core safety detector (repetition, loop, cost, abuse) must be positioned before mutation of what it measures, and every new guard must be proven non-vacuous by reintroducing the bug it guards.**

### 3.9 Provider-agnosticism is enforceable, and worth enforcing
The shipped rule is STRICT and holds in code: no vendor SDK import, no hardcoded base URL, no branching on provider, no vendor-specific key; model names are env defaults, never literals in logic; blank key ⇒ MOCK; swapping providers is an `.env` edit with zero code change. This bought two concrete things worth preserving: a **credential-free CI gate** (MOCK mode is what the selftest runs) and genuine artifact portability. `boilerplate/llm_client.py` also records the complementary trap: **a stronger model increases fidelity to what the prompts say, never to what is true** — escalating a tier to fix bad behavior is a category error when the desired behavior isn't scripted anywhere.

### 3.10 Wholesale isolation (Lovable/v0 paradigm) with code-enforced write policy
A generated artifact is a **full copy** of the template; only declared domain surfaces are editable; engine files are copied verbatim and write-blocked, with fixes going upstream **once**. Enforced three ways: `ENGINE_FILES` in `builder_core.write_denial`, an SDK-MCP tool boundary on the web path, and a PreToolUse guard hook on the plugin path — plus a read allowlist (`references/`, `boilerplate/`, `integrations/`, `skill_steps/`, `SKILL.md`, own workspace) so a builder can't read other sessions' workspaces or live credentials. Keep the paradigm and the enforcement; the file list is new.

### 3.11 One shared deterministic core, many front doors — proven
`builder_core.py` serves both the web platform and the Claude Code plugin with **no forked logic**; both get identical behavior and identical bugfixes. The plugin surface also cost two logged traps: plugin commands are **always namespaced by plugin name** (`/alta-builder:alta-build`, not `/alta-build`), and a root `.mcp.json` is loaded twice when a repo is its own plugin root (project scope leaves `${CLAUDE_PLUGIN_ROOT}` unsubstituted) — hence the inline `mcpServers` declaration. Also: a stdio MCP server's **cwd is fixed at spawn** and is not a proxy for where the user is, so every tool takes an explicit absolute `workspace_dir`.

### 3.12 Known gaps in the shipped system (do not inherit them)
- **No instrumentation.** SPEC §Assumptions is explicit: *no timing exists on any model call*, and `vapi_adapter.py:200` hardcodes `usage` to zeros. Every latency and cost claim in the old system is reasoned, not measured. A forward-looking PRD should treat **measurement (latency, tokens, cost, correlation ids) as a day-one Core capability**, not a later increment.
- **No correlation id** generated at ingress and threaded through logs; `call.id` is the de facto one and only exists on the voice path.
- **Persistence is minimal.** `MemorySaver` is the default checkpointer (durable checkpointing is documented as the caller's job); the lead/call record is flushed to **per-call JSON**; the platform DB has two tables. A persisted lead/entity store is still an SPEC Open Question.
- **Single-tenant by non-goal.** "Hosted multi-tenant deployment" is an explicit non-goal; the platform runs locally from one `.env`, with one active runtime on one port. Multi-tenancy is net-new work, not a port.
- **Uncommitted engine change.** `boilerplate/nodes.py` carries +21 uncommitted lines (`_speak_value()` used by `_confirm_question()`, rendering ISO-8601 slot values as spoken phrases) with **no regression test**, which the project's own quality bar requires. Also uncommitted: `ARCHITECTURE.md`, `CLAUDE.md`. `ARCHITECTURE.md` separately still cites a stale 161-test count.
- **Docs/tests drift is a live risk** in this repo and should be assumed, not trusted — brownfield.md itself flags the stale count.
