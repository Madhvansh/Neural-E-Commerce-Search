# Release process

The project publishes wheels, source distributions, and checksum manifests
through GitHub Releases. It is not currently published to PyPI. GitHub
Releases, GitHub Marketplace, and Python package-registry publishing are
separate operations and must be verified independently.

## Distribution name

The original `pyproject.toml` used `necs`, but that distribution name is already
used on PyPI by another project. The metadata now uses the deliberately specific
candidate name `neural-ecommerce-search-madhvansh`; the import package remains
`necs` for source compatibility.

Distribution-name availability is not reserved and must be checked immediately
before any registry publication. If it is unavailable, choose another
project-specific distribution name and update this document, the changelog,
and `pyproject.toml` together. Never upload over or impersonate an unrelated
package.

## GitHub Release preflight

1. Confirm every README result is backed by a complete bundle under `results/`.
2. Run `pytest` and `ruff check src tests scripts` from a clean checkout.
3. Keep the version in `pyproject.toml`, `src/necs/__init__.py`, and
   `CITATION.cff` synchronized.
4. Build in an isolated environment:

   ```bash
   python -m pip install build twine
   python -m build
   python -m twine check dist/*
   ```

5. Confirm the build produced exactly one wheel and one source distribution,
   then install each into a separate fresh environment and run:

   ```bash
   necs-demo --query "wireless gaming mouse"
   python -c "import necs; print(necs.__version__)"
   ```

6. Generate a SHA-256 manifest that names exactly those two archives, and run
   `scripts/verify_release_manifest.py` against the manifest and both files.
7. Create release notes from `CHANGELOG.md`; do not claim unpublished models,
   artifacts, integrations, or performance.

## Optional Python package registry

These steps apply only when intentionally publishing to PyPI or another Python
package registry; they are not required for a GitHub Release or Marketplace
Action patch.

1. Recheck the distribution name on the target registry and its test service.
2. Upload to the test registry first.
3. Install the uploaded wheel and source distribution into separate clean
   environments and repeat the smoke tests.
4. Publish to the production registry only after the uploaded artifacts pass.

## GitHub Action and Marketplace

The root `action.yml` is independently versioned by the repository release tag.
Do not move an existing release tag to pick up later action fixes. Publish a new
semantic patch release instead.

1. Run `pytest`, Ruff, and the `action-smoke` matrix from the exact candidate
   commit. The matrix must pass on GitHub-hosted Linux, macOS, and Windows.
2. Confirm the candidate has exactly one root `action.yml` or `action.yaml`, and
   that its name, description, inputs, composite step, icon, and color pass the
   release page's metadata validator.
3. Open the action metadata file on GitHub and use **Draft a release**. Upload
   the already-verified wheel, source archive, and manifest to that draft. Do
   not proceed until the Marketplace panel says **Everything looks good!**;
   that UI is authoritative for the unique action-name check.
4. Select **Publish this Action to the GitHub Marketplace**, then choose **Code
   quality** as the primary category and **Testing** as the
   secondary category. The validator checks evaluation artifacts before metric
   computation; it is not a deployment or security scanner.
5. Prefer an immutable release-specific tag. If immutable releases are not
   enabled, publish the exact full commit SHA alongside the readable version tag
   in every workflow example.
6. Verify the release notes include checkout and Python setup. The repository
   owner must complete the Marketplace agreement and two-factor authentication,
   then publish the release and Marketplace version together. Never move or
   recreate the version tag after publication.
7. After publication, verify the public listing, install snippet, source link,
   categories, and a fresh downstream run. Record maintainer-run checks as
   compatibility evidence, not independent adoption.

The `Verify published release assets` workflow retries the automatic
`release: published` download to tolerate short asset-visibility delays. That
automatic run is a convenience signal only. After every wheel, source archive,
and SHA-256 manifest is visible on the release page, manually dispatch the same
workflow with the exact tag. Treat that post-upload `workflow_dispatch` run as
the authoritative published-artifact gate: both the wheel and source archive
must install outside the checkout and pass the version, help, valid-fixture,
and expected-failure checks.

CI verifies the candidate source and an isolated build before publication; the
post-publication workflow verifies the exact GitHub Release assets. Registry
uploads remain manual maintainer actions.
