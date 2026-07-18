# Changelog

All notable project changes should be recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and releases follow
[Semantic Versioning](https://semver.org/).

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
