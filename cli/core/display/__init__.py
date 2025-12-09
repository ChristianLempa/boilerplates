"""Display module for CLI output rendering.

This package provides centralized display management with mixin-based architecture.
DisplayManager inherits from multiple mixins to provide a flat, cohesive API.
"""

from __future__ import annotations

from rich.console import Console

from .display_base import BaseDisplay
from .display_icons import IconManager
from .display_settings import DisplaySettings
from .display_status import StatusDisplay
from .display_table import TableDisplay
from .display_template import TemplateDisplay
from .display_variable import VariableDisplay

# Console instances for stdout and stderr
console = Console()
console_err = Console(stderr=True)


class DisplayManager:
    """Main display coordinator using composition.

    This class composes specialized display components to provide a unified API.
    Each component handles a specific concern (status, tables, templates, variables).

    Design Principles:
    - Composition over inheritance
    - Explicit dependencies
    - Clear separation of concerns
    - Easy to test and extend
    """

    def __init__(self, quiet: bool = False, settings: DisplaySettings | None = None):
        """Initialize DisplayManager with composed display components.

        Args:
            quiet: If True, suppress all non-error output
            settings: Optional DisplaySettings instance for customization
        """
        self.quiet = quiet
        self.settings = settings or DisplaySettings()

        # Create base display component (includes utilities)
        self.base = BaseDisplay(self.settings, quiet)

        # Create specialized display components
        self.status = StatusDisplay(self.settings, quiet, self.base)
        self.variables = VariableDisplay(self.settings, self.base)
        self.templates = TemplateDisplay(self.settings, self.base, self.variables, self.status)
        self.tables = TableDisplay(self.settings, self.base)

    # ===== Delegate to base display =====
    def text(self, text: str, style: str | None = None) -> None:
        """Display plain text."""
        return self.base.text(text, style)

    def heading(self, text: str, style: str | None = None) -> None:
        """Display a heading."""
        return self.base.heading(text, style)

    def section(self, title: str, description: str | None = None) -> None:
        """Display a section header with optional description.

        Args:
            title: Section title
            description: Optional section description
        """
        self.base.text("")
        self.base.text(f"[bold cyan]{title}[/bold cyan]")
        if description:
            self.base.text(f"[dim]{description}[/dim]")

    def table(
        self,
        headers: list[str] | None = None,
        rows: list[tuple] | None = None,
        title: str | None = None,
        show_header: bool = True,
        borderless: bool = False,
    ) -> None:
        """Display a table."""
        return self.base.table(headers, rows, title, show_header, borderless)

    def tree(self, root_label: str, nodes: dict | list) -> None:
        """Display a tree."""
        return self.base.tree(root_label, nodes)

    def code(self, code_text: str, language: str | None = None) -> None:
        """Display code."""
        return self.base.code(code_text, language)

    def progress(self, *columns):
        """Create a progress bar."""
        return self.base.progress(*columns)

    def file_tree(
        self,
        root_label: str,
        files: list,
        file_info_fn: callable,
        title: str | None = None,
    ) -> None:
        """Display a file tree structure."""
        return self.base.file_tree(root_label, files, file_info_fn, title)

    # ===== Formatting utilities =====
    def truncate(self, value: str, max_length: int | None = None) -> str:
        """Truncate string value."""
        return self.base.truncate(value, max_length)

    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        return self.base.format_file_size(size_bytes)

    def data_table(
        self,
        columns: list[dict],
        rows: list,
        title: str | None = None,
        row_formatter: callable | None = None,
    ) -> None:
        """Display a data table with configurable columns."""
        return self.tables.data_table(columns, rows, title, row_formatter)

    def display_status_table(
        self,
        title: str,
        rows: list[tuple[str, str, bool]],
        columns: tuple[str, str] = ("Item", "Status"),
    ) -> None:
        """Display a status table with success/error indicators."""
        return self.tables.render_status_table(title, rows, columns)

    # ===== Delegate to status display =====
    def error(self, message: str, context: str | None = None, details: str | None = None) -> None:
        """Display an error message."""
        return self.status.error(message, context, details)

    def warning(self, message: str, context: str | None = None, details: str | None = None) -> None:
        """Display a warning message."""
        return self.status.warning(message, context, details)

    def success(self, message: str, context: str | None = None) -> None:
        """Display a success message."""
        return self.status.success(message, context)

    def info(self, message: str, context: str | None = None) -> None:
        """Display an info message."""
        return self.status.info(message, context)

    def skipped(self, message: str, reason: str | None = None) -> None:
        """Display skipped message."""
        return self.status.skipped(message, reason)

    # ===== Helper methods =====
    def get_lock_icon(self) -> str:
        """Get lock icon."""
        return self.base.get_lock_icon()

    def print_table(self, table) -> None:
        """Print a pre-built Rich Table object.

        Args:
            table: Rich Table object to print
        """
        return self.base._print_table(table)


# Export public API
__all__ = [
    "DisplayManager",
    "DisplaySettings",
    "IconManager",
    "console",
    "console_err",
]
