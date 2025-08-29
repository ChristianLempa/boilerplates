"""
Compose module commands and functionality.
Manage Compose configurations and services and template operations.
"""

import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table

from ...core.command import BaseModule
from ...core.helpers import find_boilerplates


class ComposeModule(BaseModule):
    """Module for managing compose boilerplates."""

    def __init__(self):
        super().__init__(name="compose", icon="🐳", description="Manage Compose Templates and Configurations")

    def _add_module_commands(self, app: typer.Typer) -> None:
        """Add Module-specific commands to the app."""

        @app.command("list", help="List all compose boilerplates")
        def list():
            """List all compose boilerplates from library/compose directory."""
            # Get the library/compose path
            library_path = Path(__file__).parent.parent.parent.parent / "library" / "compose"
            
            # Define the compose file names to search for
            compose_filenames = ["compose.yaml", "docker-compose.yaml", "compose.yml", "docker-compose.yml"]
            
            # Find all boilerplates
            bps = find_boilerplates(library_path, compose_filenames)
            
            if not bps:
                console = Console()
                console.print("[yellow]No compose boilerplates found.[/yellow]")
                return
            
            # Create a rich table
            console = Console()
            table = Table(title="🐳 Available Compose Boilerplates", title_style="bold blue")
            
            table.add_column("Name", style="cyan", no_wrap=True)
            table.add_column("Module", style="magenta")
            table.add_column("Path", style="green")
            table.add_column("Size", justify="right", style="yellow")
            table.add_column("Description", style="dim")
            
            for bp in bps:
                # Format file size
                if bp.size < 1024:
                    size_str = f"{bp.size} B"
                elif bp.size < 1024 * 1024:
                    size_str = f"{bp.size // 1024} KB"
                else:
                    size_str = f"{bp.size // (1024 * 1024)} MB"
                
                table.add_row(
                    bp.name,
                    bp.module,
                    str(bp.file_path.relative_to(library_path)),
                    size_str,
                    bp.description[:50] + "..." if len(bp.description) > 50 else bp.description
                )
            
            console.print(table)

        @app.command("show", help="Show details about a compose boilerplate")
        def show(name: str):
            pass

        @app.command("search", help="Search compose boilerplates")
        def search(query: str):
            pass
