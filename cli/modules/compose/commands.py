"""
Compose module commands and functionality.
Manage Compose configurations and services and template operations.
"""

import re
import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from typing import List, Optional, Set, Dict, Any

from ...core.command import BaseModule
from ...core.helpers import find_boilerplates
from .variables import ComposeVariables


class ComposeModule(BaseModule):
    """Module for managing compose boilerplates."""

    compose_filenames = ["compose.yaml", "docker-compose.yaml", "compose.yml", "docker-compose.yml"]
    _library_path = Path(__file__).parent.parent.parent.parent / "library" / "compose"

    def __init__(self):
        super().__init__(name="compose", icon="🐳", description="Manage Compose Templates and Configurations")

    # Core BaseModule integration
    @property
    def template_paths(self) -> List[str]:
        # Prefer compose.yaml as default per project rules
        return self.compose_filenames

    @property
    def library_path(self) -> Path:
        return self._library_path

    @property
    def variable_handler_class(self):
        return ComposeVariables
    
    def _get_variable_details(self) -> Dict[str, Dict[str, Any]]:
        """Get detailed information about variables for display."""
        variables = ComposeVariables()
        details = {}
        for var_name, (set_name, var_meta) in variables._declared.items():
            details[var_name] = {
                'set': set_name,
                'type': var_meta.get('type', 'str'),
                'display_name': var_meta.get('display_name', var_name),
                'default': var_meta.get('default'),
                'prompt': var_meta.get('prompt', '')
            }
        return details

    def _add_custom_commands(self, app: typer.Typer) -> None:
        """Add compose-specific commands to the app."""

        @app.command("list", help="List all compose boilerplates")
        def list():
            """List all compose boilerplates from library/compose directory."""
            bps = find_boilerplates(self.library_path, self.compose_filenames)
            if not bps:
                self.console.print("[yellow]No compose boilerplates found.[/yellow]")
                return
            table = Table(title="🐳 Available Compose Boilerplates", title_style="bold blue")
            table.add_column("Name", style="cyan", no_wrap=True)
            table.add_column("Module", style="magenta")
            table.add_column("Path", style="green")
            table.add_column("Size", justify="right", style="yellow")
            table.add_column("Description", style="dim")
            for bp in bps:
                if bp.size < 1024:
                    size_str = f"{bp.size} B"
                elif bp.size < 1024 * 1024:
                    size_str = f"{bp.size // 1024} KB"
                else:
                    size_str = f"{bp.size // (1024 * 1024)} MB"
                table.add_row(
                    bp.name,
                    bp.module,
                    str(bp.file_path.relative_to(self.library_path)),
                    size_str,
                    bp.description[:50] + "..." if len(bp.description) > 50 else bp.description
                )
            self.console.print(table)

        @app.command("show", help="Show details about a compose boilerplate")
        def show(name: str, raw: bool = typer.Option(False, "--raw", help="Output only the raw boilerplate content")):
            """Show details about a compose boilerplate by name."""
            bps = find_boilerplates(self.library_path, self.compose_filenames)
            # Match by directory name (parent folder of the compose file) instead of frontmatter 'name'
            bp = next((b for b in bps if b.file_path.parent.name.lower() == name.lower()), None)
            if not bp:
                self.console.print(f"[red]Boilerplate '{name}' not found.[/red]")
                return
            if raw:
                # Output only the raw boilerplate content
                print(bp.content)
                return
            # Print frontmatter info in a clean, readable format
            from rich.text import Text
            from rich.console import Group
            
            info = bp.to_dict()
            
            # Create a clean header
            header = Text()
            header.append("🐳 Boilerplate: ", style="bold")
            header.append(f"{info['name']}", style="bold blue")
            header.append(f" ({info['version']})", style="magenta")
            header.append("\n", style="bold")
            header.append(f"{info['description']}", style="dim white")
            
            # Create metadata section with clean formatting
            metadata = Text()
            metadata.append("\nDetails:\n", style="bold cyan")
            metadata.append("─" * 40 + "\n", style="dim cyan")
            
            # Format each field with consistent styling
            fields = [
                ("Tags", ", ".join(info['tags']), "cyan"),
                ("Author", info['author'], "dim white"), 
                ("Date", info['date'], "dim white"),
                ("Size", info['size'], "dim white"),
                ("Path", info['path'], "dim white")
            ]
            
            for label, value, color in fields:
                metadata.append(f"{label}: ")
                metadata.append(f"{value}\n", style=color)
            
            # Handle files list if present
            if info['files'] and len(info['files']) > 0:
                metadata.append("  Files: ")
                files_str = ", ".join(info['files'][:3])  # Show first 3
                if len(info['files']) > 3:
                    files_str += f" ... and {len(info['files']) - 3} more"
                metadata.append(f"{files_str}\n", style="green")
            
            # Display everything as a group
            display_group = Group(header, metadata)
            self.console.print(display_group)


            # Show the content of the boilerplate file in a cleaner form
            from rich.panel import Panel
            from rich.syntax import Syntax

            # Detect if content contains Jinja2 templating
            has_jinja = bool(re.search(r'\{\{.*\}\}|\{\%.*\%\}|\{\#.*\#\}', bp.content))
            
            # Use appropriate lexer based on content
            # Use yaml+jinja for combined YAML and Jinja2 highlighting when Jinja2 is present
            lexer = "yaml+jinja" if has_jinja else "yaml"
            syntax = Syntax(bp.content, lexer, theme="monokai", line_numbers=True, word_wrap=True)
            panel = Panel(syntax, title=f"{bp.file_path.name}", border_style="blue", padding=(1,2))
            self.console.print(panel)

        @app.command("search", help="Search compose boilerplates")
        def search(query: str):
            pass

        @app.command("generate", help="Generate a compose file from a boilerplate and write to --out")
        def generate(
            name: str, 
            out: Optional[Path] = typer.Option(None, "--out", "-o", help="Output path to write rendered boilerplate (prints to stdout when omitted)"),
            values_file: Optional[Path] = typer.Option(None, "--values-file", "-f", help="Load values from YAML/JSON file"),
            cli_values: Optional[List[str]] = typer.Option(None, "--values", help="Set values (format: key=value)")
        ):
            """Render a compose boilerplate interactively and write output to --out."""
            from ...core import template, values as values_mod, render
            from ...core.config import ConfigManager

            # Find and validate boilerplate
            bps = find_boilerplates(self.library_path, self.compose_filenames)
            bp = next((b for b in bps if b.file_path.parent.name.lower() == name.lower()), None)
            if not bp:
                self.console.print(f"[red]Boilerplate '{name}' not found.[/red]")
                raise typer.Exit(code=1)

            # Clean template content and find variables
            cv = ComposeVariables()
            cleaned_content = template.clean_template_content(bp.content)
            matched_sets, used_vars = cv.determine_variable_sets(cleaned_content)

            # If no variables used, return original content
            if not used_vars:
                rendered = bp.content
            else:
                # Validate template syntax
                is_valid, error = template.validate_template(cleaned_content, bp.file_path)
                if not is_valid:
                    self.console.print(f"[red]{error}[/red]")
                    raise typer.Exit(code=2)

                # Extract defaults and variable metadata
                template_defaults = cv.extract_template_defaults(cleaned_content)
                try:
                    meta_overrides = cv.extract_variable_meta_overrides(bp.content)
                    # Merge overrides into declared metadata
                    for var_name, overrides in meta_overrides.items():
                        if var_name in cv._declared and isinstance(overrides, dict):
                            existing = cv._declared[var_name][1]
                            existing.update(overrides)
                except Exception:
                    meta_overrides = {}

                # Get subscript keys and load values from all sources
                used_subscripts = cv.find_used_subscript_keys(bp.content)
                config_manager = ConfigManager(self.name)
                try:
                    merged_values = values_mod.load_and_merge_values(
                        values_file=values_file,
                        cli_values=cli_values,
                        config_values=config_manager.list_all(),
                        defaults=template_defaults
                    )
                except Exception as e:
                    self.console.print(f"[red]{str(e)}[/red]")
                    raise typer.Exit(code=1)

                # Collect final values and render template
                values_dict = cv.collect_values(used_vars, merged_values, used_subscripts)
                success, rendered, error = template.render_template(
                    cleaned_content,
                    values_dict
                )

                if not success:
                    self.console.print(f"[red]{error}[/red]")
                    raise typer.Exit(code=2)

            # Output the rendered content
            output_handler = render.RenderOutput(self.console)
            output_handler.output_rendered_content(
                rendered,
                out,
                "yaml",
                bp.name
            )
