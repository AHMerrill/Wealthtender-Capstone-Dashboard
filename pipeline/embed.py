"""Stage 2 — Text processing, embedding generation, and advisor aggregation.

Code extracted from NLP_I.ipynb (cells 9-114).
See NOTICE for full team attribution.
"""
import os
import re
import html
import hashlib
from collections import Counter

import pandas as pd
import numpy as np

from . import config


# ------------------------------------------------------------------------------
# Review identity hash (for incremental embedding)
# ------------------------------------------------------------------------------

def _review_hash(advisor_id, review_text_raw, review_date, reviewer):
    """Stable identity for a review: same advisor + text + date + reviewer = same review.

    Two different clients reviewing the same advisor -> different hashes (both count).
    Same client writing identical text on different dates -> different hashes (both count).
    Same review exported twice in overlapping data pulls -> same hash (deduped).
    """
    date_str = str(review_date).split(" ")[0].split("T")[0] if pd.notna(review_date) else "no_date"
    reviewer_str = str(reviewer).strip() if pd.notna(reviewer) else "anonymous"
    key = f"{advisor_id}||{review_text_raw}||{date_str}||{reviewer_str}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


# ------------------------------------------------------------------------------
# Text processing helpers (from NLP_I.ipynb cells 20, 23, 24, 28, 29)
# ------------------------------------------------------------------------------

def tokenize(text):
    """Cell [20]: simple whitespace tokenizer."""
    return text.split()


def remove_stopwords(tokens, stopwords=None):
    """Cell [24]: remove stopwords and short tokens."""
    if stopwords is None:
        import nltk
        nltk.download("stopwords", quiet=True)
        from nltk.corpus import stopwords as nltk_sw
        EN_STOPWORDS = set(nltk_sw.words("english"))
        stopwords = EN_STOPWORDS.union(config.DOMAIN_STOPWORDS)
    return [t for t in tokens if t not in stopwords and len(t) > 2]


# Cell [28]: compile prompt regex
_prompt_regex = re.compile(
    "|".join(config.PROMPT_PATTERNS), flags=re.IGNORECASE
)


