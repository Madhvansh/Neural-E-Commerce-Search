# Changelog

All notable project changes should be recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and releases follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- A `trec_eval` compatibility harness under `harness/trec_eval_compat/`: a
  frozen, hash-pinned copy of NIST `trec_eval`'s shipped qrels/run test files
  and a standard-library differential runner that replays the released
  `necs-validate` structural preflight over them and regenerates raw outputs
  and a summary table. The runner takes a `--validator` command so the same
  fixtures can later be pointed at a second `trec_eval` implementation. Scope
  is a structural preflight only, not a scoring-correctness oracle.

## [0.3.1] - 2026-07-19

### Security

- Execute the Action's bundled validator by its absolute file path so a caller
  checkout cannot shadow it with a top-level `necs` package.

### Added

- Regression coverage for caller-package shadowing, empty required inputs,
  invalid boolean inputs, and the Python 3.9+ runtime contract.
- A hosted-runner Action smoke matrix covering Linux, macOS, and Windows.
- A release-asset workflow that downloads a named release's wheel, source
  distribution, and SHA-256 manifest; requires the manifest to cover exactly
  both archives; and installs and exercises them in separate clean environments
  outside the checkout.

### Changed

- Detect either `python` or `python3` at version 3.9 or newer and reject empty
  required inputs or non-boolean strictness values before validation.
- Make the package smoke job install and test the uniquely selected built wheel
  from outside the source tree.
- Label compatibility-fixture SHA-256 values by their actual LF raw-byte and
  CRLF checkout encodings.

The TREC validation semantics are unchanged from v0.3.0.

## [0.3.0] - 2026-07-19

### Added

- `necs-validate`, a dependency-light structural preflight for TREC-style qrels
  and run files with text and JSON reports.
- A reusable GitHub Action that fails CI on malformed rows, duplicate returned
  documents, and optional task metadata mismatches. Standards-compatible query
  coverage, advisory-rank, and unjudged-document diagnostics warn by default and
  each has an explicit strict mode.
- Sample evaluation files and focused validator documentation.
- Runtime validation and a published JSON Schema for remix catalogues.
- A copyable browser-result report for low-friction independent feedback.

### Changed

- Made the lightweight contributor installation the default and reserved the
  full model/data/retrieval stack for explicit full-pipeline work.

## [0.2.0] - 2026-07-19

### Added

- A dependency-free offline demo with a small synthetic catalogue.
- A no-login browser lab using real client-side MiniLM embeddings over a
  synthetic product catalogue, with model identity and scores exposed.
- Community health, citation, security, roadmap, and result-bundle guidance.
- Packaging extras for model, retrieval, data, serving, and development use.

### Changed

- Withdrew unsupported historical benchmark figures until their raw artifacts
  and multi-seed reruns are published.
- Corrected ESCI Task 1/Task 2 dataset selection, two-stage evaluation,
  full-qrels NDCG, missing-query scoring, and warm-checkpoint propagation.
- Added a clean-wheel installation smoke test and browser-lab syntax check to CI.
- Replaced the already-occupied `necs` distribution name with the candidate
  distribution name `neural-ecommerce-search-madhvansh`. PyPI's JSON endpoint
  returned `Not Found` on 2026-07-19; availability still must be checked
  immediately before any upload.

## 0.1.0

- Initial public research implementation of the ESCI retrieve-and-rank pipeline.
