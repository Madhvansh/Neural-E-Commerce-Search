---
title: "Field report: 13 public TREC evaluation artifacts, structurally validated"
description: >-
  A structural validation survey of 13 public TREC qrels and run files from
  across the IR evaluation ecosystem, with pinned commit SHAs, per-file
  SHA-256, and exact reproduction commands.
---

# Field report: 13 public TREC evaluation artifacts, structurally validated

**Date:** 2026-07-21
**Validator:** `necs-validate` from `neural-ecommerce-search-madhvansh` **0.3.1**
**Wheel source:** `https://github.com/Madhvansh/Neural-E-Commerce-Search/releases/download/v0.3.1/neural_ecommerce_search_madhvansh-0.3.1-py3-none-any.whl`
**Wheel SHA-256:** `ffb2b2f42f8f08817800aaeb2c493f6b9ae2e12db93281268e9d1c351054d4b5`
**Runtime:** Python 3.14.4, isolated virtualenv, Windows 11.

This survey was run by the validator's maintainer; it demonstrates format
compatibility, not third-party adoption.

The artifacts are public qrels and run files drawn from across the IR
evaluation ecosystem: `trec_eval`'s own regression fixtures, anserini-tools,
pyserini, pyterrier, ir_measures, ranx, tevatron, TREC-RAG development data, and
QueryGym, plus two previously validated research artifacts (ikat2025 and
Rankify). Every file is fetched at a pinned commit SHA and recorded with its
SHA-256 so the survey is exactly reproducible.

---

## Method

`necs-validate` is a dependency-light **structural preflight** for TREC-style
evaluation artifacts. It checks structural integrity and evaluation coverage
before metrics are computed; it does **not** judge whether a dataset, relevance
scale, or experiment design is scientifically appropriate. All observations
below are structural only.

Severity model (validator defaults):

- **Errors** (block a PASS): malformed row / wrong column count, non-finite or
  non-numeric relevance, non-finite score, negative or non-integer rank,
  duplicate query/document judgement, duplicate run document, conflicting or
  mismatched `# task:` metadata.
- **Advisory warnings** (do not block a PASS): run query absent from qrels,
  qrels query with no run entries, run document unjudged for its query, and
  rank-column anomalies (duplicate / non-contiguous / out-of-order / unusual
  base). These are advisory because common evaluators re-sort a run by score
  and tolerate zero-scored or unjudged documents.

Procedure for every artifact:

1. Resolve the repository's head commit and **pin** to that immutable SHA.
2. Fetch each file over `raw.githubusercontent.com` at the pinned SHA.
3. Record the file **SHA-256**.
4. Validate:
   - **qrels + run pair** → `necs-validate --qrels <q> --run <r> --format json`
   - **qrels only** (no run published) → `qrels_only.py --qrels <q> --format json`,
     a thin wrapper that calls necs 0.3.1's own `parse_qrels` and reports the
     same issue codes (full source in Appendix A).

> Note on qrels-only rows: coverage and rank advisories require a run file, so a
> qrels-only structural parse legitimately emits **0 warnings** when the file is
> well-formed. This is expected, not a gap in checking.

**Scope of this report:** 13 artifacts across 11 repositories.

- Section A: 11 artifacts across 9 repositories, fetched and validated in this
  sweep (4-column qrels + optional 6-column runs).
- Section B: 2 artifacts across 2 repositories, previously validated and
  verified; their recorded results are reused here and clearly marked (not
  re-run).
- 5 additional repositories were examined during discovery but ship no
  standalone TREC-format file to fetch; they are listed for completeness under
  "Repositories examined without a fetchable TREC artifact".

---

## Results table

### A. Validated in this sweep

