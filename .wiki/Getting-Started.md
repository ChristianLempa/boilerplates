# Getting Started

This guide walks through the current Boilerplates workflow: install the CLI, sync a library, inspect a template, and generate files from a `template.json` manifest.

## Prerequisites

- Python 3.9 or newer
- Git
- network access for Git-based libraries

## Install the CLI

Use the installer script:

```bash
curl -fsSL https://raw.githubusercontent.com/christianlempa/boilerplates/main/scripts/install.sh | bash
```

For platform-specific instructions, see [Installation](Installation).

## Sync the Default Library

```bash
boilerplates repo update
```

This syncs the official default library configuration, which points to `christianlempa/boilerplates-library`.

## Browse Templates

List available templates for a module:

```bash
boilerplates compose list
```

Search by ID:

```bash
boilerplates compose search nginx
```

## Inspect a Template

Before generating, inspect the template:

```bash
boilerplates compose show nginx
```

This shows:
- template metadata
- the visible version label from `metadata.version.name` when present
- file structure under `files/`
- the actual variable groups and items exposed by the template

## Generate Files

Interactive mode:

```bash
boilerplates compose generate nginx --output ./my-nginx
```

Non-interactive mode:

```bash
boilerplates compose generate nginx \
  --output ./my-nginx \
  --var service_name=my-nginx \
  --no-interactive
```

Preview only:

```bash
boilerplates compose generate nginx --dry-run --show-files
```

## Override Variables

Direct overrides:

```bash
boilerplates compose generate traefik \
  --output ./proxy \
  --var service_name=traefik \
  --var traefik_enabled=true \
  --var traefik_host=proxy.example.com
```

Variable file:

```bash
boilerplates compose generate traefik \
  --output ./proxy \
  --var-file ./vars.yaml \
  --no-interactive
```

## Save Reusable Defaults

```bash
boilerplates compose defaults set container_timezone="Europe/Berlin"
boilerplates compose defaults set restart_policy="unless-stopped"
```

List defaults:

```bash
boilerplates compose defaults list
```

## Validate Templates

Validate one template:

```bash
boilerplates compose validate nginx
```

Validate all templates in a module:

```bash
boilerplates compose validate
```

## What Changed in the Current Format

The current runtime uses:
- `template.json` instead of `template.yaml`
- `files/` instead of top-level `.j2` render files
- custom delimiters instead of default Jinja delimiters
- structured optional `metadata.version` objects

If you are reading older examples that use `template.yaml`, `.j2`, or positional output arguments for `generate`, treat them as outdated.
