# AGENTS.md

Guidance for AI Agents working with this repository.

## Project Overview

A sophisticated collection of infrastructure templates (boilerplates) with a Python CLI for management. Supports Terraform, Docker, Ansible, Kubernetes, etc. Built with Typer (CLI) and Jinja2 (templating).

## Development Setup

### Running and Testing

```bash
# Run the CLI application
python3 -m cli
# Debugging and Testing commands
python3 -m cli --log-level DEBUG compose list
```

### Linting and Formatting

Should **always** happen before pushing anything to the repository.

- Use `yamllint` for YAML files and `ruff` for Python code.

### Project Management and Git

The project is stored in a public GitHub Repository, use issues, and branches for features/bugfixes and open PRs for merging.

**Naming Conventions and Best-Practices:**
- Branches, PRs: `feature/2314-add-feature`, `problem/1249-fix-bug`
- Issues should have clear titles and descriptions, link related issues/PRs, and have appropriate labels like (problem, feature, discussion, question).
- Commit messages should be clear and concise, following the format: `type(scope): subject` (e.g., `fix(compose): correct variable parsing`).

## Architecture

### File Structure

- `cli/` - Python CLI application source code
  - `cli/core/` - Core Components of the CLI application
  - `cli/modules/` - Modules implementing variable specs and technology-specific functions
  - `cli/__main__.py` - CLI entry point, auto-discovers modules and registers commands
- `library/` - Template collections organized by module
  - `library/ansible/` - Ansible playbooks and configurations
  - `library/compose/` - Docker Compose configurations
  - `library/docker/` - Docker templates
  - `library/kubernetes/` - Kubernetes deployments
  - `library/packer/` - Packer templates
  - `library/terraform/` - OpenTofu/Terraform templates and examples

### Core Components

- `cli/core/collection.py` - Dataclass for VariableCollection (stores variable sections and variables)
- `cli/core/config.py` - Configuration management (loading, saving, validation)
- `cli/core/display.py` - Centralized CLI output rendering (**Always use this to display output - never print directly**)
- `cli/core/exceptions.py` - Custom exceptions for error handling (**Always use this for raising errors**)
- `cli/core/library.py` - LibraryManager for template discovery from git-synced libraries and static file paths
- `cli/core/module.py` - Abstract base class for modules (defines standard commands)
- `cli/core/prompt.py` - Interactive CLI prompts using rich library
- `cli/core/registry.py` - Central registry for module classes (auto-discovers modules)
- `cli/core/repo.py` - Repository management for syncing git-based template libraries
- `cli/core/section.py` - Dataclass for VariableSection (stores section metadata and variables)
- `cli/core/template.py` - Template Class for parsing, managing and rendering templates
- `cli/core/variable.py` - Dataclass for Variable (stores variable metadata and values)
- `cli/core/validators.py` - Semantic validators for template content (Docker Compose, YAML, etc.)
- `cli/core/version.py` - Version comparison utilities for semantic versioning

### Modules

**Module Structure:**
Modules can be either single files or packages:
- **Single file**: `cli/modules/modulename.py` (for simple modules)
- **Package**: `cli/modules/modulename/` with `__init__.py` (for multi-schema modules)

**Creating Modules:**
- Subclass `Module` from `cli/core/module.py`
- Define `name`, `description`, and `schema_version` class attributes
- For multi-schema modules: organize specs in separate files (e.g., `spec_v1_0.py`, `spec_v1_1.py`)
- Call `registry.register(YourModule)` at module bottom
- Auto-discovered and registered at CLI startup

**Module Spec:**
Optional class attribute for module-wide variable defaults. Example:
```python
spec = VariableCollection.from_dict({
  "general": {"vars": {"common_var": {"type": "str", "default": "value"}}},
  "networking": {"title": "Network", "toggle": "net_enabled", "vars": {...}}
})
```

**Multi-Schema Modules:**
For modules supporting multiple schema versions, use package structure:
```
cli/modules/compose/
  __init__.py          # Module class, loads appropriate spec
  spec_v1_0.py         # Schema 1.0 specification
  spec_v1_1.py         # Schema 1.1 specification
```

