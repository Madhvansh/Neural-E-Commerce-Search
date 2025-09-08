# Architecture

Neural E-Commerce Search is a **two-stage retrieve-and-rank** system. The two
stages trade off cost against precision: a cheap dense retriever narrows the
catalogue to a few hundred candidates, then an expensive cross-encoder reranks
only those.

```
                 query
                   │
        ┌──────────▼───────────┐
        │  Stage 1: Retriever  │   bi-encoder  (shared MiniLM encoder)
        │  dense FAISS search  │   embed query → top-N via cosine
        └──────────┬───────────┘
                   │  N≈100 candidate products
        ┌──────────▼───────────┐
        │  Stage 2: Reranker   │   cross-encoder (DeBERTa-v3-base)
        │  joint query×product │   4-way ESCI head → expected relevance
        └──────────┬───────────┘
                   │  reordered top-k + ESCI label
                   ▼
              ranked results
```

## Stage 1 — Bi-encoder retriever

* A single shared transformer (`all-MiniLM-L6-v2` by default) encodes both the
  query and each product passage into a 384-d space. Sharing weights keeps the
  query encoder and the index consistent and halves parameters versus a
  two-tower design.
* Embeddings are **L2-normalized**, so inner-product search over a FAISS
  `IndexFlatIP` is exactly cosine similarity.
* Training uses a temperature-scaled **InfoNCE** loss with in-batch negatives,
  then a second pass with **mined hard negatives** (see
  [`docs/training.md`](training.md)).
* Product passages are built by concatenating `title · brand · color · bullets ·
  description`, truncated to a fixed budget (`build_product_text`).

## Stage 2 — Cross-encoder reranker

* `microsoft/deberta-v3-base` encodes `[CLS] query [SEP] product [SEP]` jointly,
  so the two texts attend to each other. This cross-attention is what lets the
  model separate **Substitute** from **Complement** — a distinction lexical
  overlap and independent embeddings cannot make.
* A 4-way classification head predicts the ESCI label. The softmax distribution
  is reused two ways:
  * **prediction** — arg-max class → `E / S / C / I`,
  * **ranking score** — expected relevance `Σ_c P(c)·w_c` with
    `w = (1.0, 0.1, 0.01, 0.0)`, which orders results E > S > C > I.
* Class-weighted cross-entropy counteracts the heavy Exact-label skew.

## Why two stages?

A cross-encoder over the full catalogue is `O(queries × products)` forward
passes — infeasible online. A bi-encoder is `O(products)` once (offline
indexing) plus one query embedding at serve time, but it cannot model
query×product interactions. Combining them recovers most of the cross-encoder's
quality at a fraction of the cost.

## Module map

| Concern              | Module                                  |
|----------------------|-----------------------------------------|
| Config               | `necs.config`                           |
| ESCI loading         | `necs.data.esci`, `necs.data.preprocess`|
| Datasets / collators | `necs.data.datasets`                    |
| Hard-negative mining | `necs.data.hard_negatives`              |
| Models               | `necs.models.bi_encoder` / `cross_encoder` |
| Losses               | `necs.training.losses`                  |
| Training             | `necs.training.train_bi_encoder` / `train_cross_encoder` |
| Retrieval            | `necs.retrieval.index` (FAISS), `necs.retrieval.bm25` |
| Metrics / eval       | `necs.eval.metrics`, `necs.eval.evaluate` |
| Pipeline             | `necs.pipeline.search`                  |
| Serving              | `necs.api.app`                          |
