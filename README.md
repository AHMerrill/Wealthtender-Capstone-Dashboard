# Wealthtender Capstone Dashboard

A two-service analytics dashboard built for the UT Austin MSBA 2026 Capstone with Wealthtender. Analyzes financial advisor client reviews using NLP-derived similarity scoring, interactive visualizations, and role-based access control.

- **API** (`api/`) — FastAPI backend that serves normalized review data and advisor-dimension similarity scores from pre-built artifacts.
- **Dashboard** (`dashboard/`) — Plotly Dash frontend with Advisor DNA analysis, EDA charts, benchmarks, leaderboard, comparisons, and role-based access.

---

## Table of Contents

1. [Features Overview](#1-features-overview)
2. [Getting Access (SSH Setup)](#2-getting-access-ssh-setup)
3. [Cloning the Repo](#3-cloning-the-repo)
4. [Running Locally](#4-running-locally)
5. [Making Changes](#5-making-changes)
6. [Project Structure](#6-project-structure)
7. [Dashboard Pages](#7-dashboard-pages)
8. [API Endpoints](#8-api-endpoints)
9. [Artifacts & Data Pipeline](#9-artifacts--data-pipeline)
10. [Environment Variables](#10-environment-variables)
11. [Docker Compose (Alternative)](#11-docker-compose-alternative)
12. [Deployment](#12-deployment)
13. [Auth & Security](#13-auth--security)
14. [Production Handoff](#14-production-handoff)
15. [Tech Stack & Versions](#15-tech-stack--versions)

---

## 1. Features Overview

### Advisor DNA

Interactive analysis of advisor-dimension similarity scores derived from client reviews. Uses sentence-transformer embeddings to compute cosine similarity between each review and six quality dimensions (Trust & Integrity, Customer Empathy & Personalization, Communication Clarity, Responsiveness, Life Event Support, Investment Expertise).

- **Macro view** — Horizontal bar chart showing dimension distribution across all reviews, with Bar/Spider toggle and Comparison Pool selector (All Advisors vs Premier 20+ Reviews)
- **Firm / Advisor view** — Entity-specific bar chart with Dimension Profile bars, tier labels (Very Strong / Strong / Moderate / Foundational), spider/radar chart toggle, and premier pool comparison
- **Confidence tiers** — Review count-based confidence system: <10 reviews shows amber "Directional Insights" banner, 20+ reviews earns green "Robust Data" badge and inclusion in the premier benchmarking pool
- **Evidence cards** — Click any dimension to see the top-3 reviews driving that score, with rank badges, reviewer info, tier labels, and text snippets
- **Review drill-down** — Click a pie wedge or evidence card to see full review text alongside a spider/radar chart of per-dimension scores
- **Display modes** — Toggle between Raw Similarity and Percentile Rank views
- **Scoring methods** — Mean, Penalized (consistency penalty), and Weighted (time-weighted) scoring with method-specific tier breakpoints
- **Premier benchmarking** — "Compare against: All Advisors | Premier Advisors (20+ reviews)" toggle filters the percentile peer group to high-confidence entities only

### EDA (Exploratory Data Analysis)

- Review volume over time with Year/Quarter granularity toggle
- Rating distributions, word counts, n-gram analysis
- Searchable firm/advisor dropdown with "Return to Global" reset
- Date range filter with "Use Max Range" button
- Rating, word count, and review count filters
- Stopword exclusion (applied to n-gram charts only) with custom stopword input

### Benchmarks *(Sprint 3 — In Progress)*

Deep-dive into the premier benchmark pool: composition stats, dimension distributions at advisor and firm levels, P25/P50/P75 breakpoints, and peer percentile summary cards for selected entities.

### Leaderboard *(Sprint 3 — In Progress)*

Dimension leaderboard showing top-performing entities per dimension. Filterable by entity type (firm/advisor) and comparison pool (All/Premier). Click-to-expand detail cards.

### Comparisons *(Sprint 3 — In Progress)*

Intra-firm team comparison (side-by-side radar/bar of advisors within a firm) and entity-to-entity head-to-head comparison. Uses synthetic `partner_group` data for firm associations until Wealthtender provides the real export. Prominent disclaimer on synthetic data.

### Other Pages

- **Methodology** — Documentation of analytical methods
- **Home (Splash)** — Role selection portal with admin password and firm access

---

## 2. Getting Access (SSH Setup)

This is a private repo. Once you're added as a collaborator, you'll need an SSH key to clone and push. If you already have SSH keys set up with GitHub, skip to [Cloning the Repo](#3-cloning-the-repo).

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

```bash
ssh -T git@github.com
```

You should see: `Hi <username>! You've successfully authenticated...`

---

## 3. Cloning the Repo

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

## 4. Running Locally

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

## 5. Making Changes

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

## 6. Project Structure

```
api/                          FastAPI backend
  main.py                     All API routes
  services/
    artifacts.py              ArtifactStore — data loading, scoring, filtering

dashboard/                    Plotly Dash frontend
  app.py                      Main layout, sidebar, navigation, core callbacks
  branding.py                 Colors, fonts, and global CSS (from Brandbook)
  roles.py                    Role-based access configuration
  components/
    eda_content.py             EDA page charts and callback logic
  pages/
    splash.py                  Login / role selection page
    advisor_dna.py             Advisor DNA — bar/spider charts, evidence cards, drill-down
    eda.py                     EDA page registration
    benchmarks.py              Benchmarks page — premier pool analytics
    leaderboard.py             Leaderboard page — top entities per dimension
    comparisons.py             Comparisons page — intra-firm and head-to-head
    methodology.py             Methodology page
  plots/
    eda_charts.py              EDA Plotly chart builders
  services/
    api.py                     HTTP client for the FastAPI backend
    brand.py                   Brand asset loader

artifacts/                    Pre-built data artifacts
  macro_insights/              EDA artifacts (reviews, lexical, quality)
  scoring/
    review_dimension_scores.csv    Per-review cosine similarity scores (6 dimensions)
    advisor_dimension_scores.csv   Aggregated entity-level scores (mean, penalized, weighted)
  metadata.json                Artifact manifest

notebooks/
  collaborator/                Scoring notebook (generates scoring artifacts)

Brandbook/                    Brand guidelines and assets
data_contract/                Schema expectations for artifacts
run.sh                        Local dev launcher (macOS/Linux)
run.ps1                       Local dev launcher (Windows)
docker-compose.yml            Local Docker setup (alternative to run.sh)
Dockerfile.api                Container image for the API
Dockerfile.dashboard          Container image for the dashboard
render.yaml                   Render deployment blueprint
requirements.txt              Python dependencies (pinned for production)
```

---

## 7. Dashboard Pages

### Home (`/`)
Role selection splash page. Admin users enter a password; firm users select their firm. This is the default landing page on login and refresh.

### Advisor DNA (`/advisor-dna`)
Core analytical page for advisor-dimension similarity analysis.

**Sidebar controls:**
- Entity type toggle (Firm / Advisor)
- Searchable entity dropdown (shows review counts, filterable by premier status)
- Scoring method selector (Mean / Penalized / Weighted) with info tooltip and expandable "Read more" panel
- Display mode toggle (Raw Similarity / Percentile Rank)
- Comparison pool toggle (All Advisors / Premier 20+ Reviews)
- Reset to Macro View button

**Views:**
- **Macro** — Horizontal bar chart of dimension totals across all reviews, with Bar/Spider toggle and All/Premier pool selector (All: 4,579 reviews, Premier: 2,629 reviews)
- **Entity** — Horizontal bar chart with tier labels and spider/radar chart toggle. Clickable dimension cards with evidence panels showing top-3 reviews driving each score
- **Review** — Full review text with reviewer name, date, and spider chart showing per-dimension scores

**Confidence system:**
- **< 10 reviews:** Amber "Directional Insights" banner
- **10–19 reviews:** Normal access, no banner
- **20+ reviews:** Green "Robust Data" badge, included in premier pool

**Scoring methods:**
- **Mean** — Average cosine similarity across all reviews for the entity
- **Penalized** — Mean with a consistency penalty (high variance lowers the score)
- **Weighted** — Time-weighted mean giving more recent reviews higher weight

**Tier labels** (applied from method-specific percentile breakpoints):
- Very Strong (≥75th percentile)
- Strong (50th–75th)
- Moderate (25th–50th)
- Foundational (<25th)

### EDA (`/eda`)
Exploratory data analysis of the review corpus.

**Sidebar controls:**
- Entity type toggle (Firm / Advisor) with searchable dropdown
- "Return to Global" button to reset to full dataset
- Date range picker with "Use Max Range" reset button
- Time granularity selector (Year / Quarter)
- Rating, word count, review count, and n-gram filters
- Stopword controls (applied to n-gram chart only)

**Charts:** Review volume over time, rating distribution, reviews per advisor, word count distribution, rating vs. word count scatter, top n-grams.

### Benchmarks (`/benchmarks`) *(Sprint 3)*
Premier pool analytics and peer benchmarking. Available to both admin and firm roles.

**Planned content:**
- Premier pool composition: advisor vs firm breakdown, review count distributions
- Dimension score distributions at advisor and firm levels
- P25/P50/P75 benchmark breakpoints per dimension
- Peer percentile summary card for a selected entity (strengths & gaps at a glance)

### Leaderboard (`/leaderboard`) *(Sprint 3)*
Top-performing entities per dimension. Available to admin role.

**Planned content:**
- Top-N entities per dimension with score bars
- Filterable by entity type (Firm / Advisor) and pool (All / Premier)
- Click-to-expand detail cards showing full dimension profile

### Comparisons (`/comparisons`) *(Sprint 3)*
Intra-firm and head-to-head entity comparisons. Available to admin role.

**Planned content:**
- Intra-firm team comparison: side-by-side radar/bar of advisors within a firm
- Entity-to-entity comparison: overlay two entities for head-to-head dimension comparison
- Uses synthetic partner group data (with disclaimer) until Wealthtender provides real firm-advisor associations

### Methodology (`/methodology`)
Documentation of analytical methods used in the dashboard. Admin-only.

---

## 8. API Endpoints

All endpoints are prefixed with `/api/`. Authentication via `X-API-Key` header (see [Auth & Security](#13-auth--security)).

### Core

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Health check (always open) |
| `GET /api/metadata/latest` | Artifact metadata and timestamps |
| `GET /api/stopwords` | Default stopword list for EDA |

### EDA

| Endpoint | Description |
|----------|-------------|
| `GET /api/eda/charts` | All EDA chart data. Accepts `scope`, `firm_id`, `advisor_id`, `date_start`, `date_end`, `min_rating`, `token_cat`, `review_cat`, `ngram_n`, `ngram_topn`, `exclude_stopwords`, `custom_stopwords` |

### Advisor DNA

| Endpoint | Description |
|----------|-------------|
| `GET /api/advisor-dna/macro` | Sampled review-dimension scores for macro view |
| `GET /api/advisor-dna/macro-totals` | Dimension totals across all reviews. Accepts `min_peer_reviews` for premier pool filtering |
| `GET /api/advisor-dna/entities` | List of firms or advisors (`entity_type` param) |
| `GET /api/advisor-dna/entity-reviews` | Reviews for a specific entity (`advisor_id` param) |
| `GET /api/advisor-dna/advisor-scores` | Aggregated dimension scores (`advisor_id`, `method` params) |
| `GET /api/advisor-dna/percentile-scores` | Percentile rank scores within peer group. Accepts `min_peer_reviews` for premier pool |
| `GET /api/advisor-dna/population-medians` | Population median scores by method |
| `GET /api/advisor-dna/method-breakpoints` | Percentile breakpoints for tier labeling (`method`, `entity_type` params) |
| `GET /api/advisor-dna/review/{review_idx}` | Single review detail by index |

### Firm (Legacy)

| Endpoint | Description |
|----------|-------------|
| `GET /api/firms` | List of firms |
| `GET /api/firm/{firm_id}/summary` | Firm summary |
| `GET /api/firm/{firm_id}/dimensions` | Firm dimension scores |
| `GET /api/firm/{firm_id}/advisors` | Advisors within a firm |
| `GET /api/firm/{firm_id}/advisor/{advisor_id}` | Individual advisor detail |
| `GET /api/firm/{firm_id}/benchmarks` | Firm benchmark data |
| `GET /api/firm/{firm_id}/personas` | Firm persona clusters |
| `GET /api/reviews/{review_id}` | Single review by ID |

---

## 9. Artifacts & Data Pipeline

### EDA Artifacts (`artifacts/macro_insights/`)

Pre-built from the EDA notebook. The dashboard reads these on startup.

| File | Purpose |
|------|---------|
| `reviews_clean.csv` | Cleaned review data (text, ratings, metadata) |
| `eda/eda_summary.json` | Summary statistics |
| `eda/coverage.json` | Data coverage metrics |
| `quality/quality_summary.json` | Quality report |
| `quality/raw_file_meta.json` | Raw file metadata |
| `quality/missing_report.csv` | Missing data report |
| `lexical/top_tokens.csv` | Top unigram tokens |
| `lexical/top_bigrams.csv` | Top bigram tokens |

### Scoring Artifacts (`artifacts/scoring/`)

Generated by the collaborator notebook (`notebooks/collaborator/query_embeddings_vs_review_embeddings.ipynb`). This notebook:
1. Loads pre-computed review embeddings and advisor embeddings
2. Encodes six dimension query strings using `sentence-transformers`
3. Computes cosine similarity between each review embedding and each query
4. Aggregates scores at the entity level using mean, penalized, and weighted methods
5. Exports two CSV files

| File | Contents |
|------|----------|
| `review_dimension_scores.csv` | Per-review similarity scores for 6 dimensions, with review metadata |
| `advisor_dimension_scores.csv` | Entity-level aggregated scores (mean, penalized, weighted) for each dimension |

To regenerate scoring artifacts, run the notebook end-to-end and copy the outputs to `artifacts/scoring/`.

---

## 10. Environment Variables

All settings have sensible defaults for local development — you don't need to configure anything to run locally.

See `.env.example` for the full list. On Render, set these in each service's **Environment** tab.

| Variable | Default | Set On | What It Does |
|----------|---------|--------|--------------|
| `API_BASE` | `http://localhost:8000` | Dashboard | URL the dashboard uses to reach the API |
| `PORT` | `8050` / `8000` | Both | Listening port (Render injects this automatically) |
| `API_KEY` | *(empty — auth off)* | Both | Shared secret between services (see [Auth](#13-auth--security)) |
| `ADMIN_PASSWORD` | `WT$msba2026` | Dashboard | Password for the admin portal on the splash page |

---

## 11. Docker Compose (Alternative)

If you prefer Docker over the `run.sh` script:

```bash
docker compose up --build     # first time or after code changes
docker compose up              # subsequent runs
docker compose down            # stop everything
```

Dashboard at http://localhost:8050, API at http://localhost:8000.

---

## 12. Deployment

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

## 13. Auth & Security

There are two layers of authentication:

### API Key (service-to-service)

The API rejects any request without a valid `X-API-Key` header. The dashboard sends this header automatically. Both services read the key from the `API_KEY` environment variable. An API key is already set on both Render services.

- **Locally:** `API_KEY` is empty by default, so auth is skipped. Nothing to configure.
- **On Render:** The `API_KEY` is already configured on both `wt-api` and `wt-dash`. To rotate it, update the value on both services in their Environment tabs — they must always match.
- The `/api/health` endpoint is always open (required for health checks).

### Admin Password (user-facing)

The admin portal on the splash page requires a password before granting access. The password is read from `ADMIN_PASSWORD` (defaults to `WT$msba2026`). This is already set on Render. The check is server-side and cannot be bypassed from the browser.

---

## 14. Production Handoff

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

## 15. Tech Stack & Versions

### Production Dependencies (`requirements.txt`)

| Package | Version | Role |
|---------|---------|------|
| `dash` | 2.16.1 | Frontend framework (Plotly Dash) |
| `plotly` | 5.20.0 | Chart library (bar, radar/spider, histogram charts) |
| `fastapi` | 0.119.0 | Backend API framework |
| `uvicorn` | 0.29.0 | ASGI server for FastAPI |
| `pydantic` | 2.11.0 | Data validation for API models |
| `pandas` | 2.2.2 | Data manipulation and artifact loading |
| `requests` | 2.31.0 | HTTP client (dashboard to API) |
| `gunicorn` | ≥21.2.0 | Production WSGI server for Dash |

### Offline / Notebook Dependencies

These are used only for regenerating scoring artifacts, not at runtime:

- `sentence-transformers` — Encodes dimension query strings into embeddings
- `numpy` — Array operations for cosine similarity
- `pyarrow` — Parquet file I/O for embedding data

### Infrastructure

- **Containerization:** Docker (multi-stage builds)
- **Deployment:** Render (via `render.yaml` blueprint)
- **Local dev:** `run.sh` / `run.ps1` launcher scripts or `docker compose`
