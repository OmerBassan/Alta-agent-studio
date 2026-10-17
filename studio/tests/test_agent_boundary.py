"""The agent runtime boundary (AD-14): configuration, the provider-agnostic
model port, the live model agent and the credential-free agent.

The model endpoint is replaced by an in-process HTTP transport, so these tests
make no network call and cost nothing, yet exercise the real request and
response handling (anti-pattern: an untested boundary)."""

import asyncio
import json
from datetime import date

import httpx
import pytest

from studio.agent.deterministic import DeterministicAgent
from studio.agent.llm_agent import LLMAgent, render
from studio.agent.model_port import ModelError, ModelPort
from studio.config import ConfigurationError, Settings
from studio.core import Core, EpisodeStore, InboundMessage, SpecRegistry
from studio.extensions.simulated import SimulatedCalendar
from studio.spec import compile_specification, load_specification
from studio.tests.helpers import BUSINESSES

DENTAL = BUSINESSES / "dental" / "specification.toml"


# --- configuration (NFR17): validated at startup, never at first use ------------------

def test_no_credentials_means_credential_free_mode():
    assert Settings.from_env({}).live is False


def test_a_half_configured_endpoint_is_rejected_at_startup():
    with pytest.raises(ConfigurationError, match="STUDIO_AGENT_MODEL"):
        Settings.from_env({"OPENAI_API_KEY": "sk-test"})


@pytest.mark.parametrize("env,match", [
    ({"OPENAI_TOKEN_PARAM": "max_output"}, "OPENAI_TOKEN_PARAM"),
    ({"OPENAI_REASONING_EFFORT": "very high!"}, "OPENAI_REASONING_EFFORT"),
    ({"STUDIO_PRICE_IN": "cheap"}, "STUDIO_PRICE_IN"),
])
def test_invalid_model_settings_are_rejected_at_startup(env, match):
    with pytest.raises(ConfigurationError, match=match):
        Settings.from_env({"OPENAI_API_KEY": "sk", "STUDIO_AGENT_MODEL": "m", **env})


def test_a_local_endpoint_needs_no_key():
    s = Settings.from_env({"OPENAI_BASE_URL": "http://localhost:11434/v1/", "STUDIO_AGENT_MODEL": "llama"})
    assert s.live and s.model.base_url == "http://localhost:11434/v1" and s.model.api_key == "local"


# --- the model port: provider-agnostic wire protocol ---------------------------------------

def port_with(handler, **settings):
    s = Settings.from_env({"OPENAI_API_KEY": "sk-test", "STUDIO_AGENT_MODEL": "test-model", **settings}).model
    return ModelPort(s, httpx.AsyncClient(transport=httpx.MockTransport(handler)))


def completion(content: str, usage=None):
    return httpx.Response(200, json={"choices": [{"message": {"content": content}}],
                                     "usage": usage or {"prompt_tokens": 120, "completion_tokens": 30}})


def test_the_port_sends_a_plain_v1_request_configured_by_environment():
    seen = {}

    def handler(request: httpx.Request):
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        seen["auth"] = request.headers["authorization"]
        return completion('{"ok": true}')

    port = port_with(handler, OPENAI_TOKEN_PARAM="max_completion_tokens", OPENAI_REASONING_EFFORT="none")
    parsed, call = asyncio.run(port.complete_json([{"role": "user", "content": "hi"}]))
    assert parsed == {"ok": True}
    assert seen["url"] == "https://api.openai.com/v1/chat/completions" and seen["auth"] == "Bearer sk-test"
    assert seen["body"]["model"] == "test-model" and "max_completion_tokens" in seen["body"]
    assert seen["body"]["reasoning_effort"] == "none" and seen["body"]["response_format"] == {"type": "json_object"}
    assert call.ok and call.input_tokens == 120 and call.output_tokens == 30


@pytest.mark.parametrize("response,error", [
    (httpx.Response(400, text="Unsupported parameter: 'max_tokens'"), "HTTP 400"),
    (completion("I think you should book it."), "not_json"),
    (httpx.Response(200, json={"choices": []}), "no_content"),
])
def test_model_failures_are_typed_errors_with_a_call_record(response, error):
    port = port_with(lambda request: response)
    with pytest.raises(ModelError) as exc:
        asyncio.run(port.complete_json([{"role": "user", "content": "hi"}]))
    assert exc.value.call.ok is False and exc.value.call.error == error


# --- the live agent: model output is untrusted input -----------------------------------------

