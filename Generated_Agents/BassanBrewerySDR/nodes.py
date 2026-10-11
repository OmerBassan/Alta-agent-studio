"""Pipeline nodes: the multi-model chain, all executed within ONE user turn.
Generic — the domain enters via config.py; do not edit per client.

Roles (each a model tier via llm_client):
  1. intent_detect  (INTENT) — hierarchical classify (category -> intent) +
                               extract slots (+ carry a pending flow, resolve a
                               pending yes/no confirmation). Two deterministic
                               tier-0 gates run BEFORE the model: the
                               confirmation gate and the FAST ROUTER (a
                               mid-slot-fill message that deterministically
                               fills a missing slot bypasses the INTENT call).
                               A second FLOW interrupting a pending one is
                               parked in the depth-1 interrupt archive
                               (paused_flow) and restored deterministically.
  2. knowledge / chitchat / closing (ANSWER) — direct LLM answer, no tool;
                               grounded on last_action, never kills a pending flow
  2b. agentic_retrieval (subgraph) — for RETRIEVAL_INTENTS: run the private
                               retrieve->grade->rewrite loop, hand back ONLY
                               retrieved_context (semantic memory)
  2c. system (no model)        — deterministic SYSTEM intents: help / restart /
                                 human_handoff (escalation: raises the
                                 Shell-observable handoff_requested flag)
  2d. planner (ANSWER, ONCE)   — COMPOUND requests: turn a multi-action
                                 utterance into an ordered plan_steps array
  2e. plan_step (no model)     — deterministic plan controller: record the
                                 previous step's outcome, dispatch the next
                                 step into the ordinary think->act machinery
                                 (monotonic index, doubly bounded)
  3. think (ANSWER)            — Think step for any config.FLOWS intent:
                                 entity resolution + slot validators, then
                                 act-now (cold tool payload), need-info, a
                                 confirm question (state_changing), or the
                                 HITL gate (liability) — see authz.py
  3b. hitl_gate (no model)     — interrupt(): suspend for OPERATOR approval of
                                 a liability payload before Act
  4. tool_exec (no model)      — Act step: refuses a gated tool without a
                                 one-time platform record for this exact
                                 payload (authz.py), then deterministic
                                 side-effect via registry, breaker guarded
  4b. execution_validator (no model) — Layer 2.5: inspect the tool result;
                                 route failure vs enrich vs SLM-bypass
  4c. failure (no model)       — graceful tool-failure reply, flow retryable
  5. enrichment (ENRICH, SLM)  — terse tool result -> warm prose (only when the
                                 execution validator asked for it)
  6. validator (no model)      — RESPONSE validator (Layer 3): exit filter ->
                                 final_response; carries the deterministic
                                 STALL gate (invariant 25): the N-th
                                 consecutive identical reply is swapped for
                                 the clarify-then-escalate STALL_TEXT.
                                 Also hosts three zero-model sales gates, in
                                 this ORDER (each is in-node, never a graph
                                 node): objection A-I-P -> director agenda move
                                 -> scrub -> stall fingerprint -> tie-down.
                                 The tie-down is appended LAST, after the
                                 fingerprint, so its rotating text can never
                                 mask a repeated reply from the stall gate.

Every node returns a state-update dict only; routing lives on edges (graph.py).
In MOCK mode each model-backed node uses a deterministic fallback so the whole
chain runs with zero credentials. Every LIVE call also degrades to its mock
fallback on error (auth, rate limit, network) so a turn never crashes.
"""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime

import asyncio

from langchain_core.messages import AIMessage
from langgraph.types import interrupt

import authz
import compaction
import config
import filler
import prompts
import tools
from llm_client import llm_client, INTENT_MODEL, ANSWER_MODEL, ENRICH_MODEL
from rag_subgraph import rag_subgraph
from schemas import AgentState, EnrichVerdict, IntentResult, PlanResult, PlanStep, ThinkDecision

logger = logging.getLogger(__name__)

# tool name -> Flow (for the execution validator's enrich decision, the
# router's HITL check on confirmed payloads, and tool_exec's gate lookup —
# authz.preflight_flows guarantees a GATED tool has exactly one owning flow).
FLOW_BY_TOOL = {flow.tool: flow for flow in config.FLOWS.values()}

# Yes/no resolution for the confirmation gate. Negation is checked FIRST so
# "no, don't do it" never reads as an affirmative.
_NEGATE_RE = re.compile(r"\b(no|nope|don'?t|cancel|stop|wait|not yet|hold on|"
                        r"changed my mind|never ?mind)\b", re.IGNORECASE)
_AFFIRM_RE = re.compile(r"\b(yes|yep|yeah|sure|confirm|confirmed|go ahead|do it|"
                        r"ok(ay)?|please do|correct|right|absolutely)\b", re.IGNORECASE)

# Mock-mode heuristic for "explain yourself" questions grounded on last_action.
_GROUNDING_Q_RE = re.compile(r"\b(how do you know|how would you know|are you sure|"
                             r"based on what|how come|why is that|says who)\b", re.IGNORECASE)

# Slot REFUSAL (tier-0, deterministic): the lead declines to give the asked
# value. Deliberately NARROW — refusal phrasing only, never a plain "no",
# which keeps its existing abandonment/decline semantics (_NEGATE_RE). A
# match mid slot-fill marks the asked slot config.SLOT_REFUSED so it is
# never re-asked; re-asking a refused question loses the lead.
_REFUSAL_RE = re.compile(
    r"(rather not|prefer not to|won'?t (say|share|tell|give)|"
    r"not (saying|sharing|telling|comfortable)|"
    r"don'?t (want|wanna|feel like) (to )?(say|share|tell|give|answer)|"
    r"none of your business|skip (that|this|it)|why do you need)",
    re.IGNORECASE)


def _fast_route(user_message: str, intent: str, collected: dict) -> dict | None:
    """Fast-router gate (tier-0, deterministic, NO model): mid slot-fill,
    decide whether the message simply fills a missing slot of `intent`. On a
    confident match, return the exact dict a continuation turn would produce
    (routing straight to Think); return None to fall through to the normal
    INTENT-tier path. Every guard is fall-through-biased — a false negative
    costs one model call, a false positive misroutes an interruption — so on
    ANY doubt, return None. This gate fronts the INTENT tier; it never
    replaces it."""
    if not config.FAST_ROUTER_ENABLED:
        return None
    flow = config.FLOWS.get(intent)
    if flow is None:
        return None
    # Negation ("no wait", "cancel") may be an abandonment — the model decides.
    if _NEGATE_RE.search(user_message):
        return None
    # Interruption guard: a keyword of ANY other intent (another flow, goodbye,
    # restart, an FAQ) means this is not a bare slot answer.
    low = user_message.lower()
    for name, keys in config.INTENT_KEYWORDS.items():
        if name != intent and any(k in low for k in keys):
            return None
    missing = [s for s in flow.slots if not collected.get(s)]
    if not missing:
        return None
    extracted: dict = {}
    for s in missing:
        fn = config.SLOT_EXTRACTORS.get(s)
        val = fn(user_message) if fn else None
        if not val:
            continue
        # Pre-TEST with the same hooks Think will run (result discarded —
        # Think stays the single authoritative resolver/validator pass and
        # receives the raw value; hooks are idempotent on canonical values).
        # A bounce ("any branch") needs a conversation, not a bypass.
        for hooks in (config.ENTITY_RESOLVERS, flow.validators):
            check = hooks.get(s)
            if check is not None:
                ok, _ = check(str(val), {**collected, **extracted, s: val})
                if not ok:
                    return None
        extracted[s] = val
    if not extracted:
        return None   # bare "ok" / free text extracted nothing — LLM decides
    return {"intent": intent, "category": config.CATEGORY_OF.get(intent, "FLOW"),
            "slots": {**collected, **extracted}, "fast_routed": True}


def _history(state) -> list:
    # Raw window kept in the prompt is SHORT on purpose (config.HISTORY_TURNS,
    # default 8 ~= 4 exchanges): a voice payload must stay light for low TTFT,
    # and durable detail already survives outside it — session_facts (hard IDs),
    # last_action (last tool result), pending_slots (in-flight flow), and the
    # cross-turn call_summary lead record. Older raw turns are largely redundant.
    role_map = {"human": "user", "ai": "assistant"}
    out = []
    for m in state.get("recent_messages", [])[-config.HISTORY_TURNS:]:
        out.append({"role": role_map.get(getattr(m, "type", ""), "user"), "content": str(m.content)})
    return out


