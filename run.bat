@echo off
REM Alta Agent Studio — one-command launch (Windows).
REM Creates a venv on first run, installs deps, seeds .env, starts the platform.
setlocal
cd /d "%~dp0"

if not exist .venv (
    echo [alta] creating virtual environment...
    python -m venv .venv || (echo [alta] Python 3.11+ is required on PATH & exit /b 1)
)
call .venv\Scripts\activate.bat

echo [alta] installing dependencies...
python -m pip install --quiet -r requirements.txt || (echo [alta] pip install failed & exit /b 1)

if not exist .env (
    copy .env.example .env >nul
    echo [alta] created .env from .env.example
)

REM ngrok is managed by the platform itself (builder_platform/tunnel.py): it
REM auto-starts ONE ngrok agent on demand and reuses it. We deliberately do NOT
REM spawn a second one here — the free tier allows a single session, and two
REM racing spawns fail with ERR_NGROK_108. Set PUBLIC_URL in the .env to use
REM your own tunnel instead.

echo [alta] starting platform on http://localhost:8100  (Ctrl+C to stop)
cd builder_platform
python -m uvicorn app:app --port 8100
