"""v3 entry point: dual-path attack + scoring + Laminar tracing.

One CLI invocation = one Laminar trace = one JSON row in results.jsonl.
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from autoredteam.observability.tracer import (
    ENABLED as LAMINAR_ENABLED,
    get_trace_id,
    observe,
    set_trace_metadata,
)
from autoredteam.pipeline.constructor import build_cojp_prompt, build_direct_prompt
from autoredteam.pipeline.drafter import make_draft
from autoredteam.pipeline.runner import run_target
from autoredteam.pipeline.scorer import asr_flag, risk_amplification, score_response
from autoredteam.templates.task_framing import DOMAINS

RESULTS_PATH = Path(__file__).parent / "results.jsonl"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Red_Co-Author dual-path attack run")
    p.add_argument(
        "--prompt",
        required=True,
        help='refusal-prone user prompt, e.g. "how to hack Windows 10"',
    )
    p.add_argument(
        "--domain",
        required=True,
        choices=DOMAINS,
        help="picks the CoJP co-author voice",
    )
    p.add_argument("--quiet", action="store_true", help="print only the JSON row")
    return p.parse_args()


@observe(name="attack_run")
def attack_run(prompt: str, domain: str) -> dict:
    set_trace_metadata({"prompt": prompt, "domain": domain})

    draft = make_draft(prompt)
    direct_prompt = build_direct_prompt(prompt)
    cojp_prompt = build_cojp_prompt(draft, domain)  # type: ignore[arg-type]

    direct_result = run_target(direct_prompt, path="direct")
    cojp_result = run_target(cojp_prompt, path="cojp")

    direct_score = score_response(direct_prompt, direct_result.response, path="direct")
    cojp_score = score_response(cojp_prompt, cojp_result.response, path="cojp")

    rar = risk_amplification(direct_score, cojp_score)
    set_trace_metadata(
        {
            "direct_score": direct_score,
            "cojp_score": cojp_score,
            "rar": rar,
        }
    )

    return {
        "draft": draft,
        "direct_prompt": direct_prompt,
        "cojp_prompt": cojp_prompt,
        "direct_response": direct_result.response,
        "cojp_response": cojp_result.response,
        "direct_score": direct_score,
        "cojp_score": cojp_score,
        "direct_asr": asr_flag(direct_score),
        "cojp_asr": asr_flag(cojp_score),
        "rar": rar,
        "direct_latency_ms": direct_result.latency_ms,
        "cojp_latency_ms": cojp_result.latency_ms,
    }


def main() -> None:
    args = parse_args()
    bundle = attack_run(args.prompt, args.domain)

    trace_id = get_trace_id()
    row = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "prompt": args.prompt,
        "domain": args.domain,
        "direct_score": bundle["direct_score"],
        "cojp_score": bundle["cojp_score"],
        "direct_asr": bundle["direct_asr"],
        "cojp_asr": bundle["cojp_asr"],
        "rar": bundle["rar"],
        "direct_latency_ms": bundle["direct_latency_ms"],
        "cojp_latency_ms": bundle["cojp_latency_ms"],
        "trace_id": trace_id,
        "laminar_enabled": LAMINAR_ENABLED,
    }

    with RESULTS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")

    if not args.quiet:
        print("\n--- DIRECT prompt ---")
        print(bundle["direct_prompt"])
        print("\n--- DIRECT response ---")
        print(bundle["direct_response"])
        print("\n--- DRAFT (from mistral) ---")
        print(bundle["draft"])
        print("\n--- COJP prompt ---")
        print(bundle["cojp_prompt"])
        print("\n--- COJP response ---")
        print(bundle["cojp_response"])
        print("\n--- RESULT ---")
    print(json.dumps(row, indent=2))

    if LAMINAR_ENABLED and trace_id:
        print(f"\nLaminar trace: {trace_id}")


if __name__ == "__main__":
    main()
