import json
import re
from collections import Counter
from pathlib import Path
from typing import Optional, List, Dict, Any

import pandas as pd

# --------------------------------------------------------------------------------------
# Paths / constants
# --------------------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_METADATA = ROOT / "artifacts" / "metadata.json"

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but",
    "by", "can", "could", "did", "do", "does", "doing", "down", "during", "each", "few", "for",
    "from", "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself",
    "him", "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just",
    "me", "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once",
    "only", "or", "other", "our", "ours", "ourselves", "out", "over", "own", "same", "she",
    "should", "so", "some", "such", "than", "that", "the", "their", "theirs", "them", "themselves",
    "then", "there", "these", "they", "this", "those", "through", "to", "too", "under", "until",
    "up", "very", "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom",
    "why", "with", "you", "your", "yours", "yourself", "yourselves",
}


# --------------------------------------------------------------------------------------
# Artifact Store
# --------------------------------------------------------------------------------------

class ArtifactStore:
    """
    Capability-aware artifact loader.

    This class intentionally supports two valid operating modes:
      1) Firm-scoped datasets (scores contain firm_id)
      2) Global-only datasets (macro insights without firms)

    All public methods degrade gracefully when a capability is unavailable.
    """

    def __init__(self, metadata_path: Optional[Path] = None) -> None:
        self.metadata_path = metadata_path or DEFAULT_METADATA
        self.metadata = self._load_metadata()

        # Core tables
        self.scores = self._load_table("scores")
        self.benchmarks = self._load_table("benchmarks")
        self.themes = self._load_table("themes")

        # Macro artifacts
        self.macro_reviews_clean = self._load_table("macro_reviews_clean")
        self.macro_eda_summary = self._load_json("macro_eda_summary")
        self.macro_coverage = self._load_json("macro_coverage")
        self.macro_quality_summary = self._load_json("macro_quality_summary")
        self.macro_raw_file_meta = self._load_json("macro_raw_file_meta")
        self.macro_missing_report = self._load_table("macro_missing_report")
        self.macro_top_tokens = self._load_table("macro_top_tokens")
        self.macro_top_bigrams = self._load_table("macro_top_bigrams")

        # Capabilities
        self.has_firms = (
            not self.scores.empty
            and "firm_id" in self.scores.columns
            and "advisor_id" in self.scores.columns
        )

        self._prepare_macro_reviews()

    # ----------------------------------------------------------------------------------
    # Loading helpers
    # ----------------------------------------------------------------------------------

    def _load_metadata(self) -> dict:
        if not self.metadata_path.exists():
            return {"artifact_manifest": []}
        return json.loads(self.metadata_path.read_text())

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

        if not path.exists():
            return pd.DataFrame()

        try:
            if file_type == "csv":
                return pd.read_csv(path)
            if file_type == "json":
                return pd.DataFrame(json.loads(path.read_text()))
            if file_type == "parquet":
                return pd.read_parquet(path)
        except Exception:
            return pd.DataFrame()

        return pd.DataFrame()

    def _load_json(self, name: str) -> dict:
        item = self._get_manifest_item(name)
        if not item:
            return {}
        path = ROOT / item.get("path", "")
        if path.exists():
            try:
                return json.loads(path.read_text())
            except Exception:
                return {}
        return {}

    # ----------------------------------------------------------------------------------
    # Preparation
    # ----------------------------------------------------------------------------------

    def _prepare_macro_reviews(self) -> None:
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
        return summary.to_dict(orient="records")

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
        return summary.to_dict(orient="records")

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
            self.themes[self.themes.get("advisor_id") == advisor_id]
            if not self.themes.empty else pd.DataFrame()
        )

        return {
            "advisor_id": advisor_id,
            "firm_id": firm_id,
            "scores": df.to_dict(orient="records"),
            "themes": themes.to_dict(orient="records"),
        }

    def firm_benchmarks(self, firm_id: str) -> Optional[List[Dict]]:
        if not self.has_firms or self.benchmarks.empty:
            return None
        return self.benchmarks.to_dict(orient="records")

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
        return personas.to_dict(orient="records")

    # ----------------------------------------------------------------------------------
    # Macro insights
    # ----------------------------------------------------------------------------------

    def macro_insights_payload(self, **kwargs) -> Dict[str, Any]:
        if self.macro_reviews_clean.empty:
            return {}

        preset = kwargs.get("preset")
        if preset == "eda":
            return self._macro_payload_from_df(
                self.macro_reviews_clean.copy(),
                kwargs.get("lexical_top_n", 20),
                preset="eda",
            )

        base_df = self._apply_macro_filters(**kwargs)
        payload = self._macro_payload_from_df(
            base_df,
            kwargs.get("lexical_top_n", 20),
            lexical_n=kwargs.get("lexical_n", 1),
            exclude_stopwords=kwargs.get("exclude_stopwords", False),
        )
        payload["meta"] = self._macro_meta(base_df)
        return payload

    def _apply_macro_filters(self, **kwargs) -> pd.DataFrame:
        df = self.macro_reviews_clean.copy()

        if kwargs.get("scope") == "firm" and self.has_firms:
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

        return df

    # ----------------------------------------------------------------------------------
    # Macro helpers
    # ----------------------------------------------------------------------------------

    def _macro_payload_from_df(self, df: pd.DataFrame, lexical_top_n: int,
                               preset: Optional[str] = None,
                               lexical_n: int = 1,
                               exclude_stopwords: bool = False) -> Dict[str, Any]:

        return {
            "summary": self._macro_summary(df, preset),
            "quality": self._macro_quality(df, preset),
            "coverage": self._macro_coverage(df, preset),
            "rating_distribution": self._macro_rating_distribution(df),
            "reviews_over_time": self._macro_reviews_over_time(df),
            "reviews_per_advisor": self._macro_reviews_per_advisor(df),
            "token_counts": self._macro_token_counts(df),
            "rating_vs_token": self._macro_rating_vs_token(df),
            "lexical": self._macro_lexical(df, lexical_top_n, preset, lexical_n, exclude_stopwords),
            "meta": self._macro_meta(df),
        }

    # ---- remaining macro helpers unchanged in behavior ----
    # (kept verbatim but safe)

    def _macro_meta(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty or "review_date" not in df.columns:
            return {}
        return {
            "row_count": int(df.shape[0]),
            "date_min": df["review_date"].min().isoformat() if pd.notna(df["review_date"].min()) else None,
            "date_max": df["review_date"].max().isoformat() if pd.notna(df["review_date"].max()) else None,
        }

    def _macro_summary(self, df: pd.DataFrame, preset: Optional[str]) -> Dict[str, Any]:
        if preset == "eda" and self.macro_eda_summary:
            return self.macro_eda_summary
        if df.empty:
            return {}
        return {"reviews": int(df.shape[0])}

    def _macro_quality(self, df: pd.DataFrame, preset: Optional[str]) -> Dict[str, Any]:
        if preset == "eda" and self.macro_quality_summary:
            return self.macro_quality_summary
        if df.empty:
            return {}
        return {"n_rows": int(df.shape[0]), "n_cols": int(df.shape[1])}

    def _macro_coverage(self, df: pd.DataFrame, preset: Optional[str]) -> Dict[str, Any]:
        if preset == "eda" and self.macro_coverage:
            return self.macro_coverage
        if df.empty or "advisor_id" not in df.columns:
            return {}
        counts = df.groupby("advisor_id").size()
        return {"advisors_total": int(counts.shape[0])}

    def _macro_rating_distribution(self, df: pd.DataFrame) -> List[Dict]:
        if df.empty or "rating" not in df.columns:
            return []
        return [
            {"rating": str(k), "count": int(v)}
            for k, v in df["rating"].value_counts(dropna=False).items()
        ]

    def _macro_reviews_over_time(self, df: pd.DataFrame) -> List[Dict]:
        if df.empty or "review_date" not in df.columns:
            return []
        series = df.dropna(subset=["review_date"]).set_index("review_date").resample("M").size()
        return [{"period": idx.strftime("%Y-%m"), "count": int(val)} for idx, val in series.items()]

    def _macro_reviews_per_advisor(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty or "advisor_id" not in df.columns:
            return {"counts": []}
        return {"counts": df.groupby("advisor_id").size().tolist()}

    def _macro_token_counts(self, df: pd.DataFrame) -> List[int]:
        if df.empty or "token_count" not in df.columns:
            return []
        return df["token_count"].dropna().astype(int).tolist()

    def _macro_rating_vs_token(self, df: pd.DataFrame) -> List[Dict]:
        if df.empty or "rating" not in df.columns or "token_count" not in df.columns:
            return []
        subset = df.dropna(subset=["rating", "token_count"])
        return subset[["rating", "token_count"]].to_dict(orient="records")

    def _macro_lexical(self, df: pd.DataFrame, top_n: int,
                       preset: Optional[str], lexical_n: int,
                       exclude_stopwords: bool) -> Dict[str, Any]:

        if preset == "eda":
            return {"top_ngrams": self.macro_top_tokens.to_dict(orient="records")}

        if df.empty or "review_text_clean" not in df.columns:
            return {"top_ngrams": []}

        counter = Counter()
        for text in df["review_text_clean"].dropna().astype(str):
            parts = re.findall(r"[a-z0-9']+", text.lower())
            if exclude_stopwords:
                parts = [p for p in parts if p not in STOPWORDS]
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
    if score >= 80:
        return "Headliner"
    if score >= 65:
        return "Opener"
    return "Indie"
