import html as _html
import json
import logging
import re
from collections import Counter
from pathlib import Path
from typing import Optional, List, Dict, Any

import pandas as pd

log = logging.getLogger(__name__)


def _sanitize_records(df: pd.DataFrame) -> list:
    """Convert DataFrame to list of dicts with NaN replaced by None.

    This ensures valid JSON (NaN is not a valid JSON value).
    """
    return df.where(df.notna(), None).to_dict(orient="records")

# --------------------------------------------------------------------------------------
# Paths / constants
# --------------------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_METADATA = ROOT / "artifacts" / "metadata.json"

# NLTK english stopwords (nltk.corpus.stopwords.words("english")) -- vendored
# to avoid adding NLTK as a dependency.  This is the exact frozen set from
# NLTK 3.8.1 so the dashboard matches standard NLP practice.
STOPWORDS: set[str] = {
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you",
    "you're", "you've", "you'll", "you'd", "your", "yours", "yourself",
    "yourselves", "he", "him", "his", "himself", "she", "she's", "her",
    "hers", "herself", "it", "it's", "its", "itself", "they", "them",
    "their", "theirs", "themselves", "what", "which", "who", "whom", "this",
    "that", "that'll", "these", "those", "am", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "having", "do", "does",
    "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because",
    "as", "until", "while", "of", "at", "by", "for", "with", "about",
    "against", "between", "through", "during", "before", "after", "above",
    "below", "to", "from", "up", "down", "in", "out", "on", "off", "over",
    "under", "again", "further", "then", "once", "here", "there", "when",
    "where", "why", "how", "all", "both", "each", "few", "more", "most",
    "other", "some", "such", "no", "nor", "not", "only", "own", "same",
    "so", "than", "too", "very", "s", "t", "can", "will", "just", "don",
    "don't", "should", "should've", "now", "d", "ll", "m", "o", "re",
    "ve", "y", "ain", "aren", "aren't", "couldn", "couldn't", "didn",
    "didn't", "doesn", "doesn't", "hadn", "hadn't", "hasn", "hasn't",
    "haven", "haven't", "isn", "isn't", "ma", "mightn", "mightn't",
    "mustn", "mustn't", "needn", "needn't", "shan", "shan't", "shouldn",
    "shouldn't", "wasn", "wasn't", "weren", "weren't", "won", "won't",
    "wouldn", "wouldn't",
    "nbsp", "amp",
}

# Sorted list for the frontend dropdown (exported via /api/stopwords)
STOPWORDS_SORTED: list[str] = sorted(STOPWORDS)


def _tokenize_simple(s: str) -> list[str]:
    """Tokenizer matching the notebook's tokenize_simple exactly.

    Lowercases, strips non-alphanumeric (keeping apostrophes), collapses
    whitespace, and drops single-character tokens.
    """
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s']", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return [w for w in s.split() if len(w) > 1]


# --------------------------------------------------------------------------------------
# Artifact Store
# --------------------------------------------------------------------------------------

