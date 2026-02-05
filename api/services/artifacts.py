import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_METADATA = ROOT / "artifacts" / "sample" / "metadata.json"


class ArtifactStore:
    def __init__(self, metadata_path: Path | None = None) -> None:
        self.metadata_path = metadata_path or DEFAULT_METADATA
        self.metadata = self._load_metadata()
        self.scores = self._load_table("scores")
        self.benchmarks = self._load_table("benchmarks")
        self.themes = self._load_table("themes")

    def _load_metadata(self) -> dict:
        return json.loads(self.metadata_path.read_text())

    def _load_table(self, name: str) -> pd.DataFrame:
        manifest = {item["name"]: item for item in self.metadata["artifact_manifest"]}
        if name not in manifest:
            return pd.DataFrame()
        path = ROOT / manifest[name]["path"]
        file_type = manifest[name]["type"]

        if file_type == "json":
            return pd.DataFrame(json.loads(path.read_text()))
        if file_type == "csv":
            return pd.read_csv(path)
        if file_type == "parquet":
            return pd.read_parquet(path)

        return pd.DataFrame()

    def list_firms(self) -> list[dict]:
        firms = self.scores[["firm_id"]].drop_duplicates().sort_values("firm_id")
        return [{"firm_id": fid} for fid in firms["firm_id"].tolist()]

    def firm_summary(self, firm_id: str) -> dict | None:
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

    def firm_advisors(self, firm_id: str) -> list[dict] | None:
        df = self.scores[self.scores["firm_id"] == firm_id]
        if df.empty:
            return None
        summary = (
            df.groupby("advisor_id")[["score", "confidence", "review_count"]]
            .mean()
            .reset_index()
        )
        return summary.to_dict(orient="records")

    def advisor_detail(self, firm_id: str, advisor_id: str) -> dict | None:
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

    def firm_benchmarks(self, firm_id: str) -> list[dict] | None:
        df = self.scores[self.scores["firm_id"] == firm_id]
        if df.empty:
            return None
        return self.benchmarks.to_dict(orient="records")

    def firm_personas(self, firm_id: str) -> list[dict] | None:
        df = self.scores[self.scores["firm_id"] == firm_id]
        if df.empty:
            return None
        # Placeholder persona grouping until real clustering exists
        personas = (
            df.groupby("advisor_id")["score"].mean().reset_index()
            .assign(persona=lambda d: d["score"].apply(_score_to_persona))
        )
        return personas.to_dict(orient="records")


def _score_to_persona(score: float) -> str:
    if score >= 80:
        return "Headliner"
    if score >= 65:
        return "Opener"
    return "Indie"
