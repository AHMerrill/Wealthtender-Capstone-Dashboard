# Wealthtender Capstone Dashboard

This repo contains two modular apps:
- `api/` (FastAPI) serves normalized dashboard data.
- `dashboard/` (Plotly Dash) renders views for firms and advisors.

## Quickstart (local)

### macOS / Linux (one command, single clone)

```bash
REPO_DIR="$HOME/Projects/Wealthtender-Dashboard"
if [ -d "$REPO_DIR/.git" ]; then
  cd "$REPO_DIR" && git pull
else
  mkdir -p "$REPO_DIR" && git clone https://github.com/AHMerrill/Wealthtender-Capstone-Dashboard.git "$REPO_DIR" && cd "$REPO_DIR"
fi
./run.sh
```

### Windows PowerShell (one command, single clone)

```powershell
$RepoDir = "$HOME\Projects\Wealthtender-Dashboard"
if (Test-Path "$RepoDir\.git") {
  Set-Location $RepoDir
  git pull
} else {
  New-Item -ItemType Directory -Force -Path $RepoDir | Out-Null
  git clone https://github.com/AHMerrill/Wealthtender-Capstone-Dashboard.git $RepoDir
  Set-Location $RepoDir
}
.\run.ps1
```

### Open the dashboard

After the script starts, open:

```
http://localhost:8050
```

You can also click:

[![Launch Dashboard](https://img.shields.io/badge/launch-dashboard-blue)](http://localhost:8050)

### Already cloned?

From the repo root, run:

```bash
./run.sh
```

Do not run `git clone` from inside an existing clone (it creates nested folders).

Note: the first run installs dependencies and can take a minute. Subsequent runs are fast.

### Local Files (where they are stored)

Running the commands above downloads files to your local machine. The repo will be stored at:

- macOS/Linux: `~/Projects/Wealthtender-Dashboard`
- Windows: `C:\Users\<you>\Projects\Wealthtender-Dashboard`

To remove the files later, delete that folder.

## Edit and Push Workflow

1. Clone the repo (or pull latest changes).
2. Make local edits.
3. Run the app and verify at `http://localhost:8050`.
4. Commit and push to `main` when it looks correct.

Example commands:

```bash
git status
git add .
git commit -m "Update dashboard"
git push origin main
```

## Notes on Python Version

This repo supports Python 3.9–3.13. The launcher prefers 3.12 or 3.11 if available,
but will use your default `python3` if not.

## Structure

- `api/` FastAPI service that reads artifacts and exposes firm/advisor endpoints.
- `dashboard/` Dash app (multi-page) that calls the API.
- `artifacts/` Real artifacts (Macro Insights + manifest in `artifacts/metadata.json`).
- `data_contract/` Data contract and schema expectations.
- `docs/` Brandbook and project docs.

## Notes

- Auth is stubbed. The dashboard currently uses a firm selector to simulate firm scoping.
- Artifacts are loaded via the API. The dashboard does not read files directly.
- Macro Insights charts are built from `artifacts/macro_insights/**` (moved from the EDA outputs).

## Macro Insights Data

The Macro Insights view is generated from these artifact files:

- `artifacts/macro_insights/reviews_clean.csv`
- `artifacts/macro_insights/eda/eda_summary.json`
- `artifacts/macro_insights/eda/coverage.json`
- `artifacts/macro_insights/quality/quality_summary.json`
- `artifacts/macro_insights/quality/raw_file_meta.json`
- `artifacts/macro_insights/quality/missing_report.csv`
- `artifacts/macro_insights/lexical/top_tokens.csv`
- `artifacts/macro_insights/lexical/top_bigrams.csv`

If you replace these artifacts with new exports from the EDA notebook, the dashboard will reflect the new outputs.

## Deployment + Auth Handoff

This repo is designed for a standard production setup:

1. Deploy the API and Dash app on a server or container.
2. Put authentication in front of the app (reverse proxy or API-layer auth).
3. Expose a URL like `dashboard.clientsite.com`, or embed via iframe.

Common auth options:
- Username/password via reverse proxy (e.g., Nginx + basic auth or OAuth/SSO).
- Firm-scoped JWTs enforced by the API.
- SSO integration handled at the hosting layer.

The dashboard already assumes firm scoping. In production, the selected firm should
come from the authenticated user context rather than a dropdown.
