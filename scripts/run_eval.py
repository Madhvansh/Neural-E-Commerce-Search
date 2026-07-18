#!/usr/bin/env python
"""Evaluate ESCI Task 1 ranking and Task 2 classification separately.

Task 1 uses Amazon's reduced ranking subset. Task 2 uses the full multiclass
labelled set. No metric from this command should be published without the
dataset revision, configuration, raw outputs, environment, and commit identity.
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
    for query_id, examples in grouped.items():
        index = BM25Index(
            [example.product_id for example in examples],
            [example.product_text for example in examples],
        )
        hits = index.search(examples[0].query, top_k=top_k)
        rankings[query_id] = [hit.product_id for hit in hits]
    return rankings


def _pipeline_rankings(
    grouped,
    retriever,
    reranker,
    retrieval_top_k,
    rerank_top_k,
):
    """Retrieve with the bi-encoder before reranking its candidate set."""
    if retrieval_top_k < 1 or rerank_top_k < 1:
        raise ValueError("retrieval_top_k and rerank_top_k must be positive")

    rankings = {}
    for query_id, examples in grouped.items():
        query = examples[0].query
        product_texts = [example.product_text for example in examples]
        query_embedding = retriever.encode_texts([query]).numpy()[0]
        product_embeddings = retriever.encode_texts(product_texts).numpy()
        dense_scores = product_embeddings @ query_embedding

        candidate_indices = np.argsort(-dense_scores)[:retrieval_top_k]
        candidate_texts = [product_texts[index] for index in candidate_indices]
        rerank_scores = reranker.score(query, candidate_texts).numpy()
        rerank_order = np.argsort(-rerank_scores)[:rerank_top_k]

        rankings[query_id] = [
            examples[int(candidate_indices[index])].product_id
            for index in rerank_order
        ]
    return rankings


def _classification_predictions(grouped, reranker):
    """Predict every judged Task 2 pair without retrieval-based filtering."""
    y_true = []
    y_pred = []
    from necs.data.preprocess import index_to_label

    for examples in grouped.values():
        query = examples[0].query
        texts = [example.product_text for example in examples]
        labels = reranker.predict_labels(query, texts).numpy()
        y_true.extend(example.label for example in examples)
        y_pred.extend(index_to_label(int(label)) for label in labels)
    return y_true, y_pred


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/pipeline.yaml")
    parser.add_argument("--retriever", default="artifacts/bi_encoder")
    parser.add_argument("--reranker", default="artifacts/cross_encoder")
    parser.add_argument("--baseline-only", action="store_true")
    parser.add_argument(
        "--ranking-only",
        action="store_true",
        help="skip the separate full Task 2 classification evaluation",
    )
    args = parser.parse_args()

    config = load_config(args.config)

    ranking_examples = load_esci(
        config.data.raw_dir,
        config.data.locale,
        task="task1_ranking",
    )
    _, ranking_test = train_test_split(ranking_examples)
    ranking_grouped = group_by_query(ranking_test)
    max_candidates = max((len(rows) for rows in ranking_grouped.values()), default=0)

    bm25_rankings = _bm25_rankings(ranking_grouped, max_candidates)
    bm25_metrics = evaluate_rankings(bm25_rankings, ranking_grouped, recall_k=10)
    logger.info("\n%s", summarize("Task 1 BM25 candidate ranking", bm25_metrics))

    if args.baseline_only:
        return

    from necs.models.bi_encoder import BiEncoder
    from necs.models.cross_encoder import CrossEncoder

    retriever = BiEncoder(
        args.retriever,
        config.bi_encoder.pooling,
        config.bi_encoder.normalize,
    )
    reranker = CrossEncoder(args.reranker, config.cross_encoder.num_labels)
    pipeline_rankings = _pipeline_rankings(
        ranking_grouped,
        retriever,
        reranker,
        config.bi_encoder.retrieval_top_k,
        config.cross_encoder.rerank_top_k,
    )
    pipeline_metrics = evaluate_rankings(
        pipeline_rankings,
        ranking_grouped,
        recall_k=10,
    )
    logger.info("\n%s", summarize("Task 1 dense plus reranker", pipeline_metrics))

    if args.ranking_only:
        return

    classification_examples = load_esci(
        config.data.raw_dir,
        config.data.locale,
        task="task2_classification",
    )
    _, classification_test = train_test_split(classification_examples)
    classification_grouped = group_by_query(classification_test)
    y_true, y_pred = _classification_predictions(classification_grouped, reranker)
    classification = evaluate_classification(y_true, y_pred)
    logger.info(
        "\n=== Task 2 ESCI classification ===\n"
        "  micro_f1       %.4f\n"
        "  macro_f1       %.4f",
        classification["micro_f1"],
        classification["macro_f1"],
    )


if __name__ == "__main__":
    main()
