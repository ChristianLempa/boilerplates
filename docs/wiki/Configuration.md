# Configuration

Learn how to configure the Boilerplates CLI for your needs.

## Configuration File

The configuration file is stored at:
```
~/.config/boilerplates/config.yaml
```

## Setting Default Values

Save time by setting default values for variables you use frequently:

```bash
# Set a default value for a specific module
boilerplates compose defaults set container_timezone "America/New_York"
boilerplates compose defaults set restart_policy "unless-stopped"

# Alternative format
boilerplates compose defaults set container_timezone=America/New_York
```

## Viewing Defaults

```bash
# View all defaults for a module
boilerplates compose defaults get

# View a specific default value
boilerplates compose defaults get container_timezone
```

## Managing Defaults

```bash
# Remove a specific default
boilerplates compose defaults rm container_timezone

# Clear all defaults for a module
boilerplates compose defaults clear

# List configuration in YAML format
boilerplates compose defaults list
```

## Template Libraries

Boilerplates uses git-based libraries to manage templates.

### List Configured Libraries

```bash
boilerplates repo list
```

### Update All Libraries

```bash
boilerplates repo update
```

### Add Custom Library

```bash
boilerplates repo add my-templates https://github.com/user/templates \
  --directory library \
  --branch main
```

### Remove Library

```bash
boilerplates repo remove my-templates
```

## Configuration Structure

Example `config.yaml`:

```yaml
defaults:
  compose:
    container_timezone: America/New_York
    restart_policy: unless-stopped
    user_uid: 1000
    user_gid: 1000

libraries:
  - name: default
    type: git
    url: https://github.com/christianlempa/boilerplates.git
    branch: main
    directory: library
```

## Next Steps

- [Explore available modules](Modules)
- [Learn about variables](Variables)
