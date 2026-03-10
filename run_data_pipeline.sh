#!/usr/bin/env bash
set -euo pipefail

# Always run from the repo root (where this script lives).
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$SCRIPT_DIR"

# Prefer a Python version that has wheels for torch / sentence-transformers.
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
pip install -q -r requirements-pipeline.txt

# Forward all arguments to the pipeline runner.
# Examples:
#   ./run_data_pipeline.sh                     # run all stages
#   ./run_data_pipeline.sh --stage clean       # run only Stage 1
#   ./run_data_pipeline.sh --stage embed       # run only Stages 2 + 2b
#   ./run_data_pipeline.sh --stage score       # run only Stage 3
#   ./run_data_pipeline.sh --full              # force full re-embed
#   ./run_data_pipeline.sh --validate          # compare outputs to backup
python -m pipeline.run "$@"
