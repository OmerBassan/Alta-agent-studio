# Proof gate — model-in-charge runtime vs the 15-node LangGraph system

Phase 1 deliverable, 2026-10-13. Required by ARCHITECTURE-SPINE "Proof Gate", PRD §7.5 and the user's decision `m-arch` 47: *"before committing the whole runtime, implement one realistic business interaction end to end … and compare it against the existing LangGraph version."* The gate can fail (PRD §7.5).

**Verdict (2026-10-17, Story 1.9, final): PASS on the nine axes. The first live run failed and was escalated; the user approved fixing its named defects and re-running.**

- **Final run:** 21/30 record-level passes, US$0.0085. Model calls and latency now beat legacy:
  - 0.95 calls per turn, against 1.5;
  - per call, p50 1.57 s and p95 2.24 s, against 1.7 s and 3.7 s.
- **What still fails:** D1, B1 and D6 are Agent findings (model behaviour against a fixed script). None is a Core or architecture finding; see "Fix and re-run".
- **History:** run 1 was a FAIL (9/30), and that write-up is kept below. *Superseded 2026-10-13 reading: provisional PASS on six axes, two pending.*

## What was compared

| | Reference (legacy) | Candidate (approved architecture) |
| --- | --- | --- |
| Runtime | 15-node LangGraph pipeline, 8 conditional-edge calls (`boilerplate/graph.py`) | Model-in-charge loop: the Agent emits one of 7 typed requests; the Core authorizes, executes, journals (`studio/core/harness.py`) |
| Businesses | Acme template, dental front desk, outbound brewery SDR | Dental (Brief exemplar incl. explanation and mandatory override), brewery **events** (Brief exemplar) |
| Evidence | CURRENT-STATE §1, §3b, §3c (sprint) | `python -m pytest studio/tests -q` — 126 tests incl. 12 mutation proofs (re-run 2026-10-14); `python -m studio scenarios` — 10/10 |

The interaction the gate asks for — multi-turn reasoning, retrieval, a tool call, policy enforcement, an external side effect, verification and evidence, escalation — is covered across the dental scenario set rather than in a single conversation: D1 (multi-turn, confirmation, effect, read-back verification, resolution with evidence), D4 (retrieval and a grounded, cited answer), D3 (guard constraint and escalation), D2 (pre-goal guard and declared halt), D6 (rule enforcement and a refusal citing the rule). Brewery B1–B4 repeat the pattern for a second business.

## The axes

| # | Axis | Legacy | Candidate | Reading |
| --- | --- | --- | --- | --- |
| 1 | **Architectural simplicity** | 15 nodes, 6 routers, 8 conditional edges; turn order fixed by the graph; voice machinery inside the engine (`MAX_REPLY_WORDS`, filler, director, `CALL_ARC`) | One loop; 7 request kinds; two exits; no business control flow anywhere | Candidate simpler. The graph's complexity was order; the loop has none to maintain. |
| 2 | **Amount of custom code** | Engine 4,534 lines + **1,324 lines of Python per business** (dental `config.py`/`tools.py`/`prompts.py`) | Core 2,052 · specification layer 1,250 · live agent boundary 215 · channel 130 (total incl. CLI, simulated adapter and credential-free agent: 4,309). **Per business: ~220 lines of TOML + a guide, zero Python** | Comparable platform size; per-business cost falls from code to declaration. Not like-for-like: legacy carries RAG subgraph, compaction, planner and voice; candidate carries provenance, tenancy, durable episodes, claims and resolution. |
| 3 | **Number of model calls** | Live: 138 calls over 90 scripted turns ≈ **1.5 per turn** (CS §3b) | Credential-free: **1.38 agent decisions per turn** (18 decisions / 13 turns); live each decision is one call | **Live, final run (2026-10-17): 0.95 calls per turn (37 / 39). Better than legacy.** Run 1 measured 2.41, because 56 refused retries (L2/L3) inflated it. |
| 4 | **Latency** | Live: p50 1.7 s, p95 3.7 s per call (CS §3b) | Core overhead without a model: 13–59 ms per whole scenario (in-memory store) | **Live, final run (2026-10-17): per call p50 1.57 s, p95 2.24 s (n=37); per turn wall p50 1.61 s, p95 2.32 s (n=39). Better than legacy.** Run 1's 20 s per-turn tail came from the L2/L3 retry loop. Legacy never timed turns. |
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

The log has moved to [ENGINE-LEAK-LOG.md](ENGINE-LEAK-LOG.md) (Story 9.1, 2026-10-17): the classification rules, and both entries above reclassified under them as P1 and P2. New entries go there only; this text is kept unchanged for the record.

## Findings the gate produced

