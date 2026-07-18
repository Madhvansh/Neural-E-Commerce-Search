# Evidence status

This page is the shortest path for reviewers who want to distinguish what this
repository demonstrates today from what remains research work.

## Current evidence boundary

| Surface | Current status | What it proves |
|---|---|---|
| Browser lab | Real client-side `all-MiniLM-L6-v2` embeddings at revision `751bff3` over a synthetic catalogue | The inspectable neural-retrieval interaction works without an account or project-side query logging |
| Offline demo | Deterministic, dependency-light heuristic ranking over bundled synthetic data | The package, CLI, custom-catalogue schema, and result contract work |
| Lightweight suite | 67 lightweight Python tests pass locally on Windows/Python 3.12; model-heavy optional paths are outside this count | Task-column mapping, evaluator edge cases, run integrity, mining-checkpoint selection, configuration, and demo behavior are regression-tested |
| Distribution | Package CI builds the wheel and source archive, installs the wheel in a fresh environment, and invokes both packaged CLIs | The release candidate is checked independently of the source tree |
| Run validator | `necs-validate` and the root GitHub Action preflight TREC-style qrels/run files without model dependencies | Evaluation files can be checked for structural errors and standards-aware coverage/rank diagnostics before metrics are computed |
| Learned ESCI results | No current public benchmark claim | A corrected clean training run and complete result bundle are still required |

The browser lab is intentionally not described as an ESCI benchmark or as the
project's trained two-stage pipeline. It uses a general-purpose MiniLM model,
runs entirely in the visitor's browser, and displays cosine similarity over a
small synthetic catalogue.

The lab pins Transformers.js 3.8.1 and model revision
`751bff37182d3f1213fa05d7196b954e230abad9`. A first visit fetches roughly
25 MB of quantized model assets plus the JavaScript library from Hugging Face
and jsDelivr; the project has no query backend and the query stays on-device.

## What changed in v0.3.0

The launch audit withdrew unsupported historical figures and repaired the paths
that must be correct before learned results return:

- ESCI Task 1 ranking uses `small_version`; Task 2 classification uses
  `large_version`.
- Two-stage evaluation calls the retriever first and reranks only retrieved
  candidates.
- Missing queries score zero, and ideal DCG is computed from the complete qrels.
- Hard-negative mining, the second training pass, and index construction use the
  requested trained checkpoint instead of silently reloading the base model.
- CI builds and installs the wheel in a clean environment before invoking the
  packaged CLI.

Regression tests for these boundaries live in
[`tests/test_esci_protocol.py`](tests/test_esci_protocol.py),
[`tests/test_evaluate.py`](tests/test_evaluate.py),
[`tests/test_run_eval.py`](tests/test_run_eval.py), and
[`tests/test_hard_negatives.py`](tests/test_hard_negatives.py).

The v0.3.0 release also turns the reusable integrity checks into a standalone
CLI and GitHub Action. See [`docs/validation.md`](docs/validation.md). A passing
validation report confirms file structure and evaluation coverage only; it does
not certify an experiment's scientific design or model quality.

## What a publishable learned result requires

A learned number returns to the README only when `results/<release>/` contains:

1. immutable dataset and model revisions plus SHA-256 checksums;
2. the exact task, split, locale, gains, seeds, environment, and hardware;
3. raw rankings or predictions sufficient to recompute every table;
4. per-seed metrics, failed or contradictory runs, and generation commands;
5. checkpoint hashes and a manifest that validates against
   [`results/manifest.schema.json`](results/manifest.schema.json).

The complete checklist is in
[`docs/reproducibility.md`](docs/reproducibility.md). The current empty-bundle
contract is in [`results/README.md`](results/README.md).

## How to review this release candidate

```bash
python -m pip install -e ".[dev]"
ruff check src tests scripts
pytest
python scripts/offline_demo.py --json --top-k 3
python -m build
```

For a focused review, inspect the task filters, missing-query behavior, ideal
DCG construction, retriever-before-reranker ordering, and warm-checkpoint flow.
Please open an issue with the exact command, platform, commit SHA, and observed
output when reporting a reproduction or failure.
