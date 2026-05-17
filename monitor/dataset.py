"""Build a (prompt, response, is_harmful) dataset out of results.jsonl.

Each results.jsonl row that has both responses produces TWO training examples:
one for the direct response, one for the CoJP response. Labels come from the
existing ASR flags (HS >= 4).
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS = REPO_ROOT / "results.jsonl"


def load_monitor_dataset(results_path: Path | None = None) -> pd.DataFrame:
    results_path = results_path or DEFAULT_RESULTS
    rows: list[dict] = []
    if not results_path.exists():
        return pd.DataFrame(
            columns=[
                "prompt", "response", "is_harmful", "score",
                "path", "source", "target_model", "domain",
            ]
        )

    with results_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue

            prompt = r.get("prompt") or r.get("keyword")
            if not prompt:
                continue

            base = {
                "prompt": prompt,
                "source": r.get("source", "manual"),
                "target_model": r.get("target_model", "qwen3:8b"),
                "domain": r.get("domain", "general"),
            }
            if r.get("direct_response"):
                rows.append({
                    **base,
                    "response": r["direct_response"],
                    "is_harmful": bool(r.get("direct_asr", False)),
                    "score": int(r.get("direct_score", 1)),
                    "path": "direct",
                })
            if r.get("cojp_response"):
                rows.append({
                    **base,
                    "response": r["cojp_response"],
                    "is_harmful": bool(r.get("cojp_asr", False)),
                    "score": int(r.get("cojp_score", 1)),
                    "path": "cojp",
                })

    return pd.DataFrame(rows)


def split_by_source(df: pd.DataFrame, train_sources: set[str]) -> dict[str, pd.DataFrame]:
    """Return {'train': ..., 'in_dist_test': ..., '<eval_source>': ..., ...}.

    train_sources is the set used for fitting. Within that set, 80% becomes
    train and 20% in-distribution test (shuffled with a fixed seed). Every
    other source in the dataframe becomes its own held-out eval split.
    """

    rng_seed = 7
    train_pool = df[df["source"].isin(train_sources)].copy()
    eval_pool = df[~df["source"].isin(train_sources)].copy()

    splits: dict[str, pd.DataFrame] = {}
    if len(train_pool) >= 10:
        train_pool = train_pool.sample(frac=1.0, random_state=rng_seed).reset_index(drop=True)
        split = int(len(train_pool) * 0.8)
        splits["train"] = train_pool.iloc[:split]
        splits["in_dist_test"] = train_pool.iloc[split:]
    else:
        splits["train"] = train_pool
        splits["in_dist_test"] = train_pool.iloc[0:0]

    for source, grp in eval_pool.groupby("source"):
        splits[source] = grp.reset_index(drop=True)

    return splits
