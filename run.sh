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

$PY -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start API in background, then start dashboard.
uvicorn api.main:app --reload --port 8000 &
API_PID=$!

python dashboard/app.py

# Clean up API on exit
kill $API_PID
