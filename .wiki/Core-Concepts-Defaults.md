# Default Variables

Save time by setting default values for variables you use frequently. This page explains how to manage your default variable configuration.

## What are Default Variables?

**Default variables** are user-defined values that override module and template defaults. They allow you to:
- Avoid repetitive typing during template generation
- Standardize values across multiple templates
- Customize your environment once, use everywhere

## Precedence Order

Variables are resolved in this order (lowest to highest priority):

1. Module spec (module-wide defaults)
2. Template spec (template-specific defaults)
3. **User config** (your saved defaults) ← This page
4. CLI arguments (`--var` flags)

Your defaults override module and template values but can be overridden by CLI arguments.

## Managing Defaults

All default management commands follow this pattern:
```bash
boilerplates <module> defaults <command> [args]
```

### View Defaults

List all saved defaults for a module:

```bash
boilerplates compose defaults list
```

Output:
```
Default Variables (Compose):
  container_timezone: America/New_York
  restart_policy: unless-stopped
  traefik_network: traefik
  network_external: true
```

### Set a Default

Save a default value:

```bash
boilerplates compose defaults set container_timezone "America/New_York"
```

Response:
```
Set default: container_timezone = America/New_York
```

**Tips:**
- Use quotes for values with spaces
- Booleans: `true` or `false`
- Numbers: no quotes needed

**Examples:**
```bash
# String
boilerplates compose defaults set restart_policy "unless-stopped"

# Integer
boilerplates compose defaults set user_uid 1000

# Boolean
boilerplates compose defaults set traefik_enabled true

# String with spaces
boilerplates compose defaults set container_hostname "my app server"
```

### Get a Default

View a single default value:

```bash
boilerplates compose defaults get container_timezone
```

Output:
```
container_timezone: America/New_York
```

### Remove a Default

Delete a saved default:

```bash
boilerplates compose defaults rm container_timezone
```

Response:
```
Removed default: container_timezone
```

The variable will now use module/template defaults again.

### Clear All Defaults

Remove all saved defaults for a module:

```bash
boilerplates compose defaults clear
```

Response:
```
Cleared all defaults for compose
```

**Warning:** This cannot be undone. Consider backing up your config first.

## Configuration Storage

Defaults are stored in:
```
~/.config/boilerplates/config.yaml
```

Example content:
```yaml
libraries:
  - name: default
    type: git
    url: https://github.com/christianlempa/boilerplates
    branch: main
    directory: library

defaults:
  compose:
    container_timezone: America/New_York
    restart_policy: unless-stopped
    traefik_network: traefik
    network_external: true
  terraform:
    region: us-east-1
    instance_type: t3.micro
```

### Manual Editing

You can manually edit the config file:

```bash
# Edit configuration
nano ~/.config/boilerplates/config.yaml

# Verify defaults
boilerplates compose defaults list
```

## Common Use Cases

### Timezone Configuration

Set your local timezone once:

```bash
boilerplates compose defaults set container_timezone "Europe/Berlin"
```

Now all Docker containers use your timezone by default.

### Network Configuration

Standardize network settings:

```bash
boilerplates compose defaults set network_external true
boilerplates compose defaults set network_name "docker-network"
```

### Traefik Configuration

Set common Traefik values:

```bash
boilerplates compose defaults set traefik_network "traefik"
boilerplates compose defaults set traefik_domain "example.com"
boilerplates compose defaults set traefik_tls_certresolver "cloudflare"
```

### User IDs

Match your host user:

```bash
boilerplates compose defaults set user_uid $(id -u)
boilerplates compose defaults set user_gid $(id -g)
```

### Restart Policy

Standardize container behavior:

```bash
boilerplates compose defaults set restart_policy "unless-stopped"
```

## Overriding Defaults

Even with defaults set, you can override them:

### Interactive Mode

During interactive generation, defaults appear as pre-filled values. Press Enter to accept or type a new value:

```
Container timezone [America/New_York]: Europe/London
```

### CLI Arguments

Override with `--var`:

```bash
boilerplates compose generate nginx \
  --var container_timezone="UTC" \
  --no-interactive
```

