# AGENTS.md

This file provides guidance to AI Agents when working with code in this repository.

## Project Overview

This repository contains a sophisticated collection of templates (called boilerplates) for managing infrastructure across multiple technologies including Terraform, Docker, Ansible, Kubernetes, etc. The project also includes a Python CLI application that allows an easy management, creation, and deployment of boilerplates.

The CLI is a Python application built with Typer for the command-line interface and Jinja2 for templating.

## Repository Structure

- `cli/` - Python CLI application source code
  - `cli/core/` - Core functionality (app, config, commands, logging)
  - `cli/modules/` - Technology-specific modules (terraform, docker, compose, config, etc.)
- `library/` - Template collections organized by module
  - `library/ansible/` - Ansible playbooks and configurations
  - `library/ci/` - CI/CD automation templates (GitHub Actions, GitLab CI, Kestra)
  - `library/config/` - Application-specific configuration templates
  - `library/compose/` - Docker Compose configurations
  - `library/kubernetes/` - Kubernetes deployments
  - `library/terraform/` - OpenTofu/Terraform templates and examples
  - And more...

## Development Setup

### Running the CLI

```bash
# List available commands
python3 -m cli

# List templates for a module
python3 -m cli compose list

# Debugging commands
python3 -m cli --log-level DEBUG compose list

# Generate template to directory named after template (default)
python3 -m cli compose generate nginx

# Generate template to custom directory
python3 -m cli compose generate nginx my-nginx-server

# Generate template interactively (default - prompts for variables)
python3 -m cli compose generate authentik

# Generate template non-interactively (skips prompts, uses defaults and CLI variables)
python3 -m cli compose generate authentik my-auth --no-interactive

# Generate with variable overrides (non-interactive)
python3 -m cli compose generate authentik my-auth \
  --var service_name=auth \
  --var ports_enabled=false \
  --var database_type=postgres \
  --no-interactive

# Show template details
python3 -m cli compose show authentik

# Managing default values
python3 -m cli compose defaults set service_name my-app
python3 -m cli compose defaults get
python3 -m cli compose defaults list
```

## Common Development Tasks

## Architecture Notes

### Key Components

The CLI application is built with a modular and extensible architecture.

- **`cli/__main__.py`**: The main entry point using `Typer`. It dynamically discovers and imports modules from the `cli/modules` directory, registering their commands with the main application.

- **`cli/core/registry.py`**: Provides a `ModuleRegistry` which acts as a central store for all discovered module classes. This avoids magic and keeps module registration explicit.

- **`cli/core/module.py`**: Defines the abstract `Module` base class. Each technology (e.g., `compose`, `terraform`) is a subclass of `Module`. It standardizes the `list`, `search`, `show`, and `generate` commands and handles their registration.

- **`cli/core/library.py`**: Implements the `LibraryManager` and `Library` classes, which are responsible for finding template files within the `library/` directory. It supports a priority system, allowing different template sources to override each other.

- **`cli/core/template.py`**: Contains the `Template` class, which is the heart of the engine. It parses a template file, separating the YAML frontmatter (metadata, variable specifications) from the Jinja2 content. It intelligently merges variable definitions from both the module and the template file.

- **`cli/core/variables.py`**: Defines the data structures for managing variables:
  - `Variable`: Represents a single variable, including its type, validation rules, and default value.
  - `VariableSection`: Groups variables into logical sections for better presentation and conditional logic.
  - `VariableCollection`: Manages the entire set of sections and variables for a template.

- **`cli/core/prompt.py`**: The `PromptHandler` provides the interactive CLI experience. It uses the `rich` library to prompt the user for variable values, organized by the sections defined in the `VariableCollection`.

- **`cli/core/display.py`**: The `DisplayManager` handles all output rendering using `rich`. It provides consistent and visually appealing displays for lists, search results, variable summaries, and error messages.

### Template Format

Templates are directory-based. Each template is a directory containing all the necessary files and subdirectories for the boilerplate.

#### Main Template File

Every template directory must contain a main template file named either `template.yaml` or `template.yml`. This file serves as the entry point and contains the template's metadata and variable specifications in YAML frontmatter format.

Example `template.yaml`:

```yaml
---
kind: compose
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

#### Template Files

-   **Jinja2 Templates (`.j2`)**: Any file within the template directory that has a `.j2` extension will be rendered by the Jinja2 engine. The `.j2` extension is removed from the final output file name (e.g., `config.json.j2` becomes `config.json`). These files can use `{% include %}` and `{% import %}` statements to share code with other files in the template directory.

-   **Static Files**: Any file without a `.j2` extension is treated as a static file and will be copied to the output directory as-is, preserving its relative path and filename.

-   **Content Sanitization**: All rendered Jinja2 templates are automatically sanitized to improve output quality:
    - Multiple consecutive blank lines are reduced to a single blank line
    - Leading blank lines are removed
    - Trailing whitespace is stripped from each line
    - Files are ensured to end with exactly one newline character
    - This prevents common formatting issues from conditional Jinja2 blocks

#### Example Directory Structure

```
library/compose/my-nginx-template/
├── template.yaml
├── compose.yaml.j2
├── config/
│   └── nginx.conf.j2
└── static/
    └── README.md
