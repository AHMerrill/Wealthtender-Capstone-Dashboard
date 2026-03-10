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

## Regenerating Artifacts

The scoring artifacts are generated by `notebooks/collaborator/query_embeddings_vs_review_embeddings.ipynb`. To regenerate:

1. Run the notebook end-to-end (requires `sentence-transformers`, `numpy`, `pandas`)
2. Copy outputs to `artifacts/scoring/`
3. Redeploy the API (it loads artifacts at startup)

The EDA artifacts are pre-built and do not currently have an automated regeneration pipeline.
