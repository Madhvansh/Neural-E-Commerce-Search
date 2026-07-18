"""Tests for hard-negative mining (pure-Python paths)."""

import sys
from types import ModuleType, SimpleNamespace

import numpy as np

from necs.data.esci import ESCIExample
from necs.data.hard_negatives import (
    _retrieve_rankings,
    build_positive_map,
    mine_from_rankings,
)


def _ex(qid, pid, label):
    return ESCIExample(
        query_id=qid,
        query=f"query {qid}",
        product_id=pid,
        product_text=f"product {pid}",
        label=label,
        split="train",
    )


def test_build_positive_map_collects_only_exact():
    examples = [_ex(1, "a", "E"), _ex(1, "b", "S"), _ex(1, "c", "E")]
    positives = build_positive_map(examples)
    assert positives[1] == {"a", "c"}


def test_mining_excludes_true_positives():
    examples = [_ex(1, "a", "E"), _ex(1, "b", "S"), _ex(1, "c", "I")]
    rankings = {1: ["a", "b", "c"]}  # retriever ranked the positive 'a' first
    mined = mine_from_rankings(rankings, examples, num_negatives=5)
    texts = mined[1]
    assert "product a" not in texts  # positive never used as a negative
    assert "product b" in texts and "product c" in texts


def test_mining_respects_num_negatives_cap():
    examples = [_ex(1, "a", "E")] + [_ex(1, f"n{i}", "S") for i in range(10)]
    rankings = {1: ["a"] + [f"n{i}" for i in range(10)]}
    mined = mine_from_rankings(rankings, examples, num_negatives=3)
    assert len(mined[1]) == 3


def test_mining_skips_queries_without_candidates():
    examples = [_ex(1, "a", "E")]
    rankings = {1: ["a"]}  # only the positive is retrieved -> nothing to mine
    mined = mine_from_rankings(rankings, examples, num_negatives=4)
    assert 1 not in mined


def test_mining_ignores_products_not_judged_negative_for_that_query():
    examples = [
        _ex(1, "a", "E"),
        _ex(1, "b", "S"),
        _ex(2, "c", "E"),
    ]
    rankings = {1: ["a", "c", "b"]}
    mined = mine_from_rankings(rankings, examples, num_negatives=4)
    assert mined[1] == ["product b"]


def test_retrieval_uses_requested_warm_checkpoint(monkeypatch):
    loaded_sources = []

    class FakeTensor:
        def __init__(self, values):
            self.values = np.asarray(values, dtype=np.float32)

        def numpy(self):
            return self.values

    class FakeBiEncoder:
        def __init__(self, source, pooling, normalize):
            loaded_sources.append((source, pooling, normalize))

        def encode_texts(self, texts):
            return FakeTensor(np.ones((len(texts), 2), dtype=np.float32))

    class FakeDenseIndex:
        def __init__(self, dim):
            assert dim == 2
            self.product_ids = []

        def add(self, product_ids, embeddings):
            self.product_ids = list(product_ids)

        def search(self, query_embeddings, top_k):
            hits = [
                SimpleNamespace(product_id=product_id)
                for product_id in self.product_ids[:top_k]
            ]
            return [hits for _ in range(len(query_embeddings))]

    models_package = ModuleType("necs.models")
    models_package.__path__ = []
    bi_encoder_module = ModuleType("necs.models.bi_encoder")
    bi_encoder_module.BiEncoder = FakeBiEncoder
    retrieval_package = ModuleType("necs.retrieval")
    retrieval_package.__path__ = []
    index_module = ModuleType("necs.retrieval.index")
    index_module.DenseIndex = FakeDenseIndex

    monkeypatch.setitem(sys.modules, "necs.models", models_package)
    monkeypatch.setitem(sys.modules, "necs.models.bi_encoder", bi_encoder_module)
    monkeypatch.setitem(sys.modules, "necs.retrieval", retrieval_package)
    monkeypatch.setitem(sys.modules, "necs.retrieval.index", index_module)

    class BiEncoderConfig:
        model_name = "base-model"
        pooling = "mean"
        normalize = True

    class Config:
        bi_encoder = BiEncoderConfig()

    examples = [_ex(1, "a", "E"), _ex(1, "b", "S")]
    rankings = _retrieve_rankings(
        Config(),
        examples,
        top_k=2,
        retriever_checkpoint="artifacts/bi_encoder_warm",
    )

    assert loaded_sources == [("artifacts/bi_encoder_warm", "mean", True)]
    assert rankings[1] == ["a", "b"]
