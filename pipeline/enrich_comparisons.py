#!/usr/bin/env python3
"""Generate partner-group associations for the Comparisons tab.

THIS FILE IS TEMPORARY DEVELOPMENT SCAFFOLDING.
It can be deleted with zero impact on the rest of the pipeline once
real partner_group data arrives in the raw Wealthtender export.

How it works
------------
1. Reads reviews_clean.csv (output of clean.py).
2. Checks whether a `partner_group` column already exists in the data.
   - YES → writes real partner_groups.csv from it (production mode).
   - NO  → derives mock groups from firm URL slugs (dev mode).
3. Writes to artifacts/scoring/partner_groups_mock.csv, which the API
   (api/services/artifacts.py) already knows how to load.

Usage
-----
    python -m pipeline.enrich_comparisons          # standalone
    python -m pipeline.run                          # called automatically if present

Delete this file later — nothing in clean.py, embed.py, or score.py
imports or depends on it.

See NOTICE for full team attribution.
"""
import os
import re

import pandas as pd

from . import config


# ──────────────────────────────────────────────────────────────────────────────
# Mock group definitions
# ──────────────────────────────────────────────────────────────────────────────
# These map real advisory-firm URL slugs to partner group codes/names.
# When real partner_group data arrives, this entire dict goes away.

_FIRM_SLUG_TO_GROUP = {
    "berkshire-money-management": ("PG-BMM", "Berkshire Money Management"),
    "twin-peaks-wealth-advisors": ("PG-TPWA", "Twin Peaks Wealth Advisors"),
    "pax-financial-group":        ("PG-PAX", "PAX Financial Group"),
    "edge-financial-advisors":    ("PG-EDGE", "Edge Financial Advisors"),
    "zenith-wealth-partners":     ("PG-ZWP", "Zenith Wealth Partners"),
    "beacon-wealth-consultants":  ("PG-BWC", "Beacon Wealth Consultants"),
    "level-wealth-management":    ("PG-LWM", "Level Wealth Management"),
    "covenant-wealth-advisors":   ("PG-CWA", "Covenant Wealth Advisors"),
    "bouchey-financial-group":    ("PG-BFG", "Bouchey Financial Group"),
    "abundo-wealth":              ("PG-ABUN", "Abundo Wealth"),
}


def _extract_firm_slug(advisor_id: str) -> str | None:
    """Extract advisory-firm slug from an advisor URL, if present."""
    # Firm URLs:  .../advisory-firms/abundo-wealth/
    # Advisor URLs: .../financial-advisors/john-doe-cfp/
    # We want to associate advisors with firms, so we look at the
    # advisor_dimension_scores to find which advisors share a firm.
    return None  # advisors don't carry firm slug in their own URL


def _build_mock_groups(reviews_clean: pd.DataFrame,
                       advisor_scores: pd.DataFrame) -> pd.DataFrame:
    """Build mock partner_groups_mock.csv from advisor score data.

    Strategy: for each firm in advisor_dimension_scores, find individual
    advisors that share reviews for that firm (via reviews_clean), and
    group them under a mock partner_group code.
    """
    # Get firms and individual advisors from the scores file
    firms = advisor_scores[
        advisor_scores["entity_type"] == "firm"
    ]["advisor_id"].tolist()

    advisors = advisor_scores[
        advisor_scores["entity_type"] == "advisor"
    ][["advisor_id", "advisor_name"]].copy()

    # From reviews_clean, build a mapping: advisor_id → set of firm_ids
    # An advisor's reviews appear under their personal URL, but we can
    # also check if the same advisor_name appears under a firm URL.
    # However, the simplest approach: use the existing mock definitions.

    # Check if we already have a mock file we should preserve
    existing_path = os.path.join(config.SCORING_DIR, "partner_groups_mock.csv")
    if os.path.exists(existing_path):
        existing = pd.read_csv(existing_path, encoding="utf-8")
        # Verify all advisor_ids in existing mock still exist in scores
        valid_ids = set(advisor_scores["advisor_id"])
        existing_valid = existing[existing["advisor_id"].isin(valid_ids)]
        if len(existing_valid) == len(existing):
            print("Existing partner_groups_mock.csv is still valid — keeping it.")
            return existing
        else:
            dropped = len(existing) - len(existing_valid)
            print(f"Existing mock has {dropped} stale advisor_ids — regenerating.")

    # Build from the hardcoded firm-slug mapping
    # For each firm slug, find advisors in reviews_clean whose reviews
    # are associated with that firm
    rows = []

    # Get unique advisor_ids from reviews that are individual advisors
    review_advisors = reviews_clean[
        reviews_clean["advisor_id"].str.contains("/financial-advisors/", na=False)
    ]["advisor_id"].unique()

    # For each known firm, find advisors whose reviews mention that firm
    # by checking if they appear in the scores file
    for firm_slug, (group_code, group_name) in _FIRM_SLUG_TO_GROUP.items():
        firm_url = f"https://wealthtender.com/advisory-firms/{firm_slug}/"
        # Check if this firm exists in our data
        if firm_url not in set(advisor_scores["advisor_id"]):
            # Try without trailing slash
            firm_url = firm_url.rstrip("/")
            if firm_url not in set(advisor_scores["advisor_id"]):
                continue

        # Find advisors associated with this firm
        # Strategy: look for advisors whose reviews also appear under
        # the firm's reviews (shared advisor_name)
        firm_reviews = reviews_clean[
            reviews_clean["advisor_id"] == firm_url
        ]
        if firm_reviews.empty:
            # Try with trailing slash
            firm_reviews = reviews_clean[
                reviews_clean["advisor_id"] == firm_url + "/"
            ]

        if not firm_reviews.empty:
            # Find advisor names that appear in both firm and individual reviews
            firm_reviewer_names = set()
            # Get advisor names from the firm's reviews
            firm_name = advisor_scores.loc[
                advisor_scores["advisor_id"].str.contains(firm_slug, na=False),
                "advisor_name"
            ]
            if not firm_name.empty:
                firm_name = firm_name.iloc[0]

            # Find individual advisors that have reviews mentioning
            # the same firm name or similar patterns
            # Simpler: just pick advisors whose names appear in the
            # scores file and randomly assign them
            pass

        # Fallback: use advisors from the original mock if available
        # This keeps the mock stable across regenerations

    # If we couldn't build organically, reproduce the existing mock pattern
    # This is the pragmatic approach: the mock data was hand-curated to
    # demonstrate the feature. We preserve it until real data arrives.
    if not rows:
        print("Generating mock partner groups from curated firm assignments.")
        rows = _generate_curated_mock(advisor_scores, reviews_clean)

    df = pd.DataFrame(rows, columns=["advisor_id", "partner_group_code",
                                      "partner_group_name"])
    return df


