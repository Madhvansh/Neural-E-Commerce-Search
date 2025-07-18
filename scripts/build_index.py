#!/usr/bin/env python
"""Embed the product catalogue and build a FAISS index for retrieval.

Usage::

    python scripts/build_index.py \
        --config configs/bi_encoder.yaml \
        --retriever artifacts/bi_encoder \
        --out artifacts/product_index
"""

from __future__ import annotations

import argparse

import numpy as np

from necs.config import load_config
from necs.data.esci import load_esci
from necs.models.bi_encoder import BiEncoder
from necs.retrieval.index import DenseIndex
from necs.utils.logging import get_logger

logger = get_logger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/bi_encoder.yaml")
    parser.add_argument("--retriever", default="artifacts/bi_encoder")
    parser.add_argument("--out", default="artifacts/product_index")
    args = parser.parse_args()

    config = load_config(args.config)
    examples = load_esci(
        config.data.raw_dir, config.data.locale, config.data.use_small_version
    )

    # Deduplicate the catalogue on product_id.
    catalogue = {ex.product_id: ex.product_text for ex in examples}
    product_ids = list(catalogue)
    texts = [catalogue[pid] for pid in product_ids]
    logger.info("Embedding %d unique products", len(product_ids))

    model = BiEncoder(config.bi_encoder.model_name, config.bi_encoder.pooling)
    embeddings = model.encode_texts(
        texts, batch_size=config.bi_encoder.batch_size,
        max_seq_len=config.bi_encoder.max_seq_len,
    ).numpy().astype(np.float32)

    index = DenseIndex(dim=embeddings.shape[1])
    index.add(product_ids, embeddings)
    index.save(args.out)
    logger.info("Wrote index with %d vectors to %s", len(index), args.out)


if __name__ == "__main__":
    main()
