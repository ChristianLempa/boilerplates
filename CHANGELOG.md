# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Multiple Library Support (#1314) for git and local libraries
- Multi-Schema Module Support and Backward Compatibility (Schema-1.0)
- Schema-1.1 `network_mode` with options: bridge, host, macvlan
- Schema-1.1 `swarm` module support
- Variable-level and Section-level depenendencies `needs` with multiple values support
- Optional Variables `optional: true` to allow empty/None values
- PEP 8 formatting alignment
- CLI variable dependency validation - raises error when CLI-provided variables have unsatisfied dependencies

### Changed
- Schema-1.1 Unified Docker Swarm Placement (#1359) - Simplified swarm placement constraints into a single variable
- Refactored compose module from single file to package structure
- Dependency validation moved to `validate_all()` for better error reporting
- Schema-1.1 removed `network_enabled`, `ports_enabled` and `database_enabled` toggles (no longer optional)

### Fixed
- Required sections now ignore toggle and are always enabled
- Module spec loading based on correct template schema version
- Interactive prompts now skip all variables (including required) when parent section is disabled

## [0.0.6] - 2025-01-XX

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

[unreleased]: https://github.com/christianlempa/boilerplates/compare/v0.0.6...HEAD
[0.0.6]: https://github.com/christianlempa/boilerplates/compare/v0.0.4...v0.0.6
[0.0.4]: https://github.com/christianlempa/boilerplates/releases/tag/v0.0.4
