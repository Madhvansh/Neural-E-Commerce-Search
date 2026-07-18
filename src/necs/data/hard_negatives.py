"""Hard-negative mining for the retriever.

After a warm-up pass, we embed the catalogue, retrieve the top-``k`` products
for every training query, and keep the *non-positive* hits as hard negatives:
documents the model currently ranks highly but that are labelled S / C / I.
These are far more informative than random negatives and drive most of the
retriever's gains on Substitute-vs-Complement queries.

Run as a module::

    python -m necs.data.hard_negatives --config configs/bi_encoder.yaml \
        --out artifacts/hard_negatives.json
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path

from necs.data.esci import ESCIExample
from necs.utils.logging import get_logger

logger = get_logger(__name__)

# Labels that may serve as hard negatives (everything that is not an Exact match).
_NEGATIVE_LABELS = {"S", "C", "I"}


def build_positive_map(examples: Sequence[ESCIExample]) -> dict[int, set[str]]:
    """query_id -> set of product_ids judged Exact (true positives)."""
    positives: dict[int, set[str]] = defaultdict(set)
    for ex in examples:
        if ex.label == "E":
            positives[ex.query_id].add(ex.product_id)
    return positives


def mine_from_rankings(
    rankings: dict[int, list[str]],
    examples: Sequence[ESCIExample],
    num_negatives: int = 4,
) -> dict[int, list[str]]:
    """Select hard negatives from per-query retrieval rankings.

    Parameters
    ----------
    rankings:
        ``query_id -> ranked product_ids`` from the warmed-up retriever.
    examples:
        Labelled examples, used to look up positives and product text.
    num_negatives:
        How many hard negatives to keep per query.
    """
    positives = build_positive_map(examples)
    text_by_id = {ex.product_id: ex.product_text for ex in examples}
    # Known non-exact judgements are reliable hard negatives.
    judged_negatives: dict[int, set[str]] = defaultdict(set)
    for ex in examples:
        if ex.label in _NEGATIVE_LABELS:
            judged_negatives[ex.query_id].add(ex.product_id)

    mined: dict[int, list[str]] = {}
    for qid, ranked in rankings.items():
        pos = positives.get(qid, set())
        negative_ids = judged_negatives.get(qid, set())
        chosen: list[str] = []
        chosen_ids: set[str] = set()
        for pid in ranked:
            if pid in pos:
                continue  # never use a true positive as a negative
            # Task-specific mining uses only query-product pairs with an
            # explicit S/C/I judgement. A product's label for another query is
            # not evidence that it is negative for this one.
            if pid in negative_ids and pid in text_by_id and pid not in chosen_ids:
                chosen.append(text_by_id[pid])
                chosen_ids.add(pid)
            if len(chosen) >= num_negatives:
                break
        if chosen:
            mined[qid] = chosen
    logger.info("Mined hard negatives for %d queries", len(mined))
    return mined


def _retrieve_rankings(
    config,
    examples,
    top_k: int,
    retriever_checkpoint: str,
) -> dict[int, list[str]]:
    """Retrieve with the explicit warmed checkpoint."""
    import numpy as np

    from necs.models.bi_encoder import BiEncoder
    from necs.retrieval.index import DenseIndex

    catalogue = {ex.product_id: ex.product_text for ex in examples}
    product_ids = list(catalogue)
    model = BiEncoder(
        retriever_checkpoint,
        config.bi_encoder.pooling,
        config.bi_encoder.normalize,
    )
    prod_emb = model.encode_texts([catalogue[p] for p in product_ids]).numpy()
    index = DenseIndex(dim=prod_emb.shape[1])
    index.add(product_ids, prod_emb.astype(np.float32))

    queries: dict[int, str] = {}
    for ex in examples:
        queries.setdefault(ex.query_id, ex.query)
    qids = list(queries)
    q_emb = model.encode_texts([queries[q] for q in qids]).numpy().astype(np.float32)
    hits = index.search(q_emb, top_k=top_k)
    return {qid: [h.product_id for h in row] for qid, row in zip(qids, hits)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/bi_encoder.yaml")
    parser.add_argument("--out", default="artifacts/hard_negatives.json")
    parser.add_argument(
        "--retriever",
        required=True,
        help="warmed retriever checkpoint used for hard-negative mining",
    )
    args = parser.parse_args()

    from necs.config import load_config
    from necs.data.esci import load_esci, train_test_split

    config = load_config(args.config)
    examples = load_esci(config.data.raw_dir, config.data.locale, config.data.task)
    train_ex, _ = train_test_split(examples)
    rankings = _retrieve_rankings(
        config,
        train_ex,
        config.bi_encoder.retrieval_top_k,
        retriever_checkpoint=args.retriever,
    )
    mined = mine_from_rankings(rankings, train_ex, config.bi_encoder.num_hard_negatives)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({str(k): v for k, v in mined.items()}))
    logger.info("Wrote hard negatives to %s", out)


if __name__ == "__main__":
    main()
