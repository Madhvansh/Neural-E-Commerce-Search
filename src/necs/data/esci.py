"""Load the official task-specific Amazon ESCI datasets.

Task 1 ranking uses rows flagged by the small_version column. Task 2 multiclass
classification uses rows flagged by large_version. The protocols remain
separate so ranking and classification metrics cannot silently mix populations.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from necs.data.preprocess import build_product_text, normalize_text
from necs.utils.logging import get_logger

logger = get_logger(__name__)

_EXAMPLES_FILE = "shopping_queries_dataset_examples.parquet"
_PRODUCTS_FILE = "shopping_queries_dataset_products.parquet"
_TASK_VERSION_COLUMNS = {
    "task1_ranking": "small_version",
    "task2_classification": "large_version",
}


def version_column_for_task(task: str) -> str:
    """Return the official dataset membership column for an ESCI task."""
    try:
        return _TASK_VERSION_COLUMNS[task]
    except KeyError as exc:
        choices = ", ".join(sorted(_TASK_VERSION_COLUMNS))
        raise ValueError(f"Unknown ESCI task {task!r}; choose one of: {choices}") from exc


@dataclass(frozen=True)
class ESCIExample:
    """A single query-product judgement."""

    query_id: int
    query: str
    product_id: str
    product_text: str
    label: str
    split: str

    def __post_init__(self) -> None:
        if self.label not in ("E", "S", "C", "I"):
            raise ValueError(f"Invalid ESCI label: {self.label!r}")


def _read_parquet(path: Path):
    import pandas as pd

    return pd.read_parquet(path)


def load_esci(
    raw_dir: str | Path,
    locale: str = "us",
    task: str = "task1_ranking",
) -> list[ESCIExample]:
    """Load and join ESCI examples for one explicit official task.

    Parameters
    ----------
    raw_dir:
        Directory containing the ESCI parquet files.
    locale:
        Product locale to keep: us, es, or jp.
    task:
        task1_ranking filters small_version. task2_classification filters
        large_version.
    """
    raw_dir = Path(raw_dir)
    examples = _read_parquet(raw_dir / _EXAMPLES_FILE)
    products = _read_parquet(raw_dir / _PRODUCTS_FILE)

    examples = examples[examples["product_locale"] == locale]
    products = products[products["product_locale"] == locale]

    version_column = version_column_for_task(task)
    if version_column not in examples.columns:
        raise ValueError(
            f"ESCI examples are missing required {version_column!r} column for {task}"
        )
    examples = examples[examples[version_column] == 1]

    merged = examples.merge(
        products,
        on=["product_id", "product_locale"],
        how="inner",
        validate="many_to_one",
    )
    logger.info(
        "Loaded %d ESCI examples (locale=%s, task=%s)",
        len(merged),
        locale,
        task,
    )

    output: list[ESCIExample] = []
    for row in merged.itertuples(index=False):
        output.append(
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
    return output


def train_test_split(
    examples: list[ESCIExample],
) -> tuple[list[ESCIExample], list[ESCIExample]]:
    """Split on the dataset's official split column."""
    train = [example for example in examples if example.split == "train"]
    test = [example for example in examples if example.split == "test"]
    logger.info("Split: %d train / %d test", len(train), len(test))
    return train, test
