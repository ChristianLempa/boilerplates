# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

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

### Installation and Dependencies

```bash
# Install in development mode
pip install -e .

# Install from requirements
pip install -r requirements.txt
```

### Running the CLI

```bash
# Run via Python module
python -m cli --help

# Run via installed command
boilerplate --help

# Example module usage
boilerplate terraform --help
boilerplate compose config list
```

## Common Development Tasks

### Testing and Validation

```bash
# Lint YAML files (used in CI)
yamllint --strict -- $(git ls-files '*.yaml' '*.yml')

# Run CLI with debug logging
boilerplate --log-level DEBUG [command]
```

### Adding New Modules

1. Create new module file: `cli/modules/[module_name].py`
2. Implement module class inheriting from `BaseModule` in the file
3. Add module to imports in `cli/__main__.py`
4. Create corresponding template directory in `library/[module_name]/`

## Architecture Notes

### CLI Architecture

- **Modular Design**: Each technology (terraform, docker, etc.) is implemented as a separate module
- **Configuration Management**: Per-module configuration stored in `~/.boilerplates/[module].json`
- **Template System**: Uses Jinja2 for template processing with frontmatter metadata
- **Rich UI**: Uses Rich library for enhanced terminal output and tables

### Key Components

- `ConfigManager`: Handles module-specific configuration persistence
- `BaseModule`: Abstract base class providing shared commands (config management)
- Module Commands: Each module implements technology-specific operations
- Template Library: Structured collection of boilerplates with metadata
- `Template.variable_sections`: Ordered sections with merged metadata and defaults (combined from module variable sections and template frontmatter)
- `PromptHandler`: Interactive prompting based on vars_map and template usage

### Template Format

Templates use YAML frontmatter for metadata:

```yaml
---
name: "Template Name"
description: "Template description"
version: "0.0.1"
date: "2023-10-01"
author: "Christian Lempa"
tags:
  - tag1
  - tag2
---
[Template content here]
```

## Important Rules and Conventions

- **Docker Compose**: Default to `compose.yaml` filename (not `docker-compose.yml`)
- **Logging Standards**: No emojis, avoid multi-lines, use proper log levels
- **Comment Anchors**: Use for TODOs, FIXMEs, notes, and links in source code
- **Spaces in Python**: Prefer using 2 Spaces for indentation

## Architecture Optimization (2025-09-07)

The codebase has been optimized following the ARCHITECTURE_OPTIMIZATION.md plan:

### Simplified Variable System (2025-09)
- Replaced custom registry with a unified variables map (vars_map) on Template
- Module variables are defined via nested `variable_sections` blocks and merged with template frontmatter sections
- Dotted names (e.g., traefik.tls.certresolver) imply hierarchy for prompting/sections
- No separate Variable/Registry classes needed

### Streamlined Module System
- Removed decorator pattern (@register_module)
- Direct module registration with registry.register()
- Class attributes instead of runtime __init__ modification
- Simplified module implementation

### Clean Registry
- Removed runtime __init__ modifications
- Simple explicit registration
- No decorator magic

### Module Implementation Pattern
```python
from ..core.module import Module
from ..core.registry import registry
from ..core.variables import Variable

class ExampleModule(Module):
  """Module description."""
  
  name = "example"
  description = "Manage example configurations"
  files = ["example.conf", "example.yaml"]
  
  def _init_variables(self):
    """Initialize module-specific variables."""
    # Register groups
    self.variables.register_group("general", "General Settings")
    
    # Register variables
    self.variables.register_variable(Variable(
      name="var_name",
      description="Variable description",
      group="general"
    ))

# Register the module
registry.register(ExampleModule)
```

## Configuration

- YAML linting configured with max 160 character line length
- Python 3.9+ required
- Rich markup mode enabled for enhanced CLI output
- Logging configurable via `--log-level` flag
