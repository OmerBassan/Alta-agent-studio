"""Turn-runner regression tests: the producer-consumer sentinel contract.

The property under test (tip_from_gemini.md / plan Day 1 PM): a crashed,
hanging, or cancelled graph must NEVER leave the SSE consumer blocked on
queue.get() — the caller always receives spoken text and the stream ends.
Uses a stub filler module + fake graphs so no generated project is loaded.
"""

import asyncio
import contextvars
import os
import sys
import uuid

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import runtime  # noqa: E402
from runtime import (  # noqa: E402
    AgentRuntime,
    VapiTurn,
    extract_lead_facts,
    parse_vapi_request,
)

TURN_RESET = {"intent": "", "final_response": ""}


class StubFiller:
    """Same contract as the engine's filler module: contextvar sink."""

    def __init__(self):
        self.var = contextvars.ContextVar("test_sink", default=None)

    def set_sink(self, sink):
        return self.var.set(sink)

    def reset_sink(self, token):
        self.var.reset(token)


class FakeGraph:
    def __init__(self, stub, final=None, exc=None, hang=False, fillers=()):
        self.stub, self.final, self.exc, self.hang, self.fillers = (
            stub, final or {}, exc, hang, fillers)

    async def ainvoke(self, payload, config):
        sink = self.stub.var.get()
        for text in self.fillers:
            sink.put_nowait({"type": "filler", "kind": "tool", "text": text})
        if self.hang:
            await asyncio.Event().wait()  # never returns
        if self.exc:
            raise self.exc
        return self.final


def _rt(graph, stub):
    return AgentRuntime(graph=graph, filler_mod=stub, turn_reset=TURN_RESET,
                        make_user_message=lambda t: {"content": t})


def _turn(text="hello", thread=None):
    return VapiTurn(thread_id=thread or uuid.uuid4().hex, user_text=text,
                    messages=[], stream=True, system_prompt=None)


async def _collect(rt, turn):
    return [seg async for seg in rt.stream_turn(turn)]


def test_happy_path_fillers_then_sanitized_sentences(monkeypatch):
    monkeypatch.setenv("PRETHINK_FILLER", "0")  # exact-segment assertions below
    stub = StubFiller()
    graph = FakeGraph(stub, fillers=["Let me check that…"],
                      final={"final_response": "**Great!** Booked for Monday. Anything else?"})
    segs = asyncio.run(_collect(_rt(graph, stub), _turn()))
    assert segs[0] == "Let me check that… "
    assert segs[1:] == ["Great! ", "Booked for Monday. ", "Anything else? "]


def test_prethink_token_is_first_and_immediate():
    """The turn acknowledgment must be the FIRST segment, drawn from the bank,
    and must precede everything the graph produces — it exists to cover the
    silent INTENT->ANSWER window on non-tool turns."""
    stub = StubFiller()
    graph = FakeGraph(stub, fillers=["Let me check that…"],
                      final={"final_response": "Sure."})
    segs = asyncio.run(_collect(_rt(graph, stub), _turn()))
    assert segs[0] in runtime.FILLER_THINKING
    assert segs[1] == "Let me check that… "
    assert segs[-1] == "Sure. "
    # Never on an empty-utterance re-ask…
    segs2 = asyncio.run(_collect(_rt(graph, stub), _turn(text="")))
    assert segs2 == [runtime.REASK]
    # …and never on a duplicate re-send (must stay silent, not double-speak).
    thread = uuid.uuid4().hex
    rt = _rt(graph, stub)
    asyncio.run(_collect(rt, _turn("same", thread)))
    assert asyncio.run(_collect(rt, _turn("same", thread))) == []


def test_agent_prethink_bank_is_preferred_over_platform_fallback():
    """A generated agent that declares config.FILLER_THINKING speaks ITS bank;
    the platform bank is only the fallback for agents without one."""
    stub = StubFiller()
    graph = FakeGraph(stub, final={"final_response": "Sure."})
    rt = AgentRuntime(graph=graph, filler_mod=stub, turn_reset=TURN_RESET,
                      make_user_message=lambda t: {"content": t},
                      filler_thinking=["Well now… "])
    segs = asyncio.run(_collect(rt, _turn()))
    assert segs[0] == "Well now… "


def test_crashed_graph_yields_apology_and_terminates(monkeypatch):
    monkeypatch.setenv("PRETHINK_FILLER", "0")
    stub = StubFiller()
    graph = FakeGraph(stub, exc=RuntimeError("LLM timeout"))
    segs = asyncio.run(asyncio.wait_for(_collect(_rt(graph, stub), _turn()), timeout=5))
    assert segs == [runtime.APOLOGY]  # spoken apology, no hang, no dead air


