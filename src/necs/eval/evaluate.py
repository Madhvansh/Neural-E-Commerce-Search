"""End-to-end evaluation of the two-stage pipeline against the BM25 baseline.

For every test query we form the candidate set from its judged products, score
them with each system, and compute:

* **NDCG@10** over graded ESCI gains (ranking quality),
* **Recall@100** of Exact products (first-stage coverage),
* **micro-F1** of the 4-way ESCI prediction (reranker classification).
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from necs.data.esci import ESCIExample
from necs.data.preprocess import label_to_index, relevance_gain
from necs.eval.metrics import classification_report, mean_ndcg_at_k, recall_at_k
from necs.utils.logging import get_logger

logger = get_logger(__name__)


def group_by_query(examples: Sequence[ESCIExample]) -> dict[int, list[ESCIExample]]:
    grouped: dict[int, list[ESCIExample]] = defaultdict(list)
    for ex in examples:
        grouped[ex.query_id].append(ex)
    return grouped


def gains_for_ranking(
    ranked_product_ids: Sequence[str], label_by_id: dict[str, str]
) -> list[float]:
    """Map a ranking of product ids to graded ESCI relevance gains."""
    return [relevance_gain(label_by_id.get(pid, "I")) for pid in ranked_product_ids]


def evaluate_rankings(
    rankings: dict[int, list[str]],
    grouped: dict[int, list[ESCIExample]],
    k: int = 10,
    recall_k: int = 100,
) -> dict[str, float]:
    """Compute ranking metrics from per-query product-id rankings."""
    per_query_gains: list[list[float]] = []
    recalls: list[float] = []
    for qid, ranked in rankings.items():
        label_by_id = {ex.product_id: ex.label for ex in grouped.get(qid, [])}
        per_query_gains.append(gains_for_ranking(ranked, label_by_id))

        num_exact = sum(1 for ex in grouped.get(qid, []) if ex.label == "E")
        rel_flags = [1 if label_by_id.get(pid) == "E" else 0 for pid in ranked]
        recalls.append(recall_at_k(rel_flags, num_exact, recall_k))

    return {
        f"ndcg@{k}": mean_ndcg_at_k(per_query_gains, k),
        f"recall@{recall_k}": sum(recalls) / len(recalls) if recalls else 0.0,
        "num_queries": len(rankings),
    }


def evaluate_classification(
    y_true: Sequence[str], y_pred: Sequence[str]
) -> dict:
    """Classification report from predicted vs gold ESCI letters."""
    yt = [label_to_index(y) for y in y_true]
    yp = [label_to_index(y) for y in y_pred]
    return classification_report(yt, yp, num_classes=4)


def summarize(name: str, ranking: dict, classification: dict | None = None) -> str:
    """Human-readable one-block summary for logs / reports."""
    lines = [f"=== {name} ==="]
    for key, value in ranking.items():
        formatted = f"{value:.4f}" if isinstance(value, float) else str(value)
        lines.append(f"  {key:<14} {formatted}")
    if classification:
        lines.append(f"  micro_f1       {classification['micro_f1']:.4f}")
        lines.append(f"  macro_f1       {classification['macro_f1']:.4f}")
    return "\n".join(lines)
