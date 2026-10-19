# Engine-leak log (FR89)

The single home of the engine-leak classification rules and of the log graded under them (Story 9.1). It succeeds the leak-log table in [PROOF-GATE.md](PROOF-GATE.md), which keeps its original text and now points here.

The rules were written on 2026-10-17, before any Builder-built business (Story 9.2) existed, so that the generalisation measurement of PRD §10.3 is not graded after the fact (PRD review F4.3). Sources: PRD FR89 (the class names), FR116 (the three levels), FR58, FR59, §10.3; Architecture Spine litmus test and AD-18.

**Rules version in force: 1 (2026-10-17).** No amendments yet (§3).

## 1. Rules — version 1, 2026-10-17

### 1.1 What a leak is

- **Business layer:** `studio/businesses/<business>/`, that is, the business's specification and knowledge.
- **Engine:** every path outside the business layer and outside `studio/tests/`. That includes every module under `studio/` (existing or new), the CLI, and dependency manifests (for example `requirements*.txt`, `pyproject.toml`). A change confined to `studio/tests/` changes no runtime behaviour; it is listed in the evidence but is not an engine change.
- **Core vs engine.** The Core (`studio/core`) is the narrower term. "Zero Core changes" (PROOF-GATE.md axis 8, entry 1) and P1 below agree: P1 changed no Core path, only engine paths outside the Core.
- **Leak:** any change to the engine that a business needed. This is PRD §10.3's "every instance where the Core had to change rather than the business layer".
- **One entry per need.** A need is one thing the business required that the engine did not already provide. One need can change several paths, and all of them go in one entry. One change that serves two needs gets two entries, and each names the other in "Shares a change with". The §10.3 trend counts **needs**, so a shared change is never counted twice as one need.
- **Legacy entries (the voice engine in `boilerplate/`).** The business layer is the agent's domain surfaces (`config.py`, `tools.py`, `prompts.py`, `.env`, corpus, README). The engine is every other path: the `ENGINE_FILES` in `builder_platform/builder_core.py` and their copies, and the platform runtime. Step 1 always answers no for a legacy entry. The legacy engine has no simulated system of record: simulated behaviour lives in each agent's `tools.py`, which is business layer, so a change there is already caught at step 0. For step 4, the declared contract is the tool contract in the agent's `tools.py` (the tool functions and `VERIFIERS`), in place of `studio/core/ports.py`.

### 1.2 The steps, in a fixed order

Apply the steps in this order and stop at the **first step that answers yes**. Every step up to and including the deciding one is answered yes or no in the entry, and each answer cites the evidence item it rests on (a path and line, a test, a commit or a diff). When two classes could fit, the earlier test decides, and the entry records why the earlier test answered yes.

Every question is about the change itself: its paths, the contract it touches, the semantics it adds. None is about what the author intended.

**Build start**, used by step 2: for a programme business, the start of the Builder session recorded in that business's session record (Stories 9.2–9.5). For a pre-programme business, the first commit that added the business.

| Step | Question (yes / no) | Yes means |
| --- | --- | --- |
| **0. Scope** | Did any engine path (§1.1) change to meet the need? | No → outcome **no leak**, reason *business layer only*, with the evidence that only the business layer changed. Yes → step 1. |
| **1. Fixture** | Are all the engine changes confined to a simulated system of record (any simulator under `studio/extensions/`) and the wiring that supplies its data, and do they add only data the real external system would hold (FR36: the external system is authoritative), with the adapter's Core-facing contract (`Adapter` and `AdapterResult` in `studio/core/ports.py`: method signatures, operation names, result fields) unchanged? | Yes → outcome **no leak**, reason *fixture data*. No, including a simulator change that alters that contract → step 2. |
| **2. Defect** | Does the change make the engine meet a requirement (FR, NFR, AD, approved decision) or a test that existed **before the build start**, and does that recorded text alone decide the case the build exposed? The answer must cite an evidence item proving the requirement or test existed before the build start (a commit, or a dated file version). | Yes → outcome **defect, not a leak**. It is still logged, and it carries a written justification: why the cited text, on its own, decides the case. No (no such prior requirement, no proof of its date, or the text does not decide the case) → it is a leak; step 3. |
| **3. Test C** | Is every engine line the change adds or alters either (a) a business-specific value (a literal, a table or list entry, a tenant id or business name, or a per-business selection of such a value), or (b) a schema field in `studio/spec/` whose value feeds an evaluation the Core already performed before the change? Equivalently: with the business-specific values removed, is the engine's code path the same for every business as before the change? | Yes → class **should have been configuration**. |
| **4. Test E** | Are all three true: (a) the changed module is reached only through a typed contract declared in `studio/core/ports.py`, existing or added by the change; (b) the module returns data (a value, a verdict, a score, a document), that data returns to the Agent as a typed result (AD-18), and no engine code branches on it to choose what happens next (FR59: a leaf, never control flow); (c) the recorded material of at least one other of the four exemplar businesses (brewery, gym, garden centre, dental; `_bmad-output/planning-artifacts/briefs/brief-AgentStudio-2026-10-07/spec-stress-test.md` counts), named in the entry with a file, needs the same contract (FR116: capability that recurs across businesses)? Build order does not matter for (c). | Yes → class **justifies an extension point**. |
| **5. Test N** | Did test C and test E each answer no, with each no tied to a specific line or path of the change? | Yes → class **genuinely novel**. The entry must also carry the written justification below. No → the entry is **incomplete**: re-run tests C and E with cited lines before any outcome is recorded. |

