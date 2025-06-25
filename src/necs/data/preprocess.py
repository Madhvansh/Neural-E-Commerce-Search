"""Text normalization and ESCI label helpers.

Pure-Python (no torch / pandas) so it can be unit-tested cheaply and reused
from both the offline pipeline and the online serving path.
"""

from __future__ import annotations

import re
import unicodedata

from necs import ESCI_LABELS

# Map ESCI letters to contiguous class indices used by the cross-encoder head.
_LABEL_TO_IDX = {label: i for i, label in enumerate(ESCI_LABELS)}
_IDX_TO_LABEL = {i: label for label, i in _LABEL_TO_IDX.items()}

# Graded relevance gains for ranking metrics (Exact most relevant).
ESCI_GAINS = {"E": 1.0, "S": 0.1, "C": 0.01, "I": 0.0}

_WS_RE = re.compile(r"\s+")
_HTML_RE = re.compile(r"<[^>]+>")


def normalize_text(text: str | None) -> str:
    """Lowercase, strip HTML/control chars, and collapse whitespace."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", str(text))
    text = _HTML_RE.sub(" ", text)
    text = text.replace("\n", " ").replace("\t", " ")
    text = _WS_RE.sub(" ", text).strip()
    return text.lower()


def build_product_text(
    title: str | None,
    brand: str | None = None,
    color: str | None = None,
    bullet_point: str | None = None,
    description: str | None = None,
    max_chars: int = 1024,
) -> str:
    """Concatenate product fields into a single passage for encoding.

    Title and brand lead because they carry the strongest retrieval signal;
    bullet points and description follow and are truncated to ``max_chars``.
    """
    parts = [
        normalize_text(title),
        normalize_text(brand),
        normalize_text(color),
        normalize_text(bullet_point),
        normalize_text(description),
    ]
    text = " ".join(p for p in parts if p)
    return text[:max_chars].strip()


def label_to_index(label: str) -> int:
    """ESCI letter -> class index (E=0, S=1, C=2, I=3)."""
    try:
        return _LABEL_TO_IDX[label]
    except KeyError as exc:
        raise ValueError(f"Unknown ESCI label: {label!r}") from exc


def index_to_label(index: int) -> str:
    """Class index -> ESCI letter."""
    try:
        return _IDX_TO_LABEL[index]
    except KeyError as exc:
        raise ValueError(f"Unknown class index: {index!r}") from exc


def relevance_gain(label: str) -> float:
    """Graded gain for a label, used by NDCG."""
    return ESCI_GAINS.get(label, 0.0)
