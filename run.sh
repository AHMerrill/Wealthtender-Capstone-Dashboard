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

if ! command -v "$PY" >/dev/null 2>&1; then
  echo "Error: Python 3 not found. Install python 3.11+ and try again." >&2
  exit 1
fi

if [ ! -d .venv ]; then
  "$PY" -m venv .venv
fi

source .venv/bin/activate

# Install deps (quiet on repeat runs).
pip install -q -r requirements.txt

# --- Cleanup on exit (Ctrl+C, errors, or normal finish) ---
API_PID=""
cleanup() {
  if [ -n "$API_PID" ]; then
    kill "$API_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

# Start API in background, then start dashboard.
if command -v lsof >/dev/null 2>&1 && lsof -ti :8000 >/dev/null 2>&1; then
  echo "API already running on port 8000; skipping start."
else
  python -m uvicorn api.main:app --port 8000 &
  API_PID=$!
  # Verify the API process actually started
  sleep 1
  if ! kill -0 "$API_PID" 2>/dev/null; then
    echo "Error: API failed to start. Check port 8000." >&2
    exit 1
  fi
fi

python -m dashboard.app
