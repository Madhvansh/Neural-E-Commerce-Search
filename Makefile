.PHONY: help install install-dev install-all demo data train-retriever mine-negatives train-reranker eval serve test lint format clean

help:
	@echo "Neural E-Commerce Search — common tasks"
	@echo ""
	@echo "  install         Install the lightweight runtime package"
	@echo "  install-dev     Install the lightweight package + dev tools"
	@echo "  install-all     Install models, data, retrieval, serving + dev tools"
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
	python -m pip install -e .

install-dev:
	python -m pip install -e ".[dev]"

install-all:
	python -m pip install -e ".[all,dev]"

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
