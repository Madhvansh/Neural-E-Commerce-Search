#!/usr/bin/env python
"""Download the Amazon ESCI Shopping Queries parquet files.

The dataset lives in the ``amazon-science/esci-data`` GitHub repository under
``shopping_queries_dataset/``. This script fetches the three parquet files we
need into ``--out``. Pass ``--from-hf`` to instead pull the mirrored copy from
the Hugging Face Hub (``datasets`` must be installed).

Usage::

    python scripts/download_esci.py --locale us --out data/raw
"""

from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

RAW_BASE = (
    "https://raw.githubusercontent.com/amazon-science/esci-data/main/"
    "shopping_queries_dataset"
)
FILES = (
    "shopping_queries_dataset_examples.parquet",
    "shopping_queries_dataset_products.parquet",
    "shopping_queries_dataset_sources.csv",
)


def download_github(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        dest = out / name
        if dest.exists():
            print(f"[skip] {name} already present")
            continue
        url = f"{RAW_BASE}/{name}"
        print(f"[get ] {url}")
        urllib.request.urlretrieve(url, dest)  # noqa: S310 (trusted host)
        print(f"[ok  ] -> {dest} ({dest.stat().st_size / 1e6:.1f} MB)")


def download_hf(out: Path, locale: str) -> None:
    try:
        from datasets import load_dataset
    except ImportError:
        sys.exit("`datasets` is required for --from-hf (pip install datasets)")
    out.mkdir(parents=True, exist_ok=True)
    ds = load_dataset("tasksource/esci", split="train")
    ds = ds.filter(lambda r: r["product_locale"] == locale)
    ds.to_parquet(out / "shopping_queries_dataset_examples.parquet")
    print(f"[ok  ] wrote HF mirror to {out}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="data/raw", help="output directory")
    parser.add_argument("--locale", default="us", choices=["us", "es", "jp"])
    parser.add_argument("--from-hf", action="store_true", help="use the HF mirror")
    args = parser.parse_args()

    out = Path(args.out)
    if args.from_hf:
        download_hf(out, args.locale)
    else:
        download_github(out)
    print("Done.")


if __name__ == "__main__":
    main()
