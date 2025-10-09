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

- Use `yamllint` for YAML files and `pylint` for Python code.
- Use `2` spaces for YAML and Python indentation.

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
- `cli/core/sections.py` - Dataclass for VariableSection (stores section metadata and variables)
- `cli/core/template.py` - Template Class for parsing, managing and rendering templates
- `cli/core/variables.py` - Dataclass for Variable (stores variable metadata and values)

### Modules

- `cli/modules/compose.py` - Docker Compose-specific functionality
**(Work in Progress)**
- `cli/modules/terraform.py` - Terraform-specific functionality
- `cli/modules/docker.py` - Docker-specific functionality
- `cli/modules/ansible.py` - Ansible-specific functionality
- `cli/modules/kubernetes.py` - Kubernetes-specific functionality
- `cli/modules/packer.py` - Packer-specific functionality

### LibraryManager

- Loads libraries from config file
- Stores Git Libraries under: `~/.config/boilerplates/libraries/{name}/`
- Uses sparse-checkout to clone only template directories for git-based libraries (avoiding unnecessary files)

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

**Key Features:**
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

## Prompt

Uses `rich` library for interactive prompts. Supports:
- Text input
- Password input (masked)
- Selection from list (single/multiple)
- Confirmation (yes/no)
- Default values

To skip the prompt use the `--no-interactive` flag, which will use defaults or empty values.
