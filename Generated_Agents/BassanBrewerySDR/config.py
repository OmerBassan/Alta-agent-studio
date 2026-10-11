"""Domain configuration — THE customization surface of this boilerplate.

The architect skill's Step 4 edits (mostly) THIS file, prompts.py's FACTS-free
sections, and tools.py. The graph, nodes, schemas, and shell are generic and
should rarely need changes.

Bassan Brewery — proactive outbound B2B keg-sales SDR.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Callable, Dict, FrozenSet, List, Optional, Tuple

try:  # load .env before reading safety-constant overrides (idempotent)
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:
    pass

# ── Identity ────────────────────────────────────────────── [CUSTOMIZE] ──
AGENT_NAME = "Bassan Brewery Sales"
# OPENER is spoken as the call's FIRST words by the voice platform (Vapi
# firstMessage), ~500ms after pickup, with zero model calls. Contract: a PLAIN
# string literal on this line (the platform extracts it statically — no
# f-string, no concatenation), <=20 words, human phone-pickup tone, ends with
# ONE question, never empty or whitespace-only.
OPENER = "Hi, this is Alex calling from Bassan Brewery — we supply kegs to bars and restaurants. Got a quick minute?"
EXIT_WORDS = ("exit", "quit")

# ── Ground-truth facts (knowledge intents answer ONLY from these) ─ [CUSTOMIZE] ──
FACTS = """Bassan Brewery — authoritative facts (never invent beyond this):
- We sell premium kegs directly to bars, restaurants, and hospitality venues.
- We work with any drink mix — beer, cider, seltzer, wine — and can supply a
  venue's full pour lineup or just fill gaps alongside an existing supplier.
- Pricing is typically competitive with existing distributors once delivery
  reliability and account service are factored in; exact pricing is confirmed
  by our account manager on the follow-up call, never quoted on this call.
- Venues do not need to drop their current supplier to try us — many keep
  their existing supplier and compare us on a single trial order first.
- Delivery is reliable and account managers proactively reach out ahead of
  renewal dates so venues are never caught scrambling for stock.
- This channel cannot take payment, sign contracts, or quote firm pricing —
  the account manager handles those on the scheduled follow-up call.