class ArtifactStore:
    """
    Capability-aware artifact loader.

    This class intentionally supports two valid operating modes:
      1) Firm-scoped datasets (scores contain firm_id)
      2) Global-only datasets (EDA without firms)

    All public methods degrade gracefully when a capability is unavailable.
    """

    def __init__(self, metadata_path: Optional[Path] = None) -> None:
        self.metadata_path = metadata_path or DEFAULT_METADATA
        self.metadata = self._load_metadata()

        # Core tables
        self.scores = self._load_table("scores")
        self.benchmarks = self._load_table("benchmarks")
        self.themes = self._load_table("themes")

        # EDA artifacts (property names match metadata.json manifest keys)
        self.macro_reviews_clean = self._load_table("macro_reviews_clean")
        self.macro_eda_summary = self._load_json("macro_eda_summary")
        self.macro_coverage = self._load_json("macro_coverage")
        self.macro_quality_summary = self._load_json("macro_quality_summary")
        self.macro_raw_file_meta = self._load_json("macro_raw_file_meta")
        self.macro_missing_report = self._load_table("macro_missing_report")
        self.macro_top_tokens = self._load_table("macro_top_tokens")
        self.macro_top_bigrams = self._load_table("macro_top_bigrams")

        # Advisor DNA scoring artifacts
        self.review_dim_scores = self._load_table("review_dimension_scores")
        self.advisor_dim_scores = self._load_table("advisor_dimension_scores")
        self._dna_macro_cache: Optional[list] = None
        self._enrich_review_dim_scores()
        self._enrich_advisor_review_counts()

        # Partner groups (mock data for intra-firm comparison)
        pg_path = ROOT / "artifacts" / "scoring" / "partner_groups_mock.csv"
        if pg_path.is_file():
            self.partner_groups = pd.read_csv(pg_path, encoding="utf-8")
        else:
            self.partner_groups = pd.DataFrame()

        # Capabilities
        self.has_firms = (
            not self.scores.empty
            and "firm_id" in self.scores.columns
            and "advisor_id" in self.scores.columns
        )

        self._prepare_reviews()

    # ----------------------------------------------------------------------------------
    # Loading helpers
    # ----------------------------------------------------------------------------------

    def _load_metadata(self) -> dict:
        if not self.metadata_path.exists():
            log.warning("metadata.json not found at %s", self.metadata_path)
            return {"artifact_manifest": []}
        try:
            return json.loads(self.metadata_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            log.error("Failed to load metadata.json: %s", exc)
            return {"artifact_manifest": []}

    def _get_manifest_item(self, name: str) -> Optional[dict]:
        manifest = {
            item.get("name"): item
            for item in self.metadata.get("artifact_manifest", [])
        }
        return manifest.get(name)

    def _load_table(self, name: str) -> pd.DataFrame:
        item = self._get_manifest_item(name)
        if not item:
            return pd.DataFrame()

        path = ROOT / item.get("path", "")
        file_type = item.get("type")

        if not path.is_file():
            log.warning("Artifact '%s' not found at %s", name, path)
            return pd.DataFrame()

        try:
            if file_type == "csv":
                df = pd.read_csv(path, encoding="utf-8")
            elif file_type == "json":
                df = pd.DataFrame(json.loads(path.read_text(encoding="utf-8")))
            elif file_type == "parquet":
                df = pd.read_parquet(path)
            else:
                log.warning("Unknown file type '%s' for artifact '%s'", file_type, name)
                return pd.DataFrame()

            # Unescape HTML entities (e.g. &amp; -> &) in string columns
            for col in df.select_dtypes(include="object").columns:
                df[col] = df[col].map(
                    lambda v: _html.unescape(v) if isinstance(v, str) else v
                )
            return df
        except Exception as exc:
            log.error("Failed to load artifact '%s' from %s: %s", name, path, exc)
            return pd.DataFrame()

    def _load_json(self, name: str) -> dict:
        item = self._get_manifest_item(name)
        if not item:
            return {}
        path = ROOT / item.get("path", "")
        if path.is_file():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                log.error("Failed to load JSON artifact '%s' from %s: %s",
                          name, path, exc)
                return {}
        log.warning("JSON artifact '%s' not found at %s", name, path)
        return {}

    # ----------------------------------------------------------------------------------
    # Preparation
    # ----------------------------------------------------------------------------------

    def _prepare_reviews(self) -> None:
        if self.macro_reviews_clean.empty:
            return

        df = self.macro_reviews_clean.copy()

        if "review_date" in df.columns:
            df["review_date"] = pd.to_datetime(df["review_date"], errors="coerce")

        if "clean_token_count" in df.columns and "token_count" not in df.columns:
            df["token_count"] = df["clean_token_count"]

        if self.has_firms and "advisor_id" in df.columns:
            advisor_firm = (
                self.scores[["advisor_id", "firm_id"]]
                .drop_duplicates()
            )
            df = df.merge(advisor_firm, on="advisor_id", how="left")

        self.macro_reviews_clean = df

    # ----------------------------------------------------------------------------------
    # Firm-facing endpoints
    # ----------------------------------------------------------------------------------

    def list_firms(self) -> List[Dict]:
        if not self.has_firms:
            return []
        firms = (
            self.scores[["firm_id"]]
            .drop_duplicates()
            .sort_values("firm_id")
        )
        return [{"firm_id": fid} for fid in firms["firm_id"].tolist()]

    def firm_summary(self, firm_id: str) -> Optional[Dict]:
        if not self.has_firms:
            return None
        df = self.scores[self.scores["firm_id"] == firm_id]
        if df.empty:
            return None
        return {
            "firm_id": firm_id,
            "advisor_count": int(df["advisor_id"].nunique()),
            "dimension_count": int(df["dimension"].nunique()) if "dimension" in df.columns else 0,
            "avg_score": round(float(df["score"].mean()), 2) if "score" in df.columns else None,
            "avg_confidence": round(float(df["confidence"].mean()), 2) if "confidence" in df.columns else None,
        }

    def firm_dimensions(self, firm_id: str) -> Optional[List[Dict]]:
        if not self.has_firms:
            return None
        df = self.scores[self.scores["firm_id"] == firm_id]
        if df.empty or "dimension" not in df.columns:
            return None
        summary = (
            df.groupby("dimension")[["score", "confidence", "review_count"]]
            .mean(numeric_only=True)
            .reset_index()
            .sort_values("score", ascending=False)
        )
        return _sanitize_records(summary)

    def firm_advisors(self, firm_id: str) -> Optional[List[Dict]]:
        if not self.has_firms:
            return None
        df = self.scores[self.scores["firm_id"] == firm_id]
        if df.empty:
            return None
        summary = (
            df.groupby("advisor_id")[["score", "confidence", "review_count"]]
            .mean(numeric_only=True)
            .reset_index()
        )
        return _sanitize_records(summary)

    def advisor_detail(self, firm_id: str, advisor_id: str) -> Optional[Dict]:
        if not self.has_firms:
            return None
        df = self.scores[
            (self.scores["firm_id"] == firm_id)
            & (self.scores["advisor_id"] == advisor_id)
        ]
        if df.empty:
            return None
        themes = (
            self.themes[self.themes["advisor_id"] == advisor_id]
            if not self.themes.empty and "advisor_id" in self.themes.columns
            else pd.DataFrame()
        )
        return {
            "advisor_id": advisor_id,
            "firm_id": firm_id,
            "scores": _sanitize_records(df),
            "themes": _sanitize_records(themes),
        }

    def review_detail(self, review_id: str) -> Optional[Dict[str, Any]]:
        df = self.macro_reviews_clean
        if df.empty or "ID" not in df.columns:
            return None
        match = df[df["ID"].astype(str) == str(review_id)]
        if match.empty:
            return None
        row = match.iloc[0]
        review_date = row.get("review_date")
        if pd.isna(review_date):
            review_date = None
        elif hasattr(review_date, "isoformat"):
            review_date = review_date.isoformat()
        rating = row.get("rating")
        if pd.isna(rating):
            rating = None
        token_count = row.get("token_count")
        if pd.isna(token_count):
            token_count = None
        else:
            try:
                token_count = int(token_count)
            except (TypeError, ValueError):
                token_count = None
        return {
            "review_id": str(row.get("ID")),
            "title": row.get("Title"),
            "content": row.get("Content"),
            "review_date": review_date,
            "rating": float(rating) if rating is not None else None,
            "token_count": token_count,
            "advisor_name": row.get("advisor_name"),
            "reviewer_name": row.get("reviewer_name"),
            "review_url": row.get("notification_page"),
        }

    def firm_benchmarks(self, firm_id: str) -> Optional[List[Dict]]:
        if not self.has_firms or self.benchmarks.empty:
            return None
        return _sanitize_records(self.benchmarks)

    def firm_personas(self, firm_id: str) -> Optional[List[Dict]]:
        if not self.has_firms:
            return None
        df = self.scores[self.scores["firm_id"] == firm_id]
        if df.empty:
            return None
        personas = (
            df.groupby("advisor_id")["score"]
            .mean()
            .reset_index()
            .assign(persona=lambda d: d["score"].apply(_score_to_persona))
        )
        return _sanitize_records(personas)

    def _enrich_review_dim_scores(self):
        """Join reviewer_name and review_date from reviews_clean into scoring data."""
        if self.review_dim_scores.empty or self.macro_reviews_clean.empty:
            return
        clean = self.macro_reviews_clean
        enrich_cols = []
        if "reviewer_name" in clean.columns:
            enrich_cols.append("reviewer_name")
        if "review_date" in clean.columns:
            enrich_cols.append("review_date")
        if not enrich_cols:
            return
        extra = clean[enrich_cols].copy()
        extra.index = range(len(extra))
        scores = self.review_dim_scores
        for col in enrich_cols:
            if col not in scores.columns and not scores.empty and scores.index.max() < len(extra):
                scores[col] = scores["review_idx"].map(extra[col])
        self.review_dim_scores = scores

    def _enrich_advisor_review_counts(self):
        """Add review_count column to advisor_dim_scores from review-level data.

        If the pipeline already baked review_count into the CSV (score.py),
        this is a no-op.  Otherwise it computes counts from review-level data.
        """
        if "review_count" in self.advisor_dim_scores.columns:
            self.advisor_dim_scores["review_count"] = (
                self.advisor_dim_scores["review_count"].fillna(0).astype(int))
            return
        if self.advisor_dim_scores.empty or self.review_dim_scores.empty:
            return
        counts = self.review_dim_scores.groupby("advisor_id").size().rename("review_count")
        self.advisor_dim_scores = self.advisor_dim_scores.merge(
            counts, on="advisor_id", how="left")
        self.advisor_dim_scores["review_count"] = (
            self.advisor_dim_scores["review_count"].fillna(0).astype(int))

    # ----------------------------------------------------------------------------------
    # Advisor DNA
    # ----------------------------------------------------------------------------------

    _SIM_DIMS = [
        "trust_integrity", "listening_personalization", "communication_clarity",
        "responsiveness_availability", "life_event_support", "investment_expertise",
    ]
    _REVIEW_SIM_COLS = [f"sim_{d}" for d in _SIM_DIMS]

    # ------------------------------------------------------------------
    # Score enrichment helpers (percentile, normalized, tier)
    # ------------------------------------------------------------------

    _TIER_LABELS = ("Very Strong", "Strong", "Moderate", "Foundational")

    def _tier_from_percentile(self, pctile: float) -> str:
        """Assign a tier label from a percentile rank (0-100)."""
        if pctile >= 75:
            return self._TIER_LABELS[0]
        if pctile >= 50:
            return self._TIER_LABELS[1]
        if pctile >= 25:
            return self._TIER_LABELS[2]
        return self._TIER_LABELS[3]

    def _enrich_scores(self, entity_id: str, method: str,
                       raw_scores: Dict[str, float]) -> Dict[str, Dict]:
        """Enrich raw dimension scores with percentile, normalized, and tier.

        Returns a dict keyed by dimension with sub-dict:
            {"raw", "percentile", "normalized", "tier"}
        """
        if self.advisor_dim_scores.empty:
            return {d: {"raw": v, "percentile": None, "normalized": None,
                        "tier": None} for d, v in raw_scores.items()}

        row = self.advisor_dim_scores[
            self.advisor_dim_scores["advisor_id"] == entity_id]
        if row.empty:
            return {d: {"raw": v, "percentile": None, "normalized": None,
                        "tier": None} for d, v in raw_scores.items()}

        entity_type = row.iloc[0]["entity_type"]
        peers = self.advisor_dim_scores[
            self.advisor_dim_scores["entity_type"] == entity_type].copy()

        enriched = {}
        for d in self._SIM_DIMS:
            col = f"sim_{method}_{d}"
            raw = raw_scores.get(d, 0.0)
            if col not in peers.columns or peers[col].dropna().empty:
                enriched[d] = {"raw": raw, "percentile": None,
                               "normalized": None, "tier": None}
                continue

            # Percentile rank (0-100)
            peers[f"_prank_{d}"] = peers[col].rank(pct=True)
            entity_row = peers[peers["advisor_id"] == entity_id]
            pctile = round(float(entity_row.iloc[0][f"_prank_{d}"]) * 100, 1) \
                if not entity_row.empty else 0.0

            # Normalized 0-100 (min-max rescale across same entity_type)
            col_min = float(peers[col].min())
            col_max = float(peers[col].max())
            if col_max > col_min:
                norm = round((raw - col_min) / (col_max - col_min) * 100, 1)
            else:
                norm = 50.0  # all peers identical

            enriched[d] = {
                "raw": round(raw, 6),
                "percentile": pctile,
                "normalized": norm,
                "tier": self._tier_from_percentile(pctile),
            }
        return enriched

    def _compute_composite(self, raw_scores: Dict[str, float]) -> float:
        """Mean across all 6 dimensions (mirrors former frontend calculation)."""
        vals = [raw_scores.get(d, 0.0) for d in self._SIM_DIMS]
        return sum(vals) / len(vals) if vals else 0.0

    def dna_macro_sample(self, n: int = 100, seed: int = 42) -> list:
        """Return a sampled subset of reviews (for macro-level network visualizations).

        Args:
            n: Maximum sample size (capped at available reviews).
            seed: Random state for reproducible sampling.
        """
        if self.review_dim_scores.empty:
            return []
        if self._dna_macro_cache is not None:
            return self._dna_macro_cache
        sample = self.review_dim_scores.sample(n=min(n, len(self.review_dim_scores)),
                                               random_state=seed)
        cols = ["review_idx", "advisor_id", "advisor_name", "entity_type"] + self._REVIEW_SIM_COLS
        self._dna_macro_cache = _sanitize_records(sample[[c for c in cols if c in sample.columns]])
        return self._dna_macro_cache

    def dna_macro_totals(self, min_peer_reviews: int = 0) -> dict:
        """Return aggregate dimension totals across reviews.

        min_peer_reviews: if > 0, only include reviews belonging to entities
        with at least this many reviews (premier filtering).
        """
        if self.review_dim_scores.empty:
            return {}
        df = self.review_dim_scores
        if min_peer_reviews > 0 and not self.advisor_dim_scores.empty:
            # Get entities that meet the threshold
            if "review_count" in self.advisor_dim_scores.columns:
                premier_ids = set(
                    self.advisor_dim_scores[
                        self.advisor_dim_scores["review_count"] >= min_peer_reviews
                    ]["advisor_id"]
                )
                df = df[df["advisor_id"].isin(premier_ids)]
        if df.empty:
            return {}
        totals = {}
        for col in self._REVIEW_SIM_COLS:
            if col in df.columns:
                totals[col] = float(df[col].sum())
        return {"totals": totals, "review_count": len(df)}

    def dna_entity_list(self) -> Dict[str, list]:
        if self.advisor_dim_scores.empty:
            return {"firms": [], "advisors": []}
        cols = ["advisor_id", "advisor_name", "entity_type"]
        if "review_count" in self.advisor_dim_scores.columns:
            cols.append("review_count")
        df = self.advisor_dim_scores[cols].drop_duplicates()
        out_cols = ["advisor_id", "advisor_name"]
        if "review_count" in df.columns:
            out_cols.append("review_count")
        firms = _sanitize_records(df[df["entity_type"] == "firm"][out_cols])
        advisors = _sanitize_records(df[df["entity_type"] == "advisor"][out_cols])
        return {"firms": firms, "advisors": advisors}

    def dna_entity_reviews(self, entity_id: str) -> Optional[list]:
        if self.review_dim_scores.empty:
            return None
        df = self.review_dim_scores[self.review_dim_scores["advisor_id"] == entity_id]
        if df.empty:
            return None
        cols = ["review_idx", "advisor_id", "advisor_name", "entity_type",
                "review_text_raw", "reviewer_name", "review_date"] + self._REVIEW_SIM_COLS
        return _sanitize_records(df[[c for c in cols if c in df.columns]])

    def dna_advisor_scores(self, entity_id: str, method: str = "mean") -> Optional[Dict]:
        """Return dimension scores enriched with percentile, normalized, and tier.

        Response shape per dimension:
            {"raw": float, "percentile": float, "normalized": float, "tier": str}
        Also includes a composite score with the same enrichment.
        """
        if self.advisor_dim_scores.empty:
            return None
        df = self.advisor_dim_scores[self.advisor_dim_scores["advisor_id"] == entity_id]
        if df.empty:
            return None
        row = df.iloc[0]
        sim_cols = [f"sim_{method}_{d}" for d in self._SIM_DIMS]
        missing = [c for c in sim_cols if c not in df.columns]
        if missing:
            return None
        raw_scores = {d: float(row[f"sim_{method}_{d}"]) for d in self._SIM_DIMS}
        enriched = self._enrich_scores(entity_id, method, raw_scores)

        # Composite (average of raw scores, then enrich vs peers)
        composite_raw = self._compute_composite(raw_scores)
        # Compute composite percentile/normalized vs all peers of same type
        entity_type = row["entity_type"]
        peers = self.advisor_dim_scores[
            self.advisor_dim_scores["entity_type"] == entity_type].copy()
        comp_pctile = None
        comp_norm = None
        comp_tier = None
        if not peers.empty:
            peer_composites = peers.apply(
                lambda r: sum(float(r.get(f"sim_{method}_{d}", 0))
                              for d in self._SIM_DIMS) / len(self._SIM_DIMS),
                axis=1)
            peers["_composite"] = peer_composites
            peers["_comp_rank"] = peers["_composite"].rank(pct=True)
            entity_row = peers[peers["advisor_id"] == entity_id]
            if not entity_row.empty:
                comp_pctile = round(float(entity_row.iloc[0]["_comp_rank"]) * 100, 1)
                c_min, c_max = float(peers["_composite"].min()), float(peers["_composite"].max())
                if c_max > c_min:
                    comp_norm = round((composite_raw - c_min) / (c_max - c_min) * 100, 1)
                else:
                    comp_norm = 50.0
                comp_tier = self._tier_from_percentile(comp_pctile)

        enriched["composite"] = {
            "raw": round(composite_raw, 6),
            "percentile": comp_pctile,
            "normalized": comp_norm,
            "tier": comp_tier,
        }

        return {
            "advisor_id": row["advisor_id"],
            "advisor_name": row["advisor_name"],
            "entity_type": row["entity_type"],
            "method": method,
            "review_count": int(row.get("review_count", 0)),
            "scores": enriched,
        }

    def dna_percentile_scores(self, entity_id: str, method: str = "mean",
                              min_peer_reviews: int = 0) -> Optional[Dict]:
        """Percentile rank of this entity vs peers of the same type, per dimension.

        min_peer_reviews: if > 0, only include peers with at least this many
        reviews in the comparison pool (premier benchmarking).  The target
        entity is always included regardless of its own review count.
        """
        if self.advisor_dim_scores.empty:
            return None
        all_df = self.advisor_dim_scores
        match = all_df[all_df["advisor_id"] == entity_id]
        if match.empty:
            return None
        entity_type = match.iloc[0]["entity_type"]
        peers = all_df[all_df["entity_type"] == entity_type].copy()

        # Premier filter: restrict peer pool but always keep the target entity
        if min_peer_reviews > 0 and "review_count" in peers.columns:
            peers = peers[
                (peers["review_count"] >= min_peer_reviews) |
                (peers["advisor_id"] == entity_id)
            ]

        sim_cols = [f"sim_{method}_{d}" for d in self._SIM_DIMS]
        if any(c not in peers.columns for c in sim_cols):
            return None
        for d in self._SIM_DIMS:
            col = f"sim_{method}_{d}"
            peers[f"_pctrank_{d}"] = peers[col].rank(pct=True)
        entity_row = peers[peers["advisor_id"] == entity_id].iloc[0]
        scores = {d: round(float(entity_row[f"_pctrank_{d}"]) * 100, 1)
                  for d in self._SIM_DIMS}

        # Include review_count and premier flag in response
        entity_review_count = int(entity_row.get("review_count", 0))
        return {
            "advisor_id": entity_row["advisor_id"],
            "advisor_name": entity_row["advisor_name"],
            "entity_type": entity_type,
            "method": method,
            "peer_count": len(peers),
            "review_count": entity_review_count,
            "premier": entity_review_count >= 20,  # Premier pool threshold (see data_contract)
            "scores": scores,
        }

    def dna_population_medians(self, method: str = "mean", entity_type: str = "firm") -> Dict:
        """Return per-dimension median similarity across all entities of a given type."""
        if self.advisor_dim_scores.empty:
            return {}
        peers = self.advisor_dim_scores[self.advisor_dim_scores["entity_type"] == entity_type]
        if peers.empty:
            return {}
        medians = {}
        for d in self._SIM_DIMS:
            col = f"sim_{method}_{d}"
            if col in peers.columns:
                medians[d] = float(peers[col].median())
        return medians

    def dna_method_breakpoints(self, method: str = "mean",
                               entity_type: str = "firm") -> Dict:
        """Return 25th/50th/75th percentile breakpoints per dimension for a method."""
        if self.advisor_dim_scores.empty:
            return {}
        peers = self.advisor_dim_scores[
            self.advisor_dim_scores["entity_type"] == entity_type]
        if peers.empty:
            return {}
        result = {}
        for d in self._SIM_DIMS:
            col = f"sim_{method}_{d}"
            if col in peers.columns:
                result[d] = {
                    "p25": float(peers[col].quantile(0.25)),
                    "p50": float(peers[col].quantile(0.50)),
                    "p75": float(peers[col].quantile(0.75)),
                }
        return result

    def dna_review_detail(self, review_idx: int) -> Optional[Dict]:
        if self.review_dim_scores.empty:
            return None
        df = self.review_dim_scores
        if "review_idx" not in df.columns:
            return None
        match = df[df["review_idx"] == review_idx]
        if match.empty:
            return None
        row = match.iloc[0]
        scores = {}
        for d in self._SIM_DIMS:
            col = f"sim_{d}"
            scores[d] = float(row[col]) if col in row.index and pd.notna(row[col]) else None
        return {
            "review_idx": int(row["review_idx"]),
            "advisor_id": row.get("advisor_id"),
            "advisor_name": row.get("advisor_name"),
            "entity_type": row.get("entity_type"),
            "review_text": row.get("review_text_raw"),
            "reviewer_name": row.get("reviewer_name"),
            "review_date": str(row.get("review_date", "")) if pd.notna(row.get("review_date")) else "",
            "scores": scores,
        }

    # ----------------------------------------------------------------------------------
    # Benchmarks / Leaderboard / Comparisons
    # ----------------------------------------------------------------------------------

    def benchmark_pool_stats(self, min_peer_reviews: int = 20) -> Dict:
        """Premier pool composition: counts, review distributions, dimension stats."""
        if self.advisor_dim_scores.empty:
            return {}
        df = self.advisor_dim_scores.copy()
        if "review_count" not in df.columns:
            return {}
        premier = df[df["review_count"] >= min_peer_reviews]
        all_ent = df

        def _dim_stats(sub, method="mean"):
            stats = {}
            for d in self._SIM_DIMS:
                col = f"sim_{method}_{d}"
                if col in sub.columns:
                    vals = sub[col].dropna()
                    stats[d] = {
                        "mean": float(vals.mean()),
                        "median": float(vals.median()),
                        "std": float(vals.std()),
                        "p25": float(vals.quantile(0.25)),
                        "p75": float(vals.quantile(0.75)),
                        "min": float(vals.min()),
                        "max": float(vals.max()),
                    }
            return stats

        return {
            "all": {
                "total": int(len(all_ent)),
                "firms": int((all_ent["entity_type"] == "firm").sum()),
                "advisors": int((all_ent["entity_type"] == "advisor").sum()),
                "review_count_stats": {
                    "mean": float(all_ent["review_count"].mean()),
                    "median": float(all_ent["review_count"].median()),
                    "min": int(all_ent["review_count"].min()),
                    "max": int(all_ent["review_count"].max()),
                },
                "dim_stats": _dim_stats(all_ent),
            },
            "premier": {
                "total": int(len(premier)),
                "firms": int((premier["entity_type"] == "firm").sum()),
                "advisors": int((premier["entity_type"] == "advisor").sum()),
                "review_count_stats": {
                    "mean": float(premier["review_count"].mean()),
                    "median": float(premier["review_count"].median()),
                    "min": int(premier["review_count"].min()) if len(premier) else 0,
                    "max": int(premier["review_count"].max()) if len(premier) else 0,
                },
                "dim_stats": _dim_stats(premier),
            },
        }

    def benchmark_distributions(self, method: str = "mean",
                                 entity_type: str = "all",
                                 min_peer_reviews: int = 0) -> Dict:
        """Score distributions per dimension for histogram rendering."""
        if self.advisor_dim_scores.empty:
            return {}
        df = self.advisor_dim_scores.copy()
        if entity_type != "all":
            df = df[df["entity_type"] == entity_type]
        if min_peer_reviews > 0 and "review_count" in df.columns:
            df = df[df["review_count"] >= min_peer_reviews]
        result = {}
        for d in self._SIM_DIMS:
            col = f"sim_{method}_{d}"
            if col in df.columns:
                result[d] = df[col].dropna().tolist()
        return result

    def leaderboard(self, method: str = "mean", entity_type: str = "all",
                    min_peer_reviews: int = 0, top_n: int = 10,
                    dimension: str = "all") -> Dict:
        """Top-N entities per dimension (or composite).

        dimension: "all" returns all 6 + composite, or pass a single dim key
                   or "composite" to get just that one.

        Each entry is enriched with percentile, normalized, and tier.
        """
        if self.advisor_dim_scores.empty:
            return {}
        df = self.advisor_dim_scores.copy()
        if entity_type != "all":
            df = df[df["entity_type"] == entity_type]
        if min_peer_reviews > 0 and "review_count" in df.columns:
            df = df[df["review_count"] >= min_peer_reviews]
        if df.empty:
            return {}

        # Pre-compute percentile ranks and normalized scores for the pool
        pctile_ranks = {}
        norm_scores = {}
        for d in self._SIM_DIMS:
            col = f"sim_{method}_{d}"
            if col not in df.columns:
                continue
            df[f"_prank_{d}"] = df[col].rank(pct=True)
            pctile_ranks[d] = f"_prank_{d}"
            col_min, col_max = float(df[col].min()), float(df[col].max())
            if col_max > col_min:
                df[f"_norm_{d}"] = (df[col] - col_min) / (col_max - col_min) * 100
            else:
                df[f"_norm_{d}"] = 50.0
            norm_scores[d] = f"_norm_{d}"

        # Composite column
        sim_cols = [f"sim_{method}_{d}" for d in self._SIM_DIMS
                    if f"sim_{method}_{d}" in df.columns]
        if sim_cols:
            df["_composite_raw"] = df[sim_cols].mean(axis=1)
            df["_composite_prank"] = df["_composite_raw"].rank(pct=True)
            c_min, c_max = float(df["_composite_raw"].min()), float(df["_composite_raw"].max())
            if c_max > c_min:
                df["_composite_norm"] = (df["_composite_raw"] - c_min) / (c_max - c_min) * 100
            else:
                df["_composite_norm"] = 50.0

        def _build_entries(sub_df, dim_key, score_col):
            entries = []
            for _, row in sub_df.iterrows():
                raw = float(row[score_col])
                if dim_key == "composite":
                    pctile = round(float(row["_composite_prank"]) * 100, 1)
                    norm = round(float(row["_composite_norm"]), 1)
                else:
                    pctile = round(float(row[f"_prank_{dim_key}"]) * 100, 1) \
                        if f"_prank_{dim_key}" in row.index else None
                    norm = round(float(row[f"_norm_{dim_key}"]), 1) \
                        if f"_norm_{dim_key}" in row.index else None
                tier = self._tier_from_percentile(pctile) if pctile is not None else None
                entries.append({
                    "advisor_id": row["advisor_id"],
                    "advisor_name": row["advisor_name"],
                    "entity_type": row["entity_type"],
                    "score": round(raw, 6),
                    "percentile": pctile,
                    "normalized": norm,
                    "tier": tier,
                    "review_count": int(row.get("review_count", 0)),
                })
            return entries

        dims_to_compute = self._SIM_DIMS if dimension in ("all",) else (
            [] if dimension == "composite" else [dimension])

        result = {}
        for d in dims_to_compute:
            col = f"sim_{method}_{d}"
            if col not in df.columns:
                continue
            top = df.nlargest(top_n, col)
            result[d] = _build_entries(top, d, col)

        # Add composite if requested
        if dimension in ("all", "composite") and "_composite_raw" in df.columns:
            top_comp = df.nlargest(top_n, "_composite_raw")
            result["composite"] = _build_entries(top_comp, "composite", "_composite_raw")

        return result

    def leaderboard_entity_profile(self, entity_id: str,
                                    method: str = "mean") -> Optional[Dict]:
        """Full dimension profile for a leaderboard entity."""
        return self.dna_advisor_scores(entity_id, method)

    def partner_group_list(self) -> List[Dict]:
        """Return list of partner groups with member counts."""
        if self.partner_groups.empty:
            return []
        groups = self.partner_groups.groupby(
            ["partner_group_code", "partner_group_name"]
        ).size().reset_index(name="member_count")
        return _sanitize_records(groups)

    def partner_group_members(self, group_code: str,
                               method: str = "mean") -> Optional[Dict]:
        """Return advisors in a partner group with their dimension scores."""
        if self.partner_groups.empty:
            return None
        members = self.partner_groups[
            self.partner_groups["partner_group_code"] == group_code
        ]
        if members.empty:
            return None
        advisor_ids = members["advisor_id"].tolist()
        group_name = members.iloc[0]["partner_group_name"]
        profiles = []
        for aid in advisor_ids:
            scores = self.dna_advisor_scores(aid, method)
            if scores:
                profiles.append(scores)
        return {"group_code": group_code, "group_name": group_name,
                "members": profiles}

    def entity_comparison(self, entity_ids: List[str],
                           method: str = "mean") -> List[Dict]:
        """Return enriched dimension scores for multiple entities for comparison."""
        results = []
        for eid in entity_ids:
            scores = self.dna_advisor_scores(eid, method)
            if scores:
                results.append(scores)
        return results

    def head_to_head(self, entity_id_a: str, entity_id_b: str,
                     method: str = "mean") -> Optional[Dict]:
        """Full head-to-head comparison with diffs for every score type.

        Returns both entities' enriched profiles plus a diff dict showing
        the difference (B - A) for raw, percentile, and normalized per dimension.
        """
        a = self.dna_advisor_scores(entity_id_a, method)
        b = self.dna_advisor_scores(entity_id_b, method)
        if not a or not b:
            return None

        diffs = {}
        for d in list(self._SIM_DIMS) + ["composite"]:
            a_scores = a["scores"].get(d, {})
            b_scores = b["scores"].get(d, {})
            diff_entry = {}
            for key in ("raw", "percentile", "normalized"):
                a_val = a_scores.get(key)
                b_val = b_scores.get(key)
                if a_val is not None and b_val is not None:
                    diff_entry[key] = round(b_val - a_val, 4)
                else:
                    diff_entry[key] = None
            diffs[d] = diff_entry

        return {
            "entity_a": a,
            "entity_b": b,
            "diffs": diffs,
            "method": method,
        }

    # ----------------------------------------------------------------------------------
    # EDA
    # ----------------------------------------------------------------------------------

    def eda_payload(self, **kwargs) -> Dict[str, Any]:
        if self.macro_reviews_clean.empty:
            return {}

        preset = kwargs.get("preset")
        if preset == "eda":
            return self._eda_payload_from_df(
                self.macro_reviews_clean.copy(),
                kwargs.get("lexical_top_n", 20),
                preset="eda",
            )

        base_kwargs = {
            "scope": kwargs.get("scope"),
            "firm_id": kwargs.get("firm_id"),
            "advisor_id": kwargs.get("advisor_id"),
        }
        base_df = self._apply_eda_filters(**base_kwargs)
        filtered_df = self._apply_eda_filters(**kwargs)
        payload = self._eda_payload_from_df(
            filtered_df,
            kwargs.get("lexical_top_n", 20),
            lexical_n=kwargs.get("lexical_n", 1),
            exclude_stopwords=kwargs.get("exclude_stopwords", False),
            custom_stopwords=kwargs.get("custom_stopwords"),
            time_freq=kwargs.get("time_freq", "month"),
        )
        payload["meta"] = self._eda_meta(base_df)
        return payload

    def _apply_eda_filters(self, **kwargs) -> pd.DataFrame:
        df = self.macro_reviews_clean.copy()

        advisor_id = kwargs.get("advisor_id")
        if advisor_id and "advisor_id" in df.columns:
            df = df[df["advisor_id"] == advisor_id]
        elif kwargs.get("scope") == "firm" and self.has_firms:
            firm_id = kwargs.get("firm_id")
            if firm_id and "firm_id" in df.columns:
                df = df[df["firm_id"] == firm_id]

        if kwargs.get("date_start") and "review_date" in df.columns:
            df = df[df["review_date"] >= pd.to_datetime(kwargs["date_start"], errors="coerce")]

        if kwargs.get("date_end") and "review_date" in df.columns:
            df = df[df["review_date"] <= pd.to_datetime(kwargs["date_end"], errors="coerce")]

        if kwargs.get("rating") is not None and "rating" in df.columns:
            df = df[df["rating"] == kwargs["rating"]]

        if kwargs.get("min_tokens") is not None and "token_count" in df.columns:
            df = df[df["token_count"] >= kwargs["min_tokens"]]

        if kwargs.get("max_tokens") is not None and "token_count" in df.columns:
            df = df[df["token_count"] <= kwargs["max_tokens"]]

        # Reviews-per-advisor filter
        min_rpa = kwargs.get("min_reviews_per_advisor")
        max_rpa = kwargs.get("max_reviews_per_advisor")
        if (min_rpa is not None or max_rpa is not None) and "advisor_id" in df.columns:
            counts = df.groupby("advisor_id").size()
            if min_rpa is not None:
                counts = counts[counts >= min_rpa]
            if max_rpa is not None:
                counts = counts[counts <= max_rpa]
            df = df[df["advisor_id"].isin(counts.index)]

        return df

    # ----------------------------------------------------------------------------------
    # EDA helpers
    # ----------------------------------------------------------------------------------

    @staticmethod
    def _sanitize_payload(obj):
        """Replace NaN/inf with None so JSON serialization doesn't fail."""
        if isinstance(obj, dict):
            return {k: ArtifactStore._sanitize_payload(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [ArtifactStore._sanitize_payload(v) for v in obj]
        if isinstance(obj, float):
            import math
            if math.isnan(obj) or math.isinf(obj):
                return None
        return obj

    def _eda_payload_from_df(self, df: pd.DataFrame, lexical_top_n: int,
                             preset: Optional[str] = None,
                             lexical_n: int = 1,
                             exclude_stopwords: bool = False,
                             custom_stopwords: Optional[List[str]] = None,
                             time_freq: str = "month") -> Dict[str, Any]:
        payload = {
            "summary": self._eda_summary(df, preset),
            "quality": self._eda_quality(df, preset),
            "coverage": self._eda_coverage(df, preset),
            "rating_distribution": self._eda_rating_distribution(df),
            "reviews_over_time": self._eda_reviews_over_time(df, time_freq),
            "reviews_per_advisor": self._eda_reviews_per_advisor(df),
            "token_counts": self._eda_token_counts(df),
            "rating_vs_token": self._eda_rating_vs_token(df),
            "lexical": self._eda_lexical(df, lexical_top_n, preset, lexical_n,
                                         exclude_stopwords, custom_stopwords),
            "meta": self._eda_meta(df),
        }
        return self._sanitize_payload(payload)

    def _eda_meta(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty or "review_date" not in df.columns:
            return {}
        date_min = df["review_date"].min()
        date_max = df["review_date"].max()
        token_min = df["token_count"].min() if "token_count" in df.columns else None
        token_max = df["token_count"].max() if "token_count" in df.columns else None
        rating_min = df["rating"].min() if "rating" in df.columns else None
        rating_max = df["rating"].max() if "rating" in df.columns else None

        # Quartiles for dynamic category filters (Low / Medium / High)
        token_q1 = token_q3 = None
        if "token_count" in df.columns and not df["token_count"].dropna().empty:
            token_q1 = int(df["token_count"].quantile(0.25))
            token_q3 = int(df["token_count"].quantile(0.75))

        reviews_per_advisor_min = reviews_per_advisor_max = None
        rpa_q1 = rpa_q3 = None
        if "advisor_id" in df.columns:
            review_counts = df.groupby("advisor_id").size()
            reviews_per_advisor_min = int(review_counts.min())
            reviews_per_advisor_max = int(review_counts.max())
            rpa_q1 = int(review_counts.quantile(0.25))
            rpa_q3 = int(review_counts.quantile(0.75))

        return {
            "date_min": date_min.isoformat() if pd.notna(date_min) else None,
            "date_max": date_max.isoformat() if pd.notna(date_max) else None,
            "row_count": int(df.shape[0]),
            "token_min": int(token_min) if pd.notna(token_min) else None,
            "token_max": int(token_max) if pd.notna(token_max) else None,
            "token_q1": token_q1,
            "token_q3": token_q3,
            "rating_min": float(rating_min) if pd.notna(rating_min) else None,
            "rating_max": float(rating_max) if pd.notna(rating_max) else None,
            "reviews_per_advisor_min": reviews_per_advisor_min,
            "reviews_per_advisor_max": reviews_per_advisor_max,
            "rpa_q1": rpa_q1,
            "rpa_q3": rpa_q3,
        }

    def _eda_summary(self, df: pd.DataFrame, preset: Optional[str]) -> Dict[str, Any]:
        if preset == "eda" and self.macro_eda_summary:
            return self.macro_eda_summary
        if df.empty:
            return {}
        rating_counts = df["rating"].value_counts(dropna=False).sort_index() if "rating" in df.columns else []
        return {
            "reviews": int(df.shape[0]),
            "advisors": int(df["advisor_id"].nunique()) if "advisor_id" in df.columns else 0,
            "rating_counts": {str(k): int(v) for k, v in rating_counts.items()}
            if hasattr(rating_counts, "items") else {},
            "rev_per_adv_summary": self._review_count_summary(df),
            "token_count_summary": self._token_count_summary(df),
            "pct_under_20_tokens": self._pct_under_tokens(df, 20),
            "pct_under_50_tokens": self._pct_under_tokens(df, 50),
        }

    def _review_count_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        if "advisor_id" not in df.columns:
            return {}
        counts = df.groupby("advisor_id").size()
        return counts.describe().to_dict()

    def _token_count_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        if "token_count" not in df.columns:
            return {}
        return df["token_count"].describe().to_dict()

    def _pct_under_tokens(self, df: pd.DataFrame, threshold: int) -> float:
        if "token_count" not in df.columns or df.empty:
            return 0.0
        return float((df["token_count"] < threshold).mean())

    def _eda_quality(self, df: pd.DataFrame, preset: Optional[str]) -> Dict[str, Any]:
        if preset == "eda" and self.macro_quality_summary:
            return self.macro_quality_summary
        if df.empty:
            return {}
        rating_missing_frac = float(df["rating"].isna().mean()) if "rating" in df.columns else 0.0
        text_empty_frac = float(df["review_text_clean"].isna().mean()) if "review_text_clean" in df.columns else 0.0
        date_min = df["review_date"].min() if "review_date" in df.columns else None
        date_max = df["review_date"].max() if "review_date" in df.columns else None
        return {
            "n_rows": int(df.shape[0]),
            "n_cols": int(df.shape[1]),
            "n_advisors": int(df["advisor_id"].nunique()) if "advisor_id" in df.columns else 0,
            "n_names": int(df["reviewer_name"].nunique()) if "reviewer_name" in df.columns else 0,
            "date_min": date_min.isoformat() if pd.notna(date_min) else None,
            "date_max": date_max.isoformat() if pd.notna(date_max) else None,
            "rating_missing_frac": rating_missing_frac,
            "text_empty_frac": text_empty_frac,
        }

    def _eda_coverage(self, df: pd.DataFrame, preset: Optional[str]) -> Dict[str, Any]:
        if preset == "eda" and self.macro_coverage:
            return self.macro_coverage
        if df.empty or "advisor_id" not in df.columns:
            return {}
        counts = df.groupby("advisor_id").size()
        return {
            "advisors_total": int(counts.shape[0]),
            "pct_advisors_lt3": float((counts < 3).mean()),
            "pct_advisors_lt5": float((counts < 5).mean()),
            "pct_advisors_lt10": float((counts < 10).mean()),
            "median_reviews_per_advisor": float(counts.median()),
            "p90_reviews_per_advisor": float(counts.quantile(0.9)),
        }

    def _eda_rating_distribution(self, df: pd.DataFrame) -> List[Dict]:
        if df.empty or "rating" not in df.columns:
            return []
        return [
            {"rating": str(k), "count": int(v)}
            for k, v in df["rating"].value_counts(dropna=False).items()
        ]

    def _eda_reviews_over_time(self, df: pd.DataFrame,
                               time_freq: str = "month") -> List[Dict]:
        if df.empty or "review_date" not in df.columns:
            return []
        freq_map = {"month": "MS", "quarter": "QS", "year": "YS"}
        resample_code = freq_map.get(time_freq, "MS")
        fmt_map = {"month": "%Y-%m", "quarter": "%Y-Q", "year": "%Y"}
        date_fmt = fmt_map.get(time_freq, "%Y-%m")

        series = df.dropna(subset=["review_date"]).set_index("review_date").resample(resample_code).size()
        result = []
        for idx, val in series.items():
            if time_freq == "quarter":
                label = f"{idx.year}-Q{(idx.month - 1) // 3 + 1}"
            else:
                label = idx.strftime(date_fmt)
            result.append({"period": label, "count": int(val)})
        return result

    def _eda_reviews_per_advisor(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty or "advisor_id" not in df.columns:
            return {"counts": []}
        return {"counts": df.groupby("advisor_id").size().tolist()}

    def _eda_token_counts(self, df: pd.DataFrame) -> List[int]:
        if df.empty or "token_count" not in df.columns:
            return []
        return df["token_count"].dropna().astype(int).tolist()

    def _eda_rating_vs_token(self, df: pd.DataFrame) -> List[Dict]:
        if df.empty or "rating" not in df.columns or "token_count" not in df.columns:
            return []
        subset = df.dropna(subset=["rating", "token_count"])
        records = _sanitize_records(subset[["rating", "token_count"]])
        if "ID" in df.columns:
            ids = subset["ID"].astype(str).tolist()
            for record, review_id in zip(records, ids):
                record["review_id"] = review_id
        return records

    def _eda_lexical(self, df: pd.DataFrame, top_n: int,
                     preset: Optional[str], lexical_n: int,
                     exclude_stopwords: bool,
                     custom_stopwords: Optional[List[str]] = None) -> Dict[str, Any]:

        if preset == "eda":
            return {"top_ngrams": _sanitize_records(self.macro_top_tokens)}

        if df.empty or "review_text_clean" not in df.columns:
            return {"top_ngrams": []}

        # Build the active stopword set
        stop_set: set[str] = set()
        if exclude_stopwords:
            if custom_stopwords:
                # User picked specific words to exclude
                stop_set = {w.lower().strip() for w in custom_stopwords if w}
            else:
                # No custom list (None or empty) = use full NLTK defaults
                stop_set = STOPWORDS

        counter: Counter = Counter()
        for text in df["review_text_clean"].dropna().astype(str):
            parts = _tokenize_simple(text)
            if stop_set:
                parts = [p for p in parts if p not in stop_set]
            if lexical_n == 1:
                counter.update(parts)
            else:
                counter.update(
                    " ".join(parts[i:i+lexical_n])
                    for i in range(len(parts) - lexical_n + 1)
                )

        return {
            "top_ngrams": [
                {"ngram": k, "count": int(v)}
                for k, v in counter.most_common(top_n)
            ]
        }


# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------

def _score_to_persona(score: float) -> str:
    """Map a 0-100 composite score to a persona tier.

    Thresholds: Headliner >= 80, Opener >= 65, Indie < 65.
    """
    if score >= 80:
        return "Headliner"
    if score >= 65:
        return "Opener"
    return "Indie"
