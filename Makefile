.PHONY: help install install-dev demo data train-retriever mine-negatives train-reranker eval serve test lint format clean

help:
	@echo "Neural E-Commerce Search — common tasks"
	@echo ""
	@echo "  install         Install runtime dependencies"
	@echo "  install-dev     Install runtime + dev dependencies"
	@echo "  data            Download and preprocess the ESCI dataset"
	@echo "  train-retriever Train the bi-encoder retriever"
	@echo "  mine-negatives  Mine hard negatives from the trained retriever"
	@echo "  train-reranker  Train the DeBERTa cross-encoder reranker"
	@echo "  eval            Run the end-to-end evaluation vs the BM25 baseline"
	@echo "  serve           Launch the FastAPI search service"
	@echo "  test            Run the test suite"
	@echo "  lint            Run ruff + mypy"
	@echo "  format          Auto-format with black + ruff"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt
	pip install -e .

demo:
	python scripts/offline_demo.py

data:
	python scripts/download_esci.py --locale us --out data/raw

train-retriever:
	bash scripts/train_retriever.sh

mine-negatives:
	python -m necs.data.hard_negatives --config configs/bi_encoder.yaml

train-reranker:
	bash scripts/train_reranker.sh

eval:
	python scripts/run_eval.py --config configs/pipeline.yaml

serve:
	uvicorn necs.api.app:app --host 0.0.0.0 --port 8000

test:
	pytest

lint:
	ruff check src tests scripts
	mypy src

format:
	black src tests scripts
	ruff check --fix src tests scripts

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache **/__pycache__ build dist *.egg-info
