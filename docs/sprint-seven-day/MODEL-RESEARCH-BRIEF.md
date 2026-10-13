# Model research brief — Agent Studio

Version 2, 2026-10-12. Written for a researcher with web access who has not seen this project. **Research as of 2026-10-12:** prefer sources from the last few months, and date every claim.

File paths and IDs (AD-n, FR-n, NFR-n, DL-n) refer to the project's own documents. You cannot open them and do not need to: every passage this research depends on is quoted or summarized here.

**Source order for this brief:** the finalized Architecture Spine (`_bmad-output/planning-artifacts/architecture/architecture-AgentStudio-2026-10-07/ARCHITECTURE-SPINE.md`, "AD-n") and the PRD (`…/prds/prd-AgentStudio-2026-10-08/prd.md`, "FR/NFR-n") define the requirements. The existing code is a brownfield **reference implementation** ("the reference implementation and migration source, not the foundation", Spine, Proof Gate). Its constraints appear only in section 5, as a compatibility check for one near-term test run. Where the two disagree, section 6 lists the disagreement; this brief does not resolve it.

## 1. The product, in one paragraph

Agent Studio is a platform that turns a business's specification (context, policies, authorities, granted capabilities) and knowledge into a deployed **inbound text agent**. V1's channel is **inbound email / messaging** (FR84), which is asynchronous. Voice is a separate, already-proven project. The architecture is a **hexagonal agent harness**: "A model-in-charge agent decides what to do next; a deterministic Core decides what the agent is permitted to do, executes it, and records what happened" (Spine). The model is the decision-maker. Everything that must hold is enforced outside it (AD-3).

## 2. What the model is asked to do (Spine, "Deterministic vs Delegated")

Delegated to the model: what the person is trying to accomplish; what information is still needed; when to retrieve; which capability to use; whether to act, continue, respond, **and whether to escalate**; how to phrase anything; **how to handle a situation nobody enumerated**.

Concretely, each step the model emits **one typed request from a closed set**: `retrieve`, `read`, `effect`, `clarify`, `respond`, `escalate`, `suspend` (AD-2). The Core validates it, authorizes it, and returns a typed result, always (AD-18). The model then continues the loop until it closes the episode with a claimed resolution, which the Core checks against evidence (AD-20). This is a conventional model-driven tool-use loop inside a harness.

Two narrower model uses are also allowed:

- **Model-based guard detection** (AD-21): urgency, policy violation and unsupported-request detection over free text. The verdict is enforced deterministically, and a guard never composes a reply.
- **Typed narrow decision calls** (PRD addendum AD3.2, "Not every intelligent decision needs the full Agent loop"): a small typed call may **constrain or classify, never sequence**. Using one to pick the next step is forbidden (FR39).

## 3. Requirements

### 3.1 Capability

