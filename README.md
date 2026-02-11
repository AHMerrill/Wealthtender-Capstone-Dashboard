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

| Variable         | Default                 | Where       | Description                                            |
|------------------|-------------------------|-------------|--------------------------------------------------------|
| `API_BASE`       | `http://localhost:8000` | Dashboard   | URL the dashboard uses to reach the API                |
| `PORT`           | `8050` / `8000`         | Both        | Listening port (Render injects this automatically)     |
| `API_KEY`        | *(empty — auth off)*    | Both        | Shared secret; API rejects requests without it         |
| `ADMIN_PASSWORD` | `WT$msba2026`           | Dashboard   | Password for the admin portal on the splash page       |

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
4. Generate a random `API_KEY` and set the **same value** on both services.
5. Set `ADMIN_PASSWORD` on the dashboard to your chosen admin password.

A `render.yaml` blueprint is included if using Render, but it is not the only option.

## Auth & Security

The project has two layers of authentication:

### 1. API Key (service-to-service)

The API rejects any request without a valid `X-API-Key` header. The dashboard sends this header automatically. Both services read the key from the `API_KEY` environment variable. When `API_KEY` is empty (local dev), auth is skipped.

**To enable on Render:** set the same `API_KEY` value on both the `wt-api` and `wt-dash` services in the Render dashboard. The `/api/health` endpoint is always open (needed for health checks).

### 2. Admin Password (user-facing)

The admin portal on the splash page requires a password. The password is read from the `ADMIN_PASSWORD` env var (defaults to `WT$msba2026`). The check is server-side — not bypassable from the browser.

### Production Handoff

When handing this project to Wealthtender's engineering team, here's what to change:

| Component | Current | Replace With |
|-----------|---------|-------------|
| **Admin login** (`dashboard/pages/splash.py`) | Shared password | SSO redirect (Okta, Auth0, Azure AD, etc.) |
| **Role assignment** (`splash.py` → `user-role` store) | User clicks a card | Role injected from SSO identity token |
| **Firm ID** (`splash.py` → `user-role` store) | User picks from dropdown | Firm ID from SSO claims or database lookup |
| **API auth** (`api/main.py` middleware) | Shared API key in header | JWT validation or OAuth2 client credentials |
| **CORS origins** (`api/main.py`) | `allow_origins=["*"]` | Restrict to the dashboard's production domain |

**Key files to touch:**
- `dashboard/pages/splash.py` — replace the password form and firm picker with SSO redirect
- `dashboard/roles.py` — role definitions and page permissions (may need new roles)
- `api/main.py` — swap the `X-API-Key` middleware for JWT/OAuth validation
- `dashboard/app.py` — the `user-role` `dcc.Store` and `_get_role_and_firm()` are the central auth seam

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