| # | Repository | Artifact(s) | Pinned SHA | Mode | Queries | Judgements | Errors | Warnings (breakdown) | Verdict |
|---|------------|-------------|-----------|------|--------:|-----------:|-------:|----------------------|---------|
| 1 | usnistgov/trec_eval | `test/qrels.test` + `test/results.test` | `ba38899` | pair | 3 | 3,681 | 0 | 765 (762 unjudged_document, 3 out_of_order_ranks) | PASS |
| 2 | AmenRa/ranx | `tests/unit/ranx/test_data/qrels.trec` + `run.trec` | `7363db0` | pair | 2 | 5 | 0 | 0 | PASS |
| 3 | castorini/anserini-tools | `topics-and-qrels/qrels.robust04.txt` | `1298212` | qrels-only | 249 | 311,410 | 0 | 0 | PASS |
| 4 | castorini/anserini-tools | `topics-and-qrels/qrels.beir-v1.0.0-scifact.test.txt` | `1298212` | qrels-only | 300 | 339 | 0 | 0 | PASS |
| 5 | TREC-RAG/trec-rag-data | `trec-rag-2026/development-data/rag25-dev-umbrela-qrels/rag25-climbmix-umbrela-qwen3.5-9b-v2.qrels` | `1de1b22` | qrels-only | 22 | 26,341 | 0 | 0 | PASS |
| 6 | texttron/tevatron | `examples/BrowseComp-Plus/topics-qrels/qrel_golds.txt` | `dd06310` | qrels-only | 830 | 2,407 | 0 | 0 | PASS |
| 7 | castorini/pyserini | `tests/resources/nfcorpus-qrels.tsv` | `8f6964c` | qrels-only | 5 | 234 | 0 | 0 | PASS |
| 8 | seanmacavaney/ir_measures | `tests/compat.qrels` | `64b5afd` | qrels-only | 2 | 311 | 0 | 0 | PASS |
| 9 | seanmacavaney/ir_measures | `tests/cwl.qrels` | `64b5afd` | qrels-only | 3 | 23 | 0 | 0 | PASS |
| 10 | terrier-org/pyterrier | `tests/fixtures/qrels` | `c8faed4` | qrels-only | 4 | 7 | 0 | 0 | PASS |
| 11 | ls3-lab/QueryGym | `examples/snippets/tiny_qrels.txt` | `6d2d192` | qrels-only | 2 | 3 | 0 | 0 | PASS |

### B. Previously validated (results reused, not re-run this sweep)

| # | Repository | Artifact(s) | Mode | Queries/Turns | Judgements | Errors | Warnings (breakdown) | Verdict |
|---|------------|-------------|------|--------------:|-----------:|-------:|----------------------|---------|
| 12 | irlabamsterdam/ikat2025 | `qrels-nist.trec` + `cfda-auto-3.run` | pair | 45 turns | 5,650 | 0 | 3,289 (advisory) | PASS |
| 13 | DataScienceUIBK/Rankify | FutureQueryEval qrels + BM25 run (reshaped) | pair | 148/148 aligned | 2,938 | 0 | 12,961 (unjudged_document, advisory) | PASS |

**Summary:** 13 artifacts across 11 repositories, **0 structural errors**, all
**PASS**. Every warning observed is advisory (coverage or rank-column), which is
the expected and benign class for these well-formed files.

---

## Per-repository detail and exact repro

Common setup (identical for every entry):

```bash
python -m venv venv
curl -sL -o necs.whl \
  "https://github.com/Madhvansh/Neural-E-Commerce-Search/releases/download/v0.3.1/neural_ecommerce_search_madhvansh-0.3.1-py3-none-any.whl"
# verify integrity before install
sha256sum necs.whl   # expect ffb2b2f42f8f08817800aaeb2c493f6b9ae2e12db93281268e9d1c351054d4b5
cp necs.whl neural_ecommerce_search_madhvansh-0.3.1-py3-none-any.whl
./venv/Scripts/python -m pip install ./neural_ecommerce_search_madhvansh-0.3.1-py3-none-any.whl
./venv/Scripts/python -c "import importlib.metadata as m; print(m.version('neural_ecommerce_search_madhvansh'))"  # -> 0.3.1
```

### 1. usnistgov/trec_eval  (pair)

Canonical `trec_eval` regression fixtures. `qrels.test` is 4-column TREC qrels;
`results.test` is a 6-column TREC run.

- Pinned SHA: `ba38899cbd4de0fb699b47f39b64ef1c107e4a5c`
- `test/qrels.test` — SHA-256 `6c44a070a10bfb14b123cadc597227fc63c1acec109bc6d1e5a6bc4763906698`
- `test/results.test` — SHA-256 `69019319f6cb9ce861b4ad08d90898170d3d2b27da580fb3cba59e557ff2fd20`