The CLI argument takes precedence over your saved default.

## Per-Module Defaults

Each module has its own defaults:

```bash
# Compose defaults
boilerplates compose defaults set restart_policy "unless-stopped"

# Terraform defaults (separate)
boilerplates terraform defaults set region "us-east-1"

# Ansible defaults (separate)
boilerplates ansible defaults set become true
```

Defaults don't transfer between modules—they're module-specific.

## Backup and Restore

### Backup Configuration

Save your configuration:

```bash
cp ~/.config/boilerplates/config.yaml ~/boilerplates-config-backup.yaml
```

### Restore Configuration

Restore from backup:

```bash
cp ~/boilerplates-config-backup.yaml ~/.config/boilerplates/config.yaml
```

### Share Configuration

Share defaults with your team:

```bash
# Export defaults
cat ~/.config/boilerplates/config.yaml | grep -A 100 "defaults:" > team-defaults.yaml

# Share file with team
# Team members can merge into their config.yaml
```

## Advanced Usage

### Environment-Specific Defaults

Maintain multiple configurations:

```bash
# Production defaults
cp ~/.config/boilerplates/config.yaml ~/.config/boilerplates/config-prod.yaml

# Development defaults
cp ~/.config/boilerplates/config.yaml ~/.config/boilerplates/config-dev.yaml

# Switch between them
cp ~/.config/boilerplates/config-prod.yaml ~/.config/boilerplates/config.yaml
```

### Scripted Configuration

Set defaults programmatically:

```bash
#!/bin/bash

# Set common defaults
boilerplates compose defaults set container_timezone "$(cat /etc/timezone)"
boilerplates compose defaults set user_uid "$(id -u)"
boilerplates compose defaults set user_gid "$(id -g)"
boilerplates compose defaults set restart_policy "unless-stopped"
```

## Troubleshooting

### Defaults Not Applied

If defaults aren't being used:

```bash
# Verify defaults are set
boilerplates compose defaults list

# Check config file
cat ~/.config/boilerplates/config.yaml

# Ensure module name matches
# "compose" not "docker-compose"
```

### Config File Errors

If config file is corrupted:

```bash
# Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('~/.config/boilerplates/config.yaml'))"

# Or remove and recreate
mv ~/.config/boilerplates/config.yaml ~/.config/boilerplates/config.yaml.bak
boilerplates repo update  # Recreates config
```

### Wrong Values

If wrong values appear:

```bash
# Check precedence
# 1. Module spec
# 2. Template spec
# 3. User defaults ← Check here
# 4. CLI --var

# Verify your defaults
boilerplates compose defaults list

# Check template spec
boilerplates compose show <template-name>
```

## Best Practices

### Essential Defaults

Set these common defaults:

```bash
# System
boilerplates compose defaults set container_timezone "$(cat /etc/timezone)"
boilerplates compose defaults set user_uid $(id -u)
boilerplates compose defaults set user_gid $(id -g)

# Containers
boilerplates compose defaults set restart_policy "unless-stopped"

# Networking (if using external networks)
boilerplates compose defaults set network_external true
boilerplates compose defaults set network_name "docker-network"
```

### Don't Over-Configure

Only set defaults for values you use consistently:

**Good:**
- Timezone (same everywhere)
- User UID/GID (same everywhere)
- Network settings (if standardized)

**Bad:**
- Service names (unique per service)
- Hostnames (unique per service)
- Port numbers (conflict-prone)

### Document Your Defaults

Keep a list of your defaults for reference:

```bash
# Save to file
boilerplates compose defaults list > ~/my-defaults.txt
```

### Review Periodically

Check your defaults occasionally:

```bash
boilerplates compose defaults list
```

Remove obsolete or unused values.

## Next Steps

- [Libraries](Core-Concepts-Libraries) - Managing template libraries
- [Variables](Core-Concepts-Variables) - Understanding variable types and behavior
- [Getting Started](Getting-Started) - Using defaults in template generation

## See Also

- [Installation](Installation) - CLI setup
- [Concepts](Core-Concepts-Templates) - How templates work
