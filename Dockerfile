# Slim CPU image for serving the two-stage search API.
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    NECS_RETRIEVER=/app/artifacts/bi_encoder \
    NECS_RERANKER=/app/artifacts/cross_encoder \
    NECS_INDEX=/app/artifacts/product_index \
    NECS_CATALOGUE=/app/artifacts/catalogue.json

WORKDIR /app

# System deps kept minimal; faiss-cpu and torch ship manylinux wheels.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-deps -e .

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "necs.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
