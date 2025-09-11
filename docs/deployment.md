# Deployment

The search service is a stateless FastAPI app (`necs.api.app:app`) that loads
four artifacts at startup and serves `/search`.

## Artifacts

| Env var          | Default                       | Produced by                |
|------------------|-------------------------------|----------------------------|
| `NECS_RETRIEVER` | `artifacts/bi_encoder`        | `train_retriever.sh`       |
| `NECS_RERANKER`  | `artifacts/cross_encoder`     | `train_reranker.sh`        |
| `NECS_INDEX`     | `artifacts/product_index`     | `scripts/build_index.py`   |
| `NECS_CATALOGUE` | `artifacts/catalogue.json`    | `scripts/build_index.py` / export |

`catalogue.json` is a flat `{product_id: product_text}` map used to fetch the
passage shown to the reranker and returned to the client. If artifacts are
missing the app still boots and `/health` reports `model_loaded: false`, so
Kubernetes/compose readiness probes behave correctly.

## Local (bare metal)

```bash
pip install -r requirements.txt
make serve            # uvicorn necs.api.app:app --host 0.0.0.0 --port 8000
```

## Docker

```bash
# Build
docker build -t necs-search:latest .

# Run with trained artifacts mounted read-only
docker run --rm -p 8000:8000 \
    -v "$(pwd)/artifacts:/app/artifacts:ro" \
    necs-search:latest
```

Or with compose:

```bash
docker compose up --build
```

The image is CPU-only (`faiss-cpu`, CPU torch wheels). For GPU serving, base the
image on `pytorch/pytorch:*-cuda*` and install `faiss-gpu`.

## API

### `GET /health`

```json
{ "status": "ok", "model_loaded": true, "catalogue_size": 482105 }
```

### `POST /search`

Request:

```json
{ "query": "wireless gaming mouse", "top_k": 5 }
```

Response:

```json
{
  "query": "wireless gaming mouse",
  "took_ms": 41.7,
  "results": [
    {
      "product_id": "B0XXXXXXX",
      "product_text": "logitech g pro x superlight wireless gaming mouse ...",
      "score": 0.94,
      "label": "E",
      "label_name": "Exact",
      "retrieval_rank": 2
    }
  ]
}
```

Try it:

```bash
curl -s localhost:8000/search \
  -H 'content-type: application/json' \
  -d '{"query":"wireless gaming mouse","top_k":5}' | jq
```

Interactive docs are served at `http://localhost:8000/docs` (Swagger UI).

## Scaling notes

* **Index** — `IndexFlatIP` is exact but linear in catalogue size. For millions
  of products switch to `IndexIVFFlat` or HNSW; the `DenseIndex` API is
  unchanged.
* **Reranker** — the cost driver online. Cap `rerank_top_k` (default 100), batch
  candidate scoring (already done), and serve on GPU or with ONNX / quantization
  for latency-sensitive traffic.
* **Statelessness** — the app holds no per-request state, so it scales
  horizontally behind a load balancer; bake artifacts into the image or mount a
  shared read-only volume.
* **Warm-up** — first request pays model load; rely on the `/health` readiness
  probe before routing traffic.
