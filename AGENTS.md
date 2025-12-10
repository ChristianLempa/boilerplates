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

### Production-Ready Testing

For detailed information about testing boilerplates in a production-like environment before release, see **WARP-LOCAL.md** (local file, not in git). This document covers:
- Test server infrastructure and Docker contexts
- Step-by-step testing procedures for Docker Compose, Swarm, and Kubernetes
- Comprehensive testing checklists
- Production release criteria

### Linting and Formatting

Should **always** happen before pushing anything to the repository.

- Use `yamllint` for YAML files
- Use `ruff` for Python code:
  - `ruff check --fix .` - Check and auto-fix linting errors (including unused imports)
  - `ruff format .` - Format code according to style guidelines
  - Both commands must be run before committing

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
  - `cli/core/schema/` - JSON schema definitions for all modules
  - `cli/modules/` - Modules implementing technology-specific functions
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
- `cli/core/display/` - Centralized CLI output rendering package (**Always use DisplayManager - never print directly**)
  - `__init__.py` - Package exports (DisplayManager, DisplaySettings, IconManager)
  - `display_manager.py` - Main DisplayManager facade
  - `display_settings.py` - DisplaySettings configuration class
  - `icon_manager.py` - IconManager for Nerd Font icons
  - `variable_display.py` - VariableDisplayManager for variable rendering
  - `template_display.py` - TemplateDisplayManager for template display
  - `status_display.py` - StatusDisplayManager for status messages
  - `table_display.py` - TableDisplayManager for table rendering
- `cli/core/exceptions.py` - Custom exceptions for error handling (**Always use this for raising errors**)
- `cli/core/library.py` - LibraryManager for template discovery from git-synced libraries and static file paths
- `cli/core/module.py` - Abstract base class for modules (defines standard commands)
- `cli/core/prompt.py` - Interactive CLI prompts using rich library
- `cli/core/registry.py` - Central registry for module classes (auto-discovers modules)
- `cli/core/repo.py` - Repository management for syncing git-based template libraries
- `cli/core/schema/` - Schema management package (**JSON-based schema system**)
  - `loader.py` - SchemaLoader class for loading and validating JSON schemas
  - `<module>/` - Module-specific schema directories (e.g., `compose/`, `terraform/`)
  - `<module>/v*.json` - Version-specific JSON schema files (e.g., `v1.0.json`, `v1.2.json`)
- `cli/core/section.py` - VariableSection class (stores section metadata and variables)
  - **Key Attributes**: `key`, `title`, `toggle`, `needs`, `variables` (dict of Variable objects)
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

**Module Discovery and Registration:**

The system automatically discovers and registers modules at startup:

1. **Discovery**: CLI `__main__.py` imports all Python files in `cli/modules/` directory
2. **Registration**: Each module file calls `registry.register(ModuleClass)` at module level
3. **Storage**: Registry stores module classes in a central dictionary by module name
4. **Command Generation**: CLI framework auto-generates subcommands for each registered module
5. **Instantiation**: Modules are instantiated on-demand when commands are invoked

**Benefits:**
- No manual registration needed - just add a file to `cli/modules/`
- Modules are self-contained - can be added/removed without modifying core code
- Type-safe - registry validates module interfaces at registration time

**Module Schema System:**

**JSON Schema Architecture** (Refactored from Python specs):

All module schemas are now defined as **JSON files** in `cli/core/schema/<module>/v*.json`. This provides:
- **Version control**: Easy schema comparison and diffs in git
- **Language-agnostic**: Schemas can be consumed by tools outside Python
- **Validation**: Built-in JSON schema validation
- **Documentation**: Self-documenting schema structure

**Schema File Location:**
```
cli/core/schema/
  compose/
    v1.0.json
    v1.1.json
    v1.2.json
  terraform/
    v1.0.json
  ansible/
    v1.0.json
  ...other modules...
```

**JSON Schema Structure:**

Schemas are arrays of section objects, where each section contains:

```json
[
  {
    "key": "section_key",
    "title": "Section Title",
    "description": "Optional section description",
    "toggle": "optional_toggle_variable_name",
    "needs": "optional_dependency",
    "required": true,
    "vars": [
      {
        "name": "variable_name",
        "type": "str",
        "description": "Variable description",
        "default": "default_value",
        "required": true,
        "sensitive": false,
        "autogenerated": false,
        "options": ["option1", "option2"],
        "needs": "other_var=value",
        "extra": "Additional help text"
      }
    ]
  }
]
```

**Schema Loading in Modules:**

Modules load JSON schemas on-demand using the SchemaLoader:

