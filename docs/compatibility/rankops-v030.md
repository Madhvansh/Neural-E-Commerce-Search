# v0.3.0 compatibility trial: `rankops`

Status: maintainer-run upstream-fixture trial, 2026-07-19.

This report checks `necs-validate` against the exact qrels/run constants in
[`arclabs561/rankops`](https://github.com/arclabs561/rankops). It is not a claim
of adoption, affiliation, or endorsement by that project.

## Immutable inputs

- upstream commit:
  [`d2c7140e3dd46e940c2dd773d08a1c0dbe616b77`](https://github.com/arclabs561/rankops/commit/d2c7140e3dd46e940c2dd773d08a1c0dbe616b77)
- fixture:
  [`examples/trec_eval.rs`](https://github.com/arclabs561/rankops/blob/d2c7140e3dd46e940c2dd773d08a1c0dbe616b77/examples/trec_eval.rs)
- fixture Git blob: `ee6803d7786596aae2e9d5b1c5dd0435db902c10`
- fixture SHA-256: `bacde45fa7b2bc480308b92b67472ea5b5bfa806192bf5bdf45f620c4038d0cc`
- extracted qrels SHA-256: `a4678de7c675f22209f37d8421a7a5f725b6cc5218fe9e8ff6853a45486723a0`
- extracted run SHA-256: `409564c94a8766b0ce786d441796ece34c617d212811a8d5aacfca125b41362e`

A verification script extracted the two Rust string constants from the clean
pinned checkout and byte-compared them with the trial inputs.

## Result

| Contract | Exit | Errors | Warnings |
|---|---:|---:|---:|
| default | 0 | 0 | 0 |
| `--require-query-coverage --require-judged --strict-ranks` | 0 | 0 | 0 |

The trial found no format, duplicate, coverage, judgement, or advisory-rank
conflict in this published pair. The machine-readable summary is saved in
[`rankops-v030.json`](rankops-v030.json).
