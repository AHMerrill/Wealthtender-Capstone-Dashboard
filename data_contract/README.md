# Data Contract (v0)

This contract defines the minimum normalized tables the API will expose to the dashboard.
Artifacts may be generated in any format (CSV, Parquet, JSON), but must be normalized by the API into these shapes.

## Scores (long format)
Required columns:
- `run_id` (string)
- `firm_id` (string)
- `advisor_id` (string)
- `dimension` (string)
- `score` (float, 0-100)
- `confidence` (float, 0-1)
- `review_count` (int)
- `period` (string, e.g. 2025-Q4)

## Benchmarks
Required columns:
- `run_id` (string)
- `peer_group` (string)
- `dimension` (string)
- `p25` (float)
- `p50` (float)
- `p75` (float)

## Themes
Required columns:
- `run_id` (string)
- `advisor_id` (string)
- `theme` (string)
- `example_quote` (string)
- `sentiment` (string)

## Metadata
Required fields:
- `run_id`
- `created_at`
- `schema_version`
- `artifact_manifest` (list of files + types)
