# -*- coding: utf-8 -*-
"""Drive ONE generated agent through scripted conversations, in its own process.

Agents cannot share a process: every agent's modules are named config, nodes,
tools… (the module-name collision trap the runtime avoids with
subprocess-per-agent). Tests therefore call run_agent(), which starts this file
as `python agent_driver.py <agent_dir>`, feeds a JSON request on stdin and
reads one JSON document back. MOCK mode by default: the key is blanked before
any agent module is imported, so no tokens are spent. run_agent(live=True) is
the one opt-in exception (live_eval.py uses it): the caller's OPENAI_* and
AGENT_*_MODEL environment passes through, the driver refuses to start if the
client still comes up in mock mode, and a "budget" stops the run before the
next turn once the estimated spend reaches it (overshoot: at most one turn).

Request:
  {"conversations": [[step, ...], ...],      # each on a fresh thread
   "validator_drafts": ["text", ...],         # optional: run the exit filter
   "budget": {"max_cost_usd": 0.25,           # live only, optional
              "price_in_per_m": 0.10, "price_out_per_m": 0.50}}
  step = "message"
       | {"message": "...", "inject": {...state...}, "env": {"NAME": "value"}}
       | {"resume": {"approved": bool}}   # operator decision on the open interrupt;
                                          # the driver echoes the offer_id it showed
Response:
  {"conversations": [[turn, ...], ...], "validator": ["filtered", ...],
   "tool_registry": [...], "verifiers": [...], "llm_mode": "MOCK…" | "LIVE (…)",
   "config_sha256": "…", "spend": {...}}
  A conversation cut short by the budget has fewer turns than steps, and
  spend["stopped"] is true.
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


# Spend estimate for a model call the provider reported no usage for (it
# raised before responding, or the parse attempt that preceded a JSON-mode
# retry): input from its size at a pessimistic 3 characters per token, output
# at the largest max_tokens any call site uses. Over-counting stops a run
# early; under-counting could break the ceiling.
_CHARS_PER_TOKEN_FLOOR = 3
_MAX_OUTPUT_TOKENS = 400


def turn_spend(trace: list, price_in_per_m: float, price_out_per_m: float) -> dict:
    """Tokens and estimated cost of the model calls recorded on one turn's trace."""
    tin = tout = estimated = 0
    for entry in trace:
        for c in entry.get("model_calls") or ():
            reported = c.get("input_tokens") is not None and c.get("output_tokens") is not None
            if reported:
                tin += c["input_tokens"]
                tout += c["output_tokens"]
            else:
                estimated += 1
                tin += -(-c.get("input_chars", 0) // _CHARS_PER_TOKEN_FLOOR)
                tout += _MAX_OUTPUT_TOKENS
            if c.get("parse_error"):   # the failed parse attempt before a JSON-mode retry
                estimated += 1
                tin += -(-c.get("input_chars", 0) // _CHARS_PER_TOKEN_FLOOR)
                tout += _MAX_OUTPUT_TOKENS
    cost = (tin * price_in_per_m + tout * price_out_per_m) / 1_000_000
    return {"input_tokens": tin, "output_tokens": tout, "estimated_calls": estimated, "cost_usd": cost}


def run_agent(agent_dir: Path, request: dict, timeout: float = 120, live: bool = False) -> dict:
    """Run a request against `agent_dir` in a fresh interpreter; return the reply.

    live=False (the default, and what every pytest test uses) blanks the key.
    live=True passes the caller's environment through and refuses to start
    without OPENAI_API_KEY, so a missing key can never silently become mock.
    """
    if live:
        if not os.environ.get("OPENAI_API_KEY", "").strip():
            raise RuntimeError("live run requested but OPENAI_API_KEY is not set")
        env = dict(os.environ)
    else:
        env = {**os.environ, "OPENAI_API_KEY": "", "OPENAI_BASE_URL": ""}
    argv = [sys.executable, str(Path(__file__).resolve()), str(agent_dir)] + (["--live"] if live else [])
    proc = subprocess.run(argv, input=json.dumps(request), capture_output=True, text=True,
                          encoding="utf-8", timeout=timeout, env=env)
    if proc.returncode != 0:
        raise RuntimeError(f"agent driver failed ({proc.returncode}):\n{proc.stderr[-4000:]}")
    return json.loads(proc.stdout.strip().splitlines()[-1])


def _main(agent_dir: str, live: bool) -> None:
    if not live:
        os.environ["OPENAI_API_KEY"] = ""
        os.environ["OPENAI_BASE_URL"] = ""
    sys.path.insert(0, agent_dir)
    import logging
    logging.disable(logging.CRITICAL)

    import config
    import nodes
    import tools
    from episode_trace import config_fingerprint
    from graph import TURN_RESET, build_pipeline
    from langchain_core.messages import HumanMessage
    from langgraph.types import Command
    from llm_client import llm_client

    if llm_client.mock == live:
        sys.exit(f"agent driver: requested {'LIVE' if live else 'MOCK'} but the client is {llm_client.mode}")

    request = json.loads(sys.stdin.read())
    budget = request.get("budget") if live else None
    spend = {"input_tokens": 0, "output_tokens": 0, "estimated_calls": 0, "cost_usd": 0.0,
             "stopped": False}
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
            if budget and spend["cost_usd"] >= budget["max_cost_usd"]:
                spend["stopped"] = True
                break
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
            if budget:
                used = turn_spend(st.get("trace") or [], budget["price_in_per_m"], budget["price_out_per_m"])
                for k in ("input_tokens", "output_tokens", "estimated_calls", "cost_usd"):
                    spend[k] += used[k]
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
                "verifiers": sorted(getattr(tools, "VERIFIERS", {})),
                "llm_mode": llm_client.mode,
                "config_sha256": config_fingerprint(Path(agent_dir), config)["config_sha256"],
                "spend": spend}

    print(json.dumps(asyncio.run(run()), default=str))


if __name__ == "__main__":
    _main(sys.argv[1], live="--live" in sys.argv[2:])
