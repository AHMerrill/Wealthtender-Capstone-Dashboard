# Wealthtender Dashboard — Project Log

> Living document tracking all feedback, decisions, and changes.
> Items are never deleted — they get marked with a status as the project evolves.

---

## Status Key
- **PROPOSED** — Feedback received, not yet decided
- **PLANNED** — Decided to build, assigned to a sprint
- **IN PROGRESS** — Currently being worked on
- **DONE** — Shipped
- **DEFERRED** — Intentionally pushed to a later phase
- **CANCELLED** — Decided not to pursue (with reason)

---

## Feedback Sources

| Tag | Who | Context |
|-----|-----|---------|
| **BT** | Brian Thorp | Client / Wealthtender founder. Product vision & commercial strategy. |
| **COLLAB** | Collaborator Team | UX/UI improvements, technical suggestions, modeling input. |
| **ZM** | Zan Merrill | Project lead, MSBA capstone team. |

---

## Feedback Items

### FB-01 · Rename "Listening & Personalization" → "Customer Empathy & Personalization"
- **Source:** COLLAB · **Filed:** 2026-03-09
- **Status:** DONE
- **Rationale:** Brian noted in a client meeting that "listening" and "communication" felt too similar. New label better distinguishes this dimension.
- **Scope:** String change in `DIM_LABELS`, `DIM_DESCRIPTIONS`, `DIM_QUERY_TEXTS` in `dashboard/pages/advisor_dna.py`. Underlying key `listening_personalization` unchanged.

### FB-02 · Default to Percentile Mode (hide or de-emphasize raw similarity)
- **Source:** COLLAB · **Filed:** 2026-03-09
- **Status:** DONE
- **Rationale:** Raw cosine similarity scores are unintuitive for advisors. Percentile rank is immediately meaningful.
- **Scope:** Flip `dna-display-mode` default to `"percentile"` in `advisor_dna.py`. Consider hiding raw toggle for firm role, keep for admin.

### FB-03 · Replace Donut/Pie Chart with Bar or Spider for Aggregate Dimensions
- **Source:** COLLAB · **Filed:** 2026-03-09
- **Status:** DONE
- **Rationale:** Pie charts make it hard to compare magnitudes across 6 dimensions. Bar chart is consistent with entity-level views.
- **Scope:** Swap `go.Pie` in macro view callback in `advisor_dna.py` to horizontal bar chart.

### FB-04 · Fix Spider Chart — External Legend + Disable Zoom
- **Source:** COLLAB · **Filed:** 2026-03-09
- **Status:** DONE
- **Rationale:** Labels overlap radar lines; zoom/pan is confusing on a radar chart.
- **Scope:** External legend on `go.Scatterpolar`, `config={"scrollZoom": False}` on review-level `dcc.Graph` in `advisor_dna.py`.

### FB-05 · EDA: Replace "Token" with Advisor-Friendly Language
- **Source:** COLLAB · **Filed:** 2026-03-09
- **Status:** DONE
- **Rationale:** Firm users won't know what a "token" is. The underlying metric is effectively word count.
- **Scope:** Relabel throughout `eda_content.py` and `eda_charts.py`. Optionally hide token histogram for firm role.

### FB-06 · EDA: Time Series Granularity (Year/Quarter toggle)
- **Source:** COLLAB · **Filed:** 2026-03-09
- **Status:** DONE
- **Rationale:** Monthly granularity is noisy pre-2021 when review volume was low. Year/quarter is more useful.
- **Scope:** Add `freq` parameter to `_build_eda_payload` in `artifacts.py`, dropdown in EDA sidebar.

### FB-07 · EDA: Stopwords Apply to N-Gram Chart Only
- **Source:** COLLAB · **Filed:** 2026-03-09
- **Status:** DONE
- **Rationale:** Stopword filtering should affect lexical analysis but not token counts or other metrics.
- **Scope:** In `artifacts.py` `_build_eda_payload`, apply stopword filter only in the lexical analysis block.

### FB-08 · Confidence Tiers + Premier Benchmarking Pool *(merged: originally FB-08 + FB-09)*
- **Source:** BT · **Filed:** 2026-03-09
- **Status:** DONE
- **Rationale:** Low review counts produce unreliable dimension scores. Gating and tiering by review count provides a confidence floor, a "carrot" for advisors to collect more reviews, and lays groundwork for a premium benchmarking product.
- **Decision:** Three confidence zones, one comparison toggle:
  - **< 10 reviews:** Amber "Directional insights — based on N reviews" banner. Scores visible but flagged.
  - **10–19 reviews:** Normal access, no banner.
  - **20+ reviews:** "Robust Data" badge. Included in premier comparison pool.
  - **New UI toggle on Advisor DNA:** "Compare against: All Advisors | Premier Advisors (20+ reviews)." Premier mode filters the percentile population to 20+ review entities only. Same math, smaller pool.
- **Scope:** Threshold constants in `roles.py`, banner component in `app.py`, badge rendering in `advisor_dna.py`, population filter in `artifacts.py` percentile calculation. API already returns `review_count`.
- **Note:** Premier pool may be small initially — toggle is there for Brian to see the concept and for the pool to grow into.

### FB-10 · Review-Level Evidence for Dimension Scores ("Why this score?")
- **Source:** BT · **Filed:** 2026-03-09
- **Status:** DONE
- **Rationale:** When advisors see dimension scores, their natural question is "which reviews are driving that?" Surfacing top-matching reviews makes scores tangible.
- **Scope:** `/api/advisor-dna/entity-reviews` already returns per-dimension similarity. Rank and surface top 2-3 reviews per dimension in an expandable section.

