$ErrorActionPreference = "Stop"

function Find-Python {
  if (Get-Command python3.12 -ErrorAction SilentlyContinue) { return "python3.12" }
  if (Get-Command python3.11 -ErrorAction SilentlyContinue) { return "python3.11" }
  if (Get-Command python -ErrorAction SilentlyContinue) { return "python" }
  throw "Python not found. Install Python 3.12 or 3.11."
}

$PY = Find-Python
& $PY -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Start API in background, then start dashboard.
Start-Process -NoNewWindow -FilePath uvicorn -ArgumentList "api.main:app --reload --port 8000"
python dashboard\app.py
