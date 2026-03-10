# Changelog

All notable changes to the Wealthtender Dashboard project.

---

| Date | Items | What Changed |
|------|-------|-------------|
| 2026-03-09 | FB-01 through FB-22 | Initial feedback synthesis. Sprint 1 & 2 planned and executed. |
| 2026-03-09 | FB-01–FB-07 | Sprint 1 completed: dimension rename, percentile default, pie→bar, spider fix, token→word, stopwords, time granularity. |
| 2026-03-09 | FB-08–FB-10 | Sprint 2 completed: confidence tiers, premier pool toggle, macro controls, evidence cards. |
| 2026-03-09 | FB-11–FB-18 | Sprint 3 planned: Benchmarks tab (FB-11/12/13), Leaderboard tab (FB-14/15), Comparisons tab (FB-16/17/18). |
| 2026-03-09 | FB-19–FB-22 | Backlog items (keyword highlighting, dimension trends, external ingestion, national network) moved to [FUTURE_WORK.md](./FUTURE_WORK.md). |
| 2026-03-09 | README | Updated to reflect Sprints 1-2 features and Sprint 3 plan. |
| 2026-03-09 | FB-11–FB-18 | Sprint 3 completed: Benchmarks page (pool stats, histograms, percentile table), Leaderboard page (top-N bars, detail cards), Comparisons page (team spider/bar, head-to-head overlay). New API endpoints, mock partner groups, roles/nav updated. |
| 2026-03-09 | Cleanup | Codebase cleanup: centralized shared dimension constants, removed unused imports/functions, removed legacy CSS. README rewritten for developer handoff. |
| 2026-03-09 | Handoff Prep | Repo made public. Apache 2.0 license + NOTICE. Secrets audit. Download instructions. Re-hosting note. Non-project files removed from tracking. Data contract rewritten. |
| 2026-03-09 | Code Review | Full code review tightening: advisor_dna.py now imports from constants.py (fixed color mapping mismatch), hardcoded fallback password removed from splash.py, empty DataFrame guard in artifacts.py, inline docs for thresholds, stale comments cleaned. |
| 2026-03-10 | API Enrichment | Major API enrichment: every score endpoint now returns raw, percentile, normalized (0-100), and tier per dimension. Composite score computed server-side. New `/api/comparisons/head-to-head` endpoint. Leaderboard dimension param added. |
| 2026-03-10 | Frontend Percentile | Leaderboard bars show percentile rank with ordinal labels, unselected bars fade to 30% opacity. Comparison tables show percentile (raw) per cell with composite row. Benchmarks page adds explanatory banner for raw-score histograms. All pages handle enriched API response format. |
| 2026-03-10 | Pipeline Package | Built `pipeline/` Python package: `clean.py` (Stage 1), `embed.py` (Stage 2), `score.py` (Stage 3), `enrich_comparisons.py` (mock partner groups), `run.py` (CLI orchestrator), `config.py` (all constants). Extracted from team notebooks — exact code, no inventions. Single command: `python -m pipeline.run`. |
| 2026-03-10 | Test Account Filter | Added `TEST_ADVISOR_IDS` exclusion set to `config.py` (5 test accounts: Demo Jane, Press Advisor Test, TEST John Geffert, TEST ADVISOR August 2022). Filter block in `clean.py` drops ~48 test reviews automatically. |
| 2026-03-10 | Enrich Comparisons | Built `enrich_comparisons.py` as deletable dev scaffolding for mock partner group generation. Auto-detects real `partner_group` column in data — if present, writes real associations; if absent, generates mock. Can be deleted with zero impact on main pipeline. |
| 2026-03-10 | Documentation | Created `data/raw/README.md` (raw data schema and provenance). Rewrote README Section 5 with pipeline module references, "water droplet" walkthrough tracing a single review through every stage, and database migration guide. Updated `methodology.py` with three new accordion sections: Analysis Pipeline, Following a Review Through the Pipe, and Data Storage & Migration. |
| 2026-03-10 | Weighted Embeddings | Implemented `run_weighted()` in `embed.py` (Stage 2b) from collaborator notebook `Wealthtender_Embeddings_WT.ipynb`. Separate embedding pass: `normalize_embeddings=False`, simple name stripping, half-life time-decay weighting (2yr half-life). Outputs `df_advisors_weighted_time.parquet`. Updated `run.py` to call Stage 2b after Stage 2. |
| 2026-03-10 | Documentation | Updated README (Stage 2b in pipeline diagram, water-droplet narrative, source notebooks table), methodology.py (Stage 2b sections in pipeline and water-droplet), data_contract (intermediate files schema, weighted parquet schema, regeneration instructions). |
| 2026-03-10 | Pipeline Fix | `score.py` now writes `review_count` column to `advisor_dimension_scores.csv` (API previously computed this at startup). Pipeline requirements added to `requirements.txt`. Intermediate files gitignored. |
| 2026-03-10 | Launcher Scripts | Renamed `run.sh`/`run.ps1` → `run_api_dashboard.sh`/`.ps1`. Created `run_data_pipeline.sh`/`.ps1` for pipeline execution with arg forwarding. |
| 2026-03-10 | Incremental Dedup | Append-based incremental pipeline: four-field review hash (advisor_id + review_text_raw + review_date + reviewer_name → SHA256[:16]). Three-layer dedup: within-batch, cross-batch against existing embeddings, post-concat safety. `--full` flag forces complete re-embed. Second run on same data correctly detects 0 new reviews and skips model loading. Split `requirements.txt` into runtime (`requirements.txt`) and pipeline (`requirements-pipeline.txt`) so Docker images don't ship torch/sentence-transformers. Graceful error when raw CSV is missing. Updated README, data_contract, methodology.py, and launcher scripts. |

For deferred work, technical debt, and enhancement ideas, see [FUTURE_WORK.md](./FUTURE_WORK.md).