# ======================================================================== #
# 1. INTENT DETECTION (Tier: INTENT)                                        #
# ======================================================================== #
async def intent_detect_node(state, thread_id: str = "", ledger=None) -> dict:
    user_message = state.get("user_message", "")
    pending = state.get("pending_intent")
    pending_slots = dict(state.get("pending_slots") or {})

    # Confirmation gate resolution: a stashed payload is waiting for yes/no.
    # Deterministic (no model) — a yes/no on a destructive action must never
    # depend on a model's mood. Anything that is neither falls through to
    # normal classification (a detour); the confirmation stays pending.
    confirm = state.get("pending_confirmation") or {}
    if confirm:
        if _NEGATE_RE.search(user_message):
            logger.info("confirmation declined for %s", confirm.get("tool"))
            if ledger is not None:
                ledger.revoke("confirm", thread_id)
            # A decline also aborts any active plan: later steps may depend on
            # the declined action, so never execute past a refused gate.
            return _clear_plan({"intent": "chitchat", "category": "ANSWER", "slots": {},
                                "pending_intent": None, "pending_slots": {},
                                "pending_confirmation": {}, "confirmation_declined": True})
        if _AFFIRM_RE.search(user_message):
            logger.info("confirmation accepted for %s", confirm.get("tool"))
            # The user's yes is the GRANT of the platform's outstanding offer
            # (minted by think when it asked). A yes with no offer behind it —
            # a pending_confirmation that came from anywhere but think — grants
            # nothing, and tool_exec, the one enforcement point, refuses.
            refused = ledger.grant("confirm", thread_id) if ledger is not None else None
            if refused is not None:
                logger.warning("confirm grant refused [thread=%s tool=%s]: %s",
                               thread_id, confirm.get("tool"), refused.reason)
            # The flow is handed to Act — nothing is pending anymore (mirrors
            # think's act branch). A stale pending left here would later be
            # parked by the interrupt archive as a zombie of a DONE flow.
            return {"intent": confirm.get("intent", ""), "category": "FLOW",
                    "slots": pending_slots,
                    "cold_payload": {"tool": confirm.get("tool", ""),
                                     "args": confirm.get("args", {})},
                    "tool_action_pending": True, "pending_confirmation": {},
                    "pending_intent": None, "pending_slots": {}}

    # Fast-router gate (tier-0, deterministic): mid slot-fill, a message that
    # simply fills a missing slot of the pending flow skips the INTENT-tier
    # call entirely and routes straight to Think, which re-runs the
    # authoritative resolver/validator pass on the raw value. Any doubt
    # (negation, other-intent keyword, no extraction, hook bounce) falls
    # through to normal classification below.
    if pending and pending in config.FLOWS:
        fast = _fast_route(user_message, pending, pending_slots)
        if fast is not None:
            logger.info("fast_router: bypassed INTENT tier for %s slots=%s",
                        pending, fast["slots"])
            return fast

    # Slot refusal (tier-0, deterministic, NO model): mid slot-fill, a refusal
    # aimed at the asked slot marks it SLOT_REFUSED and stays in the flow —
    # Think then asks the NEXT missing slot (or acts) instead of re-asking a
    # question the lead just declined. Guards mirror the fast router: no open
    # confirmation (that gate is yes/no, not a slot), and no other intent's
    # keyword (an interruption is not a refusal).
    if pending and pending in config.FLOWS and not confirm \
            and _REFUSAL_RE.search(user_message):
        low = user_message.lower()
        interrupting = any(
            name != pending and any(k in low for k in keys)
            for name, keys in config.INTENT_KEYWORDS.items())
        refusable = [s for s in config.FLOWS[pending].slots
                     if not pending_slots.get(s)]
        if not interrupting and refusable:
            asked = refusable[0]   # _ask_for always asks missing[0]
            logger.info("slot refusal: %s.%s marked SLOT_REFUSED", pending, asked)
            return {"intent": pending,
                    "category": config.CATEGORY_OF.get(pending, "FLOW"),
                    "slots": {**pending_slots, asked: config.SLOT_REFUSED},
                    "fast_routed": True}

    # Paused-flow restore by slot answer: no flow is pending, but the archive
    # holds an interrupted one and this message deterministically fills its
    # missing slot — restore it through the same fast-router gate (matched
    # input only, NEVER a blind re-pend). Any doubt falls through and the
    # archive stays inert.
    paused = dict(state.get("paused_flow") or {})
    if (not pending and not confirm and paused and not _plan_active(state)
            and paused.get("intent") in config.FLOWS):
        fast = _fast_route(user_message, paused["intent"], dict(paused.get("slots") or {}))
        if fast is not None:
            logger.info("fast_router: restored paused flow %s", paused["intent"])
            return {**fast, "paused_flow": {}}

    # COMPOUND detection (mock mode): a fresh multi-action utterance routes to
    # the planner. Guarded by the same seniority rule as live mode — an
    # in-progress flow, confirmation, or plan is NEVER re-planned mid-way.
    if (llm_client.mock and not pending and not confirm and not _plan_active(state)
            and _mock_compound(user_message)):
        logger.info("compound request detected (mock heuristic)")
        return {"intent": "compound_request", "category": "COMPOUND", "slots": {}}

    if llm_client.mock:
        result = _mock_intent(user_message)
    else:
        pending_ctx = ""
        if pending and pending in config.FLOWS:
            missing = [s for s in config.FLOWS[pending].slots if not pending_slots.get(s)]
            pending_ctx = (f"\n\nPENDING flow: '{pending}'. You previously asked the user for: "
                           f"{', '.join(missing) or 'a detail'}. If their message answers that, keep this "
                           f"intent and fill the slot. But if they instead ask a question, raise an "
                           f"objection, or change the subject, classify THAT accurately (the matching "
                           f"knowledge/objection intent, or chitchat) — do NOT force an unrelated message "
                           f"into the slot; the system re-anchors to the pending task on its own.")
        messages = ([{"role": "system",
                      "content": prompts.build_intent_system(pending_ctx, _last_action_intent_ctx(state),
                                                             _session_facts_ctx(state), _summary_ctx(state))}]
                    + _history(state) + [{"role": "user", "content": user_message}])
        try:
            result = await llm_client.generate_structured(INTENT_MODEL, IntentResult, messages, temperature=0.1)
        except Exception as e:
            logger.warning("intent tier failed (%s); using heuristic fallback", type(e).__name__)
            result = _mock_intent(user_message)

    intent = result.intent
    extracted = {k: v for k, v in (result.slots or {}).items() if v}
    slots = {**pending_slots, **extracted}

    # Clamp: an unknown intent name from the model becomes the pending flow if
    # one exists, else chitchat — never a session-ending guess.
    if intent not in config.VALID_INTENTS:
        intent = pending or "chitchat"

    # Never re-plan mid-way: a compound classification while a flow, a
    # confirmation, or a plan is in progress stays with the work in progress.
    if intent == "compound_request" and (pending or _plan_active(state)):
        intent = pending or "chitchat"

    # Continuation guard: mid slot-fill, a bare value ("downtown at 3pm") often
    # classifies as chitchat/knowledge. If the turn produced a slot value, stay
    # in the pending flow instead of dropping it.
    if pending and intent in ("chitchat",) + config.KNOWLEDGE_INTENTS and extracted:
        intent = pending

    # Depth-1 interrupt archive: a second tool FLOW interrupting the pending
    # one PARKS the pending flow (intent + collected slots) instead of letting
    # think/_clear_pending clobber it, and isolates the new flow's slots (the
    # old flow's values must not leak into the new tool — session_facts is the
    # sanctioned cross-flow value bus). Newest interruption wins (depth 1,
    # never a stack). Re-entering the archived flow by name restores its slots
    # so nothing already collected is re-asked. The plan walk has its own
    # pause/resume machinery — never archive/restore mid-plan.
    extra: dict = {}
    if not _plan_active(state):
        if (pending and pending in config.FLOWS and intent in config.FLOWS
                and intent != pending):
            extra["paused_flow"] = {"intent": pending, "slots": pending_slots,
                                    "offered": False}
            slots = extracted
            logger.info("interrupt archive: parked %s (slots=%s) for %s",
                        pending, pending_slots, intent)
        elif paused and intent == paused.get("intent"):
            slots = {**(paused.get("slots") or {}), **extracted}
            extra["paused_flow"] = {}
            logger.info("interrupt archive: re-entered %s by name", intent)

    # The category is DERIVED from the final intent (config.CATEGORY_OF is the
    # source of truth) — the model's own category pick is a classification aid,
    # never a routing input, so a category/intent mismatch cannot corrupt routing.
    category = config.CATEGORY_OF.get(intent, "ANSWER")

    logger.info("category=%s intent=%s slots=%s (pending was %s)", category, intent, slots, pending)
    return {"intent": intent, "category": category, "slots": slots, **extra}


def _mock_intent(text: str) -> IntentResult:
    low = (text or "").lower()
    intent = "chitchat"
    for name, keys in config.INTENT_KEYWORDS.items():
        if any(k in low for k in keys):
            intent = name
            break
    # Run every extractor unconditionally so a bare slot answer to a pending
    # flow is captured even when the phrase carries no intent keyword.
    slots = {name: fn(text) for name, fn in config.SLOT_EXTRACTORS.items()}
    return IntentResult(intent=intent, slots={k: v for k, v in slots.items() if v})


def _last_action_intent_ctx(state) -> str:
    la = state.get("last_action") or {}
    if not la:
        return ""
    return (f"\n\nLAST COMPLETED ACTION: tool '{la.get('tool')}' -> {la.get('summary', '')}\n"
            "A short reply (a payment word, 'thanks', 'why?', 'ok') most likely refers to "
            "this action — classify it as chitchat (or a matching knowledge intent), "
            "NOT as a new tool flow, unless the user clearly requests a new action.")


def _session_facts_ctx(state) -> str:
    """Functional session cache injection: verified transactional identifiers
    from earlier tool runs, injected as an immutable prompt line exactly like
    the date injection. The cache itself is written ONLY by tool_exec's
    deterministic whitelist merge — no model output ever lands in it."""
    facts = state.get("session_facts") or {}
    if not facts:
        return ""
    return ("\n\nKNOWN FACTS (verified this session — reuse these identifiers "
            f"instead of re-asking): {json.dumps(facts, ensure_ascii=False)}")


# Compound detection (mock mode): split on sequencing conjunctions and see
# whether at least TWO clauses map to DISTINCT tool flows. Runs only on fresh
# utterances (no pending flow/confirmation/plan), so slot answers like
# "downtown and 3pm" can never be misread as a plan.
_CONJ_RE = re.compile(r"\b(?:and then|then|after that|afterwards)\b|;", re.IGNORECASE)


def _mock_compound(text: str) -> list[PlanStep] | None:
    clauses = [c.strip() for c in _CONJ_RE.split(text or "") if c.strip()]
    if len(clauses) < 2:
        clauses = [c.strip() for c in re.split(r"\band\b", text or "", flags=re.IGNORECASE)
                   if c.strip()]
    if len(clauses) < 2:
        return None
    steps: list[PlanStep] = []
    for clause in clauses:
        low = clause.lower()
        intent = next((name for name, keys in config.INTENT_KEYWORDS.items()
                       if name in config.FLOWS and any(k in low for k in keys)), None)
        if intent is None or any(s.action == intent for s in steps):
            continue
        # Context isolation, mock edition: extract slots from THIS clause only.
        slots = {name: fn(clause) for name, fn in config.SLOT_EXTRACTORS.items()
                 if name in config.FLOWS[intent].slots}
        steps.append(PlanStep(action=intent, slots={k: v for k, v in slots.items() if v}))
    return steps if len(steps) >= 2 else None


# ======================================================================== #
# 2. DIRECT-ANSWER NODES (Tier: ANSWER) — no tool, no enrichment            #
#    A pending flow SURVIVES these nodes (detours don't kill flows): the    #
#    reply gets a deterministic resume line instead.                        #
# ======================================================================== #
# Referential queries ("how much does IT cost?") mean nothing standalone —
# they get deterministic context priming (rule 8) and are NEVER cached
# (rule 9): their answer depends on conversation state, not the string.
_REFERENTIAL_RE = re.compile(r"\b(it|its|that one|this one|that|this|those|these|"
                             r"they|them|the same)\b", re.IGNORECASE)

# TTL context cache (Agentic_RAG_Explained.txt rule 9): normalized query ->
# (monotonic timestamp, finalized context). In-process, bounded, exact-match
# only — semantic cache matching would need an embedding call and is exactly
# the latency this cache exists to avoid. Stores CONTEXT, never the phrased
# answer: synthesis stays live and grounded.
_RAG_CACHE: dict = {}
_RAG_CACHE_MAX = 128


def _rag_cache_key(message: str) -> str:
    return " ".join(re.findall(r"[a-z0-9']+", (message or "").lower()))


def _rag_cache_get(key: str):
    if config.RAG_CACHE_TTL_SECONDS <= 0:
        return None
    entry = _RAG_CACHE.get(key)
    if entry is None:
        return None
    ts, context = entry
    if time.monotonic() - ts > config.RAG_CACHE_TTL_SECONDS:
        _RAG_CACHE.pop(key, None)
        return None
    return context


def _rag_cache_put(key: str, context: str) -> None:
    if config.RAG_CACHE_TTL_SECONDS <= 0 or not key or not context:
        return
    if len(_RAG_CACHE) >= _RAG_CACHE_MAX:      # bounded: evict the oldest entry
        _RAG_CACHE.pop(next(iter(_RAG_CACHE)))
    _RAG_CACHE[key] = (time.monotonic(), context)


def _context_hint(state) -> str:
    """Deterministic co-reference context (rule 8, ZERO model calls): salient
    content words the retrieval query/rewrite can ground a pronoun against —
    last_action summary, session_facts, the pending flow name, then recent
    messages newest-first. Words already in the current message, stopwords,
    and short tokens are dropped; the hint is hard-capped so it can prime a
    query but never drown it. A pre-search LLM rewrite would resolve
    co-reference better — and add 300-600ms to EVERY retrieval turn, which is
    the exact latency conditional retrieval exists to save (report-12 R-01)."""
    parts = []
    la = state.get("last_action") or {}
    if la.get("summary"):
        parts.append(str(la["summary"]))
    parts.extend(str(v) for v in (state.get("session_facts") or {}).values())
    if state.get("pending_intent"):
        parts.append(str(state["pending_intent"]).replace("_", " "))
    prior = (state.get("recent_messages") or [])[:-1]   # exclude the current message
    parts.extend(str(m.content) for m in reversed(prior[-4:]))

    current = set(re.findall(r"[a-z0-9']+", (state.get("user_message", "") or "").lower()))
    words, seen = [], set()
    for part in parts:
        for w in re.findall(r"[A-Za-z0-9'-]+", part):
            lw = w.lower()
            if len(lw) < 3 or lw in config._STOPWORDS or lw in current or lw in seen:
                continue
            seen.add(lw)
            words.append(w)
            if len(words) >= 24:
                return " ".join(words)
    return " ".join(words)


