from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest
from scripts.verify_release_manifest import verify_manifest


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _artifacts(tmp_path: Path) -> tuple[Path, Path]:
    wheel = tmp_path / "example-0.3.1-py3-none-any.whl"
    sdist = tmp_path / "example-0.3.1.tar.gz"
    wheel.write_bytes(b"wheel artifact")
    sdist.write_bytes(b"source artifact")
    return wheel, sdist


def test_manifest_must_cover_the_exact_wheel_and_sdist(tmp_path):
    wheel, sdist = _artifacts(tmp_path)
    manifest = tmp_path / "SHA256SUMS.txt"
    manifest.write_text(
        f"{_digest(wheel)}  {wheel.name}\n{_digest(sdist)}  {sdist.name}\n",
        encoding="utf-8",
    )

    verify_manifest(manifest, [wheel, sdist])

    manifest.write_text(f"{_digest(wheel)}  {wheel.name}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="coverage mismatch"):
        verify_manifest(manifest, [wheel, sdist])


def test_manifest_rejects_unsafe_or_duplicate_names(tmp_path):
    wheel, sdist = _artifacts(tmp_path)
    manifest = tmp_path / "SHA256SUMS.txt"
    manifest.write_text(
        f"{_digest(wheel)}  ../{wheel.name}\n{_digest(sdist)}  {sdist.name}\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unsafe artifact name"):
        verify_manifest(manifest, [wheel, sdist])

    manifest.write_text(
        f"{_digest(wheel)}  {wheel.name}\n{_digest(wheel)}  {wheel.name}\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate manifest entry"):
        verify_manifest(manifest, [wheel, sdist])


def test_manifest_rejects_a_tampered_artifact(tmp_path):
    wheel, sdist = _artifacts(tmp_path)
    manifest = tmp_path / "SHA256SUMS.txt"
    manifest.write_text(
        f"{_digest(wheel)}  {wheel.name}\n{_digest(sdist)}  {sdist.name}\n",
        encoding="utf-8",
    )
    sdist.write_bytes(b"tampered source artifact")

    with pytest.raises(ValueError, match=f"SHA-256 mismatch for {re.escape(sdist.name)}"):
        verify_manifest(manifest, [wheel, sdist])