```bash
SHA=ba38899cbd4de0fb699b47f39b64ef1c107e4a5c
curl -sL -o qrels.test    "https://raw.githubusercontent.com/usnistgov/trec_eval/$SHA/test/qrels.test"
curl -sL -o results.test  "https://raw.githubusercontent.com/usnistgov/trec_eval/$SHA/test/results.test"
necs-validate --qrels qrels.test --run results.test --format json
```

Result: PASS. qrels 3 queries / 3,681 judgements; run 3 queries / 1,500 entries;
0 errors; 765 advisory warnings (762 `unjudged_document`, 3 `out_of_order_ranks`)
— consistent with a run whose rank column is not strictly file-ordered and whose
retrieved documents extend beyond the judged pool, both normal for scored runs.

### 2. AmenRa/ranx  (pair)

Library unit-test fixtures. `qrels.trec` is 4-column; `run.trec` is 6-column
(uses `None` as the run tag, which is a valid non-numeric tag string).

- Pinned SHA: `7363db0c35e92e90d6fa6fe73907b760678f765e`
- `tests/unit/ranx/test_data/qrels.trec` — SHA-256 `d0061fe6c53ee548e366d87a5ac4ed627ed644b8b4c3ff8c87b81894752c1df7`
- `tests/unit/ranx/test_data/run.trec` — SHA-256 `7b4f9b15558f7749d1d1535dc875803480de5f98d863ac288322152193f36114`

```bash
SHA=7363db0c35e92e90d6fa6fe73907b760678f765e
curl -sL -o ranx_qrels.trec "https://raw.githubusercontent.com/AmenRa/ranx/$SHA/tests/unit/ranx/test_data/qrels.trec"
curl -sL -o ranx_run.trec   "https://raw.githubusercontent.com/AmenRa/ranx/$SHA/tests/unit/ranx/test_data/run.trec"
necs-validate --qrels ranx_qrels.trec --run ranx_run.trec --format json
```

Result: PASS. 2 queries / 5 judgements; run 2 queries / 5 entries; 0 errors, 0
warnings — a fully judged, well-ordered miniature run.

### 3-4. castorini/anserini-tools  (qrels-only x2)

The shared topics-and-qrels resource used by Anserini/Pyserini. Both files are
4-column TREC qrels.

- Pinned SHA: `12982126736f2ed7dc45bf30acb2af9fed13c0ef`
- `topics-and-qrels/qrels.robust04.txt` — SHA-256 `f8f2c972d3c710d85daa7ead02daf4ffe2bbe3647c9f3904500182f43ddbf4c3`
- `topics-and-qrels/qrels.beir-v1.0.0-scifact.test.txt` — SHA-256 `8b7315286f8dc823956025a1fc9c9ff0bfe142d7b409458ccd758cfa0713ccba`

```bash
SHA=12982126736f2ed7dc45bf30acb2af9fed13c0ef
BASE="https://raw.githubusercontent.com/castorini/anserini-tools/$SHA/topics-and-qrels"
curl -sL -o qrels.robust04.txt                  "$BASE/qrels.robust04.txt"
curl -sL -o qrels.beir-v1.0.0-scifact.test.txt  "$BASE/qrels.beir-v1.0.0-scifact.test.txt"
python qrels_only.py --qrels qrels.robust04.txt --format json
python qrels_only.py --qrels qrels.beir-v1.0.0-scifact.test.txt --format json
```

Result: PASS both. Robust04 249 queries / 311,410 judgements; BEIR-SciFact 300
queries / 339 judgements; 0 errors, 0 warnings each. The BEIR-derived qrels ship
in genuine 4-column TREC form (not the 3-column BEIR TSV), so they parse cleanly.

### 5. TREC-RAG/trec-rag-data  (qrels-only)

TREC RAG 2026 development UMBRELA judgements. 4-column TREC qrels with graded
relevance.

- Pinned SHA: `1de1b22ac7f9936be7e42c9e70d576cc9cb83770`
- `trec-rag-2026/development-data/rag25-dev-umbrela-qrels/rag25-climbmix-umbrela-qwen3.5-9b-v2.qrels`
  — SHA-256 `7b05789905066730f99dac4e17cb292d71d4091a3762c5f12f17ce00ff4366dd`

