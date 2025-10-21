# Christian's `Boilerplates`

[![Welcome](https://cnd-prod-1.s3.us-west-004.backblazeb2.com/new-banner4-scaled-for-github.jpg)](https://youtu.be/apgp9egIKK8)

**Hey, there!**

**I'm Christian, and I'm passionate about creating educational tech content for IT Pros and Homelab nerds.**

## What are Boilerplates?

**Boilerplates** is a curated collection of production-ready templates for your homelab and infrastructure projects. Stop copying configurations from random GitHub repos or starting from scratch every time you spin up a new service!

## Boilerplates CLI

The Boilerplates CLI tool gives you instant access to battle-tested templates for Docker, Terraform, Ansible, Kubernetes, and more.

Each template includes sensible defaults, best practices, and common configuration patterns—so you can focus on customizing for your environment.

**Key Features:**
- 🚀 **Quick Setup** - Generate complete project structures in seconds
- 🔧 **Fully Customizable** - Interactive prompts or non-interactive mode with variable overrides
- 💾 **Smart Defaults** - Save your preferred values and reuse across projects

> **Note:** Technologies evolve rapidly. While I actively maintain these templates, always review generated configurations before deploying to production.

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
boilerplates compose generate nginx my-nginx-server

# Non-interactive mode with variable overrides
boilerplates compose generate traefik my-proxy \
  --var service_name=traefik \
  --var traefik_enabled=true \
  --var traefik_host=proxy.example.com \
  --no-interactive
```

### Managing Defaults

Save time by setting default values for variables you use frequently:

```bash
# Set a default value
boilerplates compose defaults set container_timezone "America/New_York"
boilerplates compose defaults set restart_policy "unless-stopped"

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

## Documentation

For comprehensive documentation, advanced usage, and template development guides, check out the **[Wiki](../../wiki)** _(coming soon)_.

If you're looking for detailed tutorials on specific tools and technologies, visit my [YouTube Channel](https://www.youtube.com/@christianlempa).

## Contribution

If you’d like to contribute to this project, reach out to me on social media or [Discord](https://christianlempa.de/discord), or create a pull request for the necessary changes.

## Other Resources

- [Dotfiles](https://github.com/christianlempa/dotfiles) - My personal configuration files on macOS
- [Cheat-Sheets](https://github.com/christianlempa/cheat-sheets) - Command Reference for various tools and technologies

## Support me

Creating high-quality videos and valuable resources that are accessible to everyone, free of charge, is a huge challenge. With your contribution, I can dedicate more time and effort into the creation process, which ultimately enhances the quality of the content. So, all your support, by becoming a member, truly makes a significant impact on what I do. And you’ll also get some cool benefits and perks in return, as a recognition of your support.

Remember, ***supporting me is entirely optional.*** Your choice to become a member or not won't change your access to my videos and resources. You are also welcome to reach out to me on Discord, if you have any questions or feedback.

[https://www.patreon.com/christianlempa](https://www.patreon.com/christianlempa)