async def agentic_retrieval_node(state) -> dict:
    """Semantic-memory hop for RETRIEVAL_INTENTS: invoke the compiled RAG
    subgraph (private RagState loop) and copy back EXACTLY ONE key. The
    subgraph's documents/grades/counters never touch the parent state.

    Dynamic-RAG boundary work happens HERE, deterministically (rules 8-9):
    a referential query is PRIMED with a context hint before the first
    retrieve (and the same hint rides along as history_hint so a rewrite-on-
    miss can resolve the pronoun), and a non-referential repeat question is
    served from the TTL context cache without touching the subgraph at all.

    The wall-clock ceiling also lives HERE (Agentic_RAG_Explained.txt rule 6):
    the whole loop runs under config.RAG_TIMEOUT_SECONDS. On timeout, degrade
    to ONE deterministic retrieve pass and use whatever it returns — degraded
    context beats a hung prompt; an empty result routes to the knowledge
    node's honest fallback, never to a retry."""
    message = state.get("user_message", "")
    referential = bool(_REFERENTIAL_RE.search(message))
    hint = _context_hint(state) if referential else ""
    query = f"{message} {hint}".strip() if hint else message

    cache_key = _rag_cache_key(message)
    if not referential:
        cached = _rag_cache_get(cache_key)
        if cached is not None:
            logger.info("agentic_retrieval: context cache hit (subgraph skipped)")
            return {"retrieved_context": cached}

    try:
        out = await asyncio.wait_for(
            rag_subgraph.ainvoke({"query": query, "original_query": message,
                                  "history_hint": hint, "rewrite_count": 0}),
            timeout=config.RAG_TIMEOUT_SECONDS,
        )
        context = out.get("context", "")
    except asyncio.TimeoutError:
        logger.warning("retrieval subgraph exceeded %.1fs wall clock; degrading to single-hop",
                       config.RAG_TIMEOUT_SECONDS)
        try:
            docs = [d for d in config.RETRIEVER(query)
                    if d.get("score", 0) >= config.RETRIEVAL_MIN_SCORE]
            context = "\n".join(f"[{d['title']}] {d['text']}" for d in docs)
        except Exception:
            context = ""
    except Exception as e:
        logger.warning("retrieval subgraph failed (%s); continuing without context",
                       type(e).__name__)
        context = ""
    if not referential:
        _rag_cache_put(cache_key, context)
    logger.info("agentic_retrieval -> %d chars of context%s", len(context),
                " (primed)" if hint else "")
    return {"retrieved_context": context}


def _word_count(text: str) -> int:
    """Spoken-word count for the reply budget. Punctuation-only tokens (a bare
    em dash) are not words — matches selftest's voice-budget counter."""
    return len([w for w in (text or "").split() if any(c.isalnum() for c in w)])


def _is_objection(state) -> bool:
    """An objection turn, decided from the STRUCTURED intent only (never prose,
    never the raw message). False for every agent with no OBJECTION_INTENTS."""
    intents = tuple(getattr(config, "OBJECTION_INTENTS", ()) or ())
    return bool(intents) and state.get("intent", "") in intents


def _objection_ctx(state) -> str:
    """ACKNOWLEDGE (step 1 of A-I-P): prompt shaping for an objection turn, zero
    extra model calls. Returned as the knowledge prompt's TAIL, replacing the
    help-desk 'offer further help' line rather than stacking on it.

    It forbids the model from asking a question, because the turn's ONE question
    is owned by the deterministic layer that runs after it — the isolate question
    (first objection) or the director's pivot (every later one). A model-authored
    question here would collide with that and ship two questions in one breath.
    Empty for non-objection turns, so ordinary knowledge prompts are unchanged."""
    if not _is_objection(state):
        return ""
    return (f"The lead just pushed back — this is an OBJECTION, not a question. Validate it "
            f"first in under six words ('Totally fair', 'I hear you'), then answer it in ONE "
            f"short sentence using ONLY the facts above. Stay under {config.MAX_REPLY_WORDS} "
            "words total and do NOT ask a question or add a next step — your next move is "
            "appended for you. Never argue with the lead or repeat a rebuttal they already heard.")


async def knowledge_node(state) -> dict:
    intent = state.get("intent", "")
    retrieval = intent in config.RETRIEVAL_INTENTS
    retrieved = state.get("retrieved_context", "") if retrieval else ""

    if retrieval and not retrieved:
        # Zero-hallucination fallback: retrieval found nothing relevant ->
        # say so deterministically; never let a model guess a policy.
        # WARNING (not INFO): an honest decline is indistinguishable from a
        # recall failure at every other surface — this line is the only signal
        # an operator can grep to audit whether declined questions were truly
        # out of scope or a corpus/alias gap (see retrieval_coverage_preflight).
        logger.warning("rag recall exhausted: intent=%s query=%r — declined honestly; "
                       "if this should be answerable, DOCS/aliases have a gap",
                       intent, state.get("user_message", ""))
        text = ("I don't have that information on hand, so I won't guess — "
                "a human agent can confirm the details for you.")
        return {"draft_response": text + _resume_suffix(state), "needs_enrichment": False}

    if retrieval:
        # Deterministic mock synthesis from the retrieved context; live mode
        # gets the context injected into the knowledge prompt instead of FACTS.
        mock = f"Here's what our policy says: {retrieved.splitlines()[0]} {config._pick_closing()}"
    else:
        mock = config.MOCK_KNOWLEDGE.get(intent,
                                         "I can help with that — could you tell me a bit more?")
    text = await _answer_or_mock(
        state,
        prompts.build_knowledge_system(_grounding_ctx(state), retrieved, _objective_ctx(state),
                                       _summary_ctx(state), _objection_ctx(state)),
        mock, anchor=_recency_anchor(state))
    return {"draft_response": text + _resume_suffix(state), "needs_enrichment": False}


async def system_node(state) -> dict:
    """SYSTEM intents are session control — always deterministic, never a
    model. help preserves a pending flow (it's a detour); restart is the one
    EXPLICIT abandonment that clears pending state; human_handoff (invariant
    26) is the structurally reachable escalation path — it sets the
    handoff_requested flag the Shell/host observes, clears pending work
    (invariant 11 names handoff as a legitimate clearer: a person takes over),
    and keeps last_action/session_facts so the human inherits the context."""
    intent = state.get("intent", "")
    if intent == "restart":
        return _clear_plan(_clear_pending({"draft_response": config.RESTART_TEXT,
                                           "needs_enrichment": False, "last_action": {},
                                           "session_facts": {}, "paused_flow": {},
                                           "stall_count": 0, "last_reply_fingerprint": "",
                                           "objections_raised": [], "turns_since_tiedown": 0}))
    if intent == "human_handoff":
        logger.info("escalation: human handoff requested")
        return _clear_plan(_clear_pending({"draft_response": config.HANDOFF_TEXT,
                                           "needs_enrichment": False, "paused_flow": {},
                                           "handoff_requested": True,
                                           "stall_count": 0, "last_reply_fingerprint": ""}))
    return {"draft_response": config.HELP_TEXT + _resume_suffix(state),
            "needs_enrichment": False}


async def chitchat_node(state) -> dict:
    if state.get("confirmation_declined"):
        # Deterministic decline acknowledgment — never let a model improvise
        # around an aborted destructive action.
        return {"draft_response": config.CONFIRM_DECLINED_TEXT, "needs_enrichment": False}
    la = state.get("last_action") or {}
    if llm_client.mock and la and _GROUNDING_Q_RE.search(state.get("user_message", "")):
        text = f"That comes straight from our live system — {la.get('summary', '')}"
    else:
        text = await _answer_or_mock(
            state,
            prompts.build_chitchat_system(_grounding_ctx(state), _objective_ctx(state),
                                          _summary_ctx(state)),
            config.MOCK_CHITCHAT, anchor=_recency_anchor(state))
    return {"draft_response": text + _resume_suffix(state), "needs_enrichment": False}


async def closing_node(state) -> dict:
    text = await _answer_or_mock(state, prompts.CLOSING_SYSTEM, config.MOCK_CLOSING)
    return _clear_plan(_clear_pending({"draft_response": text, "needs_enrichment": False,
                                       "exit_conversation": True, "paused_flow": {}}))


async def _answer_or_mock(state, system: str, mock_text: str, anchor: str = "") -> str:
    if llm_client.mock:
        return mock_text
    messages = ([{"role": "system", "content": system}] + _history(state)
                + [{"role": "user", "content": state.get("user_message", "")}])
    # Recency anchor: a compact goal/firm-no reminder placed LAST (after history +
    # the latest user turn) so it stays salient as the window fills. Empty for
    # inbound agents, so their message list is unchanged.
    if anchor:
        messages.append({"role": "system", "content": anchor})
    try:
        return await llm_client.generate_text(ANSWER_MODEL, messages, temperature=0.5)
    except Exception as e:
        logger.warning("answer tier failed (%s); using mock text", type(e).__name__)
        return mock_text


def _grounding_ctx(state) -> str:
    """Ground direct answers on the last completed tool action so the agent can
    explain WHERE a fact came from instead of deflecting to a capabilities pitch."""
    la = state.get("last_action") or {}
    if not la:
        return ""
    return (f"\n\nMOST RECENT COMPLETED ACTION (ground truth from our live system): tool "
            f"'{la.get('tool')}' returned: {json.dumps(la.get('result', {}), ensure_ascii=False)}\n"
            "If the user asks how you know something or questions your last answer, explain that "
            "it comes from this live system check and restate the key fact. If their message "
            "refers to this action (payment remarks, thanks, follow-ups), respond grounded in it; "
            "if it involves something you cannot do on this channel, say so plainly — never "
            "invent options or claim things changed.")


def _resume_suffix(state) -> str:
    """If a flow (or confirmation) is pending, remind the user how to continue —
    a detour must never silently abandon the task in progress."""
    confirm = state.get("pending_confirmation") or {}
    if confirm.get("question"):
        return " Now, back to where we were: " + confirm["question"]
    pending = state.get("pending_intent")
    if pending and pending in config.FLOWS:
        flow = config.FLOWS[pending]
        pending_slots = state.get("pending_slots") or {}
        missing = [s for s in flow.slots if not pending_slots.get(s)]
        if missing:
            hint = flow.slot_prompts.get(missing[0], missing[0])
            return (f" Now, back to your {pending.replace('_', ' ')} — "
                    f"could you tell me {hint}?")
    return ""


# ======================================================================== #
# 2d. PLANNER (Tier: ANSWER, called EXACTLY ONCE per compound request)      #
# ======================================================================== #
async def planner_node(state) -> dict:
    """Plan-and-Execute entry: convert a multi-action utterance into an ordered
    plan_steps array. The heavy model runs ONCE here; every subsequent step is
    executed deterministically by plan_step_node through the ordinary
    think->act machinery. The output is clamped in code: unknown actions are
    dropped, the array is truncated to MAX_PLAN_STEPS, and slot keys outside
    the flow's contract are discarded — a hallucinated plan cannot widen the
    agent's capabilities."""
    if llm_client.mock:
        steps = _mock_compound(state.get("user_message", "")) or []
    else:
        messages = ([{"role": "system",
                      "content": prompts.build_planner_system(_session_facts_ctx(state))}]
                    + _history(state)
                    + [{"role": "user", "content": state.get("user_message", "")}])
        try:
            result = await llm_client.generate_structured(ANSWER_MODEL, PlanResult, messages,
                                                          temperature=0.2)
            steps = result.steps or []
        except Exception as e:
            logger.warning("planner tier failed (%s); heuristic fallback", type(e).__name__)
            steps = _mock_compound(state.get("user_message", "")) or []

    plan = []
    for step in steps[: config.MAX_PLAN_STEPS]:
        if step.action not in config.FLOWS:
            logger.info("planner: dropping unknown action %r", step.action)
            continue
        allowed = config.FLOWS[step.action].slots
        slots = {k: v for k, v in (step.slots or {}).items() if v and k in allowed}
        plan.append({"step": len(plan) + 1, "action": step.action, "slots": slots,
                     "status": "pending", "summary": "", "reported": False,
                     "dispatch_calls": 0})

    if not plan:
        logger.info("planner: no valid steps — declining deterministically")
        return _clear_plan({"draft_response": config.PLAN_UNSUPPORTED_TEXT,
                            "needs_enrichment": False})
    logger.info("planner: %d step(s): %s", len(plan), [s["action"] for s in plan])
    return {"plan_steps": plan, "current_step_index": 0}


