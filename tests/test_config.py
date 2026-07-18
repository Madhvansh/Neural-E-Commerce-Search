"""Tests for config loading and override merging."""

import textwrap

import pytest

from necs.config import Config, load_config, merge_overrides


def test_defaults_are_populated():
    cfg = Config()
    assert cfg.bi_encoder.pooling in {"mean", "cls"}
    assert cfg.cross_encoder.num_labels == 4
    assert len(cfg.cross_encoder.class_weights) == 4


def test_load_config_overrides_defaults(tmp_path):
    path = tmp_path / "cfg.yaml"
    path.write_text(
        textwrap.dedent(
            """
            bi_encoder:
              lr: 3.0e-5
              batch_size: 128
            train:
              seed: 7
            """
        )
    )
    cfg = load_config(path)
    assert cfg.bi_encoder.lr == pytest.approx(3e-5)
    assert cfg.bi_encoder.batch_size == 128
    assert cfg.train.seed == 7
    # Untouched fields keep their defaults.
    assert cfg.cross_encoder.num_labels == 4


def test_load_config_rejects_stale_data_protocol_key(tmp_path):
    path = tmp_path / "stale.yaml"
    path.write_text("data:\n  use_small_version: true\n")
    with pytest.raises(ValueError, match="use_small_version"):
        load_config(path)


def test_merge_overrides_returns_new_config():
    cfg = Config()
    new = merge_overrides(cfg, {"bi_encoder.lr": 5e-5, "train.seed": 99})
    assert new.bi_encoder.lr == pytest.approx(5e-5)
    assert new.train.seed == 99
    # Original is untouched (deep copy).
    assert cfg.train.seed == 42


def test_merge_overrides_rejects_unknown_field():
    with pytest.raises(AttributeError):
        merge_overrides(Config(), {"bi_encoder.nope": 1})


def test_merge_overrides_requires_dotted_key():
    with pytest.raises(ValueError):
        merge_overrides(Config(), {"bi_encoder": 1})
