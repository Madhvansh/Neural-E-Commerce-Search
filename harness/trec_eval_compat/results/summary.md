# trec_eval_compat results summary (necs-0.3.1)

Structural preflight only. Verdict is the validator's own PASS/FAIL:
PASS means no structural errors; FAIL means one or more errors. It does
not certify metric scores. See `../README.md` for scope and provenance.

| Output file | Qrels fixture | Run fixture | Verdict | Errors | Warnings | Notable codes |
| --- | --- | --- | --- | --- | --- | --- |
| `qrels.test__results.test.txt` | `qrels.test` | `results.test` | PASS | 0 | 765 | warnings: unjudged_document: (762), out_of_order_ranks: (3) |
| `qrels-302.test__results-302.test.txt` | `qrels-302.test` | `results-302.test` | PASS | 0 | 237 | warnings: unjudged_document: (236), out_of_order_ranks: (1) |
| `qrels.comment.test__results.comment.test.txt` | `qrels.comment.test` | `results.comment.test` | PASS | 0 | 1645 | warnings: unknown_query: (270), unjudged_document: (1375) |
| `qrels.123__results.test.txt` | `qrels.123` | `results.test` | FAIL | 6629 | 765 | errors: duplicate_judgement (6629); warnings: unjudged_document: (762), out_of_order_ranks: (3) |
| `qrels.comments.123__results.test.txt` | `qrels.comments.123` | `results.test` | FAIL | 6628 | 765 | errors: duplicate_judgement (6628); warnings: unjudged_document: (762), out_of_order_ranks: (3) |
| `qrels.rel_level__results.test.txt` | `qrels.rel_level` | `results.test` | PASS | 0 | 765 | warnings: unjudged_document: (762), out_of_order_ranks: (3) |
| `qrels.test.with-comments__results.test.txt` | `qrels.test.with-comments` | `results.test` | PASS | 0 | 765 | warnings: unjudged_document: (762), out_of_order_ranks: (3) |
| `qrels.test__results.trunc.txt` | `qrels.test` | `results.trunc` | FAIL | 5 | 260 | errors: malformed_row (5); warnings: missing_query: (1), unjudged_document: (255), non_contiguous_ranks: (1), out_of_order_ranks: (2), unusual_rank_base: (1) |
