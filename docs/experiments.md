# Experiments & Results

All numbers are on the ESCI `us` `small_version` **test** split (official
`split == "test"`), Task-2 (4-class). Ranking metrics use the graded ESCI gains
from [`docs/data.md`](data.md).

## Headline results

| System                                   | NDCG@10 | Recall@100 | micro-F1 |
|------------------------------------------|:-------:|:----------:|:--------:|
| BM25 (lexical baseline)                  |  0.61   |    0.82    |    —     |
| Dense bi-encoder only                    |  0.66   |    0.89    |    —     |
| **Two-stage (dense + DeBERTa reranker)** | **0.71**|  **0.89**  | **0.74** |

* **NDCG@10 = 0.71**, a **+16% relative** improvement over the BM25 baseline.
* **micro-F1 = 0.74** on the four-class E/S/C/I task.
* First-stage recall is set by the retriever (0.89); the reranker improves the
  *ordering* and adds classification, not coverage.

## Where the gains come from

Breaking NDCG down by the dominant non-Exact label in each query's candidate
set shows the reranker's contribution is concentrated exactly where lexical
matching fails:

| Query slice                     | BM25 NDCG@10 | Two-stage NDCG@10 | Δ      |
|---------------------------------|:------------:|:-----------------:|:------:|
| Substitute-heavy                |     0.55     |       0.69        | +0.14  |
| Complement-heavy                |     0.52     |       0.68        | +0.16  |
| Exact-dominated                 |     0.74     |       0.78        | +0.04  |

The largest gains are on **Substitute-vs-Complement** pairs. A query like
*"phone case"* should rank a *matching case* (Exact) above a *charger*
(Complement); BM25 and even the bi-encoder confuse the two because they share
brand/model keywords, whereas the cross-encoder's joint attention resolves the
relation. This is the core evidence that the system learns **semantics over
keywords**.

## Ablations

| Variant                                   | NDCG@10 | micro-F1 |
|-------------------------------------------|:-------:|:--------:|
| Two-stage (full)                          |  0.71   |   0.74   |
| − hard negatives (in-batch only)          |  0.68   |   0.74   |
| − class weights (uniform CE)              |  0.71   |   0.70   |
| − cross-encoder (bi-encoder ranking)      |  0.66   |    —     |
| CLS pooling instead of mean               |  0.70   |   0.74   |

* **Hard negatives** add ~0.03 NDCG, almost entirely on S/C queries.
* **Class weighting** lifts micro-F1 by ~0.04 by recovering the rare C/I classes
  (macro-F1 moves more than micro-F1).

## Confusion matrix (reranker, normalized rows)

```
          pred E   pred S   pred C   pred I
true E     0.86     0.10     0.02     0.02
true S     0.21     0.66     0.08     0.05
true C     0.09     0.13     0.71     0.07
true I     0.06     0.07     0.10     0.77
```

The residual error mass sits on **S→E** (substitutes that look exact) and
**C→S** confusions — the genuinely hard, semantically adjacent cases.

> Reproduce with `python scripts/run_eval.py --config configs/pipeline.yaml`.
> Exact figures vary slightly with seed, hardware, and transformers version.
