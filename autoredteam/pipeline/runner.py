"""Runner: send a prompt to the target model and return the raw response."""

import ollama

TARGET_MODEL = "qwen3:8b"


def run_target(prompt: str, model: str = TARGET_MODEL) -> str:
    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.7},
    )
    return response["message"]["content"].strip()
