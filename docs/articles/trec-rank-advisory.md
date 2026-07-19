# The TREC rank column is advisory: three mistakes I fixed in an IR evaluation preflight

*Published 2026-07-20 in the project docs.*

I wanted a small CI check that could read a TREC-style qrels file and run file
before an evaluation script produced metrics. The first version sounded
reasonable: ranks should begin at one and be contiguous, every qrels query
should appear in the run, and every retrieved document should have a judgment.

Those defaults were wrong for a large part of the information-retrieval
ecosystem.

The useful part of building the check was not writing a six-column parser. It
was discovering where a strict-looking rule would reject a legitimate
experiment—and separating structural failures from evaluation-policy choices.

## Mistake 1: treating the submitted rank as authoritative

The canonical NIST `trec_eval` reader explicitly ignores the submitted rank
field. It assigns ranks internally after sorting by similarity score, with a
deterministic document-ID tie-break. That means duplicate, gapped, or
out-of-order values in the rank column can be suspicious without changing what
`trec_eval` evaluates.

There is another compatibility trap: PyTerrier's documented ranked-document
model starts each query at rank zero. A validator that insists on `1, 2, 3, ...`
rejects normal PyTerrier output before it reaches an evaluator that would accept
it.

The corrected policy is:

- a non-integer or negative rank is a structural error for this preflight;
- zero- and one-based contiguous ranks are accepted;
- duplicate, gapped, unusually based, or out-of-order rank values are visible
  warnings by default; and
- `--strict-ranks` turns those warnings into errors for teams whose exporter
  contract requires a canonical rank column.

Duplicate `(query_id, document_id)` results remain hard errors. Unlike an
advisory rank value, repeating the same result can change downstream behavior or
hide an export defect.

## Mistake 2: assuming every retrieved document must be judged

Pooled test collections are normally incomplete. A run can retrieve a document
that was never placed in the judgment pool, so “unjudged” is not the same thing
as “invalid.” Failing every such document would make the default unusable on
exactly the collections the format was designed to support.

The preflight now reports unjudged results as warnings. A fully judged candidate
set can opt into `--require-judged` and make the same condition fatal.

This distinction also improves the report. A warning is not hidden: it remains
in text and JSON output, can be counted, and can trigger a team-specific policy.
It simply does not pretend that one evaluation policy is universal.

## Mistake 3: hard-failing every query-set difference

Query coverage affects metrics, but common evaluators have defined behavior for
partial sets. A qrels query with no returned documents should receive a zero
score. A run-only query with no qrels is typically ignored. Silently dropping
either condition from the report would be dangerous; treating both as malformed
input would be an overreach.

The default therefore reports `missing_query` and `unknown_query` warnings.
Workflows that require identical query sets can add
`--require-query-coverage`.

## What still fails immediately

The compatibility work did not turn the tool into a permissive line counter.
It still fails on conditions that make the artifact structurally unsafe:

- malformed column counts;
- unreadable or empty files;
- non-finite relevance values or scores;
- duplicate qrels judgments;
- duplicate run query/document pairs;
- conflicting metadata; and
- requested task metadata that is missing or inconsistent.

The output is available as readable text or stable JSON, and a nonzero exit
status makes the same command usable in local checks and CI.

```bash
necs-validate \
  --qrels evaluation/qrels.txt \
  --run evaluation/run.txt
```

The composite Action is the same preflight with pinned release semantics:

```yaml
- uses: Madhvansh/Neural-E-Commerce-Search@6fefdad10b60e71eedfcedee1491d6e043ebe670 # v0.3.1
  with:
    qrels: evaluation/qrels.txt
    run: evaluation/run.txt
```

## A boundary, not a badge

A passing structural preflight does not certify an experiment. It does not
prove that the dataset revision is correct, that gains match the task, that an
ideal DCG was computed from complete qrels, that a checkpoint was loaded, or
that a reported model score is reproducible.

That boundary is deliberate. Small tooling is more trustworthy when it says
exactly which failures it can detect and leaves scientific claims to evidence
that actually supports them.

The validator grew out of an audit of my Neural E-Commerce Search repository,
where I withdrew historical figures that did not have a publishable evidence
bundle and repaired evaluation/checkpoint paths before adding new claims. The
repository also has a no-login browser lab, but the lab is clearly separated
from ESCI benchmark evidence.

I am looking for adversarial compatibility reports rather than endorsements:
one accepted exporter artifact that produces a false positive is more useful
than a generic compliment.

- Validator guide: https://github.com/Madhvansh/Neural-E-Commerce-Search/blob/v0.3.1/docs/validation.md
- Release: https://github.com/Madhvansh/Neural-E-Commerce-Search/releases/tag/v0.3.1
- Browser lab: https://madhvansh.github.io/Neural-E-Commerce-Search/lab.html

## Primary references

- NIST `trec_eval` results reader (rank field is ignored):
  https://github.com/usnistgov/trec_eval/blob/main/get_trec_results.c
- PyTerrier data model (first rank is zero):
  https://pyterrier.readthedocs.io/en/stable/datamodel.html
- `ir-measures` empty-set behavior:
  https://ir-measur.es/en/latest/advanced.html#empty-set-behaviour
- NIST qrels reader, whose integer contract is narrower than this preflight's
  finite graded-gain support:
  https://github.com/usnistgov/trec_eval/blob/main/get_qrels.c