```bash
SHA=1de1b22ac7f9936be7e42c9e70d576cc9cb83770
F="trec-rag-2026/development-data/rag25-dev-umbrela-qrels/rag25-climbmix-umbrela-qwen3.5-9b-v2.qrels"
curl -sL -o trecrag.qrels "https://raw.githubusercontent.com/TREC-RAG/trec-rag-data/$SHA/$F"
python qrels_only.py --qrels trecrag.qrels --format json
```

Result: PASS. 22 queries / 26,341 judgements; 0 errors, 0 warnings — the largest
single qrels file in the sweep by judgement density, all rows well-formed.

### 6. texttron/tevatron  (qrels-only)

BrowseComp-Plus gold judgements. 4-column TREC qrels (uses `Q0` in the iteration
column, which the parser treats as an ignored placeholder).

- Pinned SHA: `dd063104c81a76d6a77c845f667b46b9e5abd625`
- `examples/BrowseComp-Plus/topics-qrels/qrel_golds.txt` — SHA-256 `b875af4a745712bee7a94f464ed989232f8c77977c31824428470e11dcb28c73`

```bash
SHA=dd063104c81a76d6a77c845f667b46b9e5abd625
curl -sL -o tevatron_golds.txt "https://raw.githubusercontent.com/texttron/tevatron/$SHA/examples/BrowseComp-Plus/topics-qrels/qrel_golds.txt"
python qrels_only.py --qrels tevatron_golds.txt --format json
```

Result: PASS. 830 queries / 2,407 judgements; 0 errors, 0 warnings.

> Note: the sibling directory also ships `examples/ReasonIR/bright_qrels/*.tsv`,
> which are BEIR/BRIGHT-style TSV rather than 4-column TREC qrels; those were out
> of scope for the TREC-format validator and were not validated.

### 7. castorini/pyserini  (qrels-only)

Integration-test resource. Despite the `.tsv` extension, `nfcorpus-qrels.tsv` is
4-column TREC qrels (`query Q0 doc rel`).

- Pinned SHA: `8f6964c95d01980b1700381998c2448d9e6232de`
- `tests/resources/nfcorpus-qrels.tsv` — SHA-256 `93ab71e502c736b62d5a3dae823717b1aa3f643556097d535e149b4bfdde0ebb`

```bash
SHA=8f6964c95d01980b1700381998c2448d9e6232de
curl -sL -o nfcorpus-qrels.tsv "https://raw.githubusercontent.com/castorini/pyserini/$SHA/tests/resources/nfcorpus-qrels.tsv"
python qrels_only.py --qrels nfcorpus-qrels.tsv --format json
```

Result: PASS. 5 queries / 234 judgements; 0 errors, 0 warnings.

### 8-9. seanmacavaney/ir_measures  (qrels-only x2)

Test fixtures for the ir-measures library. Both are 4-column TREC qrels
(`compat.qrels` uses `Q0`, `cwl.qrels` uses `00` in the iteration column).

- Pinned SHA: `64b5afd5cd14f7d8323f9b24a1bfd12afdd1e776`
- `tests/compat.qrels` — SHA-256 `ba24dca130cde9aaeac9b94ddee447a91a3ecb8270850e7d1d81ef10a3cd1b58`
- `tests/cwl.qrels` — SHA-256 `449d42c4d4f30edc94d852323a97f73ef78b7a88f5cd10d762461f0a2dc7c537`

```bash
SHA=64b5afd5cd14f7d8323f9b24a1bfd12afdd1e776
curl -sL -o compat.qrels "https://raw.githubusercontent.com/seanmacavaney/ir_measures/$SHA/tests/compat.qrels"
curl -sL -o cwl.qrels    "https://raw.githubusercontent.com/seanmacavaney/ir_measures/$SHA/tests/cwl.qrels"
python qrels_only.py --qrels compat.qrels --format json
python qrels_only.py --qrels cwl.qrels --format json
```

Result: PASS both. compat 2 queries / 311 judgements; cwl 3 queries / 23
judgements; 0 errors, 0 warnings each.

### 10. terrier-org/pyterrier  (qrels-only)

Test fixture. `tests/fixtures/qrels` is 4-column TREC qrels.

- Pinned SHA: `c8faed4d264538298f1b5d20c0187cca55c2dfcc`
- `tests/fixtures/qrels` — SHA-256 `cf93f9250f9a86777ad7282057a6464e9a3832909e24708322b8f7bd453b094e`

