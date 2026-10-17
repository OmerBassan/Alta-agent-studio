"""A provider-agnostic model port: the OpenAI-compatible ``/v1`` wire protocol
over one pooled HTTP client, configured only by environment.

No vendor SDK is imported (NFR12): the request is a plain
``POST {base_url}/chat/completions``, which every compatible endpoint accepts.
Structured output uses JSON mode plus local validation — the provider-agnostic
path — so the same code serves any backend. Each call is returned as a
``ModelCall`` record (tokens, latency, ok, error) for the episode record (FR73).
"""

from __future__ import annotations

import json
import re
import time
from typing import Any, Optional

import httpx

from studio.config import ModelSettings
from studio.core.ports import ModelCall

_OBJECT = re.compile(r"\{.*\}", re.DOTALL)


class ModelError(RuntimeError):
    def __init__(self, message: str, call: ModelCall):
        super().__init__(message)
        self.call = call


class ModelPort:
    def __init__(self, settings: ModelSettings, client: Optional[httpx.AsyncClient] = None):
        self.settings = settings
        self._client = client or httpx.AsyncClient(timeout=settings.timeout_s)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def complete_json(self, messages: list[dict[str, str]], model: Optional[str] = None) -> tuple[Any, ModelCall]:
        """Ask for one JSON object; return it parsed, with the call record.

        Raises ``ModelError`` (carrying the record) on transport failure, a
        non-2xx response, or output that is not a JSON object — never a
        default value (FR46)."""
        model = model or self.settings.agent_model
        body: dict[str, Any] = {
            "model": model, "messages": messages, "temperature": self.settings.temperature,
            "response_format": {"type": "json_object"},
            self.settings.token_param: self.settings.max_output_tokens,
        }
        if self.settings.reasoning_effort:
            body["reasoning_effort"] = self.settings.reasoning_effort
        started = time.perf_counter()

        def record(ok: bool, usage: Optional[dict] = None, error: Optional[str] = None) -> ModelCall:
            return ModelCall(model=model, ok=ok, path="json_mode",
                             input_tokens=(usage or {}).get("prompt_tokens"),
                             output_tokens=(usage or {}).get("completion_tokens"),
                             latency_ms=round((time.perf_counter() - started) * 1000, 1), error=error)

        try:
            response = await self._client.post(
                f"{self.settings.base_url}/chat/completions", json=body,
                headers={"Authorization": f"Bearer {self.settings.api_key}"})
        except httpx.HTTPError as exc:
            raise ModelError(f"model endpoint unreachable: {exc}", record(False, error=type(exc).__name__)) from exc
        if response.status_code >= 400:
            detail = response.text[:300]
            raise ModelError(f"model endpoint returned {response.status_code}: {detail}",
                             record(False, error=f"HTTP {response.status_code}"))
        payload = response.json()
        usage = payload.get("usage") or {}
        try:
            content = payload["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError):
            raise ModelError("model response had no message content", record(False, usage, "no_content")) from None
        match = _OBJECT.search(content)
        try:
            parsed = json.loads(match.group(0) if match else content)
        except json.JSONDecodeError:
            raise ModelError("model output was not a JSON object", record(False, usage, "not_json")) from None
        return parsed, record(True, usage)
