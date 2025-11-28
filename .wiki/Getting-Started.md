# Getting Started

Welcome to Boilerplates! This guide will help you get up and running in just a few minutes.

## Overview

Boilerplates provides two main components:

### Template Library

A collection of ready-to-use templates for common infrastructure components:
- **Docker Compose**: Containerized applications (Nginx, Traefik, Grafana, etc.)
- **Terraform**: Cloud infrastructure (AWS, Azure, GCP)
- **Ansible**: Configuration management and automation
- **Kubernetes**: Container orchestration deployments
- **Packer**: Machine image builders

Templates include:
- Pre-configured defaults for common use cases
- Documentation and usage examples
- Variable specifications for customization
- Best practices baked in

### Management CLI

A Python-based command-line tool to work with templates:
- Browse and search the template library
- Interactive configuration with validation
- Generate customized templates
- Manage multiple template libraries (official + custom)
- Sync updates from repositories

## Prerequisites

Before you begin, ensure you have:

- Python 3.10 or higher installed
- Git installed (for syncing template libraries)
- Basic command-line knowledge
- Internet connection (for downloading templates)

## Installation

The quickest way to install the management CLI is using the automated installer:

```bash
curl -fsSL https://raw.githubusercontent.com/christianlempa/boilerplates/main/scripts/install.sh | bash
```

This installs the `boilerplates` command and configures access to the official template library.

For detailed installation instructions including platform-specific guidance, see the [Installation](Installation) page.

## Your First Template

Once installed, let's generate your first template!

### 1. Sync the Template Library

Download the latest templates from the library:

```bash
boilerplates repo update
```

This syncs the official template library to `~/.config/boilerplates/libraries/default/`.

### 2. Browse the Template Library

Explore available Docker Compose templates:

```bash
boilerplates compose list
```

You'll see a table showing available templates from the library with their descriptions.

### 3. Inspect a Template

Before generating, preview a template's structure and variables:

```bash
boilerplates compose show nginx
```

This shows:
- Template metadata (name, version, author, description)
- Available configuration variables and defaults
- Template file structure
- Variable dependencies and sections

### 4. Generate Files from Template

Now, let's use the CLI to generate customized files from a template! You have two options:

**Interactive Mode** (Recommended for beginners):

```bash
boilerplates compose generate nginx
```

The tool prompts you for each variable. You can:
- Press Enter to accept defaults from the template
- Type custom values
- Navigate with arrow keys for selections
- Skip optional sections

**Non-Interactive Mode** (For automation):

```bash
boilerplates compose generate nginx my-nginx \
  --var service_name=my-nginx \
  --var container_port=8080 \
  --no-interactive
```

This uses template defaults and provided variables without prompts.

### 5. Review Generated Files

After generation, you'll find:

```
my-nginx/
├── docker-compose.yml
└── .env
```

Review the files and adjust as needed for your environment.

## Basic Commands

Here are the essential commands you'll use regularly:

### Library Management

Manage template library repositories:

```bash
# Sync official template library
boilerplates repo update

# List all configured libraries
boilerplates repo list

# Add a custom template library
boilerplates repo add my-templates https://github.com/user/templates \
  --directory library \
  --branch main
```

### Working with Templates

Discover and use templates from the library:

```bash
# Browse available templates
boilerplates compose list

# Search the library
boilerplates compose search nginx

# Inspect template structure
boilerplates compose show nginx

# Generate files from template
boilerplates compose generate nginx ./output

# Validate template syntax
boilerplates compose validate
```

### Working with Defaults

Save frequently used values to avoid repetitive typing:

```bash
# Set a default value
boilerplates compose defaults set container_timezone "America/New_York"

# View all defaults
boilerplates compose defaults list

# Remove a default
boilerplates compose defaults rm container_timezone

# Clear all defaults
boilerplates compose defaults clear
```

## Common Workflows

### Workflow 1: Quick Generation with Defaults

Use template defaults without customization:

```bash
boilerplates compose generate portainer --no-interactive
```

### Workflow 2: Interactive Customization

Customize template variables interactively:

```bash
boilerplates compose show traefik         # Review template structure
boilerplates compose generate traefik     # Customize via prompts
```

### Workflow 3: Automation

For scripts and CI/CD pipelines:

```bash
boilerplates compose generate authentik ./auth \
  --var service_name=authentik \
  --var traefik_enabled=true \
  --var traefik_host=auth.example.com \
  --no-interactive \
  --dry-run  # Preview first
```

## Advanced Features

### Dry Run

Preview generated files without writing them:

```bash
boilerplates compose generate nginx --dry-run
```

### Debug Mode

Enable detailed logging for troubleshooting:

```bash
boilerplates --log-level DEBUG compose generate nginx
```

### Variable Override

Override specific variables without interactive prompts:

```bash
boilerplates compose generate grafana \
  --var service_name=monitoring-grafana \
  --var grafana_port=3000
```

## Next Steps

Now that you know the basics, explore more:

- [Templates](Core-Concepts-Templates) - Learn how templates work
- [Variables](Core-Concepts-Variables) - Understand variable types and dependencies
- [Configuration](Core-Concepts-Libraries) - Customize your setup
- [Variable Reference](Variables-Compose) - Complete variable documentation

## Troubleshooting

### CLI Command Not Found

If the `boilerplates` command is not found after installation:

```bash
# Ensure pipx binaries are in PATH
export PATH="$HOME/.local/bin:$PATH"

# Add to your shell profile (.bashrc, .zshrc, etc.)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

### Templates Not Available

If templates aren't showing up after installation:

```bash
# Sync the template library
boilerplates repo update

# Verify library is configured
boilerplates repo list
```

### Permission Issues

If you encounter permission errors:

```bash
# Ensure output directory is writable
chmod +w ./output-directory

# Or generate to a different location
boilerplates compose generate nginx ~/my-projects/nginx
```

## Getting Help

- **Documentation:** Browse the [Wiki](Home) for comprehensive guides
- **Discord:** Join the [community](https://christianlempa.de/discord) for real-time help
- **GitHub Issues:** Report bugs or request features
- **YouTube:** Watch [video tutorials](https://www.youtube.com/@christianlempa)

Happy templating!
