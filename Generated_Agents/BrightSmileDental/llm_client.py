"""Multi-tier LLM client. Generic — do not edit per domain.

The pipeline chains three model roles (see graph.py):
  * INTENT — cheap/fast classification (intent detection + slot extraction)
  * ANSWER — the reasoning tier (direct answers + Think→Act decisions)
  * ENRICH — small tier (SLM) that rewrites a terse tool result into warm prose

Each role is a separate env var so you can point them at different models
(small for INTENT/ENRICH, large for ANSWER) without code changes. They may all
point at the same model; the ARCHITECTURE (separate roles) is the point.

Any OpenAI-compatible endpoint works via OPENAI_BASE_URL (Mistral, OpenAI,
Ollama, Groq...). With no key the client is in MOCK mode and the nodes use
their own deterministic fallbacks so the agent runs with zero credentials.

A stronger AGENT_ANSWER_MODEL increases FIDELITY to what prompts.py/config.py
actually say — never what's true. It cannot pitch, ground an answer, or know
the call is outbound if nothing tells it so; a bigger model just executes the
same content gap more fluently and confidently (for a hallucination, that
reads as MORE convincing, not less). Before escalating a model tier to fix a
bad live call, confirm the desired behavior is scripted somewhere in
prompts.py/config.py at all — see skill_steps/step4_build.md's triage rule.
"""

import asyncio
import contextvars
import json
import os
import re
import time
from typing import Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel

try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:
    pass

T = TypeVar("T", bound=BaseModel)

_DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
INTENT_MODEL = os.getenv("AGENT_INTENT_MODEL", _DEFAULT_MODEL)
ANSWER_MODEL = os.getenv("AGENT_ANSWER_MODEL", _DEFAULT_MODEL)
ENRICH_MODEL = os.getenv("AGENT_ENRICH_MODEL", _DEFAULT_MODEL)

try:
    from openai import AsyncOpenAI

    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False


# Per-node record of live model calls. graph._traced opens a fresh list for
# each node run (open_call_log) and puts it on that node's trace entry, so a
# call that failed and left the node on its heuristic fallback is visible in
# the trace, not only in a log line. One record per generate_* call: kind,
# path actually used (parse / json_mode / text), ok, error type and message
# (truncated; a provider 400 names the field it rejected), token usage
# (None when the provider sent none, or the attempt raised before a response),
# input size in characters, and latency. A call made outside any traced node
# (no open log) is not recorded. Mock mode makes no calls, so it records
# nothing and traces are unchanged.
_ERROR_MESSAGE_CHARS = 300
_CALL_LOG: contextvars.ContextVar[Optional[list]] = contextvars.ContextVar("llm_call_log", default=None)


def open_call_log() -> tuple[list, contextvars.Token]:
    calls: list = []
    return calls, _CALL_LOG.set(calls)


def close_call_log(token: contextvars.Token) -> None:
    _CALL_LOG.reset(token)


def _record(model: str, kind: str, path: str, messages: List[Dict[str, str]], started: float,
            completion=None, error: Optional[BaseException] = None, **extra) -> None:
    calls = _CALL_LOG.get()
    if calls is None:
        return
    usage = getattr(completion, "usage", None)
    calls.append({
        "model": model, "kind": kind, "path": path, "ok": error is None,
        "error": type(error).__name__ if error is not None else None,
        "error_message": str(error)[:_ERROR_MESSAGE_CHARS] if error is not None else None,
        "input_tokens": getattr(usage, "prompt_tokens", None),
        "output_tokens": getattr(usage, "completion_tokens", None),
        "input_chars": sum(len(m.get("content") or "") for m in messages),
        "latency_ms": round((time.perf_counter() - started) * 1000, 1),
        **extra,
    })


# Name of the request field that caps output tokens. Older OpenAI-compatible
# endpoints take `max_tokens`; some current models reject it and require
# `max_completion_tokens` (400 "Unsupported parameter: 'max_tokens'…"). Which
# one is a property of the endpoint, so it is configuration (OPENAI_TOKEN_PARAM
# in .env), never a branch on the provider. Anything else fails at startup.
_TOKEN_PARAMS = ("max_tokens", "max_completion_tokens")

# Optional reasoning effort (OPENAI_REASONING_EFFORT, e.g. none / low / medium).
# Some models reason by default, and hidden reasoning tokens count against the
# output cap, so the engine's small caps (5, 40, 300, 400) can be used up before
# any answer appears. Sent ONLY when set, so an endpoint that does not know the
# field never receives it. The accepted words differ per provider, so only the
# format is checked here; the endpoint rejects a word it does not know and the
# trace records that rejection.
_EFFORT_RE = re.compile(r"^[a-z][a-z0-9_-]*$")