# ======================================================================== #
# 2e. PLAN STEP CONTROLLER (no model) — the ONE sanctioned parent-graph     #
#     loop: a deterministic, monotonic walk over plan_steps, doubly bounded #
#     (MAX_PLAN_STEPS at creation, MAX_TOOL_CALLS_PER_TURN at execution).   #
#     No model ever decides whether to continue.                            #
# ======================================================================== #
async def plan_step_node(state) -> dict:
    plan = [dict(s) for s in (state.get("plan_steps") or [])]
    idx = state.get("current_step_index", 0)
    updates: dict = {}

    # 1) Book-keeping: record the outcome of the step in flight (re-entry from
    #    the execution path, or from a think question that pauses the plan).
    if idx < len(plan) and plan[idx]["status"] in ("running", "paused"):
        step = plan[idx]
        if state.get("execution_error"):
            # Abort policy: a failed step stops the plan. failure_node already
            # produced the reply and re-pended the single flow for retry.
            step["status"] = "failed"
            for later in plan[idx + 1:]:
                later["status"] = "skipped"
            logger.info("plan: step %d (%s) failed — aborting remaining steps",
                        step["step"], step["action"])
            draft = state.get("draft_response", "") or config.FAILURE_TEXT
            return _clear_plan({"draft_response": _with_plan_report(plan, draft),
                                "needs_enrichment": False})
        if state.get("tool_call_count", 0) > step.get("dispatch_calls", 0):
            # An execution happened since dispatch -> the step completed.
            step["status"] = "complete"
            step["summary"] = (state.get("tool_result") or {}).get("summary", "")
            idx += 1
            updates["current_step_index"] = idx
            logger.info("plan: step %d (%s) complete", step["step"], step["action"])
        else:
            # Think asked something (missing slot / confirm question): pause.
            # pending_intent / pending_confirmation are already set by think —
            # the existing continuation machinery IS the resume mechanism.
            step["status"] = "paused"
            step["dispatch_calls"] = 0   # next turn's counter restarts at 0
            logger.info("plan: step %d (%s) paused awaiting the user",
                        step["step"], step["action"])
            return {"plan_steps": plan,
                    "draft_response": _with_plan_report(plan, state.get("draft_response", ""))}

    # 2) Finished? Emit the aggregated report (the last step's phrased reply
    #    plus any earlier unreported summaries) and clear the plan.
    if idx >= len(plan):
        if plan:
            plan[-1]["reported"] = True   # its content is the draft itself
        draft = state.get("draft_response", "") or ""
        logger.info("plan: all %d step(s) complete", len(plan))
        return _clear_plan({"draft_response": _with_plan_report(plan, draft),
                            "needs_enrichment": False})

    # 3) Dispatch the next step, context-isolated: the step's action IS the
    #    intent (no INTENT-tier call), and its slots are a deterministic merge
    #    of session_facts (earlier steps' outputs — the variable-mapping bus)
    #    with the planner's per-step extraction (planner values win).
    step = plan[idx]
    flow = config.FLOWS[step["action"]]
    facts = state.get("session_facts") or {}
    slots = {**{k: v for k, v in facts.items() if k in flow.slots}, **step["slots"]}
    step["status"] = "running"
    step["dispatch_calls"] = state.get("tool_call_count", 0)
    # Filler channel: a natural "still working" continuation covers the gap
    # before each step AFTER the first (the first step's own tool filler already
    # signals work; the first spoken line should not be a bare "still working").
    if idx >= 1 and config.FILLER_ENABLED:
        cont = filler.pick_from(config.FILLER_PLAN_CONTINUE, key="_plan")
        if cont:
            filler.emit({"type": "filler", "kind": "plan", "text": cont,
                         "step": idx + 1, "total": len(plan)})
    logger.info("plan: dispatching step %d/%d (%s) slots=%s",
                step["step"], len(plan), step["action"], slots)
    return {**updates, "plan_steps": plan, "intent": step["action"],
            "category": "FLOW", "slots": slots}


def _with_plan_report(plan: list, draft: str) -> str:
    """Prefix a reply with the summaries of completed-but-unreported steps so a
    pause, an abort, or the final reply always accounts for what already ran."""
    earlier = [s["summary"] for s in plan
               if s["status"] == "complete" and not s["reported"] and s["summary"]]
    for s in plan:
        if s["status"] == "complete":
            s["reported"] = True
    return " ".join(earlier + ([draft] if draft else [])).strip()


# ======================================================================== #
# 3. THINK (Tier: ANSWER) — one generic node for every config.FLOWS intent  #
# ======================================================================== #
async def think_node(state, thread_id: str = "", ledger=None) -> dict:
    intent = state.get("intent", "")
    flow = config.FLOWS[intent]
    slots = dict(state.get("slots") or {})

    # Deterministic pre-fill BEFORE the model or the lead is ever asked: never
    # interrogate the lead for a value the agent already holds or can derive.
    #   (1) session_facts by slot-name — outbound-call metadata (email, name,
    #       phone) the runtime seeded on turn 1, plus earlier tools' cached
    #       outputs. This is the SAME variable-bus plan_step_node uses; here it
    #       covers the single-flow path too, so a slot already known out-of-band
    #       is filled, not asked ("what's your email?" when it's in the metadata).
    #   (2) a slot with NO spoken slot_prompt is one the agent is never meant to
    #       ask aloud (e.g. a fixed email body) — so it MUST be derivable; fill
    #       it from its own SLOT_EXTRACTOR on this message. Such an extractor is
    #       authoritative by contract (a no-prompt slot has no ask to fall back
    #       on), so it must stay live-safe, never a mock placeholder.
    # The lead's own spoken value still wins: decision.slots overrides these
    # below, and the resolver/validator pass re-checks every filled value.
    _facts = state.get("session_facts") or {}
    for s in flow.slots:
        if slots.get(s):
            continue
        if _facts.get(s):
            slots[s] = _facts[s]
        elif s not in flow.slot_prompts:
            fn = config.SLOT_EXTRACTORS.get(s)
            val = fn(state.get("user_message", "")) if fn else None
            if val:
                slots[s] = val

    if llm_client.mock:
        decision = _mock_think(flow, slots)
    else:
        now = datetime.now().astimezone()
        known = {s: slots.get(s) for s in flow.slots}
        messages = ([{"role": "system",
                      "content": prompts.build_think_system(intent, known, now.isoformat(), f"{now:%A}",
                                                            _session_facts_ctx(state),
                                                            _objective_ctx(state), _summary_ctx(state))}]
                    + _history(state) + [{"role": "user", "content": state.get("user_message", "")}])
        try:
            decision = await llm_client.generate_structured(ANSWER_MODEL, ThinkDecision, messages, temperature=0.2)
        except Exception as e:
            logger.warning("think tier failed (%s); heuristic fallback", type(e).__name__)
            decision = _mock_think(flow, slots)

    slots.update({k: v for k, v in (decision.slots or {}).items() if v})

    # SEMANTIC ENTITY RESOLUTION first (config.ENTITY_RESOLVERS): referential
    # values ("all vegetables", "any branch", aliases) are grounded against the
    # domain catalog — canonicalized or bounced with a clarifying question —
    # BEFORE scalar validators see them. A literal referential string never
    # reaches a tool.
    # Then Flow.validators: normalize units/bounds/format or reject with a
    # clarification — silent unit/bounds mismatches never reach a tool either.
    for hooks in (config.ENTITY_RESOLVERS, flow.validators):
        for s in flow.slots:
            val = slots.get(s)
            fn = hooks.get(s)
            # SLOT_REFUSED is a terminal sentinel, not a value: validating it
            # would bounce it back to None and resurrect the re-ask loop.
            if not val or fn is None or val == config.SLOT_REFUSED:
                continue
            ok, out = fn(str(val), slots)
            if ok:
                slots[s] = out
            else:
                slots[s] = None
                logger.info("slot %s=%r rejected (%s)", s, val,
                            "entity resolver" if hooks is config.ENTITY_RESOLVERS else "validator")
                return {"draft_response": out, "needs_enrichment": False,
                        "tool_action_pending": False, "pending_confirmation": {},
                        "pending_intent": intent, "pending_slots": slots, "slots": slots}

    missing = [s for s in flow.slots if not slots.get(s)]

    if decision.status == "act" and not missing:
        args = {s: slots[s] for s in flow.slots}
        gates = authz.flow_gates(flow)
        if "confirm" in gates:
            # State-changing flow: stash the ready payload and ask before
            # acting. The question is the moment the user is shown this exact
            # payload, so the platform's confirm OFFER is minted here.
            question = _confirm_question(intent, flow, args)
            _offer(ledger, "confirm", thread_id, intent, flow.tool, args)
            return {"draft_response": question, "needs_enrichment": False,
                    "tool_action_pending": False, "slots": slots,
                    "pending_intent": intent, "pending_slots": slots,
                    "pending_confirmation": {"intent": intent, "tool": flow.tool,
                                             "args": args, "question": question}}
        if "hitl" in gates:
            # Liability flow: the payload is ready but an OPERATOR must
            # approve it — route to the interrupt gate instead of acting.
            return _clear_pending({
                "cold_payload": {"tool": flow.tool, "args": args},
                "tool_action_pending": False, "awaiting_human": True, "slots": slots,
            })
        return _clear_pending({
            "cold_payload": {"tool": flow.tool, "args": args},
            "tool_action_pending": True, "slots": slots,
        })
    # need_info: ask for the first missing slot, remember the flow for next turn.
    ask = decision.response or _ask_for(flow, missing)
    return {
        "draft_response": ask,
        "needs_enrichment": False,
        "tool_action_pending": False,
        "pending_intent": intent,
        "pending_slots": slots,
        "pending_confirmation": {},   # a new Think supersedes any stale confirmation
    }


def _ask_for(flow: config.Flow, missing: list) -> str:
    slot = missing[0] if missing else flow.slots[0]
    hint = flow.slot_prompts.get(slot, slot)
    return f"Could you tell me {hint}?"


_ISO_DT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?")


def _speak_value(value):
    """Slots may carry raw ISO-8601 datetimes (the reliable machine format for
    a booking tool) — SPOKEN strings can never surface that literally, so
    render it as a natural phrase before it reaches any template. Non-ISO
    values pass through untouched."""
    if not (isinstance(value, str) and _ISO_DT_RE.match(value)):
        return value
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return value
    hour12 = dt.hour % 12 or 12
    minute = f":{dt.minute:02d}" if dt.minute else ""
    ampm = "AM" if dt.hour < 12 else "PM"
    return f"{dt.strftime('%A, %B')} {dt.day} at {hour12}{minute} {ampm}"


