"""Runner: send prompts to the target model and capture response + latency."""

import time
from dataclasses import dataclass

import ollama

from autoredteam.observability.tracer import observe, set_span_attributes

TARGET_MODEL = "qwen3:8b"


@dataclass
class TargetResult:
    response: str
    latency_ms: int


@observe(name="target_query")
def run_target(
    prompt: str, model: str = TARGET_MODEL, path: str = "unspecified"
) -> TargetResult:
    t0 = time.perf_counter()
    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.7},
    )
    latency_ms = int((time.perf_counter() - t0) * 1000)
    text = response["message"]["content"].strip()
    set_span_attributes(
        {
            "runner.model": model,
            "runner.path": path,
            "runner.latency_ms": latency_ms,
            "runner.response_chars": len(text),
        }
    )
    return TargetResult(response=text, latency_ms=latency_ms)


def run_both(
    direct_prompt: str, cojp_prompt: str, model: str = TARGET_MODEL
) -> tuple[TargetResult, TargetResult]:
    return (
        run_target(direct_prompt, model, path="direct"),
        run_target(cojp_prompt, model, path="cojp"),
    )
