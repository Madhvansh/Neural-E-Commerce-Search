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

    report = validate_files(
        qrels,
        run,
        require_query_coverage=True,
        require_judged=True,
        strict_ranks=True,
    )
    codes = {issue.code for issue in report.errors}

    assert not report.ok
    assert "duplicate_run_document" in codes
    assert "unjudged_document" in codes
    assert "unknown_query" in codes
    assert "missing_query" in codes
    assert "non_contiguous_ranks" in codes


def test_default_coverage_and_unjudged_conditions_are_warnings(tmp_path):
    qrels = _write(tmp_path / "qrels.txt", "1 0 d1 3\n2 0 d2 1\n")
    run = _write(tmp_path / "run.txt", "1 Q0 unjudged 1 1.0 run\n")

    report = validate_files(qrels, run)

    assert report.ok
    assert {issue.code for issue in report.warnings} == {
        "missing_query",
        "unjudged_document",
    }


def test_zero_based_pyterrier_ranks_pass_without_rank_warnings(tmp_path):
    qrels = _write(tmp_path / "qrels.txt", "1 0 d1 3\n1 0 d2 1\n")
    run = _write(
        tmp_path / "run.txt",
        "1 Q0 d1 0 1.0 run\n1 Q0 d2 1 0.5 run\n",
    )

    report = validate_files(qrels, run)

    assert report.ok
    assert not report.warnings


def test_rank_anomalies_warn_by_default_and_fail_in_strict_mode(tmp_path):
    qrels = _write(tmp_path / "qrels.txt", "1 0 d1 3\n1 0 d2 1\n1 0 d3 0\n")
    run = _write(
        tmp_path / "run.txt",
        "1 Q0 d1 2 1.0 run\n1 Q0 d2 0 0.5 run\n1 Q0 d3 2 0.1 run\n",
    )

    report = validate_files(qrels, run)
    strict_report = validate_files(qrels, run, strict_ranks=True)
    expected_codes = {
        "duplicate_rank",
        "non_contiguous_ranks",
        "out_of_order_ranks",
    }

    assert report.ok
    assert report.run_entries == 3
    assert {issue.code for issue in report.warnings} == expected_codes
    assert {issue.code for issue in strict_report.errors} == expected_codes


def test_query_coverage_warns_by_default_and_can_be_required(tmp_path):
    qrels = _write(tmp_path / "qrels.txt", "1 0 d1 3\n2 0 d2 1\n")
    run = _write(
        tmp_path / "run.txt",
        "1 Q0 d1 1 1.0 run\n3 Q0 d3 1 0.5 run\n",
    )

    report = validate_files(qrels, run)
    strict_report = validate_files(qrels, run, require_query_coverage=True)
    expected_codes = {"missing_query", "unknown_query"}

    assert report.ok
    assert expected_codes <= {issue.code for issue in report.warnings}
    assert expected_codes <= {issue.code for issue in strict_report.errors}


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


def test_cli_require_judged_turns_warning_into_failure(tmp_path, capsys):
    qrels = _write(tmp_path / "qrels.txt", "1 0 d1 3\n")
    run = _write(tmp_path / "run.txt", "1 Q0 other 1 1 run\n")

    exit_code = run_cli(
        ["--qrels", str(qrels), "--run", str(run), "--require-judged"]
    )
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "unjudged_document" in output


def test_float_relevance_grades_fail_by_default(tmp_path):
    # A non-integer qrels grade (e.g. 1.5) is a structural error by default.
    # Integer-only evaluators silently truncate such a grade (1.5 -> 1),
    # quietly changing the judgement; see docs/validation.md for the failure
    # mode. "2" carries an integer value and must not be flagged.
    qrels = _write(tmp_path / "qrels.txt", "1 0 d1 1.5\n1 0 d2 1e-1\n2 0 d3 2\n")
    run = _write(
        tmp_path / "run.txt",
        "1 Q0 d1 1 1.2 necs\n1 Q0 d2 2 0.4 necs\n2 Q0 d3 1 0.7 necs\n",
    )

    report = validate_files(qrels, run)
    non_integer = [issue for issue in report.errors if issue.code == "non_integer_relevance"]

    assert not report.ok
    assert {issue.line for issue in non_integer} == {1, 2}
    assert {issue.document_id for issue in non_integer} == {"d1", "d2"}


def test_float_relevance_grades_integer_valued_floats_pass(tmp_path):
    # "2.0" and "3" round-trip to an integer, so they are not truncation
    # hazards and must never be reported; only genuinely non-integer grades are.
    qrels = _write(tmp_path / "qrels.txt", "1 0 d1 2.0\n1 0 d2 3\n2 0 d3 0\n")
    run = _write(
        tmp_path / "run.txt",
        "1 Q0 d1 1 1.2 necs\n1 Q0 d2 2 0.4 necs\n2 Q0 d3 1 0.7 necs\n",
    )

    report = validate_files(qrels, run)

    assert report.ok
    assert not any(issue.code == "non_integer_relevance" for issue in report.issues)


def test_float_relevance_grades_allowed_as_warning(tmp_path):
    # The --allow-float-grades escape hatch keeps deliberate graded-gain
    # workflows passing while still surfacing the same silent-truncation risk
    # (a non-integer grade dropped to its floor by integer-only evaluators) as
    # an advisory warning rather than a hard error.
    qrels = _write(tmp_path / "qrels.txt", "1 0 d1 1.5\n1 0 d2 1e-1\n")
    run = _write(tmp_path / "run.txt", "1 Q0 d1 1 1.2 necs\n1 Q0 d2 2 0.4 necs\n")

    report = validate_files(qrels, run, allow_float_grades=True)
    warning_codes = [issue.code for issue in report.warnings]

    assert report.ok
    assert warning_codes == ["non_integer_relevance", "non_integer_relevance"]
    assert not any(issue.code == "non_integer_relevance" for issue in report.errors)


def test_float_relevance_grades_cli_flag_flips_exit_code(tmp_path, capsys):
    # The same file fails closed by default and passes under the escape hatch.
    # Default failure guards downstream evaluators that would truncate the grade
    # to an integer without warning.
    qrels = _write(tmp_path / "qrels.txt", "1 0 d1 1.5\n")
    run = _write(tmp_path / "run.txt", "1 Q0 d1 1 1.0 necs\n")

    default_exit = run_cli(["--qrels", str(qrels), "--run", str(run)])
    default_out = capsys.readouterr().out
    allowed_exit = run_cli(
        ["--qrels", str(qrels), "--run", str(run), "--allow-float-grades"]
    )

    assert default_exit == 1
    assert "non_integer_relevance" in default_out
    assert allowed_exit == 0