def _confirm_question(intent: str, flow: config.Flow, args: dict) -> str:
    if flow.confirm_template:
        try:
            return flow.confirm_template.format(**{k: _speak_value(v) for k, v in args.items()})
        except (KeyError, IndexError):
            pass
    detail = f" ({', '.join(f'{k}: {v}' for k, v in args.items())})" if args else ""
    return f"Just to confirm — should I go ahead and {intent.replace('_', ' ')}{detail}? (yes/no)"


def _mock_think(flow: config.Flow, slots: dict) -> ThinkDecision:
    missing = [s for s in flow.slots if not slots.get(s)]
    if not missing:
        return ThinkDecision(status="act", slots={s: slots[s] for s in flow.slots})
    return ThinkDecision(status="need_info", slots={}, response=_ask_for(flow, missing))


# ======================================================================== #
# 3b. HITL GATE (no model) — interrupt() for OPERATOR approval               #
# ======================================================================== #
def _offer(ledger, gate: str, thread_id: str, flow: str, tool: str, args: dict):
    """Mint the platform offer for `gate`; None when it cannot be minted (no
    ledger, no conversation id, args that do not canonicalize). A missing offer
    is not an error HERE — it simply leaves nothing to grant, and tool_exec
    refuses the run."""
    if ledger is None or not thread_id:
        logger.warning("no %s offer minted for %s: ledger=%s thread=%r",
                       gate, tool, ledger is not None, thread_id)
        return None
    try:
        return ledger.offer(gate, ledger.binding(thread_id, flow, tool, args))
    except TypeError as e:
        logger.warning("no %s offer minted for %s: args not canonical (%s)", gate, tool, e)
        return None


async def hitl_gate_node(state, thread_id: str = "", ledger=None) -> dict:
    """Liability flows: the graph SUSPENDS here (checkpoint-persisted) with
    the ready payload and resumes only on an operator
    Command(resume={"approved": bool, "offer_id": <the id shown>}).
    Distinct from the confirm gate (end-user yes/no): this is the hard
    excessive-agency gate — the model cannot talk its way past it.

    The node re-runs from the top on resume, so the offer is minted
    idempotently: an unchanged payload finds the same offer id it showed; a
    payload changed during the suspension gets a NEW id, and the operator's
    approval of the old one no longer matches."""
    payload = state.get("cold_payload", {})
    tool = payload.get("tool", "")
    offer_id = _offer(ledger, "hitl", thread_id, state.get("intent", ""), tool,
                      payload.get("args", {}))
    if offer_id is None:
        return _hitl_refused(state, authz.Refusal(
            authz.PLATFORM_ERROR, "could not open an approval record", "hitl"), tool)
    decision = interrupt({
        "type": "hitl_approval",
        "intent": state.get("intent", ""),
        "tool": tool,
        "args": payload.get("args", {}),
        "offer_id": offer_id,
    })
    if not isinstance(decision, dict) or not decision.get("approved"):
        ledger.revoke("hitl", thread_id)
        logger.info("hitl DENIED for %s [thread=%s]", tool, thread_id)
        return _hitl_refused(state, authz.Refusal(
            authz.BUSINESS_REFUSAL, "operator denied", "hitl"), tool)
    named = decision.get("offer_id")
    refused = (ledger.grant("hitl", thread_id, offer_id=named) if isinstance(named, str) and named
               else authz.Refusal(authz.PLATFORM_ERROR, "approval does not name an offer", "hitl"))
    if refused is not None:
        logger.warning("hitl approval REFUSED for %s [thread=%s]: %s", tool, thread_id, refused.reason)
        ledger.revoke("hitl", thread_id)
        return _hitl_refused(state, refused, tool)
    logger.info("hitl APPROVED for %s [thread=%s offer=%s]", tool, thread_id, offer_id)
    return {"tool_action_pending": True, "awaiting_human": False}


def _hitl_refused(state, refusal, tool: str) -> dict:
    """No execution. An operator's no is told as a decision; a platform
    failure to establish approval is told as a snag (nothing changed) — the
    two never share wording, and `refusal` tells the Shell which it was."""
    text = (config.HITL_DENIED_TEXT if refusal.kind == authz.BUSINESS_REFUSAL
            else config.FAILURE_TEXT)
    updates = {"needs_enrichment": False, "tool_action_pending": False,
               "awaiting_human": False, "cold_payload": {},
               "refusal": refusal.as_dict(tool)}
    if _plan_active(state):
        # A refusal mid-plan aborts the remaining steps (later steps may depend
        # on the refused one) but still reports what already completed.
        plan = [dict(s) for s in state.get("plan_steps") or []]
        text = _with_plan_report(plan, text)
        updates = _clear_plan(updates)
    updates["draft_response"] = text
    return _clear_pending(updates)


def _authorize(state, name: str, thread_id: str, ledger):
    """Execution-time gate check, run by tool_exec BEFORE the tool. Returns a
    Refusal, or None when the tool needs no gate or every required gate holds a
    granted, unconsumed record for exactly this payload (consumed here)."""
    flow = FLOW_BY_TOOL.get(name)
    gates = authz.flow_gates(flow) if flow is not None else frozenset()
    if not gates:
        return None
    intent = state.get("intent", "")
    active = config.FLOWS.get(intent)
    if active is None or active.tool != name:
        return authz.Refusal(authz.PLATFORM_ERROR,
                             f"tool {name} does not belong to the active flow {intent!r}")
    if ledger is None or not thread_id:
        return authz.Refusal(authz.PLATFORM_ERROR, "no authorization ledger or conversation id")
    try:
        binding = ledger.binding(thread_id, intent, name, state.get("cold_payload", {}).get("args", {}))
    except TypeError as e:
        return authz.Refusal(authz.PLATFORM_ERROR, f"arguments are not canonical: {e}")
    return ledger.consume(gates, binding)


# ======================================================================== #
# 4. ACT (deterministic tool execution via registry, circuit-breaker guarded)#
# ======================================================================== #
async def tool_exec_node(state, thread_id: str = "", ledger=None) -> dict:
    payload = state.get("cold_payload", {})
    name = payload.get("tool", "")
    calls = state.get("tool_call_count", 0)

    # Circuit breaker: a turn gets a hard budget of tool executions. One
    # Think->Act hop needs exactly 1; anything past the cap is a runaway.
    if calls >= config.MAX_TOOL_CALLS_PER_TURN:
        logger.warning("circuit breaker: %d tool calls this turn (cap %d) — refusing %s",
                       calls, config.MAX_TOOL_CALLS_PER_TURN, name)
        result = {"tool": name or "unknown",
                  "error": f"circuit breaker: exceeded {config.MAX_TOOL_CALLS_PER_TURN} tool calls per turn",
                  "summary": "Too many actions were attempted in one turn."}
        return {"tool_result": {**result, "tool_status": "refused"},
                "tool_action_pending": False, "tool_call_count": calls}

    # Execution-time authorization: whatever routed here (a yes, an operator
    # approval, or state that merely CLAIMS one), a gated tool runs only on a
    # platform record for this exact payload. Nothing ran, so the call
    # counter does not move.
    refusal = _authorize(state, name, thread_id, ledger)
    if refusal is not None:
        logger.warning("authorization refused for %s [thread=%s intent=%s]: %s",
                       name, thread_id, state.get("intent", ""), refusal.reason)
        result = {"tool": name or "unknown", "error": f"not authorized: {refusal.reason}",
                  "refusal": refusal.kind, "tool_status": "refused",
                  "summary": config.FAILURE_TEXT}
        return {"tool_result": result, "tool_action_pending": False,
                "tool_call_count": calls, "refusal": refusal.as_dict(name)}

    fn = tools.TOOL_REGISTRY.get(name)
    if fn is None:
        result = {"tool": name or "unknown", "error": "no such tool", "tool_status": "refused",
                  "summary": "I hit a snag completing that — a human agent will follow up."}
    else:
        # Filler channel: cover the tool's latency with a canned acknowledgment
        # over the display-only side sink (never enters model context). Debounced
        # — the phrase is emitted ONLY if the tool outlasts FILLER_DELAY_MS, so
        # fast tools stay silent (the voice runtime forces FILLER_DELAY_MS=0 so
        # fillers ARE the latency cover). Filler failures never affect the result.
        #
        # A SYNC tool body (e.g. a blocking smtplib / requests call) is offloaded
        # to a worker thread via asyncio.to_thread. Running it inline on the event
        # loop would freeze the loop until it returns: no timer could race it, the
        # filler queue would stall, AND the runtime's wall-clock dead-air ceiling
        # (Rule 8) could never fire — a hung socket would become silence on the
        # call. Offloading keeps the loop free to drain fillers and enforce the
        # ceiling, and lets a slow sync tool be covered by a filler like an async
        # one. Async (MCP-wrapped) tools are awaited directly.
        filler_text = filler.pick(name)
        args = payload.get("args", {})
        try:
            if asyncio.iscoroutinefunction(fn):
                task = asyncio.ensure_future(fn(**args))
            else:
                task = asyncio.ensure_future(asyncio.to_thread(fn, **args))
            if filler_text is not None:
                done, _ = await asyncio.wait({task}, timeout=max(config.FILLER_DELAY_MS, 0) / 1000)
                if not done:
                    filler.emit({"type": "filler", "kind": "tool", "tool": name, "text": filler_text})
            # Every tool call is bounded: a hung backend becomes a typed
            # timeout, never a turn that waits for the Shell's own ceiling. A
            # sync tool's worker thread cannot be killed and may still finish
            # — which is exactly why a timed-out effect is "unverified", not
            # "nothing changed" (execution_validator).
            timeout = _setting("TOOL_TIMEOUT_S", 15.0)
            result = await asyncio.wait_for(task, timeout=timeout)
            if asyncio.iscoroutine(result):   # a sync factory that returns a coroutine
                result = await asyncio.wait_for(result, timeout=timeout)
            if isinstance(result, dict):
                result = {**result, "tool_status": "error" if result.get("error") else "ok"}
        except asyncio.TimeoutError:
            logger.warning("tool %s timed out after %.2fs [thread=%s]", name, timeout, thread_id)
            result = {"tool": name, "error": f"{name} timed out after {timeout:g}s",
                      "tool_status": "timeout",
                      "summary": "I hit a snag completing that — a human agent will follow up."}
        except Exception as e:
            logger.exception("tool %s crashed", name)
            result = {"tool": name, "error": str(e), "tool_status": "crashed",
                      "summary": "I hit a snag completing that — a human agent will follow up."}
    logger.info("tool %s -> %s", name, result)

    # Tool-result compaction (zero-model, never raises): oversized list fields
    # in a HEALTHY result are crushed to a salient subset + retrieval sentinel
    # BEFORE the result reaches state — every downstream consumer (ENRICH
    # prompt, last_action grounding, history) pays for the compact form only.
    # Error results pass through untouched; the retrieval store keeps the
    # original for retrieve_full_result.
    if config.COMPACTION_ENABLED and isinstance(result, dict):
        result = compaction.crush_result(result)

    # The session cache and last_action (grounding, flow completion) are NOT
    # written here: a tool's own report is not evidence. execution_validator
    # writes them once the outcome is classified (verified / unchecked).
    return {"tool_result": result, "tool_action_pending": False,
            "tool_call_count": calls + 1}


# ======================================================================== #
# 4b. EXECUTION VALIDATOR (no model) — Layer 2.5, decoupled from the exit    #
#     filter. Inspects the raw tool result BEFORE any phrasing: failures     #
#     route to the failure node; healthy results route to ENRICH or bypass   #
#     it entirely (Flow.enrich=False) for deterministic sub-600ms replies.   #
# ======================================================================== #
async def execution_validator_node(state) -> dict:
    """Classify what the tool call actually achieved, from evidence:

      verified    tool ok AND its read-back (tools.VERIFIERS) shows exactly
                  this effect                              -> success path
      unchecked   no read-back exists and the flow is not gated (a read-only
                  lookup), tool ok                         -> success path
      failed      the tool never ran (refused), a read-only tool erred, or an
                  effect tool RETURNED an error and the read-back proves
                  nothing landed                           -> FAILURE_TEXT, retryable
      unverified  an effect was attempted and none of the above holds:
                  timeout, crash, dropped write, mismatched or unreadable
                  read-back, or a gated tool with no read-back at all
                                                          -> UNVERIFIED_TEXT

    Only verified/unchecked results reach enrichment, the session cache and
    last_action — so nothing downstream can phrase, cache or count as done an
    effect nobody saw land."""
    result = state.get("tool_result", {}) or {}
    payload = state.get("cold_payload", {}) or {}
    tool = (result.get("tool") if isinstance(result, dict) else "") or payload.get("tool", "")
    outcome = await _classify_outcome(tool, result, payload.get("args", {}) or {})
    logger.info("execution validator: %s for %s (%s)", outcome["outcome"].upper(), tool,
                outcome.get("evidence") or outcome.get("reason", ""))
    updates: dict = {"action_outcome": outcome}

    if outcome["outcome"] in ("failed", "unverified"):
        updates.update(needs_enrichment=False, execution_error={
            "tool": tool, "error": outcome["reason"], "outcome": outcome["outcome"]})
        if outcome["outcome"] == "unverified":
            # Grounding must not repeat the tool's success summary, and the
            # flow must not count as complete (its result carries an error).
            updates["last_action"] = {"tool": tool, "summary": _unverified_text(),
                                      "result": {**result, "error": f"unverified: {outcome['reason']}"}}
        elif result.get("tool_status") != "refused":
            updates["last_action"] = {"tool": tool, "summary": result.get("summary", ""),
                                      "result": result}
        return updates

    # Functional session cache (zero-inference update): only after an outcome
    # the platform can stand behind, copy the flow's whitelisted result fields
    # into session_facts with a code-level dict merge.
    facts = dict(state.get("session_facts") or {})
    flow = FLOW_BY_TOOL.get(tool)
    for key in (flow.cache_keys if flow is not None else ()):
        if result.get(key):
            facts[key] = str(result[key])
    updates.update(execution_error={}, session_facts=facts,
                   # Grounding memory: persists across turns so follow-ups
                   # ("how do you know?") are understood in context.
                   last_action={"tool": tool, "summary": result.get("summary", ""), "result": result})
    enrich = flow.enrich if flow is not None else True
    if not enrich:
        # SLM bypass: the tool's summary is already user-ready — phrase it
        # deterministically here (summary + declared hint), zero model hops.
        updates["needs_enrichment"] = False
        updates.update(_offer_paused(state, _phrase_result(result)))
        return updates
    updates["needs_enrichment"] = True
    return updates


def _setting(name: str, default):
    """An engine knob the agent's config.py may set. config.py is per agent and
    may predate the knob, so absence means the engine default."""
    return getattr(config, name, default)


_UNVERIFIED_DEFAULT = ("I couldn't confirm that went through on our side, so please don't "
                       "count on it yet. A team member will check and get back to you.")


def _unverified_text() -> str:
    return _setting("UNVERIFIED_TEXT", _UNVERIFIED_DEFAULT)


async def _read_back(verifier, args: dict, result: dict) -> tuple:
    """Run a verifier bounded by VERIFY_TIMEOUT_S. Returns (status, detail);
    status "unreadable" when it raised or timed out — never a guess."""
    timeout = _setting("VERIFY_TIMEOUT_S", 5.0)
    try:
        if asyncio.iscoroutinefunction(verifier):
            out = await asyncio.wait_for(verifier(args, result), timeout=timeout)
        else:
            out = await asyncio.wait_for(asyncio.to_thread(verifier, args, result), timeout=timeout)
    except asyncio.TimeoutError:
        return "unreadable", f"read-back timed out after {timeout:g}s"
    except Exception as e:   # domain code: any failure is "could not read", typed below
        logger.warning("read-back raised %s: %s", type(e).__name__, e)
        return "unreadable", f"read-back failed: {type(e).__name__}: {e}"
    if not (isinstance(out, tuple) and len(out) == 2 and out[0] in ("present", "absent", "mismatch")):
        return "unreadable", f"verifier returned an invalid verdict {out!r}"
    return out


async def _classify_outcome(tool: str, result, args: dict) -> dict:
    if not isinstance(result, dict):
        return {"outcome": "failed", "verified": None, "tool_status": "malformed",
                "reason": "malformed tool result"}
    status = result.get("tool_status") or ("error" if result.get("error") else "ok")
    healthy = status == "ok" and bool(result.get("summary"))
    if status == "refused":
        return {"outcome": "failed", "verified": None, "tool_status": status,
                "reason": str(result.get("error", "refused before running"))}

    flow = FLOW_BY_TOOL.get(tool)
    verifier = getattr(tools, "VERIFIERS", {}).get(tool)
    gated = flow is not None and bool(authz.flow_gates(flow))
    if verifier is None and not gated:
        # Read-only: a failed lookup changed nothing.
        if healthy:
            return {"outcome": "unchecked", "verified": None, "tool_status": status}
        return {"outcome": "failed", "verified": None, "tool_status": status,
                "reason": str(result.get("error") or "malformed tool result")}
    if verifier is None:
        return {"outcome": "unverified", "verified": False, "tool_status": status,
                "reason": f"gated tool {tool} has no read-back in tools.VERIFIERS"}

    seen, detail = await _read_back(verifier, args, result)
    if healthy and seen == "present":
        return {"outcome": "verified", "verified": True, "tool_status": status, "evidence": detail}
    if status == "error" and seen == "absent":
        # The tool returned (did not hang) and the system holds nothing:
        # "nothing was changed" is now a checked statement.
        return {"outcome": "failed", "verified": False, "tool_status": status,
                "reason": str(result.get("error")), "evidence": detail}
    return {"outcome": "unverified", "verified": False, "tool_status": status,
            "reason": f"tool {status}; read-back {seen}: {detail}"}


def _phrase_result(result: dict) -> str:
    """Deterministic tool-result phrasing: the structured summary plus the ONE
    config-declared follow-up. Used by the enrich bypass and as the enrichment
    node's mock/error fallback."""
    text = result.get("summary") or "Done."
    hint = getattr(config, "NEXT_STEP_HINTS", {}).get(result.get("tool", ""), "")
    if hint:
        text = f"{text.rstrip()} {hint}"
    if not text.rstrip().endswith("?"):
        text = f"{text.rstrip()} {config._pick_closing()}"
    return text


def _offer_paused(state, draft: str) -> dict:
    """Append the ONE-SHOT resume offer for an archived flow to a completed
    tool reply, and mark the archive as offered (deterministic — never a model
    line, never repeated: a second nag is the broken-record anti-pattern).
    Skipped mid-plan (the plan reports its own progress) and when
    config.PAUSED_RESUME_TEXT is empty (offer disabled; restore still works)."""
    paused = dict(state.get("paused_flow") or {})
    flow = config.FLOWS.get(paused.get("intent", ""))
    if (not paused or paused.get("offered") or flow is None
            or _plan_active(state) or not config.PAUSED_RESUME_TEXT):
        return {"draft_response": draft}
    slots = paused.get("slots") or {}
    missing = [s for s in flow.slots if not slots.get(s)]
    hint = (flow.slot_prompts.get(missing[0], missing[0]) if missing
            else "whether you'd like to continue")
    offer = config.PAUSED_RESUME_TEXT.format(
        flow=paused["intent"].replace("_", " "), slot_hint=hint)
    paused["offered"] = True
    return {"draft_response": f"{draft.rstrip()} {offer}", "paused_flow": paused}


# ======================================================================== #
# 4c. FAILURE (no model) — graceful degradation for a failed Act             #
# ======================================================================== #
async def failure_node(state) -> dict:
    """A tool failed (or the breaker tripped, or authorization refused it):
    tell the user plainly, keep the session alive, and keep the flow RETRYABLE
    by re-pending it with its slots — the next 'try again' resumes without
    re-collecting everything. An UNVERIFIED effect is different: see below."""
    intent = state.get("intent", "")
    if (state.get("execution_error") or {}).get("outcome") == "unverified":
        # An effect may or may not have landed. Never "nothing was changed",
        # never an invitation to retry (a retry could double it), and the
        # promised human check is wired through the Shell-observed flag.
        return {"draft_response": _unverified_text(), "needs_enrichment": False,
                "handoff_requested": True}
    updates = {"draft_response": config.FAILURE_TEXT, "needs_enrichment": False}
    if intent in config.FLOWS:
        updates["pending_intent"] = intent
        updates["pending_slots"] = dict(state.get("slots") or {})
    return updates


# ======================================================================== #
# 5. ENRICHMENT (Tier: ENRICH / SLM) — only when the execution validator    #
#    asked for it (healthy result + Flow.enrich=True)                       #
#    The SLM is FRAMED, never trusted with free prose: it returns an        #
#    EnrichVerdict (tone + grounded facts), and a DETERMINISTIC templater   #
#    builds the sentence from config.ENRICH_TEMPLATES. A small model cannot #
#    steer the conversation it never writes. This is why the old free-text  #
#    call + post-hoc question-scrubber are gone: the constraint replaces    #
#    the cleanup. Follow-ups stay config-declared (NEXT_STEP_HINTS).        #
# ======================================================================== #
async def enrichment_node(state) -> dict:
    result = state.get("tool_result", {})
    result_json = json.dumps(result, ensure_ascii=False)

    if llm_client.mock:
        return _offer_paused(state, _phrase_result(result))

    messages = [
        {"role": "system", "content": prompts.ENRICH_SYSTEM},
        {"role": "user", "content": result_json},
    ]
    try:
        verdict = await llm_client.generate_structured(
            ENRICH_MODEL, EnrichVerdict, messages, temperature=0.2)
    except Exception as e:
        logger.warning("enrichment tier failed (%s); deterministic phrasing", type(e).__name__)
        return _offer_paused(state, _phrase_result(result))

    text = _phrase_from_verdict(verdict, result)
    if text is None:                       # verdict failed grounding -> safe fallback
        return _offer_paused(state, _phrase_result(result))
    return _offer_paused(state, _finish_enriched(text, result))


def _phrase_from_verdict(verdict: EnrichVerdict, result: dict) -> str | None:
    """Assemble the user sentence DETERMINISTICALLY from the SLM's verdict.
    Independently re-verifies grounding (never trusts verdict.grounded alone):
    every key_fact must appear verbatim in the tool result. Returns None if the
    verdict is unusable (no grounded facts / unknown tone) so the caller falls
    back to _phrase_result — never to model-authored prose.

    Rotates through the tone's ENRICH_TEMPLATES variants via filler.pick_from so
    consecutive tool results never use the same phrasing."""
    source = json.dumps(result, ensure_ascii=False)
    facts = [f.strip() for f in (verdict.key_facts or []) if f.strip() and f.strip() in source]
    if not facts:
        return None
    variants = getattr(config, "ENRICH_TEMPLATES", {}).get(verdict.tone)
    if not variants:
        return None
    template = filler.pick_from(variants, key=f"_enrich_{verdict.tone}")
    if not template:
        return None
    return template.format(facts=_join_facts(facts))


def _join_facts(facts: list[str]) -> str:
    """Join grounded facts into one natural clause (a, b and c)."""
    facts = [f.rstrip(". ") for f in facts]
    if len(facts) == 1:
        return facts[0]
    return f"{', '.join(facts[:-1])} and {facts[-1]}"


