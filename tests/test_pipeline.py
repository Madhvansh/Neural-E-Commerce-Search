"""Tests for the two-stage searcher orchestration.

The pipeline module itself is torch-free, so we drive it with lightweight fakes
that mimic the model/index interfaces. This verifies the orchestration logic
(candidate truncation, reranking order, label attachment) without loading any
heavyweight models.
"""

import numpy as np

from necs.pipeline.search import TwoStageSearcher
from necs.retrieval.index import SearchHit


class _FakeTensor:
    """Stands in for a torch tensor returned by encode_texts()."""

    def __init__(self, array):
        self._array = np.asarray(array, dtype=np.float32)

    def numpy(self):
        return self._array


class FakeBiEncoder:
    def encode_texts(self, texts, **_):
        # Return a deterministic unit vector per query.
        return _FakeTensor(np.ones((len(texts), 4), dtype=np.float32))


class FakeIndex:
    """Returns a fixed candidate list regardless of the query vector."""

    def __init__(self, hits):
        self._hits = hits

    def search(self, query_embeddings, top_k=100):
        return [self._hits[:top_k]]


class FakeCrossEncoder:
    """Scores by a lookup table so we can assert the reranking order."""

    def __init__(self, scores, labels):
        self._scores = scores
        self._labels = labels

    def score(self, query, products, **_):
        return np.asarray([self._scores[p] for p in products], dtype=np.float32)

    def predict_labels(self, query, products, **_):
        return np.asarray([self._labels[p] for p in products], dtype=np.int64)


def _make_searcher():
    hits = [SearchHit("p1", 0.9), SearchHit("p2", 0.8), SearchHit("p3", 0.7)]
    catalogue = {"p1": "alpha", "p2": "beta", "p3": "gamma"}
    # Reranker disagrees with retrieval: p3 is most relevant (Exact).
    scores = {"alpha": 0.1, "beta": 0.5, "gamma": 0.95}
    labels = {"alpha": 3, "beta": 1, "gamma": 0}  # I, S, E
    searcher = TwoStageSearcher(
        bi_encoder=FakeBiEncoder(),
        cross_encoder=FakeCrossEncoder(scores, labels),
        index=FakeIndex(hits),
        product_text=catalogue,
        retrieval_top_k=10,
        rerank_top_k=10,
    )
    return searcher


def test_reranker_reorders_candidates():
    results = _make_searcher().search("running shoes", top_k=3)
    # p3 (gamma) had the lowest retrieval score but highest rerank score.
    assert [r.product_id for r in results] == ["p3", "p2", "p1"]
    assert results[0].score == max(r.score for r in results)


def test_labels_are_attached_and_named():
    results = _make_searcher().search("running shoes", top_k=3)
    top = results[0]
    assert top.label == "E"
    assert top.label_name == "Exact"


def test_top_k_truncation():
    results = _make_searcher().search("running shoes", top_k=2)
    assert len(results) == 2


def test_empty_retrieval_returns_empty():
    searcher = TwoStageSearcher(
        bi_encoder=FakeBiEncoder(),
        cross_encoder=FakeCrossEncoder({}, {}),
        index=FakeIndex([]),
        product_text={},
    )
    assert searcher.search("anything") == []


def test_retrieval_rank_preserved():
    results = _make_searcher().search("running shoes", top_k=3)
    ranks = {r.product_id: r.retrieval_rank for r in results}
    # p1 was first out of retrieval, p3 was last.
    assert ranks["p1"] == 0 and ranks["p3"] == 2
