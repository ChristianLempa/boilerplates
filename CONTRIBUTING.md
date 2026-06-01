# Contributing

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e ".[test]" ruff
```

## Running the CLI

```bash
python3 -m cli
python3 -m cli --log-level DEBUG compose list
```

## Validation gates

Run the relevant checks before finishing changes. These are release gates, not optional cleanup.

```bash
ruff check --fix .
ruff format .
python3 -m pytest
```

If `ruff` is not installed in the active environment, install it before running the gates.

For production-like boilerplate testing before a release, see `WARP-LOCAL.md` if it exists locally. It is intentionally not tracked in git and may describe local Docker contexts, test servers, and release-readiness checklists.

## GitHub workflow

This repository uses GitHub issues, branches, pull requests, and releases.

Before GitHub-facing work such as issues, branches, PRs, merges, tags, or releases, read:

- `AGENTS.md`
- this contribution guide
- `RELEASE.md` for release-related work

## Naming conventions

- Branches and PRs: `feature/2314-add-feature`, `problem/1249-fix-bug`, `release/x.x.x`
- Commit messages: `type(scope): subject`, for example `fix(compose): correct variable parsing`
- Issues should have clear titles and descriptions, link related issues/PRs, and use appropriate labels such as `problem`, `feature`, `discussion`, or `question`.

## Standard commands

Standard module commands are auto-registered for all modules:

- `list` - list templates
- `search <query>` - search templates by ID
- `show <id>` - show template details
- `generate <id>` - generate from a template; supports `--dry-run`, `--var`, `--var-file`, `--no-interactive`, and destination options
- `validate [template_id]` - validate one or all templates
- `defaults` - manage config defaults with `get`, `set`, `rm`, `clear`, and `list`

Core repository commands include:

- `repo update` - sync git-based libraries
- `repo list` - list configured libraries
- `repo add` / `repo remove` - manage configured libraries
