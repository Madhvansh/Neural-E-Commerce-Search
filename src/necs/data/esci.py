"""Loader for the Amazon ESCI Shopping Queries dataset.

The public dataset (``amazon-science/esci-data``) ships three parquet files:

* ``shopping_queries_dataset_examples.parquet`` — (query, product, label) rows
* ``shopping_queries_dataset_products.parquet`` — product catalogue
* ``shopping_queries_dataset_sources.parquet``  — query provenance

We join examples against the catalogue, restrict to a locale, and expose the
official ``small_version`` train/test split. ESCI labels are
``esci_label ∈ {E, S, C, I}`` (Exact, Substitute, Complement, Irrelevant).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from necs.data.preprocess import build_product_text, normalize_text
from necs.utils.logging import get_logger

logger = get_logger(__name__)

_EXAMPLES_FILE = "shopping_queries_dataset_examples.parquet"
_PRODUCTS_FILE = "shopping_queries_dataset_products.parquet"


@dataclass(frozen=True)
class ESCIExample:
    """A single (query, product, label) judgement."""

    query_id: int
    query: str
    product_id: str
    product_text: str
    label: str  # one of E / S / C / I
    split: str  # "train" or "test"

    def __post_init__(self) -> None:
        if self.label not in ("E", "S", "C", "I"):
            raise ValueError(f"Invalid ESCI label: {self.label!r}")


def _read_parquet(path: Path):
    import pandas as pd

    return pd.read_parquet(path)


def load_esci(
    raw_dir: str | Path,
    locale: str = "us",
    use_small_version: bool = True,
) -> list[ESCIExample]:
    """Load and join ESCI examples with their product metadata.

    Parameters
    ----------
    raw_dir:
        Directory containing the three ESCI parquet files.
    locale:
        Product locale to keep (``us``, ``es``, or ``jp``).
    use_small_version:
        If ``True``, keep only rows flagged with ``small_version == 1``
        (the reduced product set used for the public benchmark).
    """
    raw_dir = Path(raw_dir)
    examples = _read_parquet(raw_dir / _EXAMPLES_FILE)
    products = _read_parquet(raw_dir / _PRODUCTS_FILE)

    examples = examples[examples["product_locale"] == locale]
    products = products[products["product_locale"] == locale]
    if use_small_version and "small_version" in examples.columns:
        examples = examples[examples["small_version"] == 1]

    merged = examples.merge(
        products,
        on=["product_id", "product_locale"],
        how="inner",
        validate="many_to_one",
    )
    logger.info("Loaded %d ESCI examples (locale=%s)", len(merged), locale)

    out: list[ESCIExample] = []
    for row in merged.itertuples(index=False):
        out.append(
            ESCIExample(
                query_id=int(row.query_id),
                query=normalize_text(row.query),
                product_id=str(row.product_id),
                product_text=build_product_text(
                    title=getattr(row, "product_title", None),
                    brand=getattr(row, "product_brand", None),
                    color=getattr(row, "product_color", None),
                    bullet_point=getattr(row, "product_bullet_point", None),
                    description=getattr(row, "product_description", None),
                ),
                label=str(row.esci_label),
                split=str(row.split),
            )
        )
    return out


def train_test_split(
    examples: list[ESCIExample],
) -> tuple[list[ESCIExample], list[ESCIExample]]:
    """Split on the dataset's official ``split`` column."""
    train = [e for e in examples if e.split == "train"]
    test = [e for e in examples if e.split == "test"]
    logger.info("Split: %d train / %d test", len(train), len(test))
    return train, test
