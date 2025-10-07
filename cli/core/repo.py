"""Repository management module for syncing library repositories."""
from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from typer import Argument, Option, Typer

from ..core.config import ConfigManager
from ..core.display import DisplayManager, IconManager
from ..core.exceptions import ConfigError

logger = logging.getLogger(__name__)
console = Console()
console_err = Console(stderr=True)
display = DisplayManager()

app = Typer(help="Manage library repositories")


def _run_git_command(args: list[str], cwd: Optional[Path] = None) -> tuple[bool, str, str]:
    """Run a git command and return the result.
    
    Args:
        args: Git command arguments (without 'git' prefix)
        cwd: Working directory for the command
        
    Returns:
        Tuple of (success, stdout, stderr)
    """
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out after 5 minutes"
    except FileNotFoundError:
        return False, "", "Git command not found. Please install git."
    except Exception as e:
        return False, "", str(e)


def _clone_or_pull_repo(name: str, url: str, target_path: Path, branch: Optional[str] = None, sparse_dir: Optional[str] = None) -> tuple[bool, str]:
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
        # Repository exists, pull updates
        logger.debug(f"Pulling updates for library '{name}' at {target_path}")
        
        # Determine which branch to pull
        pull_branch = branch if branch else "main"
        
        # Pull updates from specific branch
        success, stdout, stderr = _run_git_command(
            ["pull", "--ff-only", "origin", pull_branch],
            cwd=target_path
        )
        
        if success:
            # Check if anything was updated
            if "Already up to date" in stdout or "Already up-to-date" in stdout:
                return True, "Already up to date"
            else:
                return True, "Updated successfully"
        else:
            error_msg = stderr or stdout
            logger.error(f"Failed to pull library '{name}': {error_msg}")
            return False, f"Pull failed: {error_msg}"
    else:
        # Repository doesn't exist, clone it
        logger.debug(f"Cloning library '{name}' from {url} to {target_path}")
        
        # Ensure parent directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Determine if we should use sparse-checkout
        use_sparse = sparse_dir and sparse_dir != "."
        
        if use_sparse:
            # Use sparse-checkout to clone only specific directory
            logger.debug(f"Using sparse-checkout for directory: {sparse_dir}")
            
            # Initialize empty repo
            success, stdout, stderr = _run_git_command(["init"], cwd=None)
            if success:
                # Create target directory
                target_path.mkdir(parents=True, exist_ok=True)
                
                # Initialize git repo
                success, stdout, stderr = _run_git_command(["init"], cwd=target_path)
                if not success:
                    return False, f"Failed to initialize repo: {stderr or stdout}"
                
                # Add remote
                success, stdout, stderr = _run_git_command(["remote", "add", "origin", url], cwd=target_path)
                if not success:
                    return False, f"Failed to add remote: {stderr or stdout}"
                
                # Enable sparse-checkout (non-cone mode to exclude root files)
                success, stdout, stderr = _run_git_command(
                    ["sparse-checkout", "init", "--no-cone"], 
                    cwd=target_path
                )
                if not success:
                    return False, f"Failed to enable sparse-checkout: {stderr or stdout}"
                
                # Set sparse-checkout to specific directory (non-cone uses patterns)
                success, stdout, stderr = _run_git_command(
                    ["sparse-checkout", "set", f"{sparse_dir}/*"],
                    cwd=target_path
                )
                if not success:
                    return False, f"Failed to set sparse-checkout directory: {stderr or stdout}"
                
                # Fetch specific branch (without attempting to update local ref)
                fetch_args = ["fetch", "--depth", "1", "origin"]
                if branch:
                    fetch_args.append(branch)
                else:
                    fetch_args.append("main")
                
                success, stdout, stderr = _run_git_command(fetch_args, cwd=target_path)
                if not success:
                    return False, f"Fetch failed: {stderr or stdout}"
                
                # Checkout the branch
                checkout_branch = branch if branch else "main"
                success, stdout, stderr = _run_git_command(
                    ["checkout", checkout_branch],
                    cwd=target_path
                )
                if not success:
                    return False, f"Checkout failed: {stderr or stdout}"
                
                # Done! Files are in target_path/sparse_dir/
                return True, "Cloned successfully (sparse)"
            else:
                return False, f"Failed to initialize: {stderr or stdout}"
        else:
            # Regular full clone
            clone_args = ["clone", "--depth", "1"]
            if branch:
                clone_args.extend(["--branch", branch])
            clone_args.extend([url, str(target_path)])
            
            success, stdout, stderr = _run_git_command(clone_args)
            
            if success:
                return True, "Cloned successfully"
            else:
                error_msg = stderr or stdout
                logger.error(f"Failed to clone library '{name}': {error_msg}")
                return False, f"Clone failed: {error_msg}"


