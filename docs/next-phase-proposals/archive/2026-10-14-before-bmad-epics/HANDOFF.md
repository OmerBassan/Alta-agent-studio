# Handoff: Agent Studio V1, after Phase 1, Phase 2 not authorized (2026-10-14)

Standing rules: do not commit, stage or push without the user's authorization. Never run `--live` without the user's approval. Do not start Phase 2 until the user authorizes it; they are reconciling it with the full BMAD implementation plan first.

## 1. Git state

- Branch `harden/seven-day`, HEAD `dcc2860`. Nothing is committed or staged.
- `M CLAUDE.md`: one additive section ("Current work: implementing the V1 product in studio/"), +16/−1.
- `?? docs/next-phase-proposals/`: `NEXT-PHASE-PLAN.md`, `IMPLEMENTATION-STATE.md`, `BMAD-DECISION-REGISTER.md`, `PROOF-GATE.md`, and this `HANDOFF.md`.
- `?? studio/`: the new product package (spec, core, agent, channels, extensions, businesses/dental and brewery, tests).
- The 2026-10-14 session edited only the planning docs (IMPLEMENTATION-STATE §0 Verification table and Phase 2 status, NEXT-PHASE-PLAN §3.1 and §6, the PROOF-GATE timing note, the register note) and wrote this file. No application code changed.

## 2. Verified test results (run 2026-10-14)

| Command | Result |
| --- | --- |
| `python -m pytest studio/tests -q` | **126 passed**, including all 12 mutation proofs (first full run with all 126 tests) |
| `python -m studio scenarios --today 2026-10-13` | **10/10 PASS**, 0 model calls |
| `python -m pytest builder_platform/tests -q` | **332 passed** |
| `python -m pytest claude_plugin/tests -q` | **12 passed** |
| `python selftest.py` in `boilerplate/`, `Generated_Agents/BassanBrewerySDR/`, `Generated_Agents/BrightSmileDental/` | all three exit 0 |

Not done: a run on a clean checkout (`git worktree add`). It needs `studio/` committed first.

## 3. Approved scope and settled decisions

- **Architecture:** Architecture Spine AD-1 to AD-25 (hexagonal agent harness).
  - The model is in charge: "The Agent decides what to do next; the Core defines what the Agent is allowed to do." User-binding, `m-arch` 24 and 43.
  - The 15-node LangGraph system is the reference and migration source, not the foundation. Proof gate required (`m-arch` 47).
- **Product:** text, inbound, one email adapter; specification, not generated code (FR19, AD-4); voice out of V1.
  - Four exemplar businesses: brewery 40-person event, gym membership freeze, garden-centre dying plant, dental root-canal explanation.
  - The Builder is in scope (`m-brief` 52). No starter templates (B-06) and no operator test playground (B-05).
  - Ledger visual design (B-17); divergence alerting rides the escalation email (B-14).
- **Program (NEXT-PHASE-PLAN §2):**

| Phase | Covers | State |
| --- | --- | --- |
| 1 | Runtime foundation and proof gate | Done; proof-gate axes 3–4 (model calls, latency) pending one live run |
| 2 | Knowledge and grounding (E6), garden centre | Planned, **not authorized** |
| 3 | Promotion, evaluation, divergence backlog, corrections, replay | — |
| 4 | Builder (E2) | — |
| 5 | Operator UX | — |
| 6 | Email channel and go-live | — |
| 7 | Four businesses through the Builder, one real business | — |

- **Precedence for `studio/`:** approved BMAD decisions win; the Spine's ADs bind the code; the voice-only, latency and Vapi rules don't apply.
- **Still the user's** (register §12, plan §6):
  - Counterfactual replay in V1 (O11), before Phase 3; recommendation yes.
  - Mailbox and credentials, for Phase 6.
  - One real business (FR92) and 2–3 operator conversations (FR94), for Phase 7; both can start now.
  - Commit authorization.

## 4. Phase 2

Full detail: NEXT-PHASE-PLAN §3.1.

**Findings from the Phase 1 code (P2-F1–F5):**
- **P2-F1. Retrieval is nearly vacuous.** Every source reference is issued at episode start, and all source text is in the agent's view on every turn, so the agent never needs `retrieve`.
- **P2-F2. FR37 and pinned-version resume break** after a restart that follows a knowledge edit. `SpecRegistry` is in memory and no source text is stored durably.
- **P2-F3. Precedence is only a sort tie-breaker** (FR31).
- **P2-F4. Freshness is an unenforced label** (FR35). U3/G45's premise (effect-gating reads cluster near episode end) is still unmeasured.
- **P2-F5. The garden centre needs no new Core feature.** It is a clean test of business three.

