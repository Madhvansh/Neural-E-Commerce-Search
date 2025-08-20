"""Pydantic request/response models for the search API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Shopping query")
    top_k: int = Field(10, ge=1, le=100, description="Number of results to return")


class ResultItem(BaseModel):
    product_id: str
    product_text: str
    score: float = Field(..., description="Expected-relevance reranker score")
    label: str = Field(..., description="ESCI letter: E / S / C / I")
    label_name: str = Field(..., description="Exact / Substitute / Complement / Irrelevant")
    retrieval_rank: int = Field(..., description="Rank from the first-stage retriever")


class SearchResponse(BaseModel):
    query: str
    took_ms: float
    results: list[ResultItem]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    catalogue_size: int
