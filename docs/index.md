---
title: Neural E-Commerce Search
---

# Neural E-Commerce Search

**Two-stage retrieve-and-rank neural product search on the Amazon ESCI
Shopping Queries dataset.**

Given a shopping query, the system retrieves products from a large catalogue and
reranks them, classifying every result on the **ESCI** taxonomy —
**E**xact / **S**ubstitute / **C**omplement / **I**rrelevant. A dense
**bi-encoder** does cheap candidate retrieval; a **DeBERTa cross-encoder** does
precise reranking and 4-way classification.

```
 query ─▶ bi-encoder ─▶ FAISS top-100 ─▶ DeBERTa cross-encoder ─▶ ranked + labelled results
        (retrieve, cheap)                 (rerank, precise)
```

## Results

| System                                   | NDCG@10 | Recall@100 | micro-F1 |
|------------------------------------------|:-------:|:----------:|:--------:|
| BM25 (lexical baseline)                  |  0.61   |    0.82    |    —     |
| Dense bi-encoder only                    |  0.66   |    0.89    |    —     |
| **Two-stage (dense + DeBERTa)**          | **0.71**|  **0.89**  | **0.74** |

**NDCG@10 = 0.71 (+16% over BM25), micro-F1 = 0.74.** The largest gains land on
Substitute-vs-Complement queries that lexical matching cannot resolve.

## Documentation

- [Architecture](architecture.md) — two-stage design, module map, rationale
- [Data](data.md) — ESCI taxonomy, files, preprocessing
- [Training](training.md) — step-by-step training and hyper-parameters
- [Experiments](experiments.md) — results, ablations, confusion matrix
- [Deployment](deployment.md) — serving, Docker, API reference, scaling

## Links

- **Source code:** [github.com/Madhvansh/Neural-E-Commerce-Search](https://github.com/Madhvansh/Neural-E-Commerce-Search)
- **Latest release:** [releases](https://github.com/Madhvansh/Neural-E-Commerce-Search/releases)

---

<sub>MIT licensed. Built on the
[Amazon ESCI benchmark](https://github.com/amazon-science/esci-data)
(Reddy et al., 2022).</sub>
