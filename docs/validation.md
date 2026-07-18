# Validate retrieval runs before computing metrics

`necs-validate` is a dependency-light integrity check for standard TREC-style
qrels and run files. It is useful in CI before `trec_eval`, `pytrec_eval`, or a
custom metric script.

It detects:

- malformed rows and non-finite relevance or score values;
- duplicate judgements, returned documents, or ranks;
- ranks that do not form a contiguous sequence from 1;
- queries present on only one side of the evaluation;
- run documents that have no judgement for their query; and
- mismatched optional `# task: ...` headers.

This is a structural validator, not a benchmark certification. A passing report
does not establish dataset provenance, correct gains, model quality, or a sound
experimental design.

## Run the CLI

From a checkout:

```bash
python -m pip install -e .
necs-validate \
  --qrels examples/validation/sample.qrels \
  --run examples/validation/sample.run \
  --expected-task task1_ranking
```

Add `--format json` for machine-readable output. By default, missing queries and
unjudged returned documents fail validation. Use `--allow-missing-queries` or
`--allow-unjudged` only when that behavior is intentional; the conditions will
remain visible as warnings.

The command exits with `0` when no integrity errors remain and `1` when the
report fails. Invalid command-line arguments use argparse's standard nonzero
exit. That makes the same command safe to place directly in CI.

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
```

The action uses the runner's Python installation and the validator bundled at
the tagged revision. It does not install the project or download model assets.

If you adopt it in a public repository, share the workflow or any failure it
caught in the [validator adoption issue](https://github.com/Madhvansh/Neural-E-Commerce-Search/issues/8).
