#!/usr/bin/env python3
"""Re-run the trec_eval structural-compatibility harness.

This drives a structural preflight validator over a frozen set of NIST
``trec_eval`` test fixtures (see ``README.md`` for provenance) and regenerates
the raw per-pair outputs in ``results/`` plus ``results/summary.md``.

Scope: structural preflight only. It records whether each fixture parses under
the TREC qrels/run column contract the validator enforces. It is not a
scoring-correctness oracle and asserts nothing about metric values.

Design goal: two implementations. ``--validator`` selects the command to run,
so the same fixtures and the same runner can be pointed at the released
reference validator today and at a second implementation (for example an
in-progress Rust port of trec_eval) once that exposes a compatible CLI. See the
"Second implementation slot" section of ``README.md``.

Standard library only. No third-party imports.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"

# Each entry is one validator invocation: the CLI requires a qrels file and a
# run file together, so a "pair" is the smallest unit the validator accepts.
# The set below exercises every frozen qrels fixture and every frozen run
# fixture at least once. ``label`` names the raw output file in the out dir.
PAIRS = [
    (
        "qrels.test__results.test",
        "qrels.test",
        "results.test",
        "Canonical multi-query trec_eval regression pair.",
    ),
    (
        "qrels-302.test__results-302.test",
        "qrels-302.test",
        "results-302.test",
        "Single-query (topic 302) matched pair.",
    ),
    (
        "qrels.comment.test__results.comment.test",
        "qrels.comment.test",
        "results.comment.test",
        "MS MARCO v2.1-style pair with graded judgements.",
    ),
    (
        "qrels.123__results.test",
        "qrels.123",
        "results.test",
        "qrels.123 variant against the canonical run.",
    ),
    (
        "qrels.comments.123__results.test",
        "qrels.comments.123",
        "results.test",
        "qrels with in-line '#' comment lines against the canonical run.",
    ),
    (
        "qrels.rel_level__results.test",
        "qrels.rel_level",
        "results.test",
        "Relevance-level qrels variant against the canonical run.",
    ),
    (
        "qrels.test.with-comments__results.test",
        "qrels.test.with-comments",
        "results.test",
        "qrels with a leading comment line against the canonical run.",
    ),
    (
        "qrels.test__results.trunc",
        "qrels.test",
        "results.trunc",
        "Canonical qrels against results.trunc (rows carry trailing text).",
    ),
]

_SUMMARY_RE = re.compile(r"errors=(\d+)\s+warnings=(\d+)")
_ISSUE_RE = re.compile(r"^\[(ERROR|WARNING)\]\s+(\S+)")


def resolve_validator(command: list[str]) -> list[str]:
    """Return ``command`` with a relative executable path made absolute.

    The validator subprocess runs with the fixtures directory as its working
    directory so it only ever sees bare fixture filenames (stable output across
    platforms). A validator given as a bare command name is left alone for PATH
    lookup; a validator given as a relative path is resolved before the cwd
    changes so it still points at the intended binary.
    """

    if not command:
        raise SystemExit("error: empty validator command")
    head, *tail = command
    head_path = Path(head)
    if (head_path.parent != Path(".") or head_path.is_absolute()) and head_path.exists():
        head = str(head_path.resolve())
    return [head, *tail]


def parse_counts(text: str) -> tuple[str, int, int, list[str], list[str]]:
    """Extract (verdict, errors, warnings, error_codes, warning_codes)."""

    verdict = "UNKNOWN"
    for line in text.splitlines():
        if line.startswith("NECS run validation:"):
            verdict = line.split(":", 1)[1].strip()
            break
    errors = warnings = 0
    match = _SUMMARY_RE.search(text)
    if match:
        errors, warnings = int(match.group(1)), int(match.group(2))
    error_codes: list[str] = []
    warning_codes: list[str] = []
    for line in text.splitlines():
        issue = _ISSUE_RE.match(line)
        if not issue:
            continue
        severity, code = issue.group(1), issue.group(2)
        (error_codes if severity == "ERROR" else warning_codes).append(code)
    return verdict, errors, warnings, error_codes, warning_codes


def distinct_with_counts(codes: list[str]) -> str:
    """Render ``code (n)`` entries preserving first-seen order."""

    order: list[str] = []
    counts: dict[str, int] = {}
    for code in codes:
        if code not in counts:
            order.append(code)
        counts[code] = counts.get(code, 0) + 1
    return ", ".join(f"{code} ({counts[code]})" for code in order) or "-"


def run_pair(
    validator: list[str],
    label: str,
    qrels: str,
    run: str,
    note: str,
    out_dir: Path,
    impl: str,
) -> dict:
    argv = [*validator, "--qrels", qrels, "--run", run]
    completed = subprocess.run(
        argv,
        cwd=FIXTURES,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    display_cmd = f"necs-validate --qrels {qrels} --run {run}"
    header = [
        f"# harness: trec_eval_compat ({impl})",
        f"# command: {display_cmd}",
        f"# qrels fixture: {qrels}",
        f"# run fixture: {run}",
        f"# exit code: {completed.returncode}",
        f"# note: {note}",
        "",
    ]
    body = completed.stdout.rstrip("\n")
    text_out = "\n".join(header) + body + "\n"
    if completed.stderr.strip():
        text_out += "\n# stderr:\n" + completed.stderr.rstrip("\n") + "\n"

    out_path = out_dir / f"{label}.txt"
    out_path.write_text(text_out, encoding="utf-8", newline="\n")

    verdict, errors, warnings, error_codes, warning_codes = parse_counts(completed.stdout)
    return {
        "label": label,
        "qrels": qrels,
        "run": run,
        "note": note,
        "exit": completed.returncode,
        "verdict": verdict,
        "errors": errors,
        "warnings": warnings,
        "error_codes": error_codes,
        "warning_codes": warning_codes,
    }


def write_summary(rows: list[dict], out_dir: Path, impl: str) -> None:
    lines = [
        f"# trec_eval_compat results summary ({impl})",
        "",
        "Structural preflight only. Verdict is the validator's own PASS/FAIL:",
        "PASS means no structural errors; FAIL means one or more errors. It does",
        "not certify metric scores. See `../README.md` for scope and provenance.",
        "",
        "| Output file | Qrels fixture | Run fixture | Verdict | Errors | Warnings | Notable codes |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        notable_bits = []
        if row["error_codes"]:
            notable_bits.append("errors: " + distinct_with_counts(row["error_codes"]))
        if row["warning_codes"]:
            notable_bits.append("warnings: " + distinct_with_counts(row["warning_codes"]))
        notable = "; ".join(notable_bits) or "-"
        lines.append(
            f"| `{row['label']}.txt` | `{row['qrels']}` | `{row['run']}` "
            f"| {row['verdict']} | {row['errors']} | {row['warnings']} | {notable} |"
        )
    lines.append("")
    (out_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--validator",
        default="necs-validate",
        help=(
            "Command for the validator to exercise (default: 'necs-validate' on "
            "PATH). Split on spaces, so multi-token commands such as "
            "'python -m necs.validate' work. Point this at a second "
            "implementation's binary to run the differential harness."
        ),
    )
    parser.add_argument(
        "--impl",
        default="necs",
        help=(
            "Short label for the implementation under test (default: 'necs'). "
            "Stamped into the regenerated outputs so a second implementation's "
            "results are self-identifying."
        ),
    )
    parser.add_argument(
        "--out",
        default=str(HERE / "results"),
        help="Directory for per-pair outputs and summary.md (default: ./results).",
    )
    args = parser.parse_args(argv)

    validator = resolve_validator(args.validator.split())
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Fail early with a clear message if the validator command is not runnable.
    if shutil.which(validator[0]) is None and not Path(validator[0]).exists():
        print(
            f"error: validator command not found: {validator[0]!r}\n"
            "Install the released wheel (necs-validate) or pass --validator "
            "pointing at an implementation's binary.",
            file=sys.stderr,
        )
        return 2

    rows = [
        run_pair(validator, label, qrels, run, note, out_dir, args.impl)
        for label, qrels, run, note in PAIRS
    ]
    write_summary(rows, out_dir, args.impl)

    failed = sum(1 for row in rows if row["verdict"] != "PASS")
    print(
        f"Ran {len(rows)} qrels/run pair(s) through '{args.impl}'. "
        f"Outputs in {out_dir}. "
        f"{len(rows) - failed} PASS, {failed} FAIL."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
