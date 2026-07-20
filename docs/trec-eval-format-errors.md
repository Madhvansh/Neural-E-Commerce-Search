---
title: trec_eval format errors explained
description: >-
  A reference for the common TREC qrels and run format errors, what trec_eval
  and downstream tools do with each, and the exact code necs-validate reports.
---

# trec_eval format errors explained

TREC-style evaluation reads two whitespace-separated text files: a **qrels**
file of relevance judgements and a **run** file of ranked results. `trec_eval`,
`pytrec_eval`, `ir-measures`, and PyTerrier all consume these formats, and small
structural mistakes are a frequent cause of wrong scores or a hard abort. The
failure is often silent: the tool computes a number from corrupted input instead
of refusing it.

This page catalogues the format errors that most often break TREC evaluation.
For each one it states what evaluators actually do with the input, gives a
minimal broken example and its fix, and names the exact code and severity that
[`necs-validate`](validation.md) v0.3.1 reports. The codes and messages below are
taken from the v0.3.1 validator source, and the browser validator runs that same
release wheel, so its findings use the same names.

## The two formats

```text
# qrels: one judgement per line, 4 columns
query_id   iteration   document_id   relevance

# run: one retrieved document per line, 6 columns
query_id   Q0   document_id   rank   score   run_tag
```

- **qrels** has 4 columns. `iteration` is an unused historical field,
  conventionally written as `0`.
- **run** has 6 columns. The second column is conventionally the literal `Q0`
  (another historical iteration field); evaluators ignore its value but require
  the column to be present so the remaining columns align.

Columns are separated by any run of whitespace (spaces or tabs). Lines that are
blank or begin with `#` are treated as comments or `key: value` metadata, not
data rows.

## How to read necs-validate output

Every finding has a **severity** (`error` or `warning`) and a stable **code**.
The CLI prints a `PASS`/`FAIL` header and one line per finding, then exits `0`
when no errors remain and `1` otherwise, so it can sit in CI ahead of the metric
step:

```text
[SEVERITY] code (file, line N): query=<qid> document=<docid> message
```

Coverage, rank-order, and unjudged findings are **warnings by default** because
they are legitimate in common workflows (pooled judgements, score-ordered runs,
partial query sets). They promote to errors with `--require-query-coverage`,
`--strict-ranks`, and `--require-judged`. Non-integer relevance is the reverse:
an **error by default**, demoted to a warning with `--allow-float-grades`.

This is a structural preflight, not byte-for-byte parser certification. A clean
report means the files are structurally consistent, not that the dataset,
relevance scale, or experiment design is correct.

---

## Wrong column counts

A row with too few or too many fields is the most common corruption: a title
with an unquoted space, a stray tab, a missing field, or a run file pasted where
a qrels file was expected.

**What evaluators do.** `trec_eval` parses each line with a fixed field count (4
for qrels, 6 for a run). A row with the wrong number of fields either aborts the
run with a format error or shifts every later column, so `document_id` is read
as the relevance grade and the score is read from the wrong place. Either way the
resulting metrics are meaningless.

Broken run (5 columns — the score is missing):

```text
q1 Q0 d1 1 run1
```

Fixed:

```text
q1 Q0 d1 1 12.5 run1
```

**necs-validate:** `malformed_row` (error). The offending row is skipped and
reported; if no valid rows survive, `empty_qrels` or `empty_run` (error) is added.

```text
[ERROR] malformed_row (run.txt, line 1): Expected 6 whitespace-separated columns, found 5
```

## Missing Q0 in a run file

The run format's second column is conventionally the literal `Q0`. It is a
leftover iteration field and its value carries no meaning, but dropping the
column entirely leaves five fields and misaligns everything after it.

**What evaluators do.** `trec_eval` ignores the *content* of this column, so
`Q0`, `0`, or any token is accepted as long as the column is present. Omitting it
reduces the line to five fields and triggers the same parse failure as any other
wrong column count.

Broken (no `Q0` column):

```text
q1 d1 1 12.5 run1
```

Fixed:

```text
q1 Q0 d1 1 12.5 run1
```

**necs-validate:** reported as `malformed_row` (error) — it enforces the six-column
count but, like `trec_eval`, does not require the literal string `Q0` in that
position. A present-but-unconventional value such as `0` passes silently.

```text
[ERROR] malformed_row (run.txt, line 1): Expected 6 whitespace-separated columns, found 5
```

## Non-numeric or negative ranks and scores

The run file's `rank` must be a non-negative integer and `score` must be a finite
number. Exports occasionally emit `NaN`, `inf`, an empty field, a thousands
separator, or a rank of `-1` for a placeholder.

