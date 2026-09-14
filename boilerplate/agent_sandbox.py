# -*- coding: utf-8 -*-
"""Text-chat sandbox: talk to this agent's LangGraph pipeline directly from a
terminal, with zero voice infrastructure (no Vapi, no tunnel, no browser).

Engine file — copied verbatim, never edited per agent (same rule as
graph.py/nodes.py/selftest.py; see ENGINE_FILES in builder_platform/builder_core.py).
Drives the SAME graph.ainvoke(...)/TURN_RESET contract runtime.py uses for a
live voice call and selftest.py's smoke_walk uses for its scripted turns —
this is just a third, interactive shell on top of that one contract ("every
Shell ... resets these at the start of a turn", per graph.py's own docstring).

Run:  python agent_sandbox.py        (from inside a generated project)
Exit: Ctrl+C, or type "quit"/"exit".
"""

from __future__ import annotations

import asyncio
import os

# Voice-runtime latency knobs, mirrored for behavioral parity with a real
# call: setdefault (never overrides an operator's explicit env) BEFORE the
# agent's own modules import, same ordering rule runtime.py follows.
os.environ.setdefault("FAST_ROUTER_ENABLED", "1")
os.environ.setdefault("RAG_MAX_ITERATIONS", "1")

import config  # noqa: E402
from graph import build_pipeline, TURN_RESET  # noqa: E402
from langchain_core.messages import HumanMessage  # noqa: E402
from langgraph.checkpoint.memory import MemorySaver  # noqa: E402

THREAD_ID = "sandbox"


async def _run_turn(graph, cfg: dict, user_text: str) -> str:
    payload = dict(TURN_RESET)
    payload["user_message"] = user_text
    payload["recent_messages"] = [HumanMessage(content=user_text)]
    state = await graph.ainvoke(payload, config=cfg)
    if state.get("__interrupt__"):
        # Matches runtime.py's own admission: no operator console exists to
        # resolve a HITL approval live, on a call OR here — same follow-up
        # line a real caller would hear.
        return ("That needs a quick approval from my team. We'll follow up "
                "with you shortly. Anything else?")
    return state.get("final_response", "") or "(empty reply)"


async def main() -> None:
    live = bool(os.environ.get("OPENAI_API_KEY", "").strip())
    print(f"--- {config.AGENT_NAME} — text sandbox ({'LIVE' if live else 'MOCK'} brain) ---")
    print("Type a message and press Enter. 'quit' or Ctrl+C to exit.\n")

    opener = getattr(config, "OPENER", "").strip()
    if opener:
        print(f"agent> {opener}")

    graph = build_pipeline(checkpointer=MemorySaver())
    cfg = {"configurable": {"thread_id": THREAD_ID}}

    while True:
        try:
            user_text = input("you> ").strip()
        except EOFError:
            break
        if not user_text:
            continue
        if user_text.lower() in ("quit", "exit"):
            break
        reply = await _run_turn(graph, cfg, user_text)
        print(f"agent> {reply}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
