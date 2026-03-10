# Data Contract (v1)

This contract defines the artifact schemas the API loads at startup. All artifacts live in `artifacts/` and are referenced by `artifacts/metadata.json`.

---

## Review Dimension Scores (`artifacts/scoring/review_dimension_scores.csv`)

Per-review cosine similarity scores. One row per review.

| Column | Type | Description |
|--------|------|-------------|
| `review_idx` | int | Unique review index |
| `advisor_id` | string | Advisor URL slug or identifier |
| `advisor_name` | string | Display name |
| `entity_type` | string | `"advisor"` or `"firm"` |
| `review_text_raw` | string | Original review text |
| `sim_trust_integrity` | float (0–1) | Cosine similarity to Trust & Integrity query |
| `sim_listening_personalization` | float (0–1) | Cosine similarity to Customer Empathy & Personalization query |
| `sim_communication_clarity` | float (0–1) | Cosine similarity to Communication Clarity query |
| `sim_responsiveness_availability` | float (0–1) | Cosine similarity to Responsiveness query |
| `sim_life_event_support` | float (0–1) | Cosine similarity to Life Event Support query |
| `sim_investment_expertise` | float (0–1) | Cosine similarity to Investment Expertise query |

---

## Advisor Dimension Scores (`artifacts/scoring/advisor_dimension_scores.csv`)

Entity-level aggregated scores. One row per entity (advisor or firm). Each dimension has three aggregation methods.

| Column | Type | Description |
|--------|------|-------------|
| `advisor_id` | string | Entity identifier |
| `advisor_name` | string | Display name |
| `entity_type` | string | `"advisor"` or `"firm"` |
| `review_count` | int | Number of reviews for this entity |
| `sim_mean_{dimension}` | float (0–1) | Mean of review-level scores |
| `sim_penalized_{dimension}` | float (0–1) | Mean with consistency penalty (high variance reduces score) |
| `sim_weighted_{dimension}` | float (0–1) | Time-decay weighted mean (recent reviews weighted higher) |

Where `{dimension}` is one of: `trust_integrity`, `listening_personalization`, `communication_clarity`, `responsiveness_availability`, `life_event_support`, `investment_expertise`.

This gives 18 score columns total (6 dimensions x 3 methods).

---

## Partner Groups (`artifacts/scoring/partner_groups_mock.csv`)

Maps advisors to partner groups for team comparison. Currently synthetic/mock data for development.

| Column | Type | Description |
|--------|------|-------------|
| `advisor_id` | string | Advisor identifier (matches `advisor_dimension_scores.csv`) |
| `partner_group_code` | string | Group code (e.g., `PG-BMM`) |
| `partner_group_name` | string | Display name (e.g., `Berkshire Money Management`) |

---

## Reviews Clean (`artifacts/macro_insights/reviews_clean.csv`)

Cleaned review corpus used for EDA charts. One row per review.

| Column | Type | Description |
|--------|------|-------------|
| `ID` | int | WordPress post ID |
| `advisor_id` | string | Advisor identifier |
| `advisor_name` | string | Display name |
| `review_text_raw` | string | Original review text |
| `review_text_clean` | string | Cleaned/normalized text |
| `rating` | float | Star rating |
| `review_date` | date | Review date |
| `token_count` | int | Word count (raw) |
| `clean_token_count` | int | Word count (cleaned) |
| `reviewer_name` | string | Reviewer display name |

Additional columns exist (`Title`, `Content`, `Date`, `Status`, various custom fields) but are not used by the dashboard.

---

## EDA Artifacts (`artifacts/macro_insights/`)

| File | Type | Description |
|------|------|-------------|
| `eda/eda_summary.json` | JSON | Summary statistics for the review corpus |
| `eda/coverage.json` | JSON | Data coverage metrics |
| `quality/quality_summary.json` | JSON | Quality report |
| `quality/missing_report.csv` | CSV | Missing data report |
| `quality/raw_file_meta.json` | JSON | Raw file metadata |
| `lexical/top_tokens.csv` | CSV | Top unigram tokens |
| `lexical/top_bigrams.csv` | CSV | Top bigram tokens |

---

## Metadata (`artifacts/metadata.json`)

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | string | Identifier for the artifact generation run |
| `created_at` | ISO 8601 | Timestamp of artifact generation |
| `schema_version` | string | Schema version (currently `"v0"`) |
| `artifact_manifest` | array | List of `{name, type, path}` entries for all artifacts |

---

