#!/usr/bin/env python
"""Reproducibility harness: first artifact under the evidence contract.

Runs the cheapest defensible ESCI Task 1 ranking baseline -- BM25 lexical
retrieval -- end to end against a *pinned, immutable* dataset revision and
writes a result bundle whose every input and output is SHA-256 pinned.

What this harness does
----------------------
1. Reads a frozen-input pin (``dataset.pin.json``) that names the ESCI source
   repository, an immutable commit SHA, and the SHA-256 of every input file.
2. Verifies the local parquet files byte-for-byte against those SHA-256 values
   before any metric runs (the immutability gate). Missing data is reported as
   a status, not a crash, with the exact fetch command.
3. Loads the official Task 1 ranking subset with the repository's own loader
   (``small_version`` membership flag, official ``split`` column).
4. Runs BM25 per query over that query's judged candidate set, using the
   repository's ``necs.retrieval.bm25.BM25Index``.
5. Writes raw per-query predictions as a TREC run file (and JSONL) sufficient
   to recompute every table.
6. Computes NDCG@10 and Recall@10 with the repository evaluator
   (``necs.eval.evaluate.evaluate_rankings``).
7. Emits ``dataset_checksums.txt``, a schema-valid ``manifest.json``, and a
   ``SHA256SUMS`` manifest covering the dataset pin, the predictions, and the
   result tables -- then re-verifies that SHA256SUMS against the files on disk.

Honesty boundary
----------------
The number this harness publishes is a NEW lexical BM25 baseline, computed
under the repository's evidence contract (docs/reproducibility.md,
results/README.md, docs/experiments.md step 2: "Run BM25 from a clean
checkout"). BM25 uses no learned weights. This number is explicitly NOT the
withdrawn historical neural NDCG/recall/F1 figures and must never be presented
as their restoration. A learned metric returns only through the full bundle
contract described in docs/reproducibility.md.

Usage
-----
Full ESCI run (requires the pinned parquet files under --raw-dir)::

    python scripts/run_baseline_bundle.py \
        --pin results/esci-task1-us/dataset.pin.json \
        --raw-dir data/raw \
        --out results/esci-task1-us

Harness self-test (no dataset, no GPU, no network; proves the code path)::

    python scripts/run_baseline_bundle.py --self-test
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = REPO_ROOT / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    # Allow running from a clean checkout without an editable install.
    sys.path.insert(0, str(_SRC))

from necs import __version__ as PROJECT_VERSION  # noqa: E402
from necs.data.esci import ESCIExample, load_esci, train_test_split  # noqa: E402
from necs.eval.evaluate import evaluate_rankings, group_by_query, summarize  # noqa: E402
from necs.retrieval.bm25 import BM25Index  # noqa: E402

DEFAULT_PIN = REPO_ROOT / "results" / "esci-task1-us" / "dataset.pin.json"
DEFAULT_OUT = REPO_ROOT / "results" / "esci-task1-us"
SCHEMA_PATH = REPO_ROOT / "results" / "manifest.schema.json"
_CHUNK = 1024 * 1024


# --------------------------------------------------------------------------- #
# Small utilities
# --------------------------------------------------------------------------- #
def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(_CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def git_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "0" * 40  # honest placeholder; flagged in the log


# --------------------------------------------------------------------------- #
# Frozen-input pin + immutability gate
# --------------------------------------------------------------------------- #
def load_pin(pin_path: Path) -> dict:
    return json.loads(pin_path.read_text(encoding="utf-8"))


def verify_inputs(raw_dir: Path, pin: dict) -> tuple[bool, list[str]]:
    """Check every pinned input file is present with the pinned SHA-256.

    Returns (ok, messages). Never raises for missing/mismatched data -- the
    caller decides whether that is a hard failure or a reported status.
    """
    messages: list[str] = []
    ok = True
    for entry in pin["files"]:
        name = entry["name"]
        path = raw_dir / name
        if not path.is_file():
            ok = False
            messages.append(f"MISSING  {name} (expected under {raw_dir})")
            continue
        actual = sha256_file(path)
        if actual.lower() != entry["sha256"].lower():
            ok = False
            messages.append(
                f"MISMATCH {name}\n"
                f"          expected sha256 {entry['sha256']}\n"
                f"          actual   sha256 {actual}"
            )
        else:
            messages.append(f"OK       {name}  sha256={actual}")
    return ok, messages


def fetch_hint(pin: dict, raw_dir: Path) -> str:
    src = pin["source"]
    rev = pin["revision"]
    subdir = pin.get("subdir", "")
    return (
        "The pinned ESCI parquet files are Git-LFS objects and are not present.\n"
        "Fetch them at the pinned immutable revision (needs git-lfs + a large,\n"
        f"~1.1 GB download for the products file), then re-run:\n\n"
        f"    git clone {src} esci-data\n"
        f"    cd esci-data && git checkout {rev} && git lfs pull\n"
        f"    cp {subdir}/shopping_queries_dataset_examples.parquet {raw_dir}/\n"
        f"    cp {subdir}/shopping_queries_dataset_products.parquet {raw_dir}/\n\n"
        "The harness re-verifies each file's SHA-256 against the pin before use."
    )


# --------------------------------------------------------------------------- #
# BM25 baseline over each query's judged candidate set
# --------------------------------------------------------------------------- #
def bm25_rankings(
    grouped: dict[int, list[ESCIExample]],
) -> tuple[dict[int, list[str]], dict[int, list[tuple[str, float]]]]:
    """Rank each query's own candidate products by BM25 (full candidate depth).

    Mirrors scripts/run_eval.py::_bm25_rankings but also keeps the scores so a
    complete TREC run file can be written.
    """
    rankings: dict[int, list[str]] = {}
    scored: dict[int, list[tuple[str, float]]] = {}
    for query_id, examples in grouped.items():
        index = BM25Index(
            [ex.product_id for ex in examples],
            [ex.product_text for ex in examples],
        )
        hits = index.search(examples[0].query, top_k=len(examples))
        rankings[query_id] = [hit.product_id for hit in hits]
        scored[query_id] = [(hit.product_id, hit.score) for hit in hits]
    return rankings, scored


def write_run_file(path: Path, scored: dict[int, list[tuple[str, float]]], tag: str) -> None:
    """TREC run format: qid Q0 docid rank score tag (matches examples/validation)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# task: task1_ranking baseline={tag}"]
    for qid in sorted(scored):
        for rank, (product_id, score) in enumerate(scored[qid], start=1):
            lines.append(f"{qid} Q0 {product_id} {rank} {score:.6f} {tag}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_predictions_jsonl(path: Path, scored: dict[int, list[tuple[str, float]]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for qid in sorted(scored):
            record = {
                "query_id": qid,
                "ranking": [
                    {"product_id": pid, "score": round(score, 6)}
                    for pid, score in scored[qid]
                ],
            }
            handle.write(json.dumps(record) + "\n")


# --------------------------------------------------------------------------- #
# Bundle writers
# --------------------------------------------------------------------------- #
def write_environment(path: Path) -> None:
    lines = [
        f"generated_utc: {utc_now()}",
        f"python: {platform.python_version()} ({sys.implementation.name})",
        f"platform: {platform.platform()}",
        f"machine: {platform.machine()}",
        f"processor: {platform.processor() or 'unknown'}",
        "accelerator: none (CPU-only; BM25 needs no GPU)",
        "",
        "# Package versions relevant to this baseline",
    ]
    for mod in ("numpy", "pandas", "pyarrow", "rank_bm25"):
        try:
            imported = __import__(mod)
            version = getattr(imported, "__version__", "unknown")
        except Exception:  # noqa: BLE001 - reporting only
            version = "not installed"
        lines.append(f"{mod}: {version}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_dataset_checksums(path: Path, raw_dir: Path, pin: dict) -> None:
    lines = [f"# ESCI dataset inputs, pinned at {pin['source']}@{pin['revision']}"]
    for entry in pin["files"]:
        lines.append(f"{entry['sha256'].lower()}  {entry['name']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tables(out: Path, metrics: dict, tag: str) -> tuple[Path, Path]:
    tables_dir = out / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "baseline": tag,
        "kind": "lexical-bm25",
        "learned": False,
        "note": (
            "NEW lexical BM25 baseline under the evidence contract. NOT the "
            "withdrawn historical neural NDCG/recall/F1 metrics."
        ),
        "metrics": metrics,
    }
    metrics_json = tables_dir / "metrics.json"
    metrics_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    md = [
        f"# Task 1 ranking -- {tag} (lexical BM25 baseline)",
        "",
        "NEW baseline published under the evidence contract. This is a keyword",
        "BM25 reference point, NOT the withdrawn neural NDCG/recall/F1 figures.",
        "",
        "| metric | value |",
        "|---|---|",
    ]
    for key, value in metrics.items():
        formatted = f"{value:.4f}" if isinstance(value, float) else str(value)
        md.append(f"| {key} | {formatted} |")
    metrics_md = tables_dir / "metrics.md"
    metrics_md.write_text("\n".join(md) + "\n", encoding="utf-8")
    return metrics_json, metrics_md


def write_manifest(
    out: Path,
    pin: dict,
    run_relpath: str,
    log_relpath: str,
    table_relpath: str,
    command: str,
) -> Path:
    manifest = {
        "schema_version": 1,
        "project_version": PROJECT_VERSION,
        "git_commit": git_commit(),
        "dataset": {
            "source": pin["source"],
            "revision": pin["revision"],
            "locale": pin["locale"],
            "split": pin["split"],
            "checksums_file": "dataset_checksums.txt",
        },
        "environment": {
            "python": platform.python_version(),
            "dependencies_file": "environment.txt",
            "hardware": f"CPU-only; {platform.platform()}",
        },
        "runs": [
            {
                "system": "bm25-lexical",
                "seed": 0,
                "config": "configs/pipeline.yaml",
                "predictions": run_relpath,
                "log": log_relpath,
            }
        ],
        "tables": [
            {
                "path": table_relpath,
                "generator": "scripts/run_baseline_bundle.py",
                "command": command,
            }
        ],
    }
    manifest_path = out / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def validate_manifest(manifest_path: Path) -> str:
    """Validate manifest.json against results/manifest.schema.json if possible."""
    try:
        import jsonschema
    except ImportError:
        return "schema validation SKIPPED (jsonschema not installed)"
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    instance = json.loads(manifest_path.read_text(encoding="utf-8"))
    jsonschema.validate(instance, schema)
    return "manifest.json is schema-valid against results/manifest.schema.json"


def write_sha256sums(out: Path, relpaths: list[str]) -> Path:
    lines = []
    for rel in sorted(relpaths):
        digest = sha256_file(out / rel)
        lines.append(f"{digest}  {rel}")
    sums_path = out / "SHA256SUMS"
    sums_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return sums_path


def verify_sha256sums(out: Path, sums_path: Path) -> None:
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, _, rel = line.partition("  ")
        actual = sha256_file(out / rel)
        if actual != digest:
            raise ValueError(f"SHA256SUMS self-check failed for {rel}")


# --------------------------------------------------------------------------- #
# Bundle orchestration (shared by real run and self-test)
# --------------------------------------------------------------------------- #
def build_bundle(
    grouped: dict[int, list[ESCIExample]],
    out: Path,
    pin: dict,
    command: str,
    write_full_manifest: bool,
    log: list[str],
) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    tag = "bm25"

    rankings, scored = bm25_rankings(grouped)
    metrics = evaluate_rankings(rankings, grouped, k=10, recall_k=10)
    log.append(summarize("Task 1 BM25 lexical baseline", metrics))

    run_path = out / "predictions" / "bm25.run"
    jsonl_path = out / "predictions" / "bm25.jsonl"
    write_run_file(run_path, scored, tag)
    write_predictions_jsonl(jsonl_path, scored)

    metrics_json, metrics_md = write_tables(out, metrics, tag)
    write_environment(out / "environment.txt")
    write_dataset_checksums(out / "dataset_checksums.txt", out, pin)

    logs_path = out / "logs" / "run.log"
    logs_path.parent.mkdir(parents=True, exist_ok=True)
    logs_path.write_text("\n".join(log) + "\n", encoding="utf-8")

    # SHA256SUMS covers the dataset pin, the raw predictions, and the tables.
    sha_targets = [
        "dataset_checksums.txt",
        "environment.txt",
        "predictions/bm25.run",
        "predictions/bm25.jsonl",
        "tables/metrics.json",
        "tables/metrics.md",
        "logs/run.log",
    ]

    manifest_note = "manifest.json NOT written (self-test synthetic fixture is not an ESCI bundle)"
    if write_full_manifest:
        manifest_path = write_manifest(
            out,
            pin,
            run_relpath="predictions/bm25.run",
            log_relpath="logs/run.log",
            table_relpath="tables/metrics.json",
            command=command,
        )
        sha_targets.append("manifest.json")
        manifest_note = validate_manifest(manifest_path)
    log.append(manifest_note)

    # Copy the frozen-input pin into the bundle so SHA256SUMS covers it too.
    pin_copy = out / "dataset.pin.json"
    pin_copy.write_text(json.dumps(pin, indent=2) + "\n", encoding="utf-8")
    sha_targets.append("dataset.pin.json")

    sums_path = write_sha256sums(out, sha_targets)
    verify_sha256sums(out, sums_path)
    log.append(f"SHA256SUMS written and self-verified over {len(sha_targets)} files")

    return {"metrics": metrics, "out": str(out), "manifest": manifest_note}


# --------------------------------------------------------------------------- #
# Synthetic fixture (self-test only; NOT ESCI, NOT a benchmark)
# --------------------------------------------------------------------------- #
def synthetic_grouped() -> dict[int, list[ESCIExample]]:
    """Tiny hand-built ESCI-schema fixture to exercise the full code path.

    This is a harness self-test only. It is synthetic data, it is NOT the
    Amazon ESCI dataset, and its metric is NOT an ESCI benchmark number.
    """
    rows = [
        (1, "wireless mouse", "p-mouse-wl", "logitech wireless optical mouse usb", "E"),
        (1, "wireless mouse", "p-mouse-wd", "generic wired usb mouse", "S"),
        (1, "wireless mouse", "p-keyboard", "mechanical gaming keyboard rgb", "I"),
        (2, "laptop stand aluminum", "p-stand-al", "aluminum laptop stand adjustable", "E"),
        (2, "laptop stand aluminum", "p-stand-pl", "plastic laptop riser stand", "S"),
        (2, "laptop stand aluminum", "p-usb-hub", "usb c hub multiport adapter", "I"),
    ]
    examples = [
        ESCIExample(
            query_id=qid,
            query=query,
            product_id=pid,
            product_text=text,
            label=label,
            split="test",
        )
        for qid, query, pid, text, label in rows
    ]
    return group_by_query(examples)


def synthetic_pin() -> dict:
    return {
        "source": "file://synthetic-self-test",
        "revision": "synthetic-self-test",
        "subdir": "",
        "locale": "us",
        "task": "task1_ranking",
        "version_column": "small_version",
        "split": "test",
        "note": "SYNTHETIC harness self-test fixture. NOT the Amazon ESCI dataset.",
        "files": [],
    }


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def run_real(args: argparse.Namespace) -> int:
    pin = load_pin(Path(args.pin))
    raw_dir = Path(args.raw_dir)
    out = Path(args.out)

    print(f"[pin ] {pin['source']}@{pin['revision']} locale={pin['locale']} "
          f"split={pin['split']} task={pin.get('task')}")

    ok, messages = verify_inputs(raw_dir, pin)
    for message in messages:
        print(f"[data] {message}")
    if not ok:
        print("\n[status] INPUTS NOT VERIFIED -- baseline not run.")
        print(fetch_hint(pin, raw_dir))
        return 2

    print("[load] loading Task 1 ranking subset (small_version, official split) ...")
    examples = load_esci(raw_dir, pin["locale"], task=pin["task"])
    _, test = train_test_split(examples)
    grouped = group_by_query(test)
    print(f"[load] {len(grouped)} test queries / {len(test)} judged candidates")

    command = (
        f"python scripts/run_baseline_bundle.py --pin {args.pin} "
        f"--raw-dir {args.raw_dir} --out {args.out}"
    )
    log: list[str] = [f"generated_utc: {utc_now()}", f"command: {command}"]
    result = build_bundle(grouped, out, pin, command, write_full_manifest=True, log=log)

    print("\n" + summarize("Task 1 BM25 lexical baseline", result["metrics"]))
    print(f"\n[manifest] {result['manifest']}")
    print(f"[done] bundle written to {out}")
    print("[honesty] NEW lexical BM25 baseline under the evidence contract; "
          "NOT the withdrawn neural metrics.")
    return 0


def run_self_test(args: argparse.Namespace) -> int:
    out = Path(args.out) if args.out else (REPO_ROOT / "build" / "harness-selftest")
    grouped = synthetic_grouped()
    command = "python scripts/run_baseline_bundle.py --self-test"
    log = [f"generated_utc: {utc_now()}", "mode: SELF-TEST (synthetic fixture, not ESCI)"]
    result = build_bundle(
        grouped, out, synthetic_pin(), command, write_full_manifest=False, log=log
    )
    print("[self-test] harness ran end to end on a SYNTHETIC fixture (NOT ESCI).")
    print("[self-test] " + summarize("synthetic BM25 self-test", result["metrics"]))
    print(f"[self-test] bundle written to {out}")
    print("[self-test] " + result["manifest"])
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pin", default=str(DEFAULT_PIN), help="frozen-input pin JSON")
    parser.add_argument("--raw-dir", default="data/raw", help="dir with ESCI parquet files")
    parser.add_argument("--out", default=None, help="bundle output dir")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run the full code path over a synthetic fixture (no data, no GPU)",
    )
    args = parser.parse_args()

    if args.self_test:
        return run_self_test(args)
    if args.out is None:
        args.out = str(DEFAULT_OUT)
    return run_real(args)


if __name__ == "__main__":
    raise SystemExit(main())
