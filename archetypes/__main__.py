#!/usr/bin/env python3
"""
Archetypes testing tool - for developing and testing template snippets.
Usage: python3 -m archetypes <module> <command>
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

from typer import Typer, Argument, Option
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Import CLI components
from cli.core.template import Template
from cli.core.collection import VariableCollection
from cli.core.display import DisplayManager
from cli.core.exceptions import (
    TemplateLoadError,
    TemplateSyntaxError,
    TemplateValidationError,
    TemplateRenderError,
)

app = Typer(
    help="Test and develop template snippets (archetypes) without full template structure.",
    add_completion=True,
    rich_markup_mode="rich",
)
console = Console()
display = DisplayManager()

# Base directory for archetypes
ARCHETYPES_DIR = Path(__file__).parent


def setup_logging(log_level: str = "WARNING") -> None:
    """Configure logging for debugging."""
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")
    
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


class ArchetypeTemplate:
    """Simplified template for testing individual .j2 files."""
    
    def __init__(self, file_path: Path, module_name: str):
        self.file_path = file_path
        self.module_name = module_name
        self.id = file_path.stem  # Filename without extension
        self.template_dir = file_path.parent
        
        # Create a minimal template.yaml in memory
        self.metadata = type('obj', (object,), {
            'name': f"Archetype: {self.id}",
            'description': f"Testing archetype from {file_path.name}",
            'version': "0.1.0",
            'author': "Testing",
            'library': "archetype",
            'tags': ["archetype", "test"],
        })()
        
        # Parse spec from module if available
        self.variables = self._load_module_spec()
    
    def _load_module_spec(self) -> Optional[VariableCollection]:
        """Load variable spec from the module and merge with extension.yaml if present."""
        try:
            # Import the module to get its spec
            if self.module_name == "compose":
                from cli.modules.compose import spec
                from collections import OrderedDict
                import yaml
                
                # Convert spec to dict if needed
                if isinstance(spec, (dict, OrderedDict)):
                    spec_dict = OrderedDict(spec)
                elif isinstance(spec, VariableCollection):
                    # Extract dict from existing VariableCollection (shouldn't happen)
                    spec_dict = OrderedDict()
                else:
                    logging.warning(f"Spec for {self.module_name} has unexpected type: {type(spec)}")
                    return None
                
                # Check for extension.yaml in the archetype directory
                extension_file = self.template_dir / "extension.yaml"
                if extension_file.exists():
                    try:
                        with open(extension_file, 'r') as f:
                            extension_vars = yaml.safe_load(f)
                        
                        if extension_vars:
                            # Apply extension defaults to existing variables in their sections
                            # Extension vars that don't exist will be added to a "testing" section
                            applied_count = 0
                            new_vars = {}
                            
                            for var_name, var_spec in extension_vars.items():
                                found = False
                                # Search for the variable in existing sections
                                for section_name, section_data in spec_dict.items():
                                    if "vars" in section_data and var_name in section_data["vars"]:
                                        # Update the default value for existing variable
                                        if "default" in var_spec:
                                            section_data["vars"][var_name]["default"] = var_spec["default"]
                                            applied_count += 1
                                            found = True
                                            break
                                
                                # If variable doesn't exist in spec, add it to testing section
                                if not found:
                                    new_vars[var_name] = var_spec
                            
                            # Add new test-only variables to testing section
                            if new_vars:
                                if "testing" not in spec_dict:
                                    spec_dict["testing"] = {
                                        "title": "Testing Variables",
                                        "description": "Additional variables for archetype testing",
                                        "vars": {}
                                    }
                                spec_dict["testing"]["vars"].update(new_vars)
                            
                            logging.debug(f"Applied {applied_count} extension defaults, added {len(new_vars)} new test variables from {extension_file}")
                    except Exception as e:
                        logging.warning(f"Failed to load extension.yaml: {e}")
                
                return VariableCollection(spec_dict)
        except Exception as e:
            logging.warning(f"Could not load spec for module {self.module_name}: {e}")
            return None
    
    def render(self, variables: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """Render the single .j2 file using CLI's Template class."""
        # Create a minimal template directory structure in memory
        # by using the Template class's rendering capabilities
        from jinja2 import Environment, FileSystemLoader, StrictUndefined
        
        # Set up Jinja2 environment with the archetype directory
        env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )
        
        # Get variable values
        if variables is None:
            variables = {}
        
        # Get default values from spec if available
        if self.variables:
            # Get ALL variable values, not just satisfied ones
            # This is needed for archetype testing where we want full template context
            # Include None values so templates can properly handle optional variables
            spec_values = {}
            for section_name, section in self.variables._sections.items():
                for var_name, var in section.variables.items():
                    # Include ALL variables, even if value is None
                    # This allows Jinja2 templates to handle optional variables properly
                    spec_values[var_name] = var.value
            # Merge: CLI variables override spec defaults
            final_values = {**spec_values, **variables}
        else:
            final_values = variables
        
        try:
            # Load and render the template
            template = env.get_template(self.file_path.name)
            rendered_content = template.render(**final_values)
            
            # Remove .j2 extension for output filename
            output_filename = self.file_path.name.replace('.j2', '')
            
            return {output_filename: rendered_content}
        except Exception as e:
            raise TemplateRenderError(f"Failed to render {self.file_path.name}: {e}")


