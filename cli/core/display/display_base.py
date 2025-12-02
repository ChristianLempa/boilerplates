"""Base display methods for DisplayManager."""

from __future__ import annotations

import logging
from pathlib import Path

from rich.console import Console
from rich.progress import Progress
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree

from .display_icons import IconManager
from .display_settings import DisplaySettings

logger = logging.getLogger(__name__)
console = Console()


class BaseDisplay:
    """Base display methods and utilities.

    Provides fundamental display methods (text, heading, table, tree, code, progress)
    and utility/helper methods for formatting.
    """

    def __init__(self, settings: DisplaySettings, quiet: bool = False):
        """Initialize BaseDisplay.

        Args:
            settings: Display settings for formatting
            quiet: If True, suppress non-error output
        """
        self.settings = settings
        self.quiet = quiet

    def heading(self, text: str, style: str | None = None) -> None:
        """Display a standardized heading.

        Args:
            text: Heading text
            style: Optional style override (defaults to STYLE_HEADER from settings)
        """
        if style is None:
            style = self.settings.STYLE_HEADER
        console.print(f"[{style}]{text}[/{style}]")
        console.print("")  # Add newline after heading

    def text(self, text: str, style: str | None = None) -> None:
        """Display plain text with optional styling.

        Args:
            text: Text to display
            style: Optional Rich style markup
        """
        if style:
            console.print(f"[{style}]{text}[/{style}]")
        else:
            console.print(text)

    def table(
        self,
        headers: list[str] | None = None,
        rows: list[tuple] | None = None,
        title: str | None = None,
        show_header: bool = True,
        borderless: bool = False,
    ) -> None:
        """Display a standardized table.

        Args:
            headers: Column headers (if None, no headers)
            rows: List of tuples, one per row
            title: Optional table title
            show_header: Whether to show header row
            borderless: If True, use borderless style (box=None)
        """
        table = Table(
            title=title,
            show_header=show_header and headers is not None,
            header_style=self.settings.STYLE_TABLE_HEADER,
            box=None,
            padding=self.settings.PADDING_TABLE_NORMAL if borderless else (0, 1),
        )

        # Add columns
        if headers:
            for header in headers:
                table.add_column(header)
        elif rows and len(rows) > 0:
            # No headers, but need columns for data
            for _ in range(len(rows[0])):
                table.add_column()

        # Add rows
        if rows:
            for row in rows:
                table.add_row(*[str(cell) for cell in row])

        console.print(table)

    def tree(self, root_label: str, nodes: dict | list | Tree) -> None:
        """Display a tree structure.

        Args:
            root_label: Label for the root node
            nodes: Hierarchical structure (dict, list, or pre-built Tree)
        """
        if isinstance(nodes, Tree):
            console.print(nodes)
        else:
            tree = Tree(root_label)
            self._build_tree_nodes(tree, nodes)
            console.print(tree)

    def _build_tree_nodes(self, parent, nodes):
        """Recursively build tree nodes.

        Args:
            parent: Parent tree node
            nodes: Dict or list of child nodes
        """
        if isinstance(nodes, dict):
            for key, value in nodes.items():
                if isinstance(value, (dict, list)):
                    branch = parent.add(str(key))
                    self._build_tree_nodes(branch, value)
                else:
                    parent.add(f"{key}: {value}")
        elif isinstance(nodes, list):
            for item in nodes:
                if isinstance(item, (dict, list)):
                    self._build_tree_nodes(parent, item)
                else:
                    parent.add(str(item))

    def _print_tree(self, tree) -> None:
        """Print a pre-built Rich Tree object.

        Args:
            tree: Rich Tree object to print
        """
        console.print(tree)

    def _print_table(self, table) -> None:
        """Print a pre-built Rich Table object.

        Enforces consistent header styling for all tables.

        Args:
            table: Rich Table object to print
        """
        # Enforce consistent header style for all tables
        table.header_style = self.settings.STYLE_TABLE_HEADER
        console.print(table)

    def _print_markdown(self, markdown) -> None:
        """Print a pre-built Rich Markdown object.

        Args:
            markdown: Rich Markdown object to print
        """
        console.print(markdown)

    def code(self, code_text: str, language: str | None = None) -> None:
        """Display code with optional syntax highlighting.

        Args:
            code_text: Code to display
            language: Programming language for syntax highlighting
        """
        if language:
            syntax = Syntax(code_text, language, theme="monokai", line_numbers=False)
            console.print(syntax)
        else:
            # Plain code block without highlighting
            console.print(f"[dim]{code_text}[/dim]")

    def progress(self, *columns):
        """Create a Rich Progress context manager with standardized console.

        Args:
            *columns: Progress columns (e.g., SpinnerColumn(), TextColumn())

        Returns:
            Progress context manager

        Example:
            with display.progress(
                SpinnerColumn(), TextColumn("[progress.description]{task.description}")
            ) as progress:
                task = progress.add_task("Processing...", total=None)
                # do work
                progress.remove_task(task)
        """
        return Progress(*columns, console=console)

    # ===== Formatting Utilities =====

    def truncate(self, value: str, max_length: int | None = None) -> str:
        """Truncate a string value if it exceeds maximum length.

        Args:
            value: String value to truncate
            max_length: Maximum length (uses default if None)

        Returns:
            Truncated string with suffix if needed
        """
        if max_length is None:
            max_length = self.settings.VALUE_MAX_LENGTH_DEFAULT

        if max_length > 0 and len(value) > max_length:
            return value[: max_length - len(self.settings.TRUNCATION_SUFFIX)] + self.settings.TRUNCATION_SUFFIX
        return value

    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format (B, KB, MB).

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted size string (e.g., "1.5KB", "2.3MB")
        """
        if size_bytes < self.settings.SIZE_KB_THRESHOLD:
            return f"{size_bytes}B"
        if size_bytes < self.settings.SIZE_MB_THRESHOLD:
            kb = size_bytes / self.settings.SIZE_KB_THRESHOLD
            return f"{kb:.{self.settings.SIZE_DECIMAL_PLACES}f}KB"
        mb = size_bytes / self.settings.SIZE_MB_THRESHOLD
        return f"{mb:.{self.settings.SIZE_DECIMAL_PLACES}f}MB"

    def file_tree(
        self,
        root_label: str,
        files: list,
        file_info_fn: callable,
        title: str | None = None,
    ) -> None:
        """Display a file tree structure.

        Args:
            root_label: Label for root node (e.g., "📁 my-project")
            files: List of file items to display
            file_info_fn: Function that takes a file and returns
                         (path, display_name, color, extra_text) where:
                         - path: Path object for directory structure
                         - display_name: Name to show for the file
                         - color: Rich color for the filename
                         - extra_text: Optional additional text
            title: Optional heading to display before tree
        """
        if title:
            self.heading(title)

        tree = Tree(root_label)
        tree_nodes = {Path(): tree}

        for file_item in sorted(files, key=lambda f: file_info_fn(f)[0]):
            path, display_name, color, extra_text = file_info_fn(file_item)
            parts = path.parts
            current_path = Path()
            current_node = tree

            # Build directory structure
            for part in parts[:-1]:
                current_path = current_path / part
                if current_path not in tree_nodes:
                    new_node = current_node.add(f"{IconManager.folder()} [white]{part}[/white]")
                    tree_nodes[current_path] = new_node
                current_node = tree_nodes[current_path]

            # Add file
            icon = IconManager.get_file_icon(display_name)
            file_label = f"{icon} [{color}]{display_name}[/{color}]"
            if extra_text:
                file_label += f" {extra_text}"
            current_node.add(file_label)

        console.print(tree)

    def _get_icon_by_type(self, icon_type: str) -> str:
        """Get icon by semantic type name.

        Args:
            icon_type: Type of icon (e.g., 'folder', 'file', 'config', 'lock')

        Returns:
            Icon unicode character
        """
        icon_map = {
            "folder": IconManager.folder(),
            "file": IconManager.FILE_DEFAULT,
            "config": IconManager.config(),
            "lock": IconManager.lock(),
            "arrow": IconManager.arrow_right(),
        }
        return icon_map.get(icon_type, "")

    def get_lock_icon(self) -> str:
        """Get the lock icon for sensitive variables.

        Returns:
            Lock icon unicode character
        """
        return IconManager.lock()
