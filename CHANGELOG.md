# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.6] - 2025-10-14

### Changed
- Pinned all dependencies to specific tested versions for consistent installations
  - typer==0.19.2
  - rich==14.1.0
  - PyYAML==6.0.2
  - python-frontmatter==1.1.0
  - Jinja2==3.1.6

### Fixed
- **Critical:** Python 3.9 compatibility - removed Context type annotations causing RuntimeError
- Context access now uses click.get_current_context() for better compatibility
- Added tests directory to .gitignore

## [0.0.4] - 2025-01-XX

Initial public release with core CLI functionality.

[unreleased]: https://github.com/christianlempa/boilerplates/compare/v0.0.6...HEAD
[0.0.6]: https://github.com/christianlempa/boilerplates/releases/tag/v0.0.6
[0.0.4]: https://github.com/christianlempa/boilerplates/releases/tag/v0.0.4
