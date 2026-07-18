"""Ranking and classification metrics.

Pure NumPy with no torch/sklearn dependency so the suite is cheap to run and
exercises the exact code paths used in reporting. Ranking metrics take a list
of per-query relevance gains *already ordered by the system's ranking*; graded
gains follow the ESCI convention (Exact=1.0, Substitute=0.1, Complement=0.01,
Irrelevant=0.0).
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np


def dcg_at_k(gains: Sequence[float], k: int) -> float:
    """Discounted cumulative gain over the top-``k`` ranked items."""
    gains = np.asarray(gains[:k], dtype=float)
    if gains.size == 0:
        return 0.0
    discounts = 1.0 / np.log2(np.arange(2, gains.size + 2))
    return float(np.sum(gains * discounts))


def ndcg_at_k(
    ranked_gains: Sequence[float],
    k: int = 10,
    ideal_gains: Sequence[float] | None = None,
) -> float:
    """NDCG@k for a single query.

    ``ranked_gains`` are relevance gains in the order the system returned them.
    Pass the complete qrel gain set as ``ideal_gains`` whenever the returned
    ranking can omit judged items. Falling back to ``ranked_gains`` is valid only
    when that sequence contains the complete candidate set.
    """
    actual = dcg_at_k(ranked_gains, k)
    reference = ranked_gains if ideal_gains is None else ideal_gains
    ideal = dcg_at_k(sorted(reference, reverse=True), k)
    return actual / ideal if ideal > 0 else 0.0


def mean_ndcg_at_k(per_query_gains: Sequence[Sequence[float]], k: int = 10) -> float:
    """Mean NDCG@k across queries."""
    if not per_query_gains:
        return 0.0
    return float(np.mean([ndcg_at_k(g, k) for g in per_query_gains]))


def recall_at_k(ranked_relevant: Sequence[int], num_relevant: int, k: int = 100) -> float:
    """Fraction of relevant items recovered within the top-``k``.

    ``ranked_relevant`` is a 0/1 list flagging relevant items in ranked order.
    """
    if num_relevant <= 0:
        return 0.0
    hits = int(np.sum(np.asarray(ranked_relevant[:k])))
    return hits / num_relevant


def mrr(ranked_relevant: Sequence[int]) -> float:
    """Reciprocal rank of the first relevant item (0 if none)."""
    for rank, rel in enumerate(ranked_relevant, start=1):
        if rel:
            return 1.0 / rank
    return 0.0


def mean_mrr(per_query_relevant: Sequence[Sequence[int]]) -> float:
    if not per_query_relevant:
        return 0.0
    return float(np.mean([mrr(r) for r in per_query_relevant]))


def _confusion(y_true: np.ndarray, y_pred: np.ndarray, num_classes: int) -> np.ndarray:
    if y_true.ndim != 1 or y_pred.ndim != 1:
        raise ValueError("y_true and y_pred must be one-dimensional")
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")
    cm = np.zeros((num_classes, num_classes), dtype=int)
    for t, p in zip(y_true, y_pred):
        cm[t, p] += 1
    return cm


def micro_f1(y_true: Sequence[int], y_pred: Sequence[int], num_classes: int = 4) -> float:
    """Micro-averaged F1. For single-label multiclass this equals accuracy,
    but we compute it from pooled TP/FP/FN so it matches the multi-class report.
    """
    yt = np.asarray(y_true)
    yp = np.asarray(y_pred)
    cm = _confusion(yt, yp, num_classes)
    tp = np.trace(cm)
    fp = cm.sum() - tp
    fn = fp  # in single-label classification pooled FP == pooled FN
    denom = 2 * tp + fp + fn
    return float(2 * tp / denom) if denom else 0.0


def classification_report(
    y_true: Sequence[int], y_pred: Sequence[int], num_classes: int = 4
) -> dict:
    """Per-class precision/recall/F1 plus micro and macro F1."""
    yt = np.asarray(y_true)
    yp = np.asarray(y_pred)
    cm = _confusion(yt, yp, num_classes)

    per_class = {}
    f1s = []
    for c in range(num_classes):
        tp = cm[c, c]
        fp = cm[:, c].sum() - tp
        fn = cm[c, :].sum() - tp
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall)
            else 0.0
        )
        per_class[c] = {
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
            "support": int(cm[c, :].sum()),
        }
        f1s.append(f1)

    return {
        "per_class": per_class,
        "micro_f1": micro_f1(yt, yp, num_classes),
        "macro_f1": float(np.mean(f1s)) if f1s else 0.0,
        "confusion_matrix": cm.tolist(),
    }
