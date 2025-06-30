"""PyTorch datasets and collators for the two training stages.

* :class:`BiEncoderDataset` yields (query, positive product, [hard negatives])
  triples consumed with an in-batch + hard-negative contrastive objective.
* :class:`CrossEncoderDataset` yields tokenized (query, product) pairs with a
  4-way ESCI label for the reranker.

Tokenization is delegated to a Hugging Face tokenizer supplied by the caller,
so these classes carry no model-specific assumptions.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

import torch
from torch.utils.data import Dataset

from necs.data.esci import ESCIExample
from necs.data.preprocess import label_to_index

# Only Exact (and optionally Substitute) judgements are treated as positives
# for the retriever; the rest are candidates for negatives.
_POSITIVE_LABELS = {"E"}


@dataclass
class RetrieverTriple:
    query: str
    positive: str
    hard_negatives: list[str]


class BiEncoderDataset(Dataset):
    """Builds query→positive(+hard-negative) triples for the retriever."""

    def __init__(
        self,
        examples: Sequence[ESCIExample],
        hard_negatives: dict[int, list[str]] | None = None,
        num_hard_negatives: int = 4,
    ) -> None:
        self.num_hard_negatives = num_hard_negatives
        self.hard_negatives = hard_negatives or {}

        # Group positives by query so every training row has a genuine match.
        by_query: dict[int, dict] = {}
        for ex in examples:
            slot = by_query.setdefault(ex.query_id, {"query": ex.query, "pos": []})
            if ex.label in _POSITIVE_LABELS:
                slot["pos"].append(ex.product_text)
        self.triples: list[tuple[int, str, str]] = [
            (qid, slot["query"], pos)
            for qid, slot in by_query.items()
            for pos in slot["pos"]
        ]

    def __len__(self) -> int:
        return len(self.triples)

    def __getitem__(self, idx: int) -> RetrieverTriple:
        qid, query, positive = self.triples[idx]
        negs = self.hard_negatives.get(qid, [])[: self.num_hard_negatives]
        return RetrieverTriple(query=query, positive=positive, hard_negatives=negs)


class CrossEncoderDataset(Dataset):
    """Tokenized (query, product) pairs with ESCI class labels."""

    def __init__(
        self,
        examples: Sequence[ESCIExample],
        tokenizer,
        max_seq_len: int = 192,
    ) -> None:
        self.examples = list(examples)
        self.tokenizer = tokenizer
        self.max_seq_len = max_seq_len

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, idx: int) -> dict:
        ex = self.examples[idx]
        enc = self.tokenizer(
            ex.query,
            ex.product_text,
            truncation=True,
            max_length=self.max_seq_len,
            padding=False,
        )
        enc["labels"] = label_to_index(ex.label)
        return enc


def make_retriever_collate(tokenizer, max_seq_len: int = 128):
    """Collate triples into padded query/document tensor batches.

    Returns a dict with ``query`` and ``doc`` token batches. Documents are laid
    out as ``[positives | flattened hard-negatives]`` so the loss can build the
    similarity matrix without extra bookkeeping.
    """

    def collate(batch: list[RetrieverTriple]) -> dict:
        queries = [b.query for b in batch]
        docs = [b.positive for b in batch]
        for b in batch:
            docs.extend(b.hard_negatives)

        q = tokenizer(
            queries, truncation=True, max_length=max_seq_len, padding=True,
            return_tensors="pt",
        )
        d = tokenizer(
            docs, truncation=True, max_length=max_seq_len, padding=True,
            return_tensors="pt",
        )
        return {"query": q, "doc": d, "num_queries": len(queries)}

    return collate


def make_cross_encoder_collate(tokenizer):
    """Pad a batch of cross-encoder features (dynamic padding)."""

    def collate(batch: list[dict]) -> dict:
        labels = torch.tensor([b.pop("labels") for b in batch], dtype=torch.long)
        padded = tokenizer.pad(batch, padding=True, return_tensors="pt")
        padded["labels"] = labels
        return padded

    return collate


def class_distribution(examples: Sequence[ESCIExample]) -> dict[str, int]:
    """Count ESCI labels — handy for sanity checks and weighting."""
    counts: dict[str, int] = defaultdict(int)
    for ex in examples:
        counts[ex.label] += 1
    return dict(counts)
