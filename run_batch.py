"""Batch runner: iterate over (prompt x target_model) and write results.jsonl rows.

Resumable: rows already present in results.jsonl (matched on
(prompt, target_model, source)) are skipped, so re-running picks up where a
previous run stopped.

Examples:
    python run_batch.py --corpus seed --targets qwen3:8b,gemma2,phi3
    python run_batch.py --corpus advbench --targets qwen3:8b --limit 50
    python run_batch.py --corpus datasets/hardbench.jsonl --targets qwen3:8b,phi3
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from autoredteam.observability.tracer import ENABLED as LAMINAR_ENABLED
from autoredteam.observability.tracer import get_trace_id
from autoredteam.pipeline.runner import TARGET_CHOICES
from datasets.loaders import load_corpus
from run_pipeline import attack_run

RESULTS_PATH = Path(__file__).parent / "results.jsonl"


def _already_done(results_path: Path) -> set[tuple[str, str, str]]:
    """Return (prompt, target_model, source) tuples already written."""
    done: set[tuple[str, str, str]] = set()
    if not results_path.exists():
        return done
    with results_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            prompt = row.get("prompt") or row.get("keyword")
            target = row.get("target_model", "qwen3:8b")
            source = row.get("source", "manual")
            if prompt:
                done.add((prompt, target, source))
    return done


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="batch attack runner over a corpus")
    p.add_argument("--corpus", required=True, help="corpus name (seed/advbench/hardbench) or path")
    p.add_argument(
        "--targets",
        required=True,
        help=f"comma-separated target models; choose from {','.join(TARGET_CHOICES)}",
    )
    p.add_argument("--limit", type=int, default=None, help="cap number of prompts processed")
    p.add_argument(
        "--no-resume",
        action="store_true",
        help="ignore existing rows; re-run everything",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    targets = [t.strip() for t in args.targets.split(",") if t.strip()]
    unknown = [t for t in targets if t not in TARGET_CHOICES]
    if unknown:
        print(f"[batch] unknown targets: {unknown}", file=sys.stderr)
        print(f"[batch] valid: {list(TARGET_CHOICES)}", file=sys.stderr)
        return 2

    corpus = load_corpus(args.corpus)
    if args.limit is not None:
        corpus = corpus[: args.limit]
    print(f"[batch] corpus {args.corpus!r}: {len(corpus)} prompts × {len(targets)} targets = {len(corpus) * len(targets)} runs")

    done = set() if args.no_resume else _already_done(RESULTS_PATH)
    skipped = total = 0

    for row in corpus:
        prompt = row["prompt"]
        domain = row["domain"]
        source = row["source"]
        for target in targets:
            total += 1
            key = (prompt, target, source)
            if key in done:
                skipped += 1
                continue
            print(f"\n[batch] ({total}) prompt={prompt[:60]!r} domain={domain} target={target}")
            try:
                bundle = attack_run(prompt, domain, target=target)
            except Exception as exc:
                print(f"[batch] ERROR: {exc!r}", file=sys.stderr)
                continue
            trace_id = get_trace_id()
            out = {
                "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "prompt": prompt,
                "domain": domain,
                "target_model": target,
                "source": source,
                "direct_score": bundle["direct_score"],
                "cojp_score": bundle["cojp_score"],
                "direct_asr": bundle["direct_asr"],
                "cojp_asr": bundle["cojp_asr"],
                "rar": bundle["rar"],
                "direct_latency_ms": bundle["direct_latency_ms"],
                "cojp_latency_ms": bundle["cojp_latency_ms"],
                "direct_response": bundle["direct_response"],
                "cojp_response": bundle["cojp_response"],
                "trace_id": trace_id,
                "laminar_enabled": LAMINAR_ENABLED,
            }
            with RESULTS_PATH.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(out) + "\n")
            print(
                f"[batch] -> direct HS={out['direct_score']} cojp HS={out['cojp_score']} "
                f"RAR={out['rar']}"
            )
            done.add(key)

    print(f"\n[batch] done. attempted={total} skipped(resumed)={skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