**Genuinely novel needs a written justification.** It states, against the change, why no configuration surface could have carried the need (test C) and why no declared contract could (test E). The entry also records its **shape**, a fact about the change: either *platform semantics* (the change applies identically to every business and names none; FR58: a new semantic capability is platform work, done once in the Core) or *code for one business*. A genuinely novel entry without the justification is incomplete and cannot be confirmed. This is the guard F4.3 asks for: the third class is reached last, and only through two recorded no answers.

### 1.3 Outcomes, classes and levels

| Outcome | Kind | FR116 level the need belongs at |
| --- | --- | --- |
| No leak (reason: *business layer only* or *fixture data*) | not a leak | configuration (business layer only); the external system of record, FR36 (fixture data) |
| Defect, not a leak | not a leak | the engine failed a requirement it already had |
| **Should have been configuration** | leak (FR89) | configuration |
| **Justifies an extension point** | leak (FR89) | supported extension point |
| **Genuinely novel** | leak (FR89) | custom implementation: neither of the other two levels could carry it |

No other outcome or class exists. **The §10.3 trend counts only judged entries** (Judged by names the user) with one of the three FR89 classes, one count per need (§1.1). Entries still pending user confirmation, and disputed entries (the second check disagrees and the judge has not resolved it), are reported separately, with their count, in the generalisation report (Story 9.6).

### 1.4 The litmus flag (applied to every entry, whatever its outcome)

This flag is a code-level check and is **narrower than the Spine litmus test**, which asks whether a new business can be onboarded without a business-specific execution graph or state machine while the Agent still reasons about situations nobody enumerated. The flag checks only the change; it does not answer the Spine's question on its own.

**Questions:** (1) Does any engine line the change adds or alters test a business's identity (a tenant id, a business name, or a business-specific value matched as a literal) to choose which code runs? A lookup that only selects a value by tenant is not a branch; choosing a code path is. (2) Does the change add an engine code path that exists for one business only, that is, one that no other business's specification can reach?

Yes to either → the entry is flagged **litmus-test violation** (Spine litmus test; FR59), whatever its class. The flag is never cleared by reclassification; only removing the branch or path clears it, and that removal is logged in the same entry.

### 1.5 Fields every entry records

