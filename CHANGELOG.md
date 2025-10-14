# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-10-14

### Added
- Support for required variables independent of section state (#1355)
  - Variables can now be marked with `required: true` in template specs
  - Required variables are always prompted, validated, and included in rendering
  - Display shows yellow `(required)` indicator for required variables
  - Required variables from disabled sections are still collected and available

### Changed
- Improved error handling and display output consistency
- Updated dependency PyYAML to v6.0.3 (Python 3.14 compatibility)
- Updated dependency rich to v14.2.0 (Python 3.14 compatibility)

### Fixed
- Absolute paths without leading slash treated as relative paths in generate command (#1357)
  - Paths like `Users/xcad/Projects/test` are now correctly normalized to `/Users/xcad/Projects/test`
  - Supports common Unix/Linux root directories: Users/, home/, usr/, opt/, var/, tmp/
- Repository fetch fails when library directory already exists (#1279)

## [0.0.4] - 2025-01-XX

Initial public release with core CLI functionality.

[unreleased]: https://github.com/christianlempa/boilerplates/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/christianlempa/boilerplates/compare/v0.0.4...v0.1.0
[0.0.4]: https://github.com/christianlempa/boilerplates/releases/tag/v0.0.4
