# Installation

Learn how to install the Boilerplates CLI tool on your system.

## Automated Installation

Install the latest version using the automated installer:

```bash
curl -fsSL https://raw.githubusercontent.com/christianlempa/boilerplates/main/scripts/install.sh | bash
```

## Install Specific Version

```bash
curl -fsSL https://raw.githubusercontent.com/christianlempa/boilerplates/main/scripts/install.sh | bash -s -- --version v1.2.3
```

## Requirements

- Python 3.8 or higher
- `pipx` (automatically installed by the installer if missing)

## Verify Installation

After installation, verify the CLI is available:

```bash
boilerplates --version
```

## Update

To update to the latest version, simply run the installer again:

```bash
curl -fsSL https://raw.githubusercontent.com/christianlempa/boilerplates/main/scripts/install.sh | bash
```

## Uninstall

Remove the Boilerplates CLI:

```bash
pipx uninstall boilerplates
```

## Next Steps

- [Configure the CLI](Configuration)
- [Explore available modules](Modules)
