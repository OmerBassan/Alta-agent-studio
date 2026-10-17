# IMPLEMENTATION PROGRAM — Agent Studio V1

Revision 3, 2026-10-13. Supersedes revision 2's "next-phase plan".
Mandate (user, 2026-10-13): *implement the product and architecture decisions already made through BMAD; treat approved decisions as implementation commitments; implement the intended product including UX; use technical experiments to unblock implementation, not as the objective; execute phase by phase.* IDs (V-, C-, B-, S-, A-, K-, E-, D-) refer to [BMAD-DECISION-REGISTER.md](BMAD-DECISION-REGISTER.md); FR/NFR/EX/O to the PRD; AD to the Architecture Spine.

**Status of this document:** the program is the working plan. Approved BMAD decisions are commitments, not proposals. Technical choices I make inside the approved constraints are recorded in §3 and are revisable on evidence. Nothing is committed to git without the user's authorization.

---

## 1. What changed from revision 2, and why

Revision 2 treated six items as user decisions. Under the mandate and the established precedence (approved decisions and explicit amendments win; later approved decisions supersede earlier ones), four of them are already decided by approved sources:

| Rev. 2 question | Resolution by precedence | Source |
| --- | --- | --- |
| Q1 Runtime-first vs Builder-first | Not a product decision — it is sequencing. The Builder is in V1 scope (B-00, `m-brief` 52) and is planned at full approved scope (Phase 4). Ordering is a technical dependency call: the Builder's output is the specification, so the specification and the runtime that executes it come first. | `m-brief` 52; FR9; AD-4 |
| Q2 Episode list for the operator | UX decided, by operator ruling, that the interaction viewer opens only from Activity and that there is no list of all interactions (`m-ux` 85, 87). The PRD review's F3.1 is a reviewer finding, not an approved requirement. **Implemented as approved**; the residual risk (a lapsed pending episode is invisible) is recorded in §7 and addressed inside the approved design by surfacing lapsed pendings as divergence items. | `m-ux` 85, 87; FR79–80 |
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
  evaluation/  Invariant checks, business criteria, divergence, corrections, replay          (Phase 3)
  web/         The operator experience: Build and Run surfaces, Ledger design               (Phase 5)
  businesses/  Business specifications and knowledge (dental, brewery events, garden centre, gym)
  tests/
