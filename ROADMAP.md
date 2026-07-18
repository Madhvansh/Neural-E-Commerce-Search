# Roadmap

This roadmap is ordered by evidence and user value, not by promotional metrics.
Items move to complete only when the linked code, test, or artifact is public.

## 1. Establish a trustworthy baseline

- [x] Mark legacy headline figures as preliminary.
- [x] Provide an offline, no-model demo of the output contract.
- [x] Provide a no-login browser lab with real general-purpose neural embeddings
      and an explicit boundary from the unreleased ESCI-trained pipeline.
- [x] Add contribution, security, citation, and issue-reporting guidance.
- [ ] Publish the exact ESCI source revision and file checksums.
- [ ] Add an environment lock for each supported training profile.
- [ ] Re-run BM25 from a clean checkout and publish its raw run file.

## 2. Reproduce learned-system results

- [ ] Run the bi-encoder and reranker with at least three independent seeds.
- [ ] Publish immutable configs, raw predictions, logs, checkpoint hashes, and
      hardware/runtime metadata for every run.
- [ ] Generate all README tables from committed result bundles.
- [ ] Add confidence intervals and document statistical methodology.
- [ ] Have an independent contributor reproduce one complete run.

## 3. Make the project easy to evaluate

- [ ] Publish versioned model weights with model cards and license metadata.
- [ ] Launch a CPU-capable, no-login comparison demo for BM25, dense retrieval,
      and reranking.
- [ ] Add a small, legally redistributable evaluation fixture to CI.
- [ ] Publish latency and resource measurements with exact hardware context.

## 4. Grow through real use

- [ ] Document one downstream integration from setup through evaluation.
- [ ] Add adapters only in response to concrete user or contributor needs.
- [ ] Maintain a triaged set of scoped `good first issue` tasks.
- [ ] Publish release notes that distinguish shipped work from planned work.

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution expectations and
[results/README.md](results/README.md) for the evidence contract.