def core_with(agent):
    registry = SpecRegistry()
    registry.register(compile_specification(load_specification(DENTAL)))
    return Core(registry, EpisodeStore(), agent, {"calendar": SimulatedCalendar()})


def test_a_valid_model_request_reaches_the_core_and_its_call_is_recorded():
    reply = {"kind": "respond", "message": "We open at 8 on weekdays.", "claims": []}
    agent = LLMAgent(port_with(lambda request: completion(json.dumps(reply))))
    core = core_with(agent)
    out = asyncio.run(core.handle(InboundMessage(tenant="bright-smile-dental", conversation_key="c",
                                                 message_id="1", text="When do you open?")))
    assert "We open at 8" in out.messages[0].text
    calls = core.store.model_calls("bright-smile-dental", out.episode_id)
    assert len(calls) == 1 and calls[0]["input_tokens"] == 120


def test_an_invalid_model_request_is_a_typed_result_and_the_loop_stays_bounded():
    agent = LLMAgent(port_with(lambda request: completion('{"kind": "launch_rocket"}')))
    core = core_with(agent)
    out = asyncio.run(core.handle(InboundMessage(tenant="bright-smile-dental", conversation_key="c",
                                                 message_id="1", text="hello")))
    assert out.halted == "budget_exhausted"
    reasons = {d["reason"] for d in core.store.denials("bright-smile-dental")}
    assert reasons == {"agent_failed"}


def test_object_shaped_arguments_are_accepted_but_nothing_else_is_guessed():
    from studio.agent.llm_agent import _normalise
    out = _normalise({"kind": "read", "capability": "x", "arguments": {"a": 1}})
    assert out["arguments"] == [{"name": "a", "value": 1}]


def test_the_rendered_view_carries_references_constraints_and_the_request_guide():
    core = core_with(DeterministicAgent())
    captured = {}

    class Capture:
        name = "capture"

        async def decide(self, view):
            captured["messages"] = render(view)
            from studio.core.ports import AgentDecision
            from studio.core.types import RespondRequest
            return AgentDecision(request=RespondRequest(message="ok"))

    core.agent = Capture()
    asyncio.run(core.handle(InboundMessage(tenant="bright-smile-dental", conversation_key="c", message_id="1",
                                           text="I have severe pain")))
    system, user = captured["messages"][0]["content"], captured["messages"][1]["content"]
    assert "ref_" in system and "95 dollars" in system and "Reply with exactly ONE JSON object" in system
    assert "severe pain" in user.lower() and "FORBIDDEN" in system


def test_the_view_carries_the_recorded_date_so_a_live_agent_can_resolve_a_weekday():
    """Proof gate L1 (2026-10-17): the date reached the credential-free agent only from the CLI, so a live agent
    could not resolve "Monday". The view now carries the Core's recorded clock."""
    from datetime import datetime, timezone
    from studio.core.ports import AgentDecision
    from studio.core.types import RespondRequest
    registry = SpecRegistry()
    registry.register(compile_specification(load_specification(DENTAL)))
    clock = lambda: datetime(2026, 10, 13, 9, 0, tzinfo=timezone.utc)  # noqa: E731 - a Tuesday
    captured = {}

    class Capture:
        name = "capture"

        async def decide(self, view):
            captured["view"], captured["messages"] = view, render(view)
            return AgentDecision(request=RespondRequest(message="ok"))

    core = Core(registry, EpisodeStore(clock=clock), Capture(), {"calendar": SimulatedCalendar()})
    asyncio.run(core.handle(InboundMessage(tenant="bright-smile-dental", conversation_key="c", message_id="1",
                                           text="Can I come in on Monday?")))
    assert captured["view"].today == "2026-10-13"
    assert "Today is Tuesday 2026-10-13." in captured["messages"][1]["content"]


# --- the credential-free agent -----------------------------------------------------------------

def test_a_bare_yes_is_never_recorded_as_a_fact():
    agent = DeterministicAgent(today=lambda: date(2026, 10, 13))
    core = core_with(agent)

    def send(text, mid):
        return asyncio.run(core.handle(InboundMessage(tenant="bright-smile-dental", conversation_key="c",
                                                      message_id=mid, text=text)))

    send("I'd like a check-up on Monday at 9am", "1")
    send("yes", "2")
    episode = core.store.episodes("bright-smile-dental")[0]
    assert "yes" not in core.store.facts("bright-smile-dental", episode.episode_id).values()
