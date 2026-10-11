# -*- coding: utf-8 -*-
"""Drive ONE generated agent through scripted conversations, in its own process.

Agents cannot share a process: every agent's modules are named config, nodes,
tools… (the module-name collision trap the runtime avoids with
subprocess-per-agent). Tests therefore call run_agent(), which starts this file
as `python agent_driver.py <agent_dir>`, feeds a JSON request on stdin and
reads one JSON document back. Always MOCK mode: the key is blanked before any
agent module is imported, so no tokens are ever spent.

Request:
  {"conversations": [[step, ...], ...],      # each on a fresh thread
   "validator_drafts": ["text", ...]}         # optional: run the exit filter
  step = "message"
       | {"message": "...", "inject": {...state...}, "env": {"NAME": "value"}}
       | {"resume": {"approved": bool}}   # operator decision on the open interrupt;
                                          # the driver echoes the offer_id it showed
Response:
  {"conversations": [[turn, ...], ...], "validator": ["filtered", ...],
   "tool_registry": [...], "verifiers": [...]}
  turn = {"message", "final_response", "trace", "handoff_requested",
          "pending_confirmation", "pending_intent", "session_facts",
          "tool_calls": [[tool, args], ...], "interrupted", "interrupt"}
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path


def run_agent(agent_dir: Path, request: dict, timeout: float = 120) -> dict:
    """Run a request against `agent_dir` in a fresh interpreter; return the reply."""
    env = {**os.environ, "OPENAI_API_KEY": "", "OPENAI_BASE_URL": ""}
    proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), str(agent_dir)],
                          input=json.dumps(request), capture_output=True, text=True,
                          encoding="utf-8", timeout=timeout, env=env)
    if proc.returncode != 0:
        raise RuntimeError(f"agent driver failed ({proc.returncode}):\n{proc.stderr[-4000:]}")
    return json.loads(proc.stdout.strip().splitlines()[-1])


def _main(agent_dir: str) -> None:
    os.environ["OPENAI_API_KEY"] = ""
    os.environ["OPENAI_BASE_URL"] = ""
    sys.path.insert(0, agent_dir)
    import logging
    logging.disable(logging.CRITICAL)

    import nodes
    import tools
    from graph import TURN_RESET, build_pipeline
    from langchain_core.messages import HumanMessage
    from langgraph.types import Command

    request = json.loads(sys.stdin.read())
    calls: list = []
    for name, fn in list(tools.TOOL_REGISTRY.items()):
        def recorder(*a, _fn=fn, _name=name, **kw):
            calls.append([_name, kw])
            return _fn(*a, **kw)
        tools.TOOL_REGISTRY[name] = recorder

    async def converse(graph, thread: str, steps: list) -> list:
        cfg = {"configurable": {"thread_id": thread}}
        out = []
        for step in steps:
            step = {"message": step} if isinstance(step, str) else step
            for k, v in (step.get("env") or {}).items():
                os.environ[k] = v
            before = len(calls)
            if "resume" in step:
                snap = await graph.aget_state(cfg)
                offer = snap.interrupts[0].value.get("offer_id") if snap.interrupts else None
                decision = {**step["resume"], "offer_id": offer}
                st = await graph.ainvoke(Command(resume=decision), config=cfg)
                label = f"<operator {'approves' if decision.get('approved') else 'denies'}>"
            else:
                payload = dict(TURN_RESET)
                payload["user_message"] = step["message"]
                payload["recent_messages"] = [HumanMessage(content=step["message"])]
                payload.update(step.get("inject") or {})
                st = await graph.ainvoke(payload, config=cfg)
                label = step["message"]
            pause = st.get("__interrupt__") or []
            out.append({
                "message": label,
                "final_response": st.get("final_response", ""),
                "trace": st.get("trace") or [],
                "handoff_requested": bool(st.get("handoff_requested")),
                "pending_confirmation": st.get("pending_confirmation") or {},
                "pending_intent": st.get("pending_intent"),
                "session_facts": st.get("session_facts") or {},
                "tool_calls": calls[before:],
                "interrupted": bool(pause),
                "interrupt": pause[0].value if pause else None,
            })
        return out

    async def run() -> dict:
        graph = build_pipeline()
        convs = []
        for i, steps in enumerate(request.get("conversations") or []):
            tools.BACKEND.reset() if hasattr(tools, "BACKEND") else None
            os.environ.pop("SIMULATED_FAILURE", None)
            convs.append(await converse(graph, f"driver-{i}", steps))
        filtered = [nodes.validator_node({"draft_response": d})["final_response"]
                    for d in request.get("validator_drafts") or []]
        return {"conversations": convs, "validator": filtered,
                "tool_registry": sorted(tools.TOOL_REGISTRY),
                "verifiers": sorted(getattr(tools, "VERIFIERS", {}))}

    print(json.dumps(asyncio.run(run()), default=str))


if __name__ == "__main__":
    _main(sys.argv[1])
