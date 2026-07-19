"""Verify that a release manifest covers exactly the expected artifacts.

The verifier is dependency-free so the post-publication workflow can run it
before installing either distribution archive.
"""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

_MANIFEST_LINE = re.compile(
    r"^(?P<digest>[0-9a-fA-F]{64}) (?P<mode>[ *])(?P<name>[^\r\n]+)$"
)
_SAFE_BASENAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]*$")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_manifest(manifest: Path, artifacts: list[Path]) -> None:
    """Validate manifest membership, safe names, and SHA-256 values."""
    if not artifacts:
        raise ValueError("at least one expected artifact is required")

    manifest = manifest.resolve()
    expected: dict[str, Path] = {}
    for artifact in artifacts:
        resolved = artifact.resolve()
        if resolved.parent != manifest.parent:
            raise ValueError(f"artifact must be beside the manifest: {artifact}")
        if not resolved.is_file():
            raise ValueError(f"artifact is not a readable file: {artifact}")
        if resolved.name in expected:
            raise ValueError(f"duplicate expected artifact: {resolved.name}")
        expected[resolved.name] = resolved

    entries: dict[str, str] = {}
    lines = manifest.read_text(encoding="utf-8").splitlines()
    if not lines:
        raise ValueError("manifest is empty")

    for line_number, line in enumerate(lines, start=1):
        match = _MANIFEST_LINE.fullmatch(line)
        if not match:
            raise ValueError(f"invalid manifest line {line_number}")
        name = match.group("name")
        if not _SAFE_BASENAME.fullmatch(name) or Path(name).name != name:
            raise ValueError(f"unsafe artifact name on manifest line {line_number}")
        if name in entries:
            raise ValueError(f"duplicate manifest entry: {name}")
        entries[name] = match.group("digest").lower()

    if set(entries) != set(expected):
        missing = sorted(set(expected) - set(entries))
        unexpected = sorted(set(entries) - set(expected))
        raise ValueError(
            f"manifest coverage mismatch; missing={missing}, unexpected={unexpected}"
        )

    for name, path in expected.items():
        actual = _sha256(path)
        if actual != entries[name]:
            raise ValueError(f"SHA-256 mismatch for {name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--artifact", action="append", required=True, type=Path)
    args = parser.parse_args()

    try:
        verify_manifest(args.manifest, args.artifact)
    except (OSError, UnicodeError, ValueError) as exc:
        parser.exit(1, f"release manifest verification failed: {exc}\n")

    print(f"Verified {len(args.artifact)} release artifacts against {args.manifest.name}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
