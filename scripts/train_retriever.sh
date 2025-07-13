#!/usr/bin/env bash
# Stage 1: train the bi-encoder retriever.
#
# Pass 1 trains with in-batch negatives, mines hard negatives from the
# warmed-up model, then pass 2 fine-tunes against those hard negatives.
set -euo pipefail

CONFIG="${1:-configs/bi_encoder.yaml}"

echo "==> Pass 1: in-batch negatives"
python -m necs.training.train_bi_encoder --config "${CONFIG}"

echo "==> Mining hard negatives"
python -m necs.data.hard_negatives --config "${CONFIG}" --out artifacts/hard_negatives.json

echo "==> Pass 2: fine-tune with hard negatives"
python -m necs.training.train_bi_encoder \
    --config "${CONFIG}" \
    --hard-negatives artifacts/hard_negatives.json

echo "Done."