| # | Requirement | Source |
| --- | --- | --- |
| C1 | Reliable **multi-step tool use / typed request emission** in a loop: picks the right request kind and well-formed arguments over many turns, and recovers from a typed refusal by choosing a different step (it is never told the next step). | AD-1, AD-2, AD-18 |
| C2 | **Schema-faithful structured output** for typed requests, resolution claims, guard verdicts and narrow decisions. | AD-2, AD-6, AD-20, AD-21 |
| C3 | **Judgement in unenumerated situations**, including deciding to escalate. The platform never escalates for the model. | Spine, "Escalation has exactly one owner" |
| C4 | **Faithful handling of opaque references**: it cites Core-issued provenance references exactly, and does not invent, alter or infer them. | AD-7 |
| C5 | **Instruction-following under advisory constraints**: prompt text describes policy, but violations are refused by the Core (AD-3). A model that complies more often generates fewer refusals and loops less. | AD-3, AD-5 |
| C6 | **Written correspondence quality** (email/message replies, in the business's own voice). | FR113, EX1 |
| C7 | A **small, fast tier** suited to guard detection and narrow classification. | AD-21, AD3.2 |

### 3.2 Platform

| # | Requirement | Source |
| --- | --- | --- |
| P1 | **Portability:** "Changing the model, provider or agent framework MUST NOT alter the architecture. No vendor SDK import, no hardcoded provider or base URL, no branching on provider, no vendor-specific key. Swapping providers is a configuration change." | NFR12, AD-9, AD-14 |
| P2 | The model sits **behind a runtime boundary the platform owns**. The candidate runtime is **Pydantic AI 2.54.0** (verified 2026-10-08; confirm the current version and whether each candidate is supported by it). Tiering across capability classes must be expressible at that boundary. | AD-14, Spine "Stack" |
| P3 | **Measurement from day one:** per-call tokens, cost and latency, recorded as evidence in **OpenTelemetry GenAI** vocabulary. No latency target and no cost ceiling are set for V1; they come from measurement. | NFR13, NFR14, NFR16, Spine conventions |
| P4 | **No credentials in any prompt or evidence.** | AD-24, NFR11 |
| P5 | **Configuration validated at startup**; a health check never reports healthy on a configuration whose first real request will fail. | NFR17 |
| P6 | **Data handling:** episodes may hold sensitive and health-adjacent material; evidence must be removable by tenant, episode and age. | AD-25, NFR10 |

P4 and P5 are properties of the platform, not of a model: they are context for you and are not to be graded per model. For P3, report per candidate whether the provider returns token usage on every response.

## 4. Standards for any evaluation run (context: how your findings will be used)

1. **A degraded model call must be visible to the caller**, not only logged. The Spine's rule: "errors cross boundaries as typed results, never as defaults."
2. **One model per capability class across all businesses** in a comparison, so that business differences are not model differences.
3. Every result names the **exact model ID, provider endpoint and date**, and is labelled live. It is never mixed with deterministic (mock) results.
4. **Expectations are not tuned to the model.** Report what happens.
5. **Model routing and tiering policy is "an evaluation question… measured, not designed"** (Spine, Deferred). The research informs that evaluation and does not replace it.
6. The key is never written to disk, a report or logs.

## 5. Near-term compatibility check: the reference implementation

A sprint now running (DL-007) **keeps the existing 15-node LangGraph engine** and will run about 30 scripted turns × 3 repetitions against a real model. That engine predates the Spine and constrains the model differently:

- Its only model interface is an **OpenAI-compatible `/v1/chat/completions`** endpoint, set by `OPENAI_BASE_URL` / `OPENAI_API_KEY`, through the `openai` Python SDK 2.8.1 (`boilerplate/llm_client.py`).
- It uses **no native tool calling**. Decisions are JSON objects: `client.beta.chat.completions.parse` with a Pydantic schema first, falling back to `response_format={"type":"json_object"}`.
- It sends `temperature` (0.0–0.5) and `max_tokens` (5–400) on every call, and enforces a 30 s per-call timeout.
- It has three fixed roles, INTENT / ANSWER / ENRICH, each its own env var. The Spine treats this pipeline as superseded.
- On any model error it silently falls back to a keyword heuristic. That breaks standard 4.1, and the project will fix it before a live run.
- Estimated volume, not measured: 200–400 short calls.

**Question for this section only:** which of the recommended models also run cleanly on this interface (JSON schema or JSON mode, accepts `temperature` and `max_tokens`)? If the platform's best choice cannot, say what the closest compatible option is.

## 6. Contradictions between the Spine and the brownfield code (report on these, do not resolve them)

1. **Provider boundary.** The brownfield rule is "OpenAI-compatible `/v1` only". The Spine (AD-14, P2) puts providers behind a framework boundary, with Pydantic AI as the candidate; such a framework addresses providers through its own adapters. NFR12 forbids a "vendor SDK import". Does a framework that imports vendor SDKs internally, selected by a configuration string, satisfy NFR12 as written? Give the facts about how Pydantic AI 2.x selects providers, and note any OpenAI-compatible path it offers.
2. **Tool calling.** The brownfield engine avoids native tool calling. The Spine's loop is a tool-use loop (AD-2). Evaluate tool-use quality (C1) as the primary capability. JSON-mode-only compatibility matters only for section 5.
3. **Latency.** The brownfield engine was built under a voice dead-air budget. The PRD sets no V1 latency target (async channel, NFR13). Report latency as data, not as a pass/fail filter.

## 7. Candidates and open questions

Confirm each candidate from a primary source: existence, general availability, provider, exact model ID, and the date of your source.

- **Claude Haiku 5.5** (Anthropic). The architecture log records it as "released 2026-10-07, dramatically cheaper than the previous Haiku generation and positioned for high-volume, cost-sensitive workloads and real-time/agent sub-workloads". That is the owner's statement; confirm it. A candidate for C7 and possibly for the main loop.
- **Luna 6**: described by the owner as an LLM; it appears in no project document. Identify the provider.
- **OpenAI Decisions API** and **Jev** ("TypeSafe/LangChain Jev typed decision models", PRD log D9). The PRD classifies both as "IMPLEMENTATION OPPORTUNITIES ONLY… No architectural dependency on any of them. Provider agnosticism remains a hard boundary". Their natural place is AD3.2's narrow typed decisions (classify or constrain, never sequence). For each: what is it, can it sit behind the AD-14 boundary without breaking NFR12, and what would it change in the reference implementation?
- **Other current models** you judge competitive on C1–C7. Include at least one from a second provider, so portability (P1) is exercised and not just asserted.

Questions:

1. For each candidate: tool-use / agentic benchmark evidence (C1, C3), structured-output mode (C2), and reliability with exact identifiers (C4).
2. Which models suit the small tier (C7), and what is the quality gap to the main tier on classification tasks?
3. Price per million input/output tokens, rate limits at the lowest paid tier, and data retention / training-use terms (P6).
4. Latency p50/p95 for a short structured call (data only, see 6.3).
5. Section 5's compatibility question.

## 8. What to deliver

- A table: candidate × C1–C7, P1, P2, P3 (usage reporting) and P6 (pass / fail / unknown), with a source and date in each cell.
- A recommendation for the main loop tier and for the small tier, each with a runner-up, and stated as **input to the tiering evaluation**, not as the policy.
- A separate answer for section 5 (the near-term run on the reference implementation).
- A plain answer on the Decisions API and Jev.
- Findings on the three contradictions in section 6.
- Everything you could not verify, listed as unverified, not guessed.