**What evaluators do.** `trec_eval` orders each query's documents by descending
score and ignores the submitted rank, but it still parses `score` as a float; a
non-numeric or non-finite score makes the line unreadable and aborts the run.
`NaN` scores are especially dangerous because they sort unpredictably.

Broken run (row 1 has a non-numeric rank, row 2 a non-numeric score):

```text
q1 Q0 d1 x 12.5 run1
q1 Q0 d2 2 high run1
```

Fixed:

```text
q1 Q0 d1 1 12.5 run1
q1 Q0 d2 2 11.0 run1
```

**necs-validate:** `invalid_rank` (error) when the rank is not a non-negative
integer, and `invalid_score` (error) when the score is not a finite number. Each
bad row is skipped at its first failure — rank is checked before score, so a row
with both problems reports only `invalid_rank`. These are hard errors even though
the rank value is otherwise advisory (see rank-order anomalies below), because an
unparseable field signals a malformed export.

```text
[ERROR] invalid_rank (run.txt, line 1): query=q1 document=d1 Rank must be a non-negative integer, found 'x'
[ERROR] invalid_score (run.txt, line 2): query=q1 document=d2 Score must be a finite number, found 'high'
```

## Duplicate query/document pairs

The same `query_id`/`document_id` pair should appear once in the qrels and once
in a run. Duplicates usually come from concatenating shards or re-running an
export without truncating the file.

**What evaluators do.** A repeated qrels pair is ambiguous: which relevance grade
wins depends on the reader's load order. A repeated document in a run inflates the
ranked list and can be counted twice toward recall or gain. Different tools keep
the first, keep the last, or raise, so the same files can score differently across
evaluators.

Broken qrels (`d1` judged twice for `q1`):

```text
q1 0 d1 1
q1 0 d1 0
```

Fixed (one judgement per pair):

```text
q1 0 d1 1
```

**necs-validate:** `duplicate_judgement` (error) in qrels and
`duplicate_run_document` (error) in a run. The first occurrence is kept and each
later one is reported.

```text
[ERROR] duplicate_judgement (qrels.txt, line 2): query=q1 document=d1 The same query/document pair appears more than once in qrels
[ERROR] duplicate_run_document (run.txt, line 2): query=q1 document=d1 The same document appears more than once for this query
```

## Unjudged documents

A run may return documents that have no judgement in the qrels for that query.

**What evaluators do.** `trec_eval` treats an unjudged document as non-relevant
(grade `0`) by default. With pooled qrels this is expected and correct — most
returned documents were never judged. It becomes a problem only when you intend a
fully judged candidate set, where an unjudged document means a missing judgement
rather than a true negative.

Broken only under a fully-judged contract — run returns `d9`, which qrels never
judges for `q1`:

```text
# qrels
q1 0 d1 1

# run
q1 Q0 d9 1 12.5 run1
```

Fixed (judge every returned document, or accept the pooling default):

```text
# qrels
q1 0 d1 1
q1 0 d9 0
```

**necs-validate:** `unjudged_document` (warning by default; error with
`--require-judged`). Reported only for queries present in both files.

```text
[WARNING] unjudged_document: query=q1 document=d9 Run document has no judgement for this query
```

## Missing queries on one side

The qrels and run query sets often differ: a run omits a query, or returns
results for a query the qrels never judged.

**What evaluators do.** Most tools average over the qrels query set, so a qrels
query with no run rows scores zero and silently lowers the mean, while a run query
absent from the qrels is ignored entirely. Because the mean still prints, a
truncated run is easy to miss.

Broken — qrels judges `q1` and `q2`, the run only answers `q1` and also returns an
unrelated `q3`:

```text
# qrels
q1 0 d1 1
q2 0 d2 1

# run
q1 Q0 d1 1 12.5 run1
q3 Q0 d3 1 9.0 run1
```

Fixed (answer every judged query; drop or judge the extra one):

```text
# run
q1 Q0 d1 1 12.5 run1
q2 Q0 d2 1 11.0 run1
```

**necs-validate:** `missing_query` (warning) for a qrels query with no run
entries, and `unknown_query` (warning) for a run query absent from the qrels.
Both promote to errors with `--require-query-coverage`.

```text
[WARNING] missing_query: query=q2 Qrels query has no run entries and should receive a zero score
[WARNING] unknown_query: query=q3 Run query is absent from qrels and is ignored by common evaluators
```

## Rank-order anomalies

The run `rank` column can be internally inconsistent: duplicate ranks, a base
other than 0 or 1, gaps, or an order that disagrees with the file order.

**What evaluators do.** `trec_eval` ignores the rank column and re-sorts each
query by descending score (ties broken by document id), so these anomalies do not
change its metrics. They still matter as a signal: they usually mean a tool wrote
ranks but left the score column constant, or exported rows out of order, which can
break other consumers that *do* trust the rank.

