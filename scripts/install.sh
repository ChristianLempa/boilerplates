#!/usr/bin/env bash
set -euo pipefail

REPO_OWNER="christianlempa"
REPO_NAME="boilerplates"
INSTALL_VERSION="${VERSION:-${INSTALL_VERSION:-latest}}"
AUTO_INSTALL="${AUTO_INSTALL:-true}"
OS_RELEASE_FILE="${OS_RELEASE_FILE:-/etc/os-release}"
MACOS_DEPENDENCY_INSTALLER="${MACOS_DEPENDENCY_INSTALLER:-pipx}"
LINUX_DEPENDENCY_INSTALLER="${LINUX_DEPENDENCY_INSTALLER:-pipx}"
INSTALL_METHOD=""
UV_CMD=""
PIPX_CMD=""
UV_INSTALL_URL="https://astral.sh/uv/install.sh"

usage() {
  cat <<USAGE
Usage: install.sh [OPTIONS]

Install the boilerplates CLI from GitHub releases via uv or pipx.

Options:
  --version VER          Version to install (default: "latest")
  --macos-installer VAL  Auto-install dependency for macOS: uv or pipx (default: "pipx")
  --linux-installer VAL  Auto-install dependency for Linux: uv or pipx (default: "pipx")
  --no-auto-install      Skip automatic dependency installation
  -h, --help             Show this message

Examples:
  curl -fsSL https://raw.githubusercontent.com/$REPO_OWNER/$REPO_NAME/main/scripts/install.sh | bash
  curl -fsSL https://raw.githubusercontent.com/$REPO_OWNER/$REPO_NAME/main/scripts/install.sh | bash -s -- --version v1.0.0

Uninstall:
  uv tool uninstall boilerplates
  pipx uninstall boilerplates
USAGE
}

log() { printf '[boilerplates] %s\n' "$*" >&2; }
error() { printf '[boilerplates][error] %s\n' "$*" >&2; exit 1; }

is_command_usable() {
  local cmd="$1"
  [[ -n "$cmd" ]] || return 1
  "$cmd" --version >/dev/null 2>&1
}

resolve_uv_cmd() {
  if command -v uv >/dev/null 2>&1; then
    local uv_cmd
    uv_cmd="$(command -v uv)"
    if is_command_usable "$uv_cmd"; then
      printf '%s\n' "$uv_cmd"
      return 0
    fi
  fi

  if command -v uvx >/dev/null 2>&1 && is_command_usable "$(command -v uvx)"; then
    local uv_from_uvx
    uv_from_uvx="$(dirname "$(command -v uvx)")/uv"
    if [[ -x "$uv_from_uvx" ]] && is_command_usable "$uv_from_uvx"; then
      printf '%s\n' "$uv_from_uvx"
      return 0
    fi
  fi

  return 1
}

validate_dependency_installer() {
  local option_name="$1"
  local value="$2"

  case "$value" in
    uv|pipx) ;;
    *) error "$option_name must be one of: uv, pipx" ;;
  esac
}

has_uv() {
  resolve_uv_cmd >/dev/null 2>&1
}

has_pipx() {
  local pipx_user_cmd=""

  if command -v pipx >/dev/null 2>&1 && is_command_usable "$(command -v pipx)"; then
    return 0
  fi

  if command -v python3 >/dev/null 2>&1; then
    pipx_user_cmd="$(python3 -m site --user-base 2>/dev/null)/bin/pipx"
    is_command_usable "$pipx_user_cmd"
    return $?
  fi

  return 1
}

ensure_homebrew() {
  if ! command -v brew >/dev/null 2>&1; then
    log "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || error "Failed to install Homebrew"
  fi
}

install_uv() {
  if resolve_uv_cmd >/dev/null 2>&1; then
    return 0
  fi

  log "Installing uv..."

  if command -v curl >/dev/null 2>&1; then
    curl -LsSf "$UV_INSTALL_URL" | sh >/dev/null 2>&1 || return 1
  elif command -v wget >/dev/null 2>&1; then
    wget -qO- "$UV_INSTALL_URL" | sh >/dev/null 2>&1 || return 1
  else
    return 1
  fi

  export PATH="$HOME/.local/bin:$PATH"

  resolve_uv_cmd >/dev/null 2>&1
}

