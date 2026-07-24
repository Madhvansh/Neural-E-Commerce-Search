# trec_eval compatibility harness

A frozen fixture set plus a differential runner that exercises this project's
released structural preflight validator (`necs-validate`) over NIST
`trec_eval`'s own shipped test corpus. Everything is pinned by hash so the same
run can be repeated from a clean clone, and the same fixtures can later be
pointed at a second implementation -- for example an in-progress Rust port of
`trec_eval` -- once that exposes a compatible CLI.

## Scope and honesty boundary (read first)

- This is a **structural preflight** only. It records whether each fixture
  parses under the TREC qrels/run **column contract** the validator enforces
  (4-column qrels, 6-column run, integer relevance grades, no duplicate
  judgements or returned documents, plus advisory coverage and rank checks).
- It is **not** a scoring-correctness oracle. It computes **no** IR metrics and
  makes **no** claim about `trec_eval`'s numeric output (MAP, nDCG, P@k, ...).
  A `PASS` here means "no structural errors under this validator's contract",
  not "byte-for-byte parser parity with `trec_eval`" and not "the same score".
- Where the validator flags a file that `trec_eval` itself accepts, that is a
  documented **difference in contract**, not a defect in either tool. Two such
  cases appear on NIST's own files and are described under
  [Findings](#findings-what-the-validator-flags-on-nists-own-files).

## What is pinned

| Input | Identity |
| --- | --- |
| Corpus source | `usnistgov/trec_eval`, commit `ba38899cbd4de0fb699b47f39b64ef1c107e4a5c` (the `test/` directory) |
| Validator | `necs-validate` from `neural_ecommerce_search_madhvansh-0.3.1-py3-none-any.whl` |
| Wheel SHA-256 | `ffb2b2f42f8f08817800aaeb2c493f6b9ae2e12db93281268e9d1c351054d4b5` |
| Fixture hashes | `SHA256SUMS.txt` (one line per frozen input, LF raw bytes) |

The wheel SHA-256 is the value published in the release's
`NEURAL_V031_SHA256SUMS.txt`; verify it before installing (see
[Reproduce](#reproduce-from-a-clean-clone)). The pinned v0.3.1 CLI accepts
`--qrels`, `--run`, `--require-query-coverage`, `--require-judged`,
`--strict-ranks`, `--expected-task`, and `--format`; this harness uses the
default (non-strict) severities so coverage and rank anomalies stay warnings.

## Corpus inventory

The frozen fixtures under `fixtures/` are the qrels-format and run-format files
from the `trec_eval` `test/` directory, classified by inspecting their content.
Sizes are the raw LF byte counts frozen here.

### Qrels-format (`query_id  iteration  document_id  relevance`)

| File | Bytes | Notes |
| --- | --- | --- |
| `qrels.test` | 75,042 | Canonical 3-topic qrels (301/303/...); all judgements distinct. |
| `qrels-302.test` | 21,632 | Single-topic (302) qrels. |
| `qrels.comment.test` | 345,780 | MS MARCO v2.1-style ids and graded relevance. |
| `qrels.123` | 212,159 | Judgements repeated across iteration values 0/1/2. |
| `qrels.comments.123` | 212,215 | As `qrels.123`, with additional non-metadata `#` comment lines. |
| `qrels.rel_level` | 75,346 | Relevance-level variant of `qrels.test`. |
| `qrels.test.with-comments` | 75,096 | `qrels.test` with a leading `#` comment line. |

### Run-format (`query_id  Q0  document_id  rank  score  run_tag`)

| File | Bytes | Notes |
| --- | --- | --- |
| `results.test` | 65,490 | Canonical run over the `qrels.test` topics. |
| `results-302.test` | 21,874 | Single-topic (302) run. |
| `results.comment.test` | 2,793,605 | MS MARCO v2.1-style run matching `qrels.comment.test`. |
| `results.trunc` | 25,274 | Truncated/reordered run; 5 rows carry trailing free text. |

### Present in the corpus but out of scope (not frozen)

The `test/` directory also ships files that are **not** TREC qrels or run files
and therefore fall outside the qrels/run contract this preflight validates:

- Preference-format fixtures: `prefs.test`, `prefs.comment.test`,
  `prefs.rank20`, and `prefs.results.test`. (`prefs.results.test` is itself
  6-column run-format, but its companion judgements `prefs.test` are
  preference-format, not TREC qrels, so the pair is not a qrels/run pair.)
- `zscores_file` -- per-measure z-score normalisation input.
- `out.test`, `out.comment.test`, `out.test.a`, `out.test.aq*`, ... --
  **expected `trec_eval` stdout**, i.e. outputs, not inputs.
- `decorate-run.py`, `make_zscore_file.py` -- helper scripts.

These are noted for completeness and deliberately excluded from the fixture set.

## What the runner does

`necs-validate` requires a qrels file **and** a run file on every invocation, so
the smallest unit it accepts is a (qrels, run) pair. `run.py` runs a fixed set
of eight pairs that together exercise every frozen qrels fixture and every
frozen run fixture at least once, captures each raw text report to
`results/<label>.txt`, and writes `results/summary.md`.

| # | Qrels fixture | Run fixture | Purpose |
| --- | --- | --- | --- |
| 1 | `qrels.test` | `results.test` | Canonical multi-topic regression pair. |
| 2 | `qrels-302.test` | `results-302.test` | Single-topic (302) matched pair. |
| 3 | `qrels.comment.test` | `results.comment.test` | MS MARCO-style graded pair. |
| 4 | `qrels.123` | `results.test` | Repeated-iteration qrels vs canonical run. |
| 5 | `qrels.comments.123` | `results.test` | Repeated-iteration qrels with `#` comments. |
| 6 | `qrels.rel_level` | `results.test` | Relevance-level qrels vs canonical run. |
| 7 | `qrels.test.with-comments` | `results.test` | Commented qrels vs canonical run. |
| 8 | `qrels.test` | `results.trunc` | Canonical qrels vs trailing-text run. |

See [`results/summary.md`](results/summary.md) for the verdict, error count,
warning count, and notable issue codes per pair.

## Findings: what the validator flags on NIST's own files

Of the eight pairs, five `PASS` and three `FAIL`. Both failure modes are
genuine properties of the NIST fixtures, verified independently of the
validator:

1. **`qrels.123` and `qrels.comments.123` -> `duplicate_judgement`
   (6,629 and 6,628 errors).** These files record the same `(query, document)`
   judgement under several iteration-column values (0, 1, 2 observed; e.g. topic
   301 / `CR93E-10279` appears three times). The TREC qrels contract keys a
   judgement on `(query_id, document_id)` and ignores the iteration column --
   which is exactly what `trec_eval` does too -- so each repeat is a duplicate
   of an earlier judgement. Of `qrels.123`'s 10,362 data rows, 6,629 duplicate
   an earlier `(query, document)` pair. The validator treats a duplicate
   judgement as a hard error.

2. **`results.trunc` -> `malformed_row` (5 errors).** Five of its 584 data rows
   carry trailing free text (the sentence "... more junk at end of lines /
   reserved for future expansion" split across five rows), giving 7-9
   whitespace-separated columns instead of 6. `trec_eval` reads only the first
   six fields per line and ignores the rest, so it accepts this file; the
   structural preflight requires **exactly** six columns and rejects those five
   rows. This is a deliberate difference in contract -- strict column count vs
   leading-fields parsing -- not a defect in either tool.

The remaining warnings across all pairs (`unjudged_document`, `unknown_query`,
`missing_query`, `out_of_order_ranks`, `non_contiguous_ranks`,
`unusual_rank_base`) are **advisory** at the default severities: pooled qrels
leave many returned documents unjudged, and `trec_eval` orders a run by score
rather than by the submitted rank column, so these do not fail the preflight.

## Reproduce from a clean clone

From the repository root. Commands are POSIX shell; on Windows use Git Bash or
the PowerShell equivalents.

```bash
# 1. Verify the frozen fixtures are intact.
cd harness/trec_eval_compat
sha256sum -c SHA256SUMS.txt

# 2. (Optional) Re-derive the fixtures from upstream to confirm provenance.
git clone https://github.com/usnistgov/trec_eval /tmp/trec_eval
git -C /tmp/trec_eval rev-parse HEAD   # expect ba38899cbd4de0fb699b47f39b64ef1c107e4a5c
#   Note: read the pristine LF bytes, e.g.
#   git -C /tmp/trec_eval show HEAD:test/qrels.test | sha256sum

# 3. Download and verify the released wheel, then install it in a clean venv.
gh release download v0.3.1 --repo Madhvansh/Neural-E-Commerce-Search \
  --pattern 'neural_ecommerce_search_madhvansh-0.3.1-py3-none-any.whl' \
  --pattern 'NEURAL_V031_SHA256SUMS.txt'
grep 'py3-none-any.whl' NEURAL_V031_SHA256SUMS.txt | sha256sum -c -
python -m venv .venv
. .venv/bin/activate        # Windows: . .venv/Scripts/activate
pip install neural_ecommerce_search_madhvansh-0.3.1-py3-none-any.whl

# 4. Regenerate results/ and results/summary.md with the reference validator.
python run.py --impl necs-0.3.1
```

Step 4 rewrites the committed `results/` outputs in place; they should match
byte-for-byte (the outputs use LF endings and echo only bare fixture filenames,
so they are platform-independent). The `--impl necs-0.3.1` label is the stamp
carried by the committed artifacts.

## Second implementation slot

The harness is built for two implementations. `run.py` takes a `--validator`
command and an `--impl` label, so pointing it at a different `trec_eval`
implementation is a one-liner. A second implementation only needs a CLI that
accepts `--qrels PATH --run PATH` and prints the same text report shape
(`NECS run validation: PASS|FAIL`, an `errors=N warnings=M` line, and
`[SEVERITY] code ...` issue lines).

```bash
# Reference validator (default): writes results/ stamped "necs".
python run.py

# A second implementation, e.g. an in-progress Rust port of trec_eval:
python run.py \
  --validator /path/to/rust-trec-eval-validate \
  --impl rustport \
  --out results_rustport

# Then diff the two summaries to see where the contracts agree or diverge:
diff results/summary.md results_rustport/summary.md
```

`--validator` is split on spaces, so multi-token entry points work
(`--validator "python -m necs.validate"`). Divergence is the signal: a pair
that one implementation passes and the other fails is a concrete,
reproducible compatibility difference to investigate.

## Directory layout

```
harness/trec_eval_compat/
  README.md          this file
  run.py             stdlib-only differential runner
  SHA256SUMS.txt     SHA-256 of every frozen input (LF raw bytes)
  .gitattributes     freezes fixtures/ and results/ bytes across platforms
  fixtures/          frozen NIST trec_eval test files (qrels + run only)
  results/           raw validator output per pair + summary.md
```

## Provenance and license

The files under `fixtures/` are copied verbatim (pristine LF bytes) from the
`test/` directory of `usnistgov/trec_eval` at commit
`ba38899cbd4de0fb699b47f39b64ef1c107e4a5c`. `trec_eval` is a work of the U.S.
National Institute of Standards and Technology; as a U.S. Government work its
source is not subject to copyright within the United States. The fixtures are
reproduced here unmodified for reproducible compatibility testing.
