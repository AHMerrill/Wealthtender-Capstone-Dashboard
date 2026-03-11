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

<a id="top"></a>

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Project Structure](#2-project-structure)
3. [Dashboard Pages](#3-dashboard-pages)
4. [API Endpoints](#4-api-endpoints)
5. [Analysis Pipeline & Artifacts](#5-analysis-pipeline--artifacts)
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

<sup>[back to top](#top)</sup>

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

pipeline/                     Reproducible analysis pipeline (Python package)
  config.py                   Paths, constants, dimension queries, stopwords, test-account list
  clean.py                    Stage 1: raw CSV → cleaned artifacts
  embed.py                    Stage 2 + 2b: embeddings, advisor aggregation, weighted-by-time pass
  score.py                    Stage 3: embeddings → dimension similarity scores
  enrich_comparisons.py       Side-step: mock partner group generation (deletable)
  run.py                      CLI orchestrator (--stage, --full, --validate)

data/
  raw/                        Raw Wealthtender export (single CSV)
  intermediate/               Large intermediate files (gitignored)

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
run_api_dashboard.sh / .ps1   Start API + dashboard locally (macOS/Linux / Windows)
run_data_pipeline.sh / .ps1   Run the data pipeline (macOS/Linux / Windows)
requirements.txt              Runtime dependencies (API + dashboard)
requirements-pipeline.txt     Pipeline dependencies (includes runtime deps)
```

<sup>[back to top](#top)</sup>

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

<sup>[back to top](#top)</sup>

---

## 4. API Endpoints

All endpoints prefixed with `/api/`. Authentication via `X-API-Key` header (see [Auth & Security](#13-auth--security)).

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

<sup>[back to top](#top)</sup>

---

## 5. Analysis Pipeline & Artifacts

The system operates on pre-built artifacts — no model inference happens at runtime. The full analysis pipeline is packaged as a standalone Python module (`pipeline/`) that reads a single raw CSV and produces all CSV/JSON artifacts the API needs. The original Jupyter notebooks remain in the repo for reference, but `pipeline/` is the canonical, reproducible way to regenerate artifacts.

### Running the Pipeline

```bash
python -m pipeline.run                 # run all stages: clean → embed → score → enrich
python -m pipeline.run --full          # force full re-embed (ignore existing embeddings)
python -m pipeline.run --stage clean   # run only Stage 1
python -m pipeline.run --stage embed   # run only Stage 2
python -m pipeline.run --stage score   # run only Stage 3
python -m pipeline.run --stage enrich  # run only the comparisons enrichment side-step
python -m pipeline.run --validate      # compare outputs against artifacts_backup/
```

By default, Stage 2 uses **incremental append** mode: it hashes each review (using `advisor_id`, `review_text_raw`, `review_date`, and `reviewer_name`), compares against existing embeddings, and only encodes new reviews. Previously embedded reviews are preserved. Use `--full` to force a complete re-embed from scratch (e.g., after changing the embedding model).

**Requirements:** Runtime deps are in `requirements.txt`. Pipeline-specific deps (not needed at runtime) are in `requirements-pipeline.txt`: `sentence-transformers`, `nltk`, `numpy`, `pandas`, `pyarrow`, `torch`

### Pipeline Overview

```
data/raw/wealthtender_reviews.csv         (single raw CSV from Wealthtender)
    │
    ▼
┌──────────────────────────────────────────────────────────┐
│  Stage 1: Clean                                          │
│  📄 pipeline/clean.py                                    │
│                                                          │
│  • Standardize columns (advisor_id, review_text_raw)     │
│  • Filter out test/demo advisors (config.TEST_ADVISOR_IDS)│
│  • Normalize unicode, strip URLs/emails/boilerplate      │
│  • Compute token counts, quality summary, coverage stats │
│  • Export: reviews_clean.csv, EDA/lexical/quality JSONs  │
└──────────────────────────────────────────────────────────┘
    │  artifacts/macro_insights/reviews_clean.csv
    ▼
┌──────────────────────────────────────────────────────────┐
│  Stage 2: Embed (incremental append)                     │
│  📄 pipeline/embed.py                                    │
│                                                          │
│  • Filter dates (>2014), drop duplicates                 │
│  • Compute review_hash (SHA256 of 4 fields) per review   │
│  • Compare against existing embeddings — skip duplicates │
│  • Tokenize, remove NLTK + domain stopwords              │
│  • Strip prompt fragments and HTML entities               │
│  • Remove advisor names from review text                 │
│  • Encode NEW reviews with all-MiniLM-L6-v2 → 384-dim   │
│  • Append to accumulated embeddings file                 │
│  • Re-aggregate to advisor level (L2-norm mean + penalty)│
│  • Export: df_embeddings_MVP.csv, advisor parquets       │
│                                                          │
│  Stage 2b: Weighted-by-Time Embeddings                   │
│  (separate pass — different normalization & text proc.)   │
│  • Strip advisor name (simple full-name replacement)     │
│  • Encode with normalize_embeddings=False                │
│  • Half-life decay weights: 0.5^(age/2yr)               │
│  • Weighted-mean advisor aggregation (NOT L2-normed)     │
│  • Export: df_advisors_weighted_time.parquet              │
└──────────────────────────────────────────────────────────┘
    │  data/intermediate/df_embeddings_MVP.csv
    │  data/intermediate/advisor_embeddings_MVP.parquet
    │  data/intermediate/df_advisors_weighted_time.parquet
    ▼
┌──────────────────────────────────────────────────────────┐
│  Stage 3: Score                                          │
│  📄 pipeline/score.py                                    │
│                                                          │
│  • Load review embeddings, parse to numpy matrix E_r     │
│  • Encode 6 dimension query strings → matrix E_q         │
│  • Cosine similarity: S = E_r @ E_q.T (review × dim)    │
│  • Advisor-level: mean, penalized, weighted similarities │
│  • Export: review_dimension_scores.csv,                   │
│           advisor_dimension_scores.csv                    │
└──────────────────────────────────────────────────────────┘
    │  artifacts/scoring/*.csv
    ▼
┌──────────────────────────────────────────────────────────┐
│  Side-step: Enrich Comparisons (deletable scaffolding)   │
│  📄 pipeline/enrich_comparisons.py                       │
│                                                          │
│  • Auto-detects partner_group column in reviews          │
│  • If present: writes real partner_groups.csv            │
│  • If absent: generates mock partner_groups_mock.csv     │
│  • Delete this file with zero impact on clean/embed/score│
└──────────────────────────────────────────────────────────┘
    │  artifacts/scoring/partner_groups_mock.csv
    ▼
┌──────────────────────────────────────────────────────────┐
│  Runtime: API + Dashboard                                │
│  📄 api/services/artifacts.py                            │
│                                                          │
│  • Loads CSVs/JSONs into memory at startup               │
│  • Computes percentiles, normalized scores, tier labels  │
│  • Serves enriched JSON via REST endpoints               │
│  • Dashboard renders interactive visualizations           │
└──────────────────────────────────────────────────────────┘
```

### Following a Review Through the Pipe

To make the pipeline concrete, here is what happens to a single real review as it flows through every stage. The review enters the pipeline as a row in `data/raw/wealthtender_reviews.csv`:

> **ID** 55476 | **advisor** Omar A. Morillo, CFP® | **rating** 5 | **text** "Omar Morillo is an exceptional wealth advisor AND person..."

**Stage 1 — clean.py** reads the raw CSV into a DataFrame. It creates `advisor_id` from the `notification_page` URL (`https://wealthtender.com/financial-advisors/omar-a-morillo-cfp-chfc-aif/`), checks the ID against `config.TEST_ADVISOR_IDS` (not a test account — it passes), copies the raw text into `review_text_clean`, then runs ten normalization steps: unicode normalization (NFKC), line break flattening, URL/email removal, bullet/glyph removal, boilerplate stripping ("This reviewer received no compensation..."), whitespace normalization, punctuation de-duplication, letter stretching collapse, and lowercasing. It computes token counts on both raw and cleaned text, drops reviews under 5 characters, then exports the cleaned DataFrame to `artifacts/macro_insights/reviews_clean.csv`. Our review survives as a row with ~85 clean tokens.

**Stage 2 — embed.py** loads `reviews_clean.csv`, filters to reviews after 2014, drops duplicates, and tokenizes the clean text. It removes NLTK English stopwords plus domain-specific terms (e.g., "advisor," "financial," "wealth") and strips platform prompt fragments ("things you value in your advisor..."). It decodes HTML entities, normalizes whitespace again, then removes the advisor's name from the text — "omar," "morillo," and the full name phrase are all replaced with spaces so the embedding captures what the client *said*, not who they said it about. The resulting clean text is encoded by the `all-MiniLM-L6-v2` sentence-transformer into a 384-dimensional unit vector (with `normalize_embeddings=True`). This vector is our review's embedding. The review also contributes to the advisor-level mean embedding (L2-normalized centroid of all that advisor's review vectors) and the penalized embedding (mean scaled by a staleness decay factor). These are saved to `data/intermediate/df_embeddings_MVP.csv` and `advisor_embeddings_MVP.parquet`.

**Stage 2b — embed.py (weighted-by-time)** runs a second, separate embedding pass using different settings from a collaborator's notebook. It loads the same `reviews_clean.csv` but applies only a simple full-name replacement for advisor name removal (no per-token stripping, no stopword removal on the embedding input). It encodes with `normalize_embeddings=False`, producing unnormalized vectors whose norms vary (~0.3–0.9). For each advisor, it computes a time-weighted mean embedding using half-life decay weights: recent reviews count more (w = 0.5^(age_years/2.0)). The weighted aggregation is intentionally NOT L2-normalized afterward. Diagnostic columns include effective_n_time (Kish's formula) and review date ranges. Output: `data/intermediate/df_advisors_weighted_time.parquet`.

**Stage 3 — score.py** loads the embedding CSV, parses each embedding string back to a numpy array, and stacks them into a matrix E_r. It encodes the six dimension query strings with the same model, producing a 6×384 matrix E_q. The dot product `S = E_r @ E_q.T` yields a 4579×6 matrix of cosine similarities — each cell is how closely one review aligns with one dimension. Our review scores highest on Trust & Integrity (the text mentions "honest," "trustworthy," "secure") and Listening & Personalization ("takes the time to truly listen," "tailoring advice to fit personal needs"). At the advisor level, the mean and penalized similarities are computed by dotting the advisor embedding matrices against E_q. The merged results go to `artifacts/scoring/review_dimension_scores.csv` (per-review) and `advisor_dimension_scores.csv` (per-advisor/firm).

**Runtime — api/services/artifacts.py** loads these CSVs into memory when the FastAPI server starts. When a dashboard user selects Omar Morillo, the API looks up his advisor_id, retrieves his six dimension scores, computes percentile ranks within the advisor peer group (`pandas.rank(pct=True) * 100`), min-max normalizes to 0–100, assigns tier labels (e.g., "Very Strong" if ≥75th percentile), and returns the enriched JSON. The dashboard renders this as bar charts, spider charts, and tier badges — all derived from that original raw review row.

### Pipeline Modules

| Module | Purpose |
|--------|---------|
| `pipeline/config.py` | All paths, constants, dimension queries, stopwords, cleaning patterns, and test-account exclusion list |
| `pipeline/clean.py` | Stage 1: raw CSV → `reviews_clean.csv` + EDA/quality/lexical artifacts |
| `pipeline/embed.py` | Stage 2: cleaned reviews → sentence-transformer embeddings + advisor aggregation. Stage 2b: separate weighted-by-time embedding pass |
| `pipeline/score.py` | Stage 3: embeddings → cosine similarity scores (review-level and advisor-level) |
| `pipeline/enrich_comparisons.py` | Side-step: generates mock partner group associations (deletable scaffolding) |
| `pipeline/run.py` | CLI orchestrator: runs stages in sequence, supports `--stage`, `--full`, and `--validate` flags |

### Source Notebooks (Reference Only)

The `pipeline/` package was extracted from these notebooks. They remain in the repo for provenance but are no longer needed to regenerate artifacts:

| Notebook | Location | Purpose |
|----------|----------|---------|
| **NLP I** | `notebooks/NLP_I.ipynb` | Cleaning, tokenization, stopword removal, n-gram analysis, embedding generation (Stages 1–2) |
| **Scoring** | `notebooks/collaborator/query_embeddings_vs_review_embeddings.ipynb` | Dimension scoring: cosine similarity, entity-level aggregation (Stage 3) |
| **Review Pipeline** | `notebooks/Copy of WT_Capstone_ReviewPipeline.ipynb` | Earlier version of the cleaning pipeline (Stages 1 subset) |
| **Weighted Embeddings** | `notebooks/Wealthtender_Embeddings_WT.ipynb` | Time-weighted advisor embeddings with half-life decay (Stage 2b) |
| **Scoring Exploration** | `notebooks/Scoring_Exploration.ipynb` | Experimental (KMeans, alternative scoring). Not part of production. |

### EDA Artifacts (`artifacts/macro_insights/`)

| File | Purpose |
|------|---------|
| `reviews_clean.csv` | Cleaned review data (text, ratings, metadata) |
| `eda/eda_summary.json` | Summary statistics |
| `eda/coverage.json` | Data coverage metrics |
| `quality/quality_summary.json` | Quality report |
| `quality/raw_file_meta.json` | SHA-256 hash and size of the raw input CSV |
| `lexical/top_tokens.csv` | Top unigram tokens |
| `lexical/top_bigrams.csv` | Top bigram tokens |

### Scoring Artifacts (`artifacts/scoring/`)

| File | Contents |
|------|----------|
| `review_dimension_scores.csv` | Per-review cosine similarity scores for 6 dimensions (~4,600 rows) |
| `advisor_dimension_scores.csv` | Entity-level aggregated scores: mean, penalized, weighted (~334 rows) |
| `partner_groups_mock.csv` | Synthetic firm-advisor associations for the Comparisons tab (dev/demo) |

### Intermediate Files (`data/intermediate/`)

These are large files produced by Stage 2 and consumed by Stage 3. They are gitignored:

| File | Contents |
|------|----------|
| `df_embeddings_MVP.csv` | Review-level data with 384-dim embedding vectors as strings |
| `advisor_embeddings_MVP.parquet` | Advisor-level mean and penalized embedding vectors |
| `df_advisors_weighted_time.parquet` | Advisor-level time-weighted embeddings (from collaborator) |

### Runtime Enrichment (`api/services/artifacts.py`)

The API adds three derived score representations at request time, without re-running any NLP models:

| Representation | Description |
|----------------|-------------|
| **Raw** | Original cosine similarity values (typically 0.15–0.60) |
| **Percentile** | Rank within peer group (0–100), computed via `pandas.rank(pct=True)` |
| **Normalized** | Min-max rescaled to 0–100 within the peer population |
| **Tier** | Quartile label: Very Strong (≥75th), Strong (≥50th), Moderate (≥25th), Foundational (<25th) |

### Where Data Lives and How to Change It

**Current setup (flat files, local):**
The pipeline reads from `data/raw/wealthtender_reviews.csv` and writes all outputs to `artifacts/` (final) and `data/intermediate/` (working files). The API loads from `artifacts/` at startup. Everything is local filesystem, no database involved.

**To update data:** place a new Wealthtender export in `data/raw/`, then run `python -m pipeline.run`. Stage 2 automatically detects which reviews are new and only encodes those, appending to the existing embeddings. Stages 3 and 4 re-score and re-export the full accumulated dataset to `artifacts/`.

**To migrate to a database (PostgreSQL, etc.):**
1. **Pipeline input:** In `pipeline/config.py`, change `RAW_CSV` to a connection string, and swap the `pd.read_csv` call at the top of `clean.py` with `pd.read_sql`. Everything downstream receives a DataFrame — no other pipeline code changes.
2. **Pipeline output:** After each stage, write artifacts to database tables instead of CSV files. The simplest approach: keep the pipeline writing CSVs, and add a final upload step that loads them into the database.
3. **API consumption:** In `api/services/artifacts.py`, replace CSV reads with database queries. The API endpoints, request parameters, and JSON response shapes all stay identical, so the dashboard requires zero changes.
4. **Scheduled refresh:** Set up a cron job or scheduler that runs `python -m pipeline.run` whenever new reviews arrive, then the API picks up the updated data on its next startup (or on-demand if using database queries).

The API is deliberately storage-agnostic — it receives DataFrames and serves JSON. Swapping the storage backend is a plumbing change, not an architectural one.

### Future: Live Data Pipeline

The current system is snapshot-based — artifacts are static files baked into the API Docker image at build time. For a production system with continuously incoming reviews, the natural upgrade path is: new reviews land in the database → a scheduled job reruns the pipeline stages and writes updated scores back to the database → the API queries the database on each request instead of reading from memory. This is a backend-only migration.

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

### Alternative: LLM-Enhanced Scoring Pipelines

A large language model (LLM) can address the cosine similarity limitations above by *reading and reasoning about* each review. Below are three approaches, ordered from easiest to most robust. All use a lightweight model like GPT-4o-mini or Claude Haiku. The six DNA dimensions remain the same — what changes is how reviews are scored against them.

**Option A: LLM-Expanded Embeddings (Easiest)**
Before embedding reviews, run each one through an LLM with a prompt like: "Expand this review into explicit statements about each of our 6 DNA dimensions." A short review like "they were patient and listened" becomes structured sentences about trust, communication, empathy, etc. Then embed *that* expanded text instead of the raw review. The entire downstream pipeline stays exactly the same — cosine similarity, percentiles, tiers, all of it. Zero changes to the dashboard or API. The big win is that short or vague reviews now produce meaningful scores because the LLM fills in implicit meaning before the embedding step runs.

**Option B: Score Blending (Most Robust)**
Run both pipelines independently. The current embedding pipeline produces cosine similarity scores per dimension. A separate LLM pass reads each review, rates it 0–100 on each dimension with a confidence score, and returns structured JSON. Normalize both score sets to the same 0–100 scale, then blend them — e.g., 40% embedding + 60% LLM, weighted by the LLM's confidence. Aggregate to advisor level the same as now. The embedding catches semantic similarity the LLM might miss; the LLM catches context and meaning that embeddings miss. They cover each other's blind spots. Blend weights can be calibrated against a small set of human-labeled reviews for validation.

**Option C: LLM as Confidence Filter (Most Targeted)**
Keep embedding scores as the primary method. Use the LLM only to flag reviews where the embedding is likely wrong — short reviews, ambiguous language, or reviews near tier boundaries. For flagged reviews, substitute the LLM's score; everything else keeps the fast embedding score. This minimizes LLM cost while fixing the most problematic cases. The tradeoff is defining "likely wrong" without ground truth labels.

**Shared Steps (All Options):**
- **Confidence-Weighted Aggregation:** At the entity level, weight review contributions by LLM confidence (or review length as a proxy) so detailed reviews count more than one-liners.
- **Calibration:** Use a sample of ~50-100 human-labeled reviews to tune LLM prompts, blend weights, or flagging thresholds. Measure agreement between human raters and the model. This step is critical for stakeholder trust.

**Cost Estimates (GPT-4o-mini):**
LLM scoring is a one-time batch cost, not per-request — scored results are stored and served by the same API layer. GPT-4o-mini pricing is ~$0.15/M input tokens and ~$0.60/M output tokens. Per review: ~600 input tokens (review + prompt + dimension definitions) and ~150 output tokens (structured JSON response). For the current corpus (~4,200 reviews), a full scoring run costs roughly **$1–5 total**. Incremental scoring of new reviews as they arrive costs fractions of a cent each.

**Recommended Path:** Implement Option A first (a weekend of work, biggest bang for buck), then layer on Option B if time allows. The progression from pure embeddings → LLM-expanded embeddings → hybrid blending tells a strong analytical story.

<sup>[back to top](#top)</sup>

---

## 6. Shared Constants & Branding

**`dashboard/constants.py`** — Single source of truth for dimension keys, labels, short names, and colors. All page files import from here rather than defining their own copies.

**`dashboard/branding.py`** — Colors (`COLORS`), data-viz palette (`DATA_VIZ_PALETTE`), font family, and full CSS theme. The `ensure_theme_css()` function auto-writes `assets/theme.css` at startup, so the CSS stays in sync with the Python constants.

**`dashboard/roles.py`** — Role definitions (`admin`, `firm`) with page access lists. When Wealthtender integrates real auth, this is the file to edit.

<sup>[back to top](#top)</sup>

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

<sup>[back to top](#top)</sup>

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

**Pipeline only** (in `requirements-pipeline.txt`, not needed at runtime): `sentence-transformers`, `nltk`, `numpy`, `pyarrow`, `torch`

<sup>[back to top](#top)</sup>

---

## 9. Running Locally

```bash
# macOS / Linux — start the dashboard + API
bash run_api_dashboard.sh

# Windows PowerShell
.\run_api_dashboard.ps1
```

Opens at **http://localhost:8050**. The first run creates a virtual environment and installs dependencies (~1 min). Subsequent runs start in seconds. `Ctrl+C` stops both services.

To regenerate artifacts from raw review data:

```bash
# macOS / Linux — run the full pipeline
bash run_data_pipeline.sh

# Windows PowerShell
.\run_data_pipeline.ps1

# Run a single stage
bash run_data_pipeline.sh --stage clean
bash run_data_pipeline.sh --stage embed
bash run_data_pipeline.sh --stage score
```

<sup>[back to top](#top)</sup>

---

## 10. Docker Compose

```bash
docker compose up --build     # first time or after code changes
docker compose up              # subsequent runs
docker compose down            # stop
```

Dashboard at `http://localhost:8050`, API at `http://localhost:8000`.

<sup>[back to top](#top)</sup>

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

<sup>[back to top](#top)</sup>

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

<sup>[back to top](#top)</sup>

---

## 13. Auth & Security

### API Key (service-to-service)
The API rejects any request without a valid `X-API-Key` header. The dashboard sends this automatically. Both services read from `API_KEY` env var. Locally, `API_KEY` is empty so auth is skipped. `/api/health` is always open.

### Admin Password (user-facing)
The splash page admin portal requires `ADMIN_PASSWORD`. The check is server-side and cannot be bypassed from the browser.

<sup>[back to top](#top)</sup>

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

<sup>[back to top](#top)</sup>

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

<sup>[back to top](#top)</sup>

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

<sup>[back to top](#top)</sup>
