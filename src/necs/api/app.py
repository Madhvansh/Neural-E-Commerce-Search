"""FastAPI application exposing the two-stage product search.

Artifacts (retriever, reranker, FAISS index, catalogue) are loaded lazily on
startup from paths supplied via environment variables so the same image runs
locally and in production:

* ``NECS_RETRIEVER``  — path to the saved bi-encoder       (default ``artifacts/bi_encoder``)
* ``NECS_RERANKER``   — path to the saved cross-encoder    (default ``artifacts/cross_encoder``)
* ``NECS_INDEX``      — path to the saved FAISS index      (default ``artifacts/product_index``)
* ``NECS_CATALOGUE``  — JSON ``{product_id: text}`` mapping (default ``artifacts/catalogue.json``)

If artifacts are absent the service still starts and ``/health`` reports
``model_loaded: false`` so orchestration can probe readiness.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException

from necs.api.schemas import HealthResponse, ResultItem, SearchRequest, SearchResponse
from necs.utils.logging import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Neural E-Commerce Search",
    description="Two-stage retrieve-and-rank product search on Amazon ESCI.",
    version="0.1.0",
)

_STATE: dict = {"searcher": None, "catalogue_size": 0}


def _load_searcher():
    """Best-effort load of all artifacts; returns a TwoStageSearcher or None."""
    retriever_path = os.environ.get("NECS_RETRIEVER", "artifacts/bi_encoder")
    reranker_path = os.environ.get("NECS_RERANKER", "artifacts/cross_encoder")
    index_path = os.environ.get("NECS_INDEX", "artifacts/product_index")
    catalogue_path = os.environ.get("NECS_CATALOGUE", "artifacts/catalogue.json")

    if not Path(catalogue_path).exists():
        logger.warning("Catalogue %s not found; serving in degraded mode", catalogue_path)
        return None

    from necs.models.bi_encoder import BiEncoder
    from necs.models.cross_encoder import CrossEncoder
    from necs.pipeline.search import TwoStageSearcher
    from necs.retrieval.index import DenseIndex

    catalogue = json.loads(Path(catalogue_path).read_text())
    searcher = TwoStageSearcher(
        bi_encoder=BiEncoder(retriever_path),
        cross_encoder=CrossEncoder(reranker_path),
        index=DenseIndex.load(index_path),
        product_text=catalogue,
    )
    _STATE["catalogue_size"] = len(catalogue)
    logger.info("Loaded searcher with %d products", len(catalogue))
    return searcher


@app.on_event("startup")
def _startup() -> None:
    try:
        _STATE["searcher"] = _load_searcher()
    except Exception as exc:  # pragma: no cover - defensive startup guard
        logger.exception("Failed to load search artifacts: %s", exc)
        _STATE["searcher"] = None


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        model_loaded=_STATE["searcher"] is not None,
        catalogue_size=_STATE["catalogue_size"],
    )


@app.post("/search", response_model=SearchResponse)
def search(request: SearchRequest) -> SearchResponse:
    searcher = _STATE["searcher"]
    if searcher is None:
        raise HTTPException(status_code=503, detail="Search artifacts not loaded")

    start = time.perf_counter()
    results = searcher.search(request.query, top_k=request.top_k)
    took_ms = (time.perf_counter() - start) * 1000.0

    return SearchResponse(
        query=request.query,
        took_ms=round(took_ms, 2),
        results=[
            ResultItem(
                product_id=r.product_id,
                product_text=r.product_text,
                score=r.score,
                label=r.label,
                label_name=r.label_name,
                retrieval_rank=r.retrieval_rank,
            )
            for r in results
        ],
    )