**Existing Modules:**
- `cli/modules/compose/` - Docker Compose package with schema 1.0 and 1.1 support
  - `spec_v1_0.py` - Basic compose spec
  - `spec_v1_1.py` - Extended with network_mode, swarm support

**(Work in Progress):** terraform, docker, ansible, kubernetes, packer modules

### LibraryManager

- Loads libraries from config file
- Stores Git Libraries under: `~/.config/boilerplates/libraries/{name}/`
- Uses sparse-checkout to clone only template directories for git-based libraries (avoiding unnecessary files)
- Supports two library types: **git** (synced from repos) and **static** (local directories)
- Priority determined by config order (first = highest)

**Library Types:**
- `git`: Requires `url`, `branch`, `directory` fields
- `static`: Requires `path` field (absolute or relative to config)

**Duplicate Handling:**
- Within same library: Raises `DuplicateTemplateError`
- Across libraries: Uses qualified IDs (e.g., `alloy.default`, `alloy.local`)
- Simple IDs use priority: `compose show alloy` loads from first library
- Qualified IDs target specific library: `compose show alloy.local`

**Config Example:**
```yaml
libraries:
  - name: default       # Highest priority (checked first)
    type: git
    url: https://github.com/user/templates.git
    branch: main
    directory: library
  - name: local         # Lower priority
    type: static
    path: ~/my-templates
    url: ''             # Backward compatibility fields
    branch: main
    directory: .
```

**Note:** Static libraries include dummy `url`/`branch`/`directory` fields for backward compatibility with older CLI versions.

### ConfigManager

- User Config stored in `~/.config/boilerplates/config.yaml`

### DisplayManager and IconManager

External code should NEVER directly call `IconManager` or `console.print`, instead always use `DisplayManager` methods.

- `DisplayManager` provides a **centralized interface** for ALL CLI output rendering (Use `display_***` methods from `DisplayManager` for ALL output)
- `IconManager` provides **Nerd Font icons** internally for DisplayManager, don't use Emojis or direct console access

## Templates

Templates are directory-based. Each template is a directory containing all the necessary files and subdirectories for the boilerplate.

Requires `template.yaml` or `template.yml` with metadata and variables:

```yaml
---
kind: compose
schema: "1.0"  # Optional: Defaults to 1.0 if not specified
metadata:
  name: My Nginx Template
  description: >
    A template for a simple Nginx service.


    Project: https://...

    Source: https://

    Documentation: https://
  version: 0.1.0
  author: Christian Lempa
  date: '2024-10-01'
spec:
  general:
    vars:
      nginx_version:
        type: string
        description: The Nginx version to use.
        default: latest
```

### Template Schema Versioning

Templates and modules use schema versioning to ensure compatibility. Each module defines a supported schema version, and templates declare which schema version they use.

```yaml
---
kind: compose
schema: "1.0"  # Defaults to 1.0 if not specified
metadata:
  name: My Template
  version: 1.0.0
  # ... other metadata fields
spec:
  # ... variable specifications
```

**How It Works:**
- **Module Schema Version**: Each module defines `schema_version` (e.g., "1.1")
- **Module Spec Loading**: Modules load appropriate spec based on template's schema version
- **Template Schema Version**: Each template declares `schema` at the top level (defaults to "1.0")
- **Compatibility Check**: Template schema ≤ Module schema → Compatible
- **Incompatibility**: Template schema > Module schema → `IncompatibleSchemaVersionError`

**Behavior:**
- Templates without `schema` field default to "1.0" (backward compatible)
- Old templates (schema 1.0) work with newer modules (schema 1.1)
- New templates (schema 1.2) fail on older modules (schema 1.1) with clear error
- Version comparison uses 2-level versioning (major.minor format)

**When to Use:**
- Increment module schema version when adding new features (new variable types, sections, etc.)
- Set template schema when using features from a specific schema
- Example: Template using new variable type added in schema 1.1 should set `schema: "1.1"`

**Single-File Module Example:**
```python
class SimpleModule(Module):
  name = "simple"
  description = "Simple module"
  schema_version = "1.0"
  spec = VariableCollection.from_dict({...})  # Single spec
```

