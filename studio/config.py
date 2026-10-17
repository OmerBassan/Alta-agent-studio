"""Runtime configuration — one typed object, constructed once, validated at
startup (NFR17), overridable by environment.

The model is configuration, never code (NFR12, AD-14): an OpenAI-compatible
``/v1`` endpoint named by ``OPENAI_BASE_URL``, a key in ``OPENAI_API_KEY``, and
model names in ``STUDIO_AGENT_MODEL`` (and, for tiering, per-role variables
that default to it). With no key and no base URL the platform runs credential-
free on the deterministic agent. A half-configured live setup is rejected here,
at startup, rather than failing on the first request.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional

_TOKEN_PARAMS = ("max_tokens", "max_completion_tokens")
_EFFORT = re.compile(r"^[a-z][a-z0-9_-]*$")


class ConfigurationError(ValueError):
    pass


@dataclass(frozen=True)
class ModelSettings:
    base_url: str
    api_key: str
    agent_model: str
    token_param: str = "max_tokens"
    reasoning_effort: str = ""
    temperature: float = 0.2
    max_output_tokens: int = 700
    timeout_s: float = 45.0
    price_in_per_mtok: Optional[float] = None
    price_out_per_mtok: Optional[float] = None


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    model: Optional[ModelSettings]
    """None means credential-free mode."""

    @property
    def live(self) -> bool:
        return self.model is not None

    @classmethod
    def from_env(cls, env: Mapping[str, str] = os.environ) -> "Settings":
        key = env.get("OPENAI_API_KEY", "").strip()
        base = env.get("OPENAI_BASE_URL", "").strip()
        data_dir = Path(env.get("STUDIO_DATA_DIR", "").strip() or "studio_data")
        if not key and not base:
            return cls(data_dir=data_dir, model=None)
        model = env.get("STUDIO_AGENT_MODEL", "").strip()
        if not model:
            raise ConfigurationError("A model endpoint is configured but STUDIO_AGENT_MODEL is empty; name the model.")
        token_param = env.get("OPENAI_TOKEN_PARAM", "").strip() or "max_tokens"
        if token_param not in _TOKEN_PARAMS:
            raise ConfigurationError(f"OPENAI_TOKEN_PARAM must be one of {_TOKEN_PARAMS}, got {token_param!r}")
        effort = env.get("OPENAI_REASONING_EFFORT", "").strip()
        if effort and not _EFFORT.match(effort):
            raise ConfigurationError(f"OPENAI_REASONING_EFFORT must be a plain word, got {effort!r}")

        def price(name: str) -> Optional[float]:
            raw = env.get(name, "").strip()
            if not raw:
                return None
            try:
                return float(raw)
            except ValueError:
                raise ConfigurationError(f"{name} must be a number (dollars per million tokens)") from None

        return cls(data_dir=data_dir, model=ModelSettings(
            base_url=(base or "https://api.openai.com/v1").rstrip("/"),
            api_key=key or "local", agent_model=model, token_param=token_param, reasoning_effort=effort,
            price_in_per_mtok=price("STUDIO_PRICE_IN"), price_out_per_mtok=price("STUDIO_PRICE_OUT")))
