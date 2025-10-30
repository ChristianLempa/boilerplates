from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from rich.table import Table
from rich.tree import Tree

from .icon_manager import IconManager

if TYPE_CHECKING:
    from . import DisplayManager

logger = logging.getLogger(__name__)


class TableDisplayManager:
    """Handles table rendering.

    This manager is responsible for displaying various types of tables
    including templates lists, status tables, and summaries.
    """

    def __init__(self, parent: DisplayManager):
        """Initialize TableDisplayManager.

        Args:
            parent: Reference to parent DisplayManager for accessing shared resources
        """
        self.parent = parent

    def render_templates_table(
        self, templates: list, module_name: str, title: str
    ) -> None:
        """Display a table of templates with library type indicators.

        Args:
            templates: List of Template objects
            module_name: Name of the module
            title: Title for the table
        """
        if not templates:
            logger.info(f"No templates found for module '{module_name}'")
            return

        logger.info(f"Listing {len(templates)} templates for module '{module_name}'")
        table = Table()
        table.add_column("ID", style="bold", no_wrap=True)
        table.add_column("Name")
        table.add_column("Tags")
        table.add_column("Version", no_wrap=True)
        table.add_column("Schema", no_wrap=True)
        table.add_column("Library", no_wrap=True)

        settings = self.parent.settings

        for template in templates:
            name = template.metadata.name or settings.TEXT_UNNAMED_TEMPLATE
            tags_list = template.metadata.tags or []
            tags = ", ".join(tags_list) if tags_list else "-"
            version = (
                str(template.metadata.version) if template.metadata.version else ""
            )
            schema = (
                template.schema_version
                if hasattr(template, "schema_version")
                else "1.0"
            )

            # Use helper for library display
            library_name = template.metadata.library or ""
            library_type = template.metadata.library_type or "git"
            library_display = self.parent._format_library_display(
                library_name, library_type
            )

            table.add_row(template.id, name, tags, version, schema, library_display)

        self.parent._print_table(table)

    def render_status_table(
        self,
        title: str,
        rows: list[tuple[str, str, bool]],
        columns: tuple[str, str] = ("Item", "Status"),
    ) -> None:
        """Display a status table with success/error indicators.

        Args:
            title: Table title
            rows: List of tuples (name, message, success_bool)
            columns: Column headers (name_header, status_header)
        """
        table = Table(show_header=True)
        table.add_column(columns[0], style="cyan", no_wrap=True)
        table.add_column(columns[1])

        for name, message, success in rows:
            status_style = "green" if success else "red"
            status_icon = IconManager.get_status_icon("success" if success else "error")
            table.add_row(
                name, f"[{status_style}]{status_icon} {message}[/{status_style}]"
            )

        self.parent._print_table(table)

    def render_summary_table(self, title: str, items: dict[str, str]) -> None:
        """Display a simple two-column summary table.

        Args:
            title: Table title
            items: Dictionary of key-value pairs to display
        """
        settings = self.parent.settings
        table = Table(
            title=title,
            show_header=False,
            box=None,
            padding=settings.PADDING_TABLE_NORMAL,
        )
        table.add_column(style="bold")
        table.add_column()

        for key, value in items.items():
            table.add_row(key, value)

        self.parent._print_table(table)

    def render_file_operation_table(self, files: list[tuple[str, int, str]]) -> None:
        """Display a table of file operations with sizes and statuses.

        Args:
            files: List of tuples (file_path, size_bytes, status)
        """
        settings = self.parent.settings
        table = Table(
            show_header=True,
            header_style=settings.STYLE_TABLE_HEADER,
            box=None,
            padding=settings.PADDING_TABLE_COMPACT,
        )
        table.add_column("File", style="white", no_wrap=False)
        table.add_column("Size", justify="right", style=settings.COLOR_MUTED)
        table.add_column("Status", style=settings.COLOR_WARNING)

        for file_path, size_bytes, status in files:
            size_str = self.parent._format_file_size(size_bytes)
            table.add_row(str(file_path), size_str, status)

        self.parent._print_table(table)

    def _build_section_label(
        self,
        section_name: str,
        section_data: dict,
        show_all: bool,
    ) -> str:
        """Build section label with metadata."""
        section_desc = section_data.get("description", "")
        section_required = section_data.get("required", False)
        section_toggle = section_data.get("toggle")
        section_needs = section_data.get("needs")

        label = f"[cyan]{section_name}[/cyan]"
        if section_required:
            label += " [yellow](required)[/yellow]"
        if section_toggle:
            label += f" [dim](toggle: {section_toggle})[/dim]"
        if section_needs:
            needs_str = (
                ", ".join(section_needs)
                if isinstance(section_needs, list)
                else section_needs
            )
            label += f" [dim](needs: {needs_str})[/dim]"
        if show_all and section_desc:
            label += f"\n  [dim]{section_desc}[/dim]"

        return label

    def _build_variable_label(
        self,
        var_name: str,
        var_data: dict,
        show_all: bool,
    ) -> str:
        """Build variable label with type and default value."""
        var_type = var_data.get("type", "string")
        var_default = var_data.get("default", "")
        var_desc = var_data.get("description", "")
        var_sensitive = var_data.get("sensitive", False)

        label = f"[green]{var_name}[/green] [dim]({var_type})[/dim]"

        if var_default is not None and var_default != "":
            settings = self.parent.settings
            display_val = settings.SENSITIVE_MASK if var_sensitive else str(var_default)
            if not var_sensitive:
                display_val = self.parent._truncate_value(
                    display_val, settings.VALUE_MAX_LENGTH_DEFAULT
                )
            label += (
                f" = [{settings.COLOR_WARNING}]{display_val}[/{settings.COLOR_WARNING}]"
            )

        if show_all and var_desc:
            label += f"\n    [dim]{var_desc}[/dim]"

        return label

    def _add_section_variables(
        self, section_node, section_vars: dict, show_all: bool
    ) -> None:
        """Add variables to a section node."""
        for var_name, var_data in section_vars.items():
            if isinstance(var_data, dict):
                var_label = self._build_variable_label(var_name, var_data, show_all)
                section_node.add(var_label)
            else:
                # Simple key-value pair
                section_node.add(
                    f"[green]{var_name}[/green] = [yellow]{var_data}[/yellow]"
                )

    def render_config_tree(
        self, spec: dict, module_name: str, show_all: bool = False
    ) -> None:
        """Display configuration spec as a tree view.

        Args:
            spec: The configuration spec dictionary
            module_name: Name of the module
            show_all: If True, show all details including descriptions
        """
        if not spec:
            self.parent.text(
                f"No configuration found for module '{module_name}'", style="yellow"
            )
            return

        # Create root tree node
        tree = Tree(
            f"[bold blue]{IconManager.config()} {str.capitalize(module_name)} Configuration[/bold blue]"
        )

        for section_name, section_data in spec.items():
            if not isinstance(section_data, dict):
                continue

            # Build and add section
            section_label = self._build_section_label(
                section_name, section_data, show_all
            )
            section_node = tree.add(section_label)

            # Add variables to section
            section_vars = section_data.get("vars") or {}
            if section_vars:
                self._add_section_variables(section_node, section_vars, show_all)

        self.parent._print_tree(tree)