@app.command()
def update(
    library_name: Optional[str] = Argument(
        None,
        help="Name of specific library to update (updates all if not specified)"
    ),
    verbose: bool = Option(False, "--verbose", "-v", help="Show detailed output")
) -> None:
    """Update library repositories by cloning or pulling from git.
    
    This command syncs all configured libraries from their git repositories.
    If a library doesn't exist locally, it will be cloned. If it exists, it will be pulled.
    """
    config = ConfigManager()
    libraries = config.get_libraries()
    
    if not libraries:
        console.print("[yellow]No libraries configured.[/yellow]")
        console.print("Libraries are auto-configured on first run with a default library.")
        return
    
    # Filter to specific library if requested
    if library_name:
        libraries = [lib for lib in libraries if lib.get("name") == library_name]
        if not libraries:
            console_err.print(f"[red]Error:[/red] Library '{library_name}' not found in configuration")
            return
    
    libraries_path = config.get_libraries_path()
    
    # Create results table
    results = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for lib in libraries:
            name = lib.get("name")
            url = lib.get("url")
            branch = lib.get("branch")
            directory = lib.get("directory", "library")
            enabled = lib.get("enabled", True)
            
            if not enabled:
                if verbose:
                    console.print(f"[dim]Skipping disabled library: {name}[/dim]")
                results.append((name, "Skipped (disabled)", False))
                continue
            
            task = progress.add_task(f"Updating {name}...", total=None)
            
            # Target path: ~/.config/boilerplates/libraries/{name}/
            target_path = libraries_path / name
            
            # Clone or pull the repository with sparse-checkout if directory is specified
            success, message = _clone_or_pull_repo(name, url, target_path, branch, directory)
            
            results.append((name, message, success))
            progress.remove_task(task)
            
            if verbose:
                if success:
                    display.display_success(f"{name}: {message}")
                else:
                    display.display_error(f"{name}: {message}")
    
    # Display summary table
    if not verbose:
        table = Table(title="Library Update Summary", show_header=True)
        table.add_column("Library", style="cyan", no_wrap=True)
        table.add_column("Status")
        
        for name, message, success in results:
            status_style = "green" if success else "red"
            status_icon = IconManager.get_status_icon("success" if success else "error")
            table.add_row(name, f"[{status_style}]{status_icon} {message}[/{status_style}]")
        
        console.print(table)
    
    # Summary
    total = len(results)
    successful = sum(1 for _, _, success in results if success)
    
    if successful == total:
        console.print(f"\n[green]All libraries updated successfully ({successful}/{total})[/green]")
    elif successful > 0:
        console.print(f"\n[yellow]Partially successful: {successful}/{total} libraries updated[/yellow]")
    else:
        console.print(f"\n[red]Failed to update libraries[/red]")


@app.command()
def list() -> None:
    """List all configured libraries."""
    config = ConfigManager()
    libraries = config.get_libraries()
    
    if not libraries:
        console.print("[yellow]No libraries configured.[/yellow]")
        return
    
    table = Table(title="Configured Libraries", show_header=True)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("URL", style="blue")
    table.add_column("Branch", style="yellow")
    table.add_column("Directory", style="magenta")
    table.add_column("Status", style="green")
    
    libraries_path = config.get_libraries_path()
    
    for lib in libraries:
        name = lib.get("name", "")
        url = lib.get("url", "")
        branch = lib.get("branch", "main")
        directory = lib.get("directory", "library")
        enabled = lib.get("enabled", True)
        
        # Check if library exists locally
        library_base = libraries_path / name
        if directory and directory != ".":
            library_path = library_base / directory
        else:
            library_path = library_base
        exists = library_path.exists()
        
        status_parts = []
        if not enabled:
            status_parts.append("[dim]disabled[/dim]")
        elif exists:
            status_parts.append("[green]synced[/green]")
        else:
            status_parts.append("[yellow]not synced[/yellow]")
        
        status = " ".join(status_parts)
        
        table.add_row(name, url, branch, directory, status)
    
    console.print(table)


@app.command()
def add(
    name: str = Argument(..., help="Unique name for the library"),
    url: str = Argument(..., help="Git repository URL"),
    branch: str = Option("main", "--branch", "-b", help="Git branch to use"),
    directory: str = Option("library", "--directory", "-d", help="Directory within repo containing templates (metadata only)"),
    enabled: bool = Option(True, "--enabled/--disabled", help="Enable or disable the library"),
    sync: bool = Option(True, "--sync/--no-sync", help="Sync the library after adding")
) -> None:
    """Add a new library to the configuration."""
    config = ConfigManager()
    
    try:
        config.add_library(name, url, directory, branch, enabled)
        display.display_success(f"Added library '{name}'")
        
        if sync and enabled:
            console.print(f"\nSyncing library '{name}'...")
            # Call update for this specific library
            update(library_name=name, verbose=True)
    except ConfigError as e:
        display.display_error(str(e))


@app.command()
def remove(
    name: str = Argument(..., help="Name of the library to remove"),
    keep_files: bool = Option(False, "--keep-files", help="Keep the local library files (don't delete)")
) -> None:
    """Remove a library from the configuration and delete its local files."""
    config = ConfigManager()
    
    try:
        # Remove from config
        config.remove_library(name)
        display.display_success(f"Removed library '{name}' from configuration")
        
        # Delete local files unless --keep-files is specified
        if not keep_files:
            libraries_path = config.get_libraries_path()
            library_path = libraries_path / name
            
            if library_path.exists():
                import shutil
                shutil.rmtree(library_path)
                display.display_success(f"Deleted local files at {library_path}")
            else:
                display.display_info(f"No local files found at {library_path}")
    except ConfigError as e:
        display.display_error(str(e))




# Register the repo command with the CLI
def register_cli(parent_app: Typer) -> None:
    """Register the repo command with the parent Typer app."""
    parent_app.add_typer(app, name="repo")
