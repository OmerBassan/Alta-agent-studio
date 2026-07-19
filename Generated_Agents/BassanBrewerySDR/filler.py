# -*- coding: utf-8 -*-
"""Filler channel: canned, pre-answer acknowledgments over a frontend-agnostic
side sink.

WHY a side channel: the graph runs to completion via ``ainvoke`` and only its
``final_response`` crosses back to the Shell. A tool call adds real latency
mid-turn with no user-facing signal. Fillers ("Let me pull up that order…") are
short canned phrases emitted WHILE a tool runs, so the user hears/sees that the
agent is working before the real answer lands.

DESIGN-TIME BANK, ZERO RUNTIME TOKENS: the variants live in ``config`` (written
once by the architect from the tool catalog). Runtime is pure dict-lookup +
rotate — no LLM, no added tokens.

DISPLAY-ONLY: fillers are shown but NEVER appended to the LangGraph message
history / model context — they cost nothing downstream and never contaminate
reasoning.

FRONTEND-AGNOSTIC: the "sink" is anything with ``put_nowait`` (concretely an
``asyncio.Queue``). The text Shell drains it and prints each event as its own
line; a future Vapi/Retell SSE adapter sets its OWN queue as the sink and yields
each event as a content chunk. Same emit code, different renderer — the sink is
the seam a voice frontend plugs into.

See references/Filler_Channel.txt for the full spec.
"""

from __future__ import annotations

import contextvars
from typing import Dict, List, Optional

import config

# The current turn's filler sink. The Shell (or an SSE adapter) sets this before
# invoking the graph; nodes read it via emit(). A ContextVar — not config or
# state — because an asyncio.Queue is not serializable and would break the
# sqlite checkpointer if it rode along in config["configurable"] or AgentState.
_sink: contextvars.ContextVar = contextvars.ContextVar("filler_sink", default=None)

# Rotation counters keyed by tool name (and "_plan" for plan continuations).
# Module-global and deterministic: testable, and it varies the phrasing across
# turns instead of repeating the same line.
_rotation: Dict[str, int] = {}


def set_sink(sink) -> contextvars.Token:
    """Point the filler channel at a sink for the current turn. Returns a token
    to pass to reset_sink() when the turn ends."""
    return _sink.set(sink)


def reset_sink(token: contextvars.Token) -> None:
    _sink.reset(token)


def reset_rotation() -> None:
    """Clear rotation state (selftest determinism)."""
    _rotation.clear()


def pick_from(variants: Optional[List[str]], key: str) -> Optional[str]:
    """Rotate through ``variants`` deterministically, keyed by ``key``. Returns
    None for an empty/absent list."""
    if not variants:
        return None
    i = _rotation.get(key, 0)
    _rotation[key] = i + 1
    return variants[i % len(variants)]


def pick(tool: str) -> Optional[str]:
    """Pick the next filler variant for ``tool`` (its own bank, else the generic
    default). Returns None when the feature is off or no phrase is available."""
    if not config.FILLER_ENABLED:
        return None
    variants = config.FILLERS_BY_TOOL.get(tool) or config.FILLER_DEFAULT
    return pick_from(variants, key=tool)


def emit(event: dict) -> None:
    """Push a filler event to the current sink, or no-op if none is set. The
    display channel must NEVER break a turn, so all errors are swallowed."""
    sink = _sink.get()
    if sink is None:
        return
    try:
        sink.put_nowait(event)
    except Exception:  # a full/closed queue must not fail the agent turn
        pass
