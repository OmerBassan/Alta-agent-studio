"""Runtime brain adapter — request parsing foundation (Day 1 PM, step 1).

Turns a raw Vapi custom-LLM POST body into a normalized ``VapiTurn`` ready to
inject into a LangGraph invocation. The graph wiring (loading the generated
NorthwindSDR project + filler->SSE streaming) is the next step and lives below
the parsing layer; this file currently establishes the confirmed-correct
extraction that everything else builds on.

Payload shape — CONFIRMED from real calls (builder_platform/vapi_raw_capture.jsonl and
the adapter stdout), not from spec:
  body["call"]["id"]      -> UUID, e.g. "019f6542-1f8e-722c-91ad-ccc34f8b33eb"
                             This is the LangGraph thread_id (report §5C).
  body["messages"]        -> OpenAI-style array of {"role","content"} turns.
                             Vapi RESENDS the full transcript every turn, so the
                             array grows (3 -> 5 -> ...); we never persist it.
  body["stream"]          -> always true for interactive dialogue.

Barge-in: there is NO "barge_in"/interruption flag in this payload. Vapi handles
interruptions on its side (it stops the audio) and surfaces them only as a
RESENT / CORRECTED messages array on the same call_id — sometimes two POSTs for
one utterance (observed: same call_id, msgs=3 twice, last user text growing
"Yo." -> "Yo. What's up, Niko?"). Hence ``is_duplicate_of`` below: the runtime
must be idempotent against corrected re-sends or it will double-process a turn.
"""

from __future__ import annotations

import asyncio
import hashlib
import importlib
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Any, AsyncIterator


@dataclass
class VapiTurn:
    """Normalized view of one Vapi custom-LLM request."""

    thread_id: str
    user_text: str            # the current user utterance (last user message)
    messages: list[dict]      # full OpenAI-style history Vapi sent this turn
    stream: bool
    system_prompt: str | None  # first system message, if Vapi includes one
    lead_facts: dict[str, str] = field(default_factory=dict)  # outbound-call metadata
    raw: dict = field(repr=False, default_factory=dict)

    @property
    def turn_fingerprint(self) -> str:
        """Stable hash of (thread_id + current user text).

        Two POSTs on the same call with the same final user text are the same
        logical turn (a Vapi transcript correction / endpoint double-fire). Use
        this to dedupe before invoking the graph.
        """
        h = hashlib.sha1(f"{self.thread_id}\x00{self.user_text}".encode())
        return h.hexdigest()


# Where Vapi attaches per-call lead/CRM data on an outbound call. Checked in
# order; the first non-empty dict wins. Web test calls carry none of these, so
# lead injection is a silent no-op there.
_LEAD_FACT_PATHS: tuple[tuple[str, ...], ...] = (
    ("call", "metadata"),
    ("call", "assistantOverrides", "variableValues"),
    ("assistantOverrides", "variableValues"),
    ("metadata",),
)


def extract_lead_facts(body: dict[str, Any]) -> dict[str, str]:
    """Flat string->string map of the lead's metadata Vapi attached to the call.

    Untrusted boundary: only scalar values survive (a nested object or list is
    dropped, never stringified into the prompt), keys must be strings. Returns
    {} when nothing is attached — the common case for a web test call — so the
    caller can treat injection as optional.
    """
    for path in _LEAD_FACT_PATHS:
        node: Any = body
        for key in path:
            node = node.get(key) if isinstance(node, dict) else None
            if node is None:
                break
        if isinstance(node, dict) and node:
            facts = {k: str(v) for k, v in node.items()
                     if isinstance(k, str) and isinstance(v, (str, int, float, bool))}
            if facts:
                return facts
    return {}


