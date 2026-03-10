# Incremental Pipeline Processing — Gameplan

**Goal:** When new reviews arrive (mixed with old ones in the same file or database), only embed the NEW reviews. Don't re-process reviews that already have embeddings. Never allow duplicate reviews to inflate an advisor's scores.

---

## Why This Matters

Embedding is the expensive step — it loads a transformer model and encodes every review through it. With ~4,700 reviews today that's manageable (~2 min), but as the corpus grows or moves to continuous ingestion, re-embedding everything on every run becomes wasteful.

Cleaning (Stage 1) and scoring (Stage 3) are cheap — they're just pandas operations. Only Stage 2 (embed) needs the optimization.

---

## Key Principle: One Review = One Embedding = One Score

An advisor can (and should) have many reviews from many different clients. A firm can have many reviews. That's normal and expected — all of them count toward that entity's scores.

What must NEVER happen: the same individual review appearing twice in the embeddings, which would double-count it in scoring and artificially inflate that advisor's averages.

---

## Current Flow (Full Reprocess)

```
raw CSV → [Stage 1: clean] → reviews_clean.csv
                                    ↓
                            [Stage 2: embed ALL] → df_embeddings_MVP.csv
                                                   advisor_embeddings_MVP.parquet
                            [Stage 2b: embed ALL] → df_advisors_weighted_time.parquet
                                    ↓
                            [Stage 3: score ALL] → review_dimension_scores.csv
                                                   advisor_dimension_scores.csv
```

## Proposed Flow (Incremental)

```
raw CSV → [Stage 1: clean] → reviews_clean.csv
                                    ↓
                            [compare against existing embeddings by review_hash]
                                    ↓
                    ┌───────────────┴──────────────────┐
                    │ NEW reviews only                  │ EXISTING embeddings
                    ↓                                   │ (loaded from disk)
            [Stage 2: embed DELTA]                      │
                    ↓                                   │
            [MERGE new + existing embeddings] ←─────────┘
                    ↓
            [DEDUP by review_hash — keep first occurrence only]
                    ↓
            [Stage 2b: re-aggregate weighted means]
                    ↓
            [Stage 3: score ALL from merged embeddings]
```

---

## Implementation Design

### Stable Review Identity

The dedup key is `(advisor_id, review_text_raw, review_date, reviewer)` — a review is "the same review" if all four fields match. We hash this tuple to create a stable `review_hash`.

**Why these four fields?**