```bash
SHA=c8faed4d264538298f1b5d20c0187cca55c2dfcc
curl -sL -o pyterrier_qrels "https://raw.githubusercontent.com/terrier-org/pyterrier/$SHA/tests/fixtures/qrels"
python qrels_only.py --qrels pyterrier_qrels --format json
```

Result: PASS. 4 queries / 7 judgements; 0 errors, 0 warnings.

> Note: the sibling `tests/fixtures/light_results` is a 3-column PyTerrier
> result table (`docid, docno, score`), not a 6-column TREC run, so it was not
> paired against the qrels for this validator.

### 11. ls3-lab/QueryGym  (qrels-only)

Example snippet fixture. `examples/snippets/tiny_qrels.txt` is tab-separated
4-column TREC qrels.

- Pinned SHA: `6d2d19213c7212c7940143e7b9b5f1d2af7ff47b`
- `examples/snippets/tiny_qrels.txt` — SHA-256 `d192338f40dadd0bc43a9be6146ac362d6348832f642841d9e53543e7f1eedb8`

```bash
SHA=6d2d19213c7212c7940143e7b9b5f1d2af7ff47b
curl -sL -o querygym_tiny_qrels.txt "https://raw.githubusercontent.com/ls3-lab/QueryGym/$SHA/examples/snippets/tiny_qrels.txt"
python qrels_only.py --qrels querygym_tiny_qrels.txt --format json
```

Result: PASS. 2 queries / 3 judgements; 0 errors, 0 warnings.

> Note: QueryGym's `reproducibility/data/runs/**` are JSON run objects, not
> 6-column TREC run files, so the TREC-run path did not apply.

### 12-13. Previously validated (reused)

- **irlabamsterdam/ikat2025** — `qrels-nist.trec` + `cfda-auto-3.run`, structural
  PASS: 45 turns, 5,650 judgements, 0 errors, 3,289 advisory warnings. Recorded
  in a prior verified run; not re-fetched or re-run in this sweep.
- **DataScienceUIBK/Rankify** — FutureQueryEval qrels + BM25 run (reshaped to
  6-column TREC), PASS: 148/148 aligned, 2,938 judgements, 0 errors, 12,961
  `unjudged_document` advisory warnings. Recorded in a prior verified run; not
  re-fetched or re-run in this sweep.

---

## Repositories examined without a fetchable TREC artifact

These were inspected during discovery and are recorded for transparency. None
was validated because none commits a standalone TREC-format qrels or run file
(so there is nothing to fetch or fault). This is a neutral observation about
repository layout, not a defect.

| Repository | Pinned reference | Observation |
|------------|------------------|-------------|
| capreolus-ir/trecrun | `main` | Pure Python library (`trecrun/__init__.py`); test data lives inline in `tests/test_trecrun.py`, no committed TREC file. |
| cvangysel/pytrec_eval | `master` | Python wrapper; its evaluation fixtures come from the `usnistgov/trec_eval` git submodule (already covered as entry 1), not from in-repo files. |
| oceanbase/seekx | `master` | Ships benchmark shell scripts (`bench/run_scifact.sh`) that download datasets at runtime; no qrels/run committed. |
| IRLab-UDC/eval4sim | `main` | No sample TREC qrels/run committed at the pinned head. |
| xlang-ai/BRIGHT | `main` | Benchmark data ships in HuggingFace-dataset/JSON form rather than 4-column TREC qrels; out of scope for the TREC-format validator. |

---

## Findings and disclosure policy

**No structural errors were found in any validated artifact.** Every file in
Section A parsed cleanly under necs 0.3.1 with **0 errors**; every warning
observed was advisory (coverage or rank-column) and is the expected, benign
class for well-formed judged data. The two reused prior validations (Section B)
were likewise error-free.

If a future run finds an error-level issue in a third-party artifact — for
example a malformed row, a non-finite relevance value, a duplicate judgement, or
conflicting `# task:` metadata — it will be reported privately to that
repository's maintainer before appearing here.

---

## Appendix A — `qrels_only.py` (qrels-only wrapper)

This wrapper imports necs 0.3.1's own `parse_qrels`, so qrels-only results use
the identical parser and issue codes as `necs-validate`.