def parse_vapi_request(body: dict[str, Any]) -> VapiTurn:
    """Extract the fields we inject into LangGraph from a raw Vapi POST body.

    Defensive by design: Vapi is an external boundary (untrusted input), so we
    validate shape rather than assume it. A malformed body yields a VapiTurn
    with empty user_text, which the caller treats as a no-op turn.
    """
    call = body.get("call") or {}
    thread_id = call.get("id") or "default_session"

    messages = body.get("messages") or []
    if not isinstance(messages, list):
        messages = []

    user_text = ""
    for m in reversed(messages):
        if isinstance(m, dict) and m.get("role") == "user":
            user_text = (m.get("content") or "").strip()
            break

    system_prompt = None
    for m in messages:
        if isinstance(m, dict) and m.get("role") == "system":
            system_prompt = m.get("content")
            break

    return VapiTurn(
        thread_id=thread_id,
        user_text=user_text,
        messages=messages,
        stream=bool(body.get("stream", False)),
        system_prompt=system_prompt,
        lead_facts=extract_lead_facts(body),
        raw=body,
    )


def langgraph_config(turn: VapiTurn) -> dict[str, Any]:
    """Build the LangGraph run config from a parsed turn (report §5C).

    call.id -> thread_id so the checkpointer keeps per-call state (qualification
    slots, booking progress) across turns without us persisting the transcript.
    """
    return {"configurable": {"thread_id": turn.thread_id}}


# --- turn-level idempotency guard -------------------------------------------
# Keyed by thread_id -> last processed fingerprint. Guards against Vapi's
# corrected-transcript re-sends double-invoking the graph for one utterance.
_last_fingerprint: dict[str, str] = {}

# Calls whose lead metadata has already been seeded into session_facts. Lead
# facts go in ONCE, on the first turn: session_facts accumulates transactional
# identifiers across the call, and re-seeding (which replaces the channel) would
# wipe them. In-memory, per process — a mid-call process restart re-seeds, which
# is harmless (turn 1 has no identifiers to lose).
_lead_seeded: set[str] = set()


def is_duplicate_of_last(turn: VapiTurn) -> bool:
    """True if this exact (call, user_text) turn was already processed."""
    fp = turn.turn_fingerprint
    if _last_fingerprint.get(turn.thread_id) == fp:
        return True
    _last_fingerprint[turn.thread_id] = fp
    return False


# --- the brain: generated-project loader + streaming turn runner ------------
#
# Loads a generated agent project (a full Python package: config/tools/graph/…)
# via sys.path insert + build_pipeline, and runs turns through the filler->SSE
# queue pattern:
#
#   producer:  graph.ainvoke as a background task; every filler event the graph
#              emits lands on an asyncio.Queue (filler.set_sink) as it happens.
#   consumer:  stream_turn() drains the queue and yields each filler text as an
#              audible latency-cover segment, then the sanitized final reply in
#              sentence chunks (TTS starts on the first sentence).
#   sentinel:  the producer's try/finally ALWAYS enqueues _END — success, crash,
#              or cancellation — so the consumer can never hang on queue.get().
#              Belt-and-suspenders: every get() also has a wall-clock ceiling
#              (RUNTIME_TURN_TIMEOUT_S, default 45s > the graph's own 30s LLM
#              hard timeout); on breach we speak a short apology instead of
#              leaving dead air on the call.

from sanitizer import sanitize_text, sentence_chunks

_END = object()  # queue sentinel: the turn is over, nothing more will arrive

DEFAULT_AGENT_DIR = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..",
    "Generated_CLI_Agents", "NorthwindSDRConcierge_20260712_224830",
))

APOLOGY = ("Sorry, I'm having a technical hiccup on my end. "
           "Could you say that again in a moment?")
REASK = "Sorry, I didn't catch that. Could you say it again?"

# Pre-think filler (turn acknowledgment): a short acoustic token pushed the
# moment the turn arrives, BEFORE the graph runs. Tool fillers only cover
# tool latency; a pure-reasoning turn (INTENT -> ANSWER, no tool) is silent
# for its whole 4-5s TTFT — dead air on a phone. This token starts the TTS
# immediately and buys the pipeline that gap. Generated agents ship their own
# bank in their own voice (config.FILLER_THINKING, required by the skill's
# voice pass); this platform bank is the fallback for agents without one.
# Disable with PRETHINK_FILLER=0.
FILLER_THINKING = [
    "Hmm… ",
    "Umm… ",
    "Let's see… ",
    "Right. ",
    "Okay… ",
    "Mm-hmm… ",
]