**Proposed steps:**
- 2.1 `studio/knowledge/`: content-addressed source store, `Retriever` port, lexical default, Markdown/plain-text ingestion contract, source text snapshotted at pinning.
- 2.2 Retrieval as a decided action: references issued at retrieval; evidence records source, version and locator per item.
- 2.3 Precedence and freshness.
- 2.4 Garden centre from `spec-stress-test.md` §3, including the lavender failure case: care advice marked as general knowledge, guarantee position stated as undetermined, claim deferred not refused, no conclusion of neglect.
- 2.5 Phase report.

Each new check is proven by injecting its violation and by mutation.

**Proposed technical choices (PROPOSED, not approved):**

| # | Choice |
| --- | --- |
| T9 | Source material reaches the agent only through `retrieve`; the specification projection stays in context |
| T10 | Lexical retrieval behind a port; an embeddings adapter (K-08) only if measured recall misses justify it |
| T11 | Same-heading conflicts resolved by declared precedence, lower item marked superseded and uncitable; the specification outranks sources |
| T12 | A missing or stale gating read is a typed refusal, never a Core-scheduled read; the read-to-effect gap is recorded (U3) |

**Dependencies:**
- Phase 2 uses the Phase 1 Core: claims, the provenance table, conclusions, suspend/pending, multiple goals.
- It feeds Phase 3 (replay needs FR37), Phase 4 (the ingestion contract) and Phase 7 (engine-leak log entry 2).

**Not in Phase 2:**
- PDF ingestion (FR2, Phase 4)
- Durable immutable specification versions (Phase 3)
- The NFR6 faithfulness measurement (Phase 3)
- The gym (Phase 7)

**Unresolved:**
1. **Live proof-gate timing.**
   - Recommendation: run it once after Phase 2, because T9 changes model calls per turn.
   - **Not confirmed.** PRD §12 (`prd.md` line 665) says "The proof gate (§7.5) sits in front of E4–E9", Phase 2 is E6, and `m-arch` 47 requires the gate "before committing the whole runtime".
   - Phase 1 already built E4/E5/E7/E8/E9 alongside the gate.
   - Alternative that honours the text: run now (≤ US$0.25), then again after Phase 2 for a before and after.
2. **Approval of T9–T12**, especially T9, which changes visible behaviour (answers from source material cost a retrieval call).
3. **Authorization to start Phase 2.**

## 5. Documents to read in a fresh context

1. `CLAUDE.md`, the section "Current work: implementing the V1 product in studio/"
2. `docs/next-phase-proposals/IMPLEMENTATION-STATE.md` §0
3. `docs/next-phase-proposals/NEXT-PHASE-PLAN.md`: §2, §3, **§3.1**, §4.4, §6
4. `docs/next-phase-proposals/BMAD-DECISION-REGISTER.md`: the revision 3 note, §0.3, §6 (K-rows), §10, §11 (U3), §12
5. `docs/next-phase-proposals/PROOF-GATE.md`
6. `_bmad-output/planning-artifacts/architecture/architecture-AgentStudio-2026-10-07/ARCHITECTURE-SPINE.md` (AD-7, AD-8, AD-11, Deferred)
7. `_bmad-output/planning-artifacts/prds/prd-AgentStudio-2026-10-08/prd.md`: §2 exemplars, §7.5, §8.4 (FR30–37), §12 (line 665)
8. `_bmad-output/planning-artifacts/briefs/brief-AgentStudio-2026-10-07/spec-stress-test.md` §3 (garden centre); `brief.md` "Grounding has two tiers"
9. `_bmad-output/planning-artifacts/architecture/architecture-AgentStudio-2026-10-07/.memlog.md` entry 47
10. Code: `studio/core/harness.py` (`SpecRegistry`, `_start_episode`, `_retrieve`, `_read`, `_check_claims`, the agent-view assembly), `studio/spec/compile.py` (`_items`), `studio/spec/model.py` (`Source`, `Grounding`, `Capability.freshness`), `studio/spec/loader.py`