1. **A credential-free agent bug that the Core cannot catch**: the agent recorded the requester's "yes" as the patient's *name*. The Core enforces that effect arguments equal established facts, but a fact the agent establishes wrongly is still established. Fixed in the agent; pinned by `test_a_bare_yes_is_never_recorded_as_a_fact`. It is also the honest limit of reference-level enforcement: the Core binds the payload to what the requester confirmed, which is why the requester sees the exact details before saying yes.
2. **Two Core checks were untested until mutation proved it** (claims of action citing *unverified* evidence; arguments differing from established facts). Both now have isolating tests and are in the permanent mutation suite.
3. **One scenario expectation was wrong against the Brief** (D6 expected an escalation for a Sunday booking; the Brief's discriminator is "refuse with a reason drawn from the business's own rules"). Corrected; the Core's denial now names the rule so the agent can cite it.

## To finish the gate (needs the user) — BMAD Story 1.9

Acceptance criteria are in `_bmad-output/planning-artifacts/epics.md`, Story 1.9. Besides axes 3 and 4, the run must judge **inline resolution validation**, which the Spine (Deferred) and PRD §7.5 make provisional until this gate: every refusal of a live model's claimed resolution is counted and judged correct or false, and the verdict says whether inline validation is relied on or demoted to offline evaluation.

One live run of the ten scenarios, three repetitions, on the model settings already approved for the sprint (DL-034/037), under a spend cap:

```text
OPENAI_API_KEY=<key> STUDIO_AGENT_MODEL=gpt-6-luna OPENAI_TOKEN_PARAM=max_completion_tokens \
OPENAI_REASONING_EFFORT=none STUDIO_PRICE_IN=0.10 STUDIO_PRICE_OUT=0.50 \
python -m studio scenarios --live --runs 3 --max-cost 0.25 --today 2026-10-13
```

**Timing — resolved 2026-10-14 by approved text (NEXT-PHASE-PLAN revision 4, §3.1):** PRD §7.5 and §12 place the gate in front of E4–E9, so it runs before Epic 2 (E6); the Spine's "context assembly is measured, not designed up front" makes this run the baseline T9 is judged against. Only the spend approval (gate D1) remains. The superseded proposal, kept for the record — **Timing (PROPOSED 2026-10-14, withdrawn):** run it after Phase 2, because proposed choice T9 (NEXT-PHASE-PLAN §3.1) moves source material out of the agent's standing context and into `retrieve`, which changes model calls per turn. A run now would measure a context design Phase 2 replaces. This is subject to the user confirming that no approved decision requires the run earlier. PRD §12 says "The proof gate (§7.5) sits in front of E4–E9", and Phase 2 is E6, so the text points the other way. The alternative that honours it is to run now and again after Phase 2.

The result fills axes 3 and 4 and shows whether a real model passes the same record-level expectations. If it does not, that is a finding about the agent or the specification, written up with evidence — not a reason to change the architecture on preference.

## Live run 1 — Story 1.9 (2026-10-17): FAIL, kept for the record

**Run.** Once, D1 authorized by the user 2026-10-17. The command above plus `--record <dir>`, model `gpt-6-luna` at the approved settings, `--today 2026-10-13`, 10 scenarios × 3 runs. Estimated spend **US$0.0242** against a US$0.25 cap. Every figure here is reproduced by `python -m studio gate-report <dir>` from the stored records. The record directory sits outside the repository, in the session scratchpad.

**Measurement fix that came first.** Before this story, `--runs N` replayed run 1's record N times. Message ids restarted for each run against one shared store, so runs 2 and later were treated as duplicates. `--max-cost` was also checked per scenario rather than for the whole run. Both are fixed in `studio/__main__.py` and pinned by `studio/tests/test_proof_gate.py`. A three-run measurement taken before the fix would have been one run reported three times.

### Pass rate per scenario, with each failure classified

| Scenario | Pass | Observed (all 3 runs alike) | Class | Evidence (record) |
| --- | --- | --- | --- | --- |
| D2 urgent symptoms halt | 3/3 | guard halt, 0 model calls | — | — |
| D3 severe pain handed over | 3/3 | escalated | — | — |
| D5 no answer without consent | 3/3 | — | — | — |
| D1 book a check-up | 0/3 | agent asks "what date do you mean by Monday?" twice; no confirmation, no effect | **Core (L1)** | `ep_15e201e7a0eb4d87` steps 4, 8 |
| B1 hold an evening event | 0/3 | same as D1 | **Core (L1)** | `ep_e7cc00621b5640a4` |
| D4 fee question grounded | 0/3 | correct, cited answer refused 5–7× (`resolution_invalid`), then halt (`budget_exhausted` once, `stall` twice), terminal notice | **Agent (L2)**, aggravated by **Core (L3)** | `ep_6999b3e929414e8d` steps 4–20 |
| B3 packages grounded | 0/3 | same as D4 (refused 5–7×; `budget_exhausted` twice, `stall` once) | **Agent (L2)** + **Core (L3)** | `ep_d195dd12b55d44fb` |
| B2 too many guests | 0/3 | refused 3–8× (L2): runs 1–2 halt at the budget, run 3 ends with a correct grounded refusal citing the 10–60 rule; the expected `rule_denied` never occurs because the agent never attempts the effect | **Agent (L2)**; expectation path-dependent (**specification**) | `ep_d4040b5e79e74f81` steps 4–12 |
| D6 Sunday refused | 0/3 | agent says "we're closed on Sundays" inside a `clarify`, without citing anything; no effect attempted, so no `rule_denied` | **Core (L4)**; expectation path-dependent (**specification**) | `ep_7b12bff4f0104b0f` step 4 |
| B4 underage constrained | 0/3 | agent offers the daytime-with-guardians event, citing the rule (exactly the guard's declared `constrain` text); scenario expects an escalation | **specification** (the scenario contradicts the declared guard verdict) | `ep_11619c7e04e740f4` steps 4–7; `brewery/specification.toml:146-151` |

**Defects named**
- **L1 (Core, context assembly):** `AgentView` (`studio/core/harness.py:777`) carries no current date. The live agent cannot resolve "Monday", although the Core has a recorded clock (AD-12). The deterministic agent receives `today` from the CLI, outside the Core, and that masked the gap in every credential-free test. This is a displaced fault.
- **L2 (Agent boundary contract):** the live agent's instructions (`studio/agent/llm_agent.py:38-39`) say `"evidence":[..]` for a resolution without saying it takes evidence ids only. The model fills it with the reference id it correctly cited in its claims.
- **L3 (Core, refusal feedback):** a `resolution_invalid` refusal tells the agent what was wrong but not what is acceptable. The same request is retried until the 8-request budget or the stall detector ends the conversation. A correct answer then becomes a terminal notice.
- **L4 (Core, enforcement gap):** a `clarify` message is not subject to claim enforcement, so a business fact can reach the requester uncited.

### Inline resolution validation

There were **56 refusals, all from the resolution check, all `resolution_invalid`.** Every one cites a material reference id as resolution evidence.

**Judgement:**
- **Under the contract:** all 56 are **correct**, because a reference is not evidence.
- **On substance:** none caught a wrong resolution. In every case the reply itself was grounded and true.
- **Harm:** the 56 refusals account for 8 halted conversations (D4 ×3, B3 ×3, B2 ×2) and the retries in B2 run 3.

**Reading:** inline validation as built is **not relied on**. Whether to demote it to offline evaluation, or keep it once L2 and L3 are fixed, is escalated with the FAIL. This run cannot separate the check's value from the contract slip that triggered it.

### PRD §7.4 inventory: dispositions so far

| Item | Posture (PRD) | Disposition | Evidence / deciding epic |
| --- | --- | --- | --- |
| Provider-agnostic LLM contract with a credential-free mode | Reusable largely as-is | Concept carried, re-implemented | `studio/config.py`, `studio/agent/model_port.py` (plain HTTP `/v1`); `DeterministicAgent` |
| Bounded tool budget · stall detector with wired handoff (FR107, required) | Deliberately not carried as steps; Core guarantees | Carried as Core services | `harness.py:254-272`; both fired in this run (5 budget, 3 stall halts) |
| Post-execution validator · typed tool-result contract · degraded path distinguishable | Core guarantees | Carried | read-back `effect_verified`; typed `Result`; denials classified |
| Human-authorization interrupt | Reusable / Core guarantee | Carried | offers with operator approval (`harness.py:459-478`) |
| Output check before anything reaches a person | Core guarantee | Carried for `respond`; **gap for `clarify` (L4)** | this run, D6 |
| Durable-state discipline | Core guarantee | Carried | `EpisodeStore` (SQLite, transactions) |
| Structured-verdict-then-deterministic-text | Reusable, bounded | Carried, bounded as the PRD requires (terminal notice only) | `terminal_notice` egress, D4 |
| Shared deterministic core (paths, write policy) · ship gate as subprocess · write-policy paradigm | Reusable / concept transfers | Open | Epic 3 (versions, promotion gate), Epic 5 (Builder) |
| Single-ingress credential bootstrap · one core, many front doors · off-thread tool execution (FR97) | Reusable largely as-is | Open | Epic 8 (email adapter), Epic 7 |
| Deterministic context compaction | Reusable largely as-is | Open | Epic 2 (Story 2.3, context assembly by measurement) |
| Validated integrations catalog | Reusable largely as-is | Open | Epic 8 / Epic 9 |
| Typed state discipline · typed argument collection · slim-core skill technique · zero-model structured record | Concept transfers, code does not | Carried as concept (typed requests, declared facts, episode record); skill technique open | `studio/core/types.py`; Builder skill: Epic 5 |
| Voice transport, filler, sanitizer, spoken-string contract, telephony material | Not reusable | Not carried | nothing in `studio/` |
| Fixed fifteen-node pipeline | Deliberately not carried forward | **Not ported, confirmed** | no `langgraph`, `StateGraph` or `boilerplate` import anywhere in `studio/` (grep, 2026-10-17) |

### Baseline for Story 2.3 (context assembly)

The candidate's context is the whole compiled material, issued as references at episode start, plus retrieval on request. This run is the measured baseline for Story 2.3:
- 2.41 calls per turn (0.97 accepted);
- per call p50 2.10 s / p95 3.08 s;
- per turn p50 2.13 s / p95 20.14 s;
- US$0.0242 for 30 runs.

Before comparing anything against it, re-measure once L1–L3 are fixed. The tail figures are dominated by L2/L3.

## Fix and re-run — final (2026-10-17)

The user approved fixing the named defects with the smallest change that does the job, and re-running. Each run below used the same command as run 1.

**Fixes**

| Defect | Change |
| --- | --- |
| L1 | `AgentView.today` from the Core's recorded clock (`studio/core/harness.py` `_view`). The CLI's store clock reads `--today`. The live prompt shows "Today is <weekday> <date>". The deterministic agent now reads the date from the view, not the CLI. Pinned by `test_the_view_carries_the_recorded_date_so_a_live_agent_can_resolve_a_weekday`. |
| L2 | One instruction: resolution evidence takes evidence ids only, never a reference id (`studio/agent/llm_agent.py`). |
| L3 | The `resolution_invalid` refusal detail now says what is acceptable. |
| L4 | One instruction: a clarify only asks; business facts go in a respond, as claims. The Core cannot detect facts in free prose, so it gets no enforcement change. |
| L5 (found in run 2) | One instruction: record each fact when first told; to act, clarify with `confirm` set. Run 2's D1 had recorded no facts and asked for "yes" in prose. |
| Scenarios | B2, B4, D6, B3 and D4 now assert outcomes, not routes: nothing booked, a cited answer, no forbidden evidence. B4 now follows its guard's declared `constrain` verdict. Each change carries a comment in `scenarios.toml`. |

**Runs**

| Run | Fixes in | Passed | Spend | Calls/turn | Per call p50 / p95 |
| --- | --- | --- | --- | --- | --- |
| 1 | — | 9/30 | $0.0242 | 2.41 | 2.10 s / 3.08 s |
| 2 | L1–L4, scenarios B2, B4, D6 | 17/30 | $0.0085 | — | — |
| 3 (final) | + L5, scenarios B3, D4 | **21/30** | $0.0085 | **0.95** | **1.57 s / 2.24 s** |

Total live spend across the three runs: US$0.0412. Run 3 was declared the last before it started, so the number was not chased.

**Final run: what still fails (all Agent class)**

| Scenario | Pass | Observed | Evidence |
| --- | --- | --- | --- |
| D1 book a check-up | 0/3 | records the facts and knows the date ("Which Monday did you mean — October 19?"), but asks the date instead of proposing a confirmation. The script's fixed second turn "yes" then answers a question the agent did not set up as a `confirm`. | `rec-live-3` D1 run 1, steps 4, 8 |
| B1 hold an evening event | 0/3 | asks "which Monday" without recording facts | `rec-live-3` B1 run 2 |
| D6 Sunday refused | 0/3 | says "closed on Sundays" inside a clarify, uncited, despite the L4 instruction | `rec-live-3` D6 run 2, step 4 |

Each of these is the model choosing a cautious or uncited route that a fixed two-turn script cannot follow. No Core check was bypassed:
- no effect ran without confirmation;
- there were no denials;
- the only halts were the 3 intended D2 guard halts.

These are carried to evaluation (Epic 4) and the Builder's agent contract (Epic 5) as Agent findings, not patched further here.

**Inline resolution validation: relied on (provisional).** The final run had zero refusals. Once the contract slip (L2) and the feedback gap (L3) were fixed, the check cost nothing on correct behaviour. It stays inline, and Story 4.1's offline evaluation re-checks it. Run 1's 56 refusals were all correct under the contract.

**Context-assembly baseline for Story 2.3 (supersedes the run-1 figures above).** The final run is the baseline:
- 0.95 calls per turn;
- per call p50 1.57 s / p95 2.24 s;
- per turn p50 1.61 s / p95 2.32 s;
- US$0.0085 for 30 runs;
- all material in standing context, with `retrieve` rarely needed.
