#!/usr/bin/env bash
set -euo pipefail

# Always run from the repo root (where this script lives).
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$SCRIPT_DIR"

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
if command -v lsof >/dev/null 2>&1 && lsof -ti :8000 >/dev/null 2>&1; then
  echo "API already running on port 8000; skipping start."
  API_PID=""
else
  python -m uvicorn api.main:app --port 8000 &
  API_PID=$!
fi

python -m dashboard.app

# Clean up API on exit
if [ -n "${API_PID}" ]; then
  kill "$API_PID" 2>/dev/null || true
fi