```python
from cli.core.schema import load_schema, has_schema, list_versions

class MyModule(Module):
    name = "mymodule"
    schema_version = "1.2"  # Latest version supported
    
    def get_spec(self, template_schema: str) -> OrderedDict:
        """Load JSON schema and convert to dict format."""
        json_spec = load_schema(self.name, template_schema)
        # Convert JSON array to OrderedDict format
        return self._convert_json_to_dict(json_spec)
```

**Schema Design Principles:**
- **Backward compatibility**: Newer module versions can load older template schemas
- **Auto-created toggle variables**: Sections with `toggle` automatically create boolean variables
- **Conditional visibility**: Variables use `needs` constraints to show/hide based on other variable values
- **Mode-based organization**: Related settings grouped by operational mode (e.g., network_mode, volume_mode)
- **Incremental evolution**: New schemas add features without breaking existing templates

**Working with Schemas:**
- **View available versions**: Check `cli/core/schema/<module>/` directory or use `list_versions(module)`
- **Add new schema version**: Create new JSON file following naming convention (e.g., `v1.3.json`)
- **Update module**: Increment `schema_version` in module class when adding new schema
- **Validate schemas**: SchemaLoader automatically validates JSON structure on load

**Migration from Python Specs:**

Older Python-based `spec_v*.py` files have been migrated to JSON. The module `__init__.py` now:
1. Loads JSON schemas using SchemaLoader
2. Converts JSON array format to OrderedDict for backward compatibility
3. Provides lazy loading via `_SchemaDict` class

**Existing Modules:**
- `cli/modules/compose/` - Docker Compose (JSON schemas: v1.0, v1.1, v1.2)
- Other modules (ansible, terraform, kubernetes, helm, packer) - Work in Progress

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

**CRITICAL RULE - NEVER violate this:**
- NEVER use `console.print()` outside of display manager classes (`cli/core/display/` directory)
- NEVER import `Console` from `rich.console` except in display manager classes or `cli/__main__.py`
- ALWAYS use `module_instance.display.display_*()` or `display.display_*()` methods for ALL output
- Display managers (`cli/core/display/*.py`) are the ONLY exception - they implement console output

**Rationale:**
- `DisplayManager` provides a **centralized interface** for ALL CLI output rendering
- Direct console usage bypasses formatting standards, icon management, and output consistency
- `IconManager` provides **Nerd Font icons** internally for DisplayManager - never use emojis or direct icons

**DisplayManager Architecture** (Refactored for Single Responsibility Principle):

`DisplayManager` acts as a facade that delegates to specialized manager classes:

1. **VariableDisplayManager** - Handles all variable-related rendering
   - `render_variable_value()` - Variable value formatting with context awareness
   - `render_section()` - Section header display
   - `render_variables_table()` - Complete variables table with dependencies

2. **TemplateDisplayManager** - Handles all template-related rendering
   - `render_template()` - Main template display coordinator
   - `render_template_header()` - Template metadata display
   - `render_file_tree()` - Template file structure visualization
   - `render_file_generation_confirmation()` - Files preview before generation

3. **StatusDisplayManager** - Handles status messages and error display
   - `display_message()` - Core message formatting with level-based routing
   - `display_error()`, `display_warning()`, `display_success()`, `display_info()` - Convenience methods
   - `display_template_render_error()` - Detailed render error display
   - `display_warning_with_confirmation()` - Interactive warning prompts

4. **TableDisplayManager** - Handles table rendering
   - `render_templates_table()` - Templates list with library indicators
   - `render_status_table()` - Status tables with success/error indicators
   - `render_config_tree()` - Configuration tree visualization

**Usage Pattern:**
```python
# External code uses DisplayManager methods (backward compatible)
display = DisplayManager()
display.display_template(template, template_id)

# Internally, DisplayManager delegates to specialized managers
# display.templates.render_template(template, template_id)
```

**Design Principles:**
- External code calls `DisplayManager` methods only
- `DisplayManager` delegates to specialized managers internally
- Each specialized manager has a single, focused responsibility
- Backward compatibility maintained through delegation methods
- All managers can access parent DisplayManager via `self.parent`

## Templates

Templates are directory-based. Each template is a directory containing all the necessary files and subdirectories for the boilerplate.

### Template Rendering Flow

**How templates are loaded and rendered:**

