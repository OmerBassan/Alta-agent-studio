# Proof gate — model-in-charge runtime vs the 15-node LangGraph system

Phase 1 deliverable, 2026-10-13. Required by ARCHITECTURE-SPINE "Proof Gate", PRD §7.5 and the user's decision `m-arch` 47: *"before committing the whole runtime, implement one realistic business interaction end to end … and compare it against the existing LangGraph version."* The gate can fail (PRD §7.5).

**Verdict: provisional PASS on the six axes measurable without a model; two axes (model calls, latency) pending one live run that needs the user's approval to spend.** Nothing measured so far is a material problem for the approved architecture, so no product decision is escalated.

## What was compared

| | Reference (legacy) | Candidate (approved architecture) |
| --- | --- | --- |
| Runtime | 15-node LangGraph pipeline, 8 conditional-edge calls (`boilerplate/graph.py`) | Model-in-charge loop: the Agent emits one of 7 typed requests; the Core authorizes, executes, journals (`studio/core/harness.py`) |
| Businesses | Acme template, dental front desk, outbound brewery SDR | Dental (Brief exemplar incl. explanation and mandatory override), brewery **events** (Brief exemplar) |
| Evidence | CURRENT-STATE §1, §3b, §3c (sprint) | `python -m pytest studio/tests -q` — 124 tests incl. 12 mutation proofs; `python -m studio scenarios` — 10/10 |

The interaction the gate asks for — multi-turn reasoning, retrieval, a tool call, policy enforcement, an external side effect, verification and evidence, escalation — is covered across the dental scenario set rather than in a single conversation: D1 (multi-turn, confirmation, effect, read-back verification, resolution with evidence), D4 (retrieval and a grounded, cited answer), D3 (guard constraint and escalation), D2 (pre-goal guard and declared halt), D6 (rule enforcement and a refusal citing the rule). Brewery B1–B4 repeat the pattern for a second business.

## The axes

| # | Axis | Legacy | Candidate | Reading |
| --- | --- | --- | --- | --- |
| 1 | **Architectural simplicity** | 15 nodes, 6 routers, 8 conditional edges; turn order fixed by the graph; voice machinery inside the engine (`MAX_REPLY_WORDS`, filler, director, `CALL_ARC`) | One loop; 7 request kinds; two exits; no business control flow anywhere | Candidate simpler. The graph's complexity was order; the loop has none to maintain. |
| 2 | **Amount of custom code** | Engine 4,534 lines + **1,324 lines of Python per business** (dental `config.py`/`tools.py`/`prompts.py`) | Core 2,052 · specification layer 1,250 · live agent boundary 215 · channel 130 (total incl. CLI, simulated adapter and credential-free agent: 4,309). **Per business: ~220 lines of TOML + a guide, zero Python** | Comparable platform size; per-business cost falls from code to declaration. Not like-for-like: legacy carries RAG subgraph, compaction, planner and voice; candidate carries provenance, tenancy, durable episodes, claims and resolution. |
| 3 | **Number of model calls** | Live: 138 calls over 90 scripted turns ≈ **1.5 per turn** (CS §3b) | Credential-free: **1.38 agent decisions per turn** (18 decisions / 13 turns); live each decision is one call | **Pending live run.** The decision count is a floor: a live model may retrieve before answering, adding a call. |
| 4 | **Latency** | Live: p50 1.7 s, p95 3.7 s per call (CS §3b) | Core overhead without a model: 13–59 ms per whole scenario (in-memory store) | **Pending live run.** Core overhead is negligible; turn latency will be calls × per-call latency. |
| 5 | **Control** | Authorization at tool execution only (`authz.py`); confirmation and operator gates bound to payload | Every request kind authorized (reads, clarify, respond, escalate included); gates bound to tenant, episode, spec version, capability, canonical args; Core never selects a step | Candidate stronger and broader. |
| 6 | **Observability** | Per-node trace JSONL, written only by `agent_sandbox.py`; not by the runtime | Every inbound message, agent decision, Core result, effect, evidence item and egress is a durable step under one episode id; model calls with tokens and latency per step | Candidate stronger. |
| 7 | **Failure handling** | Unverified outcomes, timeouts, degraded flag on model calls | Adapter timeout, rejection, dropped write, unreachable read-back, agent exception, malformed model output, budget exhaustion, stall — each a typed result or a declared halt, each tested | Candidate equal or stronger. |
| 8 | **Extensibility to a second business** | Copy the whole engine; write domain Python; drift test keeps copies equal | Brewery added as a specification only, **zero Core changes** (engine-leak log entry 1) | Candidate stronger — the Spine's litmus test holds for business two. |
| 9 | **Ease of enforcing business boundaries** | Rules as Python hooks in `config.py`; prompt text for the rest | Closed predicate language in the spec, enforced by the Core; never-ask, conclusions, provenance, claims, general-knowledge switch; **12 Core checks proven non-vacuous by mutation** | Candidate stronger. |

(PRD §7.5 names "nine axes" and lists eight; "control and observability" is split here, which gives nine.)

## Engine-leak log (FR89, started here)

| # | Business | Change needed | Classification (FR116) |
| --- | --- | --- | --- |
| 1 | Brewery events (business 2) | None in `studio/core` or `studio/spec`. The simulated calendar gained per-business open times. | Test fixture leaf — not a Core change |

Retroactive, from the legacy sprint: DL-015 (strict consent) changed shared engine code while the third business was being built — *should have been platform behaviour from the start*; carried into the candidate as `studio/core/consent.py`.

## Findings the gate produced

1. **A credential-free agent bug that the Core cannot catch**: the agent recorded the requester's "yes" as the patient's *name*. The Core enforces that effect arguments equal established facts, but a fact the agent establishes wrongly is still established. Fixed in the agent; pinned by `test_a_bare_yes_is_never_recorded_as_a_fact`. It is also the honest limit of reference-level enforcement: the Core binds the payload to what the requester confirmed, which is why the requester sees the exact details before saying yes.
2. **Two Core checks were untested until mutation proved it** (claims of action citing *unverified* evidence; arguments differing from established facts). Both now have isolating tests and are in the permanent mutation suite.
3. **One scenario expectation was wrong against the Brief** (D6 expected an escalation for a Sunday booking; the Brief's discriminator is "refuse with a reason drawn from the business's own rules"). Corrected; the Core's denial now names the rule so the agent can cite it.

## To finish the gate (needs the user)

One live run of the ten scenarios, three repetitions, on the model settings already approved for the sprint (DL-034/037), under a spend cap:

```text
OPENAI_API_KEY=<key> STUDIO_AGENT_MODEL=gpt-6-luna OPENAI_TOKEN_PARAM=max_completion_tokens \
OPENAI_REASONING_EFFORT=none STUDIO_PRICE_IN=0.10 STUDIO_PRICE_OUT=0.50 \
python -m studio scenarios --live --runs 3 --max-cost 0.25 --today 2026-10-13
```

**Timing (PROPOSED 2026-10-14, unresolved):** run it after Phase 2, because proposed choice T9 (NEXT-PHASE-PLAN §3.1) moves source material out of the agent's standing context and into `retrieve`, which changes model calls per turn. A run now would measure a context design Phase 2 replaces. This is subject to the user confirming that no approved decision requires the run earlier. PRD §12 says "The proof gate (§7.5) sits in front of E4–E9", and Phase 2 is E6, so the text points the other way. The alternative that honours it is to run now and again after Phase 2.

The result fills axes 3 and 4 and shows whether a real model passes the same record-level expectations. If it does not, that is a finding about the agent or the specification, written up with evidence — not a reason to change the architecture on preference.
