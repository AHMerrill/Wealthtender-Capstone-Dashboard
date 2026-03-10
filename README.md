# Wealthtender Advisor Review Analytics Dashboard

A two-service analytics platform that turns financial advisor client reviews into actionable dimension-level scores, benchmarks, and leaderboards using NLP-derived cosine similarity scoring.

**Live:** [https://wt-dash.onrender.com](https://wt-dash.onrender.com)

> **Note:** The current Render deployment is temporary. The API and dashboard will need to be re-hosted on Wealthtender's own infrastructure (or any Docker-compatible platform) for long-term use. See [Deployment](#12-deployment) and [Integration Notes](#14-integration-notes-wordpress--embedding) for migration guidance.

---

## Downloading This Repository

**With Git installed:**
```bash
git clone https://github.com/AHMerrill/Wealthtender-Capstone-Dashboard.git
```

**Without Git / without a GitHub account:**

Download the full repository as a ZIP file directly from your browser — no GitHub account required:

1. Go to: [https://github.com/AHMerrill/Wealthtender-Capstone-Dashboard](https://github.com/AHMerrill/Wealthtender-Capstone-Dashboard)
2. Click the green **"Code"** button near the top-right
3. Select **"Download ZIP"**
4. Extract the ZIP to your desired location

Alternatively, download via direct link:
```
https://github.com/AHMerrill/Wealthtender-Capstone-Dashboard/archive/refs/heads/main.zip
```

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Project Structure](#2-project-structure)
3. [Dashboard Pages](#3-dashboard-pages)
4. [API Endpoints](#4-api-endpoints)
5. [Artifacts & Data Pipeline](#5-artifacts--data-pipeline)
6. [Shared Constants & Branding](#6-shared-constants--branding)
7. [Environment Variables](#7-environment-variables)
8. [Requirements](#8-requirements)
9. [Running Locally](#9-running-locally)
10. [Docker Compose](#10-docker-compose)
11. [License & Attribution](#11-license--attribution)
12. [Deployment](#12-deployment)
13. [Auth & Security](#13-auth--security)
14. [Integration Notes (WordPress / Embedding)](#14-integration-notes-wordpress--embedding)
15. [Production Auth Upgrade Roadmap](#15-production-auth-upgrade-roadmap)
16. [Key Links](#16-key-links)

---

## 1. Architecture Overview

The system is split into two independent services that communicate over REST:

```
┌──────────────────────┐       HTTP/JSON        ┌──────────────────────┐
│   Plotly Dash UI     │ ────────────────────▸   │   FastAPI Backend    │
│   (dashboard/)       │   X-API-Key header      │   (api/)             │
│                      │ ◂────────────────────   │                      │
│  • Multi-page app    │                         │  • Serves pre-built  │
│  • Sidebar + nav     │                         │    artifacts as JSON  │
│  • Role-based access │                         │  • Scoring, filtering │
│  • Interactive charts │                         │  • EDA, benchmarks   │
└──────────────────────┘                         └──────────────────────┘
        Port 8050                                        Port 8000
```

Both services are containerized with separate Dockerfiles and can be deployed to any Docker-compatible host (Render, Railway, Fly.io, AWS ECS, GCP Cloud Run, etc.).

**Why two services?** The API can be consumed independently — by the dashboard, by Wealthtender's own WordPress site, or by any other frontend. The dashboard is a read-only visualization layer.

---

## 2. Project Structure

```
api/                          FastAPI backend
  main.py                     All API routes + middleware
  services/
    artifacts.py              ArtifactStore — data loading, scoring, filtering

dashboard/                    Plotly Dash frontend
  app.py                      Main layout, sidebar, navigation, core callbacks
  constants.py                Shared dimension constants (DIMENSIONS, DIM_LABELS, etc.)
  branding.py                 Colors, fonts, CSS variables (from Brandbook)
  roles.py                    Role-based access configuration
  components/
    eda_content.py            EDA page charts and callback logic
  pages/
    splash.py                 Login / role selection page
    advisor_dna.py            Advisor DNA — bar/spider charts, evidence cards, drill-down
    eda.py                    EDA page registration (content lives in eda_content.py)
    benchmarks.py             Benchmarks page — premier pool analytics
    leaderboard.py            Leaderboard page — top entities per dimension
    comparisons.py            Comparisons page — intra-firm and head-to-head
    methodology.py            Methodology documentation page
  plots/
    eda_charts.py             EDA Plotly chart builders
  services/
    api.py                    HTTP client for the FastAPI backend (with retry + warm-up)
    brand.py                  Brand asset loader

artifacts/                    Pre-built data artifacts (loaded at startup)
  macro_insights/             EDA artifacts (reviews, lexical, quality)
  scoring/
    review_dimension_scores.csv    Per-review cosine similarity scores (6 dimensions)
    advisor_dimension_scores.csv   Aggregated entity-level scores (mean, penalized, weighted)
    partner_groups_mock.csv        Synthetic firm-advisor associations (dev/demo)
  metadata.json               Artifact manifest

assets/                       Static files served by Dash
  brand/                      Logo SVGs (mark, wordmark, full)
  theme.css                   Auto-generated CSS (written by branding.py at startup)
  favicon.png

data_contract/                Schema expectations for artifacts
notebooks/collaborator/       Scoring notebook (generates scoring artifacts)

Dockerfile.api                Container image for the API
Dockerfile.dashboard          Container image for the dashboard
docker-compose.yml            Local Docker setup
render.yaml                   Render deployment blueprint
gunicorn.conf.py              Gunicorn worker config (API warm-up in post_fork)
run.sh / run.ps1              Local dev launcher (macOS/Linux / Windows)
requirements.txt              Python dependencies (pinned)
```

---

## 3. Dashboard Pages

### Home (`/`)
Role selection splash page. Admin users enter a password; firm users select their firm from a dropdown. This gates access to all other pages.

### Advisor DNA (`/advisor-dna`)
Core analytical page. Three views:

- **Macro** — Dimension distribution across all reviews. Bar/Spider toggle, All/Premier pool selector.
- **Entity** — Entity-specific bar chart with tier labels (Very Strong / Strong / Moderate / Foundational), spider toggle, and premier pool comparison. Clickable dimension cards with top-3 evidence reviews.
- **Review** — Full review text with per-dimension spider chart.

Confidence system: <10 reviews = amber "Directional Insights" banner; 20+ = green "Robust Data" badge + premier pool.

Three scoring methods: Mean, Penalized (consistency penalty), Weighted (time-decay).

### EDA (`/eda`)
Exploratory data analysis of the review corpus: volume over time, rating distributions, word counts, n-gram analysis. Sidebar filters for entity, date range, rating, word count, review count, and stopwords.

### Benchmarks (`/benchmarks`)
Premier pool deep-dive: composition KPIs (All vs Premier), dimension score distributions with histograms, and a peer percentile comparison table when an entity is selected. Defaults to Premier pool view.

### Leaderboard (`/leaderboard`)
Top-N entities per dimension with horizontal bar charts showing **percentile rank** (ordinal labels like "92nd"). Includes a "Composite (All Dimensions)" option computed server-side. Click up to 2 entities to compare spider profiles and percentile tables below. Unselected bars fade to 30% opacity; raw scores shown on hover.

### Comparisons (`/comparisons`)
Two sections:
1. **Head-to-Head** (real data) — Select any two entities for overlaid spider + diff table.
2. **Team Comparison** (mocked data, with dev banner) — Select a partner group to see side-by-side radar/bar of all advisors. Uses synthetic `partner_group` associations until Wealthtender provides the real export.

### Methodology (`/methodology`)
Documentation of analytical methods, scoring approaches, and data pipeline. Collapsible accordion sections.

---

## 4. API Endpoints

All endpoints prefixed with `/api/`. Authentication via `X-API-Key` header (see [Auth & Security](#12-auth--security)).

### Core
| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Health check (always open, no auth) |
| `GET /api/metadata/latest` | Artifact metadata and timestamps |
| `GET /api/stopwords` | Default stopword list for EDA |

### EDA
| Endpoint | Description |
|----------|-------------|
| `GET /api/eda/charts` | All EDA chart data. Accepts `scope`, `firm_id`, `advisor_id`, `date_start`, `date_end`, `min_rating`, `token_cat`, `review_cat`, `ngram_n`, `ngram_topn`, `exclude_stopwords`, `custom_stopwords`, `time_freq` |

### Advisor DNA
| Endpoint | Description |
|----------|-------------|
| `GET /api/advisor-dna/macro` | Sampled review-dimension scores for macro view |
| `GET /api/advisor-dna/macro-totals` | Dimension totals across all reviews. `min_peer_reviews` param |
| `GET /api/advisor-dna/entities` | List of firms and advisors |
| `GET /api/advisor-dna/entity-reviews` | Reviews for a specific entity (`entity_id` param) |
| `GET /api/advisor-dna/advisor-scores` | Enriched dimension scores: raw + percentile + normalized + tier + composite (`entity_id`, `method`) |
| `GET /api/advisor-dna/percentile-scores` | Percentile rank within peer group. `min_peer_reviews` param |
| `GET /api/advisor-dna/method-breakpoints` | Percentile breakpoints for tier labeling (`method`, `entity_type`) |
| `GET /api/advisor-dna/review/{review_idx}` | Single review detail by index |

### Benchmarks / Leaderboard / Comparisons
| Endpoint | Description |
|----------|-------------|
| `GET /api/benchmarks/pool-stats` | Pool composition stats (All vs Premier) |
| `GET /api/benchmarks/distributions` | Dimension score distributions (`method`, `entity_type`, `min_peer_reviews`) |
| `GET /api/leaderboard` | Enriched top-N per dimension (`method`, `entity_type`, `min_peer_reviews`, `top_n`, `dimension`). `dimension` can be `"all"` (default), a single dim key, or `"composite"`. Each entry includes `score`, `percentile`, `normalized`, `tier`. |
| `GET /api/comparisons/partner-groups` | List of partner groups |
| `GET /api/comparisons/partner-group/{group_code}` | Members of a partner group (`method`) |
| `GET /api/comparisons/entities` | Compare entities (`entity_ids[]`, `method`) — returns enriched profiles |
| `GET /api/comparisons/head-to-head` | Full head-to-head comparison (`entity_a`, `entity_b`, `method`). Returns both enriched profiles + diffs for raw, percentile, and normalized per dimension. |

### Legacy Firm Endpoints
These endpoints exist in the API but are not currently used by the dashboard frontend. They may be useful for external integrations:

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

## 5. Artifacts & Data Pipeline

The system operates on pre-built artifacts — no model inference happens at runtime.

### EDA Artifacts (`artifacts/macro_insights/`)
Pre-built from the EDA notebook. The API loads these into memory on startup.

| File | Purpose |
|------|---------|
| `reviews_clean.csv` | Cleaned review data (text, ratings, metadata) |
| `eda/eda_summary.json` | Summary statistics |
| `eda/coverage.json` | Data coverage metrics |
| `quality/quality_summary.json` | Quality report |
| `lexical/top_tokens.csv` | Top unigram tokens |
| `lexical/top_bigrams.csv` | Top bigram tokens |

### Scoring Artifacts (`artifacts/scoring/`)
Generated by the collaborator notebook (`notebooks/collaborator/query_embeddings_vs_review_embeddings.ipynb`):

1. Loads pre-computed review embeddings
2. Encodes six dimension query strings using `sentence-transformers`
3. Computes cosine similarity between each review embedding and each query
4. Aggregates at entity level using mean, penalized, and weighted methods
5. Exports two CSV files

| File | Contents |
|------|----------|
| `review_dimension_scores.csv` | Per-review similarity scores for 6 dimensions |
| `advisor_dimension_scores.csv` | Entity-level aggregated scores (mean, penalized, weighted) |
| `partner_groups_mock.csv` | Synthetic partner group assignments (for team comparison dev/demo) |

To regenerate scoring artifacts, run the notebook end-to-end and copy outputs to `artifacts/scoring/`.

### Future: Live Data Pipeline

The current system is snapshot-based — artifacts are static files baked into the API Docker image at build time. To update the data, you rerun the scoring notebook, replace the CSVs, and rebuild the container.

For a production system with continuously incoming reviews, the natural upgrade is to swap the flat-file storage for a database (e.g., PostgreSQL). The only file that changes is `api/services/artifacts.py` — replace the CSV reads with database queries. The API endpoints, request parameters, and JSON response shapes all stay identical, so the dashboard (or any other frontend consuming the API) requires zero changes.

A typical live pipeline would look like: new reviews land in the database → a scheduled job reruns the scoring pipeline and writes updated scores back to the database → the API queries the database on each request instead of reading from memory. The API is designed to be storage-agnostic, so this is a backend-only migration.

### Six Dimensions
| Key | Label |
|-----|-------|
| `trust_integrity` | Trust & Integrity |
| `listening_personalization` | Customer Empathy & Personalization |
| `communication_clarity` | Communication Clarity |
| `responsiveness_availability` | Responsiveness |
| `life_event_support` | Life Event Support |
| `investment_expertise` | Investment Expertise |

### Known Limitations of Cosine Similarity Scoring

Cosine similarity measures **semantic overlap** between a review's language and each dimension's query definition. This is fundamentally different from understanding what a review *means*. Key implications:

- **Short reviews score low regardless of sentiment.** A five-star review saying "Great advisor, highly recommend!" has too few tokens to produce meaningful cosine similarity against any dimension's detailed query text. The model rewards *specificity and volume of language*, not positive sentiment.
- **Implied meaning is invisible.** A review like "She is patient and understanding" clearly implies empathy and trust to a human reader, but the model only detects direct semantic overlap with the dimension query strings. If the review doesn't use vocabulary close to the query text, the score stays low.
- **Entities with many short reviews rank lower than entities with fewer but longer, more detailed reviews.** This creates a systematic bias toward entities whose clients write more descriptive feedback.
- **Tier labels can be misleading.** An entity rated "Moderate" on Trust & Integrity may have universally positive reviews that simply don't use trust-specific language. "Moderate" reflects *how much trust was explicitly discussed*, not whether clients actually trust the advisor.

These are inherent limitations of embedding-based cosine similarity — not bugs. The approach works best when reviews are detailed enough to contain dimension-specific language. For a more robust alternative, see the next section.

### Alternative: LLM-Based Scoring Pipeline

A large language model (LLM) can address the limitations above by *reading and reasoning about* each review rather than measuring surface-level semantic overlap. Here is an outline of how such a pipeline would work:

**Step 1: Structured Review Analysis**
For each review, prompt an LLM (e.g., GPT-4, Claude) with the review text and the six dimension definitions. Ask it to return a structured JSON response identifying which dimensions are discussed (explicitly or implicitly), a 1-5 score per dimension, and a brief justification for each score. Reviews that don't mention a dimension get a null rather than a low score — this distinguishes "not discussed" from "discussed negatively."

**Step 2: Confidence-Weighted Aggregation**
At the entity level, aggregate dimension scores across all reviews using only reviews where that dimension was identified as present. This avoids the current problem where short positive reviews drag down an entity's score by contributing near-zero similarity on dimensions that simply weren't mentioned. Weight by review length, recency, or LLM confidence as appropriate.

**Step 3: Calibration**
Use a sample of human-labeled reviews to calibrate the LLM's scores. Measure agreement between human raters and the model, adjusting the prompt or scoring rubric until inter-rater reliability is acceptable. This step is critical for stakeholder trust.

**Step 4: Hybrid Approach (Optional)**
Combine embedding-based scores (fast, cheap, deterministic) with LLM-based scores (slower, costlier, more accurate) by using embeddings as a first pass and LLM analysis for reviews that score ambiguously or for entities near tier boundaries.

**Cost and Latency Considerations:**
LLM scoring is significantly more expensive than cosine similarity (~$0.01-0.05 per review vs. effectively free). For Wealthtender's current corpus (~4,200 reviews), a full LLM scoring run would cost roughly $40-200 depending on the model and prompt length. This is a one-time batch cost, not per-request — scored results would be stored in a database and served by the same API layer. Incremental scoring of new reviews as they arrive would cost fractions of a cent each.

---

## 6. Shared Constants & Branding

**`dashboard/constants.py`** — Single source of truth for dimension keys, labels, short names, and colors. All page files import from here rather than defining their own copies.

**`dashboard/branding.py`** — Colors (`COLORS`), data-viz palette (`DATA_VIZ_PALETTE`), font family, and full CSS theme. The `ensure_theme_css()` function auto-writes `assets/theme.css` at startup, so the CSS stays in sync with the Python constants.

**`dashboard/roles.py`** — Role definitions (`admin`, `firm`) with page access lists. When Wealthtender integrates real auth, this is the file to edit.

---

## 7. Environment Variables

All settings have sensible defaults for local development — zero configuration needed to run locally.

| Variable | Default | Set On | Purpose |
|----------|---------|--------|---------|
| `API_BASE` | `http://localhost:8000` | Dashboard | URL the dashboard uses to reach the API |
| `PORT` | `8050` / `8000` | Both | Listening port (Render injects automatically) |
| `API_KEY` | *(empty — auth off)* | Both | Shared secret between services |
| `ADMIN_PASSWORD` | `WT$msba2026` | Dashboard | Password for the admin portal |

See `.env.example` for the full list with comments.

---

## 8. Requirements

**Runtime:** Python 3.9+ (3.11 or 3.12 preferred)

| Package | Version | Role |
|---------|---------|------|
| `dash` | 2.16.1 | Frontend framework (Plotly Dash) |
| `plotly` | 5.20.0 | Chart library |
| `fastapi` | 0.119.0 | Backend API framework |
| `uvicorn` | 0.29.0 | ASGI server for FastAPI |
| `pydantic` | 2.11.0 | Data validation |
| `pandas` | 2.2.2 | Data manipulation and artifact loading |
| `requests` | 2.31.0 | HTTP client (dashboard → API) |
| `gunicorn` | ≥21.2.0 | Production WSGI server for Dash |

**Offline / Notebook only** (not needed at runtime): `sentence-transformers`, `numpy`, `pyarrow`

---

## 9. Running Locally

```bash
# macOS / Linux
bash run.sh

# Windows PowerShell
.\run.ps1
```

Opens at **http://localhost:8050**. The first run creates a virtual environment and installs dependencies (~1 min). Subsequent runs start in seconds. `Ctrl+C` stops both services.

---

## 10. Docker Compose

```bash
docker compose up --build     # first time or after code changes
docker compose up              # subsequent runs
docker compose down            # stop
```

Dashboard at `http://localhost:8050`, API at `http://localhost:8000`.

---

## 11. License & Attribution

This project is licensed under the **Apache License 2.0** — see [LICENSE](./LICENSE) for the full text.

**What this means:** You are free to use, modify, and redistribute this code, including for commercial purposes, provided you:

- Retain the copyright notice and LICENSE file in all copies
- Include the [NOTICE](./NOTICE) file in any distribution or derivative work
- Clearly state any modifications you have made
- Provide attribution to the original authors and contributors

The NOTICE file contains the required attribution text and the full list of contributors. If you deploy a modified version, the NOTICE and LICENSE must travel with it.

**Built by** the UT Austin McCombs School of Business MSBA Capstone Team (2026) in partnership with Wealthtender, with significant development assistance from Claude (Anthropic).

---

## 12. Deployment

Both services are containerized and deploy to any Docker-compatible host, including alongside an existing WordPress installation. **The current Render deployment is temporary** — when migrating to Wealthtender infrastructure, follow the same steps on any platform (AWS ECS, GCP Cloud Run, Railway, Fly.io, a WordPress-adjacent VPS, etc.). See [Integration Notes (WordPress / Embedding)](#14-integration-notes-wordpress--embedding) for WordPress-specific deployment patterns.

**Steps for any platform:**
1. Deploy the API using `Dockerfile.api`
2. Deploy the dashboard using `Dockerfile.dashboard`
3. Set `API_BASE` on the dashboard to the API's public URL
4. Generate a random `API_KEY` and set the same value on both services
5. Set `ADMIN_PASSWORD` on the dashboard

A `render.yaml` blueprint is included for Render. The project is currently deployed there:

| Service | URL |
|---------|-----|
| `wt-api` | `https://wt-api-hdji.onrender.com` |
| `wt-dash` | `https://wt-dash.onrender.com` |

These URLs will change when the project is migrated off Render. Update `API_BASE` on the dashboard accordingly.

---

## 13. Auth & Security

### API Key (service-to-service)
The API rejects any request without a valid `X-API-Key` header. The dashboard sends this automatically. Both services read from `API_KEY` env var. Locally, `API_KEY` is empty so auth is skipped. `/api/health` is always open.

### Admin Password (user-facing)
The splash page admin portal requires `ADMIN_PASSWORD`. The check is server-side and cannot be bypassed from the browser.

---

## 14. Integration Notes (WordPress / Embedding)

The API and dashboard are standalone services that need to be hosted somewhere accessible. The current Render deployment is a temporary development host — for production, Wealthtender will need to deploy both Docker containers to their own infrastructure. The dashboard is a standalone web application. There are several ways to integrate it with an existing WordPress site:

### Option A: iframe Embed (Simplest)
Embed the entire dashboard (or specific pages) inside a WordPress page using an `<iframe>`:
```html
<iframe src="https://wt-dash.onrender.com/advisor-dna"
        width="100%" height="900px" frameborder="0"
        style="border: none; border-radius: 8px;">
</iframe>
```
This works immediately with no code changes. The dashboard runs on its own domain and renders inside the WordPress page. Pros: zero integration effort. Cons: separate auth context, no deep WordPress theming.

### Option B: API-Only Integration
Ignore the Dash frontend entirely and consume the FastAPI backend directly from WordPress (or any frontend). The API returns pure JSON — build custom WordPress templates, React components, or any other frontend that calls:
```
GET https://wt-api-hdji.onrender.com/api/advisor-dna/advisor-scores?entity_id=XYZ&method=mean
```
This gives full control over presentation and lets the data live natively inside WordPress templates.

### Option C: Subdomain / Reverse Proxy
Run the dashboard on a subdomain (e.g., `analytics.wealthtender.com`) and link to it from the main site. A reverse proxy (Nginx, Cloudflare, etc.) can route traffic seamlessly. This is the most production-grade approach for a "feels like one site" experience.

### Compatibility Notes
- The Dash frontend is pure Python/HTML/JS — no WordPress PHP dependencies
- The FastAPI backend is stateless and serves JSON over HTTP — works with any client
- Both services are containerized, so they deploy independently of the WordPress stack
- CORS is currently set to `allow_origins=["*"]` — tighten to your production domain when going live
- The dashboard's CSS and branding (`dashboard/branding.py`) can be adjusted to match Wealthtender's WordPress theme colors

---

## 15. Production Auth Upgrade Roadmap

When Wealthtender's engineering team replaces the prototype auth:

| What to Change | Current Approach | Replace With |
|----------------|-----------------|--------------|
| Admin login | Shared password | SSO (Okta, Auth0, Azure AD, etc.) |
| Role assignment | User clicks card on splash page | Role from SSO identity token |
| Firm ID | User picks from dropdown | Firm ID from SSO claims or DB lookup |
| API auth | Shared `X-API-Key` header | JWT validation or OAuth2 client credentials |
| CORS origins | `allow_origins=["*"]` | Restrict to production domain |

**Key files to modify:**

| File | What Lives There |
|------|-----------------|
| `dashboard/app.py` | `user-role` store and `_get_role_and_firm()` — central auth seam |
| `dashboard/pages/splash.py` | Password form and firm picker — replace with SSO redirect |
| `dashboard/roles.py` | Role definitions and page permissions |
| `api/main.py` | `X-API-Key` middleware — swap for JWT/OAuth validation |

---

## 16. Key Links

| Resource | URL |
|----------|-----|
| Live Dashboard | [wt-dash.onrender.com](https://wt-dash.onrender.com) |
| Live API | [wt-api-hdji.onrender.com/api/health](https://wt-api-hdji.onrender.com/api/health) |
| GitHub Repo | [github.com/AHMerrill/Wealthtender-Capstone-Dashboard](https://github.com/AHMerrill/Wealthtender-Capstone-Dashboard) |
| Render Dashboard | [dashboard.render.com](https://dashboard.render.com) |
| Changelog | [CHANGELOG.md](./CHANGELOG.md) |
| Data Contract | [data_contract/README.md](./data_contract/README.md) |
| License | [LICENSE](./LICENSE) (Apache 2.0) |
| Attribution Notice | [NOTICE](./NOTICE) |
| Wealthtender | [wealthtender.com](https://wealthtender.com) |
