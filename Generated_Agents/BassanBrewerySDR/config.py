"""Domain configuration — THE customization surface of this boilerplate.

The architect skill's Step 4 edits (mostly) THIS file, prompts.py's FACTS-free
sections, and tools.py. The graph, nodes, schemas, and shell are generic and
should rarely need changes.

Domain: Tom, an outbound sales agent for Bassan Brewery (a soft-drinks
supplier for restaurants and event venues). Tom calls warm leads (people who
already left their contact details), qualifies their drink-ordering needs, and
routes qualified leads to the sales team — he never quotes a final price or
discount on the call itself.
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
AGENT_NAME = "Tom — Bassan Brewery Sales"
# Who's calling, why (the hook — a compressed pitch, not a ramble), and one
# question that confirms we have the right person (this answer is what arms
# the lead_profile flow). Cold_Call_Opener_Science: lead with the hook before
# asking anything, or the call reads as a blind interrogation.
OPENER = ("Hi, this is Tom from Bassan Brewery — you left your details for our "
          "year-long price lock. Handle your drink orders?")
EXIT_WORDS = ("exit", "quit")

# ── Ground-truth facts (knowledge intents answer ONLY from these) ─ [CUSTOMIZE] ──
FACTS = """Bassan Brewery — authoritative facts (never invent beyond this):
- Pricing: once agreed, pricing is locked for a full year and never changes mid-year, regardless of the market.
- Contracts: longer-term contracts are available with a standing weekly batched delivery.
- Core lineup: twenty everyday drinks (things like cola, lemon soda, sparkling water, and still water) at fixed year-round prices.
- Rotating lineup: ten specialty and imported drinks (for example Singha, Evian, or San Pellegrino) that change over time. These are normally short-term-order only; a long-term contract on a rotating item is possible but must be flagged for the sales team to confirm.
- Tom cannot quote a specific discount or a final price on this call — real offers come from the sales team after the call.
- Tom cannot help with custom drink recipes, delivery complaints about a past order, or other technical questions — those get logged for the sales team.
"""

# ── Intents (hierarchical: ANSWER / FLOW / SYSTEM) ──────── [CUSTOMIZE] ──
KNOWLEDGE_INTENTS: Tuple[str, ...] = (
    "pricing_info", "product_catalog", "contract_terms",
    "objection_supplier", "objection_pricing", "product_details",
)

# product_details runs through the Agentic-RAG subgraph (ingredients/allergens,
# delivery logistics, damaged-shipment handling — plausible adjacent questions
# too detailed for the small, stable FACTS block above).
RETRIEVAL_INTENTS: Tuple[str, ...] = ("product_details",)

SYSTEM_INTENTS: Tuple[str, ...] = ("help", "restart", "human_handoff")

INTENT_DESCRIPTIONS: Dict[str, str] = {
    "pricing_info": "questions about pricing, price locks, or how costs are set",
    "product_catalog": "what drinks or products Bassan Brewery carries",
    "contract_terms": "questions about contract length, or the weekly batched delivery",
    "objection_supplier": "the lead says they already have a supplier or aren't looking to switch",
    "objection_pricing": "the lead pushes back on price or says they're happy with current costs",
    "product_details": "ingredients, allergens, caffeine, calories/nutrition, delivery logistics, or damaged/short shipments",
    "lead_profile": "gathering the lead's monthly drink volume, product mix, contract timing, and buying style for the sales team",
    "flag_request": ("the lead asks for a specific discount, has a complaint about a past delivery, wants a "
                     "custom drink recipe, or asks a technical question outside the basics — Tom logs it "
                     "for the sales team rather than answering it himself"),
    "help": "what can you do / list your capabilities",
    "restart": "start over / reset the conversation / forget that",
    "human_handoff": ("the user asks for a human, manager, supervisor, or live agent, "
                      "or is clearly frustrated and wants a person instead of the agent"),
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


# ── Slot semantics: units, bounds, catalog grounding ────────────────────
_MAINSTREAM_WORDS = ("coke", "cola", "pepsi", "sprite", "fanta", "water", "soda", "lemonade")
_NICHE_WORDS = ("singha", "evian", "san pellegrino", "pellegrino", "perrier", "premium", "imported")
_ANNUAL_WORDS = ("annual", "yearly", "year-long", "year long")
_MONTHLY_WORDS = ("monthly", "every month", "month to month", "month-to-month")
_BULK_WORDS = ("bulk", "one event", "one-time", "one time", "single event")
_OPPORTUNISTIC_WORDS = ("whenever", "as needed", "opportunist", "depends")
_REFERENTIAL_MIX_WORDS = ("whatever", "usual", "anything", "don't know", "not sure")

_RENEWAL_RE = re.compile(
    r"(renews?[\w\s]{0,30}|in \d+ months?|next (?:month|quarter|year)|this (?:month|quarter|year)|"
    r"january|february|march|april|may|june|july|august|september|october|november|december)",
    re.IGNORECASE)
_VOLUME_RE = re.compile(r"\d{1,7}")


def _validate_monthly_volume(value: str, _slots: dict) -> Tuple[bool, str]:
    """Normalize to a bare digit string; bounce non-numeric or unrealistic
    values with a clarifying question — never a hardcoded default."""
    digits = "".join(c for c in str(value) if c.isdigit())
    if not digits or int(digits) <= 0:
        return False, "Could you give me a rough number of guests or customers per month?"
    if int(digits) > 200000:
        return False, "That number seems quite high — roughly how many guests or customers do you serve monthly?"
    return True, digits


def _extract_drink_mix(text: str) -> Optional[str]:
    low = text.lower()
    has_main = any(w in low for w in _MAINSTREAM_WORDS)
    has_niche = any(w in low for w in _NICHE_WORDS)
    if (has_main and has_niche) or "both" in low or "mix" in low:
        return "a mix of both"
    if has_main:
        return "everyday drinks"
    if has_niche:
        return "specialty imports"
    if any(w in low for w in _REFERENTIAL_MIX_WORDS):
        return "unspecified"   # referential placeholder — the resolver bounces this
    return None


def _resolve_drink_mix(value: str, _slots: dict) -> Tuple[bool, str]:
    low = value.strip().lower()
    if low in ("everyday drinks", "specialty imports", "a mix of both"):
        return True, low
    has_main = any(w in low for w in _MAINSTREAM_WORDS)
    has_niche = any(w in low for w in _NICHE_WORDS)
    if has_main and has_niche:
        return True, "a mix of both"
    if has_main:
        return True, "everyday drinks"
    if has_niche:
        return True, "specialty imports"
    if "both" in low or "mix" in low:
        return True, "a mix of both"
    return False, ("Just so I log this right — is that mostly everyday drinks like cola and water, "
                  "specialty imports like Singha or Evian, or a mix of both?")


def _extract_buyer_character(text: str) -> Optional[str]:
    low = text.lower()
    if any(w in low for w in _ANNUAL_WORDS):
        return "a standing annual contract"
    if any(w in low for w in _BULK_WORDS):
        return "a bulk order for one event"
    if any(w in low for w in _MONTHLY_WORDS):
        return "a monthly order"
    if any(w in low for w in _OPPORTUNISTIC_WORDS):
        return "ordering as needed"
    return None


def _resolve_buyer_character(value: str, _slots: dict) -> Tuple[bool, str]:
    low = value.strip().lower()
    canonical = ("a standing annual contract", "a monthly order",
                "a bulk order for one event", "ordering as needed")
    if low in canonical:
        return True, low
    if any(w in low for w in _ANNUAL_WORDS):
        return True, "a standing annual contract"
    if any(w in low for w in _BULK_WORDS):
        return True, "a bulk order for one event"
    if any(w in low for w in _MONTHLY_WORDS):
        return True, "a monthly order"
    if any(w in low for w in _OPPORTUNISTIC_WORDS):
        return True, "ordering as needed"
    return False, ("Would you say that's a standing annual contract, a monthly order, "
                  "a bulk order for one event, or just ordering as needed?")


def _extract_renewal(text: str) -> Optional[str]:
    m = _RENEWAL_RE.search(text)
    return m.group(0).strip() if m else None


def _extract_volume(text: str) -> Optional[str]:
    m = _VOLUME_RE.search(text)
    return m.group(0) if m else None


# Shared with INTENT_KEYWORDS["flag_request"] below so the extractor never
# fires more broadly than the intent it feeds — an unconditional extractor
# here would force EVERY knowledge-question detour back into lead_profile via
# the continuation guard, regardless of content (a Context-Blind-Fallback-
# style bug, just on the extractor side instead of the fallback classifier).
_FLAG_TRIGGER_WORDS = ("discount", "special price", "custom recipe", "recipe idea",
                      "complaint", "unhappy with", "problem with my order", "technical question about")


def _extract_request_details(text: str) -> Optional[str]:
    low = text.lower()
    if any(w in low for w in _FLAG_TRIGGER_WORDS):
        return text.strip()
    return None


FLOWS: Dict[str, Flow] = {
    "lead_profile": Flow(
        tool="submit_lead_profile",
        slots=("monthly_volume", "drink_mix", "contract_renewal", "buyer_character"),
        # Each prompt is ONE short spoken question — no product-name examples and
        # no baked-in option menus (those bleed other phases into the questionnaire
        # and make a small live model read a long list). When the lead is vague,
        # the drink_mix / buyer_character RESOLVERS below bounce with the choices.
        slot_prompts={
            "monthly_volume": "roughly how many guests or customers you serve in a typical month",
            "drink_mix": "whether you mostly serve everyday drinks or specialty imports too",
            "contract_renewal": "when your current supply arrangement is up for renewal",
            "buyer_character": "how you'd prefer to order — an ongoing arrangement, or just as you need it",
        },
        validators={"monthly_volume": _validate_monthly_volume},
        # A read-back before the write fires (Voice_SDR_Reliability rule 6):
        # STT most often mishears the volume number and the drink-mix category.
        confirm=True,
        confirm_template=("Just to make sure I've got this right — that's about {monthly_volume} guests "
                          "a month, mostly {drink_mix}. Did I get that right?"),
        enrich=False,
        cache_keys=("lead_reference",),
    ),
    "flag_request": Flow(
        tool="flag_for_team",
        slots=("request_details",),
        slot_prompts={"request_details": "what you'd like the team to help with"},
        enrich=False,
    ),
}

ENTITY_RESOLVERS: Dict[str, Callable[[str, dict], Tuple[bool, str]]] = {
    "drink_mix": _resolve_drink_mix,
    "buyer_character": _resolve_buyer_character,
}

SLOT_EXTRACTORS: Dict[str, Callable[[str], Optional[str]]] = {
    "monthly_volume": _extract_volume,
    "drink_mix": _extract_drink_mix,
    "contract_renewal": _extract_renewal,
    "buyer_character": _extract_buyer_character,
    "request_details": _extract_request_details,
}

# The ONLY follow-up the agent may offer after each tool, appended
# deterministically by the enrichment node.                     [CUSTOMIZE]
NEXT_STEP_HINTS: Dict[str, str] = {
    "submit_lead_profile": "Someone from Bassan Brewery's sales team will follow up with a real offer soon.",
    "flag_for_team": "Our sales team will reach out about that directly.",
}

# ── ENRICH templates (SLM verdict -> deterministic prose) ── [CUSTOMIZE] ──
ENRICH_TEMPLATES: Dict[str, str] = {
    "confirm": "Done — {facts}.",
    "regret":  "Sorry — {facts}.",
    "neutral": "{facts}.",
}

# ── Filler channel (references/Filler_Channel.txt) ──────── [CUSTOMIZE] ──
FILLER_ENABLED = os.getenv("FILLER_ENABLED", "1").strip().lower() not in (
    "0", "false", "off", "no", "disabled")
FILLER_DELAY_MS = int(os.getenv("FILLER_DELAY_MS", "300"))

FILLERS_BY_TOOL: Dict[str, List[str]] = {
    "submit_lead_profile": [
        "Let me get this logged for our team.",
        "One sec, saving these details.",
        "Just capturing this for the team.",
    ],
    "flag_for_team": [
        "Let me flag that for our team.",
        "One moment, noting that down.",
        "I'll get this over to the team.",
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

CONFIRM_DECLINED_TEXT = ("Okay — I won't go ahead with that; nothing has been changed. "
                         "Anything else I can help with?")

PAUSED_RESUME_TEXT = ("By the way, we didn't finish your {flow} — "
                      "could you tell me {slot_hint}?")

HITL_DENIED_TEXT = ("I'm sorry — that request couldn't be approved on this channel. "
                    "A human agent will follow up with you. Anything else I can help with?")

HANDOFF_TEXT = ("Of course — I'm passing this conversation to a person from our team right now; "
                "they'll see everything so far, so you won't have to repeat yourself. "
                "If there's anything you'd like me to note for them, tell me and I'll pass it along.")

STALL_THRESHOLD = int(os.getenv("STALL_THRESHOLD", "3"))
STALL_TEXT = ("I'm sorry — we seem to be going in circles, and I clearly haven't "
              "resolved what you need. Could you rephrase it in one short sentence? "
              "Or just say 'talk to a human' and I'll hand this conversation to a person.")

FAILURE_TEXT = ("I hit a snag saving that on our end — nothing was lost. "
               "You can ask me to try again, or I can help with something else.")

PLAN_UNSUPPORTED_TEXT = ("I can only chain the actions I actually support — gathering your order "
                         "details or flagging something for our team. Which of those would you "
                         "like to start with?")

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

MAX_PLAN_STEPS = int(os.getenv("MAX_PLAN_STEPS", "3"))

# ── Semantic memory (Agentic-RAG corpus + retriever) ────── [CUSTOMIZE] ──
# Small corpus for product_details: plausible adjacent questions (ingredients/
# allergens, delivery logistics, damaged shipments) that are too detailed for
# the stable FACTS block but real enough that a lead might ask mid-call.
DOCS: Tuple[Dict[str, str], ...] = (
    {"id": "ingredients", "title": "Ingredients & allergens",
     "text": "Our mainstream drinks are made from carbonated water, cane sugar, and natural flavoring; "
             "colas and several sodas contain caffeine. Full allergen lists are available on request "
             "for any product in our lineup.",
     "aliases": "ingredient ingredients allergen allergens allergy caffeine sugar"},
    {"id": "delivery", "title": "Delivery logistics",
     "text": "Standing weekly delivery batches are scheduled on a fixed day agreed at contract signing; "
             "single events can request a one-off delivery window instead.",
     "aliases": "delivery truck schedule route batch logistics weekly"},
    {"id": "damages", "title": "Damaged or short shipments",
     "text": "Any bottles arriving broken or a shipment arriving short is replaced on the next scheduled "
             "delivery at no extra charge; report it within 48 hours.",
     "aliases": "broken damaged short missing bottles replace"},
)

_STOPWORDS = {"what", "whats", "what's", "is", "are", "the", "your", "you", "a", "an", "of",
              "do", "does", "how", "about", "tell", "me", "can", "i", "my", "policy", "on"}


def RETRIEVER(query: str, top_k: int = 2) -> list:
    """Keyword-overlap retriever over DOCS (mock semantic memory). Returns
    [{"id","title","text","score"}] sorted by score desc; empty when nothing
    overlaps. Swap the body for a vector-store query in production.
    Matching is WORD-PREFIX, not raw substring."""
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
RETRIEVAL_PROBES: Dict[str, Tuple[str, ...]] = {
    "product_details": (
        "does the cola have caffeine in it",
        "what happens if a delivery shows up damaged",
        "can we get drinks delivered just for one event instead of every week",
    ),
}

# ── Shared deterministic heuristics (mock-mode fallbacks + fast-router) ──
# Order matters: goodbye/restart/human_handoff rank above task intents so an
# explicit escalation always wins; help stays last so "help with my order"
# reaches the real intent first.                                [CUSTOMIZE]
INTENT_KEYWORDS: Dict[str, Tuple[str, ...]] = {
    "goodbye": ("bye", "goodbye", "that's all", "thats all", "nothing else",
                "we're done", "no thanks", "done for today", "not interested"),
    "restart": ("start over", "restart", "reset", "forget all that"),
    "human_handoff": ("human", "manager", "supervisor", "real person", "live agent",
                      "speak to a person", "speak to someone", "talk to a person",
                      "representative", "operator"),
    "flag_request": _FLAG_TRIGGER_WORDS,
    "objection_supplier": ("already have a supplier", "already working with",
                           "not looking to switch", "happy with our supplier"),
    "objection_pricing": ("happy with our current price", "already get a good price",
                          "your price is too high", "too expensive"),
    "pricing_info": ("pricing", "price lock", "how much do you charge", "cost of"),
    "product_catalog": ("what drinks", "what products", "your lineup", "what do you carry"),
    "contract_terms": ("contract length", "how long is the contract", "weekly delivery",
                       "batched delivery", "standing order"),
    "product_details": ("ingredient", "allergen", "caffeine", "damaged shipment", "short shipment",
                        "one-off delivery", "logistics", "calories", "nutrition facts"),
    "lead_profile": ("handle our drink orders", "handle the drink orders", "handle drink orders",
                     "i order the drinks", "i'm the one who orders", "yes that's me", "speaking here"),
    # help LAST so "help with my order" reaches the real intent first.
    "help": ("help", "what can you do", "what do you do", "capabilities"),
}

# Canned knowledge answers for mock mode. RETRIEVAL_INTENTS don't need an
# entry — mock replies are synthesized from the retrieved context.  [CUSTOMIZE]
MOCK_KNOWLEDGE: Dict[str, str] = {
    "pricing_info": ("Our pricing is locked for a full year once we agree terms, so it never "
                     "creeps up on you mid-year. Would you like our team to look at your setup?"),
    "product_catalog": ("We carry twenty everyday drinks at fixed year-round prices, plus ten "
                        "rotating specialty imports. Anything in particular you're after?"),
    "contract_terms": ("Longer contracts come with a standing weekly batched delivery, right up "
                       "to renewal. Is that the kind of arrangement you're after?"),
    "objection_supplier": ("Totally fair — a lot of our customers felt that way before switching for "
                           "the year-long price lock. Are you the one who handles your drink orders?"),
    "objection_pricing": ("I hear you — our price is locked for a full year, so you're protected "
                          "whatever the market does. Are you the one who handles your drink orders?"),
}
MOCK_CHITCHAT = ("Hi, I'm Tom with Bassan Brewery — good to chat! Are you the person who "
                 "handles your drink orders?")
MOCK_CLOSING = "No problem at all — I'll leave the door open in case anything changes. Thanks for your time!"

# Deterministic SYSTEM replies (never model-generated).          [CUSTOMIZE]
HELP_TEXT = ("Here's what I can do: answer questions about our pricing, product lineup, contract "
            "terms, ingredients, or delivery logistics; gather details about your drink orders for "
            "our sales team; or flag something like a discount request for the team to handle "
            "directly. What would you like?")
RESTART_TEXT = "Okay, clean slate — we can start over. What would you like to do?"

# ── Output guardrails (validator exit-filter) ───────────── [CUSTOMIZE] ──
# Tom has no pricing authority on this channel — strip any invented currency amounts.
BLOCKED_PATTERNS: Tuple[Tuple[re.Pattern, str], ...] = (
    (re.compile(r"(\$\s*\d[\d,]*|\b\d[\d,]*\s*(USD|EUR|ILS|NIS)\b)", re.IGNORECASE),
     "(pricing confirmed by our sales team)"),
)