"""

# ── Drop-in knowledge base (uploaded corpus) ────────────────────────────────
# Any .txt/.md file in this agent's `knowledge/` folder is CHUNKED into the DOCS
# retrieval corpus at import (see the merge just below the DOCS definition), so
# the RAG subgraph reaches it JUST-IN-TIME on a knowledge question — it is NOT
# appended to FACTS. Appending to FACTS made the whole upload ride EVERY think-
# tier call (latency + bloat); retrieval-gating keeps the think prompt lean and
# only surfaces the relevant slice. This is what the platform's "drop a file"
# upload card writes to. NOTE (skill): a knowledge/FAQ intent backed by uploaded
# files must be a RETRIEVAL_INTENT, or the docs are indexed but never queried.
# Bounded by KNOWLEDGE_MAX_CHARS so a large upload can't blow the corpus budget.
_KNOWLEDGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge")
_KNOWLEDGE_MAX_CHARS = int(os.getenv("KNOWLEDGE_MAX_CHARS", "8000"))


def _slugify(name: str) -> str:
    base = os.path.splitext(name)[0].lower()
    return re.sub(r"[^a-z0-9]+", "-", base).strip("-") or "doc"


def _chunk_text_to_docs(name: str, text: str, max_words: int = 150) -> List[dict]:
    """Split one uploaded file into retrieval-sized DOCS entries (~max_words each,
    on paragraph boundaries) so RETRIEVER returns the relevant slice — not the
    whole file — and the upload never rides the static FACTS/think prompt."""
    slug = _slugify(name)
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    docs: List[dict] = []
    buf: List[str] = []
    count = 0

    def _flush() -> None:
        nonlocal buf, count
        if buf:
            docs.append({"id": f"{slug}-{len(docs)}", "title": name,
                         "text": " ".join(buf), "aliases": ""})
            buf, count = [], 0

    for p in paras:
        words = len(p.split())
        if count and count + words > max_words:
            _flush()
        buf.append(p)
        count += words
    _flush()
    return docs


def _load_knowledge_docs() -> List[dict]:
    if not os.path.isdir(_KNOWLEDGE_DIR):
        return []
    docs: List[dict] = []
    budget = _KNOWLEDGE_MAX_CHARS
    for name in sorted(os.listdir(_KNOWLEDGE_DIR)):
        if not name.lower().endswith((".txt", ".md")):
            continue
        try:
            with open(os.path.join(_KNOWLEDGE_DIR, name), encoding="utf-8",
                      errors="replace") as fh:
                text = fh.read().strip()
        except OSError:
            continue
        if not text:
            continue
        text = text[:budget]
        budget -= len(text)
        docs.extend(_chunk_text_to_docs(name, text))
        if budget <= 0:
            break
    return docs


# Loaded at import; MERGED into DOCS just below the DOCS definition (DOCS is not
# defined yet at this point). FACTS is deliberately left untouched.
_UPLOADED_DOCS = _load_knowledge_docs()

# ── Intents (hierarchical: ANSWER / FLOW / SYSTEM) ──────── [CUSTOMIZE] ──
# Knowledge intents: answered directly from FACTS by the ANSWER tier (no tool).
# obj_price / obj_supplier double as OBJECTION_INTENTS below (A-I-P gate).
KNOWLEDGE_INTENTS: Tuple[str, ...] = ("faq_company", "obj_price", "obj_supplier", "faq_boundaries")

# No corpus was volunteered for this build — no RETRIEVAL_INTENTS.
RETRIEVAL_INTENTS: Tuple[str, ...] = ()

# SYSTEM intents: session-control requests handled DETERMINISTICALLY (no
# model): help/capabilities, restart, and the human_handoff escalation path
# (invariant 26 — the advertised handoff must be a reachable node, not
# conversational copy). goodbye is SYSTEM too (routed to closing) — on this
# outbound agent it also covers a firm decline ("not interested").
SYSTEM_INTENTS: Tuple[str, ...] = ("help", "restart", "human_handoff")

# One-line descriptions fed to the intent-detection prompt. Must cover every
# knowledge intent, every flow, and every SYSTEM intent
# (chitchat/goodbye are added automatically).
INTENT_DESCRIPTIONS: Dict[str, str] = {
    "faq_company": "what Bassan Brewery does, what venues we work with, or general questions about the company",
    "obj_price": "the lead pushes back on cost or says we're too expensive",
    "obj_supplier": "the lead says they already have a supplier or are locked into a contract",
    "faq_boundaries": ("billing disputes, technical delivery problems, or a request for a firm quote "
                       "or signed contract on this call"),
    "lead_profile": "gathering the venue's drink mix, who handles purchasing, renewal timing, and monthly keg volume",
    "book_meeting": "scheduling a meeting with the account manager to go over pricing",
    "send_followup": "the lead asks to be sent information by email instead of continuing the call",
    "help": "what can you do / what is this call about",
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

    SLOT SOURCING (Think pre-fills deterministically before asking anyone):
      - A slot whose name matches a `session_facts` key is filled from it —
        outbound-call metadata (email/name/phone) or an earlier tool's cached
        output — so a value the agent already holds is never asked for.
      - A slot with NO `slot_prompts` entry is never asked aloud; it MUST be
        auto-derivable and is filled from its `SLOT_EXTRACTORS` hook (which
        must be live-safe, e.g. a fixed template body — never a mock
        placeholder). Give a slot a prompt only if the lead should be asked.

    properties: WHAT the action is, as a set — the engine derives the gates
      (authz.PROPERTY_GATES) and tool_exec refuses to run without a matching
      one-time platform record for each:
        "state_changing" -> confirm: an end-user yes/no read-back before Act
                            (checkout, cancel, book, send).
        "liability"      -> hitl: an OPERATOR approves via interrupt/resume
                            (money moves, deletion).
      Both -> both, user confirmation first. Must be a set of known names;
      build_pipeline rejects anything else at startup.
    confirm / hitl: legacy spellings of state_changing / liability, still
      honoured (they can only add gates). Prefer `properties`.
    confirm_template: the yes/no question, .format(**args); empty -> generic.
    validators: per-slot hooks run by Think AFTER entity resolution, before
      Act. Each takes (value, all_slots) and returns
      (ok, normalized_value_or_clarify_question). Resolvers and validators
      MUST be idempotent on canonical values (resolving/validating an
      already-canonical value passes and returns it unchanged) — the fast
      router pre-tests values with these hooks and hands them to Think RAW,
      so every value legitimately passes them twice.
    enrich: route the tool result through the ENRICH (SLM) tier. Set False for
      tools whose "summary" is already perfectly formatted — the graph bypasses
      the SLM hop entirely (deterministic phrasing, one less network call).
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
    properties: FrozenSet[str] = frozenset()


# ── Proactive sales arc (the SDR "spine") ───────────────────── [CUSTOMIZE] ──
@dataclass(frozen=True)
class Stage:
    """One scene of the OUTBOUND sales arc, executed by the zero-model director
    gate (nodes._director) so the agent LEADS the call instead of only reacting.
    See the boilerplate docstring in the original template for the full field
    contract; kept identical here."""
    name: str
    objective: str = ""
    flow: str = ""
    line: str = ""
    nudge: str = ""
    advance_when: Dict[str, object] = field(default_factory=dict)


# The ordered sales spine, extracted from the approved playbook:
#   1. qualify — confirm you've reached the person who handles purchasing, then
#                drink mix, renewal timing, monthly volume (lead_profile flow).
#   2. close   — book fifteen minutes with the account manager (book_meeting flow).
# Discovery is folded into qualify rather than given its own proactive Stage:
# lead_profile already asks the decision-maker question first, and a separate
# lead-in Stage makes turn 1 unique and the stall detector unreachable
# (reasoning-log 2026-09-07).
CALL_ARC: Tuple[Stage, ...] = (
    Stage(name="qualify", flow="lead_profile",
          objective=("confirm you've reached the person who handles beverage purchasing and why "
                     "the call matters, then capture their drink mix, current renewal timing, "
                     "and monthly keg volume"),
          advance_when={"flow_complete": "lead_profile"}),
    Stage(name="close", flow="book_meeting",
          objective="book fifteen minutes with the account manager as the concrete next step",
          advance_when={"flow_complete": "book_meeting"}),
)


# ── Objection architecture: Acknowledge → Isolate → Pivot ──── [CUSTOMIZE] ──
# Objections are ALREADY ordinary KNOWLEDGE_INTENTS (they route to knowledge_node
# and stay grounded in FACTS/RAG). The tuple below is a MARKER over that set —
# it tells the engine "this intent is a push-back, not a question", which is
# what the A-I-P gate conditions on.
OBJECTION_INTENTS: Tuple[str, ...] = ("obj_price", "obj_supplier")

# Objection intent -> the spoken noun phrase for {topic} in the isolate question.
OBJECTION_TOPICS: Dict[str, str] = {
    "obj_price": "the price",
    "obj_supplier": "switching suppliers",
}

# The one-per-call isolate question. MUST contain {topic}, MUST end in a question
# mark, and MUST stay short.
OBJECTION_ISOLATE_TEMPLATE: str = "Besides {topic}, anything else holding you back?"


# ── Micro-commitments (tie-downs) ───────────────────────────── [CUSTOMIZE] ──
# Short agreement checks appended DETERMINISTICALLY by nodes._tiedown at the
# exit filter — zero model calls, zero prompt tokens. Rotated non-repeating
# through filler.pick_from.
TIEDOWNS: List[str] = [
    "Does that make sense?",
    "Sound fair?",
    "That work for you?",
    "Make sense so far?",
]

# Emit a tie-down after this many consecutive statement-ending agent turns.
TIEDOWN_EVERY_N_TURNS = int(os.getenv("TIEDOWN_EVERY_N_TURNS", "2"))

# Hard spoken-reply word budget (TTS airtime).
MAX_REPLY_WORDS = int(os.getenv("MAX_REPLY_WORDS", "20"))


# ── Lead record (conversation memory + the SDR deliverable) ── [CUSTOMIZE] ──
@dataclass(frozen=True)
class SummaryField:
    """One field of the call's structured lead record (state.call_summary),
    built by the zero-model aggregator nodes._update_summary."""
    key: str
    source: str
    label: str = ""


SUMMARY_TEMPLATE: Tuple[SummaryField, ...] = (
    SummaryField(key="contact", source="fact:name", label="Contact"),
    SummaryField(key="phone", source="fact:phone", label="Phone"),
    SummaryField(key="email", source="fact:email", label="Email"),
    SummaryField(key="buyer_character", source="slot:lead_profile.buyer_character", label="Buyer role"),
    SummaryField(key="drink_mix", source="slot:lead_profile.drink_mix", label="Drink mix"),
    SummaryField(key="renewal", source="slot:lead_profile.renewal", label="Renewal timing"),
    SummaryField(key="monthly_volume", source="slot:lead_profile.monthly_volume", label="Monthly volume"),
    SummaryField(key="meeting_time", source="slot:book_meeting.slot_iso", label="Meeting time"),
    SummaryField(key="objections", source="objections", label="Objections raised"),
    SummaryField(key="follow_ups", source="followups", label="Follow-ups"),
    SummaryField(key="needs", source="freetext", label="What the venue needs"),
    SummaryField(key="next_steps", source="freetext", label="Agreed next steps"),
)


# Slot-refusal sentinel (ENGINE constant — do not customize). When the lead
# declines to give an asked slot value ("I'd rather not say"), the engine
# stores this sentinel in the slot so the derived missing-slot computation
# stops re-asking it — a refused question asked twice loses the lead. The
# sentinel is truthy by design. Tools receive it verbatim and should branch
# on it ("caller declined to share"); validators/resolvers skip it.
SLOT_REFUSED = "<declined>"

# ── Qualification slot catalogs, resolvers, and validators ─── [CUSTOMIZE] ──
_DRINK_MIX_CATALOG = ("beer", "cider", "seltzer", "wine", "mixed")
_DRINK_MIX_WORDS = {
    "beer": "beer", "lager": "beer", "ale": "beer", "draft": "beer", "draught": "beer",
    "cider": "cider", "hard cider": "cider",
    "seltzer": "seltzer", "hard seltzer": "seltzer",
    "wine": "wine",
    "mixed": "mixed", "variety": "mixed", "everything": "mixed", "full lineup": "mixed",
}


def _resolve_drink_mix(value: str, _slots: dict) -> Tuple[bool, str]:
    """Referential grounding for the venue's pour lineup: maps raw speech
    ('mostly beer, some cider') onto the catalog, collapsing multiple distinct
    hits to 'mixed' rather than guessing one. Unmatched text asks, never guesses."""
    if value == SLOT_REFUSED:
        return True, value
    low = value.strip().lower()
    hits = {canon for word, canon in _DRINK_MIX_WORDS.items() if word in low}
    if not hits:
        return False, "What's your drink mix — mostly beer, or cider and seltzer too?"
    return True, ("mixed" if len(hits) > 1 else next(iter(hits)))


def _validate_drink_mix(value: str, _slots: dict) -> Tuple[bool, str]:
    """Idempotent format check AFTER resolution — the resolver already
    canonicalizes, so this only guards a value that reached here unresolved."""
    if value == SLOT_REFUSED or value in _DRINK_MIX_CATALOG:
        return True, value
    return False, "What's your drink mix — mostly beer, or cider and seltzer too?"


_BUYER_ROLE_CATALOG = ("purchasing_manager", "beverage_director", "owner", "gm", "other")
_BUYER_ROLE_WORDS = {
    "purchasing manager": "purchasing_manager", "purchasing": "purchasing_manager",
    "beverage director": "beverage_director", "beverage": "beverage_director",
    "owner": "owner",
    "general manager": "gm", "gm": "gm", "manager": "gm",
}


def _resolve_buyer_character(value: str, _slots: dict) -> Tuple[bool, str]:
    """Grounds the caller's role against the catalog of titles that actually
    buy kegs; an unrecognized title (a real person's name, an unlisted role)
    is accepted as 'other' rather than stalling the call on a job title."""
    if value == SLOT_REFUSED:
        return True, value
    low = value.strip().lower()
    for phrase, canon in _BUYER_ROLE_WORDS.items():
        if phrase in low:
            return True, canon
    return True, "other"


def _validate_buyer_character(value: str, _slots: dict) -> Tuple[bool, str]:
    if value == SLOT_REFUSED or value in _BUYER_ROLE_CATALOG:
        return True, value
    return True, "other"


_RENEWAL_BUCKETS = ("immediate", "near_term", "mid_term", "long_term", "unknown")
_RENEWAL_IMMEDIATE_WORDS = ("now", "already up", "this month", "expired", "no contract")
_RENEWAL_LONG_WORDS = ("locked in", "locked-in", "a year", "12 months", "under contract")


def _classify_renewal(text: str) -> str:
    low = text.lower()
    if any(w in low for w in _RENEWAL_IMMEDIATE_WORDS):
        return "immediate"
    if any(w in low for w in _RENEWAL_LONG_WORDS):
        return "long_term"
    m = re.search(r"(\d+)\s*month", low)
    if m:
        months = int(m.group(1))
        if months <= 3:
            return "near_term"
        if months <= 6:
            return "mid_term"
        return "long_term"
    if "month" in low:
        return "near_term"
    if "year" in low:
        return "long_term"
    return "unknown"


def _validate_renewal(value: str, _slots: dict) -> Tuple[bool, str]:
    """Buckets free-form renewal timing ('renews in two months') into a
    sortable category. Never blocks the call on ambiguity — an unclassifiable
    answer is stored as 'unknown' so the account manager still follows up."""
    if value == SLOT_REFUSED:
        return True, value
    if value in _RENEWAL_BUCKETS:
        return True, value
    return True, _classify_renewal(value)


_ONES = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
         "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
         "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
         "nineteen": 19}
_TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
         "eighty": 80, "ninety": 90}


def _words_to_number(text: str) -> Optional[int]:
    tokens = re.findall(r"[a-z]+", text.lower())
    total, current, found = 0, 0, False
    for tok in tokens:
        if tok in _ONES:
            current += _ONES[tok]
            found = True
        elif tok in _TENS:
            current += _TENS[tok]
            found = True
        elif tok == "hundred":
            current = (current or 1) * 100
            found = True
        elif tok == "thousand":
            total += (current or 1) * 1000
            current = 0
            found = True
    total += current
    return total if found else None


def _validate_monthly_volume(value: str, _slots: dict) -> Tuple[bool, str]:
    """Parses digits or spoken number words ('about thirty') into a bounded
    integer keg count; bounds match a realistic single-venue monthly order —
    never a hardcoded fallback that could silently misreport volume."""
    if value == SLOT_REFUSED:
        return True, value
    digits = re.sub(r"[,\s]", "", value)
    m = re.search(r"\d+", digits)
    n = int(m.group(0)) if m else _words_to_number(value)
    if n is None:
        return False, "Roughly how many kegs do you move each month — just a ballpark?"
    if n < 1 or n > 100000:
        return False, "That number sounds off — roughly how many kegs a month, give or take?"
    return True, str(n)


ENTITY_RESOLVERS: Dict[str, Callable[[str, dict], Tuple[bool, str]]] = {
    "drink_mix": _resolve_drink_mix,
    "buyer_character": _resolve_buyer_character,
}


FLOWS: Dict[str, Flow] = {
    "lead_profile": Flow(
        tool="capture_lead_profile",
        slots=("buyer_character", "drink_mix", "renewal", "monthly_volume"),
        slot_prompts={
            "buyer_character": "are you the one who handles beverage purchasing here, or is that someone else",
            "drink_mix": "what's your current drink mix — mostly beer, or cider and seltzer too",
            "renewal": "are you locked into a supplier contract, or is that coming up for renewal",
            "monthly_volume": "roughly how many kegs are you moving a month these days",
        },
        validators={
            "buyer_character": _validate_buyer_character,
            "drink_mix": _validate_drink_mix,
            "renewal": _validate_renewal,
            "monthly_volume": _validate_monthly_volume,
        },
        cache_keys=("buyer_character", "drink_mix", "renewal", "monthly_volume"),
    ),
    "book_meeting": Flow(
        tool="book_sales_call",
        slots=("slot_iso", "email"),
        slot_prompts={
            "slot_iso": "can I set up fifteen minutes with our account manager this week — what day and time works",
        },
        properties=frozenset({"state_changing"}),
        confirm_template="Just to confirm — fifteen minutes with our account manager for {slot_iso}, and I'll send details to {email}. Sound good?",
        cache_keys=("confirmation",),
    ),
    "send_followup": Flow(
        tool="send_email",
        slots=("email", "body"),
        cache_keys=("sent",),
    ),
}

# The ONLY follow-up the agent may offer after each tool, appended
# deterministically by the enrichment node.                     [CUSTOMIZE]
NEXT_STEP_HINTS: Dict[str, str] = {
    "capture_lead_profile": "",
    "book_sales_call": "Our account manager will call at that time to go over pricing.",
    "send_email": "",
}

# ── ENRICH templates (SLM verdict -> deterministic prose) ── [CUSTOMIZE] ──
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
FILLER_ENABLED = os.getenv("FILLER_ENABLED", "1").strip().lower() not in (
    "0", "false", "off", "no", "disabled")
FILLER_DELAY_MS = int(os.getenv("FILLER_DELAY_MS", "250"))

FILLERS_BY_TOOL: Dict[str, List[str]] = {
    "capture_lead_profile": [
        "Got it, noting that down.",
        "Okay, one sec.",
        "Right, jotting that down.",
    ],
    "book_sales_call": [
        "Let me check the account manager's calendar.",
        "One sec — grabbing an open slot.",
        "Checking what's open this week.",
    ],
    "send_email": [
        "Sure — sending that over now.",
        "One sec, getting that email out.",
        "Okay, putting that together.",
    ],
}

FILLER_DEFAULT: List[str] = ["One moment.", "Just a sec.", "Bear with me a moment."]

FILLER_PLAN_CONTINUE: List[str] = ["Still working on it.", "Almost there.", "Just a moment more."]

FILLER_THINKING: List[str] = [
    "Hmm. ",
    "Okay. ",
    "Let's see. ",
    "Right. ",
    "One sec. ",
]

# ── Closing-question bank ─ [CUSTOMIZE] ──
CLOSING_QUESTIONS: List[str] = [
    "Anything else before I let you go?",
    "Anything else you'd like to ask?",
    "Anything else on your mind?",
    "Was there anything else?",
]

_closing_q_index = 0


def _pick_closing() -> str:
    global _closing_q_index
    q = CLOSING_QUESTIONS[_closing_q_index % len(CLOSING_QUESTIONS)]
    _closing_q_index += 1
    return q


CONFIRM_DECLINED_VARIANTS: List[str] = [
    "Okay — I won't go ahead with that; nothing has been changed.",
    "No problem — I've left everything as it was.",
    "Got it — nothing was changed on my end.",
]
CONFIRM_DECLINED_TEXT = CONFIRM_DECLINED_VARIANTS[0]  # selftest compat

PAUSED_RESUME_TEXT = ("By the way, we didn't finish something — "
                      "could you tell me {slot_hint}?")

HITL_DENIED_TEXT = ("I'm sorry — that request couldn't be approved on this channel. "
                    "A human agent will follow up with you.")

# Deterministic escalation reply (invariant 26): the human_handoff SYSTEM
# intent. Recaps what's already been captured so the human starts warm.
HANDOFF_TEXT = ("Of course — I'm connecting you with our sales lead right now; "
               "I'll let them know what you handle and where you're at on renewal, "
               "so you won't have to repeat yourself. Anything else to pass along?")

STALL_THRESHOLD = int(os.getenv("STALL_THRESHOLD", "3"))
STALL_TEXT = ("I'm sorry — we seem to be going in circles, and I clearly haven't "
              "gotten this across. Could you say that in one short sentence? "
              "Or just say 'talk to a human' and I'll hand this call to a person.")

FAILURE_TEXT = ("I hit a snag on our side there — nothing was lost. "
                "Want me to try that again, or should we keep going?")

PLAN_UNSUPPORTED_TEXT = ("I can only chain the actions I actually support — capturing your "
                         "order details, booking time with our account manager, or sending "
                         "a follow-up email. Which of those first?")

VALID_INTENTS: Tuple[str, ...] = (KNOWLEDGE_INTENTS + tuple(FLOWS) + SYSTEM_INTENTS
                                  + ("chitchat", "goodbye", "compound_request"))

INTENT_CATEGORIES: Dict[str, Tuple[str, ...]] = {
    "ANSWER": KNOWLEDGE_INTENTS + ("chitchat",),
    "FLOW": tuple(FLOWS),
    "COMPOUND": ("compound_request",),
    "SYSTEM": SYSTEM_INTENTS + ("goodbye",),
}
CATEGORY_OF: Dict[str, str] = {i: cat for cat, intents in INTENT_CATEGORIES.items() for i in intents}

# ── Safety rails (env-overridable, see .env.example) ────── [CUSTOMIZE] ──
MAX_TOOL_CALLS_PER_TURN = int(os.getenv("MAX_TOOL_CALLS_PER_TURN", "3"))

FAST_ROUTER_ENABLED = os.getenv("FAST_ROUTER_ENABLED", "1").strip().lower() not in (
    "0", "false", "off", "no", "disabled")

RAG_MAX_ITERATIONS = int(os.getenv("RAG_MAX_ITERATIONS", "1"))
_LIVE_LLM = bool(os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_BASE_URL"))
RAG_TIMEOUT_SECONDS = float(os.getenv("RAG_TIMEOUT_SECONDS",
                                      "8.0" if _LIVE_LLM else "2.0"))

RETRIEVAL_MIN_SCORE = float(os.getenv("RETRIEVAL_MIN_SCORE", "0"))
RAG_CACHE_TTL_SECONDS = float(os.getenv("RAG_CACHE_TTL_SECONDS", "300"))

COMPACTION_ENABLED = os.getenv("COMPACTION_ENABLED", "1").strip().lower() not in (
    "0", "false", "off", "no", "disabled")
COMPACTION_MAX_ITEMS = int(os.getenv("COMPACTION_MAX_ITEMS", "12"))

HISTORY_TURNS = int(os.getenv("HISTORY_TURNS", "8"))

MAX_PLAN_STEPS = int(os.getenv("MAX_PLAN_STEPS", "3"))

# ── Semantic memory (Agentic-RAG corpus + retriever) ────── [CUSTOMIZE] ──
# No corpus volunteered for this build — DOCS/RETRIEVAL_PROBES stay empty.
DOCS: Tuple[Dict[str, str], ...] = ()

if _UPLOADED_DOCS:
    DOCS = DOCS + tuple(_UPLOADED_DOCS)

_STOPWORDS = {"what", "whats", "what's", "is", "are", "the", "your", "you", "a", "an", "of",
              "do", "does", "how", "about", "tell", "me", "can", "i", "my", "policy", "on"}


def RETRIEVER(query: str, top_k: int = 2) -> list:
    """Keyword-overlap retriever over DOCS (mock semantic memory). Returns
    [{"id","title","text","score"}] sorted by score desc; empty when nothing
    overlaps. Swap the body for a vector-store query in production."""
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


RETRIEVAL_PROBES: Dict[str, Tuple[str, ...]] = {}

# ── Shared deterministic heuristics (mock-mode fallbacks + fast-router) ──
# Keyword → intent, checked in order. Goodbye MUST stay first and explicit;
# anything unmatched falls to chitchat (never to goodbye).      [CUSTOMIZE]
INTENT_KEYWORDS: Dict[str, Tuple[str, ...]] = {
    "goodbye": ("bye", "goodbye", "that's all", "thats all", "nothing else",
                "we're done", "no thanks", "done for today", "not interested",
                "stop calling", "take me off your list", "we're set", "we are set"),
    "restart": ("start over", "restart", "reset", "forget all that"),
    # Escalation MUST rank above the task intents.
    "human_handoff": ("human", "manager", "supervisor", "real person", "live agent",
                      "speak to a person", "speak to someone", "talk to a person",
                      "representative", "operator"),
    "obj_price": ("too expensive", "too pricey", "can't afford", "cost too much", "price is"),
    "obj_supplier": ("already have a supplier", "already got a supplier", "happy with our supplier",
                     "locked into", "under contract"),
    "send_followup": ("send me an email", "email me", "shoot me an email", "send info", "send information"),
    "faq_boundaries": ("billing dispute", "delivery problem", "technical issue", "firm quote", "sign a contract"),
    "faq_company": ("what do you do", "what is bassan", "who are you", "tell me about your company"),
    "book_meeting": ("book", "schedule", "set up a call", "set up a meeting", "sounds good"),
    "lead_profile": ("our drink mix", "monthly volume", "kegs a month"),
    # help LAST so a more specific keyword wins first.
    "help": ("help", "what can you do", "what do you do", "capabilities"),
}

# Slot extractors run on EVERY turn in mock mode (so a bare slot answer fills
# a pending flow). The fast-router gate also runs them in LIVE mode mid
# slot-fill.                                                    [CUSTOMIZE]
_VOLUME_RE = re.compile(r"\b\d{1,6}\b")
_TIME_RE = re.compile(r"(tomorrow|today|\d{1,2}\s*(am|pm)|\d{1,2}:\d{2}|monday|tuesday|"
                      r"wednesday|thursday|friday|saturday|sunday)", re.IGNORECASE)


def _extract_drink_mix(text: str) -> Optional[str]:
    low = text.lower()
    hits = {canon for word, canon in _DRINK_MIX_WORDS.items() if word in low}
    if not hits:
        return None
    return "mixed" if len(hits) > 1 else next(iter(hits))


def _extract_buyer_character(text: str) -> Optional[str]:
    low = text.lower()
    for phrase, canon in _BUYER_ROLE_WORDS.items():
        if phrase in low:
            return canon
    return None


def _extract_renewal(text: str) -> Optional[str]:
    bucket = _classify_renewal(text)
    return bucket if bucket != "unknown" else None


def _extract_monthly_volume(text: str) -> Optional[str]:
    m = _VOLUME_RE.search(text)
    if m:
        return m.group(0)
    n = _words_to_number(text)
    return str(n) if n is not None else None


SLOT_EXTRACTORS: Dict[str, Callable[[str], Optional[str]]] = {
    "drink_mix": _extract_drink_mix,
    "buyer_character": _extract_buyer_character,
    "renewal": _extract_renewal,
    "monthly_volume": _extract_monthly_volume,
    "slot_iso": lambda t: ("2026-01-01T15:00:00" if _TIME_RE.search(t) else None),
    # body has no slot_prompts entry (never asked aloud) -> fixed live-safe
    # template, per the Flow docstring's auto-derivable rule.
    "body": lambda t: "Thanks for your time today — here's more on Bassan Brewery kegs and pricing for your team to review.",
}

# Canned knowledge answers for mock mode. RETRIEVAL_INTENTS don't need an
# entry.                                                          [CUSTOMIZE]
MOCK_KNOWLEDGE: Dict[str, str] = {
    "faq_company": "We supply premium kegs directly to bars and restaurants, working with any drink mix you pour.",
    "obj_price": "We're usually competitive once delivery and service are factored in.",
    "obj_supplier": "Plenty keep their supplier and just try us on one order.",
    "faq_boundaries": "That's something our account manager handles directly on the follow-up call.",
}
# Empty by design: this agent's CALL_ARC is never empty, so the director always
# supplies its own proactive line on an unrecognized turn. A competing mock
# filler makes turn 1's reply differ from every identical repeat and leaves
# the stall detector unreachable (reasoning-log 2026-09-07).
MOCK_CHITCHAT = ""
MOCK_CLOSING = "Thanks for your time today — talk soon!"

# Deterministic SYSTEM replies (never model-generated).          [CUSTOMIZE]
HELP_TEXT = ("I'm calling to see if Bassan Brewery could supply kegs for your venue — I'd like to "
            "ask a few quick questions and set up time with our account manager. Sound okay?")
RESTART_TEXT = "Okay, clean slate — we can start over. Got a quick minute to chat about your kegs?"

# ── Output guardrails (validator exit-filter) ───────────── [CUSTOMIZE] ──
# This channel has no pricing authority, so strip invented currency amounts —
# exact pricing is confirmed by the account manager, never quoted here.
BLOCKED_PATTERNS: Tuple[Tuple[re.Pattern, str], ...] = (
    (re.compile(r"(\$\s*\d[\d,]*|\b\d[\d,]*\s*(USD|EUR|ILS|NIS)\b)", re.IGNORECASE),
     "(pricing confirmed by our account manager)"),
)
