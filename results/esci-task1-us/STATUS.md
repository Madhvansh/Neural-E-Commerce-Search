# Task 1 ranking BM25 baseline — bundle status

This directory is the designated home for the **first result bundle produced
under the evidence contract**: a lexical BM25 baseline on the official Amazon
ESCI Task 1 ranking subset. It is being built the way `docs/reproducibility.md`
and `results/README.md` require — pinned inputs, raw predictions, checksums —
rather than by re-stating a withdrawn number.

## Honesty boundary (read first)

- The metric this bundle will carry is a **NEW lexical BM25 baseline**. BM25 has
  no learned weights.
- It is **NOT** the withdrawn historical neural NDCG / recall / micro-F1 figures
  and must never be presented as their restoration. Those return only through
  the full learned-result contract in `docs/reproducibility.md`.
- Publishing a keyword baseline is exactly step 2 of the minimum rerun plan in
  `docs/experiments.md` ("Run BM25 from a clean checkout").

## What ran in this session

| Step | Status | Evidence |
|---|---|---|
| Pin the ESCI dataset to an immutable revision | DONE | `dataset.pin.json` — `amazon-science/esci-data@7916cdf6ab75a462e77f20ab40428a10923998d5` |
| Record SHA-256 for every input file | DONE | `dataset.pin.json` (LFS content hashes, verifiable after `git lfs pull`) |
| Build the end-to-end runner | DONE | `scripts/run_baseline_bundle.py` |
| Prove the runner end to end (no data, no GPU) | DONE | `--self-test` produced a full bundle + self-verified `SHA256SUMS` |
| Prove the immutability gate | DONE | missing inputs → status + exit 2; wrong bytes → SHA mismatch → exit 2 |
| Run BM25 on the real ESCI Task 1 subset | **NOT RUN** | see below |

The harness self-test ran the *identical* code path (BM25 → repo evaluator →
predictions → `SHA256SUMS`) over a tiny **synthetic** ESCI-schema fixture. Its
numbers (NDCG@10 and Recall@10 = 1.0 on 2 toy queries) are a **plumbing check
only** — synthetic, not ESCI, not a benchmark, and never to be published as one.

## What did NOT run, and why

The real BM25 baseline over ESCI Task 1 was not executed in this session. The
Task 1 candidate texts require the products parquet, which at the pinned
revision is a **1.11 GB Git-LFS object**
(`shopping_queries_dataset_products.parquet`,
`sha256:25124442…b65a265`, 1,108,857,465 bytes). Fetching it is a large
download that this session was explicitly scoped to avoid, and it must arrive
through Git LFS — the repo's `scripts/download_esci.py` uses
`raw.githubusercontent.com`, which returns the ~133-byte LFS **pointer**, not
the parquet, so that path does not obtain the real data.

A partial-but-honest artifact (pinned inputs + a proven runner) is shipped here
in preference to a fabricated number.

## Finish the bundle (one command)

On a machine willing to take the ~1.1 GB download:

```bash
# 1. fetch the pinned inputs
git clone https://github.com/amazon-science/esci-data esci-data
cd esci-data && git checkout 7916cdf6ab75a462e77f20ab40428a10923998d5 && git lfs pull
mkdir -p ../data/raw
cp shopping_queries_dataset/shopping_queries_dataset_examples.parquet ../data/raw/
cp shopping_queries_dataset/shopping_queries_dataset_products.parquet ../data/raw/
cd ..

# 2. install the retrieval + data extras
python -m pip install -e ".[retrieval,data]" jsonschema

# 3. run the baseline; the harness SHA-256-gates the inputs before it runs
python scripts/run_baseline_bundle.py \
    --pin results/esci-task1-us/dataset.pin.json \
    --raw-dir data/raw \
    --out results/esci-task1-us
```

This writes, into this directory:

```text
results/esci-task1-us/
├── dataset.pin.json        # frozen inputs (already committed)
├── dataset_checksums.txt    # sha256 of each input file
├── environment.txt          # python, platform, package versions
├── predictions/
│   ├── bm25.run             # raw per-query ranking, TREC run format
│   └── bm25.jsonl           # same, machine-readable
├── tables/
│   ├── metrics.json         # NDCG@10, Recall@10 — labelled lexical BM25
│   └── metrics.md
├── logs/run.log
├── manifest.json            # schema-valid against results/manifest.schema.json
└── SHA256SUMS               # covers the pin, predictions, and tables
```

Every metric is computed by the repository's own evaluator
(`necs.eval.evaluate.evaluate_rankings`): NDCG@10 over graded ESCI gains, and
Recall@10 over the Exact (`E`) label, with missing queries scored zero and ideal
DCG taken from the complete qrels.
