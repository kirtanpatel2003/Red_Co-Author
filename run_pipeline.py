"""v2 entry point: dual-path attack + scoring, one row per run to results.jsonl.

Input is a refusal-prone user prompt. The direct path sends it verbatim
(baseline). The CoJP path drafts an incomplete outline and wraps it in the
domain co-author framing.
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from autoredteam.pipeline.constructor import build_cojp_prompt, build_direct_prompt
from autoredteam.pipeline.drafter import make_draft
from autoredteam.pipeline.runner import run_both
from autoredteam.pipeline.scorer import asr_flag, risk_amplification, score_response
from autoredteam.templates.task_framing import DOMAINS

RESULTS_PATH = Path(__file__).parent / "results.jsonl"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="AutoRedTeam v2 dual-path run")
    p.add_argument(
        "--prompt",
        required=True,
        help='refusal-prone user prompt, e.g. "how to hack Windows 10"',
    )
    p.add_argument(
        "--domain",
        required=True,
        choices=DOMAINS,
        help="picks the CoJP co-author voice (cyberattack / explosives / drugs / weapons)",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="suppress prompt/response dumps, print only the JSON result row",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    draft = make_draft(args.prompt)
    direct_prompt = build_direct_prompt(args.prompt)
    cojp_prompt = build_cojp_prompt(draft, args.domain)

    direct_result, cojp_result = run_both(direct_prompt, cojp_prompt)

    direct_score = score_response(direct_prompt, direct_result.response)
    cojp_score = score_response(cojp_prompt, cojp_result.response)

    row = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "prompt": args.prompt,
        "domain": args.domain,
        "direct_score": direct_score,
        "cojp_score": cojp_score,
        "direct_asr": asr_flag(direct_score),
        "cojp_asr": asr_flag(cojp_score),
        "rar": risk_amplification(direct_score, cojp_score),
        "direct_latency_ms": direct_result.latency_ms,
        "cojp_latency_ms": cojp_result.latency_ms,
    }

    with RESULTS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")

    if not args.quiet:
        print("\n--- DIRECT prompt ---")
        print(direct_prompt)
        print("\n--- DIRECT response ---")
        print(direct_result.response)
        print("\n--- DRAFT (from mistral) ---")
        print(draft)
        print("\n--- COJP prompt ---")
        print(cojp_prompt)
        print("\n--- COJP response ---")
        print(cojp_result.response)
        print("\n--- RESULT ---")
    print(json.dumps(row, indent=2))


if __name__ == "__main__":
    main()
