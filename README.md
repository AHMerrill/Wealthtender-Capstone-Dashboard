# Wealthtender Capstone Dashboard

A two-service analytics dashboard built for the UT Austin MSBA 2026 Capstone with Wealthtender.

- **API** (`api/`) — FastAPI backend that serves normalized review data from pre-built artifacts.
- **Dashboard** (`dashboard/`) — Plotly Dash frontend with EDA charts, firm/advisor views, and role-based access.

---

## Table of Contents

1. [Getting Access (SSH Setup)](#1-getting-access-ssh-setup)
2. [Cloning the Repo](#2-cloning-the-repo)
3. [Running Locally](#3-running-locally)
4. [Making Changes](#4-making-changes)
5. [Project Structure](#5-project-structure)
6. [Environment Variables](#6-environment-variables)
7. [Docker Compose (Alternative)](#7-docker-compose-alternative)
8. [Deployment](#8-deployment)
9. [Auth & Security](#9-auth--security)
10. [Production Handoff](#10-production-handoff)
11. [EDA Artifacts](#11-eda-artifacts)

---

## 1. Getting Access (SSH Setup)

This is a private repo. Once you're added as a collaborator, you'll need an SSH key to clone and push. If you already have SSH keys set up with GitHub, skip to [Cloning the Repo](#2-cloning-the-repo).

### Step 1: Check for an existing SSH key

**macOS / Linux:**
```bash
ls ~/.ssh/id_ed25519.pub 2>/dev/null || ls ~/.ssh/id_rsa.pub 2>/dev/null
```

**Windows (PowerShell):**
```powershell
Test-Path "$HOME\.ssh\id_ed25519.pub"
```

If a file path prints (or `True` on Windows), you already have a key — skip to Step 3.

### Step 2: Generate a new SSH key

This command works on all platforms (macOS, Linux, and Windows 10+):

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

Press Enter through all the prompts (default file location, no passphrase is fine for dev machines).

### Step 3: Copy your public key

**macOS:**
```bash
pbcopy < ~/.ssh/id_ed25519.pub
```

**Linux:**
```bash
cat ~/.ssh/id_ed25519.pub
```
Then select and copy the output.

**Windows (PowerShell):**
```powershell
Get-Content "$HOME\.ssh\id_ed25519.pub" | Set-Clipboard
```

### Step 4: Add the key to GitHub

1. Go to [github.com/settings/ssh/new](https://github.com/settings/ssh/new)
2. **Title:** Something like "My Laptop"
3. **Key:** Paste what you copied
4. Click **Add SSH key**

### Step 5: Test the connection

Run this on any platform:

```bash
ssh -T git@github.com
```

You should see: `Hi <username>! You've successfully authenticated...`

---

## 2. Cloning the Repo

### First time (macOS / Linux)

```bash
mkdir -p ~/Projects
git clone git@github.com:AHMerrill/Wealthtender-Capstone-Dashboard.git ~/Projects/Wealthtender-Dashboard
cd ~/Projects/Wealthtender-Dashboard
```

### First time (Windows PowerShell)

```powershell
New-Item -ItemType Directory -Force -Path "$HOME\Projects" | Out-Null
git clone git@github.com:AHMerrill/Wealthtender-Capstone-Dashboard.git "$HOME\Projects\Wealthtender-Dashboard"
Set-Location "$HOME\Projects\Wealthtender-Dashboard"
```

### Already cloned? Just pull the latest

**macOS / Linux:**
```bash
cd ~/Projects/Wealthtender-Dashboard
git pull
```

**Windows PowerShell:**
```powershell
Set-Location "$HOME\Projects\Wealthtender-Dashboard"
git pull
```

---

## 3. Running Locally

**Requirements:** Python 3.9 or newer (3.11 or 3.12 preferred). The launcher finds the best version automatically.

### macOS / Linux

```bash
cd ~/Projects/Wealthtender-Dashboard
bash run.sh
```

### Windows

```powershell
Set-Location "$HOME\Projects\Wealthtender-Dashboard"
.\run.ps1
```

Then open **http://localhost:8050** in your browser.

The first run creates a virtual environment and installs dependencies (takes about a minute). After that, `bash run.sh` starts both services in a few seconds.

> **Tip:** To stop the services, press `Ctrl+C` in the terminal. The script cleans up both processes automatically.

---

## 4. Making Changes

```bash
# 1. Pull the latest before you start
git pull

# 2. Make your changes and test locally
bash run.sh

# 3. Stage, commit, and push
git add .
git commit -m "Brief description of what you changed"
git push origin main
```

If Render is connected, pushing to `main` triggers an automatic redeploy.

---

## 5. Project Structure

```
api/                  FastAPI backend — reads artifacts, exposes REST endpoints
  main.py             All API routes
  services/           Data loading and processing logic
dashboard/            Plotly Dash frontend
  app.py              Main layout, navigation, and core callbacks
  components/         Page content builders (EDA, firm view, etc.)
  plots/              Chart generation (Plotly figures)
  pages/              Dash page registrations (splash, EDA, firm)
  services/           HTTP client for the API, branding, roles
artifacts/            Pre-built data artifacts from the EDA pipeline
  macro_insights/     Reviews, lexical data, quality reports
data_contract/        Schema expectations for artifacts
run.sh                Local dev launcher (macOS/Linux)
run.ps1               Local dev launcher (Windows)
docker-compose.yml    Local Docker setup (alternative to run.sh)
Dockerfile.api        Container image for the API
Dockerfile.dashboard  Container image for the dashboard
render.yaml           Render deployment blueprint
```

---

## 6. Environment Variables

All settings have sensible defaults for local development — you don't need to configure anything to run locally.

See `.env.example` for the full list. On Render, set these in each service's **Environment** tab.

| Variable         | Default                 | Set On      | What It Does                                           |
|------------------|-------------------------|-------------|--------------------------------------------------------|
| `API_BASE`       | `http://localhost:8000` | Dashboard   | URL the dashboard uses to reach the API                |
| `PORT`           | `8050` / `8000`         | Both        | Listening port (Render injects this automatically)     |
| `API_KEY`        | *(empty — auth off)*    | Both        | Shared secret between services (see [Auth](#9-auth--security)) |
| `ADMIN_PASSWORD` | `WT$msba2026`           | Dashboard   | Password for the admin portal on the splash page       |

---

## 7. Docker Compose (Alternative)

If you prefer Docker over the `run.sh` script:

```bash
docker compose up --build     # first time or after code changes
docker compose up              # subsequent runs
docker compose down            # stop everything
```

Dashboard at http://localhost:8050, API at http://localhost:8000.

---

## 8. Deployment

Both services are containerized and can deploy to any Docker-compatible host (Render, Railway, Fly.io, AWS ECS, GCP Cloud Run, etc.).

**Steps for any platform:**

1. Deploy the API using `Dockerfile.api`.
2. Deploy the dashboard using `Dockerfile.dashboard`.
3. Set `API_BASE` on the dashboard to the API's public URL.
4. Generate a random `API_KEY` and set the **same value** on both services.
5. Set `ADMIN_PASSWORD` on the dashboard to your chosen admin password.

A `render.yaml` blueprint is included for Render, but it is not the only option.

### Current Render Setup

The project is currently deployed on Render with the following environment variables already configured:

| Service | Variable | Status |
|---------|----------|--------|
| `wt-api` | `PORT` | Set |
| `wt-api` | `API_KEY` | Set (shared secret) |
| `wt-dash` | `API_BASE` | Set (points to `wt-api`) |
| `wt-dash` | `API_KEY` | Set (same key as `wt-api`) |
| `wt-dash` | `ADMIN_PASSWORD` | Set |

If you need to rotate the API key or change the admin password, update the values in each service's **Environment** tab on the [Render dashboard](https://dashboard.render.com). The `API_KEY` must match on both services.

---

## 9. Auth & Security

There are two layers of authentication:

### API Key (service-to-service)

The API rejects any request without a valid `X-API-Key` header. The dashboard sends this header automatically. Both services read the key from the `API_KEY` environment variable. An API key is already set on both Render services.

- **Locally:** `API_KEY` is empty by default, so auth is skipped. Nothing to configure.
- **On Render:** The `API_KEY` is already configured on both `wt-api` and `wt-dash`. To rotate it, update the value on both services in their Environment tabs — they must always match.
- The `/api/health` endpoint is always open (required for health checks).

### Admin Password (user-facing)

The admin portal on the splash page requires a password before granting access. The password is read from `ADMIN_PASSWORD` (defaults to `WT$msba2026`). This is already set on Render. The check is server-side and cannot be bypassed from the browser.

---

## 10. Production Handoff

When handing this project to Wealthtender's engineering team, here's a roadmap for upgrading auth:

| What to Change | Current Approach | Replace With |
|----------------|-----------------|--------------|
| Admin login | Shared password | SSO (Okta, Auth0, Azure AD, etc.) |
| Role assignment | User clicks a card on splash page | Role injected from SSO identity token |
| Firm ID | User picks from dropdown | Firm ID from SSO claims or database lookup |
| API auth | Shared API key in `X-API-Key` header | JWT validation or OAuth2 client credentials |
| CORS origins | `allow_origins=["*"]` | Restrict to the dashboard's production domain |

**Key files to modify:**

| File | What Lives There |
|------|-----------------|
| `dashboard/app.py` | `user-role` store and `_get_role_and_firm()` — the central auth seam |
| `dashboard/pages/splash.py` | Password form and firm picker — replace with SSO redirect |
| `dashboard/roles.py` | Role definitions and page permissions |
| `api/main.py` | `X-API-Key` middleware — swap for JWT/OAuth validation |

---

## 11. EDA Artifacts

The EDA page renders from pre-built files in `artifacts/macro_insights/`:

| File | Purpose |
|------|---------|
| `reviews_clean.csv` | Cleaned review data |
| `eda/eda_summary.json` | Summary statistics |
| `eda/coverage.json` | Data coverage metrics |
| `quality/quality_summary.json` | Quality report |
| `quality/raw_file_meta.json` | Raw file metadata |
| `quality/missing_report.csv` | Missing data report |
| `lexical/top_tokens.csv` | Top unigram tokens |
| `lexical/top_bigrams.csv` | Top bigram tokens |

To update the dashboard with new data, replace these files with fresh exports from the EDA notebook and the dashboard picks them up automatically.