- `advisor_id` — Same review text from two different advisors should be treated separately (different advisor name stripping produces different cleaned text, and they're genuinely different reviews).
- `review_text_raw` — The actual content of the review. If someone edits their review, the new text gets a new hash (correct — it's meaningfully different now).
- `review_date` — Without the date, two different clients who both wrote "Great advisor!" for the same advisor would hash to the same value and one would be dropped. Adding the date distinguishes reviews posted at different times.
- `reviewer` — The reviewer's name/identifier. This closes the last meaningful edge case: two different clients writing identical text for the same advisor on the same day now produce different hashes because their names differ. Both reviews count.

**What counts as a true duplicate?** Same advisor + same text + same date + same reviewer. That's the same person submitting the exact same review twice — genuinely a duplicate, safe to dedup.

**Why not use row index or WordPress post ID as the primary key?**
- Row index changes if the CSV is re-exported with different sorting or filtering.
- Post ID (`ID` column) could work IF it's always present and stable, but the pipeline shouldn't depend on WordPress internals. It's a good fallback / future enhancement once data comes from a database with stable PKs.

### Where the Check Happens

In `embed.py`, right after loading `reviews_clean.csv`:

1. Compute `review_hash` for every row in the new clean file
2. **Dedup the clean file itself** — if the raw export contained true duplicates, drop them here before embedding (keep first occurrence per hash)
3. Load existing `df_embeddings_MVP.csv` (if it exists)
4. Build set of already-embedded hashes from existing data
5. Delta = new hashes minus existing hashes → these are the only rows to encode
6. Encode only the delta rows
7. Concatenate: existing embeddings + new embeddings
8. Drop any rows whose hash is NOT in the new clean file (handles deleted/edited reviews)
9. **Final dedup safety net** — `drop_duplicates(subset="review_hash", keep="first")`
10. Write merged result back to `df_embeddings_MVP.csv`

### Dedup Safety at Every Layer

The design has THREE dedup checkpoints to ensure no duplicates ever reach scoring:

| Layer | Where | What it catches |
|-------|-------|-----------------|
| **Layer 1: Clean-time dedup** | `embed.py` after loading `reviews_clean.csv` | True duplicates in the raw export itself |
| **Layer 2: Delta detection** | `embed.py` hash comparison | Reviews that were already embedded in a previous run |
| **Layer 3: Post-merge dedup** | `embed.py` after concatenation | Belt-and-suspenders safety net — catches anything Layers 1-2 missed |

After these three layers, `df_embeddings_MVP.csv` contains exactly one row per unique review. Stage 3 scores from this file, so scores are never inflated by duplicates.

### What About Stage 2b (Weighted)?

Stage 2b operates at the ADVISOR level, not the review level. It re-encodes all reviews for each advisor with time-decay weighting. Since the weighting depends on review age relative to "now," the weights change every time the pipeline runs — so Stage 2b must always re-aggregate from the full review embeddings. However, it still benefits from the incremental Stage 2 because the per-review embeddings are already computed.

**Optimization path:** Store per-review embeddings (unnormalized) separately, then do the weighted mean aggregation without re-encoding. This is already how it works — `run_weighted()` currently re-encodes from scratch, but could be refactored to read from the Stage 2 review-level embeddings instead. That's a separate optimization (see FUTURE_WORK.md — consolidation item).

For now: Stage 2b re-runs fully each time. The bottleneck is Stage 2 main, which is where the incremental logic lives.

### What About Scoring (Stage 3)?

Scoring always runs on the FULL set of (already-deduped) embeddings. It's a single matrix multiply — fast even at 10k+ reviews. No incremental optimization needed here. And because the embeddings are deduped upstream, no advisor's scores get inflated.

### What About Cleaning (Stage 1)?

Cleaning always runs on the FULL raw file. It's fast (seconds) and produces EDA/quality artifacts that should reflect the complete corpus. No incremental optimization needed.

**Note:** Stage 1 does NOT do dedup — that's intentionally left to Stage 2. Stage 1's job is to clean text, filter test accounts, and produce quality metrics. The quality metrics (review counts, token distributions) should reflect the raw input as-is so you can see if duplicates are coming in. Dedup happens at embed time so the scoring pipeline only ever works with unique reviews.

---

## Concrete Changes Required

### 1. Add `review_hash` computation (in `embed.py`)

```python
import hashlib

def _review_hash(advisor_id, review_text_raw, review_date, reviewer):
    """Stable identity for a review: same advisor + text + date + reviewer = same review.

    Two different clients reviewing the same advisor → different hashes (good, both count).
    Same client writing identical text on different dates → different hashes (good, both count).
    Same review exported twice in overlapping data pulls → same hash (deduped, good).
    """
    date_str = str(review_date).split(" ")[0].split("T")[0] if pd.notna(review_date) else "no_date"
    reviewer_str = str(reviewer).strip() if pd.notna(reviewer) else "anonymous"
    key = f"{advisor_id}||{review_text_raw}||{date_str}||{reviewer_str}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
```

### 2. Modify `embed.run()` in `embed.py`

Before the encoding loop:
- Compute `review_hash` for every row in clean file
- Dedup the clean file by hash (Layer 1)
- Load existing embeddings CSV (if exists)
- Build hash→embedding lookup from existing data
- Filter to only rows with NEW hashes (delta)
- Encode only the delta
- Merge: existing (minus deleted) + new
- Final dedup safety net (Layer 3)
- Continue with advisor-level aggregation as before

### 3. Add `--full` flag to `run.py`

```
python -m pipeline.run                # incremental (default)
python -m pipeline.run --full         # force full reprocess
python -m pipeline.run --stage embed  # incremental embed only
```

The `--full` flag skips the delta check and re-embeds everything. Useful when the model changes or you want a clean baseline.

### 4. Logging

Print clear messages so you can see exactly what happened:
```
Stage 2: 4,731 reviews in clean file
Stage 2: 4,731 unique reviews after dedup (0 true duplicates removed)
Stage 2: 4,650 already embedded (matched by hash)
Stage 2: 81 new reviews to embed
Stage 2: 0 stale reviews removed (deleted/edited since last run)
Stage 2: Encoding 81 new reviews...
Stage 2: Final embeddings: 4,731 total (verified unique)
```

---

## Edge Cases

| Scenario | Behavior |
|----------|----------|
| First run (no existing embeddings) | Full embed, same as today |
| Same raw file run twice | 0 new reviews detected, 0 encoded. Scores unchanged. |
| New reviews added to file | Only new reviews encoded. Merged with existing. |
| Reviews deleted from source | Hash comparison drops them from merged output |
| Review text edited (same advisor + date) | Old hash gone → old embedding dropped. New hash → re-embedded. |
| Advisor name changed (same reviews) | Hash changes (advisor_id is in the triplet) → re-embedded |
| Two clients write "Great advisor!" on different days | Different dates → different hashes → both kept (correct) |
| Two clients write "Great advisor!" on the same day | Different reviewer names → different hashes → both kept (correct) |
| Same person submits the same review twice on the same day | Same hash → treated as duplicate, one kept (correct) |
| Raw export contains true duplicates | Layer 1 dedup catches them before embedding |
| Model version changes | Use `--full` flag to re-embed everything |
| Embeddings file corrupted/missing | Falls back to full embed automatically |

---

## What NOT to Change

- **Stage 1 (clean):** Always processes the full raw file. It's fast and EDA artifacts should reflect the complete corpus.
- **Stage 3 (score):** Always scores the full embedding matrix. It's a single matrix multiply.
- **Artifact format:** No schema changes to final CSV/parquet files. The `review_hash` column is added to the embeddings intermediate file only (already gitignored).
- **API:** Zero changes. The API reads final artifacts, which are always complete.

---

## Future Enhancement: Database Primary Keys

Once the data source moves from CSV export to a database, each review will have a stable primary key (e.g., `review_id` integer). At that point, the hash-based approach can be replaced with a simpler PK-based check: "which review_ids are in the database but not in my embeddings file?" The hash approach is designed for the current CSV-based workflow where row identity isn't guaranteed.

---

## Estimated Effort

This is a ~60-line change concentrated in `embed.py`, plus a small flag addition to `run.py`. No changes to clean, score, config, API, or dashboard code.