```

| Phase | Delivers (product capability) | Epics | Proof-gate role |
| --- | --- | --- | --- |
| **1** | **Runtime foundation**: one Business Specification compiled by the Core into three projections; the model-in-charge loop; closed request taxonomy with every kind authorized and journaled; tenant-scoped durable episodes and evidence; confirmations, idempotency, read-back verification; guards, two exits, terminal notice, disclosure; suspend; resolution envelope and validation; two businesses (dental, brewery events). | E1 (core), E3 (validation core), E4, E5, E7, E8, E9 | **The proof gate is run inside this phase** as a vertical slice: the nine-axis comparison against the 15-node system is a deliverable of 1.4. No throwaway code. |
| **2** | **Knowledge and grounding**: version-pinned sources, precedence, retrieval as a decided action, Core-issued provenance for every authoritative item, two knowledge tiers, freshness per contract; garden centre. | E6 | — |
| **3** | **Change safety and the improvement loop (backend)**: immutable versions, promotion gated by the validation suite and recorded approval, rollback, version pinning per episode; per-episode evaluation computed from the record; divergence classification and backlog; human corrections; refusal sampling; replay. | E3, E9, E10 (backend) | — |
| **4** | **The Builder**: agent-driven elicitation from conversation and material to specification + knowledge; contradictions, defects, process re-derivation; correction as conversation + confirmed diff; revision of a promoted specification; burden + yield; seeded fixture. | E2 | — |
| **5** | **The operator experience** (UX spines): cold-start workspace, co-present Conversation + Understanding, correction diff, validation and approval, Activity with status line, interaction viewer, Suspend, closed vocabulary, Ledger visual system, WCAG 2.2 AA, phone-usable Run surfaces. | E10 (surfaces) + UX | — |
| **6** | **Email channel and go-live**: inbound email adapter with FR114 hazards, built against captured traffic; disclosure; escalation email (+ material divergence, Amendment 1); connect mailbox as the go-live act; mailbox status. | E11 | — |
| **7** | **Generalisation programme**: the four exemplars built through the Builder; engine-leak log, resolution strain, setup effort, validity floor; usefulness test with one real business. | E12 | — |

Phase 1 is split into four reviewable steps: **1.1** specification (schema, loader, validation, compiler) · **1.2** Core and durable store · **1.3** agent boundary, channel harness, businesses, end-to-end scenarios · **1.4** proof-gate report and handoff.

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

### 3.1 Phase 2 — findings and proposed choices (**PROPOSED, NOT APPROVED**; recorded 2026-10-14)

**Status:** proposal for the user's review. The user has **not** authorized Phase 2; nothing below is implemented. T9–T12 are not yet in force and do not join T1–T8 until the user approves.

**Findings from the Phase 1 code (verified by reading it on 2026-10-14):**

| # | Finding | Evidence | Requirement affected |
| --- | --- | --- | --- |
| P2-F1 | Retrieval is nearly vacuous. A reference for every source section is issued at episode start, and every reference's full text is in the agent's view on every turn, so the agent never needs to `retrieve`. Works only because sources are tiny (19 lines each). | `studio/core/harness.py` `_start_episode` (issues all `compiled.context.items`), the agent-view assembly (`references` with `text`) | AD-8, FR32/33 for retrieval, scalability |
| P2-F2 | FR37 and resume-at-pinned-version break after a restart that follows a knowledge edit. `SpecRegistry` is in memory and rebuilt from files; no source text is stored durably. | `studio/core/harness.py` `SpecRegistry`; `provenance` table stores ids and versions, not text | FR37, FR62, AD-11 |
| P2-F3 | Precedence is only a sort tie-breaker; no conflict between sources is detected or resolved. | `_retrieve` sort key `(−score, precedence, ref)` | FR31 |
| P2-F4 | Freshness is a label recorded on read evidence; nothing enforces it. U3/G45 (HIGH, unapplied) — the premise that effect-gating reads cluster near episode end — is still unmeasured. | `_read` evidence `"freshness": cap.freshness` | FR35, register §11 U3 |
| P2-F5 | The garden centre needs no new Core feature: conclusions, the liability class, `operator_approval`, `suspend`/pending on a named input and multiple goals all exist. It is a clean test of business three. | `studio/spec/model.py` classes; `harness.py` suspend path | FR89, E-05 |

**Proposed steps:** 2.1 `studio/knowledge/` (content-addressed source store, `Retriever` port, lexical default, ingestion contract for Markdown/plain text; source text snapshotted into the episode store at pinning) · 2.2 retrieval as a decided action (the specification projection stays in context; source material only via `retrieve`, references issued at retrieval; evidence records source, version and locator per item) · 2.3 precedence and freshness · 2.4 garden centre (spec and guides from `spec-stress-test.md` §3, simulated till-system lookup and stock adapters, scenarios incl. the lavender case: care advice marked as general knowledge, guarantee position stated as undetermined, claim deferred not refused, no conclusion of neglect) · 2.5 phase report. Each new check proven by injection and by mutation.

**Proposed technical choices:**

| # | Choice | Strongest alternative | Reason | Cost |
| --- | --- | --- | --- | --- |
| T9 | Source material reaches the agent only through `retrieve`; the specification projection stays in context. | Keep all material in context, issued at start | Spine defers context assembly as "measured, not designed"; the current form makes AD-8 hollow and does not scale | One extra model call whenever the agent retrieves; **changes proof-gate axes 3–4** |
| T10 | Lexical retrieval behind a `Retriever` port; an embeddings adapter over `/v1/embeddings` (K-08) only if garden-centre scenarios show recall misses | Embeddings now | K-03 defers retrieval architecture; E-07 measure before optimizing | Possible recall gaps until measured |
| T11 | A conflict is a same-heading section in sources of different precedence; the lower is returned marked superseded and citing it is refused. The specification outranks every source. | Agent judges conflicts; sources declare covered topics | Semantic conflict detection cannot be deterministic; the Builder surfaces contradictions at build time (FR5) | Conflicts under different headings are not caught at runtime |
| T12 | An effect contract may name the read it depends on and that read's maximum age; a missing or stale basis is a typed refusal, never a Core-scheduled read. The read-to-effect gap is recorded (U3). | Adapter re-checks at execution, no declared bound | FR35 forbids the Core sequencing a read before an act; a typed refusal constrains rather than decides (AD-1 test) | Agent must handle one more refusal reason |

**Not in Phase 2:** PDF/material ingestion (FR2, Phase 4) · durable immutable specification versions (Phase 3; Phase 2 does sources only) · the NFR6 faithfulness measurement (Phase 3; Phase 2 records its inputs) · the gym (Phase 7).

**Unresolved, needs the user:**

1. **Live proof-gate timing.** Recommendation: run it once, after Phase 2, because T9 changes model calls per turn and a run now measures a context design Phase 2 replaces. **This recommendation conflicts with an approved source:** PRD §12 (`prd.md` line 665) says "The proof gate (§7.5) sits in front of E4–E9", and Phase 2 is E6; `m-arch` 47 requires the gate "before committing the whole runtime". Phase 1 already built E4/E5/E7/E8/E9 alongside the gate (§2, "run inside this phase as a vertical slice"), with axes 3–4 still pending. So "after Phase 2" is **not confirmed** — it needs the user's ruling. Alternative that honours the text: run now on the Phase 1 runtime (≤ US$0.25) and again after Phase 2 for a before/after.
2. **Approval of T9–T12**, T9 in particular because it is the one with a visible behaviour effect (answers from source material cost a retrieval call).
3. **Authorization to start Phase 2** — withheld pending the user's reconciliation with the full BMAD implementation plan.

---

## 4. Traceability matrix — every approved V1 requirement

**Progress marks on the Req cell:** ✓ delivered and verified by the named test in Phase 1 · ◐ partly delivered (the remaining part is in the phase shown). Evidence for every mark: IMPLEMENTATION-STATE §0.

Columns: **Now** = implementation status at program start (evidence in IMPLEMENTATION-STATE) — `I` implemented in the new product, `P` partial or only in the legacy voice engine, `—` absent. **Ph** = phase that delivers it. **Verification** = the test or demonstration that proves it. Rows marked ✓ are delivered and verified (updated as phases complete; see IMPLEMENTATION-STATE §0 for the evidence).

### 4.1 Builder and elicitation (E2)

| Req | Requirement (short) | Now | Ph | Verification |
| --- | --- | --- | --- | --- |
| FR1 | Open invitation; never a form or fixed question set | — | 4 | Builder session test: first turn is the invitation; no question bank exists in code |
| FR2 | Accepts the operator's own material | — | 4 | Ingestion tests per format (text, markdown, PDF text); unreadable → FR117 outcome |
| FR3 | Adaptive clarification; no fixed questionnaire | — | 4 | Fixture: question count varies with withheld rules; no static list |
| FR4 | Interviews for prohibitions, thresholds, exceptions, authority limits, always-escalate | — | 4 | Seeded fixture recovery (FR100) |
| FR5 | Surfaces contradictions (source↔source, source↔operator) | — | 4 | Fixture with two conflicting sources → surfaced, not silently chosen |
| FR6 | Records a specification defect rather than inventing a default | — | 4 | Unresolvable item → recorded defect + "Not established" |
| FR7 | Probes printed vs practised policy | — | 4 | Fixture rule present in material but contradicted in practice → probed |
| FR8 | Optional starting points — **declined for V1** (B-06) | n/a | — | Not built, by approved UX override |
| FR9 | Produces Business Specification and Business Knowledge | — | 4 | Session output loads through `studio.spec` and passes validation |
| FR10 | Builder is agent-driven | — | 4 | Builder runs on the same agent boundary (AD-14) |
| FR11 | Recorded, attributable, blocking human approval | — | 3 | Promotion without approval record refused; approval stored with approver and time |
| FR12 | Burden instrumented (time to passing suite, sources count) | — | 4 | Session record carries both |
| FR99 | Yield instrumented with burden | — | 4 | Session record: rules recovered by interview, contradictions, defects |
| FR100 | Seeded business fixture | — | 4 | Recovered / invented / silently-defaulted counts reported |
| FR104 | Narrated process re-derived; no ordering persisted | — | 4 | Narrated sequence → specification with no ordering; validator passes |
| FR117 | Builder failures are distinguishable outcomes | — | 4 | Unreadable source, abandoned session, contradicting new source each produce a stated outcome |
| FR101 | Revise a promoted spec through the Builder conversation | — | 4 | New version from a correction conversation passes the same gate |

### 4.2 Business Specification (E1)

| Req | Requirement | Now | Ph | Verification |
| --- | --- | --- | --- | --- |
| FR13 / AD-4 ◐ | One artifact; Core compiles context, capability surface and policy; Builder never compiles; compiler version pinned | P | 1.1 | Compiler unit tests; projections all derive from one loaded spec; compiler version recorded on every episode |
| FR14 / EX1–EX17 ✓ | Every expression area addressable; empty area = recorded absence | P | 1.1 | Schema test enumerates all 17 areas; a missing area reports "not established", never a default |
| FR15 ✓ | Obligations distinct from diagnostic inputs | — | 1.1 | Schema keeps them separate per goal; obligations enforced, diagnostics not |
| FR105 / AD-19 ✓ | Goals and outstanding obligations are typed Core state; holding ≠ deciding | — | 1.2 | Episode state test; Core asserts obligations at effect and resolution, never selects a goal |
| FR106 ✓ | Waivers explicit, attributable, recorded | — | 1.2 | Waiver requires a declared waiving authority; recorded as evidence |
| FR16 ✓ | Authority classes informational / liability / state-changing, separately gated | P | 1.1–1.2 | Each class gated differently in policy tests |
| FR17 ✓ | Cause may be inferred while fault may not be determined | — | 1.2 | Respond claiming a forbidden conclusion refused; a permitted one passes |
| FR18 / FR24 ✓ | Ordering unexpressible; validator rejects sequencing with a reason | — | 1.1 | Closed schema rejects ordering keys; sequencing prose rejected with a readable reason; array order does not change the version |
| FR19 ✓ | Human-readable, diffable, neither prompt nor code | — | 1.1 | TOML artifacts; deterministic canonical form |
| FR20 / EX16 ◐ | Evaluation criteria inside the spec | — | 1.1 / 3 | Criteria in schema (1.1); evaluated per episode (3) |
| FR21 ◐ | Versioned; promoted version immutable | P | 1.1 / 3 | Content-addressed version (1.1); immutability enforced by the registry (3) |

### 4.3 Validation, promotion, rollback (E3)

| Req | Requirement | Now | Ph | Verification |
| --- | --- | --- | --- | --- |
| FR22 / FR25 / FR95 ◐ | One platform-owned, spec-derived gate before promotion and deployment; invariants block; business criteria warn unless declared blocking; never stubbed | P | 1.1 / 3 | Suite runs over every business spec; blocking vs warning findings typed |
| FR23 ✓ | Granted-but-always-denied detected and blocks | — | 1.1 | Injected always-deny rule → blocking finding |
| FR26 | Rollback = selecting an earlier version | — | 3 | Pointer move test with replay |
| FR27 / AD-11 / NFR7 ◐ | Episode keeps the version pinned at start | — | 1.2 / 3 | Episode stores spec version + compiler version; promotion mid-episode does not change it |
| FR28 | Promotion reviewable, revertable, attributable | — | 3 | Promotion record test |
| FR29 | No silent behaviour mutation | — | 3 | Only promotion changes the live version |
| FR96 ◐ | Every safety check before mutation and proven non-vacuous | — | every | Each check has a test that injects the violation and a test that it fails when the check is disabled |
| AD-23 / NFR8 | Promotion versioned and hard-gated | — | 3 | — |

### 4.4 Knowledge and grounding (E6)

| Req | Requirement | Now | Ph | Verification |
| --- | --- | --- | --- | --- |
| FR30 / AD-8 ◐ | Sources pinned to versions | P | 1.1 / 2 | Source content hash part of the spec version (1.1); per-source versions on provenance (2) |
| FR31 | Declared precedence among sources | — | 2 | Conflicting sources resolved by declared precedence |
| FR32 / FR33 / AD-7 / NFR5 ◐ | Authoritative claims carry Core-issued provenance bound to tenant, source, version, locator; unissued/altered/cross-tenant refused before egress | — | 1.2 (spec projection) / 2 (retrieval) | Forged, altered, other-episode and other-tenant references each refused |
| FR34 ✓ | General knowledge marked, per-business switch | — | 1.2 | Claim of kind general refused when disabled; marked in evidence when enabled |
| FR35 | Freshness per read and per contract | — | 2 | Capability contract declares freshness; effect-gating read must be fresh |
| FR36 | No system of record owned | I (by design) | 1 | Adapters read and write external systems; Core stores evidence only |
| FR37 | Every answer reconstructible against exact source versions | — | 2 | Episode record replays the context items used |
| NFR6 | Faithfulness measured against a threshold, never guaranteed | — | 3 | Evaluation reports a rate; no guarantee claimed |

### 4.5 Agent reasoning inside the Core boundary (E4, E5)

| Req | Requirement | Now | Ph | Verification |
| --- | --- | --- | --- | --- |
| FR38 / FR39 / AD-1 ✓ | Agent decides the next step; Core never selects it | — | 1.2–1.3 | Core code has no next-step selection; loop test with scripted agents choosing different paths through identical Core |
| FR40 / AD-2 ✓ | Closed seven-kind taxonomy; every kind authorized and journaled, reads included; no precedence | — | 1.2 | Each kind authorized and journaled; unknown kind rejected at parse |
| FR41 ✓ | Agent never contacts anything outside the Core | — | 1.2 | Agent port has no adapter/store access; adapters reachable only through Core |
| FR42 ◐ | Five generic guardrails, zero configuration | P | 1.2 | One test per guardrail with no spec configuration |
| FR43 / AD-3 ✓ | Constraints enforced by the Core, never by prompt | P | 1.2 | Misbehaving scripted agent tests |
| FR44 / AD-21 ✓ | Guards before goal recognition; model detection allowed; binding verdict; two outcomes; never composes a reply | — | 1.2 | Guard fires before the agent is invoked; halt or typed constraint only |
| FR45 / AD-18 ✓ | Exactly two exits | — | 1.2 | Every Core outcome is a typed result or a declared halt |
| FR111 ✓ | Terminal notice on halt, emitted by the Core | — | 1.2 | Halt → requester receives the business's notice |
| FR46 ✓ | Typed errors; degraded distinguishable by the caller | P | 1.2 | Adapter timeout → typed platform_error result, never a default |
| FR47 ✓ | Agent owns escalation; platform returns typed refusal | — | 1.2 | No Core path creates an escalation |
| FR48 ✓ | Rules silent → Agent escalates; gap recorded as spec defect | — | 1.2 | Escalation with reason `rules_silent` records a spec_defect |
| FR49 ✓ | Goals only from the declared set | — | 1.2 | Undeclared goal id refused |
| FR50 ✓ | Multi-goal, one active, explicit park and resume | — | 1.2 | Goal switch recorded; parked goal resumable |
| FR107 ✓ | Loop termination bound + stall detector with a wired outcome | P | 1.2 | Budget and repetition each end in a declared halt with notices (T5) |
| AD-14 / NFR12 ◐ | Runtime boundary owned; provider-agnostic | P | 1.3 | No vendor import in Core/Spec; model configured only by env |

### 4.6 Capabilities and extensions (E7)

| Req | Requirement | Now | Ph | Verification |
| --- | --- | --- | --- | --- |
| FR51 ✓ | Verb-first capability contract incl. success evidence; no evidence definition = not shippable | P | 1.1 | Validator blocks a capability without success evidence |
| FR52 ◐ | Consequence class declared and visible | — | 1.1 / 5 | Schema field (1.1); shown to operator (5) |
| FR53 ✓ | Confirmation recorded before a confirm-required effect | P | 1.2 | Effect without the Core confirmation record refused; forged, replayed, mutated and cross-episode confirmations refused |
| FR109 ✓ | Authority established, not assumed from the channel | — | 1.1–1.2 | Validator blocks a state-changing capability without a declared authority basis; effect refused until basis established |
| FR54 ✓ | Retry eligibility visible; no key → not eligible | — | 1.1 | Compiled policy exposes eligibility |
| FR55 / AD-10 / NFR2 ✓ | Core-issued tenant+episode idempotency key; no duplicate effect; no false suppression | — | 1.2 | Retried effect executes once; same payload in another tenant/episode executes |
| FR56 / AD-9 ✓ | Core contract → adapter → extension | — | 1.2 | Adapter port; Core imports no vendor |
| FR57 / AD-24 / NFR11 ◐ | Credentials never in state, evidence, context or prompt | — | 1.2 / 6 | Sentinel credential never appears in the store or prompts |
| FR58 / AD-15 ✓ | Configuration never changes Core semantics | — | 1.1 | Closed schema; no executable fields |
| FR59 / FR116 ◐ | Custom code only as a leaf; three-level variation recorded | — | 1.3 / 7 | Adapters are leaves; leak log (7) |
| FR97 ✓ | No blocking on the request path; per-client timeouts | P | 1.2 | Adapter calls bounded by timeout; a hung adapter yields a typed platform_error |

### 4.7 Episode lifecycle and continuity (E8)

| Req | Requirement | Now | Ph | Verification |
| --- | --- | --- | --- | --- |
| FR60 ✓ | Lifecycle exactly active / pending (named input) / closed | — | 1.2 | No other state accepted by the store |
| FR61 / AD-22 ✓ | Initiated or resumed only by inbound or external event | — | 1.2 | No Core path initiates an episode |
| FR62 ✓ | Resume with state, evidence, version, context intact | — | 1.2 | Pending → later inbound resumes with pinned version |
| FR63 ✓ | Late result never mutates the resolution | — | 1.2 | Result after close recorded as late |
| FR64 / AD-12 / NFR1 ◐ | Survives process failure; nothing un-journaled read | — | 1.2 | New process resumes from the store with no duplicate effect |
| FR65 / AD-13 / NFR9 ✓ | Core sole writer; concurrent inbound serialized | — | 1.2 | Concurrent turns on one episode serialized (lock test) |
| FR66 ✓ | No cross-episode memory | I (by design) | 1.2 | Context built only from the episode |
| FR67 ✓ | Lifecycle says nothing about outcome | — | 1.2 | Resolution stored separately from lifecycle |

### 4.8 Resolution and evidence (E9)

| Req | Requirement | Now | Ph | Verification |
| --- | --- | --- | --- | --- |
| FR68 / AD-20 ✓ | Fixed resolution envelope (goal, served, authority, evidence, payload) | — | 1.2 | Envelope type; enumeration deferred (O4) |
| FR69 ✓ | Escalation may be a declared success | — | 1.2 | Spec flags reason classes as success |
| FR70 / AD-6 ✓ | Only the Core attests effects; typed evidence | P | 1.2 | Evidence written only by Core; typed records |
| FR71 ✓ | Resolution asserting an effect without a Core record is invalid | — | 1.2 | Scripted agent claims "booked" with no record → refused |
| FR72 ✓ | Action record ≠ resolution | — | 1.2 | Separate tables and types |
| FR73 / NFR13 / NFR14 ◐ | Durable evidence incl. model calls, tool calls, tokens, cost | P | 1.2–1.3 | Episode record carries all; cost from configured prices |
| FR74 ✓ | Every escalation records its reason class | — | 1.2 | — |
| FR75 / AD-25 / NFR10 ✓ | Evidence addressable and removable by tenant, episode, age | — | 1.2 | Delete-by-tenant/episode/age test; executor policy deferred |
| FR76 | Per-episode and per-business criteria computable from the record | — | 3 | Evaluation reads only the store |
| FR102 | Human corrections as first-class records | — | 3 | — |
| NFR3 / AD-17 ✓ | Tenant on every record; cross-tenant rejected, not filtered | — | 1.2 | Cross-tenant reference refused, never an empty result |
| NFR4 ✓ | Every request kind authorized and journaled; only Core authors evidence; every denial classified | — | 1.2 | — |
| NFR16 ◐ | One correlation id per episode on every record, reportable | P | 1.2 | Every record carries the episode id; a reference code shown on platform errors (5) |
| NFR17 ◐ | Config validated at startup; health asserts what a real request needs | P | 1.3 / 5 | Startup validation of spec and model config; health endpoint test (5) |
| NFR18 ✓ | UTC throughout | — | 1.2 | — |

### 4.9 Divergence and operator surface (E10)

| Req | Requirement | Now | Ph | Verification |
| --- | --- | --- | --- | --- |
| FR77 / AD-5 ✓ | Every denial classified exactly once (spec_defect / business_refusal / platform_error) | P | 1.2 | Classification on every refusal |
| FR78 | Only spec defects enter the backlog | — | 3 | — |
| FR108 | Corrections are a divergence source | — | 3 | — |
| FR115 | Business refusals sampled for adjudication at a business-set rate | — | 3 | Sampling rate in spec; sampled items queued |
| FR79 | Divergence list is the primary surface | — | 5 | UX acceptance |
| FR80 | Open one episode (interaction viewer) | — | 5 | UX acceptance |
| FR81 | Closed vocabulary for every operator-visible status | — | 3 / 5 | Vocabulary module; UI uses only it |
| FR82 / FR101 | Divergence actionable through the Builder conversation | — | 4–5 | "This was wrong" opens the correction conversation |
| FR110 ◐ | Immediate suspend, incl. effects only; recorded; in-flight episodes end recorded | — | 1.2 / 5 | Flags in Core (1.2); one-press UI (5) |

### 4.10 Channel (E11)

| Req | Requirement | Now | Ph | Verification |
| --- | --- | --- | --- | --- |
| FR83 / AD-16 ✓ | Agent and Core never learn the channel | — | 1.3 | Core types carry no channel fields |
| FR84 | One adapter: inbound email / messaging, ingress and egress | — | 6 | — |
| FR85 ◐ | Adapter replaceable without touching behaviour | — | 1.3 / 6 | Harness and email adapters share one port |
| FR113 | Adapter shapes writing for the channel | — | 6 | — |
| FR86 ✓ | Correlation to episode; explicit join key | — | 1.2 / 6 | Channel conversation key → episode |
| FR87 ✓ | Duplicate and corrected re-sends do not create a second episode or effect | — | 1.2 | Same message id processed once |
| FR98 | Built against captured real traffic, pinned by tests | — | 6 | Captured fixtures |
| FR114 | Threading, recipients, attachments, bounces, auto-responder loops | — | 6 | One pinned test each |
| FR103 ◐ | Escalation delivered to the declared destination with reason and link | — | 1.2 (outbox) / 6 (email) | — |
| FR112 ✓ | Disclosure in the first message | — | 1.2 | First egress of every episode carries the business's disclosure |

### 4.11 Generalisation programme (E12)

| Req | Requirement | Now | Ph | Verification |
| --- | --- | --- | --- | --- |
| FR88 | Four exemplars built through the Builder | — | 7 | — |
| FR89 / FR116 ◐ | Engine leaks recorded and classified | — | 1.3 → 7 | Leak log started in Phase 1 (second business) |
| FR90 | Resolution-model strain | — | 7 | — |
| FR91 | Setup effort from Builder burden | — | 7 | — |
| FR92 | One business real end to end | — | 7 | **User dependency** (§6) |
| FR93 | Validity floor | — | 3 / 7 | — |
| FR94 | Two or three operator conversations | — | parallel | **User action** (§6) |

### 4.12 Architecture decisions without a single FR

AD-1–AD-25 are mapped through the rows above. Additional: **AD-12** step boundaries carry no behavioural meaning (journal is append-only; nothing reads step order as permission) — Ph 1.2 · **AD-13** episode creation by the Core on adapter request — 1.2 · **AD-14** tiering expressible at the boundary (per-role model variables) — 1.3 · **AD-25** retention executor deferred — post-V1 (§5).

### 4.13 UX requirements and journeys (EXPERIENCE.md, DESIGN.md) — all Phase 5 unless noted

| UX requirement | Ph | Verification |
| --- | --- | --- |
| Locked mental model: Conversation mechanism · Understanding object · Activity review; two destinations, no further navigation | 5 | Route inventory test |
| Cold-start workspace: one open prompt, optional material, no funnel or templates | 4–5 | — |
| Co-present Conversation + live Understanding, framed as "what the Builder currently understands" | 5 | — |
| Understanding: five sections over EX1–17; four item states; "Not established" first-class; no sequencing affordances | 5 | DOM test: no arrows/steps/progress |
| Correction diff: Before / After / Also affected / Unchanged; accept / push back | 4–5 | Flow 2 acceptance |
| Validation result at approval; blocking vs not blocking; no override; approval ≠ validity | 3 / 5 | — |
| Connect mailbox = go-live act | 6 | Flow 1 acceptance |
| Activity: three classes as kinds; class + label + one-line request; status line always above | 5 | — |
| Interaction viewer: email, reply, basis; no generated explanations; "This was wrong" | 5 | — |
| Suspend / Stop actions only / resume; announced; failure stated | 5 | Flow 5 acceptance |
| Escalation email as a designed surface | 6 | Flow 4 acceptance |
| Closed vocabulary (UX seed list) | 3 / 5 | — |
| Degraded and failure states table | 5 | One test per state |
| Ledger visual system (DESIGN.md tokens) | 5 | Token conformance |
| WCAG 2.2 AA behavioural floor; keyboard-complete; status announcements; 320 px reflow; targets | 5 | axe + keyboard walkthrough |
| Responsive: Activity, viewer and Suspend fully usable on a phone | 5 | — |
| **Journeys** Flow 1 cold start → live · Flow 2 divergence → new version · Flow 3 permitted-confident-wrong · Flow 4 escalation · Flow 5 suspend | 5–6 | End-to-end acceptance scripts, one per flow |

---

## 5. Post-V1, preserved and not built

Retention policy and deletion executor (AD-25 deferred) · policy-engine technology · durability engine choice beyond the fallback floor · model routing policy (tiering is expressible; policy measured) · resolution-kind enumeration (O4, emerges from episodes) · multi-tenant hosting, billing, packaging (O8) · extension marketplace · domain safety packs (O9) · escalation routing beyond one address (O2) · jurisdictional disclosure wording (O3) · spend ceiling (O6) · voice as a later channel adapter (O10) · starter templates (declined for V1, reconsiderable as an onboarding optimisation) · typed decision models (DL-041) · the faithfulness threshold value (O5).

## 6. Items needing the user, and why each is a dependency rather than a reopened decision

| When | Item | Kind | Recommendation |
| --- | --- | --- | --- |
| Phase 1.4 | **Approval to spend on one live-model run** of the new runtime, so the proof gate's model-call and latency axes have real numbers. Standing rule: ask before any live call (LATEST-HANDOFF §2). | Permission, and now a timing question (§3.1, unresolved 1) | Reuse `gpt-6-luna` at the settled settings and the US$0.50 ceiling (DL-034/035/037). **Proposed 2026-10-14:** run after Phase 2, *subject to the user confirming that PRD §12 ("proof gate sits in front of E4–E9") does not require it earlier* — see §3.1. |
| Phase 3 | **Counterfactual replay in V1** (O11) | Open product item | Yes — it is how a correction is verified. |
| Phase 6 | A mailbox to connect and its credentials | Dependency | Generic IMAP/SMTP, provider-agnostic. |
| Phase 7 | **One real business** with its operator, material and inbound mail (FR92); **2–3 operator conversations** (FR94) | Human action | Can start now, in parallel. |
| Any | Authorization to commit | Permission | Commit per phase after review. |

## 7. Risks carried

- **Pending episodes are invisible to the operator by approved design** (no list of all interactions). Inside the approved design, Phase 3 records a pending episode whose declared deadline has passed as a divergence item, so it reaches Activity; that is a mitigation, not a list.
- **The proof gate can fail.** If the nine-axis comparison shows a material problem, the evidence and the decision required are written up and escalated — the architecture is not changed on preference.
- **Prose that asserts a business fact without a typed claim** is not caught deterministically; it is measured (NFR6), never claimed as enforced.
- The legacy voice product continues to exist alongside `studio/`; until `CLAUDE.md` is scoped, a session could follow the wrong rules (mitigated in the Phase 1 handoff).

## 8. Verification discipline for every phase

`python -m pytest studio/tests -q` (new) plus the existing three commands (`builder_platform/tests`, `claude_plugin/tests`, three `selftest.py`) stay green; mock mode only unless the user approves a live run; every new safety check is proven to fire by injecting its violation and proven non-vacuous by a disabled-check test; System Frame (global manual §1.7) answered in the phase handoff; clean-checkout run before any commit is called green.
