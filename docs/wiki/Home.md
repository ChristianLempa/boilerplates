# Boilerplates CLI Documentation

Welcome to the comprehensive documentation for the Boilerplates CLI tool!

## What is Boilerplates?

Boilerplates is a powerful command-line tool that provides instant access to battle-tested infrastructure templates for Docker Compose, Terraform, Ansible, Kubernetes, and more. Stop copying configurations from random sources or starting from scratch—use production-ready templates with sensible defaults and best practices.

## Quick Navigation

### User Documentation

**Getting Started**
- [Getting Started](Getting-Started) - Quick introduction and first steps
- [Installation](Installation) - Install the CLI on Linux, MacOS, or NixOS

**Core Concepts**
- [Templates](Concepts-Templates) - Understanding templates and how they work
- [Variables](Concepts-Variables) - Variable types, sections, and dependencies

**Configuration**
- [Libraries](Configuration-Libraries) - Managing template libraries
- [Default Variables](Configuration-Default-Variables) - Setting and managing default values

**Variable Reference** (Auto-generated)
- [Ansible Variables](Variables-Ansible)
- [Compose Variables](Variables-Compose)
- [Helm Variables](Variables-Helm)
- [Kubernetes Variables](Variables-Kubernetes)
- [Packer Variables](Variables-Packer)
- [Terraform Variables](Variables-Terraform)

### Developer Documentation

**Contributing**

Before contributing, please read our [Contributing Guidelines](https://github.com/ChristianLempa/boilerplates/blob/main/CONTRIBUTING.md):
- **CLI Development**: Requires Discord discussion first—no direct PRs
- **Template Updates**: Follow Developer Documentation—issues and PRs welcome

**Architecture & Development**
- [Architecture Overview](Developers-Architecture) - System design and core components
- [Module Development](Developers-Modules) - Creating new modules
- [Template Development](Developers-Templates) - Building templates
- [Contributing Guide](Developers-Contributing) - Detailed contribution workflow

## Quick Start

```bash
# Install with automated installer
curl -fsSL https://raw.githubusercontent.com/christianlempa/boilerplates/main/scripts/install.sh | bash

# Update repository library
boilerplates repo update

# List available templates
boilerplates compose list

# Generate a template
boilerplates compose generate authentik
```

## Getting Help

- **Discord:** Join the [community Discord](https://christianlempa.de/discord) for support and discussions
- **GitHub Issues:** Report bugs or request features on [GitHub](https://github.com/ChristianLempa/boilerplates/issues)
- **YouTube:** Watch [Christian's tutorials](https://www.youtube.com/@christianlempa) for visual guides
- **Contributing:** Read the [CONTRIBUTING.md](https://github.com/ChristianLempa/boilerplates/blob/main/CONTRIBUTING.md) guide

## Project Links

- **GitHub Repository:** https://github.com/ChristianLempa/boilerplates
- **PyPI Package:** https://pypi.org/project/boilerplates-cli/
- **Christian's Website:** https://christianlempa.de/
