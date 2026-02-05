#!/usr/bin/env bash
set -euo pipefail

# Prefer a Python version that has wheels for pydantic-core.
if command -v python3.12 >/dev/null 2>&1; then
  PY=python3.12
elif command -v python3.11 >/dev/null 2>&1; then
  PY=python3.11
else
  PY=python3
fi

if [ ! -d .venv ]; then
  $PY -m venv .venv
fi

source .venv/bin/activate

# Install once; re-running is fast if already installed.
pip install -r requirements.txt

# Start API in background, then start dashboard.
uvicorn api.main:app --port 8000 &
API_PID=$!

python -m dashboard.app

# Clean up API on exit
kill $API_PID