## Enriched API Response Schema

When the dashboard requests scores from the API, each dimension score is returned as an enriched object rather than a plain float.

### Per-Dimension Score Object

| Field | Type | Description |
|-------|------|-------------|
| `raw` | float | Original cosine similarity score |
| `percentile` | float (0–100) | Percentile rank within same entity type |
| `normalized` | float (0–100) | Min-max rescaled to 0-100 within peer population |
| `tier` | string | `"Very Strong"`, `"Strong"`, `"Moderate"`, or `"Foundational"` |

### `/api/advisor-dna/advisor-scores` Response

```json
{
  "advisor_id": "string",
  "advisor_name": "string",
  "entity_type": "advisor|firm",
  "method": "mean|penalized|weighted",
  "review_count": 25,
  "scores": {
    "trust_integrity": {"raw": 0.42, "percentile": 85.0, "normalized": 72.3, "tier": "Very Strong"},
    "listening_personalization": {"raw": 0.38, ...},
    ...
    "composite": {"raw": 0.39, "percentile": 78.2, "normalized": 65.1, "tier": "Very Strong"}
  }
}
```

### `/api/leaderboard` Response

Accepts `dimension` param: `"all"` (default, returns all 6 + composite), a single dimension key, or `"composite"`.

```json
{
  "trust_integrity": [
    {"advisor_id": "...", "advisor_name": "...", "entity_type": "...",
     "score": 0.52, "percentile": 95.0, "normalized": 88.1,
     "tier": "Very Strong", "review_count": 30},
    ...
  ],
  "composite": [...],
  ...
}
```

### `/api/comparisons/head-to-head` (new)

| Parameter | Type | Description |
|-----------|------|-------------|
| `entity_a` | string (required) | First entity ID |
| `entity_b` | string (required) | Second entity ID |
| `method` | string | `mean` (default), `penalized`, or `weighted` |

Returns `entity_a` and `entity_b` enriched profiles plus a `diffs` object with `raw`, `percentile`, and `normalized` differences (B − A) per dimension.

---

## Intermediate Files (`data/intermediate/`)

These large files are produced by Stage 2 (embed) and consumed by Stage 3 (score). They are gitignored.

| File | Type | Description |
|------|------|-------------|
| `df_embeddings_MVP.csv` | CSV | Review-level data with 384-dim embedding vectors as strings. One row per review. Includes `review_hash` column (SHA256[:16] of 4 fields) for incremental dedup. |
| `advisor_embeddings_MVP.parquet` | Parquet | Advisor-level mean and penalized embedding vectors. Embeddings are L2-normalized (norm=1.0). |
| `df_advisors_weighted_time.parquet` | Parquet | Advisor-level time-weighted embeddings. Embeddings are NOT L2-normalized (norms vary ~0.3–0.9). |

### `df_advisors_weighted_time.parquet` Schema

| Column | Type | Description |
|--------|------|-------------|
| `advisor_id` | string | Advisor identifier |
| `advisor_name` | string | Display name |
| `advisor_embedding_weighted_time` | array(float32) | 384-dim time-weighted mean embedding (unnormalized) |
| `n_reviews_used` | int | Number of reviews used for this advisor |
| `total_tokens` | int | Sum of token counts across reviews |
| `total_tokens_nostop` | int | Sum of informative token counts |
| `median_age_years` | float | Median review age in years |
| `min_review_date` | date | Oldest review date |
| `max_review_date` | date | Most recent review date |
| `effective_n_time` | float | Kish's effective sample size given time weights |

---

## Regenerating Artifacts

All artifacts are generated by the `pipeline/` Python package. To regenerate from scratch:

```bash
python -m pipeline.run                 # run all stages (incremental embed by default)
python -m pipeline.run --full          # force full re-embed from scratch
python -m pipeline.run --validate      # compare outputs against artifacts_backup/
```

Stage 2 uses incremental append by default: reviews are identified by a four-field hash (`advisor_id` + `review_text_raw` + `review_date` + `reviewer_name` → SHA256[:16]). Only reviews not already in the embeddings file are encoded. Use `--full` to re-embed everything (e.g., after changing the embedding model).

Requirements: `pip install -r requirements-pipeline.txt` (includes `sentence-transformers`, `nltk`, `numpy`, `pandas`, `pyarrow`, `torch`)

The original Jupyter notebooks remain in the repo for provenance but are no longer needed to regenerate artifacts. See `pipeline/run.py` for CLI options and stage selection.