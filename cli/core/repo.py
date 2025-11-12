"""Repository management module for syncing library repositories."""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

from rich.progress import SpinnerColumn, TextColumn
from rich.table import Table
from typer import Argument, Option, Typer

from ..core.config import ConfigManager, LibraryConfig
from ..core.display import DisplayManager, IconManager
from ..core.exceptions import ConfigError

logger = logging.getLogger(__name__)
display = DisplayManager()

app = Typer(help="Manage library repositories")


def _run_git_command(args: list[str], cwd: Path | None = None) -> tuple[bool, str, str]:
    """Run a git command and return the result.

    Args:
        args: Git command arguments (without 'git' prefix)
        cwd: Working directory for the command

    Returns:
        Tuple of (success, stdout, stderr)
    """
    try:
        result = subprocess.run(
            ["git", *args],
            check=False,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out after 5 minutes"
    except FileNotFoundError:
        return False, "", "Git command not found. Please install git."
    except Exception as e:
        return False, "", str(e)


def _clone_or_pull_repo(
    name: str,
    url: str,
    target_path: Path,
    branch: str | None = None,
    sparse_dir: str | None = None,
) -> tuple[bool, str]:
    """Clone or pull a git repository with optional sparse-checkout.

    Args:
        name: Library name
        url: Git repository URL
        target_path: Target directory for the repository
        branch: Git branch to clone/pull (optional)
        sparse_dir: Directory to sparse-checkout (optional, use None or "." for full clone)

    Returns:
        Tuple of (success, message)
    """
    if target_path.exists() and (target_path / ".git").exists():
        return _pull_repo_updates(name, target_path, branch)
    return _clone_new_repo(name, url, target_path, branch, sparse_dir)


def _pull_repo_updates(name: str, target_path: Path, branch: str | None) -> tuple[bool, str]:
    """Pull updates for an existing repository."""
    logger.debug(f"Pulling updates for library '{name}' at {target_path}")

    pull_branch = branch if branch else "main"
    success, stdout, stderr = _run_git_command(["pull", "--ff-only", "origin", pull_branch], cwd=target_path)

    if not success:
        error_msg = stderr or stdout
        logger.error(f"Failed to pull library '{name}': {error_msg}")
        return False, f"Pull failed: {error_msg}"

    if "Already up to date" in stdout or "Already up-to-date" in stdout:
        return True, "Already up to date"
    return True, "Updated successfully"


def _clone_new_repo(
    name: str, url: str, target_path: Path, branch: str | None, sparse_dir: str | None
) -> tuple[bool, str]:
    """Clone a new repository, optionally with sparse-checkout."""
    logger.debug(f"Cloning library '{name}' from {url} to {target_path}")
    target_path.parent.mkdir(parents=True, exist_ok=True)

    use_sparse = sparse_dir and sparse_dir != "."

    if use_sparse:
        return _clone_sparse_repo(url, target_path, branch, sparse_dir)
    return _clone_full_repo(name, url, target_path, branch)


def _clone_sparse_repo(url: str, target_path: Path, branch: str | None, sparse_dir: str) -> tuple[bool, str]:
    """Clone repository with sparse-checkout."""
    logger.debug(f"Using sparse-checkout for directory: {sparse_dir}")
    target_path.mkdir(parents=True, exist_ok=True)

    # Define git operations to perform sequentially
    operations = [
        (["init"], "Failed to initialize repo"),
        (["remote", "add", "origin", url], "Failed to add remote"),
        (["sparse-checkout", "init", "--no-cone"], "Failed to enable sparse-checkout"),
        (
            ["sparse-checkout", "set", f"{sparse_dir}/*"],
            "Failed to set sparse-checkout directory",
        ),
    ]

    # Execute initial operations
    for cmd, error_msg in operations:
        success, stdout, stderr = _run_git_command(cmd, cwd=target_path)
        if not success:
            return False, f"{error_msg}: {stderr or stdout}"

    # Fetch and checkout
    fetch_branch = branch if branch else "main"
    success, stdout, stderr = _run_git_command(["fetch", "--depth", "1", "origin", fetch_branch], cwd=target_path)
    if not success:
        return False, f"Fetch failed: {stderr or stdout}"

    success, stdout, stderr = _run_git_command(["checkout", fetch_branch], cwd=target_path)
    result_success = success
    result_msg = "Cloned successfully (sparse)" if success else f"Checkout failed: {stderr or stdout}"

    return result_success, result_msg


def _clone_full_repo(name: str, url: str, target_path: Path, branch: str | None) -> tuple[bool, str]:
    """Clone full repository."""
    clone_args = ["clone", "--depth", "1"]
    if branch:
        clone_args.extend(["--branch", branch])
    clone_args.extend([url, str(target_path)])

    success, stdout, stderr = _run_git_command(clone_args)

    if success:
        return True, "Cloned successfully"
    error_msg = stderr or stdout
    logger.error(f"Failed to clone library '{name}': {error_msg}")
    return False, f"Clone failed: {error_msg}"


def _process_library_update(lib: dict, libraries_path: Path, progress, verbose: bool) -> tuple[str, str, bool]:
    """Process a single library update and return result."""
    name = lib.get("name")
    lib_type = lib.get("type", "git")
    enabled = lib.get("enabled", True)

    if not enabled:
        if verbose:
            display.text(f"Skipping disabled library: {name}", style="dim")
        return (name, "Skipped (disabled)", False)

    if lib_type == "static":
        if verbose:
            display.text(f"Skipping static library: {name} (no sync needed)", style="dim")
        return (name, "N/A (static)", True)

    # Handle git libraries
    url = lib.get("url")
    branch = lib.get("branch")
    directory = lib.get("directory", "library")

    task = progress.add_task(f"Updating {name}...", total=None)
    target_path = libraries_path / name
    success, message = _clone_or_pull_repo(name, url, target_path, branch, directory)
    progress.remove_task(task)

    if verbose:
        if success:
            display.success(f"{name}: {message}")
        else:
            display.error(f"{name}: {message}")

    return (name, message, success)


def _display_update_summary(results: list[tuple[str, str, bool]]) -> None:
    """Display update summary."""
    total = len(results)
    successful = sum(1 for _, _, success in results if success)

    display.text("")
    if successful == total:
        display.text(f"All libraries updated successfully ({successful}/{total})", style="green")
    elif successful > 0:
        display.text(
            f"Partially successful: {successful}/{total} libraries updated",
            style="yellow",
        )
    else:
        display.text("Failed to update libraries", style="red")


@app.command()
def update(
    library_name: str | None = Argument(None, help="Name of specific library to update (updates all if not specified)"),
    verbose: bool = Option(False, "--verbose", "-v", help="Show detailed output"),
) -> None:
    """Update library repositories by cloning or pulling from git.

    This command syncs all configured libraries from their git repositories.
    If a library doesn't exist locally, it will be cloned. If it exists, it will be pulled.
    """
    config = ConfigManager()
    libraries = config.get_libraries()

    if not libraries:
        display.warning("No libraries configured")
        display.text("Libraries are auto-configured on first run with a default library.")
        return

    # Filter to specific library if requested
    if library_name:
        libraries = [lib for lib in libraries if lib.get("name") == library_name]
        if not libraries:
            display.error(f"Library '{library_name}' not found in configuration")
            return

    libraries_path = config.get_libraries_path()
    results = []

    with display.progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        for lib in libraries:
            result = _process_library_update(lib, libraries_path, progress, verbose)
            results.append(result)

    # Display summary table
    if not verbose:
        display.display_status_table("Library Update Summary", results, columns=("Library", "Status"))

    _display_update_summary(results)


def _get_library_path_for_git(lib: dict, libraries_path: Path, name: str) -> Path:
    """Get library path for git library type."""
    directory = lib.get("directory", "library")
    library_base = libraries_path / name
    if directory and directory != ".":
        return library_base / directory
    return library_base


def _get_library_path_for_static(lib: dict, config: ConfigManager) -> Path:
    """Get library path for static library type."""
    url_or_path = lib.get("path", "")
    library_path = Path(url_or_path).expanduser()
    if not library_path.is_absolute():
        library_path = (config.config_path.parent / library_path).resolve()
    return library_path


def _get_library_info(lib: dict, config: ConfigManager, libraries_path: Path) -> tuple[str, str, str, str, str, str]:
    """Extract library information based on type."""
    name = lib.get("name", "")
    lib_type = lib.get("type", "git")
    enabled = lib.get("enabled", True)

    if lib_type == "git":
        url_or_path = lib.get("url", "")
        branch = lib.get("branch", "main")
        directory = lib.get("directory", "library")
        library_path = _get_library_path_for_git(lib, libraries_path, name)
        exists = library_path.exists()
        type_icon = IconManager.UI_LIBRARY_GIT

    elif lib_type == "static":
        url_or_path = lib.get("path", "")
        branch = "-"
        directory = "-"
        library_path = _get_library_path_for_static(lib, config)
        exists = library_path.exists()
        type_icon = IconManager.UI_LIBRARY_STATIC

    else:
        # Unknown type
        url_or_path = "<unknown type>"
        branch = "-"
        directory = "-"
        exists = False
        type_icon = "?"

    # Build status string
    status_parts = []
    if not enabled:
        status_parts.append("[dim]disabled[/dim]")
    elif exists:
        status_parts.append("[green]available[/green]")
    else:
        status_parts.append("[yellow]not found[/yellow]")

    status = " ".join(status_parts)
    type_display = f"{type_icon} {lib_type}"

    return url_or_path, branch, directory, type_display, type_icon, status


@app.command()
def list() -> None:
    """List all configured libraries."""
    config = ConfigManager()
    libraries = config.get_libraries()

    if not libraries:
        display.text("No libraries configured.", style="yellow")
        return

    settings = display.settings
    table = Table(
        title="Configured Libraries",
        show_header=True,
        header_style=settings.STYLE_TABLE_HEADER,
    )
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("URL/Path", style="blue")
    table.add_column("Branch", style="yellow")
    table.add_column("Directory", style="magenta")
    table.add_column("Type", style="cyan")
    table.add_column("Status", style="green")

    libraries_path = config.get_libraries_path()

    for lib in libraries:
        name = lib.get("name", "")
        url_or_path, branch, directory, type_display, _type_icon, status = _get_library_info(
            lib, config, libraries_path
        )
        table.add_row(name, url_or_path, branch, directory, type_display, status)

    display.print_table(table)


@app.command()
def add(
    name: str = Argument(..., help="Unique name for the library"),
    *,
    library_type: str | None = None,
    url: str | None = None,
    branch: str = "main",
    directory: str = "library",
    path: str | None = None,
    enabled: bool = Option(True, "--enabled/--disabled", help="Enable or disable the library"),
    sync: bool = Option(True, "--sync/--no-sync", help="Sync after adding (git only)"),
) -> None:
    """Add a new library to the configuration.

    Examples:
      # Add a git library
      repo add mylib --type git --url https://github.com/user/templates.git

      # Add a static library
      repo add local --type static --path ~/my-templates
    """
    config = ConfigManager()

    try:
        if library_type == "git":
            if not url:
                display.error("--url is required for git libraries")
                return
            lib_config = LibraryConfig(
                name=name,
                library_type="git",
                url=url,
                branch=branch,
                directory=directory,
                enabled=enabled,
            )
        elif library_type == "static":
            if not path:
                display.error("--path is required for static libraries")
                return
            lib_config = LibraryConfig(
                name=name,
                library_type="static",
                path=path,
                enabled=enabled,
            )
        else:
            display.error(f"Invalid library type: {library_type}. Must be 'git' or 'static'.")
            return

        config.add_library(lib_config)
        display.success(f"Added {library_type} library '{name}'")

        if library_type == "git" and sync and enabled:
            display.text(f"\nSyncing library '{name}'...")
            update(library_name=name, verbose=True)
        elif library_type == "static":
            display.info(f"Static library points to: {path}")
    except ConfigError as e:
        display.error(str(e))


@app.command()
def remove(
    name: str = Argument(..., help="Name of the library to remove"),
    keep_files: bool = Option(False, "--keep-files", help="Keep the local library files (don't delete)"),
) -> None:
    """Remove a library from the configuration and delete its local files."""
    config = ConfigManager()

    try:
        # Remove from config
        config.remove_library(name)
        display.success(f"Removed library '{name}' from configuration")

        # Delete local files unless --keep-files is specified
        if not keep_files:
            libraries_path = config.get_libraries_path()
            library_path = libraries_path / name

            if library_path.exists():
                shutil.rmtree(library_path)
                display.success(f"Deleted local files at {library_path}")
            else:
                display.info(f"No local files found at {library_path}")
    except ConfigError as e:
        display.error(str(e))


# Register the repo command with the CLI
def register_cli(parent_app: Typer) -> None:
    """Register the repo command with the parent Typer app."""
    parent_app.add_typer(app, name="repo", rich_help_panel="Configuration Commands")
