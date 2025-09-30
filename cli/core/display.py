from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.table import Table
from rich.tree import Tree

if TYPE_CHECKING:
    from .template import Template

logger = logging.getLogger(__name__)
console = Console()


class DisplayManager:
    """Handles all rich rendering for the CLI."""

    def display_templates_table(
        self, templates: list[dict], module_name: str, title: str
    ) -> None:
        """Display a table of templates."""
        if not templates:
            logger.info(f"No templates found for module '{module_name}'")
            return

        logger.info(f"Listing {len(templates)} templates for module '{module_name}'")
        table = Table(title=title)
        table.add_column("ID", style="bold", no_wrap=True)
        table.add_column("Name")
        table.add_column("Description")
        table.add_column("Version", no_wrap=True)
        table.add_column("Library", no_wrap=True)

        for template_info in templates:
            template = template_info["template"]
            indent = template_info["indent"]
            name = template.metadata.name or "Unnamed Template"
            desc = template.metadata.description or "No description available"
            version = template.metadata.version or ""
            library = template.metadata.library or ""

            template_id = f"{indent}{template.id}"
            table.add_row(template_id, name, desc, version, library)

        console.print(table)

    def display_template_details(self, template: Template, template_id: str) -> None:
        """Display template information panel and variables table."""
        self._display_template_header(template, template_id)
        self._display_file_tree(template)
        self._display_variables_table(template)

    def display_section_header(self, title: str, description: str | None) -> None:
        """Display a section header."""
        console.print(f"\n[bold cyan]{title}[/bold cyan]")
        if description:
            console.print(f"[dim]{description}[/dim]")
        console.print("─" * 40, style="dim")

    def display_validation_error(self, message: str) -> None:
        """Display a validation error message."""
        console.print(f"[red]{message}[/red]")

    def _display_template_header(self, template: Template, template_id: str) -> None:
        """Display the header for a template."""
        template_name = template.metadata.name or "Unnamed Template"
        version = template.metadata.version or "Not specified"
        description = template.metadata.description or "No description available"

        console.print(
            f"[bold blue]{template_name} ({template_id} - [cyan]{version}[/cyan])[/bold blue]"
        )
        console.print(description)

    def _display_file_tree(self, template: Template) -> None:
        """Display the file structure of a template."""
        file_tree = Tree("[bold blue]Template File Structure:[/bold blue]")
        tree_nodes = {Path("."): file_tree}

        for template_file in sorted(
            template.template_files, key=lambda f: f.relative_path
        ):
            parts = template_file.relative_path.parts
            current_path = Path(".")
            current_node = file_tree

            for part in parts[:-1]:
                current_path = current_path / part
                if current_path not in tree_nodes:
                    new_node = current_node.add(f"uf07b [bold blue]{part}[/bold blue]")
                    tree_nodes[current_path] = new_node
                    current_node = new_node
                else:
                    current_node = tree_nodes[current_path]

            if template_file.file_type == "j2":
                current_node.add(
                    f"[green]ue235 {template_file.relative_path.name}[/green]"
                )
            elif template_file.file_type == "static":
                current_node.add(
                    f"[yellow]uf15b {template_file.relative_path.name}[/yellow]"
                )

        if file_tree.children:
            console.print()
            console.print(file_tree)

    def _display_variables_table(self, template: Template) -> None:
        """Display a table of variables for a template."""
        if not (template.variables and template.variables.has_sections()):
            return

        console.print()
        console.print("[bold blue]Template Variables:[/bold blue]")

        variables_table = Table(show_header=True, header_style="bold blue")
        variables_table.add_column("Variable", style="cyan", no_wrap=True)
        variables_table.add_column("Type", style="magenta")
        variables_table.add_column("Default", style="green")
        variables_table.add_column("Description", style="white")
        variables_table.add_column("Origin", style="yellow")

        first_section = True
        for section in template.variables.get_sections().values():
            if not section.variables:
                continue

            if not first_section:
                variables_table.add_row("", "", "", "", "", style="dim")
            first_section = False

            is_dimmed = False
            if section.toggle:
                toggle_var = section.variables.get(section.toggle)
                if toggle_var and not toggle_var.get_typed_value():
                    is_dimmed = True

            disabled_text = " (disabled)" if is_dimmed else ""
            required_text = " [yellow](required)[/yellow]" if section.required else ""
            header_text = f"[bold dim]{section.title}{required_text}{disabled_text}[/bold dim]" if is_dimmed else f"[bold]{section.title}{required_text}{disabled_text}[/bold]"
            variables_table.add_row(header_text, "", "", "", "")

            for var_name, variable in section.variables.items():
                row_style = "dim" if is_dimmed else None
                default_val = str(variable.value) if variable.value is not None else ""
                if variable.sensitive:
                    default_val = "********"
                elif len(default_val) > 30:
                    default_val = default_val[:27] + "..."

                variables_table.add_row(
                    f"  {var_name}",
                    variable.type or "str",
                    default_val,
                    variable.description or "",
                    variable.origin or "unknown",
                    style=row_style,
                )

        console.print(variables_table)
