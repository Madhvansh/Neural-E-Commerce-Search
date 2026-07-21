# Evidence index

This index is the shortest path for a reviewer to check what this repository
actually demonstrates. Each row pairs a public claim with the artifact that
backs it and a live URL you can open in seconds. Every link below was confirmed
reachable before publication.

## Verify every claim in 90 seconds

| Claim | Artifact | URL |
|---|---|---|
| v0.3.1 ships three assets — the wheel, the source tarball, and a SHA-256 manifest — so any install can be checksum-verified. | GitHub Release v0.3.1 | https://github.com/Madhvansh/Neural-E-Commerce-Search/releases/tag/v0.3.1 |
| The published wheel and sdist SHA-256 values are recorded in a release asset (wheel `ffb2b2f4…d4b5`). | NEURAL_V031_SHA256SUMS.txt | https://github.com/Madhvansh/Neural-E-Commerce-Search/releases/download/v0.3.1/NEURAL_V031_SHA256SUMS.txt |
| An authoritative post-publication workflow re-downloaded the released v0.3.1 assets, re-verified the SHA-256 manifest, and installed and exercised both the wheel and the sdist — green on `main`. | Actions run: Verify published release assets | https://github.com/Madhvansh/Neural-E-Commerce-Search/actions/runs/29693240862 |
| The NIST `trec_eval` project documents that `trec_eval` silently truncates non-integer relevance values — the exact error class `necs-validate` blocks before metrics run. | usnistgov/trec_eval issue #49 | https://github.com/usnistgov/trec_eval/issues/49 |
| 13 public TREC qrels/run artifacts from 11 IR repositories validated structurally: 0 errors, all PASS, each pinned to an immutable commit SHA with per-file SHA-256. | Field report (rendered) | https://madhvansh.github.io/Neural-E-Commerce-Search/validated-artifacts.html |
| The same field report in source form carries the exact fetch-and-validate commands and the full SHA-256 manifest to reproduce every row. | docs/validated-artifacts.md (audit source) | https://github.com/Madhvansh/Neural-E-Commerce-Search/blob/main/docs/validated-artifacts.md |
| Public correction of three earlier mistakes in how the preflight treated the TREC rank column, and why that column is advisory. | Discussion #13 | https://github.com/Madhvansh/Neural-E-Commerce-Search/discussions/13 |
| Open invitation to reproduce and adopt `necs-validate` in an independently owned workflow; the project states it claims no independent third-party adoption yet. | Issue #9 | https://github.com/Madhvansh/Neural-E-Commerce-Search/issues/9 |
| Maintainer-run interoperability trials of the released wheel against pinned upstream fixtures, each with machine-readable per-trial output and no adoption claim. | docs/compatibility/ | https://github.com/Madhvansh/Neural-E-Commerce-Search/tree/main/docs/compatibility |
| Historical NDCG/recall/F1 numbers stay withdrawn until a release satisfies the reproducibility checklist and result-bundle contract. | docs/reproducibility.md | https://github.com/Madhvansh/Neural-E-Commerce-Search/blob/main/docs/reproducibility.md |
| CI runs the unit suite and Ruff on Python 3.9–3.14 (Ubuntu) and smoke-tests the packaged Action on Ubuntu, macOS, and Windows. | .github/workflows/ci.yml | https://github.com/Madhvansh/Neural-E-Commerce-Search/actions/workflows/ci.yml |
| Drop-in TREC qrels/run validation running the exact v0.3.1 wheel client-side through Pyodide; files never leave the browser. | Browser validator (validate.html) | https://madhvansh.github.io/Neural-E-Commerce-Search/validate.html |
| Real client-side `all-MiniLM-L6-v2` embeddings at pinned revision `751bff3` rank a synthetic catalogue with no account or backend. | Browser lab (lab.html) | https://madhvansh.github.io/Neural-E-Commerce-Search/lab.html |

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
