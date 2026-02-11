# Wealthtender Capstone Dashboard

A two-service analytics dashboard built for the UT Austin MSBA 2026 Capstone with Wealthtender.

- **API** (`api/`) — FastAPI backend that serves normalized review data from pre-built artifacts.
- **Dashboard** (`dashboard/`) — Plotly Dash frontend with EDA charts, firm/advisor views, and role-based access.

## Quick Start

### macOS / Linux

```bash
REPO_DIR="$HOME/Projects/Wealthtender-Dashboard"
if [ -d "$REPO_DIR/.git" ]; then
  cd "$REPO_DIR" && git pull
else
  mkdir -p "$REPO_DIR" && git clone https://github.com/AHMerrill/Wealthtender-Capstone-Dashboard.git "$REPO_DIR" && cd "$REPO_DIR"
fi
bash run.sh
```

### Windows PowerShell

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

Then open **http://localhost:8050**.

The first run creates a virtualenv and installs dependencies (takes about a minute). After that, `bash run.sh` starts both services in seconds.

> **Already cloned?** Just `cd` into the repo and run `bash run.sh`.

## Project Structure

```
api/                  FastAPI service — reads artifacts, exposes endpoints
dashboard/            Dash app (multi-page) — calls the API, renders UI
artifacts/            Data artifacts from the EDA pipeline
  macro_insights/     Reviews, lexical data, quality reports (legacy dir name)
data_contract/        Schema expectations
docs/                 Brandbook and project docs
```

## Environment Variables

See `.env.example` for all settings. Defaults work out of the box for local dev.

| Variable   | Default                 | Description                              |
|------------|-------------------------|------------------------------------------|
| `API_BASE` | `http://localhost:8000` | URL the dashboard uses to reach the API  |
| `PORT`     | `8050` / `8000`         | Listening port for dashboard / API       |

## Docker Compose (alternative)

```bash
docker compose up --build     # first time or after code changes
docker compose up              # subsequent runs
```

Dashboard at http://localhost:8050, API at http://localhost:8000.

## Deployment

Both services are containerized and deploy to any Docker-compatible host (Render, Railway, Fly.io, AWS ECS, GCP Cloud Run, etc.).

**Key steps for any platform:**
1. Deploy the API service using `Dockerfile.api`.
2. Deploy the dashboard service using `Dockerfile.dashboard`.
3. Set `API_BASE` on the dashboard to the API's public URL.

A `render.yaml` blueprint is included if using Render, but it is not the only option.

## Auth

The splash page currently uses a role selector for demo purposes (Admin vs. Firm Portal). In production, replace this with your auth provider and inject the user's role and `firm_id` from the session.

Common approaches:
- Reverse proxy auth (Nginx + OAuth2 Proxy, SSO)
- Firm-scoped JWTs enforced by API middleware
- SSO at the hosting layer (Cloudflare Access, etc.)

## EDA Artifacts

The EDA page is built from these files in `artifacts/macro_insights/` (legacy directory name):

- `reviews_clean.csv`
- `eda/eda_summary.json`
- `eda/coverage.json`
- `quality/quality_summary.json`, `raw_file_meta.json`, `missing_report.csv`
- `lexical/top_tokens.csv`, `top_bigrams.csv`

Replace these with new exports from the EDA notebook and the dashboard updates automatically.

## Python Version

Supports Python 3.9–3.13. The launcher prefers 3.12 or 3.11 if available.

## Edit and Push

```bash
# Make changes, test locally
bash run.sh

# Commit
git add .
git commit -m "Describe your change"
git push origin main
```
