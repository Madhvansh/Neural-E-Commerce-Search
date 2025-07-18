"""Dense vector index over product embeddings (FAISS).

Embeddings are L2-normalized, so inner-product search (``IndexFlatIP``) is
equivalent to cosine similarity. For larger catalogues swap in an IVF/HNSW
index; the public API here stays the same.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class SearchHit:
    product_id: str
    score: float


class DenseIndex:
    """Thin wrapper around a FAISS inner-product index keyed by product id."""

    def __init__(self, dim: int):
        import faiss

        self.dim = dim
        self._index = faiss.IndexFlatIP(dim)
        self.product_ids: list[str] = []

    def add(self, product_ids: list[str], embeddings: np.ndarray) -> None:
        if embeddings.shape[1] != self.dim:
            raise ValueError(f"Expected dim {self.dim}, got {embeddings.shape[1]}")
        if len(product_ids) != embeddings.shape[0]:
            raise ValueError("product_ids and embeddings length mismatch")
        self._index.add(np.ascontiguousarray(embeddings, dtype=np.float32))
        self.product_ids.extend(product_ids)

    def search(self, query_embeddings: np.ndarray, top_k: int = 100) -> list[list[SearchHit]]:
        """Return the top-``k`` hits for each query embedding."""
        q = np.ascontiguousarray(query_embeddings, dtype=np.float32)
        if q.ndim == 1:
            q = q[None, :]
        scores, idx = self._index.search(q, top_k)
        results: list[list[SearchHit]] = []
        for row_scores, row_idx in zip(scores, idx):
            hits = [
                SearchHit(self.product_ids[i], float(s))
                for s, i in zip(row_scores, row_idx)
                if i != -1
            ]
            results.append(hits)
        return results

    def __len__(self) -> int:
        return self._index.ntotal

    def save(self, path: str | Path) -> None:
        import faiss

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(path.with_suffix(".faiss")))
        path.with_suffix(".ids").write_text("\n".join(self.product_ids))

    @classmethod
    def load(cls, path: str | Path) -> DenseIndex:
        import faiss

        path = Path(path)
        index = faiss.read_index(str(path.with_suffix(".faiss")))
        obj = cls.__new__(cls)
        obj._index = index
        obj.dim = index.d
        obj.product_ids = path.with_suffix(".ids").read_text().splitlines()
        return obj