```

#### Variables

Variables are a cornerstone of the CLI, allowing for dynamic and customizable template generation. They are defined and processed with a clear precedence and logic.

**1. Definition and Precedence:**

Variables are sourced and merged from multiple locations, with later sources overriding earlier ones:

1.  **Module `spec` (Lowest Precedence)**: Each module (e.g., `cli/modules/compose.py`) can define a base `spec` dictionary. This provides default variables and sections for all templates of that `kind`.
2.  **Template `spec`**: The `spec` block within the `template.yaml` or `template.yml` file can override or extend the module's `spec`. This is the single source of truth for defaults within the template.
3.  **CLI Overrides (`--var`) (Highest Precedence)**: Providing a variable via the command line (`--var KEY=VALUE`) has the highest priority and will override any default or previously set value.

The `Variable.origin` attribute is updated to reflect this chain (e.g., `module -> template -> cli`).

**2. Required Sections:**

- A section in the `spec` can be marked as `required: true`.
- The `general` section is implicitly required by default.
- During an interactive session, users must provide inputs for all variables within a required section and cannot skip it.

**3. Toggle Settings (Conditional Sections):**

- A section can be made conditional by setting the `toggle` property to the name of a boolean variable within that same section.
- **Example**: `toggle: "advanced_enabled"`
- **Validation**: The toggle variable MUST be of type `bool`. This is validated at load-time by `VariableCollection._validate_section_toggle()`.
- During an interactive session, the CLI will first ask the user to enable or disable the section by prompting for the toggle variable (e.g., "Enable advanced settings?").
- If the section is disabled (the toggle is `false`), all other variables within that section are skipped, and the section is visually dimmed in the summary table. This provides a clean way to manage optional or advanced configurations.

**4. Section Dependencies:**

- Sections can declare dependencies on other sections using the `needs` property.
- **Example**: `needs: "traefik"` or `needs: ["database", "redis"]` for multiple dependencies.
- **Purpose**: Ensures that dependent sections are only shown/processed when their dependency sections are enabled.
- **Behavior**:
  - During interactive prompting: If a dependency is not satisfied (disabled or not enabled), the dependent section is automatically skipped with a message like `⊘ Section Name (skipped - requires dependency_name to be enabled)`.
  - During non-interactive generation: Variables from sections with unsatisfied dependencies are excluded from the Jinja2 rendering context.
  - During validation: Sections with unsatisfied dependencies are skipped.
- **Validation**: Dependencies are validated at template load time:
  - Circular dependencies are detected and cause an error (e.g., A needs B, B needs A).
  - Missing dependencies cause an error (e.g., A needs B, but B doesn't exist).
  - Self-dependencies cause an error (e.g., A needs A).
- **Sorting**: Sections are automatically sorted using topological sort to ensure dependencies come before dependents, while preserving the original order within priority groups (required, enabled, disabled).
- **Use Cases**:
  - Split complex configurations: e.g., `traefik` (basic) and `traefik_tls` (needs traefik) sections.
  - Conditional features: e.g., `database_backup` (needs database) or `monitoring_alerts` (needs monitoring).
  - Hierarchical settings: e.g., `email` (basic) and `email_advanced` (needs email) sections.

**Example Section with Dependencies:**

```yaml
spec:
  traefik:
    title: "Traefik"
    toggle: "traefik_enabled"
    vars:
      traefik_enabled:
        type: "bool"
        default: false
      traefik_host:
        type: "hostname"
  
  traefik_tls:
    title: "Traefik TLS/SSL"
    needs: "traefik"  # Only shown if traefik is enabled
    toggle: "traefik_tls_enabled"
    vars:
      traefik_tls_enabled:
        type: "bool"
        default: true
      traefik_tls_certresolver:
        type: "str"
