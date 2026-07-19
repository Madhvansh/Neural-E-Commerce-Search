# v0.3.0 compatibility trial: `RankFlow`

Status: maintainer-run upstream-fixture and API-round-trip trial, 2026-07-19.

This report checks `necs-validate` against exact public fixtures from
[`izikeros/rankflow`](https://github.com/izikeros/rankflow) and a TREC run
regenerated through its pinned API. It is not a claim of adoption, affiliation,
or endorsement by that project.

## Immutable inputs

- upstream commit:
  [`889778fd030fd4e1d1a370a1b2a465ad8d11c480`](https://github.com/izikeros/rankflow/commit/889778fd030fd4e1d1a370a1b2a465ad8d11c480)
- fixture:
  [`tests/unit/test_adapters.py`](https://github.com/izikeros/rankflow/blob/889778fd030fd4e1d1a370a1b2a465ad8d11c480/tests/unit/test_adapters.py),
  Git blob `7f8559f0b100ac714d39dc2856e546eb9f1c576e`
- adapter:
  [`src/rankflow/adapters/trec.py`](https://github.com/izikeros/rankflow/blob/889778fd030fd4e1d1a370a1b2a465ad8d11c480/src/rankflow/adapters/trec.py),
  Git blob `6d0b6a4846e9bf7ff06177c661eefb9c4bdb443b`
- raw fixture SHA-256 (Git blob bytes with LF line endings):
  `f5293313ebb9630b133acb52624c5aca5bce80936fc21a2e21a6c65011448ff5`
- Windows checkout SHA-256 (CRLF line endings used for this trial):
  `16f1648c8f8717b467a54921e4d55aed2a89039b95510363e7c20b24f775aae8`

A standard-library AST check extracted and byte-verified the upstream BM25,
reranker, and qrels fixture strings.

## Exact API round trip

Pinned RankFlow `0.2.1` loaded the two TREC runs with
`RankFlow.from_trec_run`, selected query `q1`, and wrote the reranker step with
`RankFlow.to_trec_run`. The output retained document order `doc_b, doc_a,
doc_c`, used zero-based ranks `0, 1, 2`, and had SHA-256
`85c0ed4e83a43cd7cc75aed2cb7e8d0ce39f59ff6212f4e2413eb442658f8320`.

## Result

| Artifact / contract | Exit | Errors | Warnings |
|---|---:|---:|---:|
| checked-in BM25 run, default | 0 | 0 | 2 |
| checked-in reranker run, default | 0 | 0 | 2 |
| API round trip, default | 0 | 0 | 1 |
| API round trip, `--strict-ranks` | 0 | 0 | 1 |
| API round trip, full strict contract | 1 | 1 | 0 |

Every warning concerns `doc_b`, which the public runs retrieve but the public
qrels do not judge. The full strict contract deliberately promotes that same
finding to an error. There were no malformed-row, duplicate, query-coverage, or
advisory-rank diagnostics; RankFlow's zero-based ranks pass strict validation.

The machine-readable summary is saved in
[`rankflow-v030.json`](rankflow-v030.json).
