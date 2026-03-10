"""Stage 1 — Raw data ingestion, cleaning, and artifact generation.

Code extracted from WT_Capstone_ReviewPipeline.ipynb (cells 1–24).
See NOTICE for full team attribution.
"""
import os
import hashlib
import json
import re
import unicodedata
from collections import Counter

import pandas as pd
import numpy as np

from . import config


# ──────────────────────────────────────────────────────────────────────────────
# Helpers (from WT_Capstone_ReviewPipeline.ipynb cell [5])
# ──────────────────────────────────────────────────────────────────────────────

def sha256_file(path, chunk_size=1024 * 1024):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


# ──────────────────────────────────────────────────────────────────────────────
# Helpers (from WT_Capstone_ReviewPipeline.ipynb cell [11])
# ──────────────────────────────────────────────────────────────────────────────

def missing_report(d):
    return (
        d.isna().mean().sort_values(ascending=False)
        .rename("missing_frac").to_frame()
        .assign(missing_count=d.isna().sum())
    )


# ──────────────────────────────────────────────────────────────────────────────
# Helpers (from WT_Capstone_ReviewPipeline.ipynb cell [24])
# ──────────────────────────────────────────────────────────────────────────────

def tokenize_simple(s):
    """Simple tokenization (no heavy deps)."""
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s']", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return [w for w in s.split() if len(w) > 1]


# ──────────────────────────────────────────────────────────────────────────────
# Main pipeline
# ──────────────────────────────────────────────────────────────────────────────

