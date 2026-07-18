# Release process

No package has been published from this checkout. A GitHub release and a Python
package-registry release are separate operations and should be verified
independently.

## Distribution name

The original `pyproject.toml` used `necs`, but that distribution name is already
used on PyPI by another project. The metadata now uses the deliberately specific
candidate name `neural-ecommerce-search-madhvansh`; the import package remains
`necs` for source compatibility.

PyPI's JSON endpoint returned `Not Found` for this candidate on 2026-07-19.
Availability is not reserved and must be checked again immediately before
publishing. If it is unavailable, choose another project-specific distribution
name and update this document, the changelog, and `pyproject.toml` together.
Never upload over or impersonate an unrelated package.

## Preflight

1. Confirm every README result is backed by a complete bundle under `results/`.
2. Run `pytest` and `ruff check src tests scripts` from a clean checkout.
3. Keep the version in `pyproject.toml`, `src/necs/__init__.py`, and
   `CITATION.cff` synchronized.
4. Check the candidate distribution name on PyPI and TestPyPI.
5. Build in an isolated environment:

   ```bash
   python -m pip install build twine
   python -m build
   python -m twine check dist/*
   ```

6. Install the wheel into a fresh environment and run:

   ```bash
   necs-demo --query "wireless gaming mouse"
   python -c "import necs; print(necs.__version__)"
   ```

7. Upload to TestPyPI first and repeat the clean-environment smoke test.
8. Create release notes from `CHANGELOG.md`; do not claim unpublished models,
   artifacts, integrations, or performance.

Publishing is intentionally a manual maintainer action. CI should verify an
artifact before a human authorizes a registry upload.
