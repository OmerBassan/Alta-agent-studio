# IMPLEMENTATION PROGRAM — Agent Studio V1

Revision 4, 2026-10-14. Revision 3 (2026-10-13) is archived unchanged at [archive/2026-10-14-before-bmad-epics/NEXT-PHASE-PLAN.md](archive/2026-10-14-before-bmad-epics/NEXT-PHASE-PLAN.md).
Mandate (user, 2026-10-13): *implement the product and architecture decisions already made through BMAD; treat approved decisions as implementation commitments; implement the intended product including UX; use technical experiments to unblock implementation, not as the objective; execute phase by phase.* IDs (V-, C-, B-, S-, A-, K-, E-, D-) refer to [BMAD-DECISION-REGISTER.md](BMAD-DECISION-REGISTER.md); FR/NFR/EX/O to the PRD; AD to the Architecture Spine.

**What this document holds.** The program: phases and their order (§2), technical choices made inside approved constraints (§3), the decision gates that need the user (§6), and risks (§7). It does **not** hold story acceptance criteria or the per-requirement trace: since revision 4 those live once, in the BMAD artifacts listed in §9, and this document refers to them by story ID.

**What changed in revision 4.** The program was broken into BMAD epics and stories (`bmad-create-epics-and-stories`) and a sprint status file was generated (`bmad-sprint-planning`). While reconciling against the PRD, Spine, UX spines, register and memlogs, five discrepancies in revision 3 were corrected, each from a source: NFR15 was missing from the matrix (PRD §9.4); FR60 was marked delivered but its deadline expiry is not an external event yet (PRD FR60, code: `harness.py` stores the deadline, nothing emits its expiry); §7's lapsed-pending mitigation added a divergence source the PRD does not have (FR77, FR108, FR115) and is replaced by FR60's own route; inline resolution validation is provisional until the proof gate (Spine Deferred, PRD §7.5) and is now part of the gate; and the proof-gate timing is resolved by approved text (§3.1). No decision status changed.

**Status of this document:** the program is the working plan. Approved BMAD decisions are commitments, not proposals. Technical choices I make inside the approved constraints are recorded in §3 and are revisable on evidence. Nothing is committed to git without the user's authorization.

---

## 1. What changed from revision 2, and why

Revision 2 treated six items as user decisions. Under the mandate and the established precedence (approved decisions and explicit amendments win; later approved decisions supersede earlier ones), four of them are already decided by approved sources:

| Rev. 2 question | Resolution by precedence | Source |
| --- | --- | --- |
| Q1 Runtime-first vs Builder-first | Not a product decision — it is sequencing. The Builder is in V1 scope (B-00, `m-brief` 52) and is planned at full approved scope (Phase 4). Ordering is a technical dependency call: the Builder's output is the specification, so the specification and the runtime that executes it come first. | `m-brief` 52; FR9; AD-4 |
| Q2 Episode list for the operator | UX decided, by operator ruling, that the interaction viewer opens only from Activity and that there is no list of all interactions (`m-ux` 85, 87). The PRD review's F3.1 is a reviewer finding, not an approved requirement. **Implemented as approved**; the residual risk (a lapsed pending episode is invisible) is recorded in §7 and addressed by FR60's own route — deadline expiry as an external event (Story 1.10). *(Revision 3's "lapsed pendings as divergence items" is withdrawn: FR77, FR108 and FR115 define no such source.)* | `m-ux` 85, 87; FR79–80 |
| Q3 Specification, not generated code | Decided by approved FR19 ("neither a generated prompt nor generated code") and AD-4. | FR19; AD-4; `m-arch` 72 |
| Q4 `CLAUDE.md` scoping | `m-arch` 10 deferred it "to the appropriate workflow point". Starting implementation of the new product line is that point. A minimal additive section is written with the first handoff; the voice `SPEC.md` is not mutated. | `m-arch` 10 |
| Q5 Counterfactual replay | Genuinely open (PRD O11, UX Amendment 8). Not blocking until Phase 3. Recommended yes; escalated there. | O11 |
| Q6 Budget | The mandate is to execute phase by phase. Each phase is scoped to be reviewable on its own. | user mandate |

**Genuinely blocking decisions now: none.** See §6 for the items that will need the user later, and why each is a real dependency rather than a re-opened decision.

---

## 2. Program structure

The product is built as **vertical increments of the real product**, not throwaway spikes. Each phase adds production code to one new package, `studio/`, organised by the Spine's own namespaces. The shipped voice system stays intact and governed by its own spec of record (`m-arch` 10); nothing in `boilerplate/`, `Generated_Agents/` or `builder_platform/` is modified by this program unless a phase says so explicitly.

```text
studio/
  spec/        Business Specification: schema (EX1–EX17), loader, platform validation suite, Core compiler
  core/        The harness: request taxonomy, authorization, journal, evidence, episodes, guards, egress checks
  agent/       Agent runtime boundary (AD-14): agent port, scripted agent, deterministic mock agent, live model agent
  knowledge/   Version-pinned sources, precedence, retrieval, provenance issuance          (Phase 2)
  extensions/  Adapter port + simulated systems of record with failure injection and read-back
  channels/    Channel adapters: scenario harness (Phase 1), inbound email (Phase 6)
  builder/     The elicitation Builder                                                       (Phase 4)
  evaluation/  Invariant checks, business criteria, divergence, corrections, replay (if O11)  (Phase 3)
  web/         The operator experience: Build and Run surfaces, Ledger design               (Phase 5)
  businesses/  Business specifications and knowledge (dental, brewery events, garden centre, gym)
  tests/
```

| Phase | Delivers (product capability) | Epics | Proof-gate role |
| --- | --- | --- | --- |
| **1** | **Runtime foundation**: one Business Specification compiled by the Core into three projections; the model-in-charge loop; closed request taxonomy with every kind authorized and journaled; tenant-scoped durable episodes and evidence; confirmations, idempotency, read-back verification; guards, two exits, terminal notice, disclosure; suspend; resolution envelope and validation; two businesses (dental, brewery events). | E1 (core), E3 (validation core), E4, E5, E7, E8, E9 | **The proof gate is run inside this phase** as a vertical slice. Six axes measured credential-free; axes 3–4 and the inline-resolution-validation verdict need one live run (Story 1.9). No throwaway code. |
| **2** | **Knowledge and grounding**: version-pinned sources, precedence, retrieval as a decided action, Core-issued provenance for every authoritative item, two knowledge tiers, freshness per contract; garden centre. | E6 | Starts after the gate verdict: PRD §7.5 and §12 place the gate "in front of E4–E9". |
| **3** | **Change safety and the improvement loop (backend)**: immutable versions, promotion gated by the validation suite and recorded approval, rollback, version pinning per episode; per-episode evaluation computed from the record; divergence classification and backlog; human corrections; refusal sampling; replay **only if O11 is approved** (gate D7). | E3, E9, E10 (backend) | — |
| **4** | **The Builder**: agent-driven elicitation from conversation and material to specification + knowledge; contradictions, defects, process re-derivation; correction as conversation + confirmed diff; revision of a promoted specification; burden + yield; seeded fixture. | E2 | — |
| **5** | **The operator experience** (UX spines): cold-start workspace, co-present Conversation + Understanding, correction diff, validation and approval, Activity with status line, interaction viewer, Suspend, closed vocabulary, Ledger visual system, WCAG 2.2 AA, phone-usable Run surfaces. | E10 (surfaces) + UX | — |
| **6** | **Email channel and go-live**: inbound email adapter with FR114 hazards, built against captured traffic; disclosure; escalation email (+ material divergence, Amendment 1); connect mailbox as the go-live act; mailbox status. | E11 | — |
| **7** | **Generalisation programme**: the four exemplars built through the Builder; engine-leak log, resolution strain, setup effort, validity floor; usefulness test with one real business. | E12 | — |

Phase 1 was split into four reviewable steps (historical): **1.1** specification · **1.2** Core and durable store · **1.3** agent boundary, channel harness, businesses, scenarios · **1.4** proof-gate report and handoff.

### 2.1 Phases → BMAD epics and stories

Story acceptance criteria are in `_bmad-output/planning-artifacts/epics.md`; sprint state is in `_bmad-output/implementation-artifacts/sprint-status.yaml`. Story numbers below are BMAD IDs (Epic.Story), not the historical step numbers above.

| Phase | BMAD epic | Stories | State (2026-10-14) |
| --- | --- | --- | --- |
| 1 | Epic 1 — Bounded agent runtime | 1.1–1.12 done (Sprint 1 closed 2026-10-18) | Done: proof gate PASS (PROOF-GATE.md), CI green on Linux and Windows |
| 2 | Epic 2 — Grounded answers | 2.1–2.6 | After the 1.9 verdict; 2.3–2.5 blocked on D2, D4–D6 |
| 3 | Epic 3 — Safe change; Epic 4 — Evaluation and backlog | 3.1–3.4; 4.1–4.7 | 4.7 blocked on D7 (O11); 3.3 on D14, D15; 4.5's reference criterion on D15; 4.1's suspension-exclusion criterion on D14 |
| 4 | Epic 5 — Builder | 5.1–5.9 | Recommended before 5.3, not a dependency: 9.8 operator conversations; 5.2 blocked on D15 |
| 5 | Epic 6 — Teaching workspace; Epic 7 — Run surfaces | 6.1–6.6; 7.1–7.8 | 7.7 blocked on D9; 7.8 on D8; criteria of 7.1, 7.2 and 7.3 on D14 |
| 6 | Epic 8 — Go live on email | 8.1–8.7 | 8.1, 8.6 blocked on D10; 8.5 (last AC) on D10, D12; 8.7 on D11 |
| 7 | Epic 9 — Prove it generalises | 9.1–9.8 | 9.1 and 9.8 can start now; 9.7 blocked on D13 |

### 2.2 Why this order

1. **The proof gate first** (1.9): approved text puts it in front of further E4–E9 work (PRD §7.5, §12; `m-arch` 47), and the Spine requires context assembly to be measured before it is designed — the gate run is that measurement.
2. **Knowledge before versions** (Epic 2 before 3): FR37 reconstruction and pinned sources are what replay (4.7), the interaction viewer (7.3) and the Builder's ingestion (5.2) read from.
3. **Versions, promotion and evaluation before the Builder** (Epics 3–4 before 5): the Builder's output is a version that must pass the gate and be approved (FR11, FR101); building it first would author against a moving contract.
4. **Surfaces after what they render** (Epics 6–7 after 3–5).
5. **Email last before generalisation** (Epic 8): go-live needs approval, suspension and the status line.
6. **Generalisation last, but its human track now** (9.8, 9.1): V-04 ranks a real user first, and A4 is the premise the Builder rests on.

### 2.3 Sprint 1 — Phase 1 close-out

Goal: close Epic 1 and the proof gate. **9.1** (engine-leak classification rules) and **9.8** (operator conversations, owner: the user) run in parallel; neither is behind the gate.

| Order | Story | Needs |
| --- | --- | --- |
| 1 | 1.12 Credential-free CI on a clean checkout | D3 (commit and push) |
| 2 | 1.9 Complete the proof gate with a live comparison | D1 (spend) |
| 3 | 1.10 Deadline expiry as an external event | 1.9 verdict |
| 4 | 1.11 Crash mid-turn recovery | 1.9 verdict |
| parallel | 9.1 Engine-leak classification rules | — |
| parallel | 9.8 Two or three operator conversations | the user's time (D13) |

Definition of done for Sprint 1: every story's acceptance criteria in `epics.md` met; a written gate verdict; Epic 1 marked done in `sprint-status.yaml`; the Epic 1 retrospective (optional) run; all suites green on a clean checkout.

If D1 is withheld, Sprint 1 can still deliver 1.12, 9.1 and the planning-document corrections, and nothing behind the gate starts.

---

## 3. Technical choices made inside the approved constraints

Each passes AD-1's filter ("does this constrain the Agent, or decide its next step?") and none changes an approved decision. Each is revisable on evidence.

| # | Choice | Alternatives considered | Why, against the dominant constraint | What it makes harder later |
| --- | --- | --- | --- | --- |
| T1 | **Own thin agent loop** behind an `AgentRuntime` port (AD-14); no agent framework in Phase 1. | Pydantic AI (A-19, PROPOSED); OpenAI Agents SDK; reuse LangGraph. | Dominant constraint: **debuggability and enforcement visibility** — the loop *is* what the proof gate measures, and a framework that owns the loop hides it (AUDIT §5). Provider agnosticism (AD-14, NFR12) and deterministic mock testing are easiest with no framework types crossing the boundary. Pydantic AI's decisive advantage (serializable deferred approvals, `m-arch` 60) is reproduced by the Core's own durable confirmation records. | Owning tool-call parsing and retries. Mitigated: the port allows adopting Pydantic AI later without touching Core or Specification. |
| T2 | **Specification format: TOML**, validated by Pydantic models with `extra="forbid"`; content-addressed version = sha256 of the canonical, order-normalised specification plus source contents. | YAML (needs a dependency, implicit typing pitfalls); JSON (not human-friendly); typed Python (is code — violates FR19). | Dominant constraint: **human-readable, diffable, not code** (FR19). TOML parses with the standard library (`tomllib`), so no new dependency. A closed schema is the *mechanism* that makes ordering unexpressible (FR18); the validator is the backstop (FR24). Content addressing removes the sprint fingerprint's folder dependence. | Deep nesting is verbose. Acceptable: the schema is deliberately shallow. |
| T3 | **Episode store: SQLite** (stdlib) behind an `EpisodeStore` port, schema at the Spine's fallback floor — evidence and effect rows written in one transaction, `UNIQUE (tenant, episode, idempotency_key)`. | PostgreSQL 16+ (Spine seed); DBOS (A-20, PROPOSED). | Dominant constraint: **zero-setup, inspectable, transactional** for a solo V1. AD-9/AD-12 fix semantics, not the engine (`m-arch` 48: durability is infrastructure). The schema is portable; moving to Postgres is an adapter change. | Single writer; no cross-process concurrency. Stated as a limitation (§8). |
| T4 | **Confirmation is a Core record granted only by the requester's own inbound event** (a deterministic bare yes/no, reusing the approved strict-consent rule DL-015), bound to tenant, episode, specification version, capability and canonical arguments; consumed once. | Let the model judge consent; HMAC tokens. | AD-3: no enforcement may rely on the model. DL-008: confirmation records are Core-owned and unforgeable through model output. Reasoning-log `routing-is-not-an-authorization-gate`: records live outside model- or caller-writable state. | A long "yes, Tuesday works" is asked again (known cost, accepted in DL-015). |
| T5 | **Budget exhaustion and stall detection end in a declared safety halt** (AD-18) with the business's terminal notice to the requester and a halt notice delivered to the business's escalation destination. | Core-initiated escalation. | FR107 requires a wired outcome; FR47 forbids the platform escalating on the Agent's behalf; AD-18 allows exactly one non-return exit. A halt with a delivered notice satisfies all three. Register CX-03. | — |
| T6 | **Typed claims on `respond`**: every business fact the Agent asserts is a claim naming a Core-issued provenance reference; general-knowledge claims are marked; conclusions name a declared conclusion; action claims name a Core evidence id. | Free-text faithfulness checks. | AD-7 and FR32 scope the absolute guarantee to *reference integrity*; meaning is measured (NFR6). Typed claims make the guarantee enforceable without overclaiming (`m-arch` 39). | Prose that asserts a fact without a claim is not caught deterministically — measured in evaluation (Phase 3), stated in limitations. |
| T7 | **Model port**: a studio-owned, provider-agnostic OpenAI-compatible `/v1` client configured only by environment (`STUDIO_MODEL`, `OPENAI_BASE_URL`, `OPENAI_API_KEY`, `OPENAI_TOKEN_PARAM`, `OPENAI_REASONING_EFFORT`), JSON-mode structured output with parse-then-validate, per-call records (tokens, latency, path, ok) on the episode record. Arguments are `[{name, value}]` lists, never free-keyed dicts. | Import `boilerplate/llm_client.py`. | That file is an engine file copied per agent and loads a `.env` beside itself at import, so it cannot be a shared package dependency. PRD §7.4 classifies the client as "reusable as concept". DL-037 showed free-keyed dicts break strict schemas. | — |
| T8 | **Credential-free mode is a deterministic, domain-agnostic agent** that reads only the compiled projections. | Domain-coded mock heuristics (the old system). | PRD §7.4 keeps "a credential-free mock mode" as reusable; FR95 and the reasoning-log `domain-coupled-selftest` lesson forbid domain-coupled gates. Lets the whole product run and be demonstrated with zero tokens, and lets CI run end to end. | It is not the product's intelligence and is never presented as such. |

### 3.1 Phase 2 — findings and choices (recorded 2026-10-14; **T9–T12 APPROVED by the user 2026-10-19**)

**Status:** the user approved Sprint 2 (Phase 2) and T9–T12 on 2026-10-19; they join T1–T8. T9 is approved as recommended: both modes as a platform setting, default chosen by measurement.

**Findings from the Phase 1 code (verified by reading it on 2026-10-14):**

| # | Finding | Evidence | Requirement affected |
| --- | --- | --- | --- |
| P2-F1 | Retrieval is nearly vacuous. A reference for every source section is issued at episode start, and every reference's full text is in the agent's view on every turn, so the agent never needs to `retrieve`. Works only because sources are tiny (19 lines each). | `studio/core/harness.py` `_start_episode` (issues all `compiled.context.items`), the agent-view assembly (`references` with `text`) | AD-8, FR32/33 for retrieval, scalability |
| P2-F2 | FR37 and resume-at-pinned-version break after a restart that follows a knowledge edit. `SpecRegistry` is in memory and rebuilt from files; no source text is stored durably. | `studio/core/harness.py` `SpecRegistry`; `provenance` table stores ids and versions, not text | FR37, FR62, AD-11 |
| P2-F3 | Precedence is only a sort tie-breaker; no conflict between sources is detected or resolved. | `_retrieve` sort key `(−score, precedence, ref)` | FR31 |
| P2-F4 | Freshness is a label recorded on read evidence; nothing enforces it. U3/G45 (HIGH, unapplied) — the premise that effect-gating reads cluster near episode end — is still unmeasured. | `_read` evidence `"freshness": cap.freshness` | FR35, register §11 U3 |
| P2-F5 | The garden centre needs no new Core feature: conclusions, the liability class, `operator_approval`, `suspend`/pending on a named input and multiple goals all exist. It is a clean test of business three. | `studio/spec/model.py` classes; `harness.py` suspend path | FR89, E-05 |

**Proposed steps (now BMAD Stories 2.1–2.6; acceptance criteria in `epics.md`):** 2.1 `studio/knowledge/` (content-addressed source store, `Retriever` port, lexical default, ingestion contract for Markdown/plain text; source text snapshotted into the episode store at pinning) · 2.2 retrieval as a decided action (the specification projection stays in context; source material only via `retrieve`, references issued at retrieval; evidence records source, version and locator per item) · 2.3 precedence and freshness · 2.4 garden centre (spec and guides from `spec-stress-test.md` §3, simulated till-system lookup and stock adapters, scenarios incl. the lavender case: care advice marked as general knowledge, guarantee position stated as undetermined, claim deferred not refused, no conclusion of neglect) · 2.5 phase report. Each new check proven by injection and by mutation.

**Proposed technical choices:**

| # | Choice | Strongest alternative | Reason | Cost |
| --- | --- | --- | --- | --- |
| T9 | Source material reaches the agent only through `retrieve`; the specification projection stays in context. | Keep all material in context, issued at start | Spine defers context assembly as "measured, not designed"; the current form makes AD-8 hollow and does not scale | One extra model call whenever the agent retrieves; **changes proof-gate axes 3–4** |
| T10 | Lexical retrieval behind a `Retriever` port; an embeddings adapter over `/v1/embeddings` (K-08) only if garden-centre scenarios show recall misses | Embeddings now | K-03 defers retrieval architecture; E-07 measure before optimizing | Possible recall gaps until measured |
| T11 | A conflict is a same-heading section in sources of different precedence; the lower is returned marked superseded and citing it is refused. The specification outranks every source. | Agent judges conflicts; sources declare covered topics | Semantic conflict detection cannot be deterministic; the Builder surfaces contradictions at build time (FR5) | Conflicts under different headings are not caught at runtime |
| T12 | An effect contract may name the read it depends on and that read's maximum age; a missing or stale basis is a typed refusal, never a Core-scheduled read. The read-to-effect gap is recorded (U3). | Adapter re-checks at execution, no declared bound | FR35 forbids the Core sequencing a read before an act; a typed refusal constrains rather than decides (AD-1 test) | Agent must handle one more refusal reason |

**Not in Phase 2:** PDF/material ingestion (FR2, Phase 4) · durable immutable specification versions (Phase 3; Phase 2 does sources only) · the NFR6 faithfulness measurement (Phase 3; Phase 2 records its inputs) · the gym (Phase 7).

**Status of the three items revision 3 left unresolved:**

1. **Live proof-gate timing — resolved by approved text, not by preference.** PRD §7.5 ("It sits in front of E4–E9") and §12 place the gate before E6, `m-arch` 47 (user) requires it "before committing the whole runtime", and the Spine's Deferred table says context assembly is "measured, not designed up front" — so the gate run (Story 1.9) is also the baseline T9 needs. Epic 2 therefore starts after the 1.9 verdict. What remains for the user is permission to spend (**D1**). Revision 3's "run after Phase 2" recommendation is withdrawn.
2. **T9–T12 remain PROPOSED, not approved** (gates **D2, D4, D5, D6**). They do not join T1–T8 until the user approves. Recommendation for T9, also PROPOSED: build both context-assembly modes as a platform setting and choose the default from the measured comparison (Story 2.3), rather than adopting T9 outright.
3. **Authorization to start Phase 2** is now the combination of the 1.9 verdict and the user's go-ahead on Sprint 2.

---

## 4. Traceability — moved to the BMAD artifacts

The per-requirement matrix of revision 3 now lives in one place: **`_bmad-output/planning-artifacts/epics.md`**, sections *FR Coverage Map* (requirement → epic) and *Story Traceability* (requirement → stories → state), generated from each story's **Traces** line by `docs/next-phase-proposals/tools/trace_epics.py`, which also fails loudly on any requirement left without a story. Acceptance criteria and verification are on the stories. Revision 3's matrix is preserved verbatim in the archive copy.

Coverage at revision 4: **134 of 135 PRD IDs** (FR1–FR117, NFR1–NFR18) are traced to stories, and **FR8** is declined for V1 by the `m-ux` 22 override (register B-06); **30 of 30 UX design requirements** are traced. Corrections made while moving the matrix:

| ID | Revision 3 said | Revision 4 | Source |
| --- | --- | --- | --- |
| NFR15 | absent | Story 9.6 (cost slope measured during the four-business run) | PRD §9.4 |
| FR60 | ✓ delivered | partly done: Story 1.4 (lifecycle) + Story 1.10 (deadline expiry as an external event) | PRD FR60; `harness.py` stores the deadline only |
| FR71 | ✓ delivered | delivered, **provisional** until the gate verdict (Story 1.9) | Spine Deferred; PRD §7.5 |
| FR36 | "I (by design)" | traced to Story 1.5 (read-back against the business's own system) | PRD FR36 |
| FR96 | "every" | standing criterion of every story (`epics.md`, Story conventions) plus Stories 1.2, 1.3 | PRD FR96 |
| UX-DR21 | traced to 6.1 only | also 7.2, 7.3, 7.5, 8.5 (product voice on Run surfaces and the escalation email) | EXPERIENCE.md Voice and Tone |
| PRD §7.4 migration assessment | no story | Story 1.9's gate report keeps the record: dispositions decided so far, and the epic that decides each open item | PRD §12 |
| Epic 6 header | claimed UX-DR13 | UX-DR13 belongs to Story 8.6 | EXPERIENCE.md Surface inventory |
| Epic 9 builds | no rule on inputs | 9.2–9.5 forbid the hand-written specifications as Builder input | PRD review F4.3; FR88 |
| UX gaps 3–19 | not scheduled | each owned by a story or a decision gate (`epics.md` Additional Requirements; §6 below) | EXPERIENCE.md Amendments |

## 5. Post-V1, preserved and not built

Retention policy and deletion executor (AD-25 deferred) · policy-engine technology · durability engine choice beyond the fallback floor · model routing policy (tiering is expressible; policy measured) · resolution-kind enumeration (O4, emerges from episodes) · multi-tenant hosting, billing, packaging (O8) · extension marketplace · domain safety packs (O9) · escalation routing beyond one address (O2) · jurisdictional disclosure wording (O3) · spend ceiling (O6) · voice as a later channel adapter (O10) · starter templates (declined for V1, reconsiderable as an onboarding optimisation) · typed decision models (DL-041) · the faithfulness threshold value (O5).

## 6. Decision gates — what needs the user, and what it blocks

Status words follow the register: **OPEN** = undecided product item; **PROPOSED** = a technical choice awaiting approval; **Permission / Human action** = not a design decision. No gate below is decided by this document. *Blocks Sprint 1* marks the gates the first phase cannot finish without.

| Gate | Item | Kind | Blocks | Blocks Sprint 1 | Recommendation | Strongest alternative, and its cost |
| --- | --- | --- | --- | --- | --- | --- |
| **D1** | Spend on one live proof-gate run | Permission | 1.9 → 1.10, 1.11, Epic 2 onward | **Yes** | Approve ≤ US$0.25 under the existing US$0.50 ceiling, on the settled model settings (DL-034/037) | Withhold: nothing behind the gate starts |
| **D3** | Commit and push | Permission | 1.12; protects the untracked `studio/` | **Yes** | Commit Phase 1 and the planning set on a new branch (e.g. `studio/v1`); push when you say | Stay untracked: an accidental clean is unrecoverable and no clean-checkout proof is possible |
| **D2** | T9 — source material reached only through `retrieve` | **APPROVED 2026-10-19** (both modes, default by measurement) | 2.3 | No (Sprint 2) | Build both modes as a platform setting; choose the default from the measured comparison | Adopt T9 outright: less code, but designs up front what the Spine says to measure |
| **D4** | T10 — lexical retrieval behind a port; embeddings only on measured misses | **APPROVED 2026-10-19** | 2.3 | No | Approve | Embeddings now: earlier recall, an unmeasured optimization (E-07) |
| **D5** | T11 — same-heading conflicts resolved by declared precedence | **APPROVED 2026-10-19** | 2.4 | No | Approve | Agent judges conflicts: non-deterministic, unenforceable |
| **D6** | T12 — stale or missing effect basis is a typed refusal; gap recorded (U3) | **APPROVED 2026-10-19** | 2.5 | No | Approve | Adapter re-checks at execution: no declared bound, U3 stays unmeasured |
| **D7** | O11 — counterfactual replay in V1 | OPEN (product) | 4.7 | No (before Phase 3) | Yes: it is how a correction is shown to fix its case, and the unoccupied position the Brief found (`m-brief` 36) | Defer: the correction loop has no proof of effect |
| **D8** | Who adjudicates sampled refusals, and where (UX gap 15) | OPEN (product) | 7.8 | No (before Phase 5) | In V1, adjudication outside the operator surface by the platform developer over the 4.4 queue, since Activity holds divergences only (`m-ux` 87) | The operator adjudicates in Activity: needs a UX amendment and adds a non-divergence item to the list |
| **D9** | A rollback action on the operator surface (UX gap 16) | OPEN (product) | 7.7 | No (before Phase 5) | Offer "return to the previous version" at the approval moment, recorded like any promotion; amend EXPERIENCE.md through `bmad-ux` | Developer-only rollback in V1: an operator cannot undo a bad change themselves |
| **D10** | Mailbox provider, credentials and authorisation; where the escalation address is declared (UX gap 3, open question 4) | OPEN (dependency) | 8.1, 8.5, 8.6 | No (before Phase 6) | Provider-agnostic IMAP/SMTP; keep the address in the specification, as the Phase 1 validator already requires (`test_missing_escalation_destination_blocks`) | Declare the address at mailbox connection: one less authoring question, but validation cannot check it |
| **D11** | What makes a divergence *material* (Amendment 1; open question 3) | OPEN (product, deliberately upstream) | 8.7 | No (before Phase 6) | A specification defect or correction on a capability whose declared consequence class reaches a customer or costs money (FR52 data; no severity model) | Every specification defect is material: simplest, possibly noisy |
| **D12** | What the operator sees when an escalation email is undeliverable (UX gap 19) | OPEN (product) | 8.5 (last AC) | No (before Phase 6) | An Activity item in the existing class "Something on our side failed", naming the interaction | A status-line state: more visible, but the status line describes the Agent, not one interaction |
| **D13** | One real business (FR92); two or three operator conversations (FR94) | Human action | 9.7, 9.8 (and recommended before 5.3) | No — but 9.8 should start now | Start the conversations now; they test A4 before the Builder is designed | Defer: the Builder is designed against no real operator |
| **D14** | Architecture Spine amendments S1–S4 answering UX contract gaps 4, 5, 12, 14 (EXPERIENCE.md: "raise each with the owning document") | PROPOSED (architecture) | 3.3, 4.1, 7.1, 7.2, 7.3 (criteria) | No | Wording approved by the user and applied 2026-10-16: Spine AD-26–AD-29 (S1 as an operator-triggered declared safety halt) and PRD §14 A7; decision status pending the user's confirmation | — |
| **D15** | PRD amendments A4–A6 answering UX contract gaps 10, 13, 17 | PROPOSED (product) | 3.3, 4.5 (one criterion), 5.2 | No | Wording approved by the user and applied 2026-10-16: PRD §14 A4–A6; decision status pending the user's confirmation | — |

Not gates, recorded for completeness: **O1** (who may approve) — UX resolved it for V1 as "the operator is the approver; approval does not determine validity" (UX gap 7, register S-08); Story 3.2 implements it. The **web stack** for Epics 6–7 and the **build order** of the four exemplars (Story 9.2) are technical choices, recorded in the register when made. The UX contract gaps 4, 5, 10, 12, 13, 14 and 17 are **not** technical choices: they go to their owning documents through gates D14 and D15 (2026-10-15); their wording was approved and applied on 2026-10-16, and both gates stay PROPOSED until the user confirms the decisions.

## 7. Risks carried

- **Pending episodes are invisible to the operator by approved design** (no list of all interactions, `m-ux` 87). The approved mitigation is FR60's own: a declared deadline's expiry is an external event that resumes the episode and leaves the next step to the Agent, which can escalate by email (FR103). Story 1.10. Revision 3's mitigation — recording a lapsed pending as a divergence item — is withdrawn: it would add a divergence source FR77, FR108 and FR115 do not define.
- **The proof gate can fail.** If the nine-axis comparison shows a material problem, the evidence and the decision required are written up and escalated — the architecture is not changed on preference.
- **Prose that asserts a business fact without a typed claim** is not caught deterministically; it is measured (NFR6), never claimed as enforced.
- The legacy voice product continues to exist alongside `studio/`; `CLAUDE.md` now scopes the rules (its "Current work" section).
- **Everything since HEAD `dcc2860` is untracked** — `studio/`, the planning set, the BMAD epics and sprint files. Gate D3.
- **The epic structure is not yet approved by the user.** `epics.md` is `status: draft` until the user approves the epic list (BMAD step 2) and completes the workflow (step 4).

## 8. Verification discipline for every phase

The standing acceptance criteria every story inherits are stated once, in `epics.md` (*Story conventions*). In summary: `python -m pytest studio/tests -q` (new) plus the existing three commands (`builder_platform/tests`, `claude_plugin/tests`, three `selftest.py`) stay green; mock mode only unless the user approves a live run; every new safety check is proven to fire by injecting its violation and proven non-vacuous by a disabled-check test; System Frame (global manual §1.7) answered in the phase handoff; clean-checkout run before any commit is called green.

## 9. Sources of truth

Each kind of information has exactly one home. Other documents refer to it; they do not restate it.

| Information | Home | Updated by |
| --- | --- | --- |
| Product and architecture decisions (approved) | Brief, PRD, Architecture Spine, UX spines under `_bmad-output/planning-artifacts/` (final; not rewritten) | BMAD workflows only (`bmad-prd`, `bmad-architecture`, `bmad-ux`, `bmad-correct-course`) |
| Decision status (APPROVED / PROPOSED / OPEN / SUPERSEDED) and implementation status per decision | `BMAD-DECISION-REGISTER.md` | each session that changes a status |
| Program: phases, order, technical choices, decision gates, risks | this file | when the program changes |
| Epics, stories, acceptance criteria, per-requirement trace | `_bmad-output/planning-artifacts/epics.md` | `bmad-create-epics-and-stories`; trace regenerated with `tools/trace_epics.py` |
| Sprint state per story | `_bmad-output/implementation-artifacts/sprint-status.yaml` | `bmad-sprint-planning` (generate), `bmad-build` (per story) |
| Verification evidence (commands run, results) | `IMPLEMENTATION-STATE.md` §0 | at the end of each phase or sprint |
| Proof-gate comparison | `PROOF-GATE.md` | Story 1.9 |
| Engine-leak classification rules and the leak log (FR89) | `ENGINE-LEAK-LOG.md` | each business build (Stories 2.6, 9.2–9.5); rules changed only by dated amendment |
| Session handoff | `HANDOFF.md` | at the end of each session |
