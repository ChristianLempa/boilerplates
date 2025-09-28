#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/christianlempa/boilerplates.git}"
BRANCH="${BRANCH:-main}"
TARGET_DIR="${TARGET_DIR:-$HOME/boilerplates}"

usage() {
  cat <<USAGE
Usage: install.sh [--path DIR] [--repo URL] [--branch BRANCH]

Options:
  --path DIR      Installation directory (default: \"$HOME/boilerplates\")
  --repo URL      Git repository URL (default: $REPO_URL)
  --branch NAME   Git branch or tag to checkout (default: $BRANCH)
  -h, --help      Show this message
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
      --repo)
        [[ $# -lt 2 ]] && error "--repo requires a value"
        REPO_URL="$2"
        shift 2
        ;;
      --branch)
        [[ $# -lt 2 ]] && error "--branch requires a value"
        BRANCH="$2"
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

update_repo() {
  log "Updating existing repository at $TARGET_DIR"
  git -C "$TARGET_DIR" fetch --tags origin "$BRANCH"
  git -C "$TARGET_DIR" checkout "$BRANCH"
  git -C "$TARGET_DIR" pull --ff-only origin "$BRANCH"
}

clone_repo() {
  log "Cloning $REPO_URL into $TARGET_DIR"
  git clone --branch "$BRANCH" "$REPO_URL" "$TARGET_DIR"
}

ensure_repo() {
  if [[ -d "$TARGET_DIR/.git" ]]; then
    local current_remote
    if current_remote=$(git -C "$TARGET_DIR" remote get-url origin 2>/dev/null); then
      if [[ "$current_remote" != "$REPO_URL" ]]; then
        log "Updating origin remote to $REPO_URL"
        git -C "$TARGET_DIR" remote set-url origin "$REPO_URL"
      fi
    fi
    update_repo
  elif [[ -e "$TARGET_DIR" ]]; then
    error "Target path $TARGET_DIR exists but is not a git repository"
  else
    mkdir -p "$(dirname "$TARGET_DIR")"
    clone_repo
  fi
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

main() {
  parse_args "$@"
  require_command git
  require_command python3

  TARGET_DIR="$(make_absolute_path)"

  ensure_repo
  ensure_pipx
  pipx_install

  local pipx_info
  pipx_info=$("${PIPX_CMD}" list --short 2>/dev/null | grep -E '^boilerplates' || echo "boilerplates (not detected)")

  cat <<EOF2

Installation complete.
Repository: $TARGET_DIR
pipx environment: $pipx_info

To use the CLI:
  boilerplate --help

Re-run this script anytime to fetch the latest changes and refresh dependencies.
EOF2
}

main "$@"
