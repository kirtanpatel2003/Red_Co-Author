"""Dataset loaders — normalise every source to the same shape.

Canonical row schema:
    {
        "prompt":  str,        # the refusal-prone user query
        "domain":  Domain,     # one of DOMAINS
        "source":  str,        # "seed" | "advbench" | "hardbench" | other tag
    }

Each loader returns an iterable of these dicts. `run_batch.py` consumes them.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterator

from autoredteam.templates.task_framing import DOMAINS, Domain

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "datasets"


def _coerce_domain(raw: str | None) -> Domain:
    if raw and raw in DOMAINS:
        return raw  # type: ignore[return-value]
    return "general"  # type: ignore[return-value]


def load_jsonl(path: Path, source: str | None = None) -> Iterator[dict]:
    """Generic JSONL loader. Each line must have at least a `prompt`; we
    fill in `domain` (default 'general') and `source` (default from path)."""

    src = source or path.stem
    with path.open("r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{lineno} — bad JSON: {exc}") from exc
            prompt = row.get("prompt")
            if not prompt:
                continue
            yield {
                "prompt": prompt,
                "domain": _coerce_domain(row.get("domain")),
                "source": row.get("source", src),
            }


def load_advbench(path: Path | None = None) -> Iterator[dict]:
    """AdvBench harmful_behaviors.csv → canonical rows.

    The CSV has columns `goal,target`; `goal` is the harmful instruction we
    want to send. AdvBench is untagged by topic so domain defaults to
    'general'.
    """

    csv_path = path or (DATA_DIR / "advbench.csv")
    if not csv_path.exists():
        raise FileNotFoundError(
            f"AdvBench CSV not found at {csv_path}. "
            "Run `python -m datasets.fetch_advbench` first."
        )
    with csv_path.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            goal = (row.get("goal") or "").strip()
            if not goal:
                continue
            yield {"prompt": goal, "domain": "general", "source": "advbench"}


def load_hardbench(path: Path | None = None) -> Iterator[dict]:
    """HarDBench JSONL → canonical rows.

    Ships with the 400-row HarDBench test split (100 prompts per category:
    cyberattack / drugs / explosives / weapons), converted from
    `HarDbench_test.json`. Each row carries `prompt` (the `prompt_only`
    field from the source), `domain` (lowercased category), `source`
    ("hardbench"), plus the original `hardbench_id`, `category`, and
    `template` for traceability.
    """

    jsonl_path = path or (DATA_DIR / "hardbench.jsonl")
    if not jsonl_path.exists():
        raise FileNotFoundError(
            f"HarDBench JSONL not found at {jsonl_path}. "
            "Place the dataset there (or use the bundled placeholder)."
        )
    yield from load_jsonl(jsonl_path, source="hardbench")


def load_seed(path: Path | None = None) -> Iterator[dict]:
    """Small curated handcrafted corpus used as a fast smoke test."""

    yield from load_jsonl(path or (DATA_DIR / "seed.jsonl"), source="seed")


LOADERS = {
    "advbench": load_advbench,
    "hardbench": load_hardbench,
    "seed": load_seed,
}


def load_corpus(name_or_path: str) -> list[dict]:
    """Resolve a corpus by short-name (advbench/hardbench/seed) or path."""

    if name_or_path in LOADERS:
        return list(LOADERS[name_or_path]())
    p = Path(name_or_path)
    if p.exists() and p.suffix == ".jsonl":
        return list(load_jsonl(p))
    if p.exists() and p.suffix == ".csv":
        return list(load_advbench(p))
    raise ValueError(
        f"Unknown corpus {name_or_path!r}. "
        f"Try one of {list(LOADERS)} or a path to a .jsonl/.csv file."
    )
