"""Download AdvBench's harmful_behaviors.csv from the llm-attacks repo.

Idempotent: skips the download if the file is already present and non-empty.
Run with: `python -m datasets.fetch_advbench`
"""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

URL = "https://raw.githubusercontent.com/llm-attacks/llm-attacks/main/data/advbench/harmful_behaviors.csv"
DEST = Path(__file__).resolve().parent / "advbench.csv"


def main() -> int:
    if DEST.exists() and DEST.stat().st_size > 0:
        print(f"[fetch_advbench] already present: {DEST} ({DEST.stat().st_size} bytes)")
        return 0
    print(f"[fetch_advbench] downloading {URL}")
    try:
        with urllib.request.urlopen(URL, timeout=30) as resp:
            data = resp.read()
    except Exception as exc:  # pragma: no cover
        print(f"[fetch_advbench] FAILED: {exc}", file=sys.stderr)
        return 1
    DEST.write_bytes(data)
    print(f"[fetch_advbench] wrote {DEST} ({len(data)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
