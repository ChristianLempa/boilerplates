# Modules

Modules represent different types of infrastructure templates (Docker Compose, Terraform, Ansible, etc.).

## Available Modules

### Docker Compose

Manage Docker Compose configurations with production-ready templates.

**Commands:**
```bash
# List all compose templates
boilerplates compose list

# Show template details
boilerplates compose show nginx

# Generate a template
boilerplates compose generate nginx

# Generate with custom directory
boilerplates compose generate nginx my-nginx-server
```

**Variable References:**
- [Schema v1.0 Variables](Modules-Compose-Variables-v1.0)
- [Schema v1.1 Variables](Modules-Compose-Variables-v1.1) (Current)

### Coming Soon

More modules are in development:
- Terraform / OpenTofu
- Ansible
- Kubernetes
- Packer

## Module Commands

All modules support these standard commands:

### List Templates
```bash
boilerplates <module> list
```

### Search Templates
```bash
boilerplates <module> search <query>
```

### Show Template Details
```bash
boilerplates <module> show <template-id>
```

### Generate from Template
```bash
boilerplates <module> generate <template-id> [directory]
```

**Options:**
- `--interactive` / `--no-interactive` - Enable/disable interactive prompts
- `--var KEY=VALUE` - Override variable values
- `--dry-run` - Preview without writing files
- `--show-files` - Display generated file contents (with --dry-run)
- `--quiet` - Suppress non-error output

### Validate Templates
```bash
boilerplates <module> validate [template-id]
```

### Manage Defaults
```bash
boilerplates <module> defaults get [var-name]
boilerplates <module> defaults set <var-name> <value>
boilerplates <module> defaults rm <var-name>
boilerplates <module> defaults clear
boilerplates <module> defaults list
```

## Schema Versions

Modules may support multiple schema versions to maintain backward compatibility while adding new features. Templates specify which schema version they require.

Learn more about [Variables and Schemas](Variables).

## Next Steps

- [Docker Compose Module Variables](Modules-Compose-Variables-v1.1)
- [Learn about Variables](Variables)
