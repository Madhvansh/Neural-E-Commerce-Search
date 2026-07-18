from __future__ import annotations

import json

from necs.validate import format_text, run_cli, validate_files


def _write(path, text):
    path.write_text(text, encoding="utf-8")
    return path


def test_valid_trec_run_passes(tmp_path):
    qrels = _write(
        tmp_path / "qrels.txt",
        "# task: task1_ranking\n1 0 d1 3\n1 0 d2 0\n2 0 d3 1\n",
    )
    run = _write(
        tmp_path / "run.txt",
        "# task: task1_ranking\n1 Q0 d1 1 1.2 necs\n1 Q0 d2 2 0.4 necs\n2 Q0 d3 1 0.7 necs\n",
    )

    report = validate_files(qrels, run, expected_task="task1_ranking")

    assert report.ok
    assert report.qrels_queries == 2
    assert report.qrels_judgements == 3
    assert report.run_entries == 3
    assert "PASS" in format_text(report)


def test_integrity_errors_are_reported_together(tmp_path):
    qrels = _write(tmp_path / "qrels.txt", "1 0 d1 3\n2 0 d2 1\n")
    run = _write(
        tmp_path / "run.txt",
        "1 Q0 d1 1 1.0 run\n1 Q0 d1 2 0.9 run\n1 Q0 unknown 3 0.8 run\n3 Q0 d3 1 0.7 run\n",
    )

    report = validate_files(qrels, run)
    codes = {issue.code for issue in report.errors}

    assert not report.ok
    assert "duplicate_run_document" in codes
    assert "unjudged_document" in codes
    assert "unknown_query" in codes
    assert "missing_query" in codes
    assert "non_contiguous_ranks" in codes


def test_allow_flags_downgrade_coverage_issues(tmp_path):
    qrels = _write(tmp_path / "qrels.txt", "1 0 d1 3\n2 0 d2 1\n")
    run = _write(tmp_path / "run.txt", "1 Q0 unjudged 1 1.0 run\n")

    report = validate_files(
        qrels,
        run,
        allow_missing_queries=True,
        allow_unjudged=True,
    )

    assert report.ok
    assert {issue.code for issue in report.warnings} == {
        "missing_query",
        "unjudged_document",
    }


def test_task_mismatch_is_an_error(tmp_path):
    qrels = _write(tmp_path / "qrels.txt", "# task: task1_ranking\n1 0 d1 3\n")
    run = _write(tmp_path / "run.txt", "# task: task2_classification\n1 Q0 d1 1 1 run\n")

    report = validate_files(qrels, run)

    assert {issue.code for issue in report.errors} == {"task_mismatch"}


def test_expected_task_requires_metadata_headers(tmp_path):
    qrels = _write(tmp_path / "qrels.txt", "1 0 d1 3\n")
    run = _write(tmp_path / "run.txt", "1 Q0 d1 1 1 run\n")

    report = validate_files(qrels, run, expected_task="task1_ranking")

    assert [issue.code for issue in report.errors] == [
        "missing_task_metadata",
        "missing_task_metadata",
    ]


def test_cli_json_and_exit_code(tmp_path, capsys):
    qrels = _write(tmp_path / "qrels.txt", "1 0 d1 3\n")
    run = _write(tmp_path / "run.txt", "1 Q0 d1 1 1 run\n")

    exit_code = run_cli(["--qrels", str(qrels), "--run", str(run), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["counts"]["run_entries"] == 1
