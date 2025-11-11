#!/usr/bin/env python3
"""
Archetypes testing tool - for developing and testing template snippets.
Usage: python3 -m archetypes <module> <command>
"""

from __future__ import annotations

import builtins
import importlib
import logging
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any

import click
import yaml

# Add parent directory to Python path for CLI imports
# This allows archetypes to import from cli module when run as `python3 -m archetypes`
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

# Import CLI components
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from typer import Argument, Option, Typer

from cli.core.display import DisplayManager
from cli.core.exceptions import (
    TemplateRenderError,
)
from cli.core.module.helpers import parse_var_inputs
from cli.core.template.variable_collection import VariableCollection

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
        self.metadata = type(
            "obj",
            (object,),
            {
                "name": f"Archetype: {self.id}",
                "description": f"Testing archetype from {file_path.name}",
                "version": "0.1.0",
                "author": "Testing",
                "library": "archetype",
                "tags": ["archetype", "test"],
            },
        )()

        # Parse spec from module if available
        self.variables = self._load_module_spec()

    def _load_module_spec(self) -> VariableCollection | None:
        """Load variable spec from module and merge with archetypes.yaml if present."""
        try:
            # Load archetype config to get schema version
            archetype_config = self._load_archetype_config()
            schema_version = archetype_config.get("schema", "1.0") if archetype_config else "1.0"

            # Import module spec with correct schema
            spec = self._import_module_spec(schema_version)
            if spec is None:
                return None

            spec_dict = self._convert_spec_to_dict(spec)
            if spec_dict is None:
                return None

            # Merge variables from archetypes.yaml
            if archetype_config and "vars" in archetype_config:
                self._merge_archetype_vars(spec_dict, archetype_config["vars"])

            return VariableCollection(spec_dict)
        except Exception as e:
            logging.warning(f"Could not load spec for module {self.module_name}: {e}")
            return None

    def _load_archetype_config(self) -> dict | None:
        """Load archetypes.yaml configuration file."""
        config_file = self.template_dir / "archetypes.yaml"
        if not config_file.exists():
            return None

        try:
            with config_file.open() as f:
                return yaml.safe_load(f)
        except Exception as e:
            logging.warning(f"Failed to load archetypes.yaml: {e}")
            return None

    def _import_module_spec(self, schema_version: str) -> Any | None:
        """Import module spec for the specified schema version."""
        module_path = f"cli.modules.{self.module_name}"
        try:
            module = importlib.import_module(module_path)

            # Try to get schema-specific spec if module supports it
            if hasattr(module, "SCHEMAS") and schema_version in module.SCHEMAS:
                spec = module.SCHEMAS[schema_version]
                logging.debug(f"Using schema {schema_version} for module {self.module_name}")
            else:
                # Fall back to default spec
                spec = getattr(module, "spec", None)

            if spec is None:
                logging.warning(f"Module {self.module_name} has no 'spec' attribute")
            return spec
        except (ImportError, AttributeError) as e:
            logging.warning(f"Could not load spec from {module_path}: {e}")
            return None

    def _convert_spec_to_dict(self, spec: Any) -> OrderedDict | None:
        """Convert spec to OrderedDict."""
        if isinstance(spec, (dict, OrderedDict)):
            return OrderedDict(spec)
        if isinstance(spec, VariableCollection):
            # Extract dict from existing VariableCollection (shouldn't happen)
            return OrderedDict()
        logging.warning(f"Spec for {self.module_name} has unexpected type: {type(spec)}")
        return None

    def _merge_archetype_vars(self, spec_dict: OrderedDict, archetype_vars: dict) -> None:
        """Merge variables from archetypes.yaml into spec_dict."""
        try:
            applied_count, new_vars = self._apply_archetype_vars(spec_dict, archetype_vars)
            self._add_testing_section(spec_dict, new_vars)

            logging.debug(f"Applied {applied_count} archetype var overrides, added {len(new_vars)} new test variables")
        except Exception as e:
            logging.warning(f"Failed to merge archetype vars: {e}")

    def _apply_archetype_vars(self, spec_dict: OrderedDict, archetype_vars: dict) -> tuple[int, dict]:
        """Apply archetype variables to existing spec sections or collect as new variables."""
        applied_count = 0
        new_vars = {}

        for var_name, var_spec in archetype_vars.items():
            if self._update_existing_var(spec_dict, var_name, var_spec):
                applied_count += 1
            else:
                new_vars[var_name] = var_spec

        return applied_count, new_vars

    def _update_existing_var(self, spec_dict: OrderedDict, var_name: str, var_spec: dict) -> bool:
        """Update existing variable with extension default."""
        if "default" not in var_spec:
            return False

        for _section_name, section_data in spec_dict.items():
            if "vars" in section_data and var_name in section_data["vars"]:
                section_data["vars"][var_name]["default"] = var_spec["default"]
                return True
        return False

    def _add_testing_section(self, spec_dict: OrderedDict, new_vars: dict) -> None:
        """Add new variables to testing section."""
        if not new_vars:
            return

        if "testing" not in spec_dict:
            spec_dict["testing"] = {
                "title": "Testing Variables",
                "description": "Additional variables for archetype testing",
                "vars": {},
            }
        spec_dict["testing"]["vars"].update(new_vars)

    def render(self, variables: dict[str, Any] | None = None) -> dict[str, str]:
        """Render the single .j2 file using CLI's Template class."""
        # Create a minimal template directory structure in memory
        # by using the Template class's rendering capabilities
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
            for _section_name, section in self.variables._sections.items():
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
            output_filename = self.file_path.name.replace(".j2", "")

            return {output_filename: rendered_content}
        except Exception as e:
            raise TemplateRenderError(f"Failed to render {self.file_path.name}: {e}") from e


