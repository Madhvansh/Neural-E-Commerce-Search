"""Regression tests for retrieve-before-rerank evaluation."""

import numpy as np
from scripts.run_eval import _pipeline_rankings

from necs.data.esci import ESCIExample


class _FakeTensor:
    def __init__(self, values):
        self.values = np.asarray(values, dtype=np.float32)

    def numpy(self):
        return self.values


class _Retriever:
    def __init__(self):
        self.calls = []

    def encode_texts(self, texts):
        self.calls.append(list(texts))
        if len(texts) == 1 and texts[0] == "gaming mouse":
            return _FakeTensor([[1.0, 0.0]])
        return _FakeTensor(
            [
                [0.9, 0.0],
                [0.1, 0.0],
                [0.8, 0.0],
            ]
        )


class _Reranker:
    def __init__(self):
        self.seen_products = []

    def score(self, query, products):
        assert query == "gaming mouse"
        self.seen_products = list(products)
        scores = {"alpha": 0.2, "gamma": 0.9}
        return _FakeTensor([scores[product] for product in products])


def _example(product_id, text):
    return ESCIExample(
        query_id=1,
        query="gaming mouse",
        product_id=product_id,
        product_text=text,
        label="E" if product_id == "p3" else "I",
        split="test",
    )


def test_retriever_filters_candidates_before_reranking():
    grouped = {
        1: [
            _example("p1", "alpha"),
            _example("p2", "beta"),
            _example("p3", "gamma"),
        ]
    }
    retriever = _Retriever()
    reranker = _Reranker()

    rankings = _pipeline_rankings(
        grouped,
        retriever,
        reranker,
        retrieval_top_k=2,
        rerank_top_k=2,
    )

    assert len(retriever.calls) == 2
    assert reranker.seen_products == ["alpha", "gamma"]
    assert "beta" not in reranker.seen_products
    assert rankings[1] == ["p3", "p1"]


def test_nonretrieved_product_cannot_return_via_reranker():
    grouped = {
        1: [
            _example("p1", "alpha"),
            _example("p2", "beta"),
            _example("p3", "gamma"),
        ]
    }
    rankings = _pipeline_rankings(
        grouped,
        _Retriever(),
        _Reranker(),
        retrieval_top_k=2,
        rerank_top_k=3,
    )
    assert "p2" not in rankings[1]
