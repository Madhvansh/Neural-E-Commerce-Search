#!/usr/bin/env bash
# Two-pass bi-encoder training with an explicit warm checkpoint.
set -euo pipefail

CONFIG="${1:-configs/bi_encoder.yaml}"
WARM_DIR="artifacts/bi_encoder_warm"
FINAL_DIR="artifacts/bi_encoder"
NEGATIVES="artifacts/hard_negatives.json"

echo "==> Pass 1: in-batch negatives"
python -m necs.training.train_bi_encoder \
    --config "${CONFIG}" \
    --output-dir "${WARM_DIR}"

echo "==> Mining hard negatives with the warmed retriever"
python -m necs.data.hard_negatives \
    --config "${CONFIG}" \
    --retriever "${WARM_DIR}" \
    --out "${NEGATIVES}"

echo "==> Pass 2: continue from warm checkpoint with hard negatives"
python -m necs.training.train_bi_encoder \
    --config "${CONFIG}" \
    --init-from "${WARM_DIR}" \
    --output-dir "${FINAL_DIR}" \
    --hard-negatives "${NEGATIVES}"

echo "Done: ${FINAL_DIR}"
