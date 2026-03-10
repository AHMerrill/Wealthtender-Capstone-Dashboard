"""Stage 3 — Dimension scoring via cosine similarity.

Code extracted from query_embeddings_vs_review_embeddings.ipynb (cells 6–52)
and executed_output.ipynb (cells 38, 40 — corrected penalized scoring).
See NOTICE for full team attribution.
"""
import os

import numpy as np
import pandas as pd

from . import config


# ──────────────────────────────────────────────────────────────────────────────
# Helpers (from query_embeddings_vs_review_embeddings.ipynb cell [6])
# ──────────────────────────────────────────────────────────────────────────────

def parse_embedding(x):
    """Cell [6]: parse embedding string from CSV back to numpy array."""
    x = x.strip().replace("\n", " ")
    return np.fromstring(x.strip("[]"), sep=" ")


# ──────────────────────────────────────────────────────────────────────────────
# Main pipeline
# ──────────────────────────────────────────────────────────────────────────────

def run(embeddings_csv=None, advisor_parquet=None, weighted_parquet=None):
    """Execute Stage 3: embeddings → dimension similarity scores.

    Parameters
    ----------
    embeddings_csv : str, optional
        Path to df_embeddings_MVP.csv. Defaults to config.EMBEDDINGS_CSV.
    advisor_parquet : str, optional
        Path to advisor_embeddings_MVP.parquet. Defaults to config.ADVISOR_EMBEDDINGS_PARQUET.
    weighted_parquet : str, optional
        Path to df_advisors_weighted_time.parquet. Defaults to config.ADVISOR_WEIGHTED_PARQUET.

    Returns
    -------
    tuple of (pd.DataFrame, pd.DataFrame)
        (review_scores_df, advisor_scores_df)
    """
    from sentence_transformers import SentenceTransformer

    if embeddings_csv is None:
        embeddings_csv = config.EMBEDDINGS_CSV
    if advisor_parquet is None:
        advisor_parquet = config.ADVISOR_EMBEDDINGS_PARQUET
    if weighted_parquet is None:
        weighted_parquet = config.ADVISOR_WEIGHTED_PARQUET

    os.makedirs(config.SCORING_DIR, exist_ok=True)

    # ── Cell [3]: Load review embeddings ───────────────────────────────────
    df = pd.read_csv(embeddings_csv, low_memory=False)
    print("Review embeddings shape:", df.shape)

    # ── Cell [6]: Parse embedding strings to numpy arrays ──────────────────
    df["review_embedding"] = df["embedding"].apply(parse_embedding)

    # ── Cell [9]: Stack into matrix E_r ────────────────────────────────────
    E_r = np.vstack(df["review_embedding"].values)
    print("E_r shape:", E_r.shape)

    # ── Cell [11]: Dimension queries and labels ────────────────────────────
    query_labels = list(config.DIMENSION_QUERIES.keys())
    query_texts = list(config.DIMENSION_QUERIES.values())

    # ── Cell [13]: Encode queries ──────────────────────────────────────────
    print("Loading model:", config.MODEL_NAME)
    model = SentenceTransformer("sentence-transformers/" + config.MODEL_NAME)

    E_q = model.encode(
        query_texts,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    print("E_q shape:", E_q.shape)

    # ── Cell [15]: Review-level cosine similarity ──────────────────────────
    S = E_r @ E_q.T
    print("S shape:", S.shape)

    # ── Cell [18]: Attach review similarities to dataframe ─────────────────
    for j, label in enumerate(query_labels):
        df[f"sim_{label}"] = S[:, j]

    # ── Cell [22/38]: Load advisor embeddings (MVP parquet) ────────────────
    df_advisors_mvp = pd.read_parquet(advisor_parquet)
    print("Advisors MVP shape:", df_advisors_mvp.shape)

    # ── Cell [25/38]: Mean advisor embeddings → similarity ─────────────────
    E_adv_mean = np.vstack(df_advisors_mvp["advisor_embedding_mean"].values)
    S_adv_mean = E_adv_mean @ E_q.T

    for j, label in enumerate(query_labels):
        df_advisors_mvp[f"sim_mean_{label}"] = S_adv_mean[:, j]

    # ── Cell [40]: Penalized advisor embeddings → similarity ───────────────
    # NOTE: Cell [27] in the original notebook has a bug where it uses
    # E_adv_mean instead of E_adv_penalized. Cell [40] in executed_output.ipynb
    # contains the corrected version. We use the corrected version here.
    E_adv_penalized = np.vstack(df_advisors_mvp["advisor_embedding_penalized"].values)
    S_adv_penalized = E_adv_penalized @ E_q.T

    for j, label in enumerate(query_labels):
        df_advisors_mvp[f"sim_penalized_{label}"] = S_adv_penalized[:, j]

    # ── Cell [30/33]: Load weighted advisor embeddings ─────────────────────
    df_advisors_weighted = pd.read_parquet(weighted_parquet)
    print("Advisors weighted shape:", df_advisors_weighted.shape)

    E_adv_weighted = np.vstack(
        df_advisors_weighted["advisor_embedding_weighted_time"].values
    )
    S_adv_weighted = E_adv_weighted @ E_q.T

    for j, label in enumerate(query_labels):
        df_advisors_weighted[f"sim_weighted_{label}"] = S_adv_weighted[:, j]

    # ── Cell [42]: Merge advisor scores ────────────────────────────────────
    mvp_sim_cols = ["advisor_id"] + [
        col for col in df_advisors_mvp.columns
        if col.startswith("sim_mean_") or col.startswith("sim_penalized_")
    ]
    df_merged = pd.merge(
        df_advisors_mvp[mvp_sim_cols],
        df_advisors_weighted,
        on="advisor_id",
        how="inner",
    )
    print("Merged advisors shape:", df_merged.shape)

    # ── Cell [51]: Export review_dimension_scores.csv ───────────────────────
    df["entity_type"] = df["advisor_id"].apply(
        lambda x: "firm" if "/advisory-firms/" in str(x) else "advisor"
    )

    review_cols = [
        "advisor_id", "advisor_name", "entity_type", "review_text_raw",
        "sim_trust_integrity", "sim_listening_personalization",
        "sim_communication_clarity", "sim_responsiveness_availability",
        "sim_life_event_support", "sim_investment_expertise",
    ]
    review_path = os.path.join(config.SCORING_DIR, "review_dimension_scores.csv")
    df[review_cols].to_csv(review_path, index_label="review_idx")
    print(f"Exported {len(df)} review scores to {review_path}")

    # ── Cell [52]: Export advisor_dimension_scores.csv ──────────────────────
    df_merged["entity_type"] = df_merged["advisor_id"].apply(
        lambda x: "firm" if "/advisory-firms/" in str(x) else "advisor"
    )

    # Add review_count per advisor (API uses this for premier pool filtering)
    review_counts = df.groupby("advisor_id").size().rename("review_count")
    df_merged = df_merged.merge(review_counts, on="advisor_id", how="left")
    df_merged["review_count"] = df_merged["review_count"].fillna(0).astype(int)

    advisor_cols = (
        ["advisor_id", "advisor_name", "entity_type", "review_count"]
        + [f"sim_mean_{l}" for l in query_labels]
        + [f"sim_penalized_{l}" for l in query_labels]
        + [f"sim_weighted_{l}" for l in query_labels]
    )
    advisor_path = os.path.join(config.SCORING_DIR, "advisor_dimension_scores.csv")
    df_merged[advisor_cols].to_csv(advisor_path, index=False)
    print(f"Exported {len(df_merged)} advisor/firm scores to {advisor_path}")

    return df[review_cols + ["review_embedding"]], df_merged
