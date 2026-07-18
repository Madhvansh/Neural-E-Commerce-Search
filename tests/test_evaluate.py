"""Regression tests for qrel-complete ranking evaluation."""

import pytest

from necs.data.esci import ESCIExample
from necs.eval.evaluate import (
    evaluate_classification,
    evaluate_rankings,
    group_by_query,
)


def _example(query_id, product_id, label):
    return ESCIExample(
        query_id=query_id,
        query=f"query {query_id}",
        product_id=product_id,
        product_text=f"product {product_id}",
        label=label,
        split="test",
    )


def test_omitted_relevant_product_prevents_perfect_ndcg():
    grouped = group_by_query(
        [
            _example(1, "exact", "E"),
            _example(1, "irrelevant", "I"),
        ]
    )
    metrics = evaluate_rankings({1: ["irrelevant"]}, grouped)
    assert metrics["ndcg@10"] == 0.0
    assert metrics["recall@10"] == 0.0


def test_missing_query_counts_as_zero():
    grouped = group_by_query(
        [
            _example(1, "exact-1", "E"),
            _example(2, "exact-2", "E"),
        ]
    )
    metrics = evaluate_rankings({1: ["exact-1"]}, grouped)
    assert metrics["num_queries"] == 2
    assert metrics["ndcg@10"] == pytest.approx(0.5)
    assert metrics["recall@10"] == pytest.approx(0.5)


def test_complete_ideal_ranking_scores_one():
    grouped = group_by_query(
        [
            _example(1, "exact", "E"),
            _example(1, "substitute", "S"),
            _example(1, "irrelevant", "I"),
        ]
    )
    metrics = evaluate_rankings(
        {1: ["exact", "substitute", "irrelevant"]},
        grouped,
    )
    assert metrics["ndcg@10"] == pytest.approx(1.0)
    assert metrics["recall@10"] == pytest.approx(1.0)


def test_duplicate_product_ids_are_rejected():
    grouped = group_by_query([_example(1, "exact", "E")])
    with pytest.raises(ValueError, match="duplicate product ids"):
        evaluate_rankings({1: ["exact", "exact"]}, grouped)


def test_unjudged_product_ids_are_rejected():
    grouped = group_by_query([_example(1, "exact", "E")])
    with pytest.raises(ValueError, match="unjudged product ids"):
        evaluate_rankings({1: ["not-a-candidate"]}, grouped)


def test_classification_rejects_length_mismatch():
    with pytest.raises(ValueError, match="same length"):
        evaluate_classification(["E", "S"], ["E"])
