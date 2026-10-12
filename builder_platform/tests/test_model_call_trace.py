"""Every live model call is recorded on the trace of the node that made it.

Bug this guards against: when a model call failed (timeout, rejected
parameter, invalid JSON), the node fell back to the same keyword heuristic
mock mode uses and only logged a warning. The trace carried no sign of it, so
a live evaluation whose every call failed was indistinguishable from mock
behaviour that passes. Now each call leaves a `model_calls` record (path, ok,
error type, token usage, latency) on its node's trace entry, and the entry is
flagged `degraded` when any call on it failed.

Proven against boilerplate/ in-process with a fake OpenAI client: no network,
no tokens. Mock mode must leave traces exactly as they were (no model_calls).
"""

import asyncio
import os
import sys
import types
from pathlib import Path

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_BASE_URL"] = ""

BOILERPLATE_DIR = Path(__file__).resolve().parents[2] / "boilerplate"
sys.path.insert(0, str(BOILERPLATE_DIR))

from graph import TURN_RESET, build_pipeline  # noqa: E402
from langchain_core.messages import HumanMessage  # noqa: E402
from langgraph.checkpoint.memory import MemorySaver  # noqa: E402
from llm_client import llm_client  # noqa: E402
from schemas import IntentResult  # noqa: E402


def _usage(i, o):
    return types.SimpleNamespace(prompt_tokens=i, completion_tokens=o)


class _Parse:
    def __init__(self, fail, intent="chitchat"):
        self.fail, self.intent = fail, intent

    async def parse(self, *, response_format, **_kw):
        if self.fail or response_format is not IntentResult:
            raise RuntimeError("model rejected the request")
        msg = types.SimpleNamespace(parsed=IntentResult(intent=self.intent, category="ANSWER"))
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)], usage=_usage(120, 15))


class _Create:
    def __init__(self, fail):
        self.fail = fail

    async def create(self, *, response_format=None, **_kw):
        if self.fail or response_format is not None:   # JSON-mode fallback fails too
            raise RuntimeError("model rejected the request")
        msg = types.SimpleNamespace(content="Hello, how can I help you today?")
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)], usage=_usage(200, 9))


def _fake_client(fail, intent="chitchat"):
    return types.SimpleNamespace(
        beta=types.SimpleNamespace(chat=types.SimpleNamespace(completions=_Parse(fail, intent))),
        chat=types.SimpleNamespace(completions=_Create(fail)))


def _hello_trace(monkeypatch, fake, message="hello"):
    if fake is not None:
        monkeypatch.setattr(llm_client, "mock", False)
        monkeypatch.setattr(llm_client, "client", fake)

    async def run():
        graph = build_pipeline(MemorySaver())
        payload = dict(TURN_RESET, user_message=message,
                       recent_messages=[HumanMessage(content=message)])
        st = await graph.ainvoke(payload, config={"configurable": {"thread_id": "t-model-calls"}})
        return st["trace"]
    return {e["node"]: e for e in asyncio.run(run())}


def test_a_failed_model_call_is_visible_on_the_trace(monkeypatch):
    entries = _hello_trace(monkeypatch, _fake_client(fail=True))
    intent = entries["intent_detect"]
    calls = intent.get("model_calls")
    assert calls, "a failed intent call left no record: the heuristic fallback is invisible"
    assert calls[0]["ok"] is False and calls[0]["error"] == "RuntimeError"
    # The provider's message, not only the type: a 400 names the rejected field.
    assert calls[0]["error_message"] == "model rejected the request"
    assert calls[0]["parse_error_message"] == "model rejected the request"
    assert intent["degraded"] is True


def test_a_successful_model_call_records_path_usage_and_latency(monkeypatch):
    entries = _hello_trace(monkeypatch, _fake_client(fail=False))
    intent = entries["intent_detect"]
    assert intent["intent"] == "chitchat" and intent["degraded"] is False
    (call,) = intent["model_calls"]
    assert call["ok"] is True and call["kind"] == "structured" and call["path"] == "parse"
    assert call["input_tokens"] == 120 and call["output_tokens"] == 15
    assert call["latency_ms"] >= 0
    reply = entries["chitchat"]["model_calls"]
    assert [c["kind"] for c in reply] == ["text"] and reply[0]["output_tokens"] == 9


def test_calls_inside_the_rag_subgraph_land_on_the_retrieval_entry(monkeypatch):
    # The subgraph runs in tasks of its own; its calls must still reach the
    # log the agentic_retrieval node opened (context propagation, not luck).
    entries = _hello_trace(monkeypatch, _fake_client(fail=False, intent="faq_policy"),
                           message="what is your warranty policy?")
    rag = entries["agentic_retrieval"].get("model_calls")
    assert rag, "model calls made inside the RAG subgraph were not recorded"
    assert all(c["kind"] == "text" for c in rag)


def test_mock_mode_traces_carry_no_model_calls(monkeypatch):
    entries = _hello_trace(monkeypatch, None)
    assert all("model_calls" not in e and "degraded" not in e for e in entries.values())
