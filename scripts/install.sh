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
                    Examples: latest, v1.0.0, v0.0.1
  -h, --help        Show this message

Examples:
  # Install latest version
  curl -fsSL https://raw.githubusercontent.com/christianlempa/boilerplates/main/scripts/install.sh | bash

  # Install specific version
  curl -fsSL https://raw.githubusercontent.com/christianlempa/boilerplates/main/scripts/install.sh | bash -s -- --version v1.0.0

  # Install to custom directory
  curl -fsSL https://raw.githubusercontent.com/christianlempa/boilerplates/main/scripts/install.sh | bash -s -- --path ~/my-boilerplates
USAGE
}

log() {
  printf '[boilerplates] %s\n' "$*"
}

error() {
  printf '[boilerplates][error] %s\n' "$*" >&2
  exit 1
}

warn() {
  printf '[boilerplates][warn] %s\n' "$*" >&2
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || error "Required command '$1' not found in PATH"
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --path)
        [[ $# -lt 2 ]] && error "--path requires a value"
        TARGET_DIR="$2"
        shift 2
        ;;
      --version)
        [[ $# -lt 2 ]] && error "--version requires a value"
        VERSION="$2"
        shift 2
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        error "Unknown option: $1"
        ;;
    esac
  done
}

make_absolute_path() {
  python3 - <<'PY' "$TARGET_DIR"
import os, sys
print(os.path.abspath(os.path.expanduser(sys.argv[1])))
PY
}

get_latest_release() {
  local api_url="https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/releases/latest"
  local release_tag
  
  log "Fetching latest release information..."
  
  if command -v curl >/dev/null 2>&1; then
    release_tag=$(curl -fsSL "$api_url" | grep '"tag_name":' | sed -E 's/.*"tag_name": "([^"]+)".*/\1/')
  elif command -v wget >/dev/null 2>&1; then
    release_tag=$(wget -qO- "$api_url" | grep '"tag_name":' | sed -E 's/.*"tag_name": "([^"]+)".*/\1/')
  else
    error "Neither curl nor wget found. Please install one of them."
  fi
  
  if [[ -z "$release_tag" ]]; then
    error "Failed to fetch latest release tag"
  fi
  
  echo "$release_tag"
}

download_release() {
  local version="$1"
  local download_url
  
  # If version is "latest", resolve it to the actual version tag
  if [[ "$version" == "latest" ]]; then
    version=$(get_latest_release)
    log "Latest version is $version"
  fi
  
  # Ensure version has 'v' prefix for GitHub releases
  if [[ ! "$version" =~ ^v ]]; then
    version="v$version"
  fi
  
  download_url="https://github.com/$REPO_OWNER/$REPO_NAME/archive/refs/tags/$version.tar.gz"
  
  log "Downloading release $version..."
  log "URL: $download_url"
  
  local temp_dir
  temp_dir=$(mktemp -d)
  trap 'rm -rf "$temp_dir"' EXIT
  
  local archive_file="$temp_dir/boilerplates.tar.gz"
  
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL -o "$archive_file" "$download_url" || error "Failed to download release"
  elif command -v wget >/dev/null 2>&1; then
    wget -qO "$archive_file" "$download_url" || error "Failed to download release"
  else
    error "Neither curl nor wget found. Please install one of them."
  fi
  
  log "Extracting release..."
  
  # Remove existing installation if present
  if [[ -d "$TARGET_DIR" ]]; then
    log "Removing existing installation at $TARGET_DIR"
    rm -rf "$TARGET_DIR"
  fi
  
  # Create parent directory
  mkdir -p "$(dirname "$TARGET_DIR")"
  
  # Extract with strip-components to remove the top-level directory
  tar -xzf "$archive_file" -C "$(dirname "$TARGET_DIR")"
  
  # Rename extracted directory to target name
  local extracted_dir
  extracted_dir=$(dirname "$TARGET_DIR")/"$REPO_NAME-${version#v}"
  
  if [[ ! -d "$extracted_dir" ]]; then
    error "Extraction failed: expected directory $extracted_dir not found"
  fi
  
  mv "$extracted_dir" "$TARGET_DIR"
  
  log "Release extracted to $TARGET_DIR"
  
  # Store version info
  echo "$version" > "$TARGET_DIR/.installed-version"
}

ensure_pipx() {
  if command -v pipx >/dev/null 2>&1; then
    PIPX_CMD="pipx"
    return
  fi

  log "pipx not found; attempting user-level install"
  python3 -m pip install --user pipx >/dev/null 2>&1 || warn "pipx install via pip failed"

  if command -v pipx >/dev/null 2>&1; then
    PIPX_CMD="pipx"
    return
  fi

  local user_bin
  user_bin="$(python3 -m site --user-base 2>/dev/null)/bin"
  if [[ -x "$user_bin/pipx" ]]; then
    PIPX_CMD="$user_bin/pipx"
  else
    error "pipx is required. Install it (e.g. 'python3 -m pip install --user pipx') and ensure it is on PATH."
  fi
}

pipx_install() {
  "${PIPX_CMD}" ensurepath >/dev/null 2>&1 || warn "pipx ensurepath failed; make sure pipx's bin dir is on PATH"
  log "Installing/updating boilerplates via pipx"
  "${PIPX_CMD}" install --editable --force "$TARGET_DIR"
}

check_current_version() {
  if [[ -f "$TARGET_DIR/.installed-version" ]]; then
    cat "$TARGET_DIR/.installed-version"
  else
    echo "unknown"
  fi
}

main() {
  parse_args "$@"
  require_command python3
  require_command tar

  TARGET_DIR="$(make_absolute_path)"
  
  # Check if already installed
  local current_version
  current_version=$(check_current_version)
  
  if [[ "$current_version" != "unknown" ]]; then
    log "Currently installed version: $current_version"
  fi

  download_release "$VERSION"
  ensure_pipx
  pipx_install

  local pipx_info
  pipx_info=$("${PIPX_CMD}" list --short 2>/dev/null | grep -E '^boilerplates' || echo "boilerplates (not detected)")
  
  local installed_version
  installed_version=$(check_current_version)

  cat <<EOF2

✓ Installation complete!

Version: $installed_version
Location: $TARGET_DIR
pipx environment: $pipx_info

To use the CLI:
  boilerplate --help
  boilerplate --version

To update to the latest version:
  curl -fsSL https://raw.githubusercontent.com/$REPO_OWNER/$REPO_NAME/main/scripts/install.sh | bash

To install a specific version:
  curl -fsSL https://raw.githubusercontent.com/$REPO_OWNER/$REPO_NAME/main/scripts/install.sh | bash -s -- --version v1.0.0
EOF2
}

main "$@"