detect_os() {
  if [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="macos"
  elif [[ -f "$OS_RELEASE_FILE" ]]; then
    OS_TYPE="linux"
    . "$OS_RELEASE_FILE"
    DISTRO_ID="$ID"
    DISTRO_VERSION="${VERSION_ID:-}"
  else
    OS_TYPE="unknown"
  fi
}

install_dependencies_macos() {
  log "Detected macOS"

  validate_dependency_installer "macOS installer" "$MACOS_DEPENDENCY_INSTALLER"
  
  if ! command -v git >/dev/null 2>&1; then
    ensure_homebrew
    log "Installing git..."
    brew install git || error "Failed to install git"
  fi

  if has_uv || has_pipx; then
    return 0
  fi

  if [[ "$MACOS_DEPENDENCY_INSTALLER" == "uv" ]]; then
    install_uv || error "Failed to install uv"
    return 0
  fi

  ensure_homebrew

  if ! command -v python3 >/dev/null 2>&1; then
    log "Installing Python3..."
    brew install python3 || error "Failed to install Python3"
  fi

  if ! has_pipx; then
    log "Installing pipx..."
    brew install pipx || error "Failed to install pipx"
    pipx ensurepath
  fi
}

install_dependencies_linux() {
  log "Detected Linux ($DISTRO_ID)"
  validate_dependency_installer "Linux installer" "$LINUX_DEPENDENCY_INSTALLER"
  
  case "$DISTRO_ID" in
    ubuntu|debian|pop|linuxmint|elementary)
      PKG_MANAGER="apt"
      PYTHON_PKG="python3 python3-pip python3-venv"
      PIPX_PKG="pipx"
      GIT_PKG="git"
      UPDATE_CMD="sudo apt update"
      INSTALL_CMD="sudo apt install -y"
      ;;
    fedora|rhel|centos|rocky|almalinux)
      PKG_MANAGER="dnf"
      PYTHON_PKG="python3 python3-pip"
      PIPX_PKG="pipx"
      GIT_PKG="git"
      UPDATE_CMD="sudo dnf check-update || true"
      INSTALL_CMD="sudo dnf install -y"
      ;;
    opensuse*|sles)
      PKG_MANAGER="zypper"
      PYTHON_PKG="python3 python3-pip"
      PIPX_PKG="python3-pipx"
      GIT_PKG="git"
      UPDATE_CMD="sudo zypper refresh"
      INSTALL_CMD="sudo zypper install -y"
      ;;
    arch|archarm|manjaro|endeavouros)
      PKG_MANAGER="pacman"
      PYTHON_PKG="python python-pip"
      PIPX_PKG="python-pipx"
      GIT_PKG="git"
      UPDATE_CMD="sudo pacman -Sy"
      INSTALL_CMD="sudo pacman -S --noconfirm"
      ;;
    alpine)
      PKG_MANAGER="apk"
      PYTHON_PKG="python3 py3-pip"
      PIPX_PKG="pipx"
      GIT_PKG="git"
      UPDATE_CMD="sudo apk update"
      INSTALL_CMD="sudo apk add"
      ;;
    *)
      log "Unsupported Linux distribution: $DISTRO_ID"
      log "Please install manually: git and uv or pipx"
      return 1
      ;;
  esac
  
  if ! command -v git >/dev/null 2>&1; then
    log "Installing git..."
    $UPDATE_CMD
    $INSTALL_CMD $GIT_PKG || error "Failed to install git"
  fi

  if has_uv || has_pipx; then
    return 0
  fi

  if [[ "$LINUX_DEPENDENCY_INSTALLER" == "uv" ]]; then
    install_uv || error "Failed to install uv"
    return 0
  fi

  if ! command -v python3 >/dev/null 2>&1; then
    log "Installing Python3..."
    $UPDATE_CMD
    $INSTALL_CMD $PYTHON_PKG || error "Failed to install Python3"
  fi

  if ! python3 -m pip --version >/dev/null 2>&1; then
    log "pip not available, installing..."
    $INSTALL_CMD $PYTHON_PKG || error "Failed to install pip"
  fi

  if ! has_pipx; then
    log "Installing pipx..."
    
    # Try system package first if available
    if [[ -n "${PIPX_PKG:-}" ]]; then
      if $INSTALL_CMD $PIPX_PKG >/dev/null 2>&1; then
        log "pipx installed from system package"
      else
        # System package failed, try pip with --break-system-packages
        if python3 -m pip install --user --break-system-packages pipx 2>&1 | grep -q "Successfully installed"; then
          log "pipx installed via pip"
        elif python3 -m pip install --user pipx 2>&1 | grep -q "Successfully installed"; then
          log "pipx installed via pip"
        else
          error "Failed to install pipx. Try installing manually: sudo apt install pipx"
        fi
      fi
    else
      # No system package, use pip
      if python3 -m pip install --user --break-system-packages pipx 2>&1 | grep -q "Successfully installed"; then
        log "pipx installed via pip"
      elif python3 -m pip install --user pipx 2>&1 | grep -q "Successfully installed"; then
        log "pipx installed via pip"
      else
        error "Failed to install pipx"
      fi
    fi
    
    # Ensure pipx is in PATH
    if command -v pipx >/dev/null 2>&1; then
      pipx ensurepath >/dev/null 2>&1
    elif [[ -x "$(python3 -m site --user-base 2>/dev/null)/bin/pipx" ]]; then
      "$(python3 -m site --user-base)/bin/pipx" ensurepath >/dev/null 2>&1
    fi
  fi
}

check_dependencies() {
  local missing_deps=()
  
  command -v tar >/dev/null 2>&1 || missing_deps+=("tar")
  command -v mktemp >/dev/null 2>&1 || missing_deps+=("mktemp")
  
  if [[ ${#missing_deps[@]} -gt 0 ]]; then
    error "Required system tools missing: ${missing_deps[*]}"
  fi

  validate_dependency_installer "macOS installer" "$MACOS_DEPENDENCY_INSTALLER"
  validate_dependency_installer "Linux installer" "$LINUX_DEPENDENCY_INSTALLER"

  detect_os
  
  local needs_install=false
  
  if ! command -v git >/dev/null 2>&1; then
    log "git not found"
    needs_install=true
  fi
  
  if ! has_uv && ! has_pipx; then
    log "No supported installer found (uv/uvx or pipx)"
    needs_install=true
  fi
  
  if [[ "$needs_install" == "true" ]]; then
    if [[ "$AUTO_INSTALL" == "true" ]]; then
      log "Installing missing dependencies..."
      
      if [[ "$OS_TYPE" == "macos" ]]; then
        install_dependencies_macos
      elif [[ "$OS_TYPE" == "linux" ]]; then
        install_dependencies_linux
      else
        error "Unsupported OS. Please install manually: git and uv or pipx"
      fi
    else
      error "Missing dependencies. Install: git and uv or pipx (or run without --no-auto-install)"
    fi
  fi
  
  local resolved_uv_cmd=""
  if resolved_uv_cmd="$(resolve_uv_cmd)"; then
    UV_CMD="$resolved_uv_cmd"
    if command -v uv >/dev/null 2>&1 && [[ "$UV_CMD" == "$(command -v uv)" ]]; then
      INSTALL_METHOD="uv"
    else
      INSTALL_METHOD="uvx"
    fi
  fi

  if [[ -z "$INSTALL_METHOD" ]]; then
    if command -v pipx >/dev/null 2>&1 && is_command_usable "$(command -v pipx)"; then
      PIPX_CMD="pipx"
      INSTALL_METHOD="pipx"
    elif [[ -x "$(python3 -m site --user-base 2>/dev/null)/bin/pipx" ]]; then
      local pipx_user_cmd
      pipx_user_cmd="$(python3 -m site --user-base)/bin/pipx"
      if is_command_usable "$pipx_user_cmd"; then
        PIPX_CMD="$pipx_user_cmd"
        INSTALL_METHOD="pipx"
      fi
    fi

    [[ -z "$INSTALL_METHOD" ]] && error "No supported installer found. Install uv (preferred) or pipx and ensure the command is runnable."
  fi
  
  log "All dependencies available"
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --version)
        [[ $# -lt 2 ]] && error "--version requires an argument"
        [[ "$2" =~ ^- ]] && error "--version requires a version string, not an option"
        INSTALL_VERSION="$2"
        shift 2
        ;;
      --macos-installer)
        [[ $# -lt 2 ]] && error "--macos-installer requires an argument"
        [[ "$2" =~ ^- ]] && error "--macos-installer requires 'uv' or 'pipx', not an option"
        validate_dependency_installer "macOS installer" "$2"
        MACOS_DEPENDENCY_INSTALLER="$2"
        shift 2
        ;;
      --linux-installer)
        [[ $# -lt 2 ]] && error "--linux-installer requires an argument"
        [[ "$2" =~ ^- ]] && error "--linux-installer requires 'uv' or 'pipx', not an option"
        validate_dependency_installer "Linux installer" "$2"
        LINUX_DEPENDENCY_INSTALLER="$2"
        shift 2
        ;;
      --no-auto-install)
        AUTO_INSTALL="false"
        shift
        ;;
      -h|--help) usage; exit 0 ;;
      *) error "Unknown option: $1" ;;
    esac
  done
}


get_latest_release() {
  local api_url="https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/releases/latest"
  local result
  
  if command -v curl >/dev/null 2>&1; then
    result=$(curl -qfsSL --max-time 10 "$api_url" 2>/dev/null | sed -En 's/.*"tag_name": "([^"]+)".*/\1/p')
  elif command -v wget >/dev/null 2>&1; then
    result=$(wget --timeout=10 -qO- "$api_url" 2>/dev/null | sed -En 's/.*"tag_name": "([^"]+)".*/\1/p')
  else
    error "Neither curl nor wget found"
  fi
  
  [[ -z "$result" ]] && error "Failed to fetch release information from GitHub"
  echo "$result"
}

download_and_extract() {
  local version="$1"
  
  # Resolve "latest" to actual version
  if [[ "$version" == "latest" ]]; then
    log "Fetching latest release..."
    version=$(get_latest_release)
    log "Latest version: $version"
  fi
  
  # Ensure 'v' prefix for URL
  local version_tag="$version"
  [[ "$version_tag" =~ ^v ]] || version_tag="v$version_tag"
  
  # Strip 'v' prefix for package name
  local version_number="${version_tag#v}"
  
  # Download from release assets (sdist)
  local url="https://github.com/$REPO_OWNER/$REPO_NAME/releases/download/$version_tag/$REPO_NAME-$version_number.tar.gz"
  TEMP_DIR=$(mktemp -d)
  local archive="$TEMP_DIR/boilerplates.tar.gz"
  
  log "Downloading $version_tag from release assets..."
  
  if command -v curl >/dev/null 2>&1; then
    curl -qfsSL --max-time 30 -o "$archive" "$url" || error "Download failed. URL: $url"
  elif command -v wget >/dev/null 2>&1; then
    wget --timeout=30 -qO "$archive" "$url" || error "Download failed. URL: $url"
  fi
  
  log "Extracting package..."
  
  # Extract the tarball
  tar -xzf "$archive" -C "$TEMP_DIR" || error "Extraction failed"
  
  # Find the extracted directory (should be boilerplates-X.Y.Z)
  local source_dir=$(find "$TEMP_DIR" -maxdepth 1 -type d -name "$REPO_NAME-*" | head -n1)
  [[ -z "$source_dir" ]] && error "Failed to locate extracted files"
  
  # Verify essential files exist
  [[ ! -f "$source_dir/setup.py" ]] && [[ ! -f "$source_dir/pyproject.toml" ]] && \
    error "Invalid package: missing setup.py or pyproject.toml"
  
  # Return the path to the extracted directory
  echo "$source_dir"
}

install_cli() {
  local package_path="$1"
  local version="$2"
  
  if [[ "$INSTALL_METHOD" == "uv" ]] || [[ "$INSTALL_METHOD" == "uvx" ]]; then
    log "Installing CLI via uv..."
    "$UV_CMD" tool uninstall boilerplates >/dev/null 2>&1 || true

    if ! "$UV_CMD" tool install "$package_path" >/dev/null 2>&1; then
      error "uv installation failed. Try: uv tool install $package_path"
    fi
  else
    log "Installing CLI via pipx..."
    "$PIPX_CMD" ensurepath 2>&1 | grep -v "^$" || true
    
    # Install from tarball
    if ! "$PIPX_CMD" install --force "$package_path" >/dev/null 2>&1; then
      error "pipx installation failed. Try: pipx uninstall boilerplates && pipx install boilerplates"
    fi
  fi
  
  log "CLI installed successfully"
  
  # Verify installation
  if command -v boilerplates >/dev/null 2>&1; then
    log "Command 'boilerplates' is now available"
  else
    log "Warning: 'boilerplates' command not found in PATH. You may need to restart your shell or run: pipx ensurepath"
  fi
}

main() {
  parse_args "$@"
  
  # Ensure cleanup on exit
  trap '[[ -d "${TEMP_DIR:-}" ]] && rm -rf "$TEMP_DIR"' EXIT
  
  log "Checking dependencies..."
  check_dependencies
  
  local package_path
  package_path=$(download_and_extract "$INSTALL_VERSION")
  install_cli "$package_path" "$INSTALL_VERSION"

  local uninstall_cmd="pipx uninstall boilerplates"
  if [[ "$INSTALL_METHOD" == "uv" ]] || [[ "$INSTALL_METHOD" == "uvx" ]]; then
    uninstall_cmd="uv tool uninstall boilerplates"
  fi
  
  # Get installed version
  local installed_version=$(boilerplates --version 2>/dev/null | grep -oE 'v?[0-9]+\.[0-9]+\.[0-9]+' || echo "unknown")
  
  cat >&2 <<EOF

Installation complete!

Version: $installed_version
Installed via: $INSTALL_METHOD

Usage:
  boilerplates --help

Update:
  curl -qfsSL https://raw.githubusercontent.com/$REPO_OWNER/$REPO_NAME/main/scripts/install.sh | bash

Uninstall:
  $uninstall_cmd
EOF
}

if [[ "${BASH_SOURCE[0]-$0}" == "$0" ]]; then
  main "$@"
fi
