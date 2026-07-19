# -*- coding: utf-8 -*-
"""Python mirror of the `alta:ask` parser in static/index.html.

The builder emits ONE fenced ```alta:ask block (strict JSON) as the last thing
in a turn. The browser parses it into a question card; this module gives the
headless driver and the tests the same view of a turn.

Semantics MUST match the JS (index.html, "Guided wizard: alta:ask protocol"):
  stripFenceForLive -> visible_text   (text before the fence, right-trimmed)
  parseAskBlock     -> parse_ask_block (first fence, strict JSON, object only)
Anything malformed parses to None so the turn degrades to ordinary chat.
"""

from __future__ import annotations

import json
import re

ASK_OPEN = "```alta:ask"
ASK_FENCE_RE = re.compile(r"```alta:ask\s*(.*?)```", re.DOTALL)

STEP_ORDER = ["mission", "qualification", "objections", "close",
              "boundaries", "review", "build"]
STEP_LABELS = {
    "mission": "Mission", "qualification": "Qualify", "objections": "Objections",
    "close": "Close", "boundaries": "Boundaries", "review": "Review",
    "build": "Build",
}


def visible_text(text: str) -> str:
    """The part of a turn shown as a normal bubble: everything before the fence."""
    i = text.find(ASK_OPEN)
    return (text[:i] if i >= 0 else text).rstrip()


def parse_ask_block(text: str) -> dict | None:
    """The first well-formed ask-block in `text`, or None (degrade to chat)."""
    m = ASK_FENCE_RE.search(text)
    if not m:
        return None
    try:
        obj = json.loads(m.group(1).strip())
    except (ValueError, TypeError):
        return None
    return obj if isinstance(obj, dict) else None


def format_card(block: dict) -> str:
    """Pretty-print an ask-block for the headless log (mirrors the UI card)."""
    # ASCII only: this renders to consoles whose encoding is not UTF-8 (a
    # cp1255 Windows console cannot encode box-drawing characters and raises).
    phase = block.get("phase") or ""
    label = STEP_LABELS.get(phase, phase)
    step, of = block.get("step"), block.get("of")
    head = f"+-- {label or 'ASK'}"
    if step and of:
        head += f" | Step {step} of {of}"
    lines = [head]
    if block.get("kind") == "approve":
        approve = block.get("approve_label") or "Looks great"
        revise = block.get("revise_label") or "I'd change something"
        lines.append(f"|  {block.get('intro') or 'Does this look right?'}")
        lines.append(f"+-- [ {approve} ]  [ {revise} ]")
        return "\n".join(lines)
    if block.get("intro"):
        lines.append(f"|  {block['intro']}")
    for q in block.get("questions") or []:
        lines.append(f"|  * {q.get('label', '')}")
        if q.get("hint"):
            lines.append(f"|      ({q['hint']})")
    lines.append("+-- [ Continue ]")
    return "\n".join(lines)
