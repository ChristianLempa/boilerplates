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
    library_path = Path(__file__).parent.parent.parent.parent / "library" / "compose"

    def __init__(self):
        super().__init__(name="compose", icon="🐳", description="Manage Compose Templates and Configurations")

    def get_valid_variables(self) -> Set[str]:
        """Get the set of valid variable names for the compose module."""
        variables = ComposeVariables()
        return set(variables._declared.keys())
    
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

    def _add_module_commands(self, app: typer.Typer) -> None:
        """Add Module-specific commands to the app."""

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
            values: Optional[List[str]] = typer.Option(None, "--values", help="Set values (format: key=value)")
        ):
            """Render a compose boilerplate interactively and write output to --out."""
            bps = find_boilerplates(self.library_path, self.compose_filenames)
            # Match by directory name (parent folder of the compose file) instead of frontmatter 'name'
            bp = next((b for b in bps if b.file_path.parent.name.lower() == name.lower()), None)
            if not bp:
                self.console.print(f"[red]Boilerplate '{name}' not found.[/red]")
                raise typer.Exit(code=1)

            cv = ComposeVariables()
            # Remove any in-template `{% variables %} ... {% endvariables %}` block
            # before asking Jinja2 to parse/render the template. This block is
            # used only to provide metadata overrides and is not valid Jinja2
            # syntax for the default parser (unknown tag -> TemplateSyntaxError).
            import re
            cleaned_content = re.sub(r"\{%\s*variables\s*%\}(.+?)\{%\s*endvariables\s*%\}\n?", "", bp.content, flags=re.S)
            matched_sets, used_vars = cv.determine_variable_sets(cleaned_content)

            # If there are no detected variable sets but there are used vars, we still
            # need to prompt for the used variables. Lazy-import jinja2 only when
            # rendering is required so module import doesn't fail when Jinja2 is missing.
            if not used_vars:
                rendered = bp.content
            else:
                try:
                    import jinja2
                except Exception:
                    typer.secho("Jinja2 is required to render templates. Install it and retry.", fg=typer.colors.RED)
                    raise typer.Exit(code=2)

                # Use the cleaned content for defaults and rendering, but extract
                # overrides from the original content (which may contain the
                # variables block).
                template_defaults = cv.extract_template_defaults(cleaned_content)

                # Validate Jinja2 template syntax before proceeding. Parsing the
                # template will surface syntax errors (unclosed blocks, invalid
                # tags, etc.) early and allow us to abort with a helpful message.
                try:
                    env_for_validation = jinja2.Environment(loader=jinja2.BaseLoader())
                    env_for_validation.parse(cleaned_content)
                except jinja2.exceptions.TemplateSyntaxError as e:
                    # Show file path (if available) and error details, then exit.
                    self.console.print(f"[red]Template syntax error in '{bp.file_path}': {e.message} (line {e.lineno})[/red]")
                    raise typer.Exit(code=2)
                except Exception as e:
                    # Generic parse failure
                    self.console.print(f"[red]Failed to parse template '{bp.file_path}': {e}[/red]")
                    raise typer.Exit(code=2)
                # Extract variable metadata overrides from a {% variables %} block
                try:
                    meta_overrides = cv.extract_variable_meta_overrides(bp.content)
                    # Merge overrides into declared metadata so PromptHandler will pick them up
                    for var_name, overrides in meta_overrides.items():
                        if var_name in cv._declared and isinstance(overrides, dict):
                            existing = cv._declared[var_name][1]
                            # shallow merge
                            existing.update(overrides)
                except Exception:
                    meta_overrides = {}
                used_subscripts = cv.find_used_subscript_keys(bp.content)
                
                # Load values from file if specified
                file_values = {}
                if values_file:
                    if not values_file.exists():
                        self.console.print(f"[red]Values file '{values_file}' not found.[/red]")
                        raise typer.Exit(code=1)
                    
                    try:
                        import yaml
                        with open(values_file, 'r', encoding='utf-8') as f:
                            if values_file.suffix.lower() in ['.yaml', '.yml']:
                                file_values = yaml.safe_load(f) or {}
                            elif values_file.suffix.lower() == '.json':
                                import json
                                file_values = json.load(f)
                            else:
                                self.console.print(f"[red]Unsupported file format '{values_file.suffix}'. Use .yaml, .yml, or .json[/red]")
                                raise typer.Exit(code=1)
                        self.console.print(f"[dim]Loaded values from {values_file}[/dim]")
                    except Exception as e:
                        self.console.print(f"[red]Failed to load values from {values_file}: {e}[/red]")
                        raise typer.Exit(code=1)
                
                # Parse command-line values
                cli_values = {}
                if values:
                    for value_pair in values:
                        if '=' not in value_pair:
                            self.console.print(f"[red]Invalid value format '{value_pair}'. Use key=value format.[/red]")
                            raise typer.Exit(code=1)
                        key, val = value_pair.split('=', 1)
                        # Try to parse as JSON for complex values
                        try:
                            import json
                            cli_values[key] = json.loads(val)
                        except json.JSONDecodeError:
                            cli_values[key] = val
                        except Exception:
                            cli_values[key] = val
                
                # Override template defaults with configured values
                from ...core.config import ConfigManager
                config_manager = ConfigManager(self.name)
                config_values = config_manager.list_all()
                
                # Merge values in order of precedence: template defaults <- config <- file <- CLI
                for key, config_value in config_values.items():
                    template_defaults[key] = config_value
                
                for key, file_value in file_values.items():
                    template_defaults[key] = file_value
                
                for key, cli_value in cli_values.items():
                    template_defaults[key] = cli_value
                
                values_dict = cv.collect_values(used_vars, template_defaults, used_subscripts)

                # Enable Jinja2 whitespace control so that block tags like
                # {% if %} don't leave an extra newline in the rendered result.
                env = jinja2.Environment(loader=jinja2.BaseLoader(), trim_blocks=True, lstrip_blocks=True)
                try:
                    template = env.from_string(cleaned_content)
                except jinja2.exceptions.TemplateSyntaxError as e:
                    self.console.print(f"[red]Template syntax error in '{bp.file_path}': {e.message} (line {e.lineno})[/red]")
                    raise typer.Exit(code=2)
                except Exception as e:
                    self.console.print(f"[red]Failed to compile template '{bp.file_path}': {e}[/red]")
                    raise typer.Exit(code=2)

                try:
                    rendered = template.render(**values_dict)
                except jinja2.exceptions.TemplateError as e:
                    # Catch runtime/template errors (undefined variables, etc.)
                    self.console.print(f"[red]Template rendering error for '{bp.file_path}': {e}[/red]")
                    raise typer.Exit(code=2)
                except Exception as e:
                    self.console.print(f"[red]Unexpected error while rendering '{bp.file_path}': {e}[/red]")
                    raise typer.Exit(code=2)

            # If --out not provided, print to console; else write to file

            if out is None:
                # Print a subtle rule and a small header, then the highlighted YAML
                self.console.print(f"\n\nGenerated Boilerplate for [bold cyan]{bp.name}[/bold cyan]\n")
                syntax = Syntax(rendered, "yaml", theme="monokai", line_numbers=False, word_wrap=True)
                self.console.print(syntax)

            else:
                # Ensure parent directory exists
                out_parent = out.parent
                if not out_parent.exists():
                    out_parent.mkdir(parents=True, exist_ok=True)

                out.write_text(rendered, encoding="utf-8")
                self.console.print(f"[green]Rendered boilerplate written to {out}[/green]")
