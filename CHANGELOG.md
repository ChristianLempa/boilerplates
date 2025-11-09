# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Variable file support with `--var-file` flag (#1331) - Load variables from YAML file for non-interactive deployments
- Variable override support for `show` command with `--var` and `--var-file` flags (#1421) - Preview variable overrides before generating
- Terraform template support (#1422) - Manage Terraform configurations with schema 1.0
- Kubernetes template support (#1423) - Manage Kubernetes configurations with schema 1.0
- Helm template support (#1424) - Manage Helm charts with schema 1.0
- Ansible template support (#1426) - Manage Ansible playbooks with schema 1.0
- Packer template support (#1427) - Manage Packer templates with schema 1.0
- Alphabetically sorted commands in help output with grouped panels for better organization
- Separate help panels for "Template Commands" and "Configuration Commands"

### Changed
- Removed Jinja2 `| default()` filter extraction and merging (#1410) - All defaults must now be defined in template/module specs
- Refactored code quality (#1364) for all core modules from single files to package structure with specific submodules
- Improved debug logging to capture module discovery and registration during initialization
- Enhanced debug logging for better troubleshooting

### Fixed
- CLI --var flag now properly converts boolean and numeric strings to appropriate Python types (#1522)

## [0.0.7] - 2025-10-28

### Added
- Multiple Library Support (#1314) for git and local libraries
- Multi-Schema Module Support and Backward Compatibility (Schema-1.0)
- Schema-1.1 `network_mode` with options: bridge, host, macvlan
- Schema-1.1 `swarm` module support
- Variable-level and Section-level depenendencies `needs` with multiple values support
- Optional Variables `optional: true` to allow empty/None values
- PEP 8 formatting alignment
- CLI variable dependency validation - raises error when CLI-provided variables have unsatisfied dependencies
- Support for required variables independent of section state (#1355)
  - Variables can now be marked with `required: true` in template specs
  - Required variables are always prompted, validated, and included in rendering
  - Display shows yellow `(required)` indicator for required variables
  - Required variables from disabled sections are still collected and available

### Changed
- Schema-1.1 Unified Docker Swarm Placement (#1359) - Simplified swarm placement constraints into a single variable
- Refactored compose module from single file to package structure
- Dependency validation moved to `validate_all()` for better error reporting
- Schema-1.1 removed `network_enabled`, `ports_enabled` and `database_enabled` toggles (no longer optional)
- Improved error handling and display output consistency
- Updated dependency PyYAML to v6.0.3 (Python 3.14 compatibility)
- Updated dependency rich to v14.2.0 (Python 3.14 compatibility)
- Pinned all dependencies to specific tested versions for consistent installations

### Fixed
- Required sections now ignore toggle and are always enabled
- Module spec loading based on correct template schema version
- Interactive prompts now skip all variables (including required) when parent section is disabled
- Absolute paths without leading slash treated as relative paths in generate command (#1357)
  - Paths like `Users/xcad/Projects/test` are now correctly normalized to `/Users/xcad/Projects/test`
  - Supports common Unix/Linux root directories: Users/, home/, usr/, opt/, var/, tmp/
- Repository fetch fails when library directory already exists (#1279)
- **Critical:** Python 3.9 compatibility - removed Context type annotations causing RuntimeError
- Context access now uses click.get_current_context() for better compatibility

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

[unreleased]: https://github.com/christianlempa/boilerplates/compare/v0.0.7...HEAD
[0.0.7]: https://github.com/christianlempa/boilerplates/compare/v0.0.6...v0.0.7
[0.0.6]: https://github.com/christianlempa/boilerplates/releases/tag/v0.0.6
[0.0.4]: https://github.com/christianlempa/boilerplates/releases/tag/v0.0.4
