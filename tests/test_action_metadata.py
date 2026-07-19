from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _action_metadata() -> dict:
    return yaml.safe_load((REPOSITORY_ROOT / "action.yml").read_text(encoding="utf-8"))


def _bash_executable() -> str:
    candidates = [shutil.which("bash")]
    if os.name == "nt":
        candidates.extend(
            [
                str(Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/bash.exe"),
                "C:/msys64/usr/bin/bash.exe",
            ]
        )

    for candidate in candidates:
        if not candidate:
            continue
        try:
            result = subprocess.run(
                [candidate, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if result.returncode == 0 and "GNU bash" in result.stdout:
            return candidate

    pytest.skip("A working GNU Bash is required for the composite-action runtime tests")


def _bash_path(path: Path) -> str:
    resolved = path.resolve()
    if os.name != "nt":
        return str(resolved)
    drive = resolved.drive.rstrip(":").lower()
    tail = resolved.as_posix().split(":", maxsplit=1)[1].lstrip("/")
    return f"/{drive}/{tail}"


def _run_action(caller: Path, **overrides: str) -> subprocess.CompletedProcess[str]:
    step = _action_metadata()["runs"]["steps"][0]
    env = os.environ.copy()
    env.update(
        {
            "GITHUB_ACTION_PATH": _bash_path(REPOSITORY_ROOT),
            "NECS_QRELS": _bash_path(REPOSITORY_ROOT / "examples/validation/sample.qrels"),
            "NECS_RUN": _bash_path(REPOSITORY_ROOT / "examples/validation/sample.run"),
            "NECS_EXPECTED_TASK": "task1_ranking",
            "NECS_REQUIRE_COVERAGE": "false",
            "NECS_REQUIRE_JUDGED": "false",
            "NECS_STRICT_RANKS": "false",
        }
    )
    env.update(overrides)
    return subprocess.run(
        [_bash_executable(), "-c", step["run"]],
        cwd=caller,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def test_repository_has_one_root_action_metadata_file():
    action_files = [
        path
        for path in (REPOSITORY_ROOT / "action.yml", REPOSITORY_ROOT / "action.yaml")
        if path.exists()
    ]

    assert action_files == [REPOSITORY_ROOT / "action.yml"]


def test_marketplace_metadata_and_input_contract_are_explicit():
    metadata = _action_metadata()

    assert metadata["name"]
    assert metadata["description"]
    assert metadata["branding"] == {"icon": "check-circle", "color": "blue"}
    assert metadata["inputs"]["qrels"]["required"] is True
    assert metadata["inputs"]["run"]["required"] is True
    assert metadata["inputs"]["expected-task"]["default"] == ""
    for input_name in ("require-query-coverage", "require-judged", "strict-ranks"):
        assert metadata["inputs"][input_name]["default"] == "false"


def test_composite_action_executes_its_bundled_validator_without_input_interpolation():
    metadata = _action_metadata()
    step = metadata["runs"]["steps"][0]
    command = step["run"]

    assert metadata["runs"]["using"] == "composite"
    assert step["shell"] == "bash"
    assert '"$python_command" -I "$GITHUB_ACTION_PATH/src/necs/validate.py"' in command
    assert "python -m necs.validate" not in command
    assert "${{ inputs." not in command
    assert set(step["env"]) == {
        "NECS_QRELS",
        "NECS_RUN",
        "NECS_EXPECTED_TASK",
        "NECS_REQUIRE_COVERAGE",
        "NECS_REQUIRE_JUDGED",
        "NECS_STRICT_RANKS",
    }


def test_composite_action_ignores_a_caller_package_shadow(tmp_path):
    shadow = tmp_path / "necs"
    shadow.mkdir()
    (shadow / "__init__.py").write_text("", encoding="utf-8")
    (shadow / "validate.py").write_text(
        'raise SystemExit("caller package shadowed the action")\n',
        encoding="utf-8",
    )

    result = _run_action(tmp_path)
    output = result.stdout + result.stderr

    assert result.returncode == 0, output
    assert "NECS run validation: PASS" in output
    assert "caller package shadowed the action" not in output


def test_composite_action_ignores_caller_pythonpath_shadowing(tmp_path):
    (tmp_path / "json.py").write_text(
        'raise SystemExit("caller PYTHONPATH shadowed stdlib json")\n',
        encoding="utf-8",
    )

    result = _run_action(tmp_path, PYTHONPATH=_bash_path(tmp_path))
    output = result.stdout + result.stderr

    assert result.returncode == 0, output
    assert "NECS run validation: PASS" in output
    assert "caller PYTHONPATH shadowed stdlib json" not in output


def test_composite_action_rejects_empty_required_and_invalid_boolean_inputs(tmp_path):
    missing = _run_action(tmp_path, NECS_QRELS="")
    invalid = _run_action(tmp_path, NECS_STRICT_RANKS="yes")

    assert missing.returncode == 2
    assert "Missing required input" in missing.stdout + missing.stderr
    assert invalid.returncode == 2
    assert "Invalid action input" in invalid.stdout + invalid.stderr


def test_composite_action_reports_the_python_runtime_requirement(tmp_path):
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    for name in ("python", "python3"):
        executable = fake_bin / name
        executable.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        executable.chmod(0o755)

    result = _run_action(tmp_path, PATH=_bash_path(fake_bin))

    assert result.returncode == 2
    assert "Python 3.9+ required" in result.stdout + result.stderr
