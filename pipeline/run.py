#!/usr/bin/env python3
"""Wealthtender Review Analytics -- full pipeline orchestrator.

Usage
-----
    python -m pipeline.run                 # run stages 1->2->3 (incremental)
    python -m pipeline.run --full          # force full re-embed (ignore existing)
    python -m pipeline.run --stage clean   # run only stage 1
    python -m pipeline.run --stage embed   # run only stage 2 (incremental)
    python -m pipeline.run --stage score   # run only stage 3
    python -m pipeline.run --stage enrich  # run only comparisons enrichment
    python -m pipeline.run --validate      # compare outputs to backed-up artifacts

See NOTICE for full team attribution.
"""
import argparse
import os
import sys

from . import config


def validate_artifacts(backup_dir):
    """Compare current artifacts against a backup directory, byte-for-byte."""
    import filecmp

    pairs = [
        (config.MACRO_DIR, "reviews_clean.csv"),
        (config.QUALITY_DIR, "quality_summary.json"),
        (config.QUALITY_DIR, "missing_report.csv"),
        (config.LEXICAL_DIR, "top_tokens.csv"),
        (config.LEXICAL_DIR, "top_bigrams.csv"),
        (config.SCORING_DIR, "review_dimension_scores.csv"),
        (config.SCORING_DIR, "advisor_dimension_scores.csv"),
    ]

    all_ok = True
    for artifact_dir, filename in pairs:
        current = os.path.join(artifact_dir, filename)
        backup = os.path.join(
            backup_dir,
            os.path.relpath(artifact_dir, config.ARTIFACTS_DIR),
            filename,
        )

        if not os.path.exists(current):
            print(f"  MISSING  {current}")
            all_ok = False
            continue
        if not os.path.exists(backup):
            print(f"  NO BACKUP  {backup}")
            continue

        if filecmp.cmp(current, backup, shallow=False):
            print(f"  OK  {filename}")
        else:
            print(f"  DIFF  {filename}")
            all_ok = False

    return all_ok


def main():
    parser = argparse.ArgumentParser(description="Wealthtender pipeline runner")
    parser.add_argument(
        "--stage",
        choices=["clean", "embed", "score", "enrich"],
        default=None,
        help="Run only a specific stage (default: run all)",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Force full reprocess: re-embed all reviews from scratch "
             "(ignore existing embeddings). Useful when the model changes.",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Compare generated artifacts against artifacts_backup/",
    )
    parser.add_argument(
        "--backup-dir",
        default=os.path.join(config.PROJECT_ROOT, "artifacts_backup"),
        help="Path to backup artifacts for validation",
    )
    args = parser.parse_args()

    if args.validate:
        print("\n=== Validating artifacts ===")
        ok = validate_artifacts(args.backup_dir)
        sys.exit(0 if ok else 1)

    stages = [args.stage] if args.stage else ["clean", "embed", "score", "enrich"]

    if "clean" in stages:
        print("\n=== Stage 1: Clean ===")
        from . import clean
        clean.run()

    if "embed" in stages:
        print("\n=== Stage 2: Embed (main) ===")
        from . import embed
        embed.run(full_reprocess=args.full)

        print("\n=== Stage 2b: Embed (weighted-by-time) ===")
        embed.run_weighted()

    if "score" in stages:
        print("\n=== Stage 3: Score ===")
        from . import score
        score.run()

    if "enrich" in stages:
        print("\n=== Comparisons Enrichment ===")
        from . import enrich_comparisons
        enrich_comparisons.run()

    print("\n=== Pipeline complete ===")


if __name__ == "__main__":
    main()
