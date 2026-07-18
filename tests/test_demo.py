"""Tests for the dependency-free, explicitly non-neural demo."""

import json

import pytest

from necs.demo import DemoProduct, format_table, infer_label, load_catalog, search


def test_bundled_catalog_has_all_esci_relationships():
    results = search("wireless gaming mouse", load_catalog(), top_k=6)
    assert {result.label for result in results} == {"E", "S", "C", "I"}


def test_exact_results_rank_before_other_relationships():
    results = search("wireless gaming mouse", load_catalog(), top_k=6)
    assert results[0].label == "E"
    assert results[-1].label == "I"
    assert [result.rank for result in results] == list(range(1, 7))


def test_complement_rule_is_explicit():
    pad = DemoProduct("pad", "Large Gaming Mouse Pad", "mouse-accessory", ("mouse",))
    assert infer_label("wireless mouse", pad) == "C"


def test_top_k_must_be_positive():
    with pytest.raises(ValueError, match="top_k"):
        search("mouse", load_catalog(), top_k=0)


def test_table_discloses_non_neural_status():
    output = format_table("mouse", search("mouse", load_catalog(), top_k=2))
    assert "no neural models loaded" in output
    assert "not a model-quality result" in output


def test_custom_catalog_json(tmp_path):
    path = tmp_path / "catalog.json"
    path.write_text(
        json.dumps([{"product_id": "one", "title": "Blue Mug", "category": "mug"}]),
        encoding="utf-8",
    )
    catalog = load_catalog(path)
    assert catalog == [DemoProduct("one", "Blue Mug", "mug")]
