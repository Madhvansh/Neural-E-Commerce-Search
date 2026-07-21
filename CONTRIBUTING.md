# Contributing

Thanks for helping improve Neural E-Commerce Search. Contributions should make
the implementation easier to reproduce, evaluate, extend, or use.

## Before opening a pull request

1. Search existing issues and pull requests.
2. For a substantial change, open an issue describing the use case and proposed
   scope before implementation.
3. Keep one pull request focused on one change.
4. Add or update tests and documentation where behavior changes.
5. Report the exact commands you ran and any skipped tests.

**Test policy:** major new functionality must ship with tests, and `pytest` must
pass locally before a pull request is opened.

Good contributions include reproducible benchmark artifacts, bug fixes, dataset
or model adapters, evaluation improvements, small demo improvements, and precise
documentation corrections. Generated bulk changes, trivial activity intended to
pad contribution counts, and unrelated promotional changes will be closed.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

On Windows PowerShell, activate with `.venv\\Scripts\\Activate.ps1`.

The command above installs the lightweight package and contributor tooling used
by CI. For model training, ESCI data, FAISS retrieval, and API work, install the
full optional stack with `python -m pip install -e ".[all,dev]"`.

## Checks

```bash
ruff check src tests scripts
pytest
```

Torch-dependent tests may skip in a lightweight environment. If your change
touches model training or inference, run the relevant tests with the full
dependency stack and state the hardware and package versions in the PR.

## Benchmark changes

Benchmark pull requests must document dataset provenance, split construction,
configuration, seed, hardware, raw results, and the commit SHA. Follow
[`docs/reproducibility.md`](docs/reproducibility.md).

Do not update a benchmark table without also adding the raw inputs, manifest,
and generation command described in [`results/README.md`](results/README.md).

By participating, you agree to follow [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
