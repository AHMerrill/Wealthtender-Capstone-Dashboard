$ErrorActionPreference = "Stop"

# Always run from the repo root (where this script lives).
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

function Find-Python {
  if (Get-Command python3.12 -ErrorAction SilentlyContinue) { return "python3.12" }
  if (Get-Command python3.11 -ErrorAction SilentlyContinue) { return "python3.11" }
  if (Get-Command python -ErrorAction SilentlyContinue) { return "python" }
  throw "Python not found. Install Python 3.11+."
}

$PY = Find-Python
if (-Not (Test-Path .\.venv)) { & $PY -m venv .venv }
. .\.venv\Scripts\Activate.ps1
pip install -q -r requirements-pipeline.txt

# Forward all arguments to the pipeline runner.
# Examples:
#   .\run_data_pipeline.ps1                     # run all stages
#   .\run_data_pipeline.ps1 --stage clean       # run only Stage 1
#   .\run_data_pipeline.ps1 --stage embed       # run only Stages 2 + 2b
#   .\run_data_pipeline.ps1 --stage score       # run only Stage 3
#   .\run_data_pipeline.ps1 --full              # force full re-embed
#   .\run_data_pipeline.ps1 --validate          # compare outputs to backup
python -m pipeline.run @args
