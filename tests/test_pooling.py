"""Tests for pooling strategies (require torch)."""

import pytest

torch = pytest.importorskip("torch")

from necs.models.pooling import cls_pool, mean_pool, pool  # noqa: E402


def test_mean_pool_ignores_padding():
    # Two tokens of value 2.0 and one padded token of value 100.0.
    emb = torch.tensor([[[2.0, 2.0], [2.0, 2.0], [100.0, 100.0]]])
    mask = torch.tensor([[1, 1, 0]])
    out = mean_pool(emb, mask)
    assert torch.allclose(out, torch.tensor([[2.0, 2.0]]))


def test_mean_pool_handles_all_padding_without_nan():
    emb = torch.ones(1, 3, 2)
    mask = torch.zeros(1, 3)
    out = mean_pool(emb, mask)
    assert not torch.isnan(out).any()


def test_cls_pool_takes_first_token():
    emb = torch.tensor([[[1.0, 1.0], [9.0, 9.0]]])
    assert torch.allclose(cls_pool(emb), torch.tensor([[1.0, 1.0]]))


def test_pool_dispatch_and_unknown():
    emb = torch.ones(1, 2, 2)
    mask = torch.ones(1, 2)
    assert torch.allclose(pool("mean", emb, mask), pool("mean", emb, mask))
    with pytest.raises(ValueError):
        pool("unknown", emb, mask)
