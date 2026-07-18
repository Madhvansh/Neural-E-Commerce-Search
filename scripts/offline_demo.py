#!/usr/bin/env python
"""Run the dependency-free sample search from a source checkout."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


if __name__ == "__main__":
    importlib.import_module("necs.demo").main()
