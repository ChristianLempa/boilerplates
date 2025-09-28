# AGENTS.md

This file provides guidance to AI Agents when working with code in this repository.

## Project Overview

This repository contains a sophisticated collection of templates (called boilerplates) for managing infrastructure across multiple technologies including Terraform, Docker, Ansible, Kubernetes, etc. The project also includes a Python CLI application that allows an easy management, creation, and deployment of boilerplates.

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

- **`cli/core/module.py`**: Defines the abstract `Module` base class. Each technology (e.g., `compose`, `terraform`) is a subclass of `Module`. It standardizes the `list`, `show`, and `generate` commands and handles their registration.

- **`cli/core/library.py`**: Implements the `LibraryManager` and `Library` classes, which are responsible for finding template files within the `library/` directory. It supports a priority system, allowing different template sources to override each other.

- **`cli/core/template.py`**: Contains the `Template` class, which is the heart of the engine. It parses a template file, separating the YAML frontmatter (metadata, variable specifications) from the Jinja2 content. It intelligently merges variable definitions from both the module and the template file.

- **`cli/core/variables.py`**: Defines the data structures for managing variables:
  - `Variable`: Represents a single variable, including its type, validation rules, and default value.
  - `VariableSection`: Groups variables into logical sections for better presentation and conditional logic.
  - `VariableCollection`: Manages the entire set of sections and variables for a template.

- **`cli/core/prompt.py`**: The `PromptHandler` provides the interactive CLI experience. It uses the `rich` library to prompt the user for variable values, organized by the sections defined in the `VariableCollection`.

### Template Format

Templates use YAML frontmatter for metadata, followed by the actual template content with Jinja2 syntax. Example:

```yaml
---
kind: "compose|terraform|ansible|kubernetes|..."
metadata:
  name: "Template Name"
  description: "Template description"
  version: "0.0.1"
  date: "2023-10-01"
  author: "Christian Lempa"
  tags:
    - tag1
    - tag2
spec:
  section1:
    description: "Description of section1"
    prompt: "Do you want to configure section1?"
    toggle: "section1_enabled"
    required: false|true
    section1_enabled:
      type: "bool"
      description: "Enable section1"
      default: false
    section1_var2:
      type: "string|int|bool|list|dict"
      description: "Description of var1"
      default: "default_value"
---
# Actual template content with Jinja2 syntax
services:
  my_service:
    image: "{{ section1_var2 | default('nginx') }}"
    ...
```

#### Variables

Variables are a cornerstone of the CLI, allowing for dynamic and customizable template generation. They are defined and processed with a clear precedence and logic.

**1. Definition and Precedence:**

Variables are sourced and merged from multiple locations, with later sources overriding earlier ones:

1.  **Module `spec` (Lowest Precedence)**: Each module (e.g., `cli/modules/compose.py`) can define a base `spec` dictionary. This provides default variables and sections for all templates of that `kind`.
2.  **Template `spec`**: The `spec` block within a template file's frontmatter can override or extend the module's `spec`. This allows a template to customize variable descriptions, defaults, or add new variables.
3.  **Jinja2 `default` Filter**: A `default` filter used directly in the template content (e.g., `{{ my_var | default('value') }}`) will override any `default` value defined in the `spec` blocks.
4.  **CLI Overrides (`--var`) (Highest Precedence)**: Providing a variable via the command line (`--var KEY=VALUE`) has the highest priority and will override any default or previously set value.

The `Variable.origin` attribute is updated to reflect this chain (e.g., `module -> template -> cli`).

**2. Required Sections:**

- A section in the `spec` can be marked as `required: true`.
- The `general` section is implicitly required by default.
- During an interactive session, users must provide inputs for all variables within a required section and cannot skip it.

**3. Toggle Settings (Conditional Sections):**

- A section can be made conditional by setting the `toggle` property to the name of a boolean variable within that same section.
- **Example**: `toggle: "advanced_enabled"`
- During an interactive session, the CLI will first ask the user to enable or disable the section by prompting for the toggle variable (e.g., "Enable advanced settings?").
- If the section is disabled (the toggle is `false`), all other variables within that section are skipped, and the section is visually dimmed in the summary table. This provides a clean way to manage optional or advanced configurations.

## Future Improvements

### Work in Progress

* TODO[1-secret-support] Consider creating a "secret" variable type that automatically handles sensitive data and masks input during prompts, which also should be set via .env file and not directly in the compose files or other templates.
  * Implement multi-file support for templates, allowing jinja2 in other files as well
  * Mask secrets in rendering output (e.g. when displaying the final docker-compose file, mask secret values)
  * Add support for --out to specify a directory
* Add support for more complex validation rules for environment variables, such as regex patterns or value ranges.
* Add configuration support to allow users to override module and template spec with their own (e.g. defaults -> compose -> spec -> general ...)
* Add an installation script when cloning the repo and setup necessary commands
* Add an automatic update script to keep the tool up-to-date with the latest version from the repository.
* Add compose deploy command to deploy a generated compose project to a local or remote docker environment
