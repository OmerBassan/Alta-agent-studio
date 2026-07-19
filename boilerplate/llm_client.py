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
"""

import asyncio
import json
import os
import re
from typing import Dict, List, Type, TypeVar

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


class LLMClient:
    HARD_TIMEOUT_SECONDS = 30.0

    def __init__(self):
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
        try:
            completion = await asyncio.wait_for(
                self.client.beta.chat.completions.parse(
                    model=model, messages=messages, response_format=response_format,
                    temperature=temperature, max_tokens=max_tokens,
                ),
                timeout=self.HARD_TIMEOUT_SECONDS,
            )
            return completion.choices[0].message.parsed
        except Exception:
            return await self._structured_via_json_mode(model, response_format, messages, temperature, max_tokens)

    async def _structured_via_json_mode(self, model, response_format, messages, temperature, max_tokens):
        schema_hint = json.dumps(response_format.model_json_schema(), ensure_ascii=False)
        patched = list(messages) + [{
            "role": "system",
            "content": f"Respond with ONLY a valid JSON object matching this schema (no prose, no markdown): {schema_hint}",
        }]
        completion = await asyncio.wait_for(
            self.client.chat.completions.create(
                model=model, messages=patched, temperature=temperature,
                max_tokens=max_tokens, response_format={"type": "json_object"},
            ),
            timeout=self.HARD_TIMEOUT_SECONDS,
        )
        raw = completion.choices[0].message.content or "{}"
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        return response_format.model_validate_json(match.group(0) if match else raw)

    async def generate_text(
        self, model: str, messages: List[Dict[str, str]],
        temperature: float = 0.5, max_tokens: int = 300,
    ) -> str:
        """Model -> plain text. Used by the ANSWER and ENRICH tiers."""
        if self.mock:
            raise RuntimeError("generate_text called in MOCK mode — nodes must use their mock fallback")
        completion = await asyncio.wait_for(
            self.client.chat.completions.create(
                model=model, messages=messages, temperature=temperature, max_tokens=max_tokens,
            ),
            timeout=self.HARD_TIMEOUT_SECONDS,
        )
        return (completion.choices[0].message.content or "").strip()


llm_client = LLMClient()
