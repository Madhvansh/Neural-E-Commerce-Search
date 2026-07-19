# v0.3.0 compatibility trial: `neural-search`

Status: maintainer-run upstream-fixture trial, 2026-07-19.

This report checks `necs-validate` against an exact public fixture pair from
[`sidhulyalkar/neural-search`](https://github.com/sidhulyalkar/neural-search).
It is not a claim of adoption, affiliation, or endorsement by that project.

## Immutable inputs

- upstream commit:
  [`4498e26ecf0df7930b4643cd14afdb9ef6108895`](https://github.com/sidhulyalkar/neural-search/tree/4498e26ecf0df7930b4643cd14afdb9ef6108895)
- qrels fixture:
  [`tests/fixtures/qrels_small.jsonl`](https://github.com/sidhulyalkar/neural-search/blob/4498e26ecf0df7930b4643cd14afdb9ef6108895/tests/fixtures/qrels_small.jsonl),
  Git blob `61ff8bcc22c4313f9b7adaeb0dc1cc64d3af7aea`,
  SHA-256 `4db49e7036f050f090b2a60149e891abf785b739b2a81b37d613b68b05542a5b`
- run fixture:
  [`tests/fixtures/run_small.jsonl`](https://github.com/sidhulyalkar/neural-search/blob/4498e26ecf0df7930b4643cd14afdb9ef6108895/tests/fixtures/run_small.jsonl),
  Git blob `d3bbb9416788155e0f762c68bf1a3880138a73c2`,
  SHA-256 `9d657286e2a5944930e0a4b78c0058850112ffd552f3c7f33b157a1a51a83e16`
- validator: release
  [`v0.3.0`](https://github.com/Madhvansh/Neural-E-Commerce-Search/releases/tag/v0.3.0),
  wheel SHA-256 `0ac9bfd52427e574d7d91948cab0e8d25aef442176a23125a860320844d8a03b`

The trial used an isolated CPython 3.12 environment and imported `necs` from
the installed release wheel under `site-packages`, not from a source checkout.

## Lossless column mapping

Rows stayed in their upstream order. No label, rank, score, query id, or
document id was invented or reordered.

| Upstream JSONL | TREC-style output |
|---|---|
| qrels: `query_id`, `dataset_id`, `relevance` | `query_id 0 dataset_id relevance` |
| run: `query_id`, `record_id`, `rank`, `score` | `query_id Q0 record_id rank score neural-search-fixture` |

The converted files contained three queries, seven judgements, and eight run
entries. A verification script compared every converted column back to the
source JSON objects before validation.

## Result

| Contract | Exit | Errors | Warnings | Finding |
|---|---:|---:|---:|---|
| default | 0 | 0 | 1 | `q_smoke_001 / dandi:000010` is retrieved but unjudged |
| `--require-judged` | 1 | 1 | 0 | the same finding is promoted to an error |

The machine-readable default report is saved in
[`neural-search-v030.json`](neural-search-v030.json).

This is the intended pooled-qrels behavior: an unjudged returned document is
visible without making the default preflight unusably strict, while a fully
judged candidate-set contract can opt into failure.

## Commands

```bash
necs-validate --qrels converted.qrels --run converted.run
necs-validate --qrels converted.qrels --run converted.run --require-judged
```

If the upstream project confirms that the warning/strict split matches its
intended `.trec` export gate, that confirmation will be linked here separately.
