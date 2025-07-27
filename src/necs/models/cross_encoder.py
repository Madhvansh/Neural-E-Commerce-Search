"""DeBERTa cross-encoder reranker.

Stage 2 jointly encodes ``[CLS] query [SEP] product [SEP]`` and predicts the
4-way ESCI label (Exact / Substitute / Complement / Irrelevant). Because the two
texts attend to each other, the cross-encoder resolves fine-grained distinctions
— notably Substitute vs Complement — that a bi-encoder's separate embeddings
cannot. We reuse the softmax distribution two ways: as a class prediction and,
via an expected-relevance score, as the reranking key.
"""

from __future__ import annotations

import torch
import torch.nn as nn

# Expected-relevance weights over (E, S, C, I); used to turn the class
# distribution into a single scalar ranking score.
_RELEVANCE_WEIGHTS = torch.tensor([1.0, 0.1, 0.01, 0.0])


class CrossEncoder(nn.Module):
    def __init__(
        self,
        model_name: str = "microsoft/deberta-v3-base",
        num_labels: int = 4,
    ) -> None:
        super().__init__()
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_name, num_labels=num_labels
        )
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.num_labels = num_labels
        self.register_buffer("relevance_weights", _RELEVANCE_WEIGHTS[:num_labels])

    def forward(self, **inputs) -> torch.Tensor:
        labels = inputs.pop("labels", None)  # loss handled by the trainer
        return self.model(**inputs).logits

    @torch.no_grad()
    def score(
        self,
        query: str,
        products: list[str],
        max_seq_len: int = 192,
        batch_size: int = 32,
        device: str | None = None,
    ) -> torch.Tensor:
        """Expected-relevance score for each (query, product) pair.

        ``score = Σ_c P(class=c) · relevance_weight[c]`` — higher means more
        relevant, monotonically ordering E > S > C > I.
        """
        device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.eval()
        self.to(device)
        scores: list[torch.Tensor] = []
        for start in range(0, len(products), batch_size):
            chunk = products[start : start + batch_size]
            enc = self.tokenizer(
                [query] * len(chunk), chunk,
                truncation=True, max_length=max_seq_len,
                padding=True, return_tensors="pt",
            ).to(device)
            probs = torch.softmax(self.model(**enc).logits, dim=-1)
            scores.append((probs * self.relevance_weights.to(device)).sum(dim=-1).cpu())
        return torch.cat(scores) if scores else torch.empty(0)

    @torch.no_grad()
    def predict_labels(self, query: str, products: list[str], **kw) -> torch.Tensor:
        """Return the arg-max ESCI class index for each pair."""
        device = kw.get("device") or ("cuda" if torch.cuda.is_available() else "cpu")
        self.eval()
        self.to(device)
        enc = self.tokenizer(
            [query] * len(products), products,
            truncation=True, max_length=kw.get("max_seq_len", 192),
            padding=True, return_tensors="pt",
        ).to(device)
        return self.model(**enc).logits.argmax(dim=-1).cpu()

    def save(self, path: str) -> None:
        self.model.save_pretrained(path)
        self.tokenizer.save_pretrained(path)
