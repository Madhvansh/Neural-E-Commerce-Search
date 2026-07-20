---
title: Neural E-Commerce Search
---

# Neural E-Commerce Search

Neural E-Commerce Search is an alpha research implementation of a two-stage
product-search pipeline on the Amazon ESCI benchmark.

```text
query -> bi-encoder -> candidate set -> DeBERTa cross-encoder -> ranked ESCI labels
```

## Try neural retrieval in the browser

The [NECS Browser Lab](lab.html) runs a public MiniLM encoder through
Transformers.js and ranks a small synthetic product catalogue entirely on the
visitor's device. It needs no account or local environment and makes its model,
scores, and evidence boundary visible.

The lab is a real dense-retrieval demonstration, but it is not the repository's
unreleased ESCI-trained bi-encoder/cross-encoder pipeline and does not reproduce
historical benchmark figures.

## Validate a run in the browser

The [in-browser run validator](validate.html) runs the exact v0.3.1
`necs-validate` release wheel client-side through Pyodide. Drop a TREC-style
qrels and run file — or load a bundled valid/broken example — for a pass/warn/fail
report with no install, no server, and no uploads. It is the same structural
preflight as the [`necs-validate` CLI](validation.md), made click-to-run.

## Start without data or models

From a source checkout, run the deterministic synthetic demo:

```bash
python scripts/offline_demo.py --query "wireless gaming mouse"
```

It demonstrates the output contract with transparent heuristics. It does not
run the neural models and is not benchmark evidence.

## Evidence status

The code, configs, lightweight tests, browser retriever, and offline demo are
public. ESCI-trained project weights, full raw benchmark artifacts, multi-seed
reruns, and a hosted end-to-end reranker are not yet published. Historical
metrics are withdrawn pending a corrected rerun. Read [Experiments](experiments.md) and
[Reproducibility](reproducibility.md) before citing them.

## Documentation

- [Architecture](architecture.md): two-stage design and module map
- [Data](data.md): ESCI taxonomy, provenance, and preprocessing
- [Training](training.md): training workflow and configuration
- [Experiments](experiments.md): evidence status and rerun plan
- [Reproducibility](reproducibility.md): publication checklist
- [Deployment](deployment.md): serving and operational caveats
- [Browser lab](lab.html): client-side MiniLM retrieval demo
- [Browser validator](validate.html): drop-in TREC run validation via Pyodide
- [trec_eval format errors](trec-eval-format-errors.md): common TREC qrels/run format mistakes and how they are reported
- [Releasing](releasing.md): package and release safety checks

## Links

- [Source code](https://github.com/Madhvansh/Neural-E-Commerce-Search)
- [Roadmap](https://github.com/Madhvansh/Neural-E-Commerce-Search/blob/main/ROADMAP.md)
- [Contributing](https://github.com/Madhvansh/Neural-E-Commerce-Search/blob/main/CONTRIBUTING.md)

MIT licensed. Built on the
[Amazon ESCI benchmark](https://github.com/amazon-science/esci-data)
(Reddy et al., 2022).
