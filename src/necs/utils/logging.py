"""Minimal, dependency-free logging setup with a consistent format."""

from __future__ import annotations

import logging
import sys

_CONFIGURED = False
_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"


def _configure_root(level: int) -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATEFMT))
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
    _CONFIGURED = True


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Return a configured logger.

    The first call configures the root logger; subsequent calls reuse it so
    that importing many modules does not duplicate handlers.
    """
    _configure_root(level)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger
