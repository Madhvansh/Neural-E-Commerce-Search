"""Contrastive objectives for the bi-encoder retriever.

The retriever is trained with a temperature-scaled InfoNCE loss where, for each
query, the positive document is contrasted against (a) every other document in
the batch (in-batch negatives) and (b) any mined hard negatives appended to the
document pool. Documents are laid out as ``[positives | hard-negatives]`` so the
target for query ``i`` is simply column ``i``.
"""

from __future__ import annotations

import torch
import torch.nn.functional as F


def info_nce_loss(
    query_emb: torch.Tensor,
    doc_emb: torch.Tensor,
    temperature: float = 0.05,
) -> torch.Tensor:
    """Multiple-negatives ranking (InfoNCE) loss.

    Parameters
    ----------
    query_emb:
        ``(B, d)`` query embeddings.
    doc_emb:
        ``(B + H, d)`` document embeddings, where the first ``B`` rows are the
        positives aligned with the queries and the remaining ``H`` rows are
        shared hard negatives.
    temperature:
        Softmax temperature; lower values sharpen the distribution.
    """
    if doc_emb.size(0) < query_emb.size(0):
        raise ValueError("Need at least one document per query")
    scores = (query_emb @ doc_emb.t()) / temperature  # (B, B + H)
    targets = torch.arange(query_emb.size(0), device=query_emb.device)
    return F.cross_entropy(scores, targets)


def weighted_cross_entropy(
    logits: torch.Tensor,
    labels: torch.Tensor,
    class_weights: torch.Tensor | None = None,
) -> torch.Tensor:
    """Class-weighted cross-entropy for the 4-way ESCI reranker head."""
    return F.cross_entropy(logits, labels, weight=class_weights)
