"""Dense bi-encoder retriever.

A single shared transformer encodes queries and product passages into a common
embedding space; relevance is the dot product (cosine when normalized). Sharing
weights keeps the index and the query encoder consistent and halves the
parameter count versus a two-tower design.
"""

from __future__ import annotations

import torch
import torch.nn as nn

from necs.models.pooling import pool


class BiEncoder(nn.Module):
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        pooling: str = "mean",
        normalize: bool = True,
    ) -> None:
        super().__init__()
        from transformers import AutoModel, AutoTokenizer

        self.encoder = AutoModel.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.pooling = pooling
        self.normalize = normalize

    @property
    def embedding_dim(self) -> int:
        return int(self.encoder.config.hidden_size)

    def encode(self, batch: dict) -> torch.Tensor:
        """Encode a tokenized batch into pooled (optionally normalized) vectors."""
        outputs = self.encoder(**batch)
        emb = pool(self.pooling, outputs.last_hidden_state, batch["attention_mask"])
        if self.normalize:
            emb = torch.nn.functional.normalize(emb, p=2, dim=-1)
        return emb

    def forward(self, query: dict, doc: dict) -> tuple[torch.Tensor, torch.Tensor]:
        return self.encode(query), self.encode(doc)

    @torch.no_grad()
    def encode_texts(
        self,
        texts: list[str],
        batch_size: int = 64,
        max_seq_len: int = 128,
        device: str | None = None,
    ) -> torch.Tensor:
        """Convenience helper to embed raw strings (used for indexing)."""
        device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.eval()
        self.to(device)
        chunks: list[torch.Tensor] = []
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            enc = self.tokenizer(
                batch, truncation=True, max_length=max_seq_len,
                padding=True, return_tensors="pt",
            ).to(device)
            chunks.append(self.encode(enc).cpu())
        return torch.cat(chunks, dim=0) if chunks else torch.empty(0, self.embedding_dim)

    def save(self, path: str) -> None:
        self.encoder.save_pretrained(path)
        self.tokenizer.save_pretrained(path)
