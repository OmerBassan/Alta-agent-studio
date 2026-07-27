# -*- coding: utf-8 -*-
"""Single place credentials enter the process.

Every platform entry point imports this FIRST; it loads the repo-root ``.env``
into ``os.environ`` once, and spawned subprocesses inherit those values.

Precedence (highest first): real OS env vars > repo-root ``.env`` > legacy
``builder_platform/.env`` (backward-compat overflow, fills only unset keys).
"""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ROOT_ENV = REPO_ROOT / ".env"
# This file lives in builder_platform/, and so does the legacy overflow .env
# (Vapi keys, etc.). Derive it from __file__ so a folder rename can never make
# it stale again — an earlier `platform/` -> `builder_platform/` rename left
# this pointing at a non-existent dir, so the Vapi credentials were silently
# never loaded and every call failed with "VAPI_ASSISTANT_ID is not set".
LEGACY_PLATFORM_ENV = Path(__file__).resolve().parent / ".env"

_LOADED = False


def _looks_like_placeholder(value: str) -> bool:
    """True for unfilled template text — a blank, a bracketed placeholder like
    [INSERT_KEY_HERE] or <your-key>, or a known dummy word. Such values must
    never reach os.environ: a garbage credential is worse than an absent one
    (it disables the clean fallback and fails auth outright)."""
    v = (value or "").strip()
    if not v:
        return True
    return (v.startswith(("[", "<")) and v.endswith(("]", ">"))) or \
        v.lower() in {"changeme", "your-key-here", "insert_key_here"}


def load_env(*, force: bool = False) -> None:
    """Merge the env files into ``os.environ``. Idempotent: safe to import from
    several entry points.

    Precedence, highest to lowest:
      1. a variable already present in the real OS environment (never clobbered);
      2. a NON-EMPTY value in the repo-root ``.env`` (canonical);
      3. a value in the legacy ``builder_platform/.env`` (backward-compat overflow).
    A blank line in one file therefore never shadows a real value in the other —
    the classic two-file dotenv footgun — because we merge explicitly on
    non-empty values instead of relying on file load order.
    """
    global _LOADED
    if _LOADED and not force:
        return
    _LOADED = True
    try:
        from dotenv import dotenv_values
    except ImportError:
        # No python-dotenv: fall back to whatever the real OS environment holds.
        return
    merged: dict[str, str] = {}
    if LEGACY_PLATFORM_ENV.is_file():
        merged.update({k: v for k, v in dotenv_values(LEGACY_PLATFORM_ENV).items()
                       if v and not _looks_like_placeholder(v)})
    if ROOT_ENV.is_file():
        merged.update({k: v for k, v in dotenv_values(ROOT_ENV).items()
                       if v and not _looks_like_placeholder(v)})
    for key, value in merged.items():
        os.environ.setdefault(key, value)  # real OS env wins over files


def anthropic_key_status() -> tuple[bool, str]:
    """(usable, human message) for the builder's LLM credential.

    ``usable`` is True only when a non-placeholder ANTHROPIC_API_KEY is set.
    When it is absent the Agent SDK falls back to the machine's own Claude
    auth (e.g. a Pro subscription) — which we surface loudly so a reviewer is
    never surprised by where the tokens are billed.
    """
    raw = os.environ.get("ANTHROPIC_API_KEY", "")
    if _looks_like_placeholder(raw):
        return False, ("ANTHROPIC_API_KEY not set — the builder will use this "
                       "machine's existing Claude auth (subscription/CLI login). "
                       "Set it in the repo-root .env to bill an API key instead.")
    return True, f"ANTHROPIC_API_KEY set (…{raw.strip()[-4:]})."


# Importing this module runs the bootstrap.
load_env()
