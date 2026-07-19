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

echo "[alta] starting platform on http://localhost:8100  (Ctrl+C to stop)"
cd builder_platform
exec python -m uvicorn app:app --port 8100
