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
        self, templates: list, module_name: str, title: str
    ) -> None:
        """Display a table of templates.
        
        Args:
            templates: List of Template objects
            module_name: Name of the module
            title: Title for the table
        """
        if not templates:
            logger.info(f"No templates found for module '{module_name}'")
            return

        logger.info(f"Listing {len(templates)} templates for module '{module_name}'")
        table = Table(title=title)
        table.add_column("ID", style="bold", no_wrap=True)
        table.add_column("Name")
        table.add_column("Tags")
        table.add_column("Version", no_wrap=True)
        table.add_column("Library", no_wrap=True)

        for template in templates:
            name = template.metadata.name or "Unnamed Template"
            tags_list = template.metadata.tags or []
            tags = ", ".join(tags_list) if tags_list else "-"
            version = template.metadata.version or ""
            library = template.metadata.library or ""

            table.add_row(template.id, name, tags, version, library)

        console.print(table)

    def display_template_details(self, template: Template, template_id: str) -> None:
        """Display template information panel and variables table."""
        self._display_template_header(template, template_id)
        self._display_file_tree(template)
        self._display_variables_table(template)

    def display_section_header(self, title: str, description: str | None) -> None:
        """Display a section header."""
        if description:
            console.print(f"\n[bold cyan]{title}[/bold cyan] [dim]- {description}[/dim]")
        else:
            console.print(f"\n[bold cyan]{title}[/bold cyan]")
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
        # Preserve the heading, then use the template id as the root directory label
        console.print()
        console.print("[bold blue]Template File Structure:[/bold blue]")
        # Use the template id as the root directory label (folder glyph + white name)
        file_tree = Tree(f"\uf07b [white]{template.id}[/white]")
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
                    new_node = current_node.add(f"\uf07b [white]{part}[/white]")
                    tree_nodes[current_path] = new_node
                    current_node = new_node
                else:
                    current_node = tree_nodes[current_path]

            # Determine display name (use output_path to detect final filename)
            display_name = template_file.output_path.name if hasattr(template_file, 'output_path') else template_file.relative_path.name

            # Default icons: use Nerd Font private-use-area codepoints (PUA).
            # Docker (Font Awesome) is typically U+F308. Default file U+F15B.
            docker_icon = "\uf308"
            default_file_icon = "\uf15b"
            j2_icon = "\ue235"

            if template_file.file_type == "j2":
                # Detect common docker compose filenames from the resulting output path
                lower_name = display_name.lower()
                compose_names = {"docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"}
                if lower_name in compose_names or lower_name.startswith("docker-compose") or "compose" in lower_name:
                    icon = docker_icon
                else:
                    icon = j2_icon
                current_node.add(f"[white]{icon} {display_name}[/white]")
            elif template_file.file_type == "static":
                current_node.add(f"[white]{default_file_icon} {display_name}[/white]")

        if file_tree.children:
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

            # Use section's native is_enabled() method
            is_dimmed = not section.is_enabled()

            disabled_text = " (disabled)" if is_dimmed else ""
            required_text = " [yellow](required)[/yellow]" if section.required else ""
            header_text = f"[bold dim]{section.title}{required_text}{disabled_text}[/bold dim]" if is_dimmed else f"[bold]{section.title}{required_text}{disabled_text}[/bold]"
            variables_table.add_row(header_text, "", "", "", "")

            for var_name, variable in section.variables.items():
                row_style = "dim" if is_dimmed else None
                # Use variable's native get_display_value() method
                default_val = variable.get_display_value(mask_sensitive=True, max_length=30)
                
                # Add lock icon for sensitive variables
                sensitive_icon = " \uf084" if variable.sensitive else ""
                var_display = f"  {var_name}{sensitive_icon}"

                variables_table.add_row(
                    var_display,
                    variable.type or "str",
                    default_val,
                    variable.description or "",
                    variable.origin or "unknown",
                    style=row_style,
                )

        console.print(variables_table)

    def display_file_generation_confirmation(
        self, 
        output_dir: Path, 
        files: dict[str, str], 
        existing_files: list[Path] | None = None
    ) -> None:
        """Display files to be generated with confirmation prompt.
        
        Args:
            output_dir: The output directory path
            files: Dictionary of file paths to content
            existing_files: List of existing files that will be overwritten (if any)
        """
        console.print()
        console.print("[bold]Files to be generated:[/bold]")
        
        # Create a tree view of files
        file_tree = Tree(f"\uf07b [cyan]{output_dir.resolve()}[/cyan]")
        tree_nodes = {Path("."): file_tree}
        
        # Sort files for better display
        sorted_files = sorted(files.keys())
        
        for file_path_str in sorted_files:
            file_path = Path(file_path_str)
            parts = file_path.parts
            current_path = Path(".")
            current_node = file_tree
            
            # Build directory structure
            for part in parts[:-1]:
                current_path = current_path / part
                if current_path not in tree_nodes:
                    new_node = current_node.add(f"\uf07b [white]{part}[/white]")
                    tree_nodes[current_path] = new_node
                current_node = tree_nodes[current_path]
            
            # Add file with indicator if it will be overwritten
            file_name = parts[-1]
            full_path = output_dir / file_path
            
            if existing_files and full_path in existing_files:
                current_node.add(f"\uf15c [yellow]{file_name}[/yellow] [red](will overwrite)[/red]")
            else:
                current_node.add(f"\uf15c [green]{file_name}[/green]")
        
        console.print(file_tree)
        console.print()

    def display_config_tree(self, spec: dict, module_name: str, show_all: bool = False) -> None:
        """Display configuration spec as a tree view.
        
        Args:
            spec: The configuration spec dictionary
            module_name: Name of the module
            show_all: If True, show all details including descriptions
        """
        if not spec:
            console.print(f"[yellow]No configuration found for module '{module_name}'[/yellow]")
            return

        # Create root tree node
        tree = Tree(f"[bold blue]\ue5fc {str.capitalize(module_name)} Configuration[/bold blue]")

        for section_name, section_data in spec.items():
            if not isinstance(section_data, dict):
                continue

            # Determine if this is a section with variables
            # Guard against None from empty YAML sections
            section_vars = section_data.get("vars") or {}
            section_desc = section_data.get("description", "")
            section_required = section_data.get("required", False)
            section_toggle = section_data.get("toggle", None)

            # Build section label
            section_label = f"[cyan]{section_name}[/cyan]"
            if section_required:
                section_label += " [yellow](required)[/yellow]"
            if section_toggle:
                section_label += f" [dim](toggle: {section_toggle})[/dim]"
            
            if show_all and section_desc:
                section_label += f"\n  [dim]{section_desc}[/dim]"

            section_node = tree.add(section_label)

            # Add variables
            if section_vars:
                for var_name, var_data in section_vars.items():
                    if isinstance(var_data, dict):
                        var_type = var_data.get("type", "string")
                        var_default = var_data.get("default", "")
                        var_desc = var_data.get("description", "")
                        var_sensitive = var_data.get("sensitive", False)

                        # Build variable label
                        var_label = f"[green]{var_name}[/green] [dim]({var_type})[/dim]"
                        
                        if var_default is not None and var_default != "":
                            display_val = "********" if var_sensitive else str(var_default)
                            if not var_sensitive and len(display_val) > 30:
                                display_val = display_val[:27] + "..."
                            var_label += f" = [yellow]{display_val}[/yellow]"
                        
                        if show_all and var_desc:
                            var_label += f"\n    [dim]{var_desc}[/dim]"
                        
                        section_node.add(var_label)
                    else:
                        # Simple key-value pair
                        section_node.add(f"[green]{var_name}[/green] = [yellow]{var_data}[/yellow]")

        console.print(tree)