**Multi-Schema Module Example:**
```python
# cli/modules/compose/__init__.py
class ComposeModule(Module):
  name = "compose"
  description = "Manage Docker Compose configurations"
  schema_version = "1.1"  # Highest schema version supported
  
  def get_spec(self, template_schema: str) -> VariableCollection:
    """Load spec based on template schema version."""
    if template_schema == "1.0":
      from .spec_v1_0 import get_spec
    elif template_schema == "1.1":
      from .spec_v1_1 import get_spec
    return get_spec()
```

**Version Management:**
- CLI version is defined in `cli/__init__.py` as `__version__`
- pyproject.toml version must match `__version__` for releases
- GitHub release workflow validates version consistency

### Template Files

- **Jinja2 Templates (`.j2`)**: Rendered by Jinja2, `.j2` extension removed in output. Support `{% include %}` and `{% import %}`.
- **Static Files**: Non-`.j2` files copied as-is.
- **Sanitization**: Auto-sanitized (single blank lines, no leading blanks, trimmed whitespace, single trailing newline).

### Variables

**Precedence** (lowest to highest):
1. Module `spec` (defaults for all templates of that kind)
2. Template `spec` (overrides module defaults)
3. User `config.yaml` (overrides template and module defaults)
4. CLI `--var` (highest priority)

**Variable Types:**
- `str` (default), `int`, `float`, `bool`
- `email` - Email validation with regex
- `url` - URL validation (requires scheme and host)
- `hostname` - Hostname/domain validation
- `enum` - Choice from `options` list

**Variable Properties:**
- `sensitive: true` - Masked in prompts/display (e.g., passwords)
- `autogenerated: true` - Auto-generates value if empty (shows `*auto` placeholder)
- `default` - Default value
- `description` - Variable description
- `prompt` - Custom prompt text (overrides description)
- `extra` - Additional help text
- `options` - List of valid values (for enum type)

**Section Features:**
- **Required Sections**: Mark with `required: true` (general is implicit). Users must provide all values.
- **Toggle Settings**: Conditional sections via `toggle: "bool_var_name"`. If false, section is skipped.
- **Dependencies**: Use `needs: "section_name"` or `needs: ["sec1", "sec2"]`. Dependent sections only shown when dependencies are enabled. Auto-validated (detects circular/missing/self dependencies). Topologically sorted.

**Example Section with Dependencies:**

```yaml
spec:
  traefik:
    title: Traefik
    required: false
    toggle: traefik_enabled
    vars:
      traefik_enabled:
        type: bool
        default: false
      traefik_host:
        type: hostname
  
  traefik_tls:
    title: Traefik TLS/SSL
    needs: traefik
    toggle: traefik_tls_enabled
    vars:
      traefik_tls_enabled:
        type: bool
        default: true
      traefik_tls_certresolver:
        type: str
        sensitive: false
        default: myresolver
```

## Validation

**Jinja2 Validation:**
- Templates validated for Jinja2 syntax errors during load
- Checks for undefined variables (variables used but not declared in spec)
- Built into Template class

**Semantic Validation:**
- Validator registry system in `cli/core/validators.py`
- Extensible: `ContentValidator` abstract base class
- Built-in validators: `DockerComposeValidator`, `YAMLValidator`
- Validates rendered output (YAML structure, Docker Compose schema, etc.)
- Triggered via `compose validate` command with `--semantic` flag (enabled by default)

## Prompt

Uses `rich` library for interactive prompts. Supports:
- Text input
- Password input (masked, for `sensitive: true` variables)
- Selection from list (single/multiple)
- Confirmation (yes/no)
- Default values
- Autogenerated variables (show `*auto` placeholder, generate on render)

To skip the prompt use the `--no-interactive` flag, which will use defaults or empty values.

## Commands

**Standard Module Commands** (auto-registered for all modules):
- `list` - List all templates
- `search <query>` - Search templates by ID
- `show <id>` - Show template details
- `generate <id> [directory]` - Generate from template (supports `--dry-run`, `--var`, `--no-interactive`)
- `validate [id]` - Validate templates (Jinja2 + semantic)
- `defaults` - Manage config defaults (`get`, `set`, `rm`, `clear`, `list`)

**Core Commands:**
- `repo sync` - Sync git-based libraries
- `repo list` - List configured libraries
