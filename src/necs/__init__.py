"""Neural E-Commerce Search (necs).

A two-stage retrieve-and-rank pipeline for product search on the Amazon
ESCI Shopping Queries dataset:

* a dense **bi-encoder** retriever trained with in-batch and hard negatives,
* a **DeBERTa cross-encoder** reranker over the
  Exact / Substitute / Complement / Irrelevant (ESCI) labels.

The top-level package keeps imports light: heavy dependencies (``torch``,
``transformers``, ``faiss``) are imported lazily inside the submodules that
need them so that utilities, metrics, and configs can be used without a full
deep-learning stack installed.
"""

__version__ = "0.2.0"

ESCI_LABELS = ("E", "S", "C", "I")
ESCI_LABEL_NAMES = {
    "E": "Exact",
    "S": "Substitute",
    "C": "Complement",
    "I": "Irrelevant",
}

__all__ = ["__version__", "ESCI_LABELS", "ESCI_LABEL_NAMES"]