def _finish_enriched(text: str, result: dict) -> str:
    """Append the config next-step hint + closing question deterministically —
    identical tail to _phrase_result, shared so both paths end the same way."""
    hint = getattr(config, "NEXT_STEP_HINTS", {}).get(result.get("tool", ""), "")
    if hint:
        text = f"{text.rstrip()} {hint}"
    if not text.rstrip().endswith("?"):
        text = f"{text.rstrip()} {config._pick_closing()}"
    return text


# ======================================================================== #
# 5b. PROACTIVE SDR DIRECTOR (no model) — the sales-agenda "spine" gate.     #
#     An IN-NODE deterministic gate at the HEAD of validator_node (same      #
#     precedent as the stall detector), NOT a graph node. Walks              #
#     config.CALL_ARC so an OUTBOUND agent LEADS the call between reactive    #
#     turns instead of only answering. No-op when the arc is empty (inbound  #
#     agents) or the lead has the floor. Zero model calls, zero new edges —  #
#     it adds 0 to every row of the tier budget.                            #
# ======================================================================== #
def _arc_stages() -> tuple:
    return tuple(getattr(config, "CALL_ARC", ()) or ())


def _objective_ctx(state) -> str:
    """Inject the current stage's spoken goal into an ANSWER/think prompt so the
    agent's REACTIVE answers sound like a goal-aware SDR, not a help desk. Pure
    shaping — the director enforces the actual move. Empty when there is no arc
    or objective, so an inbound agent's prompts are byte-for-byte unchanged."""
    arc = _arc_stages()
    if not arc:
        return ""
    stages = {s.name: s for s in arc}
    stage = stages.get(state.get("call_stage") or arc[0].name)
    if stage is None or not stage.objective:
        return ""
    return ("\n\nCALL CONTEXT: this is an OUTBOUND call you placed; you are leading it, not "
            f"running a help desk. Your goal right now: {stage.objective}. Answer what the lead just "
            "said in one or two short sentences, warm and purposeful. Do NOT tack on a generic "
            "'anything else?' — the next step is steered for you. Never re-ask something they have "
            "already answered.")


def _lead_has_floor(state) -> bool:
    """True when the LEAD (not the agent) owns this turn's direction — the
    director must stand down so the reactive machinery (firm-no exit, HITL gate,
    an in-progress flow/plan, escalation) is preserved untouched."""
    return bool(
        state.get("intent") in ("goodbye", "human_handoff", "restart")
        or state.get("category") == "SYSTEM"
        or state.get("pending_intent")
        or _plan_active(state)
        or state.get("awaiting_human")
        or state.get("exit_conversation"))


def _flow_complete(intent: str, state) -> bool:
    """A flow has completed when its OWN tool ran cleanly this session
    (last_action — the reliable signal) or its hard identifiers landed in
    session_facts. Prefer the last_action signal so a slot seeded from lead
    metadata can never mark a qualification stage 'done' before its tool runs."""
    flow = config.FLOWS.get(intent)
    if flow is None:
        return False
    la = state.get("last_action") or {}
    if la.get("tool") == flow.tool and not (la.get("result") or {}).get("error"):
        return True
    facts = state.get("session_facts") or {}
    return bool(flow.cache_keys) and all(k in facts for k in flow.cache_keys)


def _stage_satisfied(stage, state) -> bool:
    """Evaluate a Stage.advance_when predicate against STRUCTURED state only
    (never prose). An empty predicate is terminal (never auto-advances)."""
    cond = getattr(stage, "advance_when", {}) or {}
    if "flow_complete" in cond:
        return _flow_complete(str(cond["flow_complete"]), state)
    if "session_fact" in cond:
        return str(cond["session_fact"]) in (state.get("session_facts") or {})
    if "agent_led_once" in cond:
        return bool(cond["agent_led_once"]) and state.get("stage_nudged") == stage.name
    if "intent_seen" in cond:
        return state.get("intent", "") in set(cond["intent_seen"])
    return False


def _append_move(draft: str, move: str) -> str:
    """Continue the reactive draft with the agenda move (ENGAGE-FIRST: answer
    first, then lead) — never replace it."""
    draft = (draft or "").rstrip()
    move = (move or "").strip()
    if not move:
        return draft
    return f"{draft} {move}" if draft else move


def _objection_gate(state) -> dict:
    """ISOLATE (step 2 of A-I-P), zero model. Records the objection in the
    cross-turn ledger and, on the FIRST objection of the call only, emits the
    isolate question under the "isolate" key (the caller pops it; it is not a
    state field).

    Two deliberately separate guards:
      * the LEDGER is written on every objection turn — it is the SDR
        deliverable, and an objection raised mid-flow still counts;
      * the QUESTION additionally requires the lead NOT to hold the floor,
        because mid slot-fill the reply already ends in the flow's own question
        (_resume_suffix) and this engine ships ONE question per turn.
    Returns {} for non-objection turns and for agents with no OBJECTION_INTENTS."""
    if not _is_objection(state):
        return {}
    intent = state.get("intent", "")
    raised = list(state.get("objections_raised") or [])
    first = not raised
    if intent not in raised:
        raised.append(intent)
    updates = {"objections_raised": raised}

    template = getattr(config, "OBJECTION_ISOLATE_TEMPLATE", "") or ""
    topic = (getattr(config, "OBJECTION_TOPICS", {}) or {}).get(intent, "")
    if first and template and topic and not _lead_has_floor(state):
        try:
            updates["isolate"] = template.format(topic=topic)
        except (KeyError, IndexError):
            # A malformed template must never break a live call; the objection
            # still acknowledges and pivots. selftest's objection_preflight
            # fails the build on this so it is caught before shipping.
            logger.warning("OBJECTION_ISOLATE_TEMPLATE is malformed (%r) — isolation skipped",
                           template)
    return updates


def _director(state, objection: bool = False, suppress_move: bool = False) -> dict:
    """Zero-model agenda gate. Advances call_stage when the current stage's
    structured exit is met, then makes ONE proactive move for the (possibly new)
    stage — enter its flow, speak its scripted line, or steer back with its
    nudge — guarded one-shot per stage. Returns a state-update dict (may carry a
    modified draft_response); {} when it stands down.

    A-I-P integration (both flags default False, so non-objection turns behave
    exactly as before):
      objection=True     the lead pushed back. The one-shot guard is BYPASSED so
                         the agent re-anchors on the arc EVERY time — the old
                         behaviour let the second objection in a stage end on the
                         lead's terms, handing back the floor mid-qualification.
      suppress_move=True the isolate question already owns this turn's one
                         question; advance the cursor but speak no agenda move.
    """
    arc = _arc_stages()
    if not arc or _lead_has_floor(state):
        return {}

    order = [s.name for s in arc]
    stages = {s.name: s for s in arc}
    cur = state.get("call_stage") or arc[0].name
    if cur not in stages:
        cur = arc[0].name

    updates: dict = {}
    # 1) Advance the cursor while the stage's structured exit holds (monotonic,
    #    bounded by the arc length).
    idx = order.index(cur)
    while idx < len(order) - 1 and _stage_satisfied(stages[order[idx]], state):
        idx += 1
    new_stage = order[idx]
    if new_stage != cur:
        updates["call_stage"] = new_stage
        updates["stage_nudged"] = ""          # a fresh stage may make its own move
    elif not state.get("call_stage"):
        updates["call_stage"] = new_stage      # lazy-init on turn 1

    stage = stages[new_stage]
    already_led = updates.get("stage_nudged", state.get("stage_nudged", "")) == new_stage
    if suppress_move:
        return updates          # the isolate question owns this turn's one question
    if already_led and not objection:
        return updates                          # one move per stage — no broken record

    draft = state.get("draft_response", "") or ""
    reactive_answer = state.get("category") == "ANSWER"    # knowledge/chitchat replied

    # 2a) Drive this stage's flow: pend it (next turn routes through the already-
    #     budgeted think path) AND ask its first slot now, so the agent leads
    #     THIS turn. Skipped when the flow has already completed.
    #     On a REPEAT objection (already_led) this is the re-pivot: re-anchor on
    #     the same flow WITHOUT clobbering what it already collected, and ask the
    #     next slot still missing — a fresh question, so no broken record.
    if stage.flow and stage.flow in config.FLOWS and not _flow_complete(stage.flow, state):
        flow = config.FLOWS[stage.flow]
        kept = dict(state.get("pending_slots") or {}) if already_led else {}
        missing = [s for s in flow.slots if s in flow.slot_prompts and not kept.get(s)]
        updates["pending_intent"] = stage.flow
        updates["pending_slots"] = kept
        updates["stage_nudged"] = new_stage
        if missing:
            updates["draft_response"] = _append_move(draft, _ask_for(flow, missing))
        return updates

    # 2b) A reactive turn (the lead asked / objected): steer back with the nudge.
    #     A repeat objection on a stage that already spoke its nudge prefers the
    #     scripted line below (different words) over repeating itself.
    if reactive_answer and stage.nudge and not (already_led and stage.line):
        updates["draft_response"] = _append_move(draft, stage.nudge)
        updates["stage_nudged"] = new_stage
        return updates

    # 2c) Idle floor with a scripted line (e.g. the close CTA): speak it once.
    if stage.line:
        updates["draft_response"] = _append_move(draft, stage.line)
        updates["stage_nudged"] = new_stage
        return updates

    return updates


# ======================================================================== #
# 5c. LEAD RECORD (no model) — config.SUMMARY_TEMPLATE. Conversation memory  #
#     AND the SDR deliverable. Structured fields are aggregated every turn    #
#     from state the INTENT/THINK calls already produced (zero extra calls);  #
#     the 'freetext' fields are synthesized ONCE at call-end by               #
#     build_call_record, OFF the reply path. No-op when the template is empty.#
# ======================================================================== #
def _summary_source_value(field, state):
    """Resolve ONE structured SummaryField source against current state. Returns
    None for 'freetext' (filled off-path at call-end) and for any source with no
    value yet, so the aggregator only ever SETS fields, never clears them."""
    src = field.source or ""
    if src == "freetext":
        return None
    if src == "followups":
        summ = ((state.get("last_action") or {}).get("summary") or "").strip()
        return summ or None
    if src == "objections":
        # The ledger is already the distinct, ordered list the record wants —
        # written zero-model by _objection_gate from structured intents.
        return list(state.get("objections_raised") or []) or None
    if src.startswith("fact:"):
        return (state.get("session_facts") or {}).get(src.split(":", 1)[1]) or None
    if src.startswith("slot:"):
        spec = src.split(":", 1)[1]
        name = spec.split(".", 1)[1] if "." in spec else spec
        merged = {**(state.get("pending_slots") or {}), **(state.get("slots") or {})}
        val = merged.get(name)
        return val if val and val != config.SLOT_REFUSED else None
    return None


def _update_summary(state) -> dict:
    """Zero-model lead-record aggregator (head of validator_node, every turn).
    Maps existing STRUCTURED state — session_facts, captured slots, last_action —
    into config.SUMMARY_TEMPLATE keys. The slots it reads are already the output
    of the INTENT/THINK calls that ran this turn, so the record costs zero extra
    tokens and zero extra calls. Monotonic (fields are set, never cleared);
    'freetext' fields are left for build_call_record. {} (no write) when the
    template is empty or nothing changed."""
    template = tuple(getattr(config, "SUMMARY_TEMPLATE", ()) or ())
    if not template:
        return {}
    record = dict(state.get("call_summary") or {})
    changed = False
    for f in template:
        val = _summary_source_value(f, state)
        if val is None:
            continue
        if f.source == "followups":
            existing = list(record.get(f.key) or [])
            if val not in existing:
                existing.append(val)
                record[f.key] = existing
                changed = True
        elif record.get(f.key) != val:
            record[f.key] = val
            changed = True
    return {"call_summary": record} if changed else {}


