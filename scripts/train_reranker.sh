#!/usr/bin/env bash
# Stage 2: train the DeBERTa cross-encoder reranker on ESCI labels.
set -euo pipefail

CONFIG="${1:-configs/cross_encoder.yaml}"

echo "==> Training cross-encoder reranker"
python -m necs.training.train_cross_encoder --config "${CONFIG}"

echo "Done."
