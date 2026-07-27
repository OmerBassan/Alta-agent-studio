#!/usr/bin/env bash
# Alta Agent Studio — one-command launch (macOS / Linux).
# Creates a venv on first run, installs deps, seeds .env, starts the platform.
set -e
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
    echo "[alta] creating virtual environment..."
    python3 -m venv .venv
fi
source .venv/bin/activate

echo "[alta] installing dependencies..."
python -m pip install --quiet -r requirements.txt

if [ ! -f .env ]; then
    cp .env.example .env
    echo "[alta] created .env from .env.example"
fi

# ngrok is managed by the platform itself (builder_platform/tunnel.py): it
# auto-starts ONE ngrok agent on demand and reuses it. We deliberately do NOT
# spawn a second one here — the free tier allows a single session, and two
# racing spawns fail with ERR_NGROK_108. Set PUBLIC_URL in the .env to use your
# own tunnel instead.

echo "[alta] starting platform on http://localhost:8100  (Ctrl+C to stop)"
cd builder_platform
exec python -m uvicorn app:app --port 8100