```python
import argparse, json
from collections import Counter
from necs.validate import parse_qrels, ValidationIssue

def main() -> int:
    ap = argparse.ArgumentParser(description="qrels-only structural preflight (necs 0.3.1 parser)")
    ap.add_argument("--qrels", required=True)
    ap.add_argument("--format", choices=("text", "json"), default="json")
    args = ap.parse_args()

    issues: list[ValidationIssue] = []
    parsed = parse_qrels(args.qrels, issues)
    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]
    n_queries = len(parsed.judgements)
    n_judgements = sum(len(v) for v in parsed.judgements.values())
    report = {
        "ok": not errors,
        "mode": "qrels-only",
        "qrels_path": args.qrels,
        "counts": {"qrels_queries": n_queries, "qrels_judgements": n_judgements,
                   "errors": len(errors), "warnings": len(warnings)},
        "metadata": parsed.metadata,
        "issue_code_breakdown": dict(Counter(i.code for i in issues)),
        "issues": [{"severity": i.severity, "code": i.code, "message": i.message,
                    "file": i.file, "line": i.line, "query_id": i.query_id,
                    "document_id": i.document_id} for i in issues],
    }
    print(json.dumps(report, indent=2, sort_keys=True) if args.format == "json"
          else f"NECS qrels validation: {'PASS' if not errors else 'FAIL'}\n"
               f"qrels={n_queries} queries/{n_judgements} judgements\n"
               f"errors={len(errors)} warnings={len(warnings)}")
    return 0 if not errors else 1

if __name__ == "__main__":
    raise SystemExit(main())
```

## Appendix B — Artifact SHA-256 manifest

```
6c44a070a10bfb14b123cadc597227fc63c1acec109bc6d1e5a6bc4763906698  usnistgov/trec_eval        test/qrels.test
69019319f6cb9ce861b4ad08d90898170d3d2b27da580fb3cba59e557ff2fd20  usnistgov/trec_eval        test/results.test
d0061fe6c53ee548e366d87a5ac4ed627ed644b8b4c3ff8c87b81894752c1df7  AmenRa/ranx                tests/unit/ranx/test_data/qrels.trec
7b4f9b15558f7749d1d1535dc875803480de5f98d863ac288322152193f36114  AmenRa/ranx                tests/unit/ranx/test_data/run.trec
f8f2c972d3c710d85daa7ead02daf4ffe2bbe3647c9f3904500182f43ddbf4c3  castorini/anserini-tools   topics-and-qrels/qrels.robust04.txt
8b7315286f8dc823956025a1fc9c9ff0bfe142d7b409458ccd758cfa0713ccba  castorini/anserini-tools   topics-and-qrels/qrels.beir-v1.0.0-scifact.test.txt
7b05789905066730f99dac4e17cb292d71d4091a3762c5f12f17ce00ff4366dd  TREC-RAG/trec-rag-data     .../rag25-climbmix-umbrela-qwen3.5-9b-v2.qrels
b875af4a745712bee7a94f464ed989232f8c77977c31824428470e11dcb28c73  texttron/tevatron          examples/BrowseComp-Plus/topics-qrels/qrel_golds.txt
93ab71e502c736b62d5a3dae823717b1aa3f643556097d535e149b4bfdde0ebb  castorini/pyserini         tests/resources/nfcorpus-qrels.tsv
ba24dca130cde9aaeac9b94ddee447a91a3ecb8270850e7d1d81ef10a3cd1b58  seanmacavaney/ir_measures  tests/compat.qrels
449d42c4d4f30edc94d852323a97f73ef78b7a88f5cd10d762461f0a2dc7c537  seanmacavaney/ir_measures  tests/cwl.qrels
cf93f9250f9a86777ad7282057a6464e9a3832909e24708322b8f7bd453b094e  terrier-org/pyterrier      tests/fixtures/qrels
d192338f40dadd0bc43a9be6146ac362d6348832f642841d9e53543e7f1eedb8  ls3-lab/QueryGym           examples/snippets/tiny_qrels.txt
```

Wheel: `ffb2b2f42f8f08817800aaeb2c493f6b9ae2e12db93281268e9d1c351054d4b5`  neural_ecommerce_search_madhvansh-0.3.1-py3-none-any.whl

See the [validator guide](validation.md) for the full CLI, JSON output, and
strictness flags, or the [trec_eval format errors](trec-eval-format-errors.md)
reference for what each code means.
