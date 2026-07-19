# v0.3.0 retrieval-tooling compatibility matrix

Status: maintainer-run upstream-fixture trials, 2026-07-19.

These trials exercise the released `necs-validate` wheel against exact public
artifacts pinned to immutable upstream commits. They test interoperability; they
do not claim adoption, affiliation, or endorsement by the upstream projects.

All trials installed the public
[`v0.3.0` wheel](https://github.com/Madhvansh/Neural-E-Commerce-Search/releases/tag/v0.3.0)
in an isolated CPython 3.12 environment. Its verified SHA-256 is
`0ac9bfd52427e574d7d91948cab0e8d25aef442176a23125a860320844d8a03b`.

| Upstream artifact | Default result | Strict result | Detailed provenance |
|---|---|---|---|
| `sidhulyalkar/neural-search` exact qrels/run fixtures | PASS; one retrieved-but-unjudged warning | `--require-judged` promotes the same finding to an expected error | [report](neural-search-v030.md) |
| `arclabs561/rankops` exact Rust qrels/run constants | PASS; no warnings | coverage + judged-only + strict ranks all PASS | [report](rankops-v030.md) |
| `izikeros/rankflow` exact fixtures and API round trip | PASS; sparse-qrels warnings only | zero-based ranks PASS `--strict-ranks`; judged-only mode finds the known unjudged document | [report](rankflow-v030.md) |

Across the three trials, no malformed-row, duplicate, query-coverage, or
advisory-rank incompatibility was found. The observed strict failures were
deliberate promotions of authentic sparse-qrels findings, not parser failures.

The separate
[maintainer-owned reference consumer](https://github.com/Madhvansh/necs-validator-example/actions/workflows/validate.yml)
proves that `Madhvansh/Neural-E-Commerce-Search@v0.3.0` also runs from another
repository's default branch. It is explicitly not counted as independent
adoption.