Broken run for `q1` — duplicated rank `1`, and rows written out of order:

```text
q1 Q0 d1 2 8.0 run1
q1 Q0 d2 1 9.0 run1
q1 Q0 d3 1 7.0 run1
```

Fixed (contiguous ranks in ascending file order, consistent with the scores):

```text
q1 Q0 d2 1 9.0 run1
q1 Q0 d1 2 8.0 run1
q1 Q0 d3 3 7.0 run1
```

**necs-validate:** advisory, so these are warnings by default and promote to
errors with `--strict-ranks`:

- `duplicate_rank` — a rank value appears more than once for a query;
- `unusual_rank_base` — the smallest rank is not 0 or 1;
- `non_contiguous_ranks` — a 0- or 1-based rank sequence has gaps;
- `out_of_order_ranks` — ranks are not ascending in file order.

```text
[WARNING] duplicate_rank: query=q1 Advisory rank 1 appears more than once for this query
[WARNING] out_of_order_ranks: query=q1 Advisory ranks are not in ascending file order; found [2, 1, 1]
```

## Float relevance grades

TREC-style qrels grade relevance with integers. A fractional grade usually comes
from writing a float column straight out of a dataframe.

**What evaluators do.** Integer-only evaluators, including NIST `trec_eval`, parse
the grade as an integer and truncate a fractional value toward zero without any
error or warning: `1.5` is scored as `1`, and `0.3` becomes `0`. Every metric that
depends on that judgement shifts silently.

Broken qrels (`1.5` grade):

```text
q1 0 d1 1.5
```

Fixed (use an integer grade; a value written as `2.0` is accepted because it is an
integer):

```text
q1 0 d1 2
```

**necs-validate:** `non_integer_relevance` (error by default; warning with
`--allow-float-grades` for deliberate graded-gain workflows). A grade that is not
a finite number at all — such as `abc` or `inf` — is `invalid_relevance` (error).

```text
[ERROR] non_integer_relevance (qrels.txt, line 1): query=q1 document=d1 Relevance grade must be an integer, found '1.5'; integer-only evaluators silently truncate non-integer grades
```

---

## necs-validate v0.3.1 code reference

| Code | File | Default severity | Notes |
| --- | --- | --- | --- |
| `malformed_row` | qrels / run | error | wrong whitespace-separated column count |
| `empty_qrels` / `empty_run` | qrels / run | error | no valid data rows survived parsing |
| `file_read_error` | qrels / run | error | file could not be read or decoded |
| `conflicting_metadata` | qrels / run | error | a `# key: value` header repeats with a different value |
| `invalid_relevance` | qrels | error | relevance is not a finite number |
| `non_integer_relevance` | qrels | error | fractional grade; `--allow-float-grades` demotes to warning |
| `duplicate_judgement` | qrels | error | same query/document pair judged twice |
| `invalid_rank` | run | error | rank is not a non-negative integer |
| `invalid_score` | run | error | score is not a finite number |
| `duplicate_run_document` | run | error | same document returned twice for a query |
| `unknown_query` | coverage | warning | run query absent from qrels; `--require-query-coverage` → error |
| `missing_query` | coverage | warning | qrels query has no run entries; `--require-query-coverage` → error |
| `unjudged_document` | coverage | warning | returned document is unjudged; `--require-judged` → error |
| `duplicate_rank` | run | warning | `--strict-ranks` → error |
| `unusual_rank_base` | run | warning | smallest rank not 0 or 1; `--strict-ranks` → error |
| `non_contiguous_ranks` | run | warning | gaps in a 0/1-based sequence; `--strict-ranks` → error |
| `out_of_order_ranks` | run | warning | ranks not ascending in file order; `--strict-ranks` → error |
| `task_mismatch` | both | error | qrels and run declare different `# task:` headers |
| `missing_task_metadata` | both | error | only when `--expected-task` is set and a header is absent |
| `unexpected_task` | both | error | only when `--expected-task` is set and a header differs |

## Check your own files

Drop a qrels and run file into the
[in-browser validator](https://madhvansh.github.io/Neural-E-Commerce-Search/validate.html)
for a pass/warn/fail report with no install, no server, and no upload.

To run the same checks locally or in CI, install the v0.3.1 release wheel:

```bash
python -m pip install "https://github.com/Madhvansh/Neural-E-Commerce-Search/releases/download/v0.3.1/neural_ecommerce_search_madhvansh-0.3.1-py3-none-any.whl"
```

See the [validator guide](validation.md) for the full CLI, JSON output, and
strictness flags.
