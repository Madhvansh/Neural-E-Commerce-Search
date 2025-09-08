# Training

Training proceeds in two stages. Stage 1 (retriever) must finish first because
its rankings drive hard-negative mining; Stage 2 (reranker) is independent and
can run in parallel once the data is prepared.

## 0. Prepare data

```bash
python scripts/download_esci.py --locale us --out data/raw
```

## 1. Bi-encoder retriever

```bash
bash scripts/train_retriever.sh configs/bi_encoder.yaml
```

The script runs three steps:

1. **Warm-up pass** — train with in-batch negatives only (InfoNCE,
   temperature 0.05). Every other document in the batch is an implicit negative.
2. **Hard-negative mining** — embed the catalogue, retrieve the top-100 products
   per training query, and keep highly-ranked non-Exact products as hard
   negatives (`necs.data.hard_negatives`).
3. **Fine-tune pass** — retrain with the mined negatives appended to each
   batch's document pool. The loss target for query *i* stays column *i* because
   documents are laid out as `[positives | hard-negatives]`.

Hard negatives are the single biggest lever on Substitute/Complement queries:
random negatives are trivially separable, whereas a Substitute product that the
retriever currently ranks #2 is exactly the signal we want.

### Key hyper-parameters (`configs/bi_encoder.yaml`)

| Param                | Default | Notes                                  |
|----------------------|---------|----------------------------------------|
| `model_name`         | all-MiniLM-L6-v2 | shared query/doc encoder      |
| `temperature`        | 0.05    | InfoNCE softmax temperature            |
| `num_hard_negatives` | 4       | mined negatives appended per query     |
| `retrieval_top_k`    | 100     | candidates pulled for mining / serving |
| `batch_size`         | 64      | larger ⇒ more in-batch negatives       |

## 2. Cross-encoder reranker

```bash
bash scripts/train_reranker.sh configs/cross_encoder.yaml
```

Trains `deberta-v3-base` on labelled (query, product) pairs with class-weighted
cross-entropy and gradient accumulation (effective batch 64). Dynamic padding
keeps step time down on the long-tailed product passages.

### Key hyper-parameters (`configs/cross_encoder.yaml`)

| Param           | Default                  | Notes                          |
|-----------------|--------------------------|--------------------------------|
| `model_name`    | microsoft/deberta-v3-base| joint encoder                  |
| `max_seq_len`   | 192                      | query + product budget         |
| `class_weights` | [1.0, 2.0, 4.0, 1.5]     | E, S, C, I — upweight rare ones |
| `lr`            | 1e-5                     | DeBERTa is lr-sensitive        |

## 3. Build the serving index

```bash
python scripts/build_index.py \
    --retriever artifacts/bi_encoder \
    --out artifacts/product_index
```

## 4. Evaluate

```bash
python scripts/run_eval.py --config configs/pipeline.yaml \
    --retriever artifacts/bi_encoder --reranker artifacts/cross_encoder
```

See [`docs/experiments.md`](experiments.md) for results.

## Reproducibility

* All entry points call `seed_everything(seed)` (Python / NumPy / Torch).
* Configs are plain YAML and fully captured per run.
* Mixed precision (`fp16`) is on by default on CUDA and is a no-op on CPU.
