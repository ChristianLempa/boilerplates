#!/usr/bin/env bash
set -euo pipefail

REPO_OWNER="christianlempa"
REPO_NAME="boilerplates"
VERSION="${VERSION:-latest}"
TARGET_DIR="${TARGET_DIR:-$HOME/boilerplates}"

usage() {
  cat <<USAGE
Usage: install.sh [OPTIONS]

Install the boilerplates CLI from GitHub releases.

Options:
  --path DIR        Installation directory (default: "$HOME/boilerplates")
  --version VER     Version to install (default: "latest")
  -h, --help        Show this message

Examples:
  curl -fsSL https://raw.githubusercontent.com/christianlempa/boilerplates/main/scripts/install.sh | bash
  curl -fsSL https://raw.githubusercontent.com/christianlempa/boilerplates/main/scripts/install.sh | bash -s -- --version v1.0.0
USAGE
}

log() { printf '[boilerplates] %s\n' "$*" >&2; }
error() { printf '[boilerplates][error] %s\n' "$*" >&2; exit 1; }

check_dependencies() {
  command -v tar >/dev/null 2>&1 || error "tar is required but not found"
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
      --path) TARGET_DIR="$2"; shift 2 ;;
      --version) VERSION="$2"; shift 2 ;;
      -h|--help) usage; exit 0 ;;
      *) error "Unknown option: $1" ;;
    esac
  done
}

get_latest_release() {
  local api_url="https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/releases/latest"
  
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$api_url" | grep '"tag_name":' | sed -E 's/.*"tag_name": "([^"]+)".*/\1/'
  elif command -v wget >/dev/null 2>&1; then
    wget -qO- "$api_url" | grep '"tag_name":' | sed -E 's/.*"tag_name": "([^"]+)".*/\1/'
  else
    echo "error" >&2; return 1
  fi
}

download_release() {
  local version="$1"
  
  # Resolve "latest" to actual version
  if [[ "$version" == "latest" ]]; then
    log "Fetching latest release..."
    version=$(get_latest_release)
    [[ "$version" =~ ^error ]] && error "Failed to fetch latest release"
    log "Latest version: $version"
  fi
  
  # Ensure 'v' prefix
  [[ "$version" =~ ^v ]] || version="v$version"
  
  local url="https://github.com/$REPO_OWNER/$REPO_NAME/archive/refs/tags/$version.tar.gz"
  local temp_dir=$(mktemp -d)
  local archive="$temp_dir/release.tar.gz"
  
  log "Downloading $version..."
  
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL -o "$archive" "$url" || { rm -rf "$temp_dir"; error "Download failed"; }
  elif command -v wget >/dev/null 2>&1; then
    wget -qO "$archive" "$url" || { rm -rf "$temp_dir"; error "Download failed"; }
  fi
  
  log "Extracting to $TARGET_DIR..."
  
  [[ -d "$TARGET_DIR" ]] && rm -rf "$TARGET_DIR"
  mkdir -p "$(dirname "$TARGET_DIR")"
  
  tar -xzf "$archive" -C "$(dirname "$TARGET_DIR")" || { rm -rf "$temp_dir"; error "Extraction failed"; }
  
  mv "$(dirname "$TARGET_DIR")/$REPO_NAME-${version#v}" "$TARGET_DIR" || { rm -rf "$temp_dir"; error "Installation failed"; }
  
  rm -rf "$temp_dir"
  echo "$version" > "$TARGET_DIR/.version"
  log "✓ Release extracted"
}

install_cli() {
  log "Installing CLI via pipx..."
  "$PIPX_CMD" ensurepath 2>&1 | grep -v "^$" || true
  "$PIPX_CMD" install --editable --force "$TARGET_DIR"
}

main() {
  parse_args "$@"
  
  log "Checking dependencies..."
  check_dependencies
  
  TARGET_DIR=$(python3 -c "import os, sys; print(os.path.abspath(os.path.expanduser('$TARGET_DIR')))")
  
  download_release "$VERSION"
  install_cli
  
  local version=$(cat "$TARGET_DIR/.version" 2>/dev/null || echo "unknown")
  
  cat <<EOF

✓ Installation complete!

Version: $version
Location: $TARGET_DIR

Usage:
  boilerplates --help
  boilerplates compose list
  boilerplates compose generate <template>

Update:
  curl -fsSL https://raw.githubusercontent.com/$REPO_OWNER/$REPO_NAME/main/scripts/install.sh | bash
