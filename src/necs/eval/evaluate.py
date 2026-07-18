"""Evaluation helpers for the official ESCI ranking and classification tasks.

Ranking metrics are computed against the complete judged candidate set for each
query. Classification metrics are computed separately because Amazon's public
Task 1 ranking subset and Task 2 multiclass dataset are different protocols.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from necs.data.esci import ESCIExample
from necs.data.preprocess import label_to_index, relevance_gain
from necs.eval.metrics import classification_report, ndcg_at_k, recall_at_k


def group_by_query(examples: Sequence[ESCIExample]) -> dict[int, list[ESCIExample]]:
    grouped: dict[int, list[ESCIExample]] = defaultdict(list)
    for ex in examples:
        grouped[ex.query_id].append(ex)
    return grouped


def gains_for_ranking(
    ranked_product_ids: Sequence[str], label_by_id: dict[str, str]
) -> list[float]:
    """Map returned product ids to graded ESCI gains."""
    return [relevance_gain(label_by_id.get(pid, "I")) for pid in ranked_product_ids]


def evaluate_rankings(
    rankings: dict[int, list[str]],
    grouped: dict[int, list[ESCIExample]],
    k: int = 10,
    recall_k: int = 10,
) -> dict[str, float]:
    """Compute ranking metrics against complete per-query judgements.

    Missing queries count as zero rather than disappearing from the mean. The
    ideal DCG comes from all judged candidates, so a system cannot improve its
    denominator by omitting relevant products from its returned ranking.
    """
    unknown_queries = sorted(set(rankings) - set(grouped))
    if unknown_queries:
        raise ValueError(f"Rankings contain unknown query ids: {unknown_queries}")

    ndcgs: list[float] = []
    recalls: list[float] = []

    for qid, examples in grouped.items():
        ranked = rankings.get(qid, [])
        label_by_id = {ex.product_id: ex.label for ex in examples}
        if len(ranked) != len(set(ranked)):
            raise ValueError(f"Ranking for query {qid} contains duplicate product ids")
        unknown_products = sorted(set(ranked) - set(label_by_id))
        if unknown_products:
            raise ValueError(
                f"Ranking for query {qid} contains unjudged product ids: "
                f"{unknown_products}"
            )
        actual_gains = gains_for_ranking(ranked, label_by_id)
        ideal_gains = sorted(
            (relevance_gain(ex.label) for ex in examples),
            reverse=True,
        )
        ndcgs.append(ndcg_at_k(actual_gains, k, ideal_gains=ideal_gains))

        num_exact = sum(1 for ex in examples if ex.label == "E")
        exact_flags = [1 if label_by_id.get(pid) == "E" else 0 for pid in ranked]
        recalls.append(recall_at_k(exact_flags, num_exact, recall_k))

    count = len(grouped)
    return {
        f"ndcg@{k}": sum(ndcgs) / count if count else 0.0,
        f"recall@{recall_k}": sum(recalls) / count if count else 0.0,
        "num_queries": count,
    }


def evaluate_classification(y_true: Sequence[str], y_pred: Sequence[str]) -> dict:
    """Return a four-way ESCI classification report."""
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")
    truth = [label_to_index(label) for label in y_true]
    predicted = [label_to_index(label) for label in y_pred]
    return classification_report(truth, predicted, num_classes=4)


def summarize(name: str, ranking: dict, classification: dict | None = None) -> str:
    """Format a compact metric block for logs and saved run output."""
    lines = [f"=== {name} ==="]
    for key, value in ranking.items():
        formatted = f"{value:.4f}" if isinstance(value, float) else str(value)
        lines.append(f"  {key:<14} {formatted}")
    if classification:
        lines.append(f"  micro_f1       {classification['micro_f1']:.4f}")
        lines.append(f"  macro_f1       {classification['macro_f1']:.4f}")
    return "\n".join(lines)
