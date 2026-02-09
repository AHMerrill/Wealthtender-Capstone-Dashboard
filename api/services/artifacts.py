import json
from collections import Counter
from pathlib import Path
from typing import Optional, List, Dict, Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_METADATA = ROOT / "artifacts" / "metadata.json"


class ArtifactStore:
    def __init__(self, metadata_path: Optional[Path] = None) -> None:
        self.metadata_path = metadata_path or DEFAULT_METADATA
        self.metadata = self._load_metadata()
        self.scores = self._load_table("scores")
        self.benchmarks = self._load_table("benchmarks")
        self.themes = self._load_table("themes")
        self.macro_reviews_clean = self._load_table("macro_reviews_clean")
        self.macro_eda_summary = self._load_json("macro_eda_summary")
        self.macro_coverage = self._load_json("macro_coverage")
        self.macro_quality_summary = self._load_json("macro_quality_summary")
        self.macro_raw_file_meta = self._load_json("macro_raw_file_meta")
        self.macro_missing_report = self._load_table("macro_missing_report")
        self.macro_top_tokens = self._load_table("macro_top_tokens")
        self.macro_top_bigrams = self._load_table("macro_top_bigrams")
        self._prepare_macro_reviews()

    def _load_metadata(self) -> dict:
        return json.loads(self.metadata_path.read_text())

    def _get_manifest_item(self, name: str) -> Optional[dict]:
        manifest = {item["name"]: item for item in self.metadata["artifact_manifest"]}
        return manifest.get(name)

    def _load_table(self, name: str) -> pd.DataFrame:
        item = self._get_manifest_item(name)
        if not item:
            return pd.DataFrame()
        path = ROOT / item["path"]
        file_type = item["type"]

        if file_type == "json":
            return pd.DataFrame(json.loads(path.read_text()))
        if file_type == "csv":
            return pd.read_csv(path)
        if file_type == "parquet":
            return pd.read_parquet(path)

        return pd.DataFrame()

    def _load_json(self, name: str) -> dict:
        item = self._get_manifest_item(name)
        if not item:
            return {}
        path = ROOT / item["path"]
        if path.exists():
            return json.loads(path.read_text())
        return {}

    def _prepare_macro_reviews(self) -> None:
        if self.macro_reviews_clean.empty:
            return
        df = self.macro_reviews_clean
        if "review_date" in df.columns:
            df["review_date"] = pd.to_datetime(df["review_date"], errors="coerce")
        if "clean_token_count" in df.columns and "token_count" not in df.columns:
            df["token_count"] = df["clean_token_count"]
        if not self.scores.empty and "advisor_id" in df.columns:
            advisor_firm = self.scores[["advisor_id", "firm_id"]].drop_duplicates()
            df = df.merge(advisor_firm, on="advisor_id", how="left")
        self.macro_reviews_clean = df

    def list_firms(self) -> list[dict]:
        firms = self.scores[["firm_id"]].drop_duplicates().sort_values("firm_id")
        return [{"firm_id": fid} for fid in firms["firm_id"].tolist()]

    def firm_summary(self, firm_id: str) -> Optional[Dict]:
        df = self.scores[self.scores["firm_id"] == firm_id]
        if df.empty:
            return None
        summary = {
            "firm_id": firm_id,
            "advisor_count": df["advisor_id"].nunique(),
            "dimension_count": df["dimension"].nunique(),
            "avg_score": round(df["score"].mean(), 2),
            "avg_confidence": round(df["confidence"].mean(), 2),
        }
        return summary

    def firm_dimensions(self, firm_id: str) -> Optional[List[Dict]]:
        df = self.scores[self.scores["firm_id"] == firm_id]
        if df.empty:
            return None
        summary = (
            df.groupby("dimension")[["score", "confidence", "review_count"]]
            .mean()
            .reset_index()
            .sort_values("score", ascending=False)
        )
        return summary.to_dict(orient="records")

    def firm_advisors(self, firm_id: str) -> Optional[List[Dict]]:
        df = self.scores[self.scores["firm_id"] == firm_id]
        if df.empty:
            return None
        summary = (
            df.groupby("advisor_id")[["score", "confidence", "review_count"]]
            .mean()
            .reset_index()
        )
        return summary.to_dict(orient="records")

    def advisor_detail(self, firm_id: str, advisor_id: str) -> Optional[Dict]:
        df = self.scores[(self.scores["firm_id"] == firm_id) & (self.scores["advisor_id"] == advisor_id)]
        if df.empty:
            return None
        themes = self.themes[self.themes["advisor_id"] == advisor_id].to_dict(orient="records")
        return {
            "advisor_id": advisor_id,
            "firm_id": firm_id,
            "scores": df.to_dict(orient="records"),
            "themes": themes,
        }

    def firm_benchmarks(self, firm_id: str) -> Optional[List[Dict]]:
        df = self.scores[self.scores["firm_id"] == firm_id]
        if df.empty:
            return None
        return self.benchmarks.to_dict(orient="records")

    def firm_personas(self, firm_id: str) -> Optional[List[Dict]]:
        df = self.scores[self.scores["firm_id"] == firm_id]
        if df.empty:
            return None
        # Placeholder persona grouping until real clustering exists
        personas = (
            df.groupby("advisor_id")["score"].mean().reset_index()
            .assign(persona=lambda d: d["score"].apply(_score_to_persona))
        )
        return personas.to_dict(orient="records")

    def macro_insights_payload(
        self,
        scope: str = "global",
        firm_id: Optional[str] = None,
        date_start: Optional[str] = None,
        date_end: Optional[str] = None,
        rating: Optional[float] = None,
        min_tokens: Optional[int] = None,
        max_tokens: Optional[int] = None,
        preset: Optional[str] = None,
        lexical_top_n: int = 20,
    ) -> Dict[str, Any]:
        if self.macro_reviews_clean.empty:
            return {}
        if preset == "eda":
            df = self.macro_reviews_clean.copy()
            return self._macro_payload_from_df(df, lexical_top_n, preset="eda")
        df = self._apply_macro_filters(
            scope=scope,
            firm_id=firm_id,
            date_start=date_start,
            date_end=date_end,
            rating=rating,
            min_tokens=min_tokens,
            max_tokens=max_tokens,
        )
        return self._macro_payload_from_df(df, lexical_top_n)

    def _apply_macro_filters(
        self,
        scope: str,
        firm_id: Optional[str],
        date_start: Optional[str],
        date_end: Optional[str],
        rating: Optional[float],
        min_tokens: Optional[int],
        max_tokens: Optional[int],
    ) -> pd.DataFrame:
        df = self.macro_reviews_clean.copy()
        if scope == "firm" and firm_id and "firm_id" in df.columns:
            df = df[df["firm_id"] == firm_id]
        if date_start and "review_date" in df.columns:
            df = df[df["review_date"] >= pd.to_datetime(date_start, errors="coerce")]
        if date_end and "review_date" in df.columns:
            df = df[df["review_date"] <= pd.to_datetime(date_end, errors="coerce")]
        if rating is not None and "rating" in df.columns:
            df = df[df["rating"] == rating]
        if min_tokens is not None and "token_count" in df.columns:
            df = df[df["token_count"] >= min_tokens]
        if max_tokens is not None and "token_count" in df.columns:
            df = df[df["token_count"] <= max_tokens]
        return df

    def _macro_payload_from_df(self, df: pd.DataFrame, lexical_top_n: int, preset: Optional[str] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        payload["summary"] = self._macro_summary(df, preset=preset)
        payload["quality"] = self._macro_quality(df, preset=preset)
        payload["coverage"] = self._macro_coverage(df, preset=preset)
        payload["rating_distribution"] = self._macro_rating_distribution(df)
        payload["reviews_over_time"] = self._macro_reviews_over_time(df)
        payload["reviews_per_advisor"] = self._macro_reviews_per_advisor(df)
        payload["token_counts"] = self._macro_token_counts(df)
        payload["rating_vs_token"] = self._macro_rating_vs_token(df)
        payload["lexical"] = self._macro_lexical(df, top_n=lexical_top_n, preset=preset)
        payload["meta"] = self._macro_meta(df)
        return payload

    def _macro_meta(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty or "review_date" not in df.columns:
            return {}
        date_min = df["review_date"].min()
        date_max = df["review_date"].max()
        token_min = df["token_count"].min() if "token_count" in df.columns else None
        token_max = df["token_count"].max() if "token_count" in df.columns else None
        rating_min = df["rating"].min() if "rating" in df.columns else None
        rating_max = df["rating"].max() if "rating" in df.columns else None
        return {
            "date_min": date_min.isoformat() if pd.notna(date_min) else None,
            "date_max": date_max.isoformat() if pd.notna(date_max) else None,
            "row_count": int(df.shape[0]),
            "token_min": int(token_min) if pd.notna(token_min) else None,
            "token_max": int(token_max) if pd.notna(token_max) else None,
            "rating_min": float(rating_min) if pd.notna(rating_min) else None,
            "rating_max": float(rating_max) if pd.notna(rating_max) else None,
        }

    def _macro_summary(self, df: pd.DataFrame, preset: Optional[str] = None) -> Dict[str, Any]:
        if preset == "eda" and self.macro_eda_summary:
            return self.macro_eda_summary
        if df.empty:
            return {}
        rating_counts = df["rating"].value_counts(dropna=False).sort_index()
        return {
            "reviews": str(df.shape[0]),
            "advisors": int(df["advisor_id"].nunique()) if "advisor_id" in df.columns else 0,
            "rating_counts": {str(k): int(v) for k, v in rating_counts.items()},
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

    def _macro_quality(self, df: pd.DataFrame, preset: Optional[str] = None) -> Dict[str, Any]:
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

    def _macro_coverage(self, df: pd.DataFrame, preset: Optional[str] = None) -> Dict[str, Any]:
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

    def _macro_rating_distribution(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        if df.empty or "rating" not in df.columns:
            return []
        counts = df["rating"].value_counts(dropna=False).sort_index()
        data = []
        for rating, count in counts.items():
            label = "NaN" if pd.isna(rating) else str(rating)
            data.append({"rating": label, "count": int(count)})
        return data

    def _macro_reviews_over_time(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        if df.empty or "review_date" not in df.columns:
            return []
        series = df.dropna(subset=["review_date"]).set_index("review_date").resample("M").size()
        return [{"period": idx.strftime("%Y-%m"), "count": int(val)} for idx, val in series.items()]

    def _macro_reviews_per_advisor(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty or "advisor_id" not in df.columns:
            return {"counts": [], "median": None, "p90": None}
        counts = df.groupby("advisor_id").size()
        return {
            "counts": counts.tolist(),
            "median": float(counts.median()),
            "p90": float(counts.quantile(0.9)),
        }

    def _macro_token_counts(self, df: pd.DataFrame) -> List[int]:
        if df.empty or "token_count" not in df.columns:
            return []
        return df["token_count"].dropna().astype(int).tolist()

    def _macro_rating_vs_token(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        if df.empty or "token_count" not in df.columns or "rating" not in df.columns:
            return []
        subset = df.dropna(subset=["token_count", "rating"])
        return [
            {"rating": float(row["rating"]), "token_count": int(row["token_count"])}
            for _, row in subset.iterrows()
        ]

    def _macro_lexical(self, df: pd.DataFrame, top_n: int, preset: Optional[str] = None) -> Dict[str, Any]:
        if preset == "eda":
            return {
                "top_tokens": self._table_to_records(self.macro_top_tokens),
                "top_bigrams": self._table_to_records(self.macro_top_bigrams),
            }
        if df.empty or "review_text_clean" not in df.columns:
            return {"top_tokens": [], "top_bigrams": []}
        tokens = Counter()
        bigrams = Counter()
        for text in df["review_text_clean"].dropna().astype(str):
            parts = [p for p in text.split() if p]
            tokens.update(parts)
            bigrams.update([" ".join(pair) for pair in zip(parts, parts[1:])])
        top_tokens = [{"token": k, "count": int(v)} for k, v in tokens.most_common(top_n)]
        top_bigrams = [{"bigram": k, "count": int(v)} for k, v in bigrams.most_common(top_n)]
        return {"top_tokens": top_tokens, "top_bigrams": top_bigrams}

    def _table_to_records(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        if df.empty:
            return []
        return df.to_dict(orient="records")


def _score_to_persona(score: float) -> str:
    if score >= 80:
        return "Headliner"
    if score >= 65:
        return "Opener"
    return "Indie"
