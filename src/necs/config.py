"""Lightweight configuration loading.

Configs are plain YAML files (see ``configs/``) parsed into nested
dataclasses. We avoid heavyweight config frameworks so that a config can be
loaded, merged with CLI overrides, and round-tripped without surprises.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field, fields, is_dataclass
from pathlib import Path
from typing import Any, get_type_hints

import yaml


@dataclass
class DataConfig:
    locale: str = "us"
    raw_dir: str = "data/raw"
    processed_dir: str = "data/processed"
    max_query_len: int = 32
    max_product_len: int = 128
    task: str = "task1_ranking"


@dataclass
class BiEncoderConfig:
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    pooling: str = "mean"  # one of {"mean", "cls"}
    embedding_dim: int = 384
    normalize: bool = True
    max_seq_len: int = 128
    temperature: float = 0.05
    batch_size: int = 64
    epochs: int = 3
    lr: float = 2e-5
    warmup_ratio: float = 0.1
    num_hard_negatives: int = 4
    retrieval_top_k: int = 100


@dataclass
class CrossEncoderConfig:
    model_name: str = "microsoft/deberta-v3-base"
    num_labels: int = 4
    max_seq_len: int = 192
    batch_size: int = 32
    epochs: int = 2
    lr: float = 1e-5
    warmup_ratio: float = 0.06
    weight_decay: float = 0.01
    # Per-class loss weights compensate for ESCI label imbalance (E ≫ S, C, I).
    class_weights: list[float] = field(default_factory=lambda: [1.0, 2.0, 4.0, 1.5])
    rerank_top_k: int = 100


@dataclass
class TrainConfig:
    seed: int = 42
    output_dir: str = "artifacts"
    fp16: bool = True
    grad_accum_steps: int = 1
    eval_every: int = 1
    early_stopping_patience: int = 2
    num_workers: int = 4


@dataclass
class Config:
    data: DataConfig = field(default_factory=DataConfig)
    bi_encoder: BiEncoderConfig = field(default_factory=BiEncoderConfig)
    cross_encoder: CrossEncoderConfig = field(default_factory=CrossEncoderConfig)
    train: TrainConfig = field(default_factory=TrainConfig)


def _from_dict(cls: type, data: dict[str, Any]) -> Any:
    """Recursively build a dataclass from a (partial) dict.

    ``from __future__ import annotations`` turns field types into strings, so we
    resolve them with :func:`get_type_hints` to detect nested dataclasses.
    """
    known_fields = {field_info.name for field_info in fields(cls)}
    unknown = sorted(set(data) - known_fields)
    if unknown:
        names = ", ".join(unknown)
        raise ValueError(f"Unknown configuration field(s) for {cls.__name__}: {names}")

    hints = get_type_hints(cls)
    kwargs: dict[str, Any] = {}
    for f in fields(cls):
        if f.name not in data:
            continue
        value = data[f.name]
        field_type = hints.get(f.name, f.type)
        if is_dataclass(field_type) and isinstance(value, dict):
            kwargs[f.name] = _from_dict(field_type, value)
        else:
            kwargs[f.name] = value
    return cls(**kwargs)


def load_config(path: str | Path) -> Config:
    """Load a :class:`Config` from a YAML file, falling back to defaults."""
    raw = yaml.safe_load(Path(path).read_text()) or {}
    return _from_dict(Config, raw)


def merge_overrides(config: Config, overrides: dict[str, Any]) -> Config:
    """Apply ``section.key=value`` overrides, returning a new config.

    Example::

        merge_overrides(cfg, {"bi_encoder.lr": 3e-5, "train.seed": 7})
    """
    cfg = copy.deepcopy(config)
    for dotted, value in overrides.items():
        section, _, key = dotted.partition(".")
        if not key:
            raise ValueError(f"Override '{dotted}' must be of the form section.key")
        target = getattr(cfg, section)
        if not hasattr(target, key):
            raise AttributeError(f"Unknown config field: {dotted}")
        setattr(target, key, value)
    return cfg
