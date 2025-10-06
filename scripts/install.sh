#!/usr/bin/env bash
set -euo pipefail

REPO_OWNER="christianlempa"
REPO_NAME="boilerplates"
VERSION="${VERSION:-latest}"

usage() {
  cat <<USAGE
Usage: install.sh [OPTIONS]

Install the boilerplates CLI from GitHub releases via pipx.

Options:
  --version VER     Version to install (default: "latest")
  -h, --help        Show this message

Examples:
  curl -qfsSL https://raw.githubusercontent.com/$REPO_OWNER/$REPO_NAME/main/scripts/install.sh | bash
  curl -qfsSL https://raw.githubusercontent.com/$REPO_OWNER/$REPO_NAME/main/scripts/install.sh | bash -s -- --version v1.0.0

Uninstall:
  pipx uninstall boilerplates
USAGE
}

log() { printf '[boilerplates] %s\n' "$*" >&2; }
error() { printf '[boilerplates][error] %s\n' "$*" >&2; exit 1; }

check_dependencies() {
  command -v tar >/dev/null 2>&1 || error "tar is required but not found"
  command -v mktemp >/dev/null 2>&1 || error "mktemp is required but not found"
  command -v python3 >/dev/null 2>&1 || error "Python 3 is required. Install: sudo apt install python3 python3-pip"
  python3 -m pip --version >/dev/null 2>&1 || error "pip is required. Install: sudo apt install python3-pip"
  
  if command -v pipx >/dev/null 2>&1; then
    PIPX_CMD="pipx"
  elif [[ -x "$(python3 -m site --user-base 2>/dev/null)/bin/pipx" ]]; then
    PIPX_CMD="$(python3 -m site --user-base)/bin/pipx"
  else
    error "pipx is required. Install: pip install --user pipx"
  fi
  
  log "✓ All dependencies available"
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --version)
        [[ $# -lt 2 ]] && error "--version requires an argument"
        [[ "$2" =~ ^- ]] && error "--version requires a version string, not an option"
        VERSION="$2"
        shift 2
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
  
  # Ensure 'v' prefix
  [[ "$version" =~ ^v ]] || version="v$version"
  
  local url="https://github.com/$REPO_OWNER/$REPO_NAME/archive/refs/tags/$version.tar.gz"
  local temp_dir=$(mktemp -d)
  local archive="$temp_dir/release.tar.gz"
  local extract_dir="$temp_dir/extracted"
  
  # Ensure cleanup on exit
  trap '[[ -d "${temp_dir:-}" ]] && rm -rf "$temp_dir"' RETURN
  
  log "Downloading $version..."
  
  if command -v curl >/dev/null 2>&1; then
    curl -qfsSL --max-time 30 -o "$archive" "$url" || error "Download failed"
  elif command -v wget >/dev/null 2>&1; then
    wget --timeout=30 -qO "$archive" "$url" || error "Download failed"
  fi
  
  log "Extracting release..."
  
  mkdir -p "$extract_dir"
  tar -xzf "$archive" -C "$extract_dir" || error "Extraction failed"
  
  # Find the extracted directory (should be boilerplates-X.Y.Z)
  local source_dir=$(find "$extract_dir" -maxdepth 1 -type d -name "$REPO_NAME-*" | head -n1)
  [[ -z "$source_dir" ]] && error "Failed to locate extracted files"
  
  # Verify essential files exist
  [[ ! -f "$source_dir/setup.py" ]] && [[ ! -f "$source_dir/pyproject.toml" ]] && \
    error "Invalid package: missing setup.py or pyproject.toml"
  
  echo "$source_dir"
}

install_cli() {
  local source_dir="$1"
  local version="$2"
  
  log "Installing CLI via pipx..."
  "$PIPX_CMD" ensurepath 2>&1 | grep -v "^$" || true
  
  # Install from source directory
  if ! "$PIPX_CMD" install --force "$source_dir" 2>&1; then
    error "pipx installation failed. Try: pipx uninstall boilerplates && pipx install boilerplates"
  fi
  
  log "✓ CLI installed successfully"
  
  # Verify installation
  if command -v boilerplates >/dev/null 2>&1; then
    log "✓ Command 'boilerplates' is now available"
  else
    log "⚠ Warning: 'boilerplates' command not found in PATH. You may need to restart your shell or run: pipx ensurepath"
  fi
}

main() {
  parse_args "$@"
  
  log "Checking dependencies..."
  check_dependencies
  
  local source_dir=$(download_and_extract "$VERSION")
  install_cli "$source_dir" "$VERSION"
  
  # Get installed version
  local installed_version=$(boilerplates --version 2>/dev/null | grep -oE 'v?[0-9]+\.[0-9]+\.[0-9]+' || echo "unknown")
  
  cat <<EOF

✓ Installation complete!

Version: $installed_version
Installed via: pipx

Usage:
  boilerplates --help
  boilerplates compose list
  boilerplates compose generate <template>

Update:
  curl -qfsSL https://raw.githubusercontent.com/$REPO_OWNER/$REPO_NAME/main/scripts/install.sh | bash

Uninstall:
  pipx uninstall boilerplates
EOF
}

main "$@"