def test_hanging_graph_hits_ceiling_and_apologizes(monkeypatch):
    monkeypatch.setenv("RUNTIME_TURN_TIMEOUT_S", "0.2")
    monkeypatch.setenv("PRETHINK_FILLER", "0")
    stub = StubFiller()
    graph = FakeGraph(stub, hang=True)
    segs = asyncio.run(asyncio.wait_for(_collect(_rt(graph, stub), _turn()), timeout=5))
    assert segs == [runtime.APOLOGY]


def test_empty_user_text_is_reask_not_graph_call():
    stub = StubFiller()
    graph = FakeGraph(stub, exc=AssertionError("graph must not be invoked"))
    segs = asyncio.run(_collect(_rt(graph, stub), _turn(text="")))
    assert segs == [runtime.REASK]


def test_duplicate_resend_yields_nothing(monkeypatch):
    monkeypatch.setenv("PRETHINK_FILLER", "0")
    stub = StubFiller()
    graph = FakeGraph(stub, final={"final_response": "Sure."})
    rt = _rt(graph, stub)
    thread = uuid.uuid4().hex
    first = asyncio.run(_collect(rt, _turn("same text", thread)))
    second = asyncio.run(_collect(rt, _turn("same text", thread)))
    assert first == ["Sure. "]
    assert second == []  # corrected-transcript double-fire is idempotent


def test_hitl_interrupt_becomes_spoken_followup():
    stub = StubFiller()
    graph = FakeGraph(stub, final={"__interrupt__": [object()], "final_response": ""})
    segs = asyncio.run(_collect(_rt(graph, stub), _turn()))
    assert any("approval" in s for s in segs)


def test_parse_vapi_request_ground_truth():
    body = {
        "call": {"id": "019f6542-1f8e-722c-91ad-ccc34f8b33eb"},
        "stream": True,
        "messages": [
            {"role": "system", "content": "You are Alta."},
            {"role": "assistant", "content": "Hi."},
            {"role": "user", "content": "Yo. What's up?"},
        ],
    }
    t = parse_vapi_request(body)
    assert t.thread_id == "019f6542-1f8e-722c-91ad-ccc34f8b33eb"
    assert t.user_text == "Yo. What's up?"
    assert t.system_prompt == "You are Alta."


def test_malformed_body_is_noop_turn():
    t = parse_vapi_request({"messages": "garbage", "call": None})
    assert t.thread_id == "default_session"
    assert t.user_text == ""


def test_extract_lead_facts_from_call_metadata():
    body = {"call": {"id": "c1", "metadata": {"lead_name": "Dana", "company": "Acme"}}}
    assert extract_lead_facts(body) == {"lead_name": "Dana", "company": "Acme"}
    # and it rides through parse into the turn
    assert parse_vapi_request(body).lead_facts == {"lead_name": "Dana", "company": "Acme"}


def test_extract_lead_facts_prefers_variable_values_and_coerces_scalars():
    body = {"call": {"id": "c1", "assistantOverrides": {"variableValues": {
        "seats": 12, "vip": True, "notes": ["nested"], "obj": {"x": 1}}}}}
    # scalars coerced to str; nested list/dict dropped (untrusted boundary)
    assert extract_lead_facts(body) == {"seats": "12", "vip": "True"}


def test_extract_lead_facts_absent_is_empty():
    # a plain web test call carries no lead metadata -> injection is a no-op
    assert extract_lead_facts({"call": {"id": "c1"}, "messages": []}) == {}


@pytest.mark.skipif(not os.path.isdir(runtime.DEFAULT_AGENT_DIR),
                    reason="generated agent project not present")
def test_real_agent_loads_and_answers_in_mock_mode(monkeypatch):
    """Integration: load the actual NorthwindSDR project (zero-key MOCK mode)
    and run one real turn through the compiled graph."""
    monkeypatch.setenv("OPENAI_API_KEY", "")   # force MOCK before agent import
    monkeypatch.setenv("OPENAI_BASE_URL", "")
    monkeypatch.setenv("MEMORY_ENABLED", "0")  # no journal writes from tests
    rt = AgentRuntime.load()
    segs = asyncio.run(asyncio.wait_for(_collect(rt, _turn("what do you do?")), timeout=30))
    assert segs and all(isinstance(s, str) and s for s in segs)
    joined = " ".join(segs)
    assert "*" not in joined and "#" not in joined  # sanitizer applied
