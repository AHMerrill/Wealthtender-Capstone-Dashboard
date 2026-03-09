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

## Sprint Tracker

### Sprint 1 — UX/UI Quick Wins ✅
| Item | Description | Status |
|------|------------|--------|
| FB-01 | Rename dimension label | DONE |
| FB-02 | Default to percentile mode | DONE |
| FB-03 | Replace pie with bar chart (macro view) | DONE |
| FB-04 | Fix spider chart readability | DONE |
| FB-05 | Replace "token" language in EDA | DONE |
| FB-06 | Time series granularity toggle | DONE |
| FB-07 | Stopwords for n-grams only | DONE |

### Sprint 2 — Confidence & Evidence ✅
| Item | Description | Status |
|------|------------|--------|
| FB-08 | Confidence tiers + premier benchmarking pool (merged FB-08/09) | DONE |
| FB-09 | Macro view: Comparison Pool (All/Premier) + Bar/Spider toggle | DONE |
| FB-10 | Review evidence per dimension ("Why this score?") | DONE |

### Sprint 3 — Benchmarks, Leaderboard & Comparisons ✅

**Three new tabs**, each with a focused purpose:

| Item | Tab | Description | Status |
|------|-----|------------|--------|
| FB-11 | **Benchmarks** | Premier pool deep-dive: composition stats, dimension distributions, P25/P50/P75 breakpoints, advisor vs firm profiles | DONE |
| FB-12 | **Benchmarks** | Population distribution charts: where entities fall on each dimension, "you are here" marker | DONE |
| FB-13 | **Benchmarks** | Peer percentile summary card: selected entity's scores vs benchmark breakpoints | DONE |
| FB-14 | **Leaderboard** | Dimension leaderboard: top-N entities per dimension, filterable by type and pool | DONE |
| FB-15 | **Leaderboard** | Leaderboard detail cards: click an entity to see its full dimension profile inline | DONE |
| FB-16 | **Comparisons** | Intra-firm team comparison: side-by-side radar/bar of advisors within a firm | DONE |
| FB-17 | **Comparisons** | Entity-to-entity comparison: overlay two entities for head-to-head dimension comparison | DONE |
| FB-18 | **Comparisons** | Mock partner group data: generate synthetic `partner_group` field for dev/demo | DONE |

### Backlog
| Item | Description | Status |
|------|------------|--------|
| FB-19 | Keyword highlighting in reviews (dimension score drivers) | DEFERRED |
| FB-20 | Dimension trend over time | DEFERRED |
| FB-21 | External review ingestion (Google Reviews, DFA Surveys, etc.) | DEFERRED |
| FB-22 | National network comparison (requires compliance portal data) | DEFERRED |

---

## Feedback Items

### Sprint 1

#### FB-01 · Rename "Listening & Personalization" → "Customer Empathy & Personalization"
- **Source:** COLLAB · **Status:** DONE
- **Rationale:** Brian noted "listening" and "communication" felt too similar. New label better distinguishes this dimension.
- **Scope:** String change in `DIM_LABELS`, `DIM_DESCRIPTIONS`, `DIM_QUERY_TEXTS`. Underlying key `listening_personalization` unchanged.

#### FB-02 · Default to Percentile Mode
- **Source:** COLLAB · **Status:** DONE
- **Rationale:** Raw cosine similarity scores are unintuitive for advisors. Percentile rank is immediately meaningful.
- **Scope:** Flip `dna-display-mode` default to `"percentile"`.

#### FB-03 · Replace Donut/Pie Chart with Bar Chart (Macro View)
- **Source:** COLLAB · **Status:** DONE
- **Rationale:** Pie charts make it hard to compare magnitudes across 6 dimensions.
- **Scope:** Swap `go.Pie` in macro view to horizontal bar chart.

#### FB-04 · Fix Spider Chart — External Legend + Disable Zoom
- **Source:** COLLAB · **Status:** DONE
- **Rationale:** Labels overlap radar lines; zoom/pan is confusing on radar.
- **Scope:** External legend on `go.Scatterpolar`, disable scrollZoom.

#### FB-05 · EDA: Replace "Token" with Advisor-Friendly Language
- **Source:** COLLAB · **Status:** DONE
- **Rationale:** Firm users won't know what a "token" is. Relabel as "word."
- **Scope:** Relabel throughout `eda_content.py` and `eda_charts.py`.

#### FB-06 · EDA: Time Series Granularity (Year/Quarter Toggle)
- **Source:** COLLAB · **Status:** DONE
- **Rationale:** Monthly granularity is noisy pre-2021. Year/quarter more useful.
- **Scope:** `freq` parameter in `_build_eda_payload`, dropdown in EDA sidebar.

#### FB-07 · EDA: Stopwords Apply to N-Gram Chart Only
- **Source:** COLLAB · **Status:** DONE
- **Rationale:** Stopword filtering should only affect lexical analysis.
- **Scope:** Apply filter only in the lexical block of `_build_eda_payload`.

### Sprint 2

#### FB-08 · Confidence Tiers + Premier Benchmarking Pool *(merged: originally FB-08 + FB-09)*
- **Source:** BT · **Status:** DONE
- **Rationale:** Low review counts produce unreliable scores. Gating by review count provides a confidence floor and a "carrot" for advisors.
- **Decision:** Three zones — <10 amber warning, 10-19 normal, 20+ green badge. "All vs Premier" toggle on entity view.
- **Scope:** Threshold constants, banner component, badge rendering, population filter in percentile calculation.

