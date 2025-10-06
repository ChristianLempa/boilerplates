# AGENTS.md

Guidance for AI Agents working with this repository.

## Project Overview

A sophisticated collection of infrastructure templates (boilerplates) with a Python CLI for management. Supports Terraform, Docker, Ansible, Kubernetes, etc. Built with Typer (CLI) and Jinja2 (templating).

## Repository Structure

- `cli/` - Python CLI application source code
  - `cli/core/` - Core functionality (app, config, commands, logging)
  - `cli/modules/` - Technology-specific modules (terraform, docker, compose, config, etc.)
- `library/` - Template collections organized by module
  - `library/ansible/` - Ansible playbooks and configurations
  - `library/compose/` - Docker Compose configurations
  - `library/docker/` - Docker templates
  - `library/kubernetes/` - Kubernetes deployments
  - `library/packer/` - Packer templates
  - `library/terraform/` - OpenTofu/Terraform templates and examples

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

## Release Management

**Process:** Tag-based workflow via `.github/workflows/release.yaml`. Push a semver tag (e.g., `v1.2.3`) to trigger.

**Workflow Steps:**
1. Extracts version from tag
2. Auto-updates `pyproject.toml` and `cli/__main__.py` with version
3. Recreates tag pointing to version bump commit
4. Builds wheel/tarball
5. Creates GitHub release (marks alpha/beta/rc as pre-release)

**Important:** Never manually edit version numbers - they're placeholders (`0.0.0`) that get auto-updated.

**User Installation:**
```bash
# Latest
curl -fsSL https://raw.githubusercontent.com/christianlempa/boilerplates/main/scripts/install.sh | bash

# Specific version
curl -fsSL https://raw.githubusercontent.com/christianlempa/boilerplates/main/scripts/install.sh | bash -s -- --version v1.2.3
```

The `install.sh` script downloads the release tarball and installs via pipx. PyPI publishing is currently disabled.

## Architecture Notes

### Key Components

Modular architecture with dynamic module discovery:

- **`cli/__main__.py`**: Entry point. Auto-discovers modules and registers commands.
- **`cli/core/registry.py`**: Central module class store.
- **`cli/core/module.py`**: Abstract `Module` base class for standardized commands (list, search, show, generate).
- **`cli/core/library.py`**: `LibraryManager` finds templates in `library/` with priority system.
- **`cli/core/template.py`**: Parses templates, merges YAML frontmatter with Jinja2 content.
- **`cli/core/variables.py`**: Variable data structures (`Variable`, `VariableSection`, `VariableCollection`).
- **`cli/core/prompt.py`**: Interactive CLI prompts via `rich` library.
- **`cli/core/display.py`**: Consistent output rendering.

### Template Format

Templates are directory-based. Each template is a directory containing all the necessary files and subdirectories for the boilerplate.

#### Main Template File

Requires `template.yaml` or `template.yml` with metadata and variables in YAML frontmatter:

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

- **Jinja2 Templates (`.j2`)**: Rendered by Jinja2, `.j2` extension removed in output. Support `{% include %}` and `{% import %}`.
- **Static Files**: Non-`.j2` files copied as-is.
- **Sanitization**: Auto-sanitized (single blank lines, no leading blanks, trimmed whitespace, single trailing newline).

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

**Precedence** (lowest to highest):
1. Module `spec` (defaults for all templates of that kind)
2. Template `spec` (overrides module defaults)
3. CLI `--var` (highest priority)

**Key Features:**
- **Required Sections**: Mark with `required: true` (general is implicit). Users must provide all values.
- **Toggle Settings**: Conditional sections via `toggle: "bool_var_name"`. If false, section is skipped.
- **Dependencies**: Use `needs: "section_name"` or `needs: ["sec1", "sec2"]`. Dependent sections only shown when dependencies are enabled. Auto-validated (detects circular/missing/self dependencies). Topologically sorted.

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

## Best Practices

### Template Structure
- Include `template.yaml`/`template.yml` with descriptive IDs (lowercase-with-hyphens)
- Use subdirectories for Jinja2 templates (e.g., `config/`)
- Prefer `config` module for app-specific configs vs complex directories

### Variables
- **Priority**: Prefer module spec → override when needed → add new only if unique
- Use descriptive underscore names, always specify `type`
- **Defaults**: Define sensible `default` values in `template.yaml` for all non-required variables (improves non-interactive generation)
- **Credentials**: Mark with `sensitive: true` (hides input), `autogenerated: true` (auto-generates secure values when empty)

### Jinja2
- Keep logic simple, add descriptive comments

### Docker Compose

**Naming Conventions:**
- Service: `service_name`, `container_name`, `container_timezone`, `restart_policy`
- App: Prefix with app name (e.g., `authentik_secret_key`)
- Database: `database_*` (type, enabled, external, host, port, name, user, password)
- Network: `network_*` (enabled, name, external)
- Traefik: `traefik_*` (enabled, host, tls_enabled, tls_entrypoint, tls_certresolver)
- Ports: `ports_*` (enabled, http, https, ssh)
- Email: `email_*` (enabled, host, port, username, password, from)

**Patterns:**
- Use scoped `.env.{service}.j2` files for better security/organization
- Always: `depends_on`, named volumes, health checks (DB), `restart: {{ restart_policy | default('unless-stopped') }}`
- Conditionals: `{% if not database_external %}` for service creation
- Common toggles: `database_enabled`, `email_enabled`, `traefik_enabled`, `ports_enabled`, `network_enabled`
