# -*- coding: utf-8 -*-
"""Vapi REST control plane — point the assistant at THIS machine's runtime.

Scope: the one write the platform needs to place a browser test call, plus the
preflight that stops a silently-dead call before it starts.

GROUND TRUTH (probed against the live account 2026-07-17, not from docs):
  * The flight-proven assistant's model object is exactly:
        {"provider":"custom-llm","model":"custom-router",
         "url":"https://<tunnel>/v1","temperature":0.2,"messages":[...]}
  * `url` is the BASE + `/v1`. Vapi appends `/chat/completions` itself, which is
    the route vapi_adapter.py serves. Do NOT include the suffix.
  * A custom-llm model CANNOT carry a shared secret: PATCHing `model.secret`
    returns 400 `model.property secret should not exist`. Vapi therefore sends
    NO auth header to the model URL, so vapi_adapter's VAPI_SERVER_SECRET check
    must be disabled for a Vapi-driven call or every turn 401s — silently, as
    dead air. `preflight_auth` turns that into a loud error at button-press.

The platform rewrites `model.url` (the wiring) and — when the generated agent
declares a static OPENER — `firstMessage` + `firstMessageMode`, so the agent's
first words play at pickup with zero model calls (~500ms, Vapi speaks them
natively). Everything else (voice, transcriber, temperature, system messages)
is left exactly as configured in the dashboard. firstMessage is NEVER set to a
blank/whitespace value: a " " firstMessage silently wedges Vapi's TTS queue
(logged trap).
"""

from __future__ import annotations

import os

import httpx

VAPI_API_BASE = os.environ.get("VAPI_API_BASE", "https://api.vapi.ai")
_TIMEOUT_S = 20.0


class VapiConfigError(RuntimeError):
    """Operator-actionable misconfiguration — never a bug in the call path."""


class VapiAPIError(RuntimeError):
    """Vapi rejected a request; carries the status and body tail."""


def _private_key() -> str:
    key = os.environ.get("VAPI_PRIVATE_KEY", "").strip()
    if not key:
        raise VapiConfigError(
            "VAPI_PRIVATE_KEY is not set. Add it to builder_platform/.env "
            "(Vapi dashboard -> Account -> API Keys -> Private Key).")
    return key


def assistant_id() -> str:
    aid = os.environ.get("VAPI_ASSISTANT_ID", "").strip()
    if not aid:
        raise VapiConfigError(
            "VAPI_ASSISTANT_ID is not set. Add it to builder_platform/.env — the id of "
            "the Vapi assistant to drive (dashboard -> Assistants -> the "
            "assistant -> its id).")
    return aid


def public_key() -> str:
    """The browser-side key. Vapi's Web SDK initializes with the PUBLIC key;
    the private key must never reach the page."""
    key = os.environ.get("VAPI_PUBLIC_KEY", "").strip()
    if not key:
        raise VapiConfigError(
            "VAPI_PUBLIC_KEY is not set. Add it to builder_platform/.env (Vapi "
            "dashboard -> Account -> API Keys -> Public Key). The browser needs "
            "it to open the web call; it is safe to expose, unlike the private key.")
    return key


def preflight_auth() -> None:
    """Refuse the call if the adapter would 401 every Vapi turn.

    Vapi cannot send a secret to a custom-llm url (see module docstring), so a
    set VAPI_SERVER_SECRET guarantees silent dead air. Failing here — loudly, at
    button-press — is the whole point: the alternative is a connected call that
    never speaks, which is exactly the failure mode that has cost this project
    the most time.
    """
    if os.environ.get("VAPI_SERVER_SECRET", "").strip():
        raise VapiConfigError(
            "VAPI_SERVER_SECRET is set, but Vapi cannot send a secret to a "
            "custom-llm endpoint (PATCHing model.secret returns 400). Every "
            "turn would be rejected with 401 and the call would connect but "
            "never speak. Comment out VAPI_SERVER_SECRET in builder_platform/.env for "
            "browser test calls. (The tunnel URL is random and short-lived; the "
            "runtime should only be exposed while you are demoing.)")


async def _request(method: str, path: str, **kw) -> dict:
    headers = {"Authorization": f"Bearer {_private_key()}",
               "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=_TIMEOUT_S) as client:
        try:
            resp = await client.request(method, f"{VAPI_API_BASE}{path}",
                                        headers=headers, **kw)
        except httpx.HTTPError as exc:
            raise VapiAPIError(f"Vapi {method} {path} failed: {exc}") from exc
    if resp.status_code >= 300:
        raise VapiAPIError(
            f"Vapi {method} {path} -> HTTP {resp.status_code}: {resp.text[:400]}")
    try:
        return resp.json()
    except ValueError as exc:
        raise VapiAPIError(f"Vapi {method} {path} returned non-JSON") from exc


async def get_assistant(aid: str) -> dict:
    return await _request("GET", f"/assistant/{aid}")


def _patch_body(model: dict, first_message: str | None) -> dict:
    """The exact PATCH payload — pure, so tests can pin the firstMessage rules.

    firstMessage is included ONLY for a non-blank opener (blank/whitespace
    wedges the TTS queue); when set, firstMessageMode makes the assistant speak
    it unprompted at pickup — the whole point of the cached opener.
    """
    body: dict = {"model": model}
    text = (first_message or "").strip()
    if text:
        body["firstMessage"] = text
        body["firstMessageMode"] = "assistant-speaks-first"
    return body


async def point_assistant_at(public_url: str, aid: str | None = None,
                             first_message: str | None = None) -> dict:
    """Point the assistant's custom-llm url at this machine's tunnel, and (when
    given) install the generated agent's cached opener as firstMessage.

    Returns {"assistant_id", "model_url", "previous_model_url",
    "first_message"} so the caller can show the operator what changed.
    """
    aid = aid or assistant_id()
    base = public_url.rstrip("/")
    if not base.startswith("https://"):
        raise VapiConfigError(
            f"Vapi requires an https endpoint; got {base!r}. Use the https "
            "form of your tunnel URL.")
    model_url = f"{base}/v1"

    assistant = await get_assistant(aid)
    model = dict(assistant.get("model") or {})
    if not model:
        raise VapiConfigError(
            f"Assistant {aid} has no model object to point at this runtime.")
    previous = model.get("url")

    # Preserve everything the dashboard configured; force only the wiring that
    # makes this assistant talk to OUR brain.
    model["provider"] = "custom-llm"
    model["url"] = model_url
    model.setdefault("model", "custom-router")

    body = _patch_body(model, first_message)
    await _request("PATCH", f"/assistant/{aid}", json=body)
    return {"assistant_id": aid, "model_url": model_url,
            "previous_model_url": previous,
            "first_message": body.get("firstMessage")}