#### FB-09 · Macro View: Comparison Pool + Bar/Spider Toggle
- **Source:** ZM · **Status:** DONE
- **Rationale:** Macro view needed the same All/Premier toggle and a spider chart option like the entity view.
- **Scope:** `min_peer_reviews` param on `dna_macro_totals`, macro controls row, `_build_macro_spider`, `toggle_macro_chart_type` callback.

#### FB-10 · Review-Level Evidence for Dimension Scores
- **Source:** BT · **Status:** DONE
- **Rationale:** "Which reviews drive this score?" Top-3 evidence cards with rank badges, reviewer name, tier/score, and text snippet.
- **Scope:** `_build_evidence_cards` function, `dna-evidence-cards` container, updated `handle_entity_pie_click` callback (8 outputs).

### Sprint 3

#### FB-11 · Benchmarks Tab: Premier Pool Deep-Dive
- **Source:** ZM / BT · **Status:** DONE
- **Rationale:** There's a lot more to say about the premier benchmark group. What's the composition? How many firms vs advisors? What does the review count distribution look like? What are the dimension averages and spreads?
- **Scope:** New page content for `/benchmarks`. Stats cards, composition breakdowns, dimension distribution visuals at both advisor and firm level.

#### FB-12 · Benchmarks Tab: Population Distribution Charts
- **Source:** ZM · **Status:** DONE
- **Rationale:** Show where all entities fall on each dimension — histograms or violin plots with a "you are here" marker for a selected entity.
- **Scope:** New chart builders, entity selector integration on benchmarks page.

#### FB-13 · Benchmarks Tab: Peer Percentile Summary Card
- **Source:** ZM · **Status:** DONE
- **Rationale:** At-a-glance card: selected entity's scores vs P25/P50/P75 benchmarks across all 6 dimensions. Quick "strengths & gaps" view.
- **Scope:** New summary component, API integration for breakpoints.

#### FB-14 · Leaderboard Tab: Dimension Leaderboard
- **Source:** COLLAB · **Status:** DONE
- **Rationale:** Advisors and firms want to know who's at the top per dimension. Filterable by entity type and pool.
- **Scope:** New `/leaderboard` page. Top-N entities per dimension with score bars.

#### FB-15 · Leaderboard Tab: Detail Cards
- **Source:** ZM · **Status:** DONE
- **Rationale:** Click a leaderboard entity to see its full dimension profile inline — avoids navigating away.
- **Scope:** Expandable detail panel within the leaderboard page.

#### FB-16 · Comparisons Tab: Intra-Firm Team Comparison
- **Source:** BT · **Status:** DONE
- **Rationale:** Multi-advisor firms want to see advisors side-by-side. Brian confirmed `partner_group` field will be available; mock data for now.
- **Scope:** New `/comparisons` page. Side-by-side radar/bar chart, firm selector, advisor checklist. Disclaimer banner for synthetic data.

#### FB-17 · Comparisons Tab: Entity-to-Entity Comparison
- **Source:** BT · **Status:** DONE
- **Rationale:** "Compare to another advisor" — select any two entities for head-to-head dimension overlay.
- **Scope:** Dual-entity selector, overlay chart on comparisons page.

#### FB-18 · Mock Partner Group Data
- **Source:** BT · **Status:** DONE
- **Rationale:** Brian suggested adding a dummy `partner_group` field to mock intra-firm associations until the real export is available.
- **Decision:** Generate synthetic partner groups for ~10 fake firm clusters using existing advisor data. Include a prominent "Synthetic Data" disclaimer.
- **Scope:** Script to generate mock data, updated `advisor_dimension_scores.csv` or supplemental CSV.

### Backlog

#### FB-19 · Keyword Highlighting in Reviews
- **Source:** COLLAB · **Status:** DEFERRED
- **Rationale:** Highlight words contributing to each dimension score (TF-IDF overlap approach).

#### FB-20 · Dimension Trend Over Time
- **Source:** BT · **Status:** DEFERRED
- **Rationale:** "Your Life Event Support score has trended up over 12 months." Needs timestamped scoring pipeline.

#### FB-21 · External Review Ingestion
- **Source:** BT · **Status:** DEFERRED
- **Rationale:** Benchmark beyond Wealthtender's proprietary dataset (Google Reviews, DFA Surveys). Architecture-level change, Phase 2+.

#### FB-22 · National Network Comparison
- **Source:** BT · **Status:** DEFERRED
- **Rationale:** Cross-network comparison using compliance portal hierarchy data. Requires external data source.

---

## Change Log

| Date | Items | What Changed |
|------|-------|-------------|
| 2026-03-09 | FB-01 through FB-22 | Initial feedback synthesis. Sprint 1 & 2 planned and executed. |
| 2026-03-09 | FB-01–FB-07 | Sprint 1 completed: dimension rename, percentile default, pie→bar, spider fix, token→word, stopwords, time granularity. |
| 2026-03-09 | FB-08–FB-10 | Sprint 2 completed: confidence tiers, premier pool toggle, macro controls, evidence cards. |
| 2026-03-09 | FB-11–FB-18 | Sprint 3 planned: Benchmarks tab (FB-11/12/13), Leaderboard tab (FB-14/15), Comparisons tab (FB-16/17/18). |
| 2026-03-09 | FB-19–FB-22 | Backlog renumbered: keyword highlighting, dimension trends, external ingestion, national network. |
| 2026-03-09 | README | Updated to reflect Sprints 1-2 features and Sprint 3 plan. |
| 2026-03-09 | FB-11–FB-18 | Sprint 3 completed: Benchmarks page (pool stats, histograms, percentile table), Leaderboard page (top-N bars, detail cards), Comparisons page (team spider/bar, head-to-head overlay). New API endpoints, mock partner groups, roles/nav updated. |
