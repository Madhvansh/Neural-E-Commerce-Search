#!/usr/bin/env python
"""Evaluate the two-stage pipeline and the BM25 baseline on the ESCI test set.

Loads the trained retriever + reranker, builds candidate rankings for every
test query under each system, and prints NDCG@10 / Recall@100 / micro-F1.

Usage::

    python scripts/run_eval.py --config configs/pipeline.yaml \
        --retriever artifacts/bi_encoder --reranker artifacts/cross_encoder
"""

from __future__ import annotations

import argparse

import numpy as np

from necs.config import load_config
from necs.data.esci import load_esci, train_test_split
from necs.eval.evaluate import (
    evaluate_classification,
    evaluate_rankings,
    group_by_query,
    summarize,
)
from necs.utils.logging import get_logger

logger = get_logger(__name__)


def _bm25_rankings(grouped, top_k):
    from necs.retrieval.bm25 import BM25Index

    rankings = {}
    for qid, exs in grouped.items():
        idx = BM25Index([e.product_id for e in exs], [e.product_text for e in exs])
        hits = idx.search(exs[0].query, top_k=top_k)
        rankings[qid] = [h.product_id for h in hits]
    return rankings


def _pipeline_rankings(grouped, retriever, reranker, top_k):
    rankings = {}
    y_true, y_pred = [], []
    for qid, exs in grouped.items():
        query = exs[0].query
        texts = [e.product_text for e in exs]
        scores = reranker.score(query, texts).numpy()
        labels = reranker.predict_labels(query, texts).numpy()
        order = np.argsort(-scores)[:top_k]
        rankings[qid] = [exs[i].product_id for i in order]
        from necs.data.preprocess import index_to_label

        for i in range(len(exs)):
            y_true.append(exs[i].label)
            y_pred.append(index_to_label(int(labels[i])))
    return rankings, y_true, y_pred


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/pipeline.yaml")
    parser.add_argument("--retriever", default="artifacts/bi_encoder")
    parser.add_argument("--reranker", default="artifacts/cross_encoder")
    parser.add_argument("--baseline-only", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config)
    examples = load_esci(
        config.data.raw_dir, config.data.locale, config.data.use_small_version
    )
    _, test_ex = train_test_split(examples)
    grouped = group_by_query(test_ex)

    bm25 = evaluate_rankings(_bm25_rankings(grouped, 100), grouped)
    logger.info("\n%s", summarize("BM25 baseline", bm25))

    if args.baseline_only:
        return

    from necs.models.bi_encoder import BiEncoder
    from necs.models.cross_encoder import CrossEncoder

    retriever = BiEncoder(args.retriever, config.bi_encoder.pooling)
    reranker = CrossEncoder(args.reranker, config.cross_encoder.num_labels)
    rankings, y_true, y_pred = _pipeline_rankings(
        grouped, retriever, reranker, config.cross_encoder.rerank_top_k
    )
    ranking = evaluate_rankings(rankings, grouped)
    clf = evaluate_classification(y_true, y_pred)
    logger.info("\n%s", summarize("Two-stage (dense + DeBERTa)", ranking, clf))


if __name__ == "__main__":
    main()
