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