def _summary_ctx(state) -> str:
    """Inject a COMPACT view of the lead record into a prompt so the short
    HISTORY_TURNS window never loses what was already qualified. Omits 'fact:'
    fields (already carried by _session_facts_ctx) and unfilled 'freetext' so we
    don't re-bloat the payload we trimmed. Empty when nothing captured yet."""
    template = tuple(getattr(config, "SUMMARY_TEMPLATE", ()) or ())
    if not template:
        return ""
    record = state.get("call_summary") or {}
    shown = {}
    for f in template:
        if f.source.startswith("fact:") or f.source == "freetext":
            continue
        val = record.get(f.key)
        if val:
            shown[f.label or f.key] = val
    if not shown:
        return ""
    return ("\n\nLEAD RECORD (captured this call — reuse, do NOT re-ask): "
            f"{json.dumps(shown, ensure_ascii=False)}")


def _recency_anchor(state) -> str:
    """A compact directive placed at the RECENCY edge (after history, by the
    latest user turn) so the immediate goal + firm-no rule stay salient as the
    window fills. Zero model, ~1 line. Empty when there is no arc/objective, so
    inbound agents' payloads are byte-for-byte unchanged."""
    arc = _arc_stages()
    if not arc:
        return ""
    stages = {s.name: s for s in arc}
    stage = stages.get(state.get("call_stage") or arc[0].name)
    obj = (stage.objective if stage else "") or ""
    if not obj:
        return ""
    return (f"Reminder — your immediate goal: {obj}. If the lead has firmly declined, "
            "thank them in one sentence and end; otherwise take one step toward it.")


def _full_transcript(state) -> str:
    """The WHOLE conversation (untrimmed) for the call-end record synthesis —
    unlike _history, this reads every persisted turn, since the record must
    summarize the full call, not the short prompt window."""
    role_map = {"human": "Lead", "ai": "Agent"}
    return "\n".join(f"{role_map.get(getattr(m, 'type', ''), 'Lead')}: {str(m.content)}"
                     for m in (state.get("recent_messages") or []))


async def build_call_record(state) -> dict:
    """Call-end enrichment (OFF the reply path — the platform calls this AFTER
    the goodbye has streamed, never on a live turn). Fills the 'freetext'
    SummaryField keys with ONE ANSWER-tier synthesis over the full transcript,
    on top of the already-aggregated structured fields. Returns the full
    call_summary dict. Mock mode / any failure -> structured record with empty
    freetext keys (never invents). Not a graph node; not in closing_node."""
    template = tuple(getattr(config, "SUMMARY_TEMPLATE", ()) or ())
    record = dict(state.get("call_summary") or {})
    freetext = [f for f in template if f.source == "freetext"]
    if not freetext:
        return record
    if llm_client.mock:
        for f in freetext:
            record.setdefault(f.key, "")
        return record
    keys = [f.key for f in freetext]
    labels = "; ".join(f"{f.key} = {f.label or f.key}" for f in freetext)
    system = (
        "You are a sales-call analyst. Read the transcript and return ONLY a JSON object "
        f"with EXACTLY these keys: {keys}. Each value is a short plain-text summary "
        f"({labels}). Base every value strictly on the transcript; use an empty string when "
        "the transcript does not support it. No markdown, no extra keys.")
    try:
        raw = await llm_client.generate_text(
            ANSWER_MODEL,
            [{"role": "system", "content": system},
             {"role": "user", "content": _full_transcript(state)}],
            temperature=0.2, max_tokens=300)
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        data = json.loads(match.group(0)) if match else {}
        if not isinstance(data, dict):
            data = {}
    except Exception as e:
        logger.warning("call-record enrichment failed (%s); leaving freetext empty",
                       type(e).__name__)
        data = {}
    for f in freetext:
        v = data.get(f.key)
        record[f.key] = v.strip() if isinstance(v, str) else ""
    return record


# ======================================================================== #
# 6. RESPONSE VALIDATOR (exit filter, Layer 3) — the only door to the user  #
# ======================================================================== #
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
_MD_RE = re.compile(r"[*_`#>~]")


def _tiedown(text: str, state, director_moved: bool) -> str | None:
    """MICRO-COMMITMENT gate (zero model, zero prompt tokens). Returns the
    tie-down to append, or None.

    Fires ONLY on a statement-ending agent turn. That single condition is what
    makes the gate safe: a tie-down is a question, this engine ships ONE question
    per turn, so refusing to append after an existing "?" is what keeps it from
    ever colliding with a slot ask, a confirm gate, the isolate question, a stage
    nudge, or the close CTA. The other guards: never stack onto a director move,
    never speak over a lead who holds the floor (a firm no, a handoff, an open
    HITL gate), and never push the reply past config.MAX_REPLY_WORDS."""
    every = int(getattr(config, "TIEDOWN_EVERY_N_TURNS", 0) or 0)
    variants = list(getattr(config, "TIEDOWNS", None) or [])
    if every <= 0 or not variants or not text:
        return None
    if text.rstrip().endswith("?") or director_moved or _lead_has_floor(state):
        return None
    if state.get("turns_since_tiedown", 0) < every:
        return None
    candidate = filler.pick_from(variants, key="_tiedown")
    if not candidate:
        return None
    cap = int(getattr(config, "MAX_REPLY_WORDS", 0) or 0)
    if cap and _word_count(text) + _word_count(candidate) > cap:
        logger.info("tie-down suppressed: %d + %d words exceeds the %d-word reply budget",
                    _word_count(text), _word_count(candidate), cap)
        return None
    return candidate


def validator_node(state: AgentState) -> dict:
    """The only door to the user: every reply leaves the graph through here.

    Five deterministic gates run in a load-bearing order, all zero-model:

      1. objection gate  -- records push-back and, on the call's first one,
                            claims this turn's question slot with the ISOLATE.
                            FIRST because its outcome decides whether the
                            director may speak an agenda move at all.
      2. director        -- advances the CALL_ARC cursor and appends the next
                            proactive move while the agent still has the floor.
      3. summary         -- folds this turn's structured state into the lead
                            record (config.SUMMARY_TEMPLATE).
      4. stall detector  -- escalates to STALL_TEXT when a reply repeats
                            STALL_THRESHOLD turns in a row.
      5. tie-down        -- appends a rotating tie-down, dropped if it would
                            push the reply past config.MAX_REPLY_WORDS.

    Every gate is a no-op on an inbound agent (empty CALL_ARC / OBJECTION_INTENTS
    / TIEDOWNS), so this node adds nothing to their latency or token budget.

    Returns the partial state update -- never mutates ``state`` in place.
    """
    # Objection gate (config.OBJECTION_INTENTS): record the push-back and, on the
    # first one of the call, take this turn's question slot with the ISOLATE
    # question. Runs BEFORE the director because its outcome decides whether the
    # director may speak an agenda move at all. Zero model; {} for inbound agents.
    objection = _objection_gate(state)
    isolate = objection.pop("isolate", "")

    # Proactive SDR director (config.CALL_ARC): advance the sales agenda and,
    # if it's the agent's turn to lead, append the next proactive move BEFORE
    # the exit filter scrubs the draft. Zero model; a no-op for inbound agents.
    # Its call_stage / stage_nudged / pending_* updates ride out in this node's
    # return so the cursor persists across turns.
    director = _director(state, objection=bool(objection), suppress_move=bool(isolate))
    if director.get("draft_response") is not None:
        state = {**state, "draft_response": director["draft_response"]}

    # PIVOT is the director's move above; ISOLATE lands here instead when it
    # owns the turn (the two are mutually exclusive by construction).
    if isolate:
        state = {**state, "draft_response": _append_move(state.get("draft_response", ""), isolate)}

    text = state.get("draft_response", "") or ""
    text = _ANSI_RE.sub("", text)
    text = _MD_RE.sub("", text)
    for pattern, replacement in config.BLOCKED_PATTERNS:
        text = pattern.sub(replacement, text)
    text = re.sub(r"\s+", " ", text).strip()

    # Stall detector (invariant 25) — an IN-NODE deterministic gate, like the
    # fast router, never a graph node. Repetition is the earliest, cheapest
    # signal of a broken-record loop: if this exact reply would go out for the
    # STALL_THRESHOLD-th consecutive turn, swap in the clarify-then-escalate
    # STALL_TEXT instead (its escape phrase routes to human_handoff). The
    # comparison is on the post-scrub text, so cosmetic differences don't
    # mask a stall. The stall reply then becomes the new fingerprint — if THE
    # LOOP persists, the gate fires again after another THRESHOLD repeats.
    # Carry the director's persistent state changes (call_stage, stage_nudged,
    # pending_*) out with the response; draft_response is per-turn (already
    # folded into `text`) so it is deliberately dropped here.
    updates = {k: v for k, v in director.items() if k != "draft_response"}
    # The objection ledger rides out with the director's persistent updates.
    updates.update(objection)
    # Lead record (config.SUMMARY_TEMPLATE): aggregate this turn's structured
    # state into the cross-turn record. Zero model — the slots/facts it reads
    # were already produced by this turn's INTENT/THINK calls. No-op for agents
    # without a template. Rides out with the director's persistent updates.
    updates.update(_update_summary(state))
    updates["final_response"] = text
    if text and config.STALL_THRESHOLD > 0:
        fingerprint = text.casefold()
        if fingerprint == state.get("last_reply_fingerprint", ""):
            count = state.get("stall_count", 0) + 1
        else:
            count = 1
        if count >= config.STALL_THRESHOLD:
            logger.warning("stall detector: reply repeated %d consecutive turns — escalating", count)
            text = config.STALL_TEXT
            fingerprint, count = text.casefold(), 1
            updates["final_response"] = text
        updates["last_reply_fingerprint"] = fingerprint
        updates["stall_count"] = count

    # Micro-commitment (tie-down) gate — DELIBERATELY the last mutation, AFTER
    # the stall fingerprint above. The tie-down bank rotates, so appending it
    # before the fingerprint would give a byte-identical repeated reply a
    # different fingerprint every turn and silently disable the stall detector
    # (invariant 25) — the escalation path of last resort. Fingerprint the reply
    # BODY; append the tie-down to the outgoing text only.
    if int(getattr(config, "TIEDOWN_EVERY_N_TURNS", 0) or 0) > 0:
        tie = _tiedown(text, state, director_moved=bool(director.get("draft_response")))
        if tie:
            updates["final_response"] = f"{text.rstrip()} {tie}".strip()
            updates["turns_since_tiedown"] = 0
        elif (_AFFIRM_RE.search(state.get("user_message", "") or "")
                and not (state.get("pending_confirmation") or {})):
            # The lead just agreed on their own — a micro-commitment landed, so
            # restart the cadence instead of nagging someone already saying yes.
            updates["turns_since_tiedown"] = 0
        else:
            updates["turns_since_tiedown"] = state.get("turns_since_tiedown", 0) + 1

    final = updates.get("final_response", "")
    if final:
        updates["recent_messages"] = [AIMessage(content=final)]
    return updates


# --- helpers ---
def _clear_pending(updates: dict) -> dict:
    updates.update({"pending_intent": None, "pending_slots": {}, "pending_confirmation": {}})
    return updates


def _plan_active(state) -> bool:
    """A plan is active while its walk index still points inside plan_steps.
    Deliberately SEPARATE from pending_* (think clears those on every ready
    payload; that must never kill the plan)."""
    plan = state.get("plan_steps") or []
    return bool(plan) and state.get("current_step_index", 0) < len(plan)


def _clear_plan(updates: dict) -> dict:
    """End a plan (completion or abort). Called on: finish, step failure,
    confirm decline, HITL denial, restart, and goodbye."""
    updates.update({"plan_steps": [], "current_step_index": 0})
    return updates