def strip_prompts(text):
    """Cell [28]: remove prompt fragments from review text."""
    if not isinstance(text, str):
        return text
    cleaned = _prompt_regex.sub(" ", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def decode_html_entities(text):
    """Cell [29]: clean HTML entities like '&amp'."""
    if not isinstance(text, str):
        return text
    return html.unescape(text)


def normalize_whitespace(text):
    """Cell [29]: clean non-breaking spaces with regular spaces."""
    if not isinstance(text, str):
        return text
    text = text.replace("\xa0", " ")
    text = " ".join(text.split())
    return text


# ------------------------------------------------------------------------------
# Advisor name removal (from NLP_I.ipynb cells 89)
# ------------------------------------------------------------------------------

def normalize_name(name):
    """Cell [89]: normalize advisor name for matching."""
    name = str(name).lower()
    name = re.sub(r"cfa|cfp|chfc|aif|cpa|mba|phd|ms|jd|esq", " ", name)
    name = re.sub(r"[^a-z\s]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def remove_advisor_identity(row):
    """Cell [89]: remove advisor name from review text."""
    text = str(row["review_text_clean2"]).lower()
    adv = normalize_name(row["advisor_name"])

    parts = adv.split()
    first = parts[0] if len(parts) else ""
    last = parts[-1] if len(parts) else ""

    # remove full normalized name phrase if it appears
    if adv:
        text = re.sub(rf"\b{re.escape(adv)}\b", " ", text)

    # remove first and last name tokens
    for token in {first, last}:
        if token and len(token) >= 3:
            text = re.sub(rf"\b{re.escape(token)}\b", " ", text)

    text = re.sub(r"\s+", " ", text).strip()
    return text


# ------------------------------------------------------------------------------
# N-gram helpers (from NLP_I.ipynb cells 41, 45)
# ------------------------------------------------------------------------------

def make_bigrams(tokens):
    """Cell [41]: create bigrams from token list."""
    from nltk.util import bigrams
    return list(bigrams(tokens))


def make_trigrams(tokens):
    """Cell [45]: create trigrams from token list."""
    from nltk.util import trigrams
    return list(trigrams(tokens))


# ------------------------------------------------------------------------------
# Helper: parse embedding string from CSV back to numpy array
# ------------------------------------------------------------------------------

def _parse_embedding(x):
    """Parse embedding stored as string in CSV back to numpy array."""
    if isinstance(x, np.ndarray):
        return x
    x = str(x).strip().replace("\n", " ")
    return np.fromstring(x.strip("[]"), sep=" ")


# ------------------------------------------------------------------------------
# Main pipeline
# ------------------------------------------------------------------------------

def run(reviews_clean_csv=None, full_reprocess=False):
    """Execute Stage 2: cleaned reviews -> embeddings + advisor aggregation.

    Supports incremental embedding: on repeat runs, only new reviews (not seen
    in the existing embeddings file) are encoded. Existing embeddings are kept
    and new ones are appended. Advisor-level aggregation always runs on the
    full accumulated set.

    Parameters
    ----------
    reviews_clean_csv : str, optional
        Path to cleaned reviews CSV. Defaults to artifacts/macro_insights/reviews_clean.csv.
    full_reprocess : bool
        If True, re-embed all reviews from scratch (ignore existing embeddings).
        If False (default), only embed new reviews not already in the embeddings file.

    Returns
    -------
    tuple of (pd.DataFrame, pd.DataFrame)
        (df_embed, advisors_df) -- review-level embeddings and advisor-level aggregation.
    """
    from sentence_transformers import SentenceTransformer

    if reviews_clean_csv is None:
        reviews_clean_csv = os.path.join(config.MACRO_DIR, "reviews_clean.csv")

    os.makedirs(config.INTERMEDIATE_DIR, exist_ok=True)

    # -- Cell [2/8]: Load cleaned reviews --
    df = pd.read_csv(reviews_clean_csv, encoding="utf-8", low_memory=False)
    print("Shape:", df.shape)

    # -- Cell [9]: Parse dates --
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["review_year"] = df["Date"].dt.year

    # -- Cell [12]: Filter dates (keep only > 2014) --
    df = df[df["review_year"] > 2014]

    # -- Cell [16]: Drop duplicates --
    df = df.drop_duplicates()

    # -- Cell [19]: Length validation --
    TEXT_COL = "review_text_clean"
    df["char_len"] = df[TEXT_COL].str.len()
    df["word_len"] = df[TEXT_COL].str.split().str.len()

    # -- Cell [20]: Tokenize --
    df["tokens"] = df[TEXT_COL].apply(tokenize)
    df["n_tokens"] = df["tokens"].apply(len)

    # -- Cell [23/24]: Stopwords --
    import nltk
    nltk.download("stopwords", quiet=True)
    from nltk.corpus import stopwords as nltk_sw
    EN_STOPWORDS = set(nltk_sw.words("english"))
    STOPWORDS = EN_STOPWORDS.union(config.DOMAIN_STOPWORDS)

    df["tokens_nostop"] = df["tokens"].apply(lambda t: remove_stopwords(t, STOPWORDS))
    df["n_tokens_nostop"] = df["tokens_nostop"].apply(len)

    # -- Cell [29]: HTML entity decode + whitespace normalize --
    df["review_text_clean2"] = df["review_text_clean"].apply(decode_html_entities)
    df["review_text_clean2"] = df["review_text_clean2"].apply(normalize_whitespace)

    # -- Cell [30]: Strip prompts --
    df["review_text_clean2"] = df["review_text_clean2"].apply(strip_prompts)

    # -- Cell [31]: Remove empty rows --
    df = df[
        df["review_text_clean2"].notna()
        & df["review_text_clean2"].str.strip().ne("")
    ].copy()

    # -- Cell [33/34]: Re-tokenize on clean2 --
    df["tokens"] = df["review_text_clean2"].apply(tokenize)
    df["n_tokens"] = df["tokens"].apply(len)
    df["tokens_nostop"] = df["tokens"].apply(lambda t: remove_stopwords(t, STOPWORDS))
    df["n_tokens_nostop"] = df["tokens_nostop"].apply(len)

    # -- Cell [41]: Bigrams --
    df["bigrams"] = df["tokens_nostop"].apply(make_bigrams)

    # -- Cell [45]: Trigrams --
    df["trigrams"] = df["tokens_nostop"].apply(make_trigrams)

    # -- Cell [73]: Filter for embedding --
    df_embed = df[
        df["review_text_clean2"].notna()
        & df["review_text_clean2"].str.strip().ne("")
        & (df["n_tokens"] >= 5)
    ].copy()

    print("Original rows:", len(df))
    print("Embedding rows:", len(df_embed))

    # -- Incremental dedup: compute review_hash for this batch --
    df_embed["review_hash"] = df_embed.apply(
        lambda r: _review_hash(
            r["advisor_id"], r["review_text_raw"],
            r.get("review_date", r.get("Date")), r.get("reviewer_name")
        ),
        axis=1,
    )

    # Dedup the input batch itself (Layer 1: true duplicates in the export)
    n_before_dedup = len(df_embed)
    df_embed = df_embed.drop_duplicates(subset="review_hash", keep="first")
    n_input_dupes = n_before_dedup - len(df_embed)
    if n_input_dupes:
        print(f"Dedup: dropped {n_input_dupes} duplicate(s) within input batch")

    # -- Incremental: load existing embeddings and find delta --
    existing_df = None
    if not full_reprocess and os.path.exists(config.EMBEDDINGS_CSV):
        try:
            existing_df = pd.read_csv(config.EMBEDDINGS_CSV, low_memory=False)
            if "review_hash" in existing_df.columns:
                existing_hashes = set(existing_df["review_hash"].values)
                new_mask = ~df_embed["review_hash"].isin(existing_hashes)
                n_already = int((~new_mask).sum())
                n_new = int(new_mask.sum())
                print(f"Incremental: {n_already} already embedded, {n_new} new to embed")
                if n_new == 0:
                    print("No new reviews to embed -- reusing existing embeddings")
                    # Parse embeddings back to numpy for advisor aggregation
                    existing_df["embedding"] = existing_df["embedding"].apply(_parse_embedding)
                    # Reconstruct df_embed from accumulated data for aggregation
                    df_embed_all = existing_df.rename(columns={
                        "review_text_processed": "review_text_clean2",
                        "total_tokens_raw": "n_tokens",
                    })
                    return _aggregate_advisors(df_embed_all, config)
                # Keep only the rows that need encoding
                df_embed_new = df_embed[new_mask].copy()
            else:
                print("Incremental: existing embeddings lack review_hash column -- full reprocess")
                existing_df = None
                df_embed_new = df_embed
        except Exception as e:
            print(f"Incremental: could not load existing embeddings ({e}) -- full reprocess")
            existing_df = None
            df_embed_new = df_embed
    else:
        if full_reprocess:
            print("Full reprocess requested -- embedding all reviews")
        df_embed_new = df_embed

    # -- Cell [87]: Compute age in years --
    today = pd.Timestamp.today()

    df_embed_new["review_date"] = pd.to_datetime(
        df_embed_new["review_date"], errors="coerce"
    )
    df_embed_new["age_years"] = (today - df_embed_new["review_date"]).dt.days / 365.25

    # -- Cell [89]: Remove advisor names from text --
    df_embed_new["review_text_clean2"] = df_embed_new.apply(remove_advisor_identity, axis=1)

    # -- Cell [90]: Encode with SentenceTransformer --
    print(f"Loading model: {config.MODEL_NAME} ({len(df_embed_new)} reviews to encode)")
    model = SentenceTransformer(config.MODEL_NAME)

    texts = df_embed_new["review_text_clean2"].tolist()

    embeddings = model.encode(
        texts,
        batch_size=config.BATCH_SIZE,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    # -- Cell [91]: Attach embeddings --
    df_embed_new = df_embed_new.reset_index(drop=True)
    df_embed_new["embedding"] = list(embeddings)

    # -- Cell [95]: Save df_embeddings_MVP.csv (append to existing) --
    df_save_new = df_embed_new.copy()
    df_save_new = df_save_new.rename(columns={
        "_custom_relationship": "custom_relationship",
        "_custom_compensation": "custom_compensation",
        "_custom_conflicts": "custom_conflicts",
        "n_tokens": "total_tokens_raw",
        "review_text_clean2": "review_text_processed",
        "tokens_nostop": "tokens_processed",
        "n_tokens_nostop": "n_tokens_processed",
    })
    save_cols = [
        "review_hash",
        "ID", "Title", "Date", "age_years",
        "custom_relationship", "custom_compensation",
        "reviewer_name", "advisor_id", "advisor_name",
        "acf_rating", "rating", "review_text_raw",
        "total_tokens_raw", "review_text_processed",
        "tokens_processed", "n_tokens_processed",
        "embedding", "bigrams", "trigrams",
    ]
    df_save_new = df_save_new[[c for c in save_cols if c in df_save_new.columns]]

    # Merge with existing: append new rows to accumulated embeddings
    if existing_df is not None:
        df_save_all = pd.concat([existing_df, df_save_new], ignore_index=True)
        # Safety net dedup (Layer 3)
        n_before = len(df_save_all)
        df_save_all = df_save_all.drop_duplicates(subset="review_hash", keep="first")
        n_after = len(df_save_all)
        if n_before != n_after:
            print(f"Safety dedup: removed {n_before - n_after} unexpected duplicate(s)")
    else:
        df_save_all = df_save_new

    df_save_all.to_csv(config.EMBEDDINGS_CSV, index=False)
    print(f"Saved: {config.EMBEDDINGS_CSV}  ({len(df_save_all)} total reviews)")

    # -- Advisor aggregation uses the FULL accumulated set --
    # Parse embeddings back to numpy for all rows (existing were strings, new are arrays)
    df_save_all["embedding"] = df_save_all["embedding"].apply(_parse_embedding)
    df_embed_all = df_save_all.rename(columns={
        "review_text_processed": "review_text_clean2",
        "total_tokens_raw": "n_tokens",
    })

    return _aggregate_advisors(df_embed_all, config)


def _aggregate_advisors(df_embed, cfg):
    """Advisor-level aggregation from full accumulated review embeddings.

    Extracted from the original run() to be shared between full-run and
    incremental-no-new-reviews paths.
    """
    today = pd.Timestamp.today()

    # Ensure review_date is parsed
    df_embed["review_date"] = pd.to_datetime(
        df_embed.get("review_date", df_embed.get("Date")), errors="coerce"
    )
    df_embed["age_years"] = (today - df_embed["review_date"]).dt.days / 365.25

    # -- Cell [97]: Build review_emb working table --
    # Ensure n_tokens exists (might be named differently from CSV reload)
    if "n_tokens" not in df_embed.columns and "total_tokens_raw" in df_embed.columns:
        df_embed["n_tokens"] = df_embed["total_tokens_raw"]

    review_emb = df_embed[[
        "advisor_id", "advisor_name", "review_date", "age_years",
        "n_tokens", "review_text_clean2", "embedding",
    ]].copy()
    review_emb = review_emb.reset_index(drop=True)

    # -- Cell [99]: Advisor-level aggregation (mean) --
    reviews = review_emb.copy()
    reviews = reviews.rename(columns={
        "n_tokens": "n_tokens_raw",
        "review_text_clean2": "review_text_processed",
    })

    reviews = reviews[[
        "advisor_id", "advisor_name", "n_tokens_raw",
        "age_years", "embedding",
    ]]

    emb_matrix = np.vstack(reviews["embedding"].to_numpy())
    advisor_to_rows = reviews.groupby(["advisor_id"]).indices

    advisor_records = []
    advisor_vectors = []

    for advisor_id, rows in advisor_to_rows.items():
        rows = np.array(list(rows))

        v = emb_matrix[rows].mean(axis=0)
        v = v / np.linalg.norm(v)

        advisor_vectors.append(v)

        advisor_records.append({
            "advisor_id": advisor_id,
            "advisor_name": reviews.loc[rows[0], "advisor_name"],
            "n_reviews": len(rows),
            "n_tokens_raw": int(reviews.loc[rows, "n_tokens_raw"].sum()),
            "median_age_years": float(np.median(reviews.loc[rows, "age_years"])),
        })

    advisor_vecs = np.vstack(advisor_vectors)
    advisors_df = pd.DataFrame(advisor_records)

    # -- Cell [102]: Recency / staleness --
    advisor_recency = (
        review_emb.groupby("advisor_id")["review_date"]
        .max()
        .reset_index()
        .rename(columns={"review_date": "most_recent_review_date"})
    )

    advisor_recency["staleness_years"] = (
        (today - advisor_recency["most_recent_review_date"]).dt.days / 365.25
    )

    # -- Cell [104]: Lambda calibration --
    s75 = advisor_recency["staleness_years"].quantile(0.75)
    target_penalty_at_s75 = 0.7
    lam = -np.log(target_penalty_at_s75) / s75

    # -- Cell [105]: Penalty factor --
    advisor_recency["penalty_factor"] = np.exp(
        -lam * advisor_recency["staleness_years"]
    )

    # -- Cell [106]: Merge recency into advisors_df --
    advisors_df = advisors_df.merge(
        advisor_recency[[
            "advisor_id", "most_recent_review_date",
            "staleness_years", "penalty_factor",
        ]],
        on="advisor_id",
        how="left",
    )

    # -- Cell [108/109]: Store embeddings --
    advisors_df["advisor_embedding_mean"] = list(advisor_vecs)

    advisor_vecs_penalized = advisor_vecs * advisors_df["penalty_factor"].values[:, None]
    advisors_df["advisor_embedding_penalized"] = list(advisor_vecs_penalized)

    # -- Cell [111]: Save advisor parquet --
    advisors_df.to_parquet(cfg.ADVISOR_EMBEDDINGS_PARQUET, index=False)
    print("Saved:", cfg.ADVISOR_EMBEDDINGS_PARQUET)

    return review_emb, advisors_df


# ------------------------------------------------------------------------------
# Weighted-by-time embeddings
# Code extracted from Wealthtender_Embeddings_WT.ipynb (cells 3-15).
# This is a SEPARATE embedding pass with different settings:
#   - normalize_embeddings=False (vs True in the main run())
#   - simpler advisor-name stripping (full name only, not per-token)
#   - time-weighted advisor aggregation using half-life decay
# ------------------------------------------------------------------------------

# -- Weighting constants (from Wealthtender_Embeddings_WT.ipynb cell [7]) --
HALF_LIFE_YEARS = 2.0
TOKEN_REF = 80
INFO_CAP = 2.0
INFO_FLOOR = 0.2


def _strip_advisor_name_for_embedding(text, name):
    """Cell [5]: Remove advisor name at embedding-time (simple replacement)."""
    if not isinstance(text, str) or not isinstance(name, str) or not name.strip():
        return text
    pattern = re.compile(re.escape(name.strip()), re.IGNORECASE)
    cleaned = pattern.sub(" ", text)
    return re.sub(r"\s+", " ", cleaned).strip()


def _weighted_mean(E, w):
    """Cell [9]: Weighted mean of embedding matrix E with weights w."""
    w = np.asarray(w, dtype=float)
    denom = w.sum()
    if denom <= 0:
        return E.mean(axis=0)
    return (E * w[:, None]).sum(axis=0) / denom


def _effective_n(w):
    """Cell [9]: Effective sample size given weights w."""
    w = np.asarray(w, dtype=float)
    s2 = (w ** 2).sum()
    if s2 == 0:
        return 0.0
    return float((w.sum() ** 2) / s2)


def run_weighted(reviews_clean_csv=None):
    """Execute weighted-by-time embedding pass.

    This is a separate embedding pass from the main run() function because
    it uses different normalization settings and text processing.

    Code extracted from Wealthtender_Embeddings_WT.ipynb.

    Parameters
    ----------
    reviews_clean_csv : str, optional
        Path to cleaned reviews CSV. Defaults to artifacts/macro_insights/reviews_clean.csv.

    Returns
    -------
    pd.DataFrame
        Advisor-level weighted-time embeddings (df_advisors_weighted_time).
    """
    from sentence_transformers import SentenceTransformer

    if reviews_clean_csv is None:
        reviews_clean_csv = os.path.join(config.MACRO_DIR, "reviews_clean.csv")

    os.makedirs(config.INTERMEDIATE_DIR, exist_ok=True)

    # -- Cell [3]: Load cleaned reviews --
    df_raw = pd.read_csv(reviews_clean_csv, encoding="utf-8", low_memory=False)

    df_raw["review_date"] = pd.to_datetime(df_raw["review_date"], errors="coerce")

    # Rename columns to match collaborator's schema
    df = df_raw.rename(columns={
        "ID": "review_id",
        "review_text_clean": "review_text_clean2",
        "token_count": "n_tokens",
        "clean_token_count": "n_tokens_nostop",
    }).copy()

    df["review_text_clean2"] = df["review_text_clean2"].astype(str)
    df = df[df["review_text_clean2"].str.strip().ne("")].reset_index(drop=True)

    # Compute age_years relative to newest review (reproducible)
    ref_date = df["review_date"].max()
    df["age_years"] = (
        (ref_date - df["review_date"]).dt.total_seconds() / (365.25 * 24 * 3600)
    ).clip(lower=0)

    print(f"Weighted embedding pass: {len(df)} reviews, ref_date={ref_date.date()}")

    # -- Cell [5]: Strip advisor name and encode --
    df["text_for_embedding"] = df.apply(
        lambda r: _strip_advisor_name_for_embedding(
            r["review_text_clean2"], r["advisor_name"]
        ),
        axis=1,
    )

    print("Loading model:", config.MODEL_NAME)
    model = SentenceTransformer("sentence-transformers/" + config.MODEL_NAME)

    embeddings = model.encode(
        df["text_for_embedding"].tolist(),
        batch_size=config.BATCH_SIZE,
        show_progress_bar=True,
        normalize_embeddings=False,  # NOTE: False -- differs from main run()
    )
    df["embedding"] = list(embeddings)

    # -- Cell [7]: Compute time weights --
    df["w_time"] = 0.5 ** (df["age_years"] / HALF_LIFE_YEARS)
    df["review_weight_time"] = df["w_time"]

    # -- Cell [9]: Advisor-level aggregation (time-weighted) --
    advisor_rows = []
    for advisor_id, g in df.groupby("advisor_id"):
        E = np.vstack(g["embedding"].values)
        emb_w_time = _weighted_mean(E, g["review_weight_time"].values)

        advisor_rows.append({
            "advisor_id": advisor_id,
            "advisor_name": g["advisor_name"].iloc[0],
            "advisor_embedding_weighted_time": emb_w_time,
            "n_reviews_used": int(len(g)),
            "total_tokens": int(g["n_tokens"].sum()),
            "total_tokens_nostop": int(g["n_tokens_nostop"].sum()),
            "median_age_years": float(g["age_years"].median()),
            "min_review_date": g["review_date"].min(),
            "max_review_date": g["review_date"].max(),
            "effective_n_time": _effective_n(g["review_weight_time"].values),
        })

    df_advisors = pd.DataFrame(advisor_rows)

    # -- Cell [15]: Save deliverable --
    df_advisors.to_parquet(config.ADVISOR_WEIGHTED_PARQUET, index=False)
    print(f"Saved: {config.ADVISOR_WEIGHTED_PARQUET}  ({len(df_advisors)} advisors)")

    return df_advisors
