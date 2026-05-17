"""Compute standard binary-classification metrics for a monitor on a split."""

from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)


def metrics(y_true: np.ndarray, y_prob: np.ndarray, threshold: float = 0.5) -> dict:
    y_true = np.asarray(y_true, dtype=int)
    y_prob = np.asarray(y_prob, dtype=float)
    y_pred = (y_prob >= threshold).astype(int)

    out = {
        "n": int(len(y_true)),
        "positive_rate": float(np.mean(y_true)) if len(y_true) else float("nan"),
        "accuracy": float(accuracy_score(y_true, y_pred)) if len(y_true) else float("nan"),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "auc": (
            float(roc_auc_score(y_true, y_prob))
            if len(set(y_true.tolist())) > 1
            else float("nan")
        ),
    }
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1]) if len(y_true) else np.zeros((2, 2))
    out["confusion_matrix"] = cm.tolist()
    return out


def roc_points(y_true: np.ndarray, y_prob: np.ndarray) -> dict:
    if len(set(np.asarray(y_true).tolist())) < 2:
        return {"fpr": [], "tpr": [], "auc": float("nan")}
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    auc = float(roc_auc_score(y_true, y_prob))
    return {"fpr": fpr.tolist(), "tpr": tpr.tolist(), "auc": auc}
