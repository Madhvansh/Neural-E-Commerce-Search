"""Pooling strategies that turn token embeddings into a single vector."""

from __future__ import annotations

import torch


def mean_pool(token_embeddings: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
    """Attention-masked mean over the sequence dimension.

    Parameters
    ----------
    token_embeddings:
        ``(batch, seq_len, hidden)`` last hidden states.
    attention_mask:
        ``(batch, seq_len)`` 1 for real tokens, 0 for padding.
    """
    mask = attention_mask.unsqueeze(-1).to(token_embeddings.dtype)
    summed = (token_embeddings * mask).sum(dim=1)
    counts = mask.sum(dim=1).clamp(min=1e-9)
    return summed / counts


def cls_pool(token_embeddings: torch.Tensor) -> torch.Tensor:
    """Take the first ([CLS]) token embedding."""
    return token_embeddings[:, 0]


def pool(strategy: str, token_embeddings: torch.Tensor, attention_mask: torch.Tensor):
    if strategy == "mean":
        return mean_pool(token_embeddings, attention_mask)
    if strategy == "cls":
        return cls_pool(token_embeddings)
    raise ValueError(f"Unknown pooling strategy: {strategy!r}")
