# Raw Data — Wealthtender Reviews

## Source

The raw input to the pipeline is a single CSV file exported from the Wealthtender platform:

```
data/raw/wealthtender_reviews.csv
```

This file is obtained manually from Wealthtender's WordPress admin panel (or via a future automated export). Each row represents one client review of a financial advisor or advisory firm hosted on [wealthtender.com](https://wealthtender.com).

## Schema

| Column | Type | Description |
|--------|------|-------------|
| `ID` | int | WordPress post ID (unique per review) |
| `Title` | str | Review title entered by the client |
| `Content` | str | Full review text (HTML may be present) |
| `Date` | datetime | Original publication date |
| `_custom_form` | int | Internal form ID |
| `notification_name` | str | Advisor display name (e.g., "Jane Doe, CFP®") |
| `notification_page` | str | Advisor profile URL on Wealthtender |
| `_custom_relationship` | str | Reviewer's relationship to the advisor (e.g., "Current Client") |
| `_custom_compensation` | str | Compensation disclosure text |
| `_custom_conflicts` | str | Conflicts-of-interest disclosure text |
| `_custom_disclosure` | str | Additional disclosure (usually empty) |
| `Status` | str | Post status (typically "publish") |
| `Post Modified Date` | datetime | Last modification date |
| `reviewer_name` | str | Name of the person who wrote the review |
| `acf_rating` | int | Star rating (1–5) |

## How the Pipeline Uses This File

The pipeline reads the raw CSV once, at the very start of Stage 1 (`pipeline/clean.py`). Every downstream artifact is derived from this single file. The path is configured in `pipeline/config.py` as `RAW_CSV`.

**To update the data:** replace `wealthtender_reviews.csv` with a newer export from the platform, then rerun the pipeline (`python -m pipeline.run`). The pipeline is designed to handle new rows, new advisors, and new columns gracefully — unknown columns are ignored during cleaning, and all artifact paths are deterministic.

## What Happens to a Review (Quick Preview)

A single review enters here as a row in the CSV and flows through the full pipeline:

1. **clean.py** — normalizes text, removes test accounts, strips boilerplate, exports `reviews_clean.csv`
2. **embed.py** — tokenizes, removes stopwords and advisor names, encodes into a 384-dim vector via `all-MiniLM-L6-v2`
3. **score.py** — computes cosine similarity against 6 dimension queries, aggregates to advisor level
4. **API** — loads the resulting CSVs, adds percentiles/tiers on the fly, serves JSON to the dashboard

See the main README Section 5 for the full "water droplet" walkthrough.

## Test / Demo Accounts

The raw export may contain reviews from internal test accounts (e.g., "Demo Jane," "Press Advisor Test"). These are filtered out automatically by `clean.py` using the exclusion list in `pipeline/config.py → TEST_ADVISOR_IDS`. If Wealthtender adds an `is_test` or `status` field to the export in the future, the pipeline should switch to filtering on that flag instead.

## Storage & Future Migration

Currently the raw file lives on disk as a flat CSV. To migrate to a database:

1. Load the CSV into a PostgreSQL (or similar) table with the same column names
2. Update `pipeline/config.py` to point `RAW_CSV` at a database connection string (or swap the `pd.read_csv` call in `clean.py` with `pd.read_sql`)
3. Everything downstream remains unchanged — the pipeline only cares about getting a DataFrame with the expected columns