1. **Discovery**: LibraryManager finds template directories containing `template.yaml`/`template.yml`
2. **Parsing**: Template class loads and parses the template metadata and spec
3. **Schema Resolution**: Module's `get_spec()` loads appropriate spec based on template's `schema` field
4. **Variable Inheritance**: Template inherits ALL variables from module schema
5. **Variable Merging**: Template spec overrides are merged with module spec (precedence: module < template < user config < CLI)
6. **Collection Building**: VariableCollection is constructed with merged variables and sections
7. **Dependency Resolution**: Sections are topologically sorted based on `needs` constraints
8. **Variable Resolution**: Variables with `needs` constraints are evaluated for visibility
9. **Jinja2 Rendering**: Template files (`.j2`) are rendered with final variable values
10. **Sanitization**: Rendered output is cleaned (whitespace, blank lines, trailing newline)
11. **Validation**: Optional semantic validation (YAML structure, Docker Compose schema, etc.)

**Key Architecture Points:**
- Templates don't "call" module specs - they declare a schema version and inherit from it
- Variable visibility is dynamic based on `needs` constraints (evaluated at prompt/render time)
- Jinja2 templates support `{% include %}` and `{% import %}` for composition

### Template Structure

Requires `template.yaml` or `template.yml` with metadata and variables:

```yaml
---
kind: compose
schema: "X.Y"  # Optional: Defaults to "1.0" if not specified (e.g., "1.0", "1.2")
metadata:
  name: My Service Template
  description: A template for a service.
  version: 1.0.0
  author: Your Name
  date: '2024-01-01'
spec:
  general:
    vars:
      service_name:
        type: str
        description: Service name
```

### Template Metadata Versioning

**Template Version Field:**
The `metadata.version` field in `template.yaml` should reflect the version of the underlying application or resource:
- **Compose templates**: Match the Docker image version (e.g., `nginx:1.25.3` → `version: 1.25.3`)
- **Terraform templates**: Match the provider version (e.g., AWS provider 5.23.0 → `version: 5.23.0`)
- **Other templates**: Match the primary application/tool version being deployed
- Use `latest` or increment template-specific version (e.g., `0.1.0`, `0.2.0`) only when no specific application version applies

**Rationale:** This helps users identify which version of the application/provider the template is designed for and ensures template versions track upstream changes.

**Application Version Variables:**
- **IMPORTANT**: Application/image versions should be **hardcoded** in template files (e.g., `image: nginx:1.25.3`)
- Do NOT create template variables for application versions (e.g., no `nginx_version` variable)
- Users should update the template file directly when they need a different version
- This prevents version mismatches and ensures templates are tested with specific, known versions
- Exception: Only create version variables if there's a strong technical reason (e.g., multi-component version pinning)

### Template Schema Versioning

**Version Format:** Schemas use 2-level versioning in `MAJOR.MINOR` format (e.g., "1.0", "1.2", "2.0").

Templates and modules use schema versioning to ensure compatibility. Each module defines a supported schema version, and templates declare which schema version they use.

```yaml
---
kind: compose
schema: "X.Y"  # Optional: Defaults to "1.0" if not specified (e.g., "1.0", "1.2")
metadata:
  name: My Template
  version: 1.0.0
  # ... other metadata fields
spec:
  # ... variable specifications
```

**How It Works:**
- **Module Schema Version**: Each module defines `schema_version` (e.g., "1.0", "1.2", "2.0")
- **Module Spec Loading**: Modules load appropriate spec based on template's schema version
- **Template Schema Version**: Each template declares `schema` at the top level (defaults to "1.0")
- **Compatibility Check**: Template schema ≤ Module schema → Compatible
- **Incompatibility**: Template schema > Module schema → `IncompatibleSchemaVersionError`

**Behavior:**
- Templates without `schema` field default to "1.0" (backward compatible)
- Older templates work with newer module versions (backward compatibility)
- Templates with newer schema versions fail on older modules with `IncompatibleSchemaVersionError`
- Version comparison uses MAJOR.MINOR format (e.g., "1.0" < "1.2" < "2.0")

**When to Use:**
- Increment module schema version when adding new features (new variable types, sections, etc.)
- Set template schema when using features from a specific schema version
- Templates using features from newer schemas must declare the appropriate schema version

**Single-File Module Example:**
```python
class SimpleModule(Module):
  name = "simple"
  description = "Simple module"
  schema_version = "X.Y"  # e.g., "1.0", "1.2"
  spec = VariableCollection.from_dict({...})  # Single spec
```

**Multi-Schema Module Example:**
```python
# cli/modules/modulename/__init__.py
class ExampleModule(Module):
  name = "modulename"
  description = "Module description"
  schema_version = "X.Y"  # Highest schema version supported (e.g., "1.2", "2.0")
  
  def get_spec(self, template_schema: str) -> VariableCollection:
    """Load spec based on template schema version."""
    # Dynamically load the appropriate spec version
    # template_schema will be like "1.0", "1.2", etc.
    version_file = f"spec_v{template_schema.replace('.', '_')}"
    spec_module = importlib.import_module(f".{version_file}", package=__package__)
    return spec_module.get_spec()
```

