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
  curl -qfsSL https://raw.githubusercontent.com/$REPO_OWNER/$REPO_NAME/main/scripts/install.sh | bash
  curl -qfsSL https://raw.githubusercontent.com/$REPO_OWNER/$REPO_NAME/main/scripts/install.sh | bash -s -- --version v1.0.0
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
      --path)
        [[ $# -lt 2 ]] && error "--path requires an argument"
        [[ "$2" =~ ^- ]] && error "--path requires a directory path, not an option"
        TARGET_DIR="$2"
        shift 2
        ;;
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

validate_target_dir() {
  local dir="$1"
  local normalized="$(python3 -c "import os, sys; print(os.path.abspath(os.path.expanduser('$dir')))" 2>/dev/null)"
  
  [[ -z "$normalized" ]] && error "Invalid path: $dir"
  
  # Prevent dangerous paths
  case "$normalized" in
    /|/bin|/boot|/dev|/etc|/lib|/lib64|/proc|/root|/sbin|/sys|/usr|/var)
      error "Refusing to use system directory: $normalized"
      ;;
    /home|/Users)
      error "Refusing to use top-level home directory: $normalized"
      ;;
  esac
  
  # If directory exists, validate it's safe to remove
  if [[ -d "$normalized" ]]; then
    # Check for our marker file
    if [[ ! -f "$normalized/.version" ]] && [[ -n "$(ls -A "$normalized" 2>/dev/null)" ]]; then
      error "Directory exists and contains unknown content: $normalized\nRefusing to overwrite for safety. Please remove it manually or choose a different path."
    fi
  fi
  
  echo "$normalized"
}

get_latest_release() {
  local api_url="https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/releases/latest"
  
  if command -v curl >/dev/null 2>&1; then
    curl -qfsSL "$api_url" | sed -En 's/.*"tag_name": "([^"]+)".*/\1/p'
  elif command -v wget >/dev/null 2>&1; then
    wget -qO- "$api_url" | sed -En 's/.*"tag_name": "([^"]+)".*/\1/p'
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
  
  # Ensure cleanup on exit
  trap '[[ -d "${temp_dir:-}" ]] && rm -rf "$temp_dir"' RETURN
  
  log "Downloading $version..."
  
  if command -v curl >/dev/null 2>&1; then
    curl -qfsSL -o "$archive" "$url" || error "Download failed"
  elif command -v wget >/dev/null 2>&1; then
    wget -qO "$archive" "$url" || error "Download failed"
  fi
  
  log "Extracting to $TARGET_DIR..."
  
  [[ -d "$TARGET_DIR" ]] && rm -rf "$TARGET_DIR"
  mkdir -p "$(dirname "$TARGET_DIR")"
  
  tar -xzf "$archive" -C "$(dirname "$TARGET_DIR")" || error "Extraction failed"
  
  mv "$(dirname "$TARGET_DIR")/$REPO_NAME-${version#v}" "$TARGET_DIR" || error "Installation failed"
  
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
  
  TARGET_DIR=$(validate_target_dir "$TARGET_DIR")
  
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
  curl -qfsSL https://raw.githubusercontent.com/$REPO_OWNER/$REPO_NAME/main/scripts/install.sh | bash
EOF
}

main "$@"
