"""Dependency-free product-search demo for the repository's output contract.

This module intentionally does not load the trained neural models. It provides
a small, deterministic lexical candidate stage plus transparent ESCI-label
heuristics so a new contributor can inspect the expected search output offline.
It is a UX and integration demo, not benchmark evidence.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import asdict, dataclass
from importlib import resources
from pathlib import Path
from typing import Any

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_LABEL_PRIORITY = {"E": 3, "S": 2, "C": 1, "I": 0}
_LABEL_NAMES = {
    "E": "Exact",
    "S": "Substitute",
    "C": "Complement",
    "I": "Irrelevant",
}


@dataclass(frozen=True)
class DemoProduct:
    product_id: str
    title: str
    category: str
    complements: tuple[str, ...] = ()


@dataclass(frozen=True)
class DemoResult:
    rank: int
    product_id: str
    label: str
    label_name: str
    lexical_score: float
    title: str


def tokenize(text: str) -> set[str]:
    """Return lowercase alphanumeric terms for the transparent demo scorer."""
    return set(_TOKEN_RE.findall(text.lower()))


def load_catalog(path: str | Path | None = None) -> list[DemoProduct]:
    """Load the bundled synthetic catalogue or a compatible JSON file."""
    if path is None:
        raw = resources.files("necs").joinpath("demo_catalog.json").read_text(encoding="utf-8")
    else:
        raw = Path(path).read_text(encoding="utf-8")
    rows: list[dict[str, Any]] = json.loads(raw)
    return [
        DemoProduct(
            product_id=str(row["product_id"]),
            title=str(row["title"]),
            category=str(row["category"]),
            complements=tuple(str(value) for value in row.get("complements", [])),
        )
        for row in rows
    ]


def lexical_score(query: str, product: DemoProduct) -> float:
    """Compute a deterministic overlap score for candidate ordering."""
    query_terms = tokenize(query)
    title_terms = tokenize(product.title)
    if not query_terms:
        return 0.0
    overlap = query_terms & title_terms
    coverage = len(overlap) / len(query_terms)
    precision = len(overlap) / max(len(title_terms), 1)
    phrase_bonus = 0.25 if query.lower() in product.title.lower() else 0.0
    return coverage + 0.25 * precision + phrase_bonus


def infer_label(query: str, product: DemoProduct) -> str:
    """Assign a documented heuristic ESCI label for the synthetic catalogue."""
    query_terms = tokenize(query)
    title_terms = tokenize(product.title)
    if not query_terms:
        return "I"
    if query_terms <= title_terms:
        return "E"

    query_head = next((term for term in reversed(query.lower().split()) if term.isalnum()), "")
    if query_head and query_head in product.complements:
        return "C"

    category_terms = tokenize(product.category.replace("-", " "))
    if query_terms & title_terms and (query_terms & category_terms or query_head in category_terms):
        return "S"
    return "I"


def search(query: str, catalog: list[DemoProduct], top_k: int = 5) -> list[DemoResult]:
    """Run the offline demo and return label-aware ranked results."""
    if top_k < 1:
        raise ValueError("top_k must be at least 1")
    scored = [
        (infer_label(query, product), lexical_score(query, product), product)
        for product in catalog
    ]
    scored.sort(
        key=lambda item: (_LABEL_PRIORITY[item[0]], item[1], item[2].product_id),
        reverse=True,
    )
    return [
        DemoResult(
            rank=rank,
            product_id=product.product_id,
            label=label,
            label_name=_LABEL_NAMES[label],
            lexical_score=round(score, 3),
            title=product.title,
        )
        for rank, (label, score, product) in enumerate(scored[:top_k], start=1)
    ]


def format_table(query: str, results: list[DemoResult]) -> str:
    """Format results without third-party table dependencies."""
    lines = [
        "Offline ESCI output demo (heuristics; no neural models loaded)",
        f"Query: {query}",
        "",
        "Rank  ID     ESCI             Lexical  Product",
        "----  -----  ---------------  -------  -------",
    ]
    for result in results:
        label = f"{result.label} ({result.label_name})"
        score = "0" if math.isclose(result.lexical_score, 0.0) else f"{result.lexical_score:.3f}"
        lines.append(
            f"{result.rank:<4}  {result.product_id:<5}  {label:<15}  {score:>7}  {result.title}"
        )
    lines.extend(
        [
            "",
            "This validates the CLI/output contract only. It is not a model-quality result.",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", default="wireless gaming mouse")
    parser.add_argument("--catalog", help="optional compatible JSON catalogue")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()

    results = search(args.query, load_catalog(args.catalog), args.top_k)
    if args.json:
        print(json.dumps({"query": args.query, "results": [asdict(r) for r in results]}, indent=2))
    else:
        print(format_table(args.query, results))


if __name__ == "__main__":
    main()