class LLMClient:
    HARD_TIMEOUT_SECONDS = 30.0
    token_param = "max_tokens"
    reasoning_effort = ""

    def _cap(self, max_tokens: int) -> Dict[str, object]:
        """Output cap (and reasoning effort, when configured) as request fields."""
        fields: Dict[str, object] = {self.token_param: max_tokens}
        if self.reasoning_effort:
            fields["reasoning_effort"] = self.reasoning_effort
        return fields

    def __init__(self):
        self.token_param = os.getenv("OPENAI_TOKEN_PARAM", "").strip() or "max_tokens"
        if self.token_param not in _TOKEN_PARAMS:
            raise ValueError(f"OPENAI_TOKEN_PARAM must be one of {_TOKEN_PARAMS}, got {self.token_param!r}")
        self.reasoning_effort = os.getenv("OPENAI_REASONING_EFFORT", "").strip()
        if self.reasoning_effort and not _EFFORT_RE.match(self.reasoning_effort):
            raise ValueError(f"OPENAI_REASONING_EFFORT must be a plain word (e.g. none, low), got {self.reasoning_effort!r}")
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.base_url = os.getenv("OPENAI_BASE_URL", "").strip() or None
        if self.base_url and not self.api_key:
            self.api_key = "local"
        self.mock = not (self.api_key and _OPENAI_AVAILABLE)
        # base_url is ALWAYS passed explicitly: with base_url=None the openai
        # SDK re-reads the OPENAI_BASE_URL env var itself, and an empty-but-set
        # value ("OPENAI_BASE_URL=" in .env) becomes a protocol-less URL that
        # fails every call with APIConnectionError(UnsupportedProtocol).
        self.client = None if self.mock else AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url or "https://api.openai.com/v1",
        )

    @property
    def mode(self) -> str:
        return "MOCK (no OPENAI_API_KEY)" if self.mock else f"LIVE ({self.base_url or 'OpenAI'})"

    async def generate_structured(
        self, model: str, response_format: Type[T], messages: List[Dict[str, str]],
        temperature: float = 0.3, max_tokens: int = 400,
    ) -> T:
        """Model -> validated Pydantic object. Prefers native structured outputs,
        falls back to JSON-mode + local validation (needed for most Mistral models)."""
        if self.mock:
            raise RuntimeError("generate_structured called in MOCK mode — nodes must use their mock fallback")
        loop = asyncio.get_running_loop()
        deadline = loop.time() + self.HARD_TIMEOUT_SECONDS
        started = time.perf_counter()
        try:
            completion = await asyncio.wait_for(
                self.client.beta.chat.completions.parse(
                    model=model, messages=messages, response_format=response_format,
                    temperature=temperature, **self._cap(max_tokens),
                ),
                timeout=self.HARD_TIMEOUT_SECONDS,
            )
            _record(model, "structured", "parse", messages, started, completion)
            return completion.choices[0].message.parsed
        except asyncio.TimeoutError as e:
            # A slow/unresponsive endpoint already burned the whole budget —
            # retrying against the same endpoint would just double the dead
            # air the caller (runtime.py's turn ceiling) is sized against.
            # Propagate immediately instead of stacking a second full timeout.
            _record(model, "structured", "parse", messages, started, error=e)
            raise
        except Exception as parse_error:
            remaining = max(deadline - loop.time(), 0.0)
            if remaining <= 0:
                _record(model, "structured", "parse", messages, started, error=parse_error)
                raise
            try:
                result, completion = await self._structured_via_json_mode(
                    model, response_format, messages, temperature, max_tokens, timeout=remaining)
            except Exception as e:
                _record(model, "structured", "json_mode", messages, started, error=e,
                        parse_error=type(parse_error).__name__,
                        parse_error_message=str(parse_error)[:_ERROR_MESSAGE_CHARS])
                raise
            _record(model, "structured", "json_mode", messages, started, completion,
                    parse_error=type(parse_error).__name__,
                    parse_error_message=str(parse_error)[:_ERROR_MESSAGE_CHARS])
            return result

    async def _structured_via_json_mode(
        self,
        model: str,
        response_format: Type[BaseModel],
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        timeout: float | None = None,
    ) -> tuple[BaseModel, object]:
        """Structured output for endpoints without the OpenAI ``.beta.parse`` path.

        This is the provider-agnostic fallback: ``.beta.chat.completions.parse``
        is an OpenAI-SDK extension, not part of the OpenAI-COMPATIBLE wire
        protocol, so any other backend (Mistral, Ollama, vLLM, Groq) lands here.
        It asks for ``response_format={"type": "json_object"}``, appends the
        JSON Schema as a system instruction, and regex-extracts the outermost
        object before validating -- models in JSON mode still wrap output in
        prose or code fences often enough that parsing the raw string is unsafe.

        ``timeout`` carries the REMAINING budget from the caller, so a failed
        primary attempt plus this fallback cannot stack two full timeouts.

        Returns ``(validated object, raw completion)``; the completion carries
        the token usage the caller records. Raises ``pydantic.ValidationError``
        if the payload does not match ``response_format``, and
        ``asyncio.TimeoutError`` on budget exhaustion.
        """
        schema_hint = json.dumps(response_format.model_json_schema(), ensure_ascii=False)
        patched = list(messages) + [{
            "role": "system",
            "content": f"Respond with ONLY a valid JSON object matching this schema (no prose, no markdown): {schema_hint}",
        }]
        completion = await asyncio.wait_for(
            self.client.chat.completions.create(
                model=model, messages=patched, temperature=temperature,
                response_format={"type": "json_object"}, **self._cap(max_tokens),
            ),
            timeout=timeout if timeout is not None else self.HARD_TIMEOUT_SECONDS,
        )
        raw = completion.choices[0].message.content or "{}"
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        return response_format.model_validate_json(match.group(0) if match else raw), completion

    async def generate_text(
        self, model: str, messages: List[Dict[str, str]],
        temperature: float = 0.5, max_tokens: int = 300,
    ) -> str:
        """Model -> plain text. Used by the ANSWER and ENRICH tiers."""
        if self.mock:
            raise RuntimeError("generate_text called in MOCK mode — nodes must use their mock fallback")
        started = time.perf_counter()
        try:
            completion = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=model, messages=messages, temperature=temperature,
                    **self._cap(max_tokens),
                ),
                timeout=self.HARD_TIMEOUT_SECONDS,
            )
        except Exception as e:
            _record(model, "text", "text", messages, started, error=e)
            raise
        _record(model, "text", "text", messages, started, completion)
        return (completion.choices[0].message.content or "").strip()


llm_client = LLMClient()
