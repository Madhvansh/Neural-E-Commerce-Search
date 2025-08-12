"""Two-stage retrieve-and-rank search.

1. **Retrieve** — embed the query with the bi-encoder and pull the top-``N``
   candidates from the FAISS index (cheap, sub-linear).
2. **Rerank** — score each candidate with the DeBERTa cross-encoder and reorder
   by expected relevance, attaching the predicted ESCI label.

The searcher is deliberately model-agnostic: it depends only on a ``DenseIndex``
and the two model wrappers, so either stage can be swapped (e.g. BM25 first
stage) without touching the orchestration.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from necs import ESCI_LABELS, ESCI_LABEL_NAMES


@dataclass
class RankedResult:
    product_id: str
    product_text: str
    score: float
    label: str  # ESCI letter
    label_name: str
    retrieval_rank: int


class TwoStageSearcher:
    def __init__(
        self,
        bi_encoder,
        cross_encoder,
        index,
        product_text: dict[str, str],
        retrieval_top_k: int = 100,
        rerank_top_k: int = 100,
    ) -> None:
        self.bi_encoder = bi_encoder
        self.cross_encoder = cross_encoder
        self.index = index
        self.product_text = product_text
        self.retrieval_top_k = retrieval_top_k
        self.rerank_top_k = rerank_top_k

    def retrieve(self, query: str) -> list:
        """Stage 1: dense candidate retrieval."""
        q_emb = self.bi_encoder.encode_texts([query]).numpy().astype(np.float32)
        return self.index.search(q_emb, top_k=self.retrieval_top_k)[0]

    def search(self, query: str, top_k: int = 10) -> list[RankedResult]:
        """Run both stages and return the reranked top-``k`` results."""
        hits = self.retrieve(query)
        if not hits:
            return []
        hits = hits[: self.rerank_top_k]
        candidates = [self.product_text.get(h.product_id, "") for h in hits]

        scores = self.cross_encoder.score(query, candidates).tolist()
        labels = self.cross_encoder.predict_labels(query, candidates).tolist()

        results = [
            RankedResult(
                product_id=hit.product_id,
                product_text=text,
                score=float(score),
                label=ESCI_LABELS[label_idx],
                label_name=ESCI_LABEL_NAMES[ESCI_LABELS[label_idx]],
                retrieval_rank=rank,
            )
            for rank, (hit, text, score, label_idx) in enumerate(
                zip(hits, candidates, scores, labels)
            )
        ]
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]
