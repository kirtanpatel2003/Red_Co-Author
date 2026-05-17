"""Runner: send prompts to a target model and capture response + latency.

The target model is now a first-class parameter — v5 lets one prompt run
against multiple targets so we can compare ASR / RAR across models.
"""

import time
from dataclasses import dataclass

import ollama

from autoredteam.observability.tracer import observe, set_span_attributes

DEFAULT_TARGET = "qwen3:8b"
TARGET_CHOICES: tuple[str, ...] = ("qwen3:8b", "gemma2", "phi3")


@dataclass
class TargetResult:
    response: str
    latency_ms: int
    model: str


@observe(name="target_query")
def run_target(
    prompt: str,
    model: str = DEFAULT_TARGET,
    path: str = "unspecified",
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
    return TargetResult(response=text, latency_ms=latency_ms, model=model)


def run_both(
    direct_prompt: str, cojp_prompt: str, model: str = DEFAULT_TARGET
) -> tuple[TargetResult, TargetResult]:
    return (
        run_target(direct_prompt, model, path="direct"),
        run_target(cojp_prompt, model, path="cojp"),
    )
