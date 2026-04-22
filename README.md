![Welcome](./.assets/banner.jpg)

Create reusable templates and turn them into configurable workloads for homelabs and self-hosted infrastructure. *Free and Open-Source.*

## How it works

Create reusable templates for infrastructure expertise like Docker, Kubernetes, Terraform, Ansible, Python, and more. Use the built-in *Jinja2-like* templating syntax with `<< >>` variables, `<% %>` blocks, and `<# #>` comments to keep configuration modular and conditional. Sync with Git in both directions or manage everything locally. Render templates, configure variables through a guided wizard, and wire up secrets. Copy them to remote servers and environments or any local directory.

✨ Explore 100+ template presets for homelabs and self-hosted infrastructure: https://github.com/ChristianLempa/boilerplates-library

## Boilerplates CLI

The Boilerplates CLI is the main interface for working with template libraries locally. It lets you discover available templates, inspect their metadata and variables, validate them, and generate ready-to-use files.

It combines template-defined variables and defaults, guided interactive prompts, CLI variable overrides, and git-backed template libraries into one workflow. In practice, that means you can keep reusable boilerplates in a repository and turn them into concrete, environment-specific configurations with a single command.

⚠️ Boilerplates `0.2.0` introduced the new template format. Legacy `template.yaml` / `template.yml` manifests and `.j2` template files are no longer supported.

ℹ️ New templates must use `template.json`, keep renderable content under `files/`, and use the custom *Jinja2*-like delimiters `<< >>`, `<% %>`, and `<# #>` instead of default *Jinja2* syntax.

### Installation

#### Automated installer script

Install the Boilerplates CLI using the automated installer:

```bash
# Install latest version
curl -fsSL https://raw.githubusercontent.com/christianlempa/boilerplates/main/scripts/install.sh | bash

# Install specific version
curl -fsSL https://raw.githubusercontent.com/christianlempa/boilerplates/main/scripts/install.sh | bash -s -- --version v1.2.3
```

The installer uses `pipx` to create an isolated environment for the CLI tool. Once installed, the `boilerplates` command will be available in your terminal.

#### Nixos

If you are using nix flakes

```bash
# Run without installing
nix run github:christianlempa/boilerplates -- --help

# Install to your profile
nix profile install github:christianlempa/boilerplates

# Or directly in your flake
{
  inputs.boilerplates.url = "github:christianlempa/boilerplates";

  outputs = { self, nixpkgs, boilerplates }: {
    # Use boilerplates.packages.${system}.default
  };
}

# Use in a temporary shell
nix shell github:christianlempa/boilerplates
```

### Quick Start

```bash
# Explore
boilerplates --help

# Update Repository Library
boilerplates repo update

# List all available templates for a docker compose
boilerplates compose list

# Show details about a specific template
boilerplates compose show nginx

# Generate a template (interactive mode)
boilerplates compose generate authentik

# Generate with custom output directory
boilerplates compose generate nginx --output my-nginx-server

# Non-interactive mode with variable overrides
boilerplates compose generate traefik --output my-proxy \
  --var service_name=traefik \
  --var traefik_enabled=true \
  --var traefik_host=proxy.example.com \
  --no-interactive
```

### Managing Defaults

Save time by setting default values for variables you use frequently:

```bash
# Set a default value
boilerplates compose defaults set container_timezone="America/New_York"
boilerplates compose defaults set restart_policy="unless-stopped"

```

### Template Libraries

Boilerplates uses git-based libraries to manage templates. You can add custom repositories:

```bash
# List configured libraries
boilerplates repo list

# Update all libraries
boilerplates repo update

# Add a custom library
boilerplates repo add my-templates https://github.com/user/templates \
  --directory library \
  --branch main

# Remove a library
boilerplates repo remove my-templates
```

## Contribution

Contributions are welcome. Feel free to open an issue or submit a pull request!

## License

This repository is licensed under the [MIT License](./LICENSE).
