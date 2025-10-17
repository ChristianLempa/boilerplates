# Variables

Variables are the configurable parameters used when generating templates. Understanding how variables work will help you customize templates for your needs.

## Variable System Overview

The Boilerplates CLI uses a hierarchical variable system organized into **sections**. Each section groups related configuration options.

### Variable Precedence

Variables can be set from multiple sources. When conflicts occur, the following precedence applies (highest to lowest):

1. **CLI overrides** (`--var` flags)
2. **Config defaults** (`~/.config/boilerplates/config.yaml`)
3. **Template spec** (defined in `template.yaml`)
4. **Module spec** (module-wide defaults)

### Example

```bash
# Module default: container_timezone = "UTC"
# You set config default: container_timezone = "Europe/Berlin"
# You override via CLI: --var container_timezone="America/New_York"
# Result: "America/New_York" is used
```

## Variable Types

Variables support different data types with automatic validation:

- `str` - String values
- `int` - Integer numbers
- `float` - Decimal numbers
- `bool` - Boolean (true/false)
- `enum` - Choice from predefined options
- `email` - Email address (validated)
- `url` - URL (validated)
- `hostname` - Hostname/domain (validated)

## Variable Properties

### Required Variables

Some variables must be provided. Required variables are marked in the reference documentation.

### Default Values

Most variables have sensible defaults. You only need to provide values for variables you want to customize.

### Sensitive Variables

Variables marked as sensitive (🔒) are:
- Masked during interactive prompts
- Hidden in logs and output
- Examples: passwords, API keys, tokens

### Auto-generated Variables

Some variables (like passwords) can be automatically generated if not provided. These are marked with *auto-generated* in the reference.

## Sections

Variables are organized into sections:

### Required Sections

The `general` section is always required and contains core configuration options.

### Toggle Sections

Most sections have a **toggle variable** (boolean) that enables/disables the entire section.

Example:
```bash
# Enable Traefik integration
--var traefik_enabled=true
```

### Dependent Sections

Some sections depend on others. For example, `traefik_tls` depends on `traefik` being enabled.

Dependencies are clearly marked in the variable reference documentation.

## Interactive Mode

By default, the CLI prompts you for variable values interactively:

```bash
boilerplates compose generate nginx
# CLI will prompt for each required variable
```

### Non-Interactive Mode

Skip prompts and use defaults/config values:

```bash
boilerplates compose generate nginx --no-interactive
```

## Variable Overrides

Override specific variables without prompts:

```bash
# Single variable
boilerplates compose generate nginx --var service_name=my-nginx

# Multiple variables
boilerplates compose generate nginx \
  --var service_name=my-nginx \
  --var container_timezone=America/New_York \
  --var ports_enabled=true
```

## Schemas

Modules support multiple schema versions to maintain backward compatibility. Each schema version may introduce new variables or sections.

**Current schemas:**
- [Compose v1.0](Modules-Compose-Variables-v1.0) - Original specification
- [Compose v1.1](Modules-Compose-Variables-v1.1) - Enhanced with network modes and swarm improvements

Templates specify which schema version they require. The CLI validates compatibility automatically.

## Module Variable References

Detailed variable documentation for each module:

### Docker Compose
- [Schema v1.0 Variables](Modules-Compose-Variables-v1.0)
- [Schema v1.1 Variables](Modules-Compose-Variables-v1.1) (Current)

### Coming Soon
Documentation for additional modules will be added as they become available.

## Tips

1. **Use config defaults** for values you use frequently across projects
2. **Enable sections selectively** - only enable what you need
3. **Check dependencies** - some sections require others to be enabled first
4. **Validate first** - use `--dry-run` to preview before generating

## Next Steps

- [View Compose Module Variables](Modules-Compose-Variables-v1.1)
- [Learn about Configuration](Configuration)
- [Explore Modules](Modules)
