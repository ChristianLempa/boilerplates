# Release Process

## Overview

Releases are prepared through a release PR and published by pushing a version tag. The GitHub Actions release workflow runs on tags matching `v*.*.*`.

The release PR should be limited to release preparation changes whenever possible: version files and changelog updates.

## Version files

The release version must match in all of these places:

- `pyproject.toml`
- `cli/__init__.py`
- Git tag, e.g. `vx.x.x`

The release workflow validates this and fails if they differ.

## Prepare a release

1. Start from an updated `main` branch.

   ```bash
   git checkout main
   git pull origin main
   git checkout -b release/x.x.x
   ```

2. Update version files if needed.

   ```toml
   # pyproject.toml
   version = "x.x.x"
   ```

   ```python
   # cli/__init__.py
   __version__ = "x.x.x"
   ```

3. Finalize `CHANGELOG.md`.

   Move entries from:

   ```md
   ## [Unreleased]
   ```

   to:

   ```md
   ## [x.x.x] - YYYY-MM-DD
   ```

   Then add a fresh empty section above it:

   ```md
   ## [Unreleased]
   ```

4. Run release gates.

   ```bash
   ruff check --fix .
   ruff format .
   python3 -m pytest
   cubic review -j
   ```

5. Commit and push.

   ```bash
   git add pyproject.toml cli/__init__.py CHANGELOG.md
   git commit -m "release: prepare vx.x.x"
   git push -u origin release/x.x.x
   ```

6. Open a PR into `main`.

   PR title:

   ```text
   release: prepare vx.x.x
   ```

7. Merge the release PR after checks and review pass.

## Publish the release

After the release PR is merged:

```bash
git checkout main
git pull origin main
git tag vx.x.x
git push origin vx.x.x
```

Pushing the tag triggers `.github/workflows/release-create-cli-release.yaml`.

The workflow will:

- validate version consistency
- build the Python package
- run package checks
- create the GitHub Release
- attach `.whl` and `.tar.gz` assets
- use the matching changelog section as release notes

## Hotfix releases

For hotfix/post releases, use the repository's existing tag format:

```text
vx.x.x-n
```

The release workflow creates package-compatible asset aliases for these versions.

## After release

Verify that:

- the GitHub Release exists
- release assets are attached
- the installer can install the release

```bash
curl -fsSL https://raw.githubusercontent.com/christianlempa/boilerplates/main/scripts/install.sh |
  bash -s -- --version vx.x.x
```