def find_archetypes(module_name: str) -> List[Path]:
    """Find all .j2 files in the module's archetype directory."""
    module_dir = ARCHETYPES_DIR / module_name
    
    if not module_dir.exists():
        console.print(f"[red]Module directory not found: {module_dir}[/red]")
        return []
    
    # Find all .j2 files
    j2_files = list(module_dir.glob("*.j2"))
    return sorted(j2_files)


def create_module_commands(module_name: str) -> Typer:
    """Create a Typer app with commands for a specific module."""
    module_app = Typer(help=f"Manage {module_name} archetypes")
    
    @module_app.command()
    def list() -> None:
        """List all archetype files for this module."""
        archetypes = find_archetypes(module_name)
        
        if not archetypes:
            display.display_warning(
                f"No archetypes found for module '{module_name}'",
                context=f"directory: {ARCHETYPES_DIR / module_name}"
            )
            return
        
        # Create table
        table = Table(title=f"Archetypes for '{module_name}'", show_header=True, header_style="bold cyan")
        table.add_column("ID", style="cyan")
        table.add_column("Filename", style="white")
        table.add_column("Size", style="dim")
        
        for archetype_path in archetypes:
            file_size = archetype_path.stat().st_size
            if file_size < 1024:
                size_str = f"{file_size}B"
            else:
                size_str = f"{file_size / 1024:.1f}KB"
            
            table.add_row(
                archetype_path.stem,
                archetype_path.name,
                size_str,
            )
        
        console.print(table)
        console.print(f"\n[dim]Found {len(archetypes)} archetype(s)[/dim]")
    
    @module_app.command()
    def show(
        id: str = Argument(..., help="Archetype ID (filename without .j2)"),
    ) -> None:
        """Show details of an archetype file."""
        archetypes = find_archetypes(module_name)
        
        # Find the archetype
        archetype_path = None
        for path in archetypes:
            if path.stem == id:
                archetype_path = path
                break
        
        if not archetype_path:
            display.display_error(
                f"Archetype '{id}' not found",
                context=f"module '{module_name}'"
            )
            return
        
        # Load archetype
        archetype = ArchetypeTemplate(archetype_path, module_name)
        
        # Display details
        console.print()
        console.print(Panel(
            f"[bold]{archetype.metadata.name}[/bold]\n"
            f"{archetype.metadata.description}\n\n"
            f"[dim]Module:[/dim] {module_name}\n"
            f"[dim]File:[/dim] {archetype_path.name}\n"
            f"[dim]Path:[/dim] {archetype_path}",
            title="Archetype Details",
            border_style="cyan",
        ))
        
        # Show variables if spec is loaded
        if archetype.variables:
            console.print("\n[bold]Available Variables:[/bold]")
            
            # Access the private _sections attribute
            for section_name, section in archetype.variables._sections.items():
                if section.variables:
                    console.print(f"\n[cyan]{section.title or section_name.capitalize()}:[/cyan]")
                    for var_name, var in section.variables.items():
                        default = var.value if var.value is not None else "[dim]none[/dim]"
                        console.print(f"  {var_name}: {default}")
        else:
            console.print("\n[yellow]No variable spec loaded for this module[/yellow]")
        
        # Show file content
        console.print("\n[bold]Template Content:[/bold]")
        console.print("─" * 80)
        with open(archetype_path, 'r') as f:
            console.print(f.read())
        console.print()
    
    @module_app.command()
    def generate(
        id: str = Argument(..., help="Archetype ID (filename without .j2)"),
        directory: Optional[str] = Argument(
            None, help="Output directory (for reference only - no files are written)"
        ),
        var: Optional[List[str]] = Option(
            None,
            "--var",
            "-v",
            help="Variable override (KEY=VALUE format)",
        ),
    ) -> None:
        """Generate output from an archetype file (always in preview mode)."""
        # Archetypes ALWAYS run in dry-run mode with content display
        # This is a testing tool - it never writes actual files
        dry_run = True
        show_content = True
        
        archetypes = find_archetypes(module_name)
        
        # Find the archetype
        archetype_path = None
        for path in archetypes:
            if path.stem == id:
                archetype_path = path
                break
        
        if not archetype_path:
            display.display_error(
                f"Archetype '{id}' not found",
                context=f"module '{module_name}'"
            )
            return
        
        # Load archetype
        archetype = ArchetypeTemplate(archetype_path, module_name)
        
        # Parse variable overrides
        variables = {}
        if var:
            for var_option in var:
                if "=" in var_option:
                    key, value = var_option.split("=", 1)
                    variables[key] = value
                else:
                    console.print(f"[yellow]Warning: Invalid --var format '{var_option}' (use KEY=VALUE)[/yellow]")
        
        # Render the archetype
        try:
            rendered_files = archetype.render(variables)
        except Exception as e:
            display.display_error(
                f"Failed to render archetype: {e}",
                context=f"archetype '{id}'"
            )
            return
        
        # Determine output directory (for display purposes only)
        if directory:
            output_dir = Path(directory)
        else:
            output_dir = Path.cwd()
        
        # Always show preview (archetypes never write files)
        console.print()
        console.print("[bold cyan]Archetype Preview (Testing Mode)[/bold cyan]")
        console.print("[dim]This tool never writes files - it's for testing template snippets only[/dim]")
        console.print()
        console.print(f"[dim]Reference directory:[/dim] {output_dir}")
        console.print(f"[dim]Files to preview:[/dim] {len(rendered_files)}")
        console.print()
        
        for filename, content in rendered_files.items():
            full_path = output_dir / filename
            status = "Would overwrite" if full_path.exists() else "Would create"
            size = len(content.encode('utf-8'))
            console.print(f"  [{status}] {filename} ({size} bytes)")
        
        console.print()
        console.print("[bold]Rendered Content:[/bold]")
        console.print("─" * 80)
        for filename, content in rendered_files.items():
            console.print(content)
        
        console.print()
        display.display_success("Preview complete - no files were written")
    
    return module_app


def init_app() -> None:
    """Initialize the application by discovering modules and registering commands."""
    # Find all module directories in archetypes/
    if ARCHETYPES_DIR.exists():
        for module_dir in ARCHETYPES_DIR.iterdir():
            if module_dir.is_dir() and not module_dir.name.startswith(('_', '.')):
                module_name = module_dir.name
                # Register module commands
                module_app = create_module_commands(module_name)
                app.add_typer(module_app, name=module_name)


@app.callback(invoke_without_command=True)
def main(
    log_level: Optional[str] = Option(
        None,
        "--log-level",
        help="Set logging level (DEBUG, INFO, WARNING, ERROR)",
    ),
) -> None:
    """Archetypes testing tool for template snippet development."""
    if log_level:
        setup_logging(log_level)
    else:
        logging.disable(logging.CRITICAL)
    
    import click
    ctx = click.get_current_context()
    
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        sys.exit(0)


if __name__ == "__main__":
    try:
        init_app()
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)
