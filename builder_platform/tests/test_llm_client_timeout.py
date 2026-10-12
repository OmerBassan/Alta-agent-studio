"""Regression test: generate_structured must not stack two independent hard
timeouts on a single call.

Bug: on a hung/slow endpoint, the primary structured-output attempt timed out
after HARD_TIMEOUT_SECONDS, but the `except Exception` handler caught the
timeout too and retried via _structured_via_json_mode with its OWN fresh
HARD_TIMEOUT_SECONDS window — up to 2x the documented cap on a single call.
runtime.py's RUNTIME_TURN_TIMEOUT_S (45s default) is sized on the documented
assumption of "the graph's own 30s LLM hard timeout" (see its module
docstring); the doubled worst case silently violated that budget and is what
produced multi-second-to-a-minute dead air on a live voice call
(Voice_SDR_Reliability.txt rule 8: every failure path must terminate in
speech within the budget the runtime promises).
"""

import asyncio
import os
import sys
import types

import pytest
from pydantic import BaseModel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "boilerplate"))

import llm_client as llm_client_mod  # noqa: E402


class _Result(BaseModel):
    value: str = "ok"


class _SlowParse:
    """Simulates a hung endpoint: sleeps well past the client's timeout."""

    async def parse(self, **_kwargs):
        await asyncio.sleep(5)


class _FailFastParse:
    """Simulates a legitimate fallback trigger: the endpoint rejects
    structured outputs outright (not a timeout) — e.g. most Mistral models."""

    async def parse(self, **_kwargs):
        raise RuntimeError("structured outputs not supported")


class _FakeMessage:
    content = '{"value": "ok"}'


class _FakeChoice:
    message = _FakeMessage()


class _FakeCompletion:
    choices = [_FakeChoice()]


class _FakeChatCompletions:
    def __init__(self, called_flag):
        self._called_flag = called_flag

    async def create(self, **_kwargs):
        self._called_flag["json_mode_called"] = True
        return _FakeCompletion()


def _make_fake_client(parse_impl, called_flag):
    client = types.SimpleNamespace()
    client.beta = types.SimpleNamespace(chat=types.SimpleNamespace(completions=parse_impl))
    client.chat = types.SimpleNamespace(completions=_FakeChatCompletions(called_flag))
    return client


def _new_client(parse_impl, called_flag, hard_timeout):
    client = llm_client_mod.LLMClient.__new__(llm_client_mod.LLMClient)
    client.mock = False
    client.HARD_TIMEOUT_SECONDS = hard_timeout
    client.client = _make_fake_client(parse_impl, called_flag)
    return client


def test_timeout_does_not_stack_a_second_full_timeout():
    called = {"json_mode_called": False}
    client = _new_client(_SlowParse(), called, hard_timeout=0.1)

    async def _run():
        start = asyncio.get_running_loop().time()
        with pytest.raises(asyncio.TimeoutError):
            await client.generate_structured("m", _Result, [{"role": "user", "content": "hi"}])
        return asyncio.get_running_loop().time() - start

    elapsed = asyncio.run(_run())
    assert elapsed < 0.3, f"took {elapsed:.2f}s — a second full timeout stacked on top of the first"
    assert called["json_mode_called"] is False, "must not retry a request that already timed out"


def test_non_timeout_failure_still_falls_back_within_remaining_budget():
    called = {"json_mode_called": False}
    client = _new_client(_FailFastParse(), called, hard_timeout=1.0)

    result = asyncio.run(
        client.generate_structured("m", _Result, [{"role": "user", "content": "hi"}])
    )
    assert result.value == "ok"
    assert called["json_mode_called"] is True


# --- token-limit parameter name -------------------------------------------
# Bug (live probe, gpt-6-luna, 2026-10-12): the client always sent the legacy
# `max_tokens`; the model answered 400 "Unsupported parameter: 'max_tokens' is
# not supported with this model. Use 'max_completion_tokens' instead." on every
# call, so every node fell back to its heuristic. The field name is now an
# env setting (OPENAI_TOKEN_PARAM), default unchanged.

class _Capture:
    def __init__(self):
        self.kwargs = []

    async def parse(self, **kw):
        self.kwargs.append(kw)
        raise RuntimeError("force the JSON-mode path too")

    async def create(self, **kw):
        self.kwargs.append(kw)
        msg = types.SimpleNamespace(content='{"value": "ok"}')
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)], usage=None)


def _capturing_client(token_param=None):
    cap = _Capture()
    client = llm_client_mod.LLMClient.__new__(llm_client_mod.LLMClient)
    client.mock = False
    client.HARD_TIMEOUT_SECONDS = 5
    if token_param:
        client.token_param = token_param
    client.client = types.SimpleNamespace(
        beta=types.SimpleNamespace(chat=types.SimpleNamespace(completions=cap)),
        chat=types.SimpleNamespace(completions=cap))
    return client, cap


@pytest.mark.parametrize("token_param, other", [
    (None, "max_completion_tokens"),                 # default: legacy name, unchanged
    ("max_tokens", "max_completion_tokens"),
    ("max_completion_tokens", "max_tokens"),
])
def test_token_limit_is_sent_under_the_configured_name_on_every_path(token_param, other):
    client, cap = _capturing_client(token_param)
    want = token_param or "max_tokens"

    async def _run():
        await client.generate_structured("m", _Result, [{"role": "user", "content": "hi"}], max_tokens=77)
        await client.generate_text("m", [{"role": "user", "content": "hi"}], max_tokens=33)
    asyncio.run(_run())

    assert len(cap.kwargs) == 3          # parse, json-mode retry, text
    for kw, n in zip(cap.kwargs, (77, 77, 33)):
        assert kw[want] == n and other not in kw, kw


def test_unknown_token_param_fails_at_startup(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    monkeypatch.setenv("OPENAI_TOKEN_PARAM", "max_toknes")
    with pytest.raises(ValueError, match="OPENAI_TOKEN_PARAM"):
        llm_client_mod.LLMClient()


# --- reasoning effort -------------------------------------------------------
# Some current models reason by default (gpt-6-luna: "medium"); hidden
# reasoning tokens can use up the small output caps the engine sends (5, 40,
# 300, 400). OPENAI_REASONING_EFFORT sets the effort, sent ONLY when set, so
# an endpoint that does not know the field never receives it.

@pytest.mark.parametrize("effort, expect_sent", [(None, False), ("", False), ("none", True), ("low", True)])
def test_reasoning_effort_is_sent_only_when_configured(effort, expect_sent):
    client, cap = _capturing_client()
    if effort is not None:
        client.reasoning_effort = effort

    async def _run():
        await client.generate_structured("m", _Result, [{"role": "user", "content": "hi"}])
        await client.generate_text("m", [{"role": "user", "content": "hi"}])
    asyncio.run(_run())

    assert len(cap.kwargs) == 3
    for kw in cap.kwargs:
        assert ("reasoning_effort" in kw) is expect_sent, kw
        if expect_sent:
            assert kw["reasoning_effort"] == effort


def test_reasoning_effort_is_read_from_the_environment(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    monkeypatch.setenv("OPENAI_REASONING_EFFORT", " none ")
    assert llm_client_mod.LLMClient().reasoning_effort == "none"
    monkeypatch.delenv("OPENAI_REASONING_EFFORT")
    assert llm_client_mod.LLMClient().reasoning_effort == ""


def test_malformed_reasoning_effort_fails_at_startup(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    monkeypatch.setenv("OPENAI_REASONING_EFFORT", "none; drop")
    with pytest.raises(ValueError, match="OPENAI_REASONING_EFFORT"):
        llm_client_mod.LLMClient()
