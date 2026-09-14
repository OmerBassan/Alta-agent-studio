"""Vapi custom-LLM adapter (Day 1 PM: real brain behind the proven skeleton).

Exposes an OpenAI-compatible ``POST /v1/chat/completions`` endpoint that Vapi
calls on every conversational turn. BRAIN_MODE selects the reply source:

  BRAIN_MODE=live      (default) — the loaded generated agent (runtime.py):
                       filler events stream as latency-cover chunks, then the
                       sanitized final reply in sentence chunks.
  BRAIN_MODE=skeleton  — the Day 1 AM hardcoded reply (round-trip debugging,
                       and the SSE-contract regression tests).

SSE contract (reports/vapi_custom_backend_report.pdf §4, §6.1):
- each event is ``data: <json>\n\n``  (two trailing newlines — Vapi's ingestion
  freezes silently without them)
- terminate with a ``finish_reason: "stop"`` chunk, then ``data: [DONE]\n\n``

Auth: Vapi sends the assistant's serverUrlSecret in the ``x-vapi-secret``
header. If VAPI_SERVER_SECRET is set in the environment, mismatches get 401;
if unset, auth is skipped (local curl testing).

Run:  uvicorn vapi_adapter:app --port 8000
"""

from __future__ import annotations

import json
import os
import time
import uuid
from typing import Any, AsyncIterator

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

# Loads .env into os.environ at import — must run before runtime.py imports the
# generated agent, so all components see the same configuration.
import env_bootstrap  # noqa: E402,F401

app = FastAPI(title="Alta voice adapter")


@app.on_event("startup")
async def _preload_brain() -> None:
    """Load the generated agent at boot, not on the first request — the lazy
    first-load costs ~4s, which would otherwise land as dead air on the first
    turn of the first call after every restart. Skeleton mode skips it (and
    the SSE-contract tests never trigger startup events)."""
    if os.environ.get("BRAIN_MODE", "live").strip().lower() != "skeleton":
        from runtime import get_runtime
        get_runtime()

# Ground-truth capture for diagnosing a payload-shape mismatch: dump the full
# raw body of each POST as a JSON line. Off by default (it logs full call
# transcripts) — set RAW_CAPTURE=1 to enable while debugging.
RAW_CAPTURE_PATH = os.environ.get(
    "RAW_CAPTURE_PATH",
    os.path.join(os.path.dirname(__file__), "vapi_raw_capture.jsonl"),
)
RAW_CAPTURE = os.environ.get("RAW_CAPTURE", "0") == "1"

MODEL_NAME = "alta-voice-agent"

HARDCODED_REPLY = (
    "Hi, this is Alta, your test agent. "
    "If you can hear me, the voice pipeline works end to end. "
    "Can you hear me okay?"
)


def _require_secret(request: Request) -> None:
    """Accept the shared secret from EITHER header Vapi may use:
    - ``x-vapi-secret``: sent when the secret is configured as the assistant's
      serverUrlSecret / Custom LLM secret field
    - ``Authorization: Bearer <secret>``: sent when it is configured as the
      Custom LLM provider's API key
    On mismatch, log which auth headers were present (fingerprints only) so a
    failed call is diagnosable from ground truth instead of dashboard guesses."""
    expected = os.environ.get("VAPI_SERVER_SECRET", "").strip()
    if not expected:
        return  # auth disabled for local dev
    x_secret = request.headers.get("x-vapi-secret", "").strip()
    bearer = request.headers.get("authorization", "").strip()
    if bearer.lower().startswith("bearer "):
        bearer = bearer[7:].strip()
    if x_secret == expected or bearer == expected:
        return
    def _fp(v: str) -> str:
        return f"'{v[:4]}…' (len={len(v)})" if v else "ABSENT"
    print(f"[vapi] AUTH REJECT: x-vapi-secret={_fp(x_secret)} "
          f"bearer={_fp(bearer)} expected='{expected[:4]}…' (len={len(expected)})",
          flush=True)
    raise HTTPException(status_code=401, detail="bad or missing x-vapi-secret")


def _chunk(chunk_id: str, created: int, content: str | None,
           finish_reason: str | None = None) -> str:
    delta: dict[str, Any] = {}
    if content is not None:
        delta["content"] = content
    payload = {
        "id": chunk_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": MODEL_NAME,
        "choices": [{"index": 0, "delta": delta, "finish_reason": finish_reason}],
    }
    return f"data: {json.dumps(payload)}\n\n"


def _brain_mode() -> str:
    return os.environ.get("BRAIN_MODE", "live").strip().lower()


async def _skeleton_segments() -> AsyncIterator[str]:
    for sentence in _sentences(HARDCODED_REPLY):
        yield sentence + " "


def _brain_segments(body: dict) -> AsyncIterator[str]:
    """Speakable text segments from the loaded generated agent."""
    from runtime import get_runtime, parse_vapi_request  # lazy: heavy first load
    return get_runtime().stream_turn(parse_vapi_request(body))


async def _stream_sse(segments: AsyncIterator[str]) -> AsyncIterator[str]:
    """Wrap text segments in the strict Vapi SSE contract. The stream ALWAYS
    terminates with a stop chunk + [DONE], even if the brain raises mid-turn —
    a malformed or unterminated stream freezes Vapi silently (dead air)."""
    chunk_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
    created = int(time.time())
    try:
        async for segment in segments:
            if segment:
                yield _chunk(chunk_id, created, segment)
    except Exception as exc:  # last line of defense before the caller's ear
        print(f"[vapi] brain stream failed: {exc!r}", flush=True)
        yield _chunk(chunk_id, created,
                     "Sorry, something went wrong on my end. Could you try again?")
    yield _chunk(chunk_id, created, None, finish_reason="stop")
    yield "data: [DONE]\n\n"


def _sentences(text: str) -> list[str]:
    out, buf = [], []
    for word in text.split():
        buf.append(word)
        if word.endswith((".", "?", "!")):
            out.append(" ".join(buf))
            buf = []
    if buf:
        out.append(" ".join(buf))
    return out


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "mode": "walking-skeleton"}


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    _require_secret(request)
    body = await request.json()

    # Ground-truth capture: append the full raw body so we can inspect the exact
    # payload shape (message internals, call object, any metadata Vapi attaches).
    if RAW_CAPTURE:
        try:
            with open(RAW_CAPTURE_PATH, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(body, ensure_ascii=False) + "\n")
        except Exception as exc:  # never let capture break a live call
            print(f"[vapi] raw-capture failed: {exc}", flush=True)

    skeleton = _brain_mode() == "skeleton"

    if body.get("stream", False):
        segments = _skeleton_segments() if skeleton else _brain_segments(body)
        return StreamingResponse(
            _stream_sse(segments),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    # Non-streaming fallback (Vapi always streams; this aids curl testing).
    if skeleton:
        reply = HARDCODED_REPLY
    else:
        parts = [seg async for seg in _brain_segments(body)]
        reply = "".join(parts).strip() or "Sorry, could you say that again?"
    return JSONResponse({
        "id": f"chatcmpl-{uuid.uuid4().hex[:24]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": MODEL_NAME,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": reply},
            "finish_reason": "stop",
        }],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    })
