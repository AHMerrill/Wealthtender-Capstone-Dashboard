# Future Work

Technical debt, deferred cleanup, and enhancement ideas. Items here are not bugs — they are intentional deferrals that can be picked up when the project stabilizes.

See [CHANGELOG.md](./CHANGELOG.md) for completed work.

---

## Pipeline & Data

### Variable Renaming Consistency
**Priority:** Medium | **Added:** 2026-03-10

The internal data keys (e.g., `listening_personalization`) do not always match the frontend display labels (e.g., "Customer Empathy & Personalization"). A consistent rename across the pipeline output columns, `constants.py`, `config.py`, API responses, and dashboard code would reduce confusion. Deferred to avoid breaking changes mid-project — do this in a single coordinated pass when the codebase is otherwise stable.

**Files involved:** `pipeline/config.py` (DIMENSION_QUERIES keys), `dashboard/constants.py` (DIMENSIONS dict), `api/services/artifacts.py` (column name expectations), all scoring CSVs.

### Consolidate Embedding Passes (Stage 2 + 2b)
**Priority:** Low | **Added:** 2026-03-10

Stage 2 (`run()`) and Stage 2b (`run_weighted()`) are two separate embedding passes with different settings:
- **Text processing:** Stage 2 does aggressive stopword removal, prompt stripping, and per-token advisor name removal. Stage 2b does only a simple full-name replacement.
- **Normalization:** Stage 2 uses `normalize_embeddings=True` (unit vectors). Stage 2b uses `normalize_embeddings=False` (norms vary ~0.3–0.9).

Unifying them would mean choosing ONE text processing approach and ONE normalization setting, which would change the output of at least one path. This would require re-baselining all weighted scores and verifying downstream dashboard behavior. Not worth doing until the project is in maintenance mode.

### Database Migration
**Priority:** Low | **Added:** 2026-03-10

The current pipeline reads/writes flat files. For a production system with continuous review ingestion, swap `pd.read_csv` for `pd.read_sql` in `clean.py` and write artifacts to database tables. The API is already storage-agnostic (receives DataFrames, serves JSON). See README Section 5 "Where Data Lives and How to Change It" for the 4-step migration guide.

---

## Dashboard & Frontend

### Keyword Highlighting in Evidence Cards
**Priority:** Low | **Added:** 2026-03-09 (FB-19)

Highlight dimension-relevant keywords in the evidence card review snippets so users can quickly see which words drove the similarity score.

### Dimension Trends Over Time
**Priority:** Low | **Added:** 2026-03-09 (FB-20)

Add a time-series view showing how an entity's dimension scores evolve as new reviews arrive. Requires storing historical score snapshots or computing scores on rolling windows.

### External Data Ingestion
**Priority:** Medium | **Added:** 2026-03-09 (FB-21)

Allow ingestion of reviews from external platforms (Google, Yelp, etc.) alongside Wealthtender-native reviews. Requires a normalization layer to map external schemas to the internal review format.

### National Network Benchmarks
**Priority:** Low | **Added:** 2026-03-09 (FB-22)

Enable cross-network benchmarking so advisors can compare their scores against a broader national peer group rather than just the Wealthtender corpus.

---

## Infrastructure

### Production Auth Upgrade
**Priority:** High (for production) | **Added:** 2026-03-09

Replace the prototype auth (shared password + dropdown) with SSO/OAuth. See README Section 15 for the full roadmap: SSO integration, JWT-based API auth, role injection from identity tokens, CORS lockdown.

### LLM-Enhanced Scoring Pipeline
**Priority:** Medium | **Added:** 2026-03-10

Address cosine similarity limitations (short reviews score low, implied meaning invisible) by adding an LLM pass. Three options outlined in README Section 5: (A) LLM-expanded embeddings before encoding, (B) score blending with LLM confidence weights, (C) LLM as confidence filter for edge cases. Option A is recommended as the first step.
