"""Runner: send prompts to the target model and capture response + latency."""

import time
from dataclasses import dataclass

import ollama

TARGET_MODEL = "qwen3:8b"


@dataclass
class TargetResult:
    response: str
    latency_ms: int


def run_target(prompt: str, model: str = TARGET_MODEL) -> TargetResult:
    t0 = time.perf_counter()
    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.7},
    )
    latency_ms = int((time.perf_counter() - t0) * 1000)
    return TargetResult(
        response=response["message"]["content"].strip(),
        latency_ms=latency_ms,
    )


def run_both(
    direct_prompt: str, cojp_prompt: str, model: str = TARGET_MODEL
) -> tuple[TargetResult, TargetResult]:
    return run_target(direct_prompt, model), run_target(cojp_prompt, model)