def _generate_curated_mock(advisor_scores: pd.DataFrame,
                           reviews_clean: pd.DataFrame) -> list:
    """Generate mock partner groups by assigning real advisors to firms.

    For each known firm in _FIRM_SLUG_TO_GROUP, find individual advisors
    that have sufficient reviews, and assign a subset to that firm's
    partner group. This gives the comparisons tab realistic-looking data.
    """
    import hashlib

    individual_advisors = advisor_scores[
        advisor_scores["entity_type"] == "advisor"
    ]["advisor_id"].tolist()

    # Count reviews per advisor
    review_counts = reviews_clean.groupby("advisor_id").size()
    # Filter to advisors with enough reviews for meaningful comparison
    eligible = [
        aid for aid in individual_advisors
        if review_counts.get(aid, 0) >= 3
    ]

    # Deterministic shuffle using hash (reproducible without numpy random)
    eligible.sort(key=lambda x: hashlib.sha256(x.encode()).hexdigest())

    rows = []
    idx = 0
    for firm_slug, (group_code, group_name) in _FIRM_SLUG_TO_GROUP.items():
        # Assign 3-5 advisors per group
        n = 3 + (hash(group_code) % 3)  # deterministic 3, 4, or 5
        for _ in range(n):
            if idx >= len(eligible):
                break
            rows.append((eligible[idx], group_code, group_name))
            idx += 1

    return rows


def _build_real_groups(reviews_clean: pd.DataFrame) -> pd.DataFrame:
    """Build partner_groups.csv from real partner_group column in data."""
    groups = reviews_clean[
        ["advisor_id", "partner_group"]
    ].drop_duplicates(subset="advisor_id")

    # Create human-readable group names from codes
    # (adjust this logic when real data format is known)
    groups = groups.rename(columns={"partner_group": "partner_group_code"})
    groups["partner_group_name"] = groups["partner_group_code"]
    return groups[["advisor_id", "partner_group_code", "partner_group_name"]]


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def run(reviews_clean_csv=None):
    """Generate partner group associations for the Comparisons tab.

    Auto-detects whether real partner_group data exists:
      - If yes → writes artifacts/scoring/partner_groups.csv
      - If no  → writes artifacts/scoring/partner_groups_mock.csv
    """
    if reviews_clean_csv is None:
        reviews_clean_csv = os.path.join(config.MACRO_DIR, "reviews_clean.csv")

    reviews = pd.read_csv(reviews_clean_csv, low_memory=False)
    print(f"Loaded {len(reviews)} reviews for comparisons enrichment.")

    os.makedirs(config.SCORING_DIR, exist_ok=True)

    # Check if real partner_group data exists
    if "partner_group" in reviews.columns:
        print("Real partner_group column found — writing production file.")
        df = _build_real_groups(reviews)
        out_path = os.path.join(config.SCORING_DIR, "partner_groups.csv")
        df.to_csv(out_path, index=False)
        print(f"Saved {len(df)} partner group associations to {out_path}")

        # Remove mock file if it exists (real data supersedes it)
        mock_path = os.path.join(config.SCORING_DIR, "partner_groups_mock.csv")
        if os.path.exists(mock_path):
            os.remove(mock_path)
            print(f"Removed obsolete {mock_path}")
    else:
        print("No partner_group column in data — generating mock associations.")
        advisor_scores_path = os.path.join(
            config.SCORING_DIR, "advisor_dimension_scores.csv"
        )
        if not os.path.exists(advisor_scores_path):
            print("WARNING: advisor_dimension_scores.csv not found. "
                  "Run score.py first, or use --stage score.")
            return

        advisor_scores = pd.read_csv(advisor_scores_path, low_memory=False)
        df = _build_mock_groups(reviews, advisor_scores)
        out_path = os.path.join(config.SCORING_DIR, "partner_groups_mock.csv")
        df.to_csv(out_path, index=False)
        print(f"Saved {len(df)} mock partner group associations to {out_path}")

    return df


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    run()
