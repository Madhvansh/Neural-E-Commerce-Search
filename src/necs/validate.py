"""Validate TREC-style qrels and retrieval runs before computing metrics.

The validator is intentionally dependency-light so it can run in a clean CI
environment.  It checks structural integrity and evaluation coverage; it does
not decide whether a dataset, relevance scale, or experiment design is
scientifically appropriate.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from pathlib import Path

_METADATA_RE = re.compile(r"^#\s*([A-Za-z0-9_.-]+)\s*:\s*(.*?)\s*$")


@dataclass(frozen=True)
class ValidationIssue:
    """One actionable problem or warning found in the input files."""

    severity: str
    code: str
    message: str
    file: str | None = None
    line: int | None = None
    query_id: str | None = None
    document_id: str | None = None


@dataclass
class ParsedQrels:
    judgements: dict[str, dict[str, float]] = field(default_factory=dict)
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class ParsedRun:
    entries: dict[str, list[tuple[str, int, float]]] = field(default_factory=dict)
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class ValidationReport:
    """Machine-readable summary returned by :func:`validate_files`."""

    qrels_path: str
    run_path: str
    qrels_queries: int
    qrels_judgements: int
    run_queries: int
    run_entries: int
    qrels_metadata: dict[str, str]
    run_metadata: dict[str, str]
    issues: list[ValidationIssue]

    @property
    def errors(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == "warning"]

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "qrels_path": self.qrels_path,
            "run_path": self.run_path,
            "counts": {
                "qrels_queries": self.qrels_queries,
                "qrels_judgements": self.qrels_judgements,
                "run_queries": self.run_queries,
                "run_entries": self.run_entries,
                "errors": len(self.errors),
                "warnings": len(self.warnings),
            },
            "metadata": {
                "qrels": self.qrels_metadata,
                "run": self.run_metadata,
            },
            "issues": [asdict(issue) for issue in self.issues],
        }


def _data_lines(
    path: Path,
    expected_columns: int,
    kind: str,
    issues: list[ValidationIssue],
) -> tuple[list[tuple[int, list[str]]], dict[str, str]]:
    rows: list[tuple[int, list[str]]] = []
    metadata: dict[str, str] = {}
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        issues.append(
            ValidationIssue(
                "error",
                "file_read_error",
                f"Could not read {kind} file: {exc}",
                file=str(path),
            )
        )
        return rows, metadata

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            match = _METADATA_RE.match(stripped)
            if match:
                key, value = match.groups()
                normalized_key = key.lower()
                if normalized_key in metadata and metadata[normalized_key] != value:
                    issues.append(
                        ValidationIssue(
                            "error",
                            "conflicting_metadata",
                            f"Metadata key {key!r} has conflicting values",
                            file=str(path),
                            line=line_number,
                        )
                    )
                metadata[normalized_key] = value
            continue

        columns = stripped.split()
        if len(columns) != expected_columns:
            issues.append(
                ValidationIssue(
                    "error",
                    "malformed_row",
                    (
                        f"Expected {expected_columns} whitespace-separated columns, "
                        f"found {len(columns)}"
                    ),
                    file=str(path),
                    line=line_number,
                )
            )
            continue
        rows.append((line_number, columns))
    return rows, metadata


def parse_qrels(path: str | Path, issues: list[ValidationIssue] | None = None) -> ParsedQrels:
    """Parse ``query_id iteration document_id relevance`` rows."""

    issue_list = issues if issues is not None else []
    qrels_path = Path(path)
    rows, metadata = _data_lines(qrels_path, 4, "qrels", issue_list)
    parsed = ParsedQrels(metadata=metadata)

    for line_number, columns in rows:
        query_id, _iteration, document_id, raw_relevance = columns
        try:
            relevance = float(raw_relevance)
            if not math.isfinite(relevance):
                raise ValueError
        except ValueError:
            issue_list.append(
                ValidationIssue(
                    "error",
                    "invalid_relevance",
                    f"Relevance must be a finite number, found {raw_relevance!r}",
                    file=str(qrels_path),
                    line=line_number,
                    query_id=query_id,
                    document_id=document_id,
                )
            )
            continue

        query_judgements = parsed.judgements.setdefault(query_id, {})
        if document_id in query_judgements:
            issue_list.append(
                ValidationIssue(
                    "error",
                    "duplicate_judgement",
                    "The same query/document pair appears more than once in qrels",
                    file=str(qrels_path),
                    line=line_number,
                    query_id=query_id,
                    document_id=document_id,
                )
            )
            continue
        query_judgements[document_id] = relevance

    if not rows:
        issue_list.append(
            ValidationIssue(
                "error",
                "empty_qrels",
                "No valid qrels rows were found",
                file=str(qrels_path),
            )
        )
    return parsed


def parse_run(path: str | Path, issues: list[ValidationIssue] | None = None) -> ParsedRun:
    """Parse ``query_id Q0 document_id rank score run_tag`` rows."""

    issue_list = issues if issues is not None else []
    run_path = Path(path)
    rows, metadata = _data_lines(run_path, 6, "run", issue_list)
    parsed = ParsedRun(metadata=metadata)
    seen_documents: set[tuple[str, str]] = set()
    seen_ranks: set[tuple[str, int]] = set()

    for line_number, columns in rows:
        query_id, _iteration, document_id, raw_rank, raw_score, _run_tag = columns
        try:
            rank = int(raw_rank)
            if rank < 1:
                raise ValueError
        except ValueError:
            issue_list.append(
                ValidationIssue(
                    "error",
                    "invalid_rank",
                    f"Rank must be a positive integer, found {raw_rank!r}",
                    file=str(run_path),
                    line=line_number,
                    query_id=query_id,
                    document_id=document_id,
                )
            )
            continue

        try:
            score = float(raw_score)
            if not math.isfinite(score):
                raise ValueError
        except ValueError:
            issue_list.append(
                ValidationIssue(
                    "error",
                    "invalid_score",
                    f"Score must be a finite number, found {raw_score!r}",
                    file=str(run_path),
                    line=line_number,
                    query_id=query_id,
                    document_id=document_id,
                )
            )
            continue

        document_key = (query_id, document_id)
        if document_key in seen_documents:
            issue_list.append(
                ValidationIssue(
                    "error",
                    "duplicate_run_document",
                    "The same document appears more than once for this query",
                    file=str(run_path),
                    line=line_number,
                    query_id=query_id,
                    document_id=document_id,
                )
            )
            continue
        seen_documents.add(document_key)

        rank_key = (query_id, rank)
        if rank_key in seen_ranks:
            issue_list.append(
                ValidationIssue(
                    "error",
                    "duplicate_rank",
                    f"Rank {rank} appears more than once for this query",
                    file=str(run_path),
                    line=line_number,
                    query_id=query_id,
                    document_id=document_id,
                )
            )
            continue
        seen_ranks.add(rank_key)
        parsed.entries.setdefault(query_id, []).append((document_id, rank, score))

    if not rows:
        issue_list.append(
            ValidationIssue(
                "error",
                "empty_run",
                "No valid run rows were found",
                file=str(run_path),
            )
        )
    return parsed


def _add_coverage_issues(
    qrels: ParsedQrels,
    run: ParsedRun,
    issues: list[ValidationIssue],
    *,
    allow_missing_queries: bool,
    allow_unjudged: bool,
) -> None:
    qrels_queries = set(qrels.judgements)
    run_queries = set(run.entries)

    for query_id in sorted(run_queries - qrels_queries):
        issues.append(
            ValidationIssue(
                "error",
                "unknown_query",
                "Run contains a query that is absent from qrels",
                query_id=query_id,
            )
        )

    missing_severity = "warning" if allow_missing_queries else "error"
    for query_id in sorted(qrels_queries - run_queries):
        issues.append(
            ValidationIssue(
                missing_severity,
                "missing_query",
                "Qrels query has no run entries and would otherwise disappear from an average",
                query_id=query_id,
            )
        )

    unjudged_severity = "warning" if allow_unjudged else "error"
    for query_id in sorted(qrels_queries & run_queries):
        judged_documents = qrels.judgements[query_id]
        entries = run.entries[query_id]
        ranks = sorted(rank for _document_id, rank, _score in entries)
        expected_ranks = list(range(1, len(ranks) + 1))
        if ranks != expected_ranks:
            issues.append(
                ValidationIssue(
                    "error",
                    "non_contiguous_ranks",
                    f"Ranks must be contiguous from 1; found {ranks}",
                    query_id=query_id,
                )
            )
        for document_id, _rank, _score in entries:
            if document_id not in judged_documents:
                issues.append(
                    ValidationIssue(
                        unjudged_severity,
                        "unjudged_document",
                        "Run document has no judgement for this query",
                        query_id=query_id,
                        document_id=document_id,
                    )
                )


def _add_task_issues(
    qrels: ParsedQrels,
    run: ParsedRun,
    issues: list[ValidationIssue],
    expected_task: str | None,
) -> None:
    qrels_task = qrels.metadata.get("task")
    run_task = run.metadata.get("task")
    if qrels_task and run_task and qrels_task != run_task:
        issues.append(
            ValidationIssue(
                "error",
                "task_mismatch",
                f"Qrels declare task {qrels_task!r}, but the run declares {run_task!r}",
            )
        )
    if expected_task:
        for kind, task in (("qrels", qrels_task), ("run", run_task)):
            if not task:
                issues.append(
                    ValidationIssue(
                        "error",
                        "missing_task_metadata",
                        (
                            f"{kind.capitalize()} do not declare a '# task: ...' header; "
                            f"expected {expected_task!r}"
                        ),
                    )
                )
            elif task != expected_task:
                issues.append(
                    ValidationIssue(
                        "error",
                        "unexpected_task",
                        f"{kind.capitalize()} declare task {task!r}, expected {expected_task!r}",
                    )
                )


def validate_files(
    qrels_path: str | Path,
    run_path: str | Path,
    *,
    allow_missing_queries: bool = False,
    allow_unjudged: bool = False,
    expected_task: str | None = None,
) -> ValidationReport:
    """Validate two TREC-style files and return a complete report."""

    issues: list[ValidationIssue] = []
    qrels = parse_qrels(qrels_path, issues)
    run = parse_run(run_path, issues)
    _add_coverage_issues(
        qrels,
        run,
        issues,
        allow_missing_queries=allow_missing_queries,
        allow_unjudged=allow_unjudged,
    )
    _add_task_issues(qrels, run, issues, expected_task)

    return ValidationReport(
        qrels_path=str(qrels_path),
        run_path=str(run_path),
        qrels_queries=len(qrels.judgements),
        qrels_judgements=sum(len(rows) for rows in qrels.judgements.values()),
        run_queries=len(run.entries),
        run_entries=sum(len(rows) for rows in run.entries.values()),
        qrels_metadata=qrels.metadata,
        run_metadata=run.metadata,
        issues=issues,
    )


def format_text(report: ValidationReport) -> str:
    status = "PASS" if report.ok else "FAIL"
    lines = [
        f"NECS run validation: {status}",
        (
            f"qrels={report.qrels_queries} queries/{report.qrels_judgements} judgements; "
            f"run={report.run_queries} queries/{report.run_entries} entries"
        ),
        f"errors={len(report.errors)} warnings={len(report.warnings)}",
    ]
    for issue in report.issues:
        location_parts = [
            part
            for part in (issue.file, f"line {issue.line}" if issue.line else None)
            if part
        ]
        location = f" ({', '.join(location_parts)})" if location_parts else ""
        context = ""
        if issue.query_id:
            context += f" query={issue.query_id}"
        if issue.document_id:
            context += f" document={issue.document_id}"
        lines.append(
            f"[{issue.severity.upper()}] {issue.code}{location}:{context} {issue.message}".rstrip()
        )
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qrels", required=True, help="TREC qrels file")
    parser.add_argument("--run", required=True, help="TREC run file")
    parser.add_argument(
        "--allow-missing-queries",
        action="store_true",
        help="report qrels queries missing from the run as warnings instead of errors",
    )
    parser.add_argument(
        "--allow-unjudged",
        action="store_true",
        help="report run documents absent from qrels as warnings instead of errors",
    )
    parser.add_argument(
        "--expected-task",
        help="require both files to declare this value in '# task: ...' headers",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="output format (default: text)",
    )
    return parser


def run_cli(argv: Iterable[str] | None = None) -> int:
    args = _build_parser().parse_args(list(argv) if argv is not None else None)
    report = validate_files(
        args.qrels,
        args.run,
        allow_missing_queries=args.allow_missing_queries,
        allow_unjudged=args.allow_unjudged,
        expected_task=args.expected_task,
    )
    if args.format == "json":
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_text(report))
    return 0 if report.ok else 1


def main() -> None:
    raise SystemExit(run_cli())


if __name__ == "__main__":
    main()
