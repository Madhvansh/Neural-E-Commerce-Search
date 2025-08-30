"""Tests for text normalization and ESCI label helpers."""

import pytest

from necs.data.preprocess import (
    build_product_text,
    index_to_label,
    label_to_index,
    normalize_text,
    relevance_gain,
)


def test_normalize_collapses_whitespace_and_lowercases():
    assert normalize_text("  Hello   WORLD\t\n") == "hello world"


def test_normalize_strips_html():
    assert normalize_text("<b>Wireless</b> Mouse") == "wireless mouse"


def test_normalize_handles_none_and_empty():
    assert normalize_text(None) == ""
    assert normalize_text("") == ""


def test_build_product_text_orders_and_joins_fields():
    text = build_product_text(
        title="Wireless Mouse", brand="Logitech", color="Black",
        bullet_point="2.4GHz", description="ergonomic",
    )
    assert text.startswith("wireless mouse logitech")
    assert "ergonomic" in text


def test_build_product_text_skips_missing_fields():
    assert build_product_text(title="Keyboard") == "keyboard"


def test_build_product_text_truncates():
    long_desc = "x" * 5000
    text = build_product_text(title="t", description=long_desc, max_chars=100)
    assert len(text) <= 100


def test_label_roundtrip():
    for i, letter in enumerate("ESCI"):
        assert label_to_index(letter) == i
        assert index_to_label(i) == letter


def test_label_to_index_rejects_unknown():
    with pytest.raises(ValueError):
        label_to_index("X")


def test_relevance_gain_ordering():
    assert relevance_gain("E") > relevance_gain("S") > relevance_gain("C") >= relevance_gain("I")
    assert relevance_gain("I") == 0.0
