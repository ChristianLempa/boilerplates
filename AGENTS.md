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
- `archetypes/` - Testing tool for template snippets (archetype development)
  - `archetypes/__init__.py` - Package initialization
  - `archetypes/__main__.py` - CLI tool entry point
  - `archetypes/<module>/` - Module-specific archetype snippets (e.g., `archetypes/compose/`)

### Core Components

- `cli/core/collection.py` - VariableCollection class (manages sections and variables)
  - **Key Attributes**: `_sections` (dict of VariableSection objects), `_variable_map` (flat lookup dict)
  - **Key Methods**: `get_satisfied_values()` (returns enabled variables), `apply_defaults()`, `sort_sections()`
- `cli/core/config.py` - Configuration management (loading, saving, validation)
- `cli/core/display.py` - Centralized CLI output rendering (**Always use this to display output - never print directly**)
- `cli/core/exceptions.py` - Custom exceptions for error handling (**Always use this for raising errors**)
- `cli/core/library.py` - LibraryManager for template discovery from git-synced libraries and static file paths
- `cli/core/module.py` - Abstract base class for modules (defines standard commands)
- `cli/core/prompt.py` - Interactive CLI prompts using rich library
- `cli/core/registry.py` - Central registry for module classes (auto-discovers modules)
- `cli/core/repo.py` - Repository management for syncing git-based template libraries
- `cli/core/section.py` - VariableSection class (stores section metadata and variables)
  - **Key Attributes**: `key`, `title`, `toggle`, `required`, `needs`, `variables` (dict of Variable objects)
- `cli/core/template.py` - Template Class for parsing, managing and rendering templates
- `cli/core/variable.py` - Variable class (stores variable metadata and values)
  - **Key Attributes**: `name`, `type`, `value` (stores default or current value), `description`, `sensitive`, `needs`
  - **Note**: Default values are stored in `value` attribute, NOT in a separate `default` attribute
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
Module-wide variable specification defining defaults for all templates of that kind.

**Important**: The `spec` variable is an **OrderedDict** (or regular dict), NOT a VariableCollection object. It's converted to VariableCollection when needed.

Example:
```python
from collections import OrderedDict

# Spec is a dict/OrderedDict, not a VariableCollection
spec = OrderedDict({
  "general": {
    "title": "General",
    "vars": {
      "common_var": {
        "type": "str",
        "default": "value",
        "description": "A common variable"
      }
    }
  },
  "networking": {
    "title": "Network",
    "toggle": "net_enabled",
    "vars": {...}
  }
})

# To use the spec, convert it to VariableCollection:
from cli.core.collection import VariableCollection
variable_collection = VariableCollection(spec)
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

### Docker Compose Best Practices

**Traefik Integration:**

When using Traefik with Docker Compose, the `traefik.docker.network` label is **CRITICAL** for stacks with multiple networks. When containers are connected to multiple networks, Traefik must know which network to use for routing.

**Implementation:**
- ALL templates using Traefik MUST follow the patterns in `archetypes/compose/traefik-v1.j2` (standard mode) and `archetypes/compose/swarm-v1.j2` (swarm mode)
- These archetypes are the authoritative reference for correct Traefik label configuration
- The `traefik.docker.network={{ traefik_network }}` label must be present in both standard `labels:` and `deploy.labels:` sections

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

## Archetypes Testing Tool

The `archetypes` package provides a testing tool for developing and testing individual template snippets (Jinja2 files) without needing a full template directory structure.

### Purpose

Archetypes are template "snippets" or "parts" that can be tested in isolation. This is useful for:
- Developing specific sections of templates (e.g., network configurations, volume mounts)
- Testing Jinja2 logic with different variable combinations
- Validating template rendering before integrating into full templates

### Usage

```bash
# Run the archetypes tool
python3 -m archetypes

# List all archetypes for a module
python3 -m archetypes compose list

# Show details of an archetype (displays variables and content)
python3 -m archetypes compose show network-v1

# Preview generated output (always in preview mode - never writes files)
python3 -m archetypes compose generate network-v1

# Preview with variable overrides
python3 -m archetypes compose generate network-v1 \
  --var network_mode=macvlan \
  --var network_macvlan_ipv4_address=192.168.1.100

# Preview with reference directory (for context only - no files written)
python3 -m archetypes compose generate network-v1 /tmp/output --var network_mode=host
```

### Structure

```
archetypes/
  __init__.py           # Package initialization
  __main__.py           # CLI tool (auto-discovers modules)
  compose/              # Module-specific archetypes
    network-v1.j2       # Archetype snippet (just a .j2 file)
    volumes-v1.j2       # Another archetype
  terraform/            # Another module's archetypes
    vpc.j2
```

### Key Features

- **Auto-discovers modules**: Scans `archetypes/` for subdirectories (module names)
- **Reuses CLI components**: Imports actual CLI classes (Template, VariableCollection, DisplayManager) for identical behavior
- **Loads module specs**: Pulls variable specifications from `cli/modules/<module>/spec_v*.py` for defaults
- **Full variable context**: Provides ALL variables with defaults (not just satisfied ones) for complete rendering
- **Three commands**: `list`, `show`, `generate`
- **Testing only**: The `generate` command NEVER writes files - it always shows preview output only

### Implementation Details

**How it works:**
1. Module discovery: Finds subdirectories in `archetypes/` (e.g., `compose`)
2. For each module, creates a Typer sub-app with list/show/generate commands
3. Archetype files are simple `.j2` files (no `template.yaml` needed)
4. Variable defaults come from module spec: `cli/modules/<module>/spec_v*.py`
5. Rendering uses Jinja2 with full variable context from spec

**ArchetypeTemplate class:**
- Simplified template wrapper for single .j2 files
- Loads module spec and converts to VariableCollection
- Extracts ALL variables (not just satisfied) from spec sections
- Merges user overrides (`--var`) on top of spec defaults
- Renders using Jinja2 FileSystemLoader

**Variable defaults source:**
```python
# Defaults come from module spec files
from cli.modules.compose import spec  # OrderedDict with variable definitions
vc = VariableCollection(spec)         # Convert to VariableCollection

# Extract all variables with their default values
for section_name, section in vc._sections.items():
    for var_name, var in section.variables.items():
        if var.value is not None:  # var.value stores the default
            render_context[var_name] = var.value
```
