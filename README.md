# Neural E-Commerce Search

**Two-stage retrieve-and-rank neural product search on the Amazon ESCI
Shopping Queries dataset.**

[![CI](https://github.com/Madhvansh/Neural-E-Commerce-Search/actions/workflows/ci.yml/badge.svg)](https://github.com/Madhvansh/Neural-E-Commerce-Search/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/lint-ruff-261230.svg)](https://github.com/astral-sh/ruff)

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

On the ESCI `us` `small_version` test split (Task-2, 4-class):

| System                                   | NDCG@10 | Recall@100 | micro-F1 |
|------------------------------------------|:-------:|:----------:|:--------:|
| BM25 (lexical baseline)                  |  0.61   |    0.82    |    —     |
| Dense bi-encoder only                    |  0.66   |    0.89    |    —     |
| **Two-stage (dense + DeBERTa)**          | **0.71**|  **0.89**  | **0.74** |

* **NDCG@10 = 0.71 — a +16% relative gain over BM25.**
* **micro-F1 = 0.74** on the four-class task.
* The biggest gains land on **Substitute-vs-Complement** queries that lexical
  matching cannot resolve — evidence the model ranks on *semantics, not
  keywords*. See [`docs/experiments.md`](docs/experiments.md) for the per-slice
  breakdown, ablations, and confusion matrix.

## Why two stages?

A cross-encoder scoring every product per query is `O(queries × products)` — far
too expensive online. A bi-encoder is sub-linear at query time but can't model
query×product interactions. The pipeline gets the best of both: the bi-encoder
narrows millions of products to ~100 candidates, then the cross-encoder applies
full joint attention only to those. Details in
[`docs/architecture.md`](docs/architecture.md).

## Features

**Current**

- 🔍 **Dense bi-encoder retriever** — shared transformer encoder, mean/CLS
  pooling, cosine retrieval over a FAISS inner-product index.
- ⛏️ **Hard-negative mining** — mines highly-ranked non-Exact products from the
  warmed-up retriever and fine-tunes against them (InfoNCE).
- 🧠 **DeBERTa cross-encoder reranker** — joint `query×product` encoding with a
  4-class ESCI head; reuses the softmax as both a label and an expected-relevance
  ranking score.
- ⚖️ **Class-weighted training** — counteracts the heavy Exact-label skew.
- 📊 **Evaluation harness** — NDCG@10, Recall@100, micro/macro-F1, per-class
  report and confusion matrix, with a **BM25 baseline** for comparison.
- 🚀 **FastAPI serving** — `/search` + `/health`, Swagger docs, graceful degraded
  startup when artifacts are absent.
- 🐳 **Docker + compose** packaging with health checks.
- ✅ **Test suite + CI** — 35+ tests, ruff lint, GitHub Actions on 3.9 & 3.11.
- ♻️ **Reproducible** — YAML configs, global seeding, mixed precision.

**Extended**

- 🔁 **Two-pass retriever training** (in-batch → mined hard negatives) wired into
  a single script (`scripts/train_retriever.sh`).
- 🧩 **Pluggable first stage** — BM25 and dense index share a `search` interface,
  so the pipeline can run hybrid or lexical-only without code changes.
- 🌐 **Multi-locale loader** — `us` / `es` / `jp`, GitHub or Hugging Face source.
- 📈 **Graded-relevance NDCG** using ESCI gains `(E=1.0, S=0.1, C=0.01, I=0.0)`.
- 📓 **Demo notebook** (`notebooks/demo.ipynb`) exercising metrics, live search,
  and the HTTP API.

## Quickstart

```bash
# 1. Install
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # or: make install-dev

# 2. Get the data
python scripts/download_esci.py --locale us --out data/raw   # or: make data

# 3. Train both stages
bash scripts/train_retriever.sh          # in-batch -> mine -> fine-tune
bash scripts/train_reranker.sh           # DeBERTa reranker
python scripts/build_index.py            # embed catalogue -> FAISS

# 4. Evaluate (prints two-stage vs BM25)
python scripts/run_eval.py --config configs/pipeline.yaml

# 5. Serve
make serve                               # http://localhost:8000/docs
```

Query the running service:

```bash
curl -s localhost:8000/search \
  -H 'content-type: application/json' \
  -d '{"query":"wireless gaming mouse","top_k":5}' | jq
```

## Project structure

```
src/necs/
├── config.py            # YAML → dataclass config + overrides
├── data/                # ESCI loader, preprocessing, datasets, hard negatives
├── models/              # bi_encoder, cross_encoder, pooling
├── training/            # losses + train_bi_encoder / train_cross_encoder
├── retrieval/           # FAISS dense index + BM25 baseline
├── eval/                # metrics + end-to-end evaluation harness
├── pipeline/            # two-stage searcher
└── api/                 # FastAPI app + schemas
configs/                 # bi_encoder / cross_encoder / pipeline YAML
scripts/                 # download, train, build_index, run_eval
tests/                   # pytest suite (torch-optional)
docs/                    # architecture, data, training, experiments, deployment
notebooks/               # demo.ipynb
```

## Documentation

| Doc                                        | Contents                                   |
|--------------------------------------------|--------------------------------------------|
| [architecture.md](docs/architecture.md)    | Two-stage design, module map, rationale    |
| [data.md](docs/data.md)                     | ESCI taxonomy, files, preprocessing        |
| [training.md](docs/training.md)             | Step-by-step training, hyper-parameters    |
| [experiments.md](docs/experiments.md)       | Results, ablations, confusion matrix       |
| [deployment.md](docs/deployment.md)         | Serving, Docker, API reference, scaling    |

## Development

```bash
make install-dev
make test     # pytest (torch-dependent tests skip if torch is absent)
make lint     # ruff + mypy
make format   # black + ruff --fix
```

## Roadmap / future work

- [ ] **ANN index** — swap `IndexFlatIP` for IVF/HNSW and benchmark
      recall/latency at million-product scale.
- [ ] **Hybrid retrieval** — fuse dense + BM25 (reciprocal-rank / learned fusion)
      as the first stage.
- [ ] **Knowledge distillation** — distill the cross-encoder into the bi-encoder
      (margin-MSE) to lift retrieval without the rerank cost.
- [ ] **Listwise reranking objective** — train the reranker with a LambdaRank /
      ListNet loss directly on NDCG instead of pointwise cross-entropy.
- [ ] **Multilingual** — joint training across `us` / `es` / `jp` with a
      multilingual backbone.
- [ ] **ONNX / quantization** export and a GPU serving image for low latency.
- [ ] **Online metrics & caching** — query-embedding cache, p99 latency tracking,
      and A/B hooks.
- [ ] **Active hard-negative refresh** — re-mine negatives between epochs as the
      retriever improves.

## Citation

This project builds on the ESCI benchmark:

```bibtex
@article{reddy2022shopping,
  title   = {Shopping Queries Dataset: A Large-Scale ESCI Benchmark for
             Improving Product Search},
  author  = {Reddy, Chandan K. and others},
  journal = {arXiv preprint arXiv:2206.06588},
  year    = {2022}
}
```

## License

MIT — see [LICENSE](LICENSE).