| Field | Content |
| --- | --- |
| Business | The business, and whether it was hand-written or Builder-built |
| Build position | *Pre-programme* (hand-written businesses: dental, brewery, garden centre of Story 2.6, and the legacy agents), or *programme business N of 4* (Stories 9.2–9.5, in the build order recorded in Story 9.2). Pre-programme entries stay outside the business 1 → 4 trend, which starts with Story 9.2. |
| Need | One sentence |
| Engine paths changed | Every path, with lines pinned to a commit |
| Evidence | File and line, test, commit or diff a second person can open |
| Shares a change with | The other entries whose need the same change served, or "none" |
| Rules version | The version the entry was graded under (§3 lists the versions) |
| Steps | Each step up to the deciding one, answered yes or no, with the evidence item it rests on |
| Outcome | One of the outcomes in §1.3, spelled exactly, with the reason for "no leak" |
| Decided by | The step or test that answered yes |
| Justification | Defect, not a leak, and genuinely novel only (§1.2); genuinely novel also records its shape |
| Litmus flag | Yes or no, with the line that decides it (§1.4) |
| Proposed by | Who proposed the classification (Claude, by the user's decision of 2026-10-17) |
| Judged by | The user, or Claude where the user has delegated the judgement (as on 2026-10-17 for P1 and P2); the delegation is recorded in the entry. Until judged: **pending** |
| Second check | Done by the user or by a person the user names, never by the session that proposed the classification. The checker receives an evidence-only extract (the Need, Engine paths changed and Evidence fields) without the Steps, the Outcome or the Justification, applies steps 0–5, and records who, the date, their outcome and whether it agrees. A disagreement goes to the judge, and both outcomes stay in the entry. Until done: **pending** |

### 1.6 Amendments

Any change to these rules after their first use (the reclassification in §2, 2026-10-17) is a dated amendment, listed in §3 with what changed and why, and it raises the rules version. Every entry recorded before an amendment is graded again under the new version, and both gradings stay in the entry. Rules are never edited in place.

## 2. The log

### Pre-programme entries (outside the business 1 → 4 trend)

#### P1 — Brewery events: per-business open times in the simulated calendar

Formerly PROOF-GATE.md leak-log entry 1, labelled "Test fixture leaf — not a Core change".

| Field | Value |
| --- | --- |
| Business | Brewery events (`studio/businesses/brewery/`, tenant `hopfield-brewery`), hand-written in Epic 1 |
| Build position | Pre-programme; second business on the studio Core, after dental |
| Need | The brewery's events are booked at 12:00, 15:00 and 18:00, not at the simulated calendar's default times (09:00, 11:00, 14:00, 16:00). |
| Engine paths changed | At commit `44c8094`: `studio/extensions/simulated.py:45` (field `tenant_times`), `:67` (lookup: per-date override, else the tenant's times, else the defaults); `studio/__main__.py:30` (`SIMULATED_TIMES`, the brewery's times), `:94` and `:122` (passed to the calendar). No Core path (`studio/core`); nothing in `studio/spec`, `studio/agent` or `studio/channels`. |
| Evidence | The lines above at `44c8094`. The `Adapter` contract (`studio/core/ports.py:142-153`: `read`, `effect`, `read_back`, and `AdapterResult`) is what `SimulatedCalendar.read` (`simulated.py:60`) implements, and the change keeps the same signature, the same operation (`availability`) and the same result fields (`date`, `open_times`). Searching `studio/` runtime code for `hopfield` or `brewery` finds only `studio/__main__.py:30`. Limit: studio V1 landed as one commit (`44c8094`), so there is no separate diff for the brewery; the evidence is the lines and the search. Tests: `studio/tests/test_brewery.py`. |
| Shares a change with | none |
| Rules version | 1 |
| Steps | 0 Scope: yes, two engine paths changed (neither in the Core). 1 Fixture: yes. The changes are confined to a simulator under `studio/extensions/` (`simulated.py:45,67`) and the CLI wiring that supplies its data (`__main__.py:30,94,122`). The data is open times, which a real calendar holds for each business (FR36). The adapter contract is unchanged (`ports.py:148` vs `simulated.py:60`). |
| Outcome | **No leak** (reason: fixture data) |
| Decided by | Step 1 (fixture) |
| Justification | not required |
| Litmus flag | No. (1) `simulated.py:67` selects a value by tenant (`tenant_times.get(tenant, ...)`); no code path depends on which business it is. (2) No code path exists for the brewery only: the lookup runs for every tenant. |
| Note | `studio/__main__.py:30` holds the demo tenant id and its times. This is test wiring for a made-up business, decided as fixture data (2026-10-17). Convention from Story 9.2 on: a business keeps its demo data in `studio/businesses/<business>/`, so this case does not recur. |
| Proposed by | Claude, 2026-10-17 |
| Judged by | Claude, under the user's delegation of 2026-10-17 ("make your own decision"); the user may override at any time |
| Second check | pending |

Relation to the old label: same substance. "Test fixture leaf" becomes the outcome *no leak*, reason *fixture data*, decided by an explicit step.

#### P2 — Dental front desk (legacy voice engine): strict consent at the confirmation gate

Formerly the retroactive note under PROOF-GATE.md's leak log: "DL-015 (strict consent) changed shared engine code while the third business was being built — *should have been platform behaviour from the start*". That label is not one of FR89's classes; this entry grades it under the rules.

| Field | Value |
| --- | --- |
| Business | BrightSmileDental (`Generated_Agents/BrightSmileDental/`), hand-written on the legacy LangGraph voice engine |
| Build position | Pre-programme; third legacy agent, after the Acme template (`boilerplate/`) and BassanBrewerySDR. Build start: commit `b6c7800` (2026-10-11 19:51), which added the dental agent. It concerns a different engine (`boilerplate/`), so it is history for the studio Core, not part of its trend. |
| Need | A reply at the booking confirmation that contains a yes-word but is not a yes ("okay, but my cheek is really puffy") must not book the visit. |
| Engine paths changed | The need spans two commits. `b6c7800`: `boilerplate/nodes.py` `intent_detect_node` (a message carrying a handoff keyword skipped yes/no resolution). `0339313`: `boilerplate/nodes.py:126-136` (`_bare_answer`) and `:228-232` (gate resolution uses it); the keyword bypass was removed. In both commits the same `nodes.py` went to all three agents: the Acme template in `boilerplate/` and its two copies, `Generated_Agents/BassanBrewerySDR/nodes.py` and `Generated_Agents/BrightSmileDental/nodes.py`. Carried into the candidate Core as `studio/core/consent.py:36` (`bare_answer`), used by `studio/core/harness.py:228` (`_resolve_consent`), at `44c8094`. |
| Evidence | Commit messages of `b6c7800` ("okay, but my face is swollen and I can't swallow" booked the visit; all five escalation replies failed in the Acme template) and `0339313` ("okay, but my cheek is really puffy" booked the visit). DL-015 in `docs/sprint-seven-day/DECISION-LOG.md`. Tests: `builder_platform/tests/test_execution_authz.py:144` (`test_escalation_at_the_confirmation_gate_is_not_consent`, added in `b6c7800`), `:157-175` (the puffy case, added in `0339313`), `builder_platform/tests/test_dental_agent.py:88`; candidate: `studio/tests/test_core.py:74`. |
| Shares a change with | none |
| Rules version | 1 |
| Steps | 0 Scope: yes, the engine file `boilerplate/nodes.py` changed. 1 Fixture: no; a legacy entry has no simulated system of record (§1.1). 2 Defect: no. Step 2 is cut at the first commit of the need, `b6c7800`, which is also the build start. The requirement recorded before it is the confirmation gate itself: commit `589c3a0` (2026-10-11 13:54, "Refuse gated tools at execution time without a one-time platform record") makes a state-changing tool need the user's confirmation record, and does not say which message counts as a confirmation. The sprint contract's C3 (`docs/sprint-seven-day/SPRINT-CONTRACT.md:48`) reads: "**C3 binding (DL-008).** Confirmation and operator-approval records are Core-owned and separate from model-controlled payload fields. Each is bound to the conversation or episode, business/agent, effective configuration version, flow and tool, and canonicalized action arguments." It binds records to payloads and never says which message counts as consent. It was also first committed in `085929d` (2026-10-12 02:07), after the build start, so it cannot serve as a prior requirement. The test that pins the case was added in the fixing commit `b6c7800`. 3 Test C: no. The change contains no business-specific value; it replaces how the gate resolves (a yes-word anywhere in the message became a whole-message match, `nodes.py:126-136` at `0339313`) for every agent. 4 Test E: no. The change touches no tool contract in any agent's `tools.py` (the legacy equivalent, §1.1); it is in `intent_detect_node` (`nodes.py:228-232` at `0339313`), and its result decides the next step (book, decline, or classify), which is control flow, not a leaf. 5 Test N: yes, C and E each answered no against the lines cited. |
| Outcome | **Genuinely novel** |
| Decided by | Test N (step 5) |
| Justification | What counts as consent is the meaning of the confirmation gate, which every business shares. A per-business setting for it would let configuration change Core semantics, which FR58 forbids, and a leaf behind a contract cannot own it, because resolving the gate decides what happens next (FR59). Shape: *platform semantics*. The same `nodes.py` went unchanged to all three agents, and the phrase lists name no business. |
| Litmus flag | No. (1) `_bare_answer` (`nodes.py:126-136` at `0339313`) and its phrase lists (`:108-114`) name no business and select no code path by business. (2) The gate resolution runs for every agent; no path exists for dental only. |
| Proposed by | Claude, 2026-10-17 |
| Judged by | Claude, under the user's delegation of 2026-10-17 ("make your own decision"); the user may override at any time |
| Second check | pending |

Relation to the old label: "should have been platform behaviour from the start" becomes *genuinely novel* with the shape *platform semantics*. It is not *should have been configuration*: the change has no business value in it (test C).

#### P3 — Garden centre: a records system for guarantee claims

| Field | Value |
| --- | --- |
| Business | Greenway Garden Centre (`studio/businesses/garden-centre/`, tenant `greenway-garden-centre`), hand-written in Story 2.6 from the Brief's exemplar 3 (`spec-stress-test.md` §3) |
| Build position | Pre-programme; third business built on the studio Core (dental and brewery events came first) |
| Need | The guarantee claim (`create_guarantee_claim`, adapter `records`, operation `claim`) needs a connected system of record to write to and read back from. |
| Engine paths changed | `studio/__main__.py` only: the scenario runner and `chat` register the same `SimulatedCalendar` instance under a second adapter name, `records`, beside `calendar`. Nothing in `studio/core`, `studio/spec`, `studio/agent`, `studio/channels` or `studio/extensions`. |
| Evidence | The change is in the Story 2.6 commit. `SimulatedCalendar.effect` and `.read_back` (`studio/extensions/simulated.py`) store and read back any payload by idempotency key whatever the operation name, so `claim` needs no simulator change. The `Adapter` contract (`studio/core/ports.py`: `read`, `effect`, `read_back`, `AdapterResult`) is unchanged. The specification passes the validation suite as written, with no `.py` file in the business folder (`test_the_garden_centre_passes_the_gate_with_no_business_python`). Scenarios G1–G5 pass credential-free. The pytest scenario runner (`test_end_to_end.py`) wires the same adapters as the CLI, and `test_an_approved_claim_is_written_to_the_records_system_and_read_back` exercises the claim on `records` through approval, effect and read-back. The Phase 2 Core changes (Stories 2.1–2.5) were made for platform requirements (FR30–FR37, T9–T12) before this business, and none was needed by it. |
| Shares a change with | none |
| Rules version | 1 |
| Steps | 0 Scope: yes, one engine path (the CLI wiring). 1 Fixture: yes. The change only wires an existing simulated system of record to the adapter name the specification declares. The claims record is data a real records system would hold (FR36), and the adapter contract is unchanged (`ports.py`). |
| Outcome | **No leak** (reason: fixture data) |
| Decided by | Step 1 (fixture) |
| Justification | not required |
| Litmus flag | No. (1) No engine line tests the business's identity; the alias is registered for every business the runner loads. (2) No code path exists for the garden centre only. |
| Note | Everything the Brief's exemplar needs is declared, not coded: the exclusions, timeframe and proof rules deny the claim (`deny_when`); the liability class with `operator_approval` defers an eligible claim to a person; `customer_neglect` is a forbidden conclusion and `general_knowledge_allowed = true` lets care advice be marked as general knowledge (P2-F5 confirmed). Not declared in this first cut, from the Brief:
  - the till-system (EPOS) lookup and the stock check;
  - "one claim per item" across conversations (idempotency stops duplicates only within one);
  - the value-threshold escalation;
  - `issue_credit_note`, `notify_horticulturist` and `get_care_guide`.

  These wait for a real till and records system (Epic 8) or the Builder build of this business (Story 9.4). The simulated system of record is the calendar simulator, so a claim's reference and its errors use booking wording (`BK-…`, "no such booking"). Test wiring only. |
| Proposed by | Claude, 2026-10-19 |
| Judged by | Claude, under the user's delegation of 2026-10-17 ("make your own decision"); the user may override at any time |
| Second check | pending |

### Programme entries (the business 1 → 4 trend)

None yet. The first comes from Story 9.2.

## 3. Rules versions and amendments

| Version | Date | Change |
| --- | --- | --- |
| 1 | 2026-10-17 | First version (Story 9.1). First used for the reclassification of P1 and P2. |
