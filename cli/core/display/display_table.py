from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from rich.table import Table
from rich.tree import Tree

from .display_icons import IconManager
from .display_settings import DisplaySettings

if TYPE_CHECKING:
    from .display_base import BaseDisplay

logger = logging.getLogger(__name__)


class TableDisplay:
    """Table rendering.

    Provides methods for displaying data tables with flexible formatting.
    """

    def __init__(self, settings: DisplaySettings, base: BaseDisplay):
        """Initialize TableDisplay.

        Args:
            settings: Display settings for formatting
            base: BaseDisplay instance for utility methods
        """
        self.settings = settings
        self.base = base

    def data_table(
        self,
        columns: list[dict],
        rows: list,
        title: str | None = None,
        row_formatter: callable | None = None,
    ) -> None:
        """Display a data table with configurable columns and formatting.

        Args:
            columns: List of column definitions, each dict with:
                     - name: Column header text
                     - style: Optional Rich style (e.g., "bold", "cyan")
                     - no_wrap: Optional bool to prevent text wrapping
                     - justify: Optional justify ("left", "right", "center")
            rows: List of data rows (dicts, tuples, or objects)
            title: Optional table title
            row_formatter: Optional function(row) -> tuple to transform row data
        """
        table = Table(title=title, show_header=True)

        # Add columns
        for col in columns:
            table.add_column(
                col["name"],
                style=col.get("style"),
                no_wrap=col.get("no_wrap", False),
                justify=col.get("justify", "left"),
            )

        # Add rows
        for row in rows:
            if row_formatter:
                formatted_row = row_formatter(row)
            elif isinstance(row, dict):
                formatted_row = tuple(str(row.get(col["name"], "")) for col in columns)
            else:
                formatted_row = tuple(str(cell) for cell in row)

            table.add_row(*formatted_row)

        self.base._print_table(table)

    def render_templates_table(self, templates: list, module_name: str, _title: str) -> None:
        """Display a table of templates with library type indicators.

        Args:
            templates: List of Template objects
            module_name: Name of the module
            _title: Title for the table (unused, kept for API compatibility)
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
        table.add_column("Library", no_wrap=True)

        settings = self.settings

        for template in templates:
            name = template.metadata.name or settings.TEXT_UNNAMED_TEMPLATE
            tags_list = template.metadata.tags or []
            tags = ", ".join(tags_list) if tags_list else "-"
            version = str(template.metadata.version) if template.metadata.version else ""

            # Format library with icon and color
            library_name = template.metadata.library or ""
            library_type = template.metadata.library_type or "git"
            icon = IconManager.UI_LIBRARY_STATIC if library_type == "static" else IconManager.UI_LIBRARY_GIT
            color = "yellow" if library_type == "static" else "blue"
            library_display = f"[{color}]{icon} {library_name}[/{color}]"

            table.add_row(template.id, name, tags, version, library_display)

        self.base._print_table(table)

    def render_status_table(
        self,
        _title: str,
        rows: list[tuple[str, str, bool]],
        columns: tuple[str, str] = ("Item", "Status"),
    ) -> None:
        """Display a status table with success/error indicators.

        Args:
            _title: Table title (unused, kept for API compatibility)
            rows: List of tuples (name, message, success_bool)
            columns: Column headers (name_header, status_header)
        """
        table = Table(show_header=True)
        table.add_column(columns[0], style="cyan", no_wrap=True)
        table.add_column(columns[1])

        for name, message, success in rows:
            status_style = "green" if success else "red"
            status_icon = IconManager.get_status_icon("success" if success else "error")
            table.add_row(name, f"[{status_style}]{status_icon} {message}[/{status_style}]")

        self.base._print_table(table)

    def render_summary_table(self, title: str, items: dict[str, str]) -> None:
        """Display a simple two-column summary table.

        Args:
            title: Table title
            items: Dictionary of key-value pairs to display
        """
        settings = self.settings
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

        self.base._print_table(table)

    def render_file_operation_table(self, files: list[tuple[str, int, str]]) -> None:
        """Display a table of file operations with sizes and statuses.

        Args:
            files: List of tuples (file_path, size_bytes, status)
        """
        settings = self.settings
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
            size_str = self.base.format_file_size(size_bytes)
            table.add_row(str(file_path), size_str, status)

        self.base._print_table(table)

    def _build_section_label(
        self,
        section_name: str,
        section_data: dict,
        show_all: bool,
    ) -> str:
        """Build section label with metadata."""
        section_desc = section_data.get("description", "")
        section_toggle = section_data.get("toggle")
        section_needs = section_data.get("needs")

        label = f"[cyan]{section_name}[/cyan]"
        if section_toggle:
            label += f" [dim](toggle: {section_toggle})[/dim]"
        if section_needs:
            needs_str = ", ".join(section_needs) if isinstance(section_needs, list) else section_needs
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
            settings = self.settings
            display_val = settings.SENSITIVE_MASK if var_sensitive else str(var_default)
            if not var_sensitive:
                display_val = self.base.truncate(display_val, settings.VALUE_MAX_LENGTH_DEFAULT)
            label += f" = [{settings.COLOR_WARNING}]{display_val}[/{settings.COLOR_WARNING}]"

        if show_all and var_desc:
            label += f"\n    [dim]{var_desc}[/dim]"

        return label

    def _add_section_variables(self, section_node, section_vars: dict, show_all: bool) -> None:
        """Add variables to a section node."""
        for var_name, var_data in section_vars.items():
            if isinstance(var_data, dict):
                var_label = self._build_variable_label(var_name, var_data, show_all)
                section_node.add(var_label)
            else:
                # Simple key-value pair
                section_node.add(f"[green]{var_name}[/green] = [yellow]{var_data}[/yellow]")

    def render_config_tree(self, spec: dict, module_name: str, show_all: bool = False) -> None:
        """Display configuration spec as a tree view.

        Args:
            spec: The configuration spec dictionary
            module_name: Name of the module
            show_all: If True, show all details including descriptions
        """
        if not spec:
            self.base.text(f"No configuration found for module '{module_name}'", style="yellow")
            return

        # Create root tree node
        icon = IconManager.config()
        tree = Tree(f"[bold blue]{icon} {str.capitalize(module_name)} Configuration[/bold blue]")

        for section_name, section_data in spec.items():
            if not isinstance(section_data, dict):
                continue

            # Build and add section
            section_label = self._build_section_label(section_name, section_data, show_all)
            section_node = tree.add(section_label)

            # Add variables to section
            section_vars = section_data.get("vars") or {}
            if section_vars:
                self._add_section_variables(section_node, section_vars, show_all)

        self.base._print_tree(tree)