```

## Future Improvements

### Managing TODOs as GitHub Issues

We use a convention to manage TODO items as GitHub issues directly from the codebase. This allows us to track our work and link it back to the specific code that needs attention.

The format for a TODO item is:

`TODO[<issue-number>-<slug>] <description>`

-   `<issue-number>`: The GitHub issue number.
-   `<slug>`: A short, descriptive slug for the epic or feature.
-   `<description>`: The description of the TODO item.

When you find a TODO item that has not been converted to an issue yet (i.e., it's missing the `[<issue-number>-<slug>]` part), you can create an issue for it using the `gh` CLI:

```bash
gh issue create --title "<title>" --body "<description>" --assignee "@me" --project "<project-name>" --label "<label>"
```

After creating the issue, update the TODO line in the `AGENTS.md` file with the issue number and a descriptive slug.

### Work in Progress

* FIXME We need proper validation to ensure all variable names are unique across all sections (currently allowed but could cause conflicts)
* FIXME Insufficient Error Messages for Template Loading
* FIXME Excessive Generic Exception Catching
* FIXME No Rollback on Config Write Failures: If writing config fails partway through, the config file can be left in a corrupted state. There's no atomic write operation.
* FIXME Inconsistent Logging Levels: Some important operations use `DEBUG` when they should use `INFO`, and vice versa.
* TODO Memory Inefficiency in Template File Collection: The template loads all file paths into memory immediately, even when only metadata is needed (like for `list` command). This is wasteful when listing many templates.
* TODO Missing Input Validation in ConfigManager
* TODO Add compose deploy command to deploy a generated compose project to a local or remote docker environment
* TODO No Caching for Module Specs: Each template loads module specs independently. If listing 50 compose templates, the compose module spec is imported 50 times.
* TODO Missing Type Hints in Some Functions: While most code has type hints, some functions are missing them, reducing IDE support and static analysis capability.
* TODO No Dry-Run Mode for Generate Command: A dry-run mode would allow users to see what files would be generated without actually writing them to disk.
* TODO Template Validation Command: A command to validate the structure and variable definitions of a template without generating it.
* TODO Interactive Variable Prompt Improvements: The interactive prompt could be improved with better navigation, help text, and validation feedback.
* TODO Better Error Recovery in Jinja2 Rendering
* TODO Icon Management Class in DisplayManager: Create a centralized icon management system in `cli/core/display.py` to standardize icons used throughout the CLI for file types (.yaml, .j2, .json, etc.), status indicators (success, warning, error, info), and UI elements. This would improve consistency, make icons easier to maintain, and allow for theme customization.

## Best Practices for Template Development

### Template Structure
- Always include a main `template.yaml` or `template.yml` file
- Use descriptive template IDs (directory names) with lowercase and hyphens
- Place Jinja2 templates in subdirectories when appropriate (e.g., `config/`)
- For application-specific configs, create templates in the `config` module instead of using complex directory structures

### Variable Definitions
- **Prefer module spec variables first**: Always check if a variable exists in the module spec before adding template-specific variables. Use existing module variables where possible to maintain consistency across templates.
- **Override module variables when needed**: If a module variable needs different behavior for a specific template, override its `description`, `default`, or `extra` properties in the template spec rather than creating a new variable.
- **Add template-specific variables only when necessary**: Only create new variables in the template spec when they are truly unique to that template and don't fit into existing module variables.
- Use descriptive names with underscores (e.g., `external_url`, `smtp_port`)
- Always specify `type` and provide sensible `default` values
- Mark sensitive data with `sensitive: true` and `autogenerated: true` for auto-generated secrets
- Use `pwgen` filter for password generation: `{{ secret_key if secret_key else (none | pwgen(50)) }}`

**Example**: For the Traefik template, use the existing `authentik` section from the module spec instead of creating custom `authentik_middleware_*` variables. Override the section's `description` and `extra` to provide Traefik-specific guidance.

### Jinja2 Templates
- Use `.j2` extension and always use `| default()` filter for safe fallbacks
- Use conditional blocks for optional features and keep logic simple
- Add descriptive comments in generated files

### Docker Compose Specific Practices

#### Variable Naming Conventions
- **Service/Container**: `service_name`, `container_name`, `container_timezone`, `restart_policy`
- **Application**: Prefix with app name (e.g., `authentik_secret_key`, `gitea_root_url`)
- **Database**: `database_type`, `database_enabled`, `database_external`, `database_host`, `database_port`, `database_name`, `database_user`, `database_password`
- **Network**: `network_enabled`, `network_name`, `network_external`
- **Traefik**: `traefik_enabled`, `traefik_host`, `traefik_tls_enabled`, `traefik_tls_entrypoint`, `traefik_tls_certresolver`
- **Ports**: `ports_enabled`, `ports_http`, `ports_https`, `ports_ssh`
- **Email**: `email_enabled`, `email_host`, `email_port`, `email_username`, `email_password`, `email_from`

#### Scoped Environment Files
Use separate `.env.{service}.j2` files for different services (e.g., `.env.authentik.j2`, `.env.postgres.j2`):

- Benefits: Better security, cleaner organization, easier management, reusable configs
- Usage: Reference via `env_file` directive in `compose.yaml.j2`
- Structure: Group related settings with comments (e.g., `# Database Connection`)

#### Common Toggle Patterns
- `database_enabled`, `email_enabled`, `traefik_enabled`, `ports_enabled`, `network_enabled`

#### Docker Compose Template Patterns
- Always define `depends_on` for startup ordering and use named volumes for persistence
- Include health checks for database services
- Use `{% if not database_external %}` for conditional service creation
- Group Traefik labels logically with proper service/router configuration
- Always include `restart: {{ restart_policy | default('unless-stopped') }}`
- Support both internal and external databases/services with conditionals

### Module Specs
- Define common sections that apply to all templates of that kind
- Use toggle variables for optional sections
- Provide comprehensive descriptions for user guidance
- Group related variables into logical sections
- Validate toggle variables are boolean type

### Testing Templates
- Test generation with default values
- Test with toggle sections enabled and disabled
- Test with edge cases (empty values, special characters)
- Verify yamllint compliance for YAML files
- Check that generated files are syntactically valid