def find_archetypes(module_name: str) -> list[Path]:
    """Find all .j2 files in the module's archetype directory."""
    module_dir = ARCHETYPES_DIR / module_name

    if not module_dir.exists():
        console.print(f"[red]Module directory not found: {module_dir}[/red]")
        return []

    # Find all .j2 files
    j2_files = list(module_dir.glob("*.j2"))
    return sorted(j2_files)


def _find_archetype_by_id(archetypes: list[Path], id: str) -> Path | None:
    """Find an archetype file by its ID."""
    for path in archetypes:
        if path.stem == id:
            return path
    return None


def _create_list_table(module_name: str, archetypes: list[Path]) -> Table:
    """Create a table showing archetype files."""
    table = Table(
        title=f"Archetypes for '{module_name}'",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("ID", style="cyan")
    table.add_column("Filename", style="white")
    table.add_column("Size", style="dim")

    size_threshold = 1024
    for archetype_path in archetypes:
        file_size = archetype_path.stat().st_size
        size_str = f"{file_size}B" if file_size < size_threshold else f"{file_size / size_threshold:.1f}KB"
        table.add_row(archetype_path.stem, archetype_path.name, size_str)

    return table


def _display_archetype_details(archetype: ArchetypeTemplate, module_name: str) -> None:
    """Display archetype metadata and variables."""
    console.print()
    console.print(
        Panel(
            f"[bold]{archetype.metadata.name}[/bold]\n"
            f"{archetype.metadata.description}\n\n"
            f"[dim]Module:[/dim] {module_name}\n"
            f"[dim]File:[/dim] {archetype.file_path.name}\n"
            f"[dim]Path:[/dim] {archetype.file_path}",
            title="Archetype Details",
            border_style="cyan",
        )
    )

    if archetype.variables:
        console.print("\n[bold]Available Variables:[/bold]")
        for section_name, section in archetype.variables._sections.items():
            if section.variables:
                console.print(f"\n[cyan]{section.title or section_name.capitalize()}:[/cyan]")
                for var_name, var in section.variables.items():
                    default = var.value if var.value is not None else "[dim]none[/dim]"
                    console.print(f"  {var_name}: {default}")
    else:
        console.print("\n[yellow]No variable spec loaded for this module[/yellow]")


def _display_archetype_content(archetype_path: Path) -> None:
    """Display the archetype template file content."""
    console.print("\n[bold]Template Content:[/bold]")
    console.print("─" * 80)
    with archetype_path.open() as f:
        console.print(f.read())
    console.print()


def _parse_var_overrides(var: list[str] | None) -> dict[str, Any]:
    """Parse --var options into a dictionary with type conversion.

    Uses the CLI's parse_var_inputs function to ensure consistent behavior.
    """
    if not var:
        return {}

    # Use CLI's parse_var_inputs function (no extra_args for archetypes)
    return parse_var_inputs(var, [])


def _display_generated_preview(output_dir: Path, rendered_files: dict[str, str]) -> None:
    """Display the generated archetype preview."""
    console.print()
    console.print("[bold cyan]Archetype Preview (Testing Mode)[/bold cyan]")
    console.print("[dim]This tool never writes files - it's for testing template snippets only[/dim]")
    console.print(f"\n[dim]Reference directory:[/dim] {output_dir}\n")

    for filename, content in rendered_files.items():
        console.print(f"[bold cyan]{filename}[/bold cyan]")
        console.print("─" * 80)
        console.print(content)
        console.print()


def create_module_commands(module_name: str) -> Typer:
    """Create a Typer app with commands for a specific module."""
    module_app = Typer(help=f"Manage {module_name} archetypes")

    @module_app.command()
    def list() -> None:
        """List all archetype files for this module."""
        archetypes = find_archetypes(module_name)

        if not archetypes:
            display.warning(
                f"No archetypes found for module '{module_name}'",
                context=f"directory: {ARCHETYPES_DIR / module_name}",
            )
            return

        table = _create_list_table(module_name, archetypes)
        console.print(table)
        console.print(f"\n[dim]Found {len(archetypes)} archetype(s)[/dim]")

    @module_app.command()
    def show(
        id: str = Argument(..., help="Archetype ID (filename without .j2)"),
    ) -> None:
        """Show details of an archetype file."""
        archetypes = find_archetypes(module_name)
        archetype_path = _find_archetype_by_id(archetypes, id)

        if not archetype_path:
            display.error(f"Archetype '{id}' not found", context=f"module '{module_name}'")
            return

        _display_archetype_content(archetype_path)

    @module_app.command()
    def generate(
        id: str = Argument(..., help="Archetype ID (filename without .j2)"),
        directory: str | None = Argument(None, help="Output directory (for reference only - no files are written)"),
        var: builtins.list[str] | None = None,
    ) -> None:
        """Generate output from an archetype file (always in preview mode).

        Use --var/-v to set variables in KEY=VALUE format.
        """
        archetypes = find_archetypes(module_name)
        archetype_path = _find_archetype_by_id(archetypes, id)

        if not archetype_path:
            display.error(f"Archetype '{id}' not found", context=f"module '{module_name}'")
            return

        archetype = ArchetypeTemplate(archetype_path, module_name)
        variables = _parse_var_overrides(var)

        try:
            rendered_files = archetype.render(variables)
        except Exception as e:
            display.error(f"Failed to render archetype: {e}", context=f"archetype '{id}'")
            return

        output_dir = Path(directory) if directory else Path.cwd()
        _display_generated_preview(output_dir, rendered_files)
        display.success("Preview complete - no files were written")

    return module_app


def init_app() -> None:
    """Initialize the application by discovering modules and registering commands."""
    # Find all module directories in archetypes/
    if ARCHETYPES_DIR.exists():
        for module_dir in ARCHETYPES_DIR.iterdir():
            if module_dir.is_dir() and not module_dir.name.startswith(("_", ".")):
                module_name = module_dir.name
                # Register module commands
                module_app = create_module_commands(module_name)
                app.add_typer(module_app, name=module_name)


@app.callback(invoke_without_command=True)
def main(
    log_level: str | None = Option(
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