**Version Management:**
- CLI version is defined in `cli/__init__.py` as `__version__`
- pyproject.toml version must match `__version__` for releases
- GitHub release workflow validates version consistency

### Template Files

- **Jinja2 Templates (`.j2`)**: Rendered by Jinja2, `.j2` extension removed in output. Support `{% include %}` and `{% import %}`.
- **Static Files**: Non-`.j2` files copied as-is.
- **Sanitization**: Auto-sanitized (single blank lines, no leading blanks, trimmed whitespace, single trailing newline).
- **Shortcodes**: Template descriptions support emoji-style shortcodes (e.g., `:warning:`, `:info:`, `:docker:`) which are automatically replaced with Nerd Font icons during display. Add new shortcodes to `IconManager.SHORTCODES` dict.

### Docker Compose Best Practices

**Traefik Integration:**

When using Traefik with Docker Compose, the `traefik.docker.network` label is **CRITICAL** for stacks with multiple networks. When containers are connected to multiple networks, Traefik must know which network to use for routing.

**Implementation:**
- Review `archetypes/compose/` directory for reference implementations of Traefik integration patterns
- The `traefik.docker.network={{ traefik_network }}` label must be present in both standard `labels:` and `deploy.labels:` sections
- Standard mode and Swarm mode require different label configurations - check archetypes for examples

### Variables

**How Templates Inherit Variables:**

Templates automatically inherit ALL variables from the module schema version they declare. The template's `schema: "X.Y"` field determines which module spec is loaded, and all variables from that schema are available.

**When to Define Template Variables:**

You only need to define variables in your template's `spec` section when:
1. **Overriding defaults**: Change default values for module variables (e.g., hardcode `service_name` for your specific app)
2. **Adding custom variables**: Define template-specific variables not present in the module schema
3. **Upgrading to newer schema**: To use new features, update `schema: "X.Y"` to a higher version - no template spec changes needed

**Variable Precedence** (lowest to highest):
1. Module `spec` (defaults for all templates of that kind)
2. Template `spec` (overrides module defaults)
3. User `config.yaml` (overrides template and module defaults)
4. CLI `--var` (highest priority)

**Template Variable Override Rules:**
- **Override module defaults**: Only specify properties that differ from module spec (e.g., change `default` value)
- **Create new variables**: Define template-specific variables not in module spec
- **Minimize duplication**: Do NOT re-specify `type`, `description`, or other properties if they remain unchanged from module spec

**Example:**
```yaml
# Template declares schema: "1.2" → inherits ALL variables from compose schema 1.2
# Template spec ONLY needs to override specific defaults:
spec:
  general:
    vars:
      service_name:
        default: whoami  # Only override the default, type already defined in module
      # All other schema 1.2 variables (network_mode, volume_mode, etc.) are automatically available
```

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
- **Toggle Settings**: Conditional sections via `toggle: "bool_var_name"`. If false, section is skipped.
  - **IMPORTANT**: When a section has `toggle: "var_name"`, that boolean variable is AUTO-CREATED by the system
  - Toggle variable behavior may vary by schema version - check current schema documentation
  - Example: `ports` section with `toggle: "ports_enabled"` automatically provides `ports_enabled` boolean
- **Dependencies**: Use `needs: "section_name"` or `needs: ["sec1", "sec2"]`. Dependent sections only shown when dependencies are enabled.

**Dependency Resolution Architecture:**

Sections and variables support `needs` constraints to control visibility based on other variables.

**Section-Level Dependencies:**
- Format: `needs: "section_name"` or `needs: ["sec1", "sec2"]`
- Section only appears when all required sections are enabled (their toggle variables are true)
- Automatically validated: detects circular, missing, and self-dependencies
- Topologically sorted: ensures dependencies are prompted/processed before dependents

**Variable-Level Dependencies:**
- Format: `needs: "var_name=value"` or `needs: "var1=val1;var2=val2"` (semicolon-separated)
- Variable only visible when constraint is satisfied (e.g., `needs: "network_mode=bridge"`)
- Supports multiple values: `needs: "network_mode=bridge,macvlan"` (comma = OR)
- Evaluated dynamically at prompt and render time

**Validation:**
- Circular dependencies: Raises error if A needs B and B needs A
- Missing dependencies: Raises error if referencing non-existent sections/variables
- Self-dependencies: Raises error if section depends on itself

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
- `generate <id> -o <directory>` - Generate from template (supports `--dry-run`, `--var`, `--no-interactive`)
- `validate [template_id]` - Validate template(s) (Jinja2 + semantic). Omit template_id to validate all templates
- `defaults` - Manage config defaults (`get`, `set`, `rm`, `clear`, `list`)