def run(raw_csv=None):
    """Execute Stage 1: raw CSV → cleaned artifacts.

    Parameters
    ----------
    raw_csv : str, optional
        Path to raw Wealthtender reviews CSV. Defaults to config.RAW_CSV.

    Returns
    -------
    pd.DataFrame
        The cleaned reviews DataFrame.
    """
    raw_csv = raw_csv or config.RAW_CSV

    if not os.path.isfile(raw_csv):
        raise FileNotFoundError(
            f"Raw CSV not found: {raw_csv}\n"
            f"Place your Wealthtender reviews CSV at {config.RAW_CSV} "
            f"(or pass --input <path>)."
        )

    # Ensure output directories exist
    os.makedirs(config.QUALITY_DIR, exist_ok=True)
    os.makedirs(config.LEXICAL_DIR, exist_ok=True)
    os.makedirs(config.MACRO_DIR, exist_ok=True)

    # ── Cell [5/6]: Raw file metadata ────────────────────────────────────────
    meta = {
        "raw_csv": os.path.basename(raw_csv),
        "sha256": sha256_file(raw_csv),
        "bytes": os.path.getsize(raw_csv),
    }
    meta_path = os.path.join(config.QUALITY_DIR, "raw_file_meta.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    print("Saved:", meta_path)

    # ── Cell [8]: Load & standardize ─────────────────────────────────────────
    df = pd.read_csv(raw_csv)

    # standardize column names (safe)
    df.columns = [c.strip() for c in df.columns]

    # Parse dates robustly
    for col in ["Date", "Post Modified Date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Basic checks
    expected = ["notification_page", "notification_name", "Content", "acf_rating"]
    missing_expected = [c for c in expected if c not in df.columns]
    if missing_expected:
        raise ValueError(f"Missing expected columns: {missing_expected}")

    print("Shape:", df.shape)

    # ── Cell [10]: Standardize review fields ─────────────────────────────────
    df["advisor_id"] = df["notification_page"].fillna(df["notification_name"]).astype(str).str.strip()
    df["advisor_name"] = df["notification_name"].astype(str).str.strip()
    df["review_text_raw"] = df["Content"].fillna("").astype(str)
    df["rating"] = pd.to_numeric(df["acf_rating"], errors="coerce")
    df["review_date"] = df["Date"]
    if "Post Modified Date" in df.columns:
        df["review_date"] = df["review_date"].fillna(df["Post Modified Date"])

    # ── Filter: Remove known test/demo advisors ────────────────────────────
    # Uses explicit ID list from config. Remove this block when the raw
    # export includes an is_test or status field.
    n_before = len(df)
    df = df[~df["advisor_id"].isin(config.TEST_ADVISOR_IDS)].copy()
    n_dropped = n_before - len(df)
    if n_dropped > 0:
        print(f"Dropped {n_dropped} test/demo reviews "
              f"({len(config.TEST_ADVISOR_IDS)} excluded advisor IDs).")

    # ── Cell [11/12]: Quality summary & missing report ───────────────────────
    quality = {
        "n_rows": len(df),
        "n_cols": df.shape[1],
        "n_advisors": df["advisor_id"].nunique(),
        "n_names": df["advisor_name"].nunique(),
        "date_min": str(df["review_date"].min()),
        "date_max": str(df["review_date"].max()),
        "rating_missing_frac": float(df["rating"].isna().mean()),
        "text_empty_frac": float((df["review_text_raw"].str.strip() == "").mean()),
    }

    quality_path = os.path.join(config.QUALITY_DIR, "quality_summary.json")
    with open(quality_path, "w") as f:
        json.dump(quality, f, indent=2)
    print("Saved:", quality_path)

    quality_df = missing_report(df)
    quality_df_path = os.path.join(config.QUALITY_DIR, "missing_report.csv")
    quality_df.to_csv(quality_df_path, index=True)
    print("Saved:", quality_df_path)

    # ── Cell [14]: Token counts on raw text ──────────────────────────────────
    def token_count(s):
        return len(str(s).split())

    df["token_count"] = df["review_text_raw"].map(token_count)

    # ── Cell [21]: Text cleaning & normalization ─────────────────────────────
    # 0) Start from raw and keep a clean working copy (do NOT overwrite raw)
    df["review_text_clean"] = df["review_text_raw"].copy()

    # 1) Handle missing values + enforce string type safely
    df["review_text_clean"] = df["review_text_clean"].fillna("").astype(str)

    # 2) Normalize unicode (keeps meaning but standardizes characters like smart quotes)
    df["review_text_clean"] = df["review_text_clean"].apply(lambda x: unicodedata.normalize("NFKC", x))

    # 3) Standardize line breaks/tabs into spaces (turn multi-line reviews into single-line text)
    df["review_text_clean"] = df["review_text_clean"].str.replace(r"[\r\n\t]+", " ", regex=True)

    # 4) Remove URLs (common scrape noise)
    df["review_text_clean"] = df["review_text_clean"].str.replace(r"http\S+|www\.\S+|www\S+", " ", regex=True)

    # 5) Remove emails (rare but noisy if present)
    df["review_text_clean"] = df["review_text_clean"].str.replace(r"\S+@\S+", " ", regex=True)

    # 6) Remove bullets / separator glyphs (copy-paste artifacts)
    df["review_text_clean"] = df["review_text_clean"].str.replace(r"[•▪►◆■│]+", " ", regex=True)

    # 7) Remove platform boilerplate disclaimers ONLY if present
    for pat in config.BOILERPLATE_PATTERNS:
        df["review_text_clean"] = df["review_text_clean"].str.replace(pat, " ", regex=True, flags=re.IGNORECASE)

    # 8) Normalize whitespace again (after removals)
    df["review_text_clean"] = df["review_text_clean"].str.replace(r"\s+", " ", regex=True).str.strip()

    # 9) Normalize exaggerated punctuation + stretched letters (light-touch)
    df["review_text_clean"] = df["review_text_clean"].str.replace(r"([!?.,])\1{2,}", r"\1", regex=True)
    df["review_text_clean"] = df["review_text_clean"].str.replace(r"(.)\1{3,}", r"\1\1", regex=True)

    # 10) Lowercase for consistency
    df["review_text_clean"] = df["review_text_clean"].str.lower()

    # 11) Create token counts on cleaned text
    df["clean_token_count"] = df["review_text_clean"].str.split().str.len()

    # 12) Drop empty / near-empty reviews created after cleaning
    df = df[df["review_text_clean"].str.len() > 5].copy()

    # 13) Track cleaning impact
    df["raw_len"] = df["review_text_raw"].fillna("").astype(str).str.len()
    df["clean_len"] = df["review_text_clean"].str.len()

    print("Number of reviews after cleaning:", df.shape[0])

    # ── Cell [22]: Save cleaned reviews ──────────────────────────────────────
    processed_path = os.path.join(config.MACRO_DIR, "reviews_clean.csv")
    df.to_csv(processed_path, index=False)
    print("Saved:", processed_path)

    # ── Cell [14/15]: EDA summary ────────────────────────────────────────────
    eda = {}
    eda["reviews"] = int(df["review_text_raw"].notna().sum())
    eda["advisors"] = int(df["advisor_id"].nunique())
    eda["rating_counts"] = df["rating"].value_counts(dropna=False).sort_index()
    rev_per_adv = df.groupby("advisor_id").size().sort_values(ascending=False)
    eda["rev_per_adv_summary"] = rev_per_adv.describe()
    eda["token_count_summary"] = df["token_count"].describe()
    eda["pct_under_20_tokens"] = float((df["token_count"] < 20).mean())
    eda["pct_under_50_tokens"] = float((df["token_count"] < 50).mean())

    eda_dir = os.path.join(config.MACRO_DIR, "eda")
    os.makedirs(eda_dir, exist_ok=True)
    eda_path = os.path.join(eda_dir, "eda_summary.json")
    with open(eda_path, "w") as f:
        json.dump(
            {k: (v.to_dict() if hasattr(v, "to_dict") else v) for k, v in eda.items()},
            f, indent=2, default=str,
        )
    print("Saved:", eda_path)

    # ── Cell [19]: Coverage ──────────────────────────────────────────────────
    rev_per_adv = df.groupby("advisor_id").size()
    coverage = {
        "advisors_total": int(rev_per_adv.shape[0]),
        "pct_advisors_lt3": float((rev_per_adv < 3).mean()),
        "pct_advisors_lt5": float((rev_per_adv < 5).mean()),
        "pct_advisors_lt10": float((rev_per_adv < 10).mean()),
        "median_reviews_per_advisor": float(rev_per_adv.median()),
        "p90_reviews_per_advisor": float(rev_per_adv.quantile(0.90)),
    }
    coverage_path = os.path.join(eda_dir, "coverage.json")
    with open(coverage_path, "w") as f:
        json.dump(coverage, f, indent=2)
    print("Saved:", coverage_path)

    # ── Cell [24]: Lexical analysis ──────────────────────────────────────────
    tokens = []
    for t in df["review_text_clean"].astype(str).tolist():
        tokens.extend(tokenize_simple(t))

    top_words = Counter(tokens).most_common(40)

    def bigrams(words):
        return list(zip(words, words[1:]))

    bigram_counts = Counter()
    for t in df["review_text_clean"].astype(str).tolist():
        w = tokenize_simple(t)
        bigram_counts.update(bigrams(w))

    top_bigrams = bigram_counts.most_common(40)

    top_words_df = pd.DataFrame(top_words, columns=["token", "count"])
    top_bigrams_df = pd.DataFrame(
        [(" ".join(bg), c) for bg, c in top_bigrams],
        columns=["bigram", "count"],
    )

    top_words_df.to_csv(os.path.join(config.LEXICAL_DIR, "top_tokens.csv"), index=False)
    top_bigrams_df.to_csv(os.path.join(config.LEXICAL_DIR, "top_bigrams.csv"), index=False)
    print("Saved lexical CSVs.")

    return df
