from __future__ import annotations

import re
from pathlib import Path

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "0.3.1"


def test_release_version_metadata_is_synchronized():
    pyproject = (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    package_init = (REPOSITORY_ROOT / "src/necs/__init__.py").read_text(encoding="utf-8")
    citation = yaml.safe_load((REPOSITORY_ROOT / "CITATION.cff").read_text(encoding="utf-8"))
    changelog = (REPOSITORY_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    project_version = re.search(r'^version = "([^"]+)"$', pyproject, re.MULTILINE)
    package_version = re.search(r'^__version__ = "([^"]+)"$', package_init, re.MULTILINE)

    assert project_version and project_version.group(1) == EXPECTED_VERSION
    assert package_version and package_version.group(1) == EXPECTED_VERSION
    assert citation["version"] == EXPECTED_VERSION
    assert f"## [{EXPECTED_VERSION}]" in changelog


def test_changed_action_and_workflow_yaml_parses():
    paths = [
        REPOSITORY_ROOT / "action.yml",
        REPOSITORY_ROOT / ".github/workflows/ci.yml",
        REPOSITORY_ROOT / ".github/workflows/release-assets.yml",
    ]

    for path in paths:
        assert yaml.safe_load(path.read_text(encoding="utf-8"))


def test_ci_installs_the_unique_built_wheel_outside_the_checkout():
    workflow = (REPOSITORY_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "test \"${#wheels[@]}\" -eq 1" in workflow
    assert '"$smoke_dir/bin/python" -m pip install "${wheels[0]}"' in workflow
    assert 'pushd "$RUNNER_TEMP"' in workflow
    assert "necs.__version__ == \"0.3.1\"" in workflow
    assert "PYTHONPATH: ${{ github.workspace }}" in workflow


def test_release_workflow_verifies_and_installs_the_downloaded_asset():
    workflow = (REPOSITORY_ROOT / ".github/workflows/release-assets.yml").read_text(
        encoding="utf-8"
    )

    assert 'gh release download "$RELEASE_TAG"' in workflow
    assert "python -I scripts/verify_release_manifest.py" in workflow
    assert '--artifact "${wheels[0]}"' in workflow
    assert '--artifact "${sdists[0]}"' in workflow
    assert '"$smoke_dir/bin/python" -m pip install "${wheels[0]}"' in workflow
    assert '"$smoke_dir/bin/python" -m pip install "${sdists[0]}"' in workflow
    assert 'test "$installed_version" = "$release_version"' in workflow