def _prethink_enabled() -> bool:
    return os.environ.get("PRETHINK_FILLER", "1").strip().lower() not in (
        "0", "false", "no", "off")


class AgentRuntime:
    """One loaded generated agent: its compiled graph + filler seam + reset dict.

    Construct via :meth:`load` (real project) or directly with injected parts
    (tests). One runtime per process — the subprocess-per-agent model from the
    plan; regenerating an agent restarts the process, never re-imports.
    """

    def __init__(self, graph, filler_mod, turn_reset: dict,
                 make_user_message, agent_name: str = "agent",
                 filler_thinking: list | None = None) -> None:
        self.graph = graph
        self.filler = filler_mod
        self.turn_reset = dict(turn_reset)
        self._make_user_message = make_user_message
        self.agent_name = agent_name
        # Agent-voiced pre-think bank (config.FILLER_THINKING); platform
        # fallback when the agent doesn't declare one.
        self.filler_thinking = list(filler_thinking) if filler_thinking else FILLER_THINKING
        self._locks: dict[str, asyncio.Lock] = {}

    @classmethod
    def load(cls, agent_dir: str | None = None) -> "AgentRuntime":
        agent_dir = os.path.abspath(agent_dir or os.environ.get("AGENT_DIR")
                                    or DEFAULT_AGENT_DIR)
        if not os.path.isdir(agent_dir):
            raise FileNotFoundError(f"AGENT_DIR does not exist: {agent_dir}")

        # Voice latency knobs — set BEFORE the agent's modules import (its
        # load_dotenv never overrides existing env). setdefault so an explicit
        # operator env still wins.
        os.environ.setdefault("FILLER_DELAY_MS", "0")     # fillers ARE the latency cover
        os.environ.setdefault("FAST_ROUTER_ENABLED", "1")
        os.environ.setdefault("RAG_MAX_ITERATIONS", "1")

        sys.path.insert(0, agent_dir)
        config = importlib.import_module("config")
        filler_mod = importlib.import_module("filler")
        graph_mod = importlib.import_module("graph")
        llm = importlib.import_module("llm_client")
        from langchain_core.messages import HumanMessage
        from langgraph.checkpoint.memory import MemorySaver

        graph = graph_mod.build_pipeline(checkpointer=MemorySaver())


        return cls(
            graph=graph,
            filler_mod=filler_mod,
            # The engine's own reset dict — copying it here would drift.
            turn_reset=graph_mod.TURN_RESET,
            make_user_message=lambda text: HumanMessage(content=text),
            agent_name=config.AGENT_NAME,
            filler_thinking=getattr(config, "FILLER_THINKING", None),
        )

    async def stream_turn(self, turn: VapiTurn) -> AsyncIterator[str]:
        """Run one turn; yield speakable text segments (fillers, then reply)."""
        if not turn.user_text:
            yield REASK
            return
        if is_duplicate_of_last(turn):
            return  # corrected-transcript re-send; the first request is answering

        # Pre-think acknowledgment: first SSE chunk leaves NOW, before the
        # graph (and before any lock wait) — TTS starts speaking while the
        # INTENT -> ANSWER pipeline is still thinking. Never on re-asks or
        # duplicates (those must stay instant/silent respectively).
        if _prethink_enabled():
            yield random.choice(self.filler_thinking)

        # Serialize turns per call: two POSTs racing one checkpointer thread
        # would interleave state writes.
        lock = self._locks.setdefault(turn.thread_id, asyncio.Lock())
        async with lock:
            queue: asyncio.Queue = asyncio.Queue()
            token = self.filler.set_sink(queue)  # producer task inherits this context

            payload = dict(self.turn_reset)
            payload["user_message"] = turn.user_text
            payload["recent_messages"] = [self._make_user_message(turn.user_text)]

            # Lead-context injection (outbound calls): on the FIRST turn of a
            # call, seed the lead's metadata into session_facts so the KNOWN
            # FACTS prompt line carries it from the opening exchange. First turn
            # only — see _lead_seeded. No metadata (web test call) = no-op.
            if turn.lead_facts and turn.thread_id not in _lead_seeded:
                payload["session_facts"] = dict(turn.lead_facts)
                _lead_seeded.add(turn.thread_id)

            async def _produce() -> None:
                try:
                    state = await self.graph.ainvoke(payload, config=langgraph_config(turn))
                    queue.put_nowait({"type": "final", "state": state or {}})
                except Exception as exc:  # typed result onto the queue, never lost
                    queue.put_nowait({"type": "error", "error": repr(exc)})
                finally:
                    queue.put_nowait(_END)  # ALWAYS: success, crash, or cancel

            task = asyncio.create_task(_produce())
            ceiling = float(os.environ.get("RUNTIME_TURN_TIMEOUT_S", "45"))
            try:
                while True:
                    try:
                        item = await asyncio.wait_for(queue.get(), timeout=ceiling)
                    except asyncio.TimeoutError:
                        print(f"[runtime] turn ceiling {ceiling}s breached "
                              f"(call={turn.thread_id})", flush=True)
                        yield APOLOGY
                        return
                    if item is _END:
                        return
                    kind = (item or {}).get("type", "")
                    if kind == "final":
                        for seg in self._final_segments(item["state"]):
                            yield seg
                    elif kind == "error":
                        print(f"[runtime] graph error (call={turn.thread_id}): "
                              f"{item['error']}", flush=True)
                        yield APOLOGY
                    else:  # filler event: audible latency cover
                        text = (item or {}).get("text", "")
                        if text:
                            yield text + " "
            finally:
                task.cancel()
                self.filler.reset_sink(token)

    def _final_segments(self, state: dict) -> list[str]:
        if state.get("__interrupt__"):
            # A hitl=True flow suspended for operator approval; no operator
            # console exists on a phone call yet, so promise the follow-up.
            return ["That needs a quick approval from my team. "
                    "We'll follow up with you shortly. Anything else?"]
        text = sanitize_text(state.get("final_response", ""))
        # Trailing space per segment: chunk contents are concatenated verbatim
        # downstream, and "Enterprise.Business" reads wrong to a TTS voice.
        return [s + " " for s in sentence_chunks(text)] if text else [REASK]


