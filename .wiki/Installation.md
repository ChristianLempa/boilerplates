# Installation

This guide covers installing the Boilerplates CLI on various platforms.

## Prerequisites

Before installing, ensure you have:

- **Python 3.10 or higher** - Check with `python3 --version`
- **Git** - Required for syncing template libraries
- **Internet connection** - For downloading dependencies and templates

### Checking Python Version

```bash
python3 --version
```

If you see version 3.10 or higher, you're ready to proceed. If not, see the platform-specific instructions below for installing Python.

## Quick Install (Recommended)

The automated installer script handles all dependencies and setup:

```bash
curl -fsSL https://raw.githubusercontent.com/christianlempa/boilerplates/main/scripts/install.sh | bash
```

### Install Specific Version

```bash
curl -fsSL https://raw.githubusercontent.com/christianlempa/boilerplates/main/scripts/install.sh | bash -s -- --version v0.1.0
```

The installer will:
1. Check for required dependencies (Python, pipx)
2. Install pipx if not present
3. Install the Boilerplates CLI in an isolated environment
4. Add the `boilerplates` command to your PATH

## Platform-Specific Installation

### Linux

#### Ubuntu / Debian

1. **Install Python and dependencies:**

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git
```

2. **Install pipx:**

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

3. **Install Boilerplates:**

```bash
pipx install boilerplates-cli
```

4. **Verify installation:**

```bash
boilerplates --version
```

#### Fedora / RHEL / CentOS

1. **Install Python and dependencies:**

```bash
sudo dnf install -y python3 python3-pip git
```

2. **Install pipx:**

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

3. **Install Boilerplates:**

```bash
pipx install boilerplates-cli
```

#### Arch Linux

1. **Install Python and dependencies:**

```bash
sudo pacman -S python python-pip git
```

2. **Install pipx:**

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

3. **Install Boilerplates:**

```bash
pipx install boilerplates-cli
```

### MacOS

#### Using Homebrew (Recommended)

1. **Install Homebrew** (if not already installed):

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

2. **Install Python and pipx:**

```bash
brew install python pipx
pipx ensurepath
```

3. **Install Boilerplates:**

```bash
pipx install boilerplates-cli
```

#### Using Python from python.org

1. Download and install Python 3.10+ from [python.org](https://www.python.org/downloads/macos/)

2. **Install pipx:**

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

3. **Install Boilerplates:**

```bash
pipx install boilerplates-cli
```

### NixOS

Boilerplates is available as a Nix Flake for NixOS and Nix users.

#### Run Without Installing

```bash
nix run github:christianlempa/boilerplates -- --help
```

#### Install to Profile

```bash
nix profile install github:christianlempa/boilerplates
```

#### Use in Flake

Add to your `flake.nix`:

```nix
{
  inputs.boilerplates.url = "github:christianlempa/boilerplates";

  outputs = { self, nixpkgs, boilerplates }: {
    # Use boilerplates.packages.${system}.default
    packages.x86_64-linux.default = boilerplates.packages.x86_64-linux.default;
  };
}
```

#### Temporary Shell

```bash
nix shell github:christianlempa/boilerplates
```

### Windows (WSL Recommended)

While Boilerplates can run on Windows, we recommend using Windows Subsystem for Linux (WSL) for the best experience.

#### Install WSL (Windows 10/11)

1. **Install WSL:**

```powershell
wsl --install
```

2. **Restart** your computer

3. **Follow Linux installation** instructions above (Ubuntu is the default distribution)

#### Native Windows (Not Recommended)

1. Install Python 3.10+ from [python.org](https://www.python.org/downloads/windows/)

2. Install pipx:

```powershell
python -m pip install --user pipx
python -m pipx ensurepath
```

3. Install Boilerplates:

```powershell
pipx install boilerplates-cli
```

## Manual Installation

For development or custom installations:

### Using pip (Not Recommended for End Users)

```bash
pip install --user boilerplates-cli
```

Note: This installs globally and may conflict with system packages. Use pipx instead.

### From Source

1. **Clone the repository:**

```bash
git clone https://github.com/ChristianLempa/boilerplates.git
cd boilerplates
```

2. **Create virtual environment:**

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install in development mode:**

```bash
pip install -e .
```

4. **Run the CLI:**

```bash
python3 -m cli --help
```

## Post-Installation Setup

### Verify Installation

```bash
boilerplates --version
```

Expected output:
```
Boilerplates CLI v0.1.0
```

### Initialize Template Library

Sync the default template library:

```bash
boilerplates repo update
```

This downloads all available templates to:
```
~/.config/boilerplates/libraries/
```

### Shell Completion (Optional)

Enable tab completion for your shell:

#### Bash

```bash
echo 'eval "$(_BOILERPLATES_COMPLETE=bash_source boilerplates)"' >> ~/.bashrc
source ~/.bashrc
```

#### Zsh

```bash
echo 'eval "$(_BOILERPLATES_COMPLETE=zsh_source boilerplates)"' >> ~/.zshrc
source ~/.zshrc
```

#### Fish

```bash
echo '_BOILERPLATES_COMPLETE=fish_source boilerplates | source' >> ~/.config/fish/completions/boilerplates.fish
```

## Updating

### Update to Latest Version

```bash
pipx upgrade boilerplates-cli
```

### Update Template Library

```bash
boilerplates repo update
```

## Uninstalling

### Remove the CLI

```bash
pipx uninstall boilerplates-cli
```

### Remove Configuration and Templates

```bash
rm -rf ~/.config/boilerplates
```

## Troubleshooting

### Command Not Found After Installation

If `boilerplates` is not found, ensure pipx binaries are in your PATH:

```bash
# Add to your shell profile (.bashrc, .zshrc, etc.)
export PATH="$HOME/.local/bin:$PATH"
```

Then reload your shell:
```bash
source ~/.bashrc  # or ~/.zshrc
```

### Python Version Too Old

If you have Python < 3.10, install a newer version:

**Ubuntu/Debian:**
```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.11
```

**Fedora:**
```bash
sudo dnf install python3.11
```

**MacOS (Homebrew):**
```bash
brew install python@3.11
```

### Permission Denied Errors

If you encounter permission errors during installation:

```bash
# Use --user flag
python3 -m pip install --user pipx

# Or use virtual environments
python3 -m venv ~/venvs/boilerplates
source ~/venvs/boilerplates/bin/activate
pip install boilerplates-cli
```

### SSL Certificate Errors

If you encounter SSL errors:

```bash
# Ubuntu/Debian
sudo apt install ca-certificates

# Update certificates
sudo update-ca-certificates
```

## Next Steps

Now that you've installed Boilerplates:

- [Getting Started](Getting-Started) - Generate your first template
- [Configuration](Core-Concepts-Libraries) - Customize your setup
- [Templates](Core-Concepts-Templates) - Learn about template structure

## Getting Help

- **Discord:** [Join the community](https://christianlempa.de/discord)
- **GitHub Issues:** [Report installation problems](https://github.com/ChristianLempa/boilerplates/issues)
- **Documentation:** [Browse the Wiki](Home)
