# Libraries

Libraries are collections of templates that can be synced from Git repositories or loaded from local directories. This page explains how to manage template libraries.

## What is a Library?

A **library** is a collection of templates organized by module type (compose, terraform, ansible, etc.). Libraries can be:
- **Git-based** - Synced from remote repositories
- **Static** - Local directories on your filesystem

## Default Library

By default, Boilerplates uses the official template library:

```
Name: default
URL: https://github.com/christianlempa/boilerplates
Branch: main
Directory: library
```

This provides production-ready templates for various services and infrastructure.

## Library Location

Libraries are stored locally at:
```
~/.config/boilerplates/libraries/
└── default/
    └── library/
        ├── compose/
        ├── terraform/
        └── ansible/
```

## Managing Libraries

### List Libraries

View all configured libraries:

```bash
boilerplates repo list
```

Output:
```
Libraries:
  default (git)
    URL: https://github.com/christianlempa/boilerplates
    Branch: main
    Directory: library
    Status: Synced
```

### Update Libraries

Sync all Git-based libraries:

```bash
boilerplates repo update
```

This:
- Pulls latest changes from Git repositories
- Uses sparse-checkout (only downloads template directories)
- Updates metadata cache

### Add Custom Library

Add your own template library:

```bash
boilerplates repo add my-templates https://github.com/user/templates \
  --directory library \
  --branch main
```

Parameters:
- **name** - Unique library identifier
- **url** - Git repository URL
- **--directory** - Path to templates within repository (default: `.`)
- **--branch** - Git branch to use (default: `main`)

### Remove Library

Remove a library from configuration:

```bash
boilerplates repo remove my-templates
```

This removes the configuration but keeps downloaded files. To fully clean up:

```bash
rm -rf ~/.config/boilerplates/libraries/my-templates
```

## Library Types

### Git Libraries

Synced from remote Git repositories:

```yaml
libraries:
  - name: default
    type: git
    url: https://github.com/christianlempa/boilerplates
    branch: main
    directory: library
```

**Benefits:**
- Always up-to-date
- Version controlled
- Easy to share
- Automatic updates

**Use cases:**
- Official templates
- Team-shared templates
- Public template collections

### Static Libraries

Local directories on your filesystem:

```yaml
libraries:
  - name: local
    type: static
    path: ~/my-templates
```

**Benefits:**
- No network required
- Full control
- Fast access
- Development/testing

**Use cases:**
- Local development
- Private templates
- Custom modifications
- Testing new templates

## Library Priority

When multiple libraries contain the same template, **priority** determines which is used:

```yaml
libraries:
  - name: local      # Priority 1 (highest)
    type: static
    path: ~/my-templates
  - name: default    # Priority 2
    type: git
    url: https://github.com/christianlempa/boilerplates
```

### Simple IDs

Use the template name without qualification:

```bash
boilerplates compose generate nginx
```

The CLI uses the first matching template (from `local` in the example above).

### Qualified IDs

Target a specific library:

```bash
boilerplates compose generate nginx.local    # Uses local library
boilerplates compose generate nginx.default  # Uses default library
```

## Configuration File

Library configuration is stored in:
```
~/.config/boilerplates/config.yaml
```

Example:
```yaml
libraries:
  - name: default
    type: git
    url: https://github.com/christianlempa/boilerplates
    branch: main
    directory: library
  - name: local
    type: static
    path: /Users/me/my-templates
```

### Manual Editing

You can manually edit `config.yaml`:

```bash
# Edit configuration
nano ~/.config/boilerplates/config.yaml

# Verify changes
boilerplates repo list
```

## Advanced Usage

### Multiple Git Branches

Use different branches for stable vs. development templates:

```yaml
libraries:
  - name: stable
    type: git
    url: https://github.com/user/templates
    branch: main
    directory: library
  - name: dev
    type: git
    url: https://github.com/user/templates
    branch: development
    directory: library
```

### Sparse Checkout

Git libraries use sparse-checkout to minimize disk usage:

```
# Only downloads:
library/compose/
library/terraform/
library/ansible/

# Ignores:
.github/
docs/
tests/
README.md
```

This keeps library downloads fast and disk usage low.

### Private Repositories

For private Git repositories, ensure SSH or HTTPS authentication is configured:

**SSH:**
```bash
boilerplates repo add private git@github.com:user/private-templates.git \
  --directory library \
  --branch main
```

Requires SSH key configured with GitHub/GitLab.

**HTTPS with credentials:**
```bash
# Configure Git credential helper
git config --global credential.helper store

# Add library (will prompt for credentials on first sync)
boilerplates repo add private https://github.com/user/private-templates.git \
  --directory library \
  --branch main
```

## Template Discovery

After adding libraries, templates are discovered automatically:

```bash
# Sync libraries
boilerplates repo update

# List templates from all libraries
boilerplates compose list

# Show template details (uses priority order)
boilerplates compose show nginx

# Show from specific library
boilerplates compose show nginx.local
```

## Troubleshooting

### Library Not Syncing

If `repo update` fails:

```bash
# Check network connectivity
ping github.com

# Verify Git access
git ls-remote https://github.com/christianlempa/boilerplates

# Remove and re-add library
boilerplates repo remove default
boilerplates repo add default https://github.com/christianlempa/boilerplates \
  --directory library \
  --branch main
```

### Templates Not Found

If templates don't appear:

```bash
# Verify library is configured
boilerplates repo list

# Update libraries
boilerplates repo update

# Check library directory structure
ls -la ~/.config/boilerplates/libraries/default/library/compose/
```

### Duplicate Template Names

If two libraries have the same template:

```bash
# Check which library provides it
boilerplates compose show nginx

# Use qualified ID to target specific library
boilerplates compose generate nginx.local
```

## Best Practices

### Library Organization

Structure your libraries consistently:

```
my-templates/
├── library/
│   ├── compose/
│   │   ├── app1/
│   │   └── app2/
│   ├── terraform/
│   └── ansible/
└── README.md
```

### Version Control

For Git libraries:
- Use semantic versioning tags
- Maintain a CHANGELOG
- Test templates before merging
- Use branches for development

### Naming

- Use descriptive library names
- Avoid special characters
- Keep names short but meaningful

**Good:** `production`, `dev`, `team-infra`  
**Bad:** `my-lib-123`, `temp`, `new`

### Documentation

Each library should have:
- README.md with overview
- Template documentation
- Usage examples
- Contribution guidelines

## Next Steps

- [Default Variables](Core-Concepts-Defaults) - Managing variable defaults
- [Templates](Core-Concepts-Templates) - Understanding template structure
- [Developer Guide](Developers-Templates) - Creating templates for libraries

## See Also

- [Getting Started](Getting-Started) - Your first template
- [Installation](Installation) - Installing the CLI
