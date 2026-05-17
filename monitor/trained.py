"""Trained monitor — Ollama embeddings (nomic-embed-text) + sklearn LogisticRegression.

Embeddings are computed via the local Ollama daemon so no torch / sentence-
transformers install is needed. Trained classifier persists to monitor/artifacts/.
"""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import ollama
from sklearn.linear_model import LogisticRegression

EMBED_MODEL = "nomic-embed-text"
ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
ARTIFACT_PATH = ARTIFACT_DIR / "monitor.joblib"


def _embed_one(text: str) -> np.ndarray:
    out = ollama.embeddings(model=EMBED_MODEL, prompt=text)
    return np.asarray(out["embedding"], dtype=np.float32)


def _combine(prompt: str, response: str) -> str:
    return f"USER PROMPT:\n{prompt}\n\nASSISTANT RESPONSE:\n{response}"


def embed_pairs(prompts: list[str], responses: list[str]) -> np.ndarray:
    return np.stack([_embed_one(_combine(p, r)) for p, r in zip(prompts, responses)])


def train(prompts: list[str], responses: list[str], labels: list[int]) -> LogisticRegression:
    X = embed_pairs(prompts, responses)
    y = np.asarray(labels, dtype=int)
    clf = LogisticRegression(max_iter=1000, class_weight="balanced")
    clf.fit(X, y)
    return clf


def predict_proba(clf: LogisticRegression, prompts: list[str], responses: list[str]) -> np.ndarray:
    X = embed_pairs(prompts, responses)
    return clf.predict_proba(X)[:, 1]


def save(clf: LogisticRegression, path: Path = ARTIFACT_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, path)
    return path


def load(path: Path = ARTIFACT_PATH) -> LogisticRegression:
    return joblib.load(path)


def exists(path: Path = ARTIFACT_PATH) -> bool:
    return path.exists()