### FB-11 · Top-Scoring Reviews/Advisors Per Dimension (Leaderboard)
- **Source:** COLLAB · **Filed:** 2026-03-09
- **Status:** PROPOSED
- **Rationale:** Advisors could study high-scoring reviews to understand what clients value. Anonymization option for privacy.
- **Scope:** New API endpoint, new UI panel. Sprint TBD.

### FB-12 · Advisor-to-Advisor Comparison Within a Firm
- **Source:** BT · **Filed:** 2026-03-09
- **Status:** PROPOSED
- **Rationale:** Immediately valuable for multi-advisor firms. Side-by-side radar/bar of dimension scores.
- **Blocker:** Current data exports don't reliably associate firm-level reviews with individual advisors. Brian confirmed a `partner_group` field can be added in a future export. Mock data can be used in the interim.
- **Scope:** New sub-view in `advisor_dna.py`, comparison endpoint in API. Sprint TBD.

### FB-13 · Advisor/Firm-to-External Entity Comparison
- **Source:** BT · **Filed:** 2026-03-09
- **Status:** PROPOSED
- **Rationale:** "Compare to another advisor" overlay, or compare to aggregated population data.
- **Scope:** Extension of FB-12. Sprint TBD.

### FB-14 · Keyword Highlighting in Reviews (Dimension Score Drivers)
- **Source:** COLLAB · **Filed:** 2026-03-09
- **Status:** DEFERRED — Backlog
- **Rationale:** Highlight words contributing to each dimension score, similar to Amazon review keyword search.
- **Approach:** TF-IDF overlap between dimension query text and review text (simpler than attention attribution).

### FB-15 · Trend Over Time at Dimension Level
- **Source:** BT · **Filed:** 2026-03-09
- **Status:** DEFERRED — Backlog
- **Rationale:** "Your Life Event Support score has trended up over 12 months." Encourages ongoing feedback collection.
- **Blocker:** Needs timestamped scoring aggregation pipeline (data exists, pipeline doesn't).

### FB-16 · External Review Ingestion (Google Reviews, DFA Surveys, etc.)
- **Source:** BT · **Filed:** 2026-03-09
- **Status:** DEFERRED — Backlog
- **Rationale:** Benchmark beyond Wealthtender's proprietary dataset.
- **Notes:** Architecture-level change. Phase 2+.

### FB-17 · Advisor-to-Advisor Comparison Within National Network
- **Source:** BT · **Filed:** 2026-03-09
- **Status:** PROPOSED
- **Rationale:** Similar to FB-12 but across a national advisor network. Would leverage an advisor/firm hierarchy from a compliance portal.
- **Blocker:** Requires hierarchy data from Wealthtender's compliance portal export.

---

## Change Log

| Date | Items | What Changed |
|------|-------|-------------|
| 2026-03-09 | FB-01 through FB-17 | Initial feedback synthesis from BT and COLLAB. Sprint 1 & 2 planned. |
| 2026-03-09 | FB-08, FB-09 | Merged into single "Confidence Tiers + Premier Pool" item. Three zones (<10 warning, 10-19 normal, 20+ badge) with "All vs Premier" comparison toggle. |
| 2026-03-09 | FB-01–FB-07 | Sprint 1 completed: dimension rename, percentile default, pie→bar, spider fix, token→word, stopwords, time granularity. |
| 2026-03-09 | FB-08 | Sprint 2: Confidence banners, premier pool toggle, sidebar premier filter, entity bar/spider toggle. UX polish pass. |
| 2026-03-09 | Macro view | Added Comparison Pool (All/Premier) and Bar/Spider toggle to macro view. Backend supports premier-filtered macro totals. |
| 2026-03-09 | FB-10 | Sprint 2: Top-3 evidence cards per dimension. "Why this score?" surfaced automatically when drilling into a dimension. |

---

## Sprint Tracker

### Sprint 1 — 2026-03-09 (UX/UI Quick Wins)
| Item | Description | Status |
|------|------------|--------|
| FB-01 | Rename dimension label | DONE |
| FB-02 | Default to percentile mode | DONE |
| FB-03 | Replace pie with bar chart | DONE |
| FB-04 | Fix spider chart readability | DONE |
| FB-05 | Replace "token" language | DONE |
| FB-07 | Stopwords for n-grams only | DONE |

### Sprint 2 — 2026-03-09 (Confidence & Evidence)
| Item | Description | Status |
|------|------------|--------|
| FB-06 | Time series granularity toggle | DONE |
| FB-08 | Confidence tiers + premier benchmarking pool (merged FB-08/09) | DONE |
| FB-10 | Review evidence per dimension | DONE |

### Sprint 3 — TBD (Comparison Views)
| Item | Description | Status |
|------|------------|--------|
| FB-11 | Top reviews/advisors leaderboard | PROPOSED |
| FB-12 | Intra-firm advisor comparison | PROPOSED |
| FB-13 | External entity comparison | PROPOSED |

### Backlog
| Item | Description | Status |
|------|------------|--------|
| FB-14 | Keyword highlighting | DEFERRED |
| FB-15 | Dimension trend over time | DEFERRED |
| FB-16 | External review ingestion | DEFERRED |
| FB-17 | National network comparison | PROPOSED |
