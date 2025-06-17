"""Reproducibility helpers."""

from __future__ import annotations

import os
import random


def seed_everything(seed: int = 42, deterministic: bool = True) -> int:
    """Seed Python, NumPy, and (if available) PyTorch RNGs.

    Returns the seed so callers can log it. Torch and NumPy are imported
    lazily so this helper works in environments without them installed.
    """
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)

    try:
        import numpy as np

        np.random.seed(seed)
    except ImportError:  # pragma: no cover - numpy always present in practice
        pass

    try:
        import torch

        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        if deterministic:
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass

    return seed
