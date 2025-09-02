"""Tests for dataset construction (require torch)."""

import pytest

pytest.importorskip("torch")

from necs.data.datasets import (  # noqa: E402
    BiEncoderDataset,
    RetrieverTriple,
    class_distribution,
)
from necs.data.esci import ESCIExample  # noqa: E402


def _ex(qid, pid, label):
    return ESCIExample(qid, f"q{qid}", pid, f"text {pid}", label, "train")


def test_bi_encoder_dataset_builds_positive_triples():
    examples = [_ex(1, "a", "E"), _ex(1, "b", "S"), _ex(2, "c", "E")]
    ds = BiEncoderDataset(examples)
    # Two Exact positives -> two triples.
    assert len(ds) == 2
    item = ds[0]
    assert isinstance(item, RetrieverTriple)
    assert item.positive.startswith("text")


def test_bi_encoder_dataset_attaches_hard_negatives():
    examples = [_ex(1, "a", "E")]
    negatives = {1: ["neg1", "neg2", "neg3"]}
    ds = BiEncoderDataset(examples, hard_negatives=negatives, num_hard_negatives=2)
    item = ds[0]
    assert item.hard_negatives == ["neg1", "neg2"]


def test_bi_encoder_dataset_skips_queries_without_positives():
    examples = [_ex(1, "a", "S"), _ex(1, "b", "I")]
    ds = BiEncoderDataset(examples)
    assert len(ds) == 0


def test_class_distribution_counts_labels():
    examples = [_ex(1, "a", "E"), _ex(1, "b", "E"), _ex(2, "c", "S")]
    dist = class_distribution(examples)
    assert dist["E"] == 2 and dist["S"] == 1
