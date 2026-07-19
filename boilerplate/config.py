"""Domain configuration — THE customization surface of this boilerplate.

The architect skill's Step 4 edits (mostly) THIS file, prompts.py's FACTS-free
sections, and tools.py. The graph, nodes, schemas, and shell are generic and
should rarely need changes.

Ships with a small demo domain ("Acme Outdoors" gear store) so the agent runs
out of the box in mock mode. Every [CUSTOMIZE] block is a swap point.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

try:  # load .env before reading safety-constant overrides (idempotent)
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:
    pass

# ── Identity ────────────────────────────────────────────── [CUSTOMIZE] ──
AGENT_NAME = "Acme Outdoors Support"
# OPENER is spoken as the call's FIRST words by the voice platform (Vapi
# firstMessage), ~500ms after pickup, with zero model calls. Contract: a PLAIN
# string literal on this line (the platform extracts it statically — no
# f-string, no concatenation), <=20 words, human phone-pickup tone, ends with
# ONE question, never empty or whitespace-only.
OPENER = "Hi, this is Acme Outdoors! I can help with hours, returns, or booking a gear fitting — what do you need?"
EXIT_WORDS = ("exit", "quit")

# ── Ground-truth facts (knowledge intents answer ONLY from these) ─ [CUSTOMIZE] ──
FACTS = """Acme Outdoors — authoritative facts (never invent beyond this):
- Branches: Downtown (12 River St), Mall (Westfield, level 2), Airport (Terminal B, landside).
- Hours (all branches): Mon-Sat 9:00-21:00, Sun 10:00-18:00.
- Returns: 30 days with receipt, unused items; refunds to original payment method within 5 business days.
- Payments cannot be taken on this channel; a human agent verifies payment details.
"""

# ── Intents (hierarchical: ANSWER / FLOW / SYSTEM) ──────── [CUSTOMIZE] ──
# Knowledge intents: answered directly from FACTS by the ANSWER tier (no tool).
KNOWLEDGE_INTENTS: Tuple[str, ...] = ("faq_hours", "faq_returns", "faq_policy")

# Knowledge intents in this tuple are answered via the Agentic-RAG subgraph
# (retrieve -> grade -> rewrite loop over DOCS) instead of the static FACTS
# block. Use for catalogs/policies too large or too dynamic for the prompt.
RETRIEVAL_INTENTS: Tuple[str, ...] = ("faq_policy",)

# SYSTEM intents: session-control requests handled DETERMINISTICALLY (no
# model): help/capabilities, restart, and the human_handoff escalation path
# (invariant 26 — the advertised handoff must be a reachable node, not
# conversational copy). goodbye is SYSTEM too (routed to closing).
SYSTEM_INTENTS: Tuple[str, ...] = ("help", "restart", "human_handoff")

# One-line descriptions fed to the intent-detection prompt. Must cover every
# knowledge intent, every flow, and every SYSTEM intent
# (chitchat/goodbye are added automatically).
INTENT_DESCRIPTIONS: Dict[str, str] = {
    "faq_hours": "opening hours / when are you open",
    "faq_returns": "return or exchange policy questions",
    "faq_policy": "shipping, warranty, price-match, or other store policy questions",
    "order_status": "where is my order / tracking / order status",
    "book_fitting": "booking a gear-fitting appointment at a branch",
    "request_refund": "the user wants a refund issued for an order",
    "help": "what can you do / list your capabilities",
    "restart": "start over / reset the conversation / forget that",
    "human_handoff": ("the user asks for a human, manager, supervisor, or live agent, "
                      "or is clearly frustrated and wants a person instead of the bot"),
}


# ── Tool-backed flows (Think→Act) ───────────────────────── [CUSTOMIZE] ──
@dataclass(frozen=True)
class Flow:
    """A tool-backed intent: which tool runs, which slots it needs, and how to
    ask for each missing slot. `slot_prompts` doubles as the slot description
    in the live intent-extraction prompt AND the mock clarifying question.

    confirm: destructive/irreversible flows (checkout, cancel, book) ask a
      deterministic yes/no before Act; the payload is stashed until answered.
    confirm_template: the yes/no question, .format(**args); empty -> generic.
    validators: per-slot hooks run by Think AFTER entity resolution, before
      Act. Each takes (value, all_slots) and returns
      (ok, normalized_value_or_clarify_question). Resolvers and validators
      MUST be idempotent on canonical values (resolving/validating an
      already-canonical value passes and returns it unchanged) — the fast
      router pre-tests values with these hooks and hands them to Think RAW,
      so every value legitimately passes them twice.
      This is where units, bounds,
      and format rules live — a mismatched value never silently reaches a tool
      (e.g. '1000 kg' when stock is 40 packs). Bounds MUST be derived from the
      catalog entry of the already-RESOLVED entity; if that lookup fails,
      validate format only (bounds re-check on the next Think pass) — NEVER
      substitute a hardcoded default limit (a fallback stock of "200" is what
      turned a wrong product key into a confidently wrong stock answer).
    enrich: route the tool result through the ENRICH (SLM) tier. Set False for
      tools whose "summary" is already perfectly formatted — the graph bypasses
      the SLM hop entirely (deterministic phrasing, one less network call).
    hitl: HIGH-STAKES flows (refunds, deletion): instead of executing, the
      graph interrupt()-suspends with the ready payload and waits for an
      OPERATOR approval (Command(resume=...)). Distinct from `confirm`, which
      is an in-band end-user yes/no.
    cache_keys: whitelist of tool-result fields copied into session_facts
      after a SUCCESSFUL Act (hard transactional identifiers only — order ids,
      confirmation numbers — never soft data). The merge is a code-level dict
      update in tool_exec; no model is involved. These names double as the
      variable-mapping bus for plan steps: a later step's missing slot with
      the same name auto-fills from session_facts."""
    tool: str
    slots: Tuple[str, ...]
    slot_prompts: Dict[str, str] = field(default_factory=dict)
    confirm: bool = False
    confirm_template: str = ""
    validators: Dict[str, Callable[[str, dict], Tuple[bool, str]]] = field(default_factory=dict)
    enrich: bool = True
    hitl: bool = False
    cache_keys: Tuple[str, ...] = ()


# Slot-refusal sentinel (ENGINE constant — do not customize). When the lead
# declines to give an asked slot value ("I'd rather not say"), the engine
# stores this sentinel in the slot so the derived missing-slot computation
# stops re-asking it — a refused question asked twice loses the lead. The
# sentinel is truthy by design. Tools receive it verbatim and should branch
# on it ("caller declined to share"); validators/resolvers skip it.
SLOT_REFUSED = "<declined>"


def _validate_order_id(value: str, _slots: dict) -> Tuple[bool, str]:
    """Normalize bare digits ('12345' -> 'AC-12345'); reject other shapes with
    a clarifying question instead of sending garbage to the tool."""
    v = value.strip().upper().replace(" ", "")
    if v.isdigit():
        return True, f"AC-{v}"
    if v.startswith("AC-") and v[3:].isdigit():
        return True, v
    if v.startswith("AC") and v[2:].isdigit():
        return True, f"AC-{v[2:]}"
    return False, "Order numbers look like AC-12345 — could you double-check yours?"


FLOWS: Dict[str, Flow] = {
    "order_status": Flow(
        tool="lookup_order",
        slots=("order_id",),
        slot_prompts={"order_id": "your order number (it looks like AC-12345)"},
        validators={"order_id": _validate_order_id},
        cache_keys=("order_id",),
    ),
    "book_fitting": Flow(
        tool="book_appointment",
        slots=("branch", "slot_iso"),
        slot_prompts={
            "branch": "which branch works for you — Downtown, Mall, or Airport",
            "slot_iso": "what day and time you'd like to come in",
        },
        # Booking creates a real-world commitment -> confirm before acting.
        confirm=True,
        confirm_template="Just to confirm — book your fitting at the {branch} branch for {slot_iso}? (yes/no)",
        cache_keys=("confirmation",),
    ),
    "request_refund": Flow(
        tool="issue_refund",
        slots=("order_id",),
        slot_prompts={"order_id": "the order number to refund (it looks like AC-12345)"},
        validators={"order_id": _validate_order_id},
        # Money moves -> an OPERATOR must approve the payload (graph suspends).
        hitl=True,
        # The refund tool's summary is already fully formatted -> skip the SLM.
        enrich=False,
        cache_keys=("reference",),
    ),
}

# The ONLY follow-up the agent may offer after each tool, appended
# deterministically by the enrichment node. The ENRICH model itself is
# forbidden from inventing next steps (that's how agents start asking about
# payment flows that don't exist).                              [CUSTOMIZE]
NEXT_STEP_HINTS: Dict[str, str] = {
    "lookup_order": "",
    "book_appointment": "You can reschedule any time by booking again.",
    "issue_refund": "The refund lands within 5 business days.",
}

# ── ENRICH templates (SLM verdict -> deterministic prose) ── [CUSTOMIZE] ──
# The ENRICH (SLM) tier NEVER writes the user-facing sentence. It returns an
# EnrichVerdict (tone + grounded facts). The node assembles the reply from the
# tone-keyed template below: "{facts}" is filled with the SLM's grounded,
# source-verified key_facts joined naturally; NEXT_STEP_HINTS + the closing
# question are still appended deterministically after. Keep templates in this
# agent's tone. If a tone is missing or the verdict fails grounding, the node
# falls back to _phrase_result (the summary verbatim) — never to free prose.
#
# VARIANT BANKS: each tone maps to a LIST of templates; the node rotates
# through them so consecutive tool results never sound identical. Same
# pattern as FILLERS_BY_TOOL — design-time variety, zero runtime cost.
ENRICH_TEMPLATES: Dict[str, List[str]] = {
    "confirm": [
        "Done — {facts}.",
        "All set — {facts}.",
        "Got it taken care of — {facts}.",
        "That's sorted — {facts}.",
    ],
    "regret": [
        "Sorry — {facts}.",
        "Unfortunately, {facts}.",
        "Ah, no luck — {facts}.",
        "Hmm — {facts}.",
    ],
    "neutral": [
        "{facts}.",
        "Here's what I've got — {facts}.",
        "So, {facts}.",
        "Looks like {facts}.",
    ],
}

# ── Filler channel (references/Filler_Channel.txt) ──────── [CUSTOMIZE] ──
# Short, canned acknowledgments emitted WHILE a tool runs, over a frontend-
# agnostic side channel (the Shell prints them; a future voice/SSE adapter
# streams them). DISPLAY-ONLY: never appended to model context, so zero token
# cost. Design-time bank: write 3-5 variants PER TOOL here, once — runtime is
# pure dict-lookup + rotate (no model, no latency). Every phrase must read as
# NATURAL SPOKEN CONVERSATION in this agent's tone (they are heard aloud in
# voice): no step numbers, no status-report phrasing.
FILLER_ENABLED = os.getenv("FILLER_ENABLED", "1").strip().lower() not in (
    "0", "false", "off", "no", "disabled")

# Emit a filler only if the tool outlasts this many ms — fast tools stay silent,
# so text mode isn't chatty. A voice/SSE frontend can set 0 (always cover the
# gap). MOCK tools are instant, so selftest forces 0 to exercise the path.
FILLER_DELAY_MS = int(os.getenv("FILLER_DELAY_MS", "250"))

# Per-tool banks (keyed by Flow.tool). The architect generates these from the
# tool catalog on opt-in; every FLOW tool SHOULD have an entry (selftest gates
# it) — the whole ROI is tool-SPECIFIC acks, not the generic fallback.
FILLERS_BY_TOOL: Dict[str, List[str]] = {
    "lookup_order": [
        "Let me pull up that order…",
        "One sec — checking on that order…",
        "Looking that up for you now…",
    ],
    "book_appointment": [
        "Let me check the calendar…",
        "Checking what's available…",
        "One moment while I look at the openings…",
    ],
    "issue_refund": [
        "Let me get that refund started…",
        "Okay — putting that through for you…",
        "One moment while I set that up…",
    ],
}

# Generic fallback for any tool without its own bank (keep it truly neutral).
FILLER_DEFAULT: List[str] = ["One moment…", "Just a sec…", "Bear with me a moment…"]

# Natural continuation phrases for the gap BETWEEN plan steps of a compound
# request (never "step 2 of 3" — that exposes internal mechanics and sounds
# robotic aloud). Empty list disables plan fillers.
FILLER_PLAN_CONTINUE: List[str] = ["Still working on it…", "Almost there…", "Just a moment more…"]

# Pre-think acknowledgment bank (voice): ultra-short spoken tokens the HOST
# RUNTIME speaks the instant a turn arrives — BEFORE the graph runs — covering
# the INTENT->ANSWER time-to-first-token that tool fillers can't reach (a
# pure-reasoning turn calls no tool and would be dead air on a phone).
# Design-time, written in this agent's voice. Every token must be sub-second
# to speak and safe ahead of ANY reply type — never "Sure!" or "Great
# question!" (the reply might be a refusal or a clarifying question).
# The runtime falls back to its own generic bank if this is absent or empty.
FILLER_THINKING: List[str] = [
    "Hmm… ",
    "Okay… ",
    "Let's see… ",
    "Right. ",
    "One sec… ",
]

# ── Closing-question bank (replaces the hardcoded "Anything else?") ─ [CUSTOMIZE] ──
# Rotated deterministically so consecutive turns never end with the same
# closing. Same rotation pattern as the filler banks. Every phrase must be
# safe as a SPOKEN line after any reply type — keep them short, warm, and
# genuinely varied (not paraphrases of one sentence).                [CUSTOMIZE]
CLOSING_QUESTIONS: List[str] = [
    "Anything else I can help with?",
    "What else can I do for you?",
    "Need anything else?",
    "Anything else on your mind?",
    "Is there something else I can help with?",
    "Was there anything else?",
]

# Module-level rotation counter for closing questions (same pattern as filler).
_closing_q_index = 0


def _pick_closing() -> str:
    """Rotate through CLOSING_QUESTIONS so consecutive turns never repeat."""
    global _closing_q_index
    q = CLOSING_QUESTIONS[_closing_q_index % len(CLOSING_QUESTIONS)]
    _closing_q_index += 1
    return q


# Deterministic acknowledgment when the user declines a confirmation gate.
CONFIRM_DECLINED_VARIANTS: List[str] = [
    "Okay — I won't go ahead with that; nothing has been changed.",
    "No problem — I've left everything as it was.",
    "Got it — nothing was changed on my end.",
]
CONFIRM_DECLINED_TEXT = CONFIRM_DECLINED_VARIANTS[0]  # selftest compat

# One-shot resume offer appended after an interrupting flow completes while an
# earlier flow sits in the paused_flow archive. Placeholders: {flow} is the
# paused intent name (underscores -> spaces), {slot_hint} its first missing
# slot's prompt. Empty string disables the offer (archive + restore still work).
PAUSED_RESUME_TEXT = ("By the way, we didn't finish your {flow} — "
                      "could you tell me {slot_hint}?")

# Deterministic reply when the OPERATOR denies a HITL payload.
HITL_DENIED_TEXT = ("I'm sorry — that request couldn't be approved on this channel. "
                    "A human agent will follow up with you.")

# Deterministic escalation reply (invariant 26): the human_handoff SYSTEM
# intent. The reply is copy; the STRUCTURAL part is the handoff_requested
# state flag the Shell/host observes to actually page a person.  [CUSTOMIZE]
HANDOFF_TEXT = ("Of course — I'm handing this conversation to a human agent right now; "
                "they'll see the full context, so you won't have to repeat yourself. "
                "If there's anything you'd like me to note for them, tell me and I'll pass it along.")

# Stall detector (invariant 25): if the agent is about to emit the SAME final
# reply for the STALL_THRESHOLD-th consecutive turn, the validator swaps in
# STALL_TEXT instead — repetition is the earliest, cheapest failure signal,
# and an unmonitored broken-record loop is a judged failure mode
# (report-11072026 defect #5). 0 disables the gate. The escape hatch phrase
# must match a human_handoff keyword so saying it actually escalates.
STALL_THRESHOLD = int(os.getenv("STALL_THRESHOLD", "3"))
STALL_TEXT = ("I'm sorry — we seem to be going in circles, and I clearly haven't "
              "resolved what you need. Could you rephrase it in one short sentence? "
              "Or just say 'talk to a human' and I'll hand this conversation to a person.")

# Deterministic reply from the failure node (execution validator caught a tool
# error or the circuit breaker tripped). Keeps the session alive and retryable.
FAILURE_TEXT = ("I hit a snag completing that on our side — nothing was changed. "
                "You can ask me to try again, or I can help with something else.")

# Deterministic reply when the planner produced zero valid steps (every action
# was outside the flow catalog): say what CAN be chained instead of guessing.
PLAN_UNSUPPORTED_TEXT = ("I can only chain the actions I actually support — tracking an "
                         "order, booking a fitting, or requesting a refund. Which of "
                         "those would you like to start with?")

VALID_INTENTS: Tuple[str, ...] = (KNOWLEDGE_INTENTS + tuple(FLOWS) + SYSTEM_INTENTS
                                  + ("chitchat", "goodbye", "compound_request"))

# Hierarchical routing map (derived — single source of truth is the tuples
# above). The intent prompt presents the catalog grouped by these macro
# categories; routing derives the category FROM the final intent, so a model
# category/intent mismatch can never corrupt the graph.
# COMPOUND is the Plan-and-Execute trigger: a single utterance requesting TWO
# OR MORE tool actions routes to the planner (ANSWER tier, exactly once),
# then a deterministic bounded step walk (see graph.py).
INTENT_CATEGORIES: Dict[str, Tuple[str, ...]] = {
    "ANSWER": KNOWLEDGE_INTENTS + ("chitchat",),
    "FLOW": tuple(FLOWS),
    "COMPOUND": ("compound_request",),
    "SYSTEM": SYSTEM_INTENTS + ("goodbye",),
}
CATEGORY_OF: Dict[str, str] = {i: cat for cat, intents in INTENT_CATEGORIES.items() for i in intents}

# ── Safety rails (env-overridable, see .env.example) ────── [CUSTOMIZE] ──
# Circuit breaker: max deterministic tool executions per user turn. One
# Think->Act hop needs exactly 1; anything past the cap is a runaway.
MAX_TOOL_CALLS_PER_TURN = int(os.getenv("MAX_TOOL_CALLS_PER_TURN", "3"))

# Fast-router gate (tier-0, deterministic, NO model): mid slot-fill, if the
# user's message deterministically fills a missing slot of the pending flow
# (extractor hit + resolver/validator pass, no other-intent keyword, no
# negation), intent_detect skips the INTENT-tier LLM call and routes straight
# to Think. Falls through to the normal LLM path on ANY doubt — this gate
# never replaces the model tiering, it only fronts it. Flows whose slots have
# no SLOT_EXTRACTORS entry can never fast-route (the implicit per-flow opt-out).
FAST_ROUTER_ENABLED = os.getenv("FAST_ROUTER_ENABLED", "1").strip().lower() not in (
    "0", "false", "off", "no", "disabled")

# Agentic-RAG ceilings — BOTH bound the retrieve->grade->rewrite loop, either
# one sufficient to exit (Agentic_RAG_Explained.txt rule 6):
#   RAG_MAX_ITERATIONS  — max query rewrites. Default 1: every extra loop is
#                         two more LLM calls and visible dead air on the voice channel.
#   RAG_TIMEOUT_SECONDS — wall clock for the WHOLE subgraph; on timeout the
#                         agentic_retrieval node degrades to one deterministic
#                         retrieve pass (nodes.py), never a retry.
RAG_MAX_ITERATIONS = int(os.getenv("RAG_MAX_ITERATIONS", "1"))
# Mode-aware default: the live miss->rewrite->grade loop is 2 sequential
# INTENT-tier API calls (~1.5-4s observed); a mock-calibrated 2s budget aborts
# live exploration ~half the time and the degrade path re-runs the raw query,
# which re-misses — the user sees "I don't have that" for an answerable
# question. Mirrors llm_client's liveness test; an env override is absolute.
_LIVE_LLM = bool(os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_BASE_URL"))
RAG_TIMEOUT_SECONDS = float(os.getenv("RAG_TIMEOUT_SECONDS",
                                      "8.0" if _LIVE_LLM else "2.0"))

# Dynamic-RAG knobs (report-12072026; Agentic_RAG_Explained.txt rules 8-10):
#   RETRIEVAL_MIN_SCORE — confidence floor applied to RETRIEVER results inside
#       the subgraph's retrieve node: docs below it are dropped BEFORE grading,
#       so a low-confidence match degrades to the honest "won't guess" fallback
#       instead of a confident hallucination (R-05). The mock keyword retriever
#       scores by term-overlap count (leave 0 = off); a live cosine-similarity
#       retriever typically wants ~0.70.
#   RAG_CACHE_TTL_SECONDS — in-process TTL cache for retrieval CONTEXT (never
#       the phrased answer): an identical repeat question within the TTL skips
#       the whole retrieve->grade loop (and its live grade call). Keyed on the
#       exact normalized query — never semantic matching — and SKIPPED for
#       context-thin/pronoun queries, whose meaning depends on conversation
#       state. 0 disables.
RETRIEVAL_MIN_SCORE = float(os.getenv("RETRIEVAL_MIN_SCORE", "0"))
RAG_CACHE_TTL_SECONDS = float(os.getenv("RAG_CACHE_TTL_SECONDS", "300"))

# Tool-result compaction (compaction.py): any list field in a HEALTHY tool
# result longer than COMPACTION_MAX_ITEMS is crushed to a salient subset
# (errors/rare statuses/first/last are always kept) plus a sentinel carrying a
# retrieval ref; the original stays retrievable via the retrieve_full_result
# tool for the life of the process. Error results are never compacted. The
# threshold is per LIST FIELD, not per result — mock tools never trip it.
# See references/Context_Compression.txt.
COMPACTION_ENABLED = os.getenv("COMPACTION_ENABLED", "1").strip().lower() not in (
    "0", "false", "off", "no", "disabled")
COMPACTION_MAX_ITEMS = int(os.getenv("COMPACTION_MAX_ITEMS", "12"))

# Plan ceiling: max steps the planner may emit for a COMPOUND request; excess
# steps are truncated deterministically at plan creation. Keep it <=
# MAX_TOOL_CALLS_PER_TURN, or a same-turn plan trips the circuit breaker
# mid-plan (each step is one tool execution). Raising it past ~4 also needs a
# higher LangGraph recursion_limit (~5 super-steps per plan step; see graph.py).
MAX_PLAN_STEPS = int(os.getenv("MAX_PLAN_STEPS", "3"))

# ── Semantic memory (Agentic-RAG corpus + retriever) ────── [CUSTOMIZE] ──
# Demo corpus for RETRIEVAL_INTENTS. A real deployment swaps RETRIEVER for a
# LOCAL vector index (FAISS / SQLite-vss — in-process, no server, no
# credentials; see Agentic_RAG_Explained.txt rule 7) — same signature, and
# nothing else in the graph changes. Hosted vector DBs only when the corpus
# or team genuinely demands it.
#
# "aliases": CONSUMER-side vocabulary the doc text itself doesn't contain —
# acronyms, colloquialisms, the words real users actually type ("broken" for
# a warranty doc). This is offline ingestion enrichment (Anthropic's
# contextual-embedding principle scaled to a config corpus): written ONCE at
# design time, scored by RETRIEVER at zero runtime cost, and it closes
# lexical gaps in mock mode too. The docs are authored in the VENDOR's
# vocabulary; users ask in THEIRS — aliases are the bridge.
DOCS: Tuple[Dict[str, str], ...] = (
    {"id": "shipping", "title": "Shipping policy",
     "text": "Standard shipping is free on qualifying orders and takes 3-5 business days. "
             "Express shipping arrives in 1-2 business days. We ship to the continental US only.",
     "aliases": "delivery deliver mail arrive arrives order"},
    {"id": "warranty", "title": "Warranty policy",
     "text": "All gear carries a 2-year manufacturer warranty covering defects in materials "
             "and workmanship. Normal wear and tear is not covered.",
     "aliases": "broken broke stopped working guarantee repair replace faulty"},
    {"id": "pricematch", "title": "Price-match policy",
     "text": "We match any advertised price from an authorized retailer within 14 days of purchase. "
             "Bring the ad or URL to any branch.",
     "aliases": "cheaper elsewhere found it cheaper competitor discount beat the price"},
)

_STOPWORDS = {"what", "whats", "what's", "is", "are", "the", "your", "you", "a", "an", "of",
              "do", "does", "how", "about", "tell", "me", "can", "i", "my", "policy", "on"}


def RETRIEVER(query: str, top_k: int = 2) -> list:
    """Keyword-overlap retriever over DOCS (mock semantic memory). Returns
    [{"id","title","text","score"}] sorted by score desc; empty when nothing
    overlaps. Swap the body for a vector-store query in production.
    Matching is WORD-PREFIX, not raw substring: "month" still hits "monthly",
    but "pet" no longer hits "comPETitor" — a substring false-HIT quotes the
    WRONG document instead of declining, which is strictly worse than a miss."""
    terms = {w for w in re.findall(r"[a-z']+", query.lower()) if w not in _STOPWORDS}
    scored = []
    for doc in DOCS:
        hay = f"{doc['title']} {doc['text']} {doc.get('aliases', '')}".lower()
        hay_words = set(re.findall(r"[a-z']+", hay))
        score = sum(1 for t in terms if t and any(w.startswith(t) for w in hay_words))
        if score > 0:
            scored.append({**doc, "score": score})
    scored.sort(key=lambda d: -d["score"])
    return scored[:top_k]


# ── Retrieval probes (selftest recall gate) ─────────────── [CUSTOMIZE] ──
# ≥3 consumer-phrasing questions per retrieval intent — the words real users
# type, deliberately NOT copied from DOCS text or INTENT_KEYWORDS: a probe
# derived from the corpus samples the author's vocabulary and passes
# trivially, so it could never catch the lexical-gap misses it exists to
# catch. selftest.retrieval_coverage_preflight asserts every probe retrieves;
# a failing probe means an answerable question would get the honest decline.
RETRIEVAL_PROBES: Dict[str, Tuple[str, ...]] = {
    "faq_policy": (
        "when will my order arrive",
        "my item broke after a year",
        "i found it cheaper somewhere else",
    ),
}

# ── Shared deterministic heuristics (mock-mode fallbacks + fast-router) ──
# Keyword → intent, checked in order. Goodbye MUST stay first and explicit;
# anything unmatched falls to chitchat (never to goodbye). Besides the mock
# classifier, the fast-router gate scans these in LIVE mode as its
# interruption guard (an other-intent keyword hit forces the LLM path), so
# keep them honest per client.                                  [CUSTOMIZE]
INTENT_KEYWORDS: Dict[str, Tuple[str, ...]] = {
    "goodbye": ("bye", "goodbye", "that's all", "thats all", "nothing else",
                "we're done", "no thanks", "done for today"),
    "restart": ("start over", "restart", "reset", "forget all that"),
    # Escalation MUST rank above the task intents: an explicit ask for a
    # person ("a manager, about my order") is a handoff, not an order lookup.
    # Bare "agent" is deliberately absent (too ambiguous — "you're a good agent").
    "human_handoff": ("human", "manager", "supervisor", "real person", "live agent",
                      "speak to a person", "speak to someone", "talk to a person",
                      "representative", "operator"),
    # request_refund MUST precede faq_returns: "refund" requests are actions.
    "request_refund": ("refund",),
    "faq_hours": ("hour", "open", "close", "when are you"),
    "faq_returns": ("return", "exchange"),
    "faq_policy": ("shipping", "warranty", "price match", "price-match", "policy"),
    "order_status": ("order", "track", "where is my", "package", "delivery status"),
    "book_fitting": ("book", "fitting", "appointment", "visit", "come in"),
    # help LAST so "help with my order" reaches order_status first.
    "help": ("help", "what can you do", "what do you do", "capabilities"),
}

# Slot extractors run on EVERY turn in mock mode (so a bare slot answer like
# "downtown tomorrow at 3pm" fills a pending flow). The fast-router gate also
# runs them in LIVE mode mid slot-fill: an extractor hit that survives its
# resolver/validator lets the turn skip the INTENT-tier call.   [CUSTOMIZE]
_ORDER_RE = re.compile(r"\b(AC-?\d{4,}|\d{5,})\b", re.IGNORECASE)
_TIME_RE = re.compile(r"(tomorrow|today|\d{1,2}\s*(am|pm)|\d{1,2}:\d{2}|monday|tuesday|"
                      r"wednesday|thursday|friday|saturday|sunday)", re.IGNORECASE)
_BRANCH_WORDS = {"downtown": "downtown", "river": "downtown",
                 "mall": "mall", "westfield": "mall",
                 "airport": "airport", "terminal": "airport",
                 # Referential phrases the ENTITY RESOLVER must disambiguate:
                 "any branch": "any", "anywhere": "any", "whichever": "any",
                 "nearest": "any", "closest": "any"}


def _extract_branch(text: str) -> Optional[str]:
    low = text.lower()
    for word, branch in _BRANCH_WORDS.items():
        if word in low:
            return branch
    return None


SLOT_EXTRACTORS: Dict[str, Callable[[str], Optional[str]]] = {
    "order_id": lambda t: (m.group(1).upper() if (m := _ORDER_RE.search(t)) else None),
    "branch": _extract_branch,
    # Mock placeholder: any time-like phrase -> fixed ISO slot. Live mode has
    # the ANSWER tier resolve real dates (it gets the current date injected).
    "slot_iso": lambda t: ("2026-01-01T15:00:00" if _TIME_RE.search(t) else None),
}

# ── Semantic entity resolution (pre-validator referential grounding) ─────
# Resolvers run in Think BEFORE Flow.validators. They ground REFERENTIAL
# values ("all vegetables", "any branch", aliases) against the domain catalog:
# return (True, canonical_value) or (False, clarifying_question). This is the
# layer that stops a literal string like "all vegetables" from ever reaching a
# tool as-is (the GreenCart failure).
#
# LIVE-MODE RULE: in live mode the LLM hands over RAW extracted text
# ("tomatoes", "Bell Peppers") — resolvers are the ONLY canonicalization that
# text gets (mock extractors normalize on their own, which is why a missing
# resolver is invisible to mock runs). Therefore EVERY slot whose value keys
# into a catalog/DB/inventory MUST have a resolver here, sharing its synonym/
# plural logic with the mock extractor so the two modes never drift — and the
# selftest's HOOK_CHECKS must exercise it with raw live-style values.
#                                                                [CUSTOMIZE]
_BRANCH_CATALOG = ("downtown", "mall", "airport")


def _resolve_branch(value: str, _slots: dict) -> Tuple[bool, str]:
    v = value.strip().lower()
    if v in _BRANCH_CATALOG:
        return True, v
    for word, branch in _BRANCH_WORDS.items():
        if word in v and branch in _BRANCH_CATALOG:
            return True, branch
    # Referential/unknown ("any", "the usual", a city we don't serve) -> the
    # user must pick a real entity; never guess on their behalf.
    return False, "We have three branches — Downtown, Mall, or Airport. Which one works for you?"


ENTITY_RESOLVERS: Dict[str, Callable[[str, dict], Tuple[bool, str]]] = {
    "branch": _resolve_branch,
}

# Canned knowledge answers for mock mode. RETRIEVAL_INTENTS don't need an
# entry — mock replies are synthesized from the retrieved context.
# NOTE: closing questions are appended by the ANSWER nodes, not baked in here.
#                                                                   [CUSTOMIZE]
MOCK_KNOWLEDGE: Dict[str, str] = {
    "faq_hours": "All branches are open Mon-Sat 9:00-21:00 and Sun 10:00-18:00.",
    "faq_returns": "You can return unused items within 30 days with a receipt; refunds land within 5 business days.",
}
MOCK_CHITCHAT = "Hi! I can help with hours, returns, order tracking, or booking a gear fitting — what would you like?"
MOCK_CLOSING = "Thanks for reaching out — have a great day!"

# Deterministic SYSTEM replies (never model-generated).          [CUSTOMIZE]
HELP_TEXT = ("Here's what I can do: answer questions about hours, returns, and store "
             "policies (shipping, warranty, price-match); track an order; book a gear "
             "fitting; or request a refund. What would you like?")
RESTART_TEXT = "Okay, clean slate — we can start over. What would you like to do?"

# ── Output guardrails (validator exit-filter) ───────────── [CUSTOMIZE] ──
# (pattern, replacement) applied to every outgoing reply. Demo: this channel
# has no pricing authority, so strip invented currency amounts.
BLOCKED_PATTERNS: Tuple[Tuple[re.Pattern, str], ...] = (
    (re.compile(r"(\$\s*\d[\d,]*|\b\d[\d,]*\s*(USD|EUR|ILS|NIS)\b)", re.IGNORECASE),
     "(pricing confirmed by a human agent)"),
)
