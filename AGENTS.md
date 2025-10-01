# AGENTS.md

This file provides guidance to AI Agents when working with code in this repository.

## Project Overview

This repository contains a sophisticated collection of templates (called boilerplates) for managing infrastructure across multiple technologies including Terraform, Docker, Ansible, Kubernetes, etc. The project also includes a Python CLI application that allows an easy management, creation, and deployment of boilerplates.

The CLI is a Python application built with Typer for the command-line interface and Jinja2 for templating.

## Repository Structure

- `cli/` - Python CLI application source code
  - `cli/core/` - Core functionality (app, config, commands, logging)
  - `cli/modules/` - Technology-specific modules (terraform, docker, compose, etc.)
- `library/` - Template collections organized by technology
  - `library/terraform/` - OpenTofu/Terraform templates and examples
  - `library/compose/` - Docker Compose configurations
  - `library/proxmox/` - Packer templates for Proxmox
  - `library/ansible/` - Ansible playbooks and configurations
  - `library/kubernetes/` - Kubernetes deployments
  - And more...

## Development Setup

### Running the CLI

```bash
# Running commands
python3 -m cli

# Debugging commands
python3 -m cli --log-level DEBUG compose list
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

#### Sub-Templates

Sub-templates are specialized templates that use dot notation in their directory names to create related template variations or components. They provide a way to organize templates hierarchically and create focused, reusable configurations.

**Directory Naming Convention:**
- Sub-templates use dot notation: `parent.sub-name`
- Example: `traefik.authentik-middleware`, `traefik.external-service`
- The parent name should match an existing template for logical grouping

**Visibility:**
- By default, sub-templates are hidden from the standard `list` command
- Use `list --all` to show all templates including sub-templates
- This keeps the default view clean while providing access to specialized templates

**Usage Examples:**
```bash
# Show only main templates (default behavior)
python3 -m cli compose list

# Show all templates including sub-templates
python3 -m cli compose list --all

# Search for templates by ID
python3 -m cli compose search traefik

# Search for templates including sub-templates
python3 -m cli compose search authentik --all

# Generate a sub-template
python3 -m cli compose generate traefik.authentik-middleware
```

**Common Use Cases:**
- Configuration variations (e.g., `service.production`, `service.development`)
- Component templates (e.g., `traefik.middleware`, `traefik.router`)
- Environment-specific templates (e.g., `app.docker`, `app.kubernetes`)

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

## Best Practices for Template Development

### Template Structure
- Always include a main `template.yaml` or `template.yml` file
- Use descriptive template IDs (directory names) with lowercase and hyphens
- Use dot notation for sub-templates (e.g., `parent.sub-name`)
- Place Jinja2 templates in subdirectories when appropriate (e.g., `config/`)

### Variable Definitions
- Define variables in module specs for common, reusable settings
- Define variables in template specs for template-specific settings
- Only override specific fields in templates (don't redefine entire variables)
- Use descriptive variable names with underscores (e.g., `external_url`, `smtp_port`)
- Always specify `type` for new variables
- Provide sensible `default` values when possible

### Jinja2 Templates
- Use `.j2` extension for all Jinja2 template files
- Use conditional blocks (`{% if %}`) for optional features
- Keep template logic simple and readable
- Use comments to explain complex logic
- Test with different variable combinations

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
