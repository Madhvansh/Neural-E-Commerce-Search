"""Tests for hard-negative mining (pure-Python paths)."""

from necs.data.esci import ESCIExample
from necs.data.hard_negatives import build_positive_map, mine_from_rankings


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
