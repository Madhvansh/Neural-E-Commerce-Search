# Validate retrieval runs before computing metrics

`necs-validate` is a dependency-light structural preflight for TREC-style qrels
and run files. It is useful in CI before `trec_eval`, `pytrec_eval`, or a custom
metric script.

It detects or reports:

- malformed rows and non-finite relevance or score values;
- duplicate judgements or returned documents;
- advisory rank columns with duplicate, gapped, unusually based, or out-of-order values;
- queries present on only one side of the evaluation;
- run documents that have no judgement for their query; and
- mismatched optional `# task: ...` headers.

This is not byte-for-byte NIST input certification or benchmark certification.
A passing report does not establish dataset provenance, correct gains, model
quality, or a sound experimental design.

## Run the CLI

From a checkout:

```bash
python -m pip install -e .
necs-validate \
  --qrels examples/validation/sample.qrels \
  --run examples/validation/sample.run \
  --expected-task task1_ranking
```

Add `--format json` for machine-readable output. Query-set differences, advisory
rank anomalies, and unjudged documents are visible warnings by default. Use
`--require-query-coverage`, `--strict-ranks`, or `--require-judged` to promote
the corresponding diagnostics to errors when a fully matched evaluation
contract requires them.

The command exits with `0` when no integrity errors remain and `1` when the
report fails. Invalid command-line arguments use argparse's standard nonzero
exit. That makes the same command safe to place directly in CI.

## Compatibility defaults

The defaults follow common IR tooling instead of enforcing one exporter:

- [PyTerrier ranks begin at 0](https://pyterrier.readthedocs.io/en/stable/datamodel.html),
  so both 0-based and 1-based rank columns are accepted.
- [NIST `trec_eval` ignores the submitted rank column and orders by score](https://github.com/usnistgov/trec_eval/blob/main/get_trec_results.c),
  so duplicate, gapped, or out-of-order rank values are diagnostics unless
  `--strict-ranks` is requested. Duplicate query/document pairs remain errors.
- [`ir-measures` evaluates every qrels query and ignores run-only queries](https://ir-measur.es/en/latest/advanced.html#empty-set-behaviour),
  so query-set differences warn by default; `--require-query-coverage` provides
  a stricter matched-set contract.
- Unjudged returned documents are common with pooled qrels, so they warn by
  default; `--require-judged` is appropriate for fully judged candidate sets.
- For broader graded-retrieval compatibility, relevance values may be any
  finite numeric gain. [NIST `trec_eval` uses a narrower integer qrels contract](https://github.com/usnistgov/trec_eval/blob/main/get_qrels.c),
  so this preflight intentionally does not claim byte-for-byte parser parity.

The accepted whitespace-separated formats are:

```text
# optional metadata header
# task: task1_ranking

# qrels
query_id iteration document_id relevance

# run
query_id Q0 document_id rank score run_tag
```

## Use the GitHub Action

```yaml
name: Validate retrieval evidence
on: [push, pull_request]

jobs:
  validate-run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: Madhvansh/Neural-E-Commerce-Search@v0.3.0
        with:
          qrels: evaluation/qrels.txt
          run: evaluation/run.txt
          expected-task: task1_ranking
          # Optional strict contracts:
          # require-query-coverage: "true"
          # require-judged: "true"
          # strict-ranks: "true"
```

The action uses the runner's Python installation and the validator bundled at
the tagged revision. It does not install the project or download model assets.

If you adopt it in a public repository, share the workflow or any failure it
caught through the [validator compatibility report](https://github.com/Madhvansh/Neural-E-Commerce-Search/issues/new?template=validator_report.yml).
