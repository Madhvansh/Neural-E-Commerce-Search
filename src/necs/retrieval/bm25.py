"""BM25 lexical baseline.

A first-stage keyword retriever used as the reference point for the dense
retriever and the full pipeline. Wraps ``rank_bm25`` with a tiny tokenizer so
the rest of the codebase can treat it interchangeably with :class:`DenseIndex`.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from necs.retrieval.index import SearchHit

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


class BM25Index:
    def __init__(self, product_ids: Sequence[str], texts: Sequence[str]):
        from rank_bm25 import BM25Okapi

        if len(product_ids) != len(texts):
            raise ValueError("product_ids and texts length mismatch")
        self.product_ids = list(product_ids)
        self._bm25 = BM25Okapi([tokenize(t) for t in texts])

    def search(self, query: str, top_k: int = 100) -> list[SearchHit]:
        scores = self._bm25.get_scores(tokenize(query))
        # Top-k by score, descending.
        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [SearchHit(self.product_ids[i], float(scores[i])) for i in order]
