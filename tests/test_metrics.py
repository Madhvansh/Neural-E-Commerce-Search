"""Tests for ranking and classification metrics."""

import math

import pytest

from necs.eval.metrics import (
    classification_report,
    dcg_at_k,
    mean_ndcg_at_k,
    micro_f1,
    mrr,
    ndcg_at_k,
    recall_at_k,
)


def test_dcg_first_item_undiscounted():
    # First position discount is 1 / log2(2) = 1, so DCG@1 == the first gain.
    assert dcg_at_k([3.0, 2.0, 1.0], 1) == pytest.approx(3.0)


def test_ndcg_perfect_ranking_is_one():
    gains = [1.0, 0.1, 0.01, 0.0]
    assert ndcg_at_k(gains, 10) == pytest.approx(1.0)


def test_ndcg_reversed_ranking_below_one():
    gains = [1.0, 0.1, 0.01, 0.0]
    assert ndcg_at_k(list(reversed(gains)), 10) < 1.0


def test_ndcg_all_zero_is_zero():
    assert ndcg_at_k([0.0, 0.0, 0.0], 10) == 0.0


def test_ndcg_is_order_sensitive():
    good = ndcg_at_k([1.0, 0.0, 0.1], 10)
    bad = ndcg_at_k([0.0, 0.1, 1.0], 10)
    assert good > bad


def test_mean_ndcg_averages_queries():
    q = [[1.0, 0.0], [0.0, 1.0]]
    assert 0.0 < mean_ndcg_at_k(q, 10) < 1.0


def test_recall_counts_hits_in_top_k():
    assert recall_at_k([1, 0, 1, 0, 1], num_relevant=3, k=3) == pytest.approx(2 / 3)


def test_recall_zero_when_no_relevant():
    assert recall_at_k([0, 0], num_relevant=0, k=2) == 0.0


def test_mrr_reciprocal_of_first_hit():
    assert mrr([0, 0, 1]) == pytest.approx(1 / 3)
    assert mrr([1, 0, 0]) == pytest.approx(1.0)
    assert mrr([0, 0, 0]) == 0.0


def test_micro_f1_perfect():
    assert micro_f1([0, 1, 2, 3], [0, 1, 2, 3], 4) == pytest.approx(1.0)


def test_micro_f1_matches_accuracy_single_label():
    # 3/4 correct -> micro-F1 equals accuracy = 0.75 for single-label multiclass.
    assert micro_f1([0, 1, 2, 3], [0, 1, 2, 0], 4) == pytest.approx(0.75)


def test_classification_report_structure():
    report = classification_report([0, 1, 2, 3, 0], [0, 1, 2, 3, 1], 4)
    assert set(report) == {"per_class", "micro_f1", "macro_f1", "confusion_matrix"}
    assert len(report["confusion_matrix"]) == 4
    assert report["per_class"][0]["support"] == 2
    assert 0.0 <= report["macro_f1"] <= 1.0
    assert not math.isnan(report["micro_f1"])
