"""Fit the trained monitor on rows from chosen training corpora and persist it.

Examples:
    python -m monitor.train --train-sources seed,manual,ui
    python -m monitor.train --train-sources seed
"""

from __future__ import annotations

import argparse
import sys

from monitor.dataset import load_monitor_dataset, split_by_source
from monitor.trained import save, train


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--train-sources",
        default="seed,manual,ui",
        help="comma-separated source values used for training",
    )
    args = ap.parse_args()
    train_sources = set(s.strip() for s in args.train_sources.split(",") if s.strip())

    df = load_monitor_dataset()
    if df.empty:
        print("[train] results.jsonl is empty — generate data with run_batch.py first.", file=sys.stderr)
        return 1

    splits = split_by_source(df, train_sources=train_sources)
    train_df = splits["train"]
    if len(train_df) < 4:
        print(f"[train] only {len(train_df)} training samples (need >=4)", file=sys.stderr)
        return 1
    if train_df["is_harmful"].nunique() < 2:
        print("[train] training set has only one class — need both harmful and safe examples", file=sys.stderr)
        return 1

    print(f"[train] fitting on {len(train_df)} samples from sources={list(train_sources)}")
    print(f"[train] class balance: {train_df['is_harmful'].mean():.0%} harmful")

    clf = train(
        train_df["prompt"].tolist(),
        train_df["response"].tolist(),
        train_df["is_harmful"].astype(int).tolist(),
    )
    path = save(clf)
    print(f"[train] saved to {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