# One runtime per process (plan: subprocess-per-agent, restart on regenerate).
_runtime: AgentRuntime | None = None


def get_runtime() -> AgentRuntime:
    global _runtime
    if _runtime is None:
        _runtime = AgentRuntime.load()
    return _runtime


# --- self-check against captured ground truth -------------------------------
if __name__ == "__main__":
    # Sanity check on the exact bodies Vapi sent (from the observed logs).
    sample = {
        "call": {"id": "019f6542-1f8e-722c-91ad-ccc34f8b33eb"},
        "stream": True,
        "messages": [
            {"role": "system", "content": "You are Alta."},
            {"role": "assistant", "content": "Hi, this is Alta."},
            {"role": "user", "content": "Yo. What's up, Niko?"},
        ],
    }
    t = parse_vapi_request(sample)
    assert t.thread_id == "019f6542-1f8e-722c-91ad-ccc34f8b33eb"
    assert t.user_text == "Yo. What's up, Niko?"
    assert t.stream is True
    assert t.system_prompt == "You are Alta."
    assert langgraph_config(t) == {
        "configurable": {"thread_id": "019f6542-1f8e-722c-91ad-ccc34f8b33eb"}
    }
    # duplicate re-send (Vapi correction) is caught the second time
    assert is_duplicate_of_last(t) is False
    assert is_duplicate_of_last(t) is True