**Core Commands:**
- `repo sync` - Sync git-based libraries
- `repo list` - List configured libraries

## Archetypes

The `archetypes` package provides reusable, standardized template building blocks for creating boilerplates. Archetypes are modular Jinja2 snippets that represent specific configuration sections.

### Purpose

1. **Template Development**: Provide standardized, tested building blocks for creating new templates
2. **Testing & Validation**: Enable testing of specific configuration sections in isolation with different variable combinations

### Usage

```bash
# List available archetypes for a module
python3 -m archetypes compose list

# Preview an archetype component
python3 -m archetypes compose generate <archetype-name>

# Test with variable overrides
python3 -m archetypes compose generate <archetype-name> \
  --var traefik_enabled=true \
  --var swarm_enabled=true

# Validate templates against archetypes
python3 -m archetypes compose validate            # All templates
python3 -m archetypes compose validate <template> # Single template
```

### Archetype Validation

The `validate` command compares templates against archetypes to measure coverage and identify which archetype patterns are being used.

**What it does:**
- Compares each template file against all available archetypes using **structural pattern matching**
- Abstracts away specific values to focus on:
  - **Jinja2 control flow**: `{% if %}`, `{% elif %}`, `{% else %}`, `{% for %}` structures
  - **YAML structure**: Key names, indentation, and nesting patterns
  - **Variable usage patterns**: Presence of `{{ }}` placeholders (not specific names)
  - **Wildcard placeholders**: `__ANY__`, `__ANYSTR__`, `__ANYINT__`, `__ANYBOOL__`
  - **Repeat markers**: `{# @repeat-start #}` / `{# @repeat-end #}`
  - **Optional markers**: `{# @optional-start #}` / `{# @optional-end #}`
- This allows detection of archetypes even when specific values differ (e.g., `grafana_data` vs `alloy_data`)
- Calculates **containment ratio**: what percentage of each archetype structure is found within the template
- Reports usage status: **exact** (≥95%), **high** (≥70%), **partial** (≥30%), or **none** (<30%)
- Provides coverage metrics: (exact + high matches) / total archetypes

### Advanced Pattern Matching in Archetypes

Archetypes support special annotations for flexible pattern matching:

**Wildcard Placeholders** (match any value):
- `__ANY__` - Matches anything
- `__ANYSTR__` - Matches any string
- `__ANYINT__` - Matches any integer
- `__ANYBOOL__` - Matches any boolean

**Repeat Markers** (pattern can appear 1+ times):
```yaml
{# @repeat-start #}
  pattern
{# @repeat-end #}
```

**Optional Markers** (section may or may not exist):
```yaml
{# @optional-start #}
  pattern
{# @optional-end #}
```

**Example:**
```yaml
volumes:
  {# @repeat-start #}
  __ANY__:
    driver: local
  {# @repeat-end #}
```
Matches any number of volumes with `driver: local`

**Usage:**
```bash
# Validate all templates in library - shows summary table
python3 -m archetypes compose validate

# Validate specific template - shows detailed archetype breakdown
python3 -m archetypes compose validate whoami

# Validate templates in custom location
python3 -m archetypes compose validate --library /path/to/templates
```

**Output:**
- **Summary mode** (all templates): Table showing exact/high/partial/none counts and coverage % per template
- **Detail mode** (single template): Table showing each archetype's status, similarity %, and matching file

**Use cases:**
- **Quality assurance**: Ensure templates follow established patterns
- **Refactoring**: Identify templates that could benefit from archetype alignment
- **Documentation**: Track which archetypes are most/least used across templates

### Template Development Workflow

1. **Discover**: Use `list` command to see available archetype components for your module
2. **Review**: Preview archetypes to understand implementation patterns
3. **Copy**: Copy relevant archetype components to your template directory
4. **Customize**: Modify as needed (hardcode image, add custom labels, etc.)
5. **Validate**: Use `compose validate` to check Jinja2 syntax and semantic correctness

### Architecture

**Key Concepts:**
- Each module can have its own `archetypes/<module>/` directory with reusable components
- `archetypes.yaml` configures schema version and variable overrides for testing
- Components are modular Jinja2 files that can be tested in isolation or composition
- **Testing only**: The `generate` command NEVER writes files - always shows preview output

**How it works:**
- Loads module spec based on schema version from `archetypes.yaml`
- Merges variable sources: module spec → archetypes.yaml → CLI --var
- Renders using Jinja2 with support for `{% include %}` directives
