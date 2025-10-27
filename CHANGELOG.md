# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Multi-Schema Module Support
  - Modules can now maintain multiple schema versions simultaneously
  - Schema specs organized in separate files (e.g., `spec_v1_0.py`, `spec_v1_1.py`)
  - CLI automatically uses appropriate schema based on template declaration
  - Module discovery now supports both file and package modules
- Compose Schema 1.1 Network Enhancements
  - Added `network_mode` with options: bridge, host, macvlan
  - Macvlan support with conditional fields (IP address, interface, subnet, gateway)
  - Host mode support for direct host network access
  - Network fields conditionally shown based on selected mode
- Comma-Separated Values in Dependencies
  - `needs` now supports multiple values: `network_mode=bridge,macvlan`
  - Variable shown if actual value matches ANY of the specified values
- Template Schema Versioning (#1360)
  - Templates can now declare schema version (defaults to "1.0" for backward compatibility)
  - Modules validate template compatibility against supported schema version
  - Incompatible templates show clear error with upgrade instructions
  - New `cli/core/version.py` module for semantic version comparison
  - New `IncompatibleSchemaVersionError` exception for version mismatches
- Variable-level Dependencies
  - Variables can now have `needs` dependencies with format `variable=value`
  - Sections support new dependency format: `needs: "variable=value"`
  - Backward compatible with old section-only dependencies (`needs: "section_name"`)
  - `is_variable_satisfied()` method added to VariableCollection
- Show/Generate `--all` flag
  - Added `--all` flag to `show` and `generate` commands
  - Shows all variables/sections regardless of needs satisfaction
  - Useful for debugging and viewing complete template structure
- Optional Variables
  - Variables can now be marked with `optional: true` to allow empty/None values
- Docker Swarm Volume Configuration
  - Support for local, mount, and NFS storage backends
  - Configurable NFS server, paths, and mount options

### Changed
- Compose module schema version bumped to "1.1"
- Traefik TLS section now uses variable-level dependencies (`needs: "traefik_enabled=true"`)
- Display manager hides sections/variables with unsatisfied needs by default (unless `--all` flag is used)
- Variables with unsatisfied needs are dimmed when shown with `--all` flag
- Dependency validation now supports both old (section) and new (variable=value) formats

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
