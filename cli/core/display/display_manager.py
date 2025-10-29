"""Main display coordinator for the CLI."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.tree import Tree

from .display_settings import DisplaySettings
from .icon_manager import IconManager
from .variable_display import VariableDisplayManager
from .template_display import TemplateDisplayManager
from .status_display import StatusDisplayManager
from .table_display import TableDisplayManager

if TYPE_CHECKING:
    from ..exceptions import TemplateRenderError
    from ..template import Template

logger = logging.getLogger(__name__)
console = Console()


class DisplayManager:
    """Main display coordinator with shared resources.

    This class acts as a facade that delegates to specialized display managers.
    External code should use DisplayManager methods which provide backward
    compatibility while internally using the specialized managers.

    Design Principles:
    - All display logic should go through DisplayManager methods
    - IconManager is ONLY used internally by display managers
    - External code should never directly call IconManager or console.print
    - Consistent formatting across all display types
    """

    def __init__(self, quiet: bool = False, settings: DisplaySettings | None = None):
        """Initialize DisplayManager with specialized sub-managers.

        Args:
            quiet: If True, suppress all non-error output
            settings: Optional DisplaySettings instance for customization
        """
        self.quiet = quiet
        self.settings = settings or DisplaySettings()

        # Initialize specialized managers
        self.variables = VariableDisplayManager(self)
        self.templates = TemplateDisplayManager(self)
        self.status = StatusDisplayManager(self)
        self.tables = TableDisplayManager(self)

    # ===== Shared Helper Methods =====

    def _format_library_display(self, library_name: str, library_type: str) -> str:
        """Format library name with appropriate icon and color.

        Args:
            library_name: Name of the library
            library_type: Type of library ('static' or 'git')

        Returns:
            Formatted library display string with Rich markup
        """
        if library_type == "static":
            color = self.settings.COLOR_LIBRARY_STATIC
            icon = IconManager.UI_LIBRARY_STATIC
        else:
            color = self.settings.COLOR_LIBRARY_GIT
            icon = IconManager.UI_LIBRARY_GIT

        return f"[{color}]{icon} {library_name}[/{color}]"

    def _truncate_value(self, value: str, max_length: int | None = None) -> str:
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
            return (
                value[: max_length - len(self.settings.TRUNCATION_SUFFIX)]
                + self.settings.TRUNCATION_SUFFIX
            )
        return value

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format (B, KB, MB).

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted size string (e.g., "1.5KB", "2.3MB")
        """
        if size_bytes < self.settings.SIZE_KB_THRESHOLD:
            return f"{size_bytes}B"
        elif size_bytes < self.settings.SIZE_MB_THRESHOLD:
            kb = size_bytes / self.settings.SIZE_KB_THRESHOLD
            return f"{kb:.{self.settings.SIZE_DECIMAL_PLACES}f}KB"
        else:
            mb = size_bytes / self.settings.SIZE_MB_THRESHOLD
            return f"{mb:.{self.settings.SIZE_DECIMAL_PLACES}f}MB"

    # ===== Backward Compatibility Delegation Methods =====
    # These methods delegate to specialized managers for backward compatibility

    def display_templates_table(
        self, templates: list, module_name: str, title: str
    ) -> None:
        """Delegate to TableDisplayManager."""
        return self.tables.render_templates_table(templates, module_name, title)

    def display_template(self, template: "Template", template_id: str) -> None:
        """Delegate to TemplateDisplayManager."""
        return self.templates.render_template(template, template_id)

    def display_section(self, title: str, description: str | None) -> None:
        """Delegate to VariableDisplayManager."""
        return self.variables.render_section(title, description)

    def display_validation_error(self, message: str) -> None:
        """Delegate to StatusDisplayManager."""
        return self.status.display_validation_error(message)

    def display_message(
        self, level: str, message: str, context: str | None = None
    ) -> None:
        """Delegate to StatusDisplayManager."""
        return self.status.display_message(level, message, context)

    def display_error(self, message: str, context: str | None = None) -> None:
        """Delegate to StatusDisplayManager."""
        return self.status.display_error(message, context)

    def display_warning(self, message: str, context: str | None = None) -> None:
        """Delegate to StatusDisplayManager."""
        return self.status.display_warning(message, context)

    def display_success(self, message: str, context: str | None = None) -> None:
        """Delegate to StatusDisplayManager."""
        return self.status.display_success(message, context)

    def display_info(self, message: str, context: str | None = None) -> None:
        """Delegate to StatusDisplayManager."""
        return self.status.display_info(message, context)

    def display_version_incompatibility(
        self, template_id: str, required_version: str, current_version: str
    ) -> None:
        """Delegate to StatusDisplayManager."""
        return self.status.display_version_incompatibility(
            template_id, required_version, current_version
        )

    def display_file_generation_confirmation(
        self,
        output_dir: Path,
        files: dict[str, str],
        existing_files: list[Path] | None = None,
    ) -> None:
        """Delegate to TemplateDisplayManager."""
        return self.templates.render_file_generation_confirmation(
            output_dir, files, existing_files
        )

    def display_config_tree(
        self, spec: dict, module_name: str, show_all: bool = False
    ) -> None:
        """Delegate to TableDisplayManager."""
        return self.tables.render_config_tree(spec, module_name, show_all)

    def display_status_table(
        self,
        title: str,
        rows: list[tuple[str, str, bool]],
        columns: tuple[str, str] = ("Item", "Status"),
    ) -> None:
        """Delegate to TableDisplayManager."""
        return self.tables.render_status_table(title, rows, columns)

    def display_summary_table(self, title: str, items: dict[str, str]) -> None:
        """Delegate to TableDisplayManager."""
        return self.tables.render_summary_table(title, items)

    def display_file_operation_table(self, files: list[tuple[str, int, str]]) -> None:
        """Delegate to TableDisplayManager."""
        return self.tables.render_file_operation_table(files)

    def display_warning_with_confirmation(
        self, message: str, details: list[str] | None = None, default: bool = False
    ) -> bool:
        """Delegate to StatusDisplayManager."""
        return self.status.display_warning_with_confirmation(message, details, default)

    def display_skipped(self, message: str, reason: str | None = None) -> None:
        """Delegate to StatusDisplayManager."""
        return self.status.display_skipped(message, reason)

    def display_template_render_error(
        self, error: "TemplateRenderError", context: str | None = None
    ) -> None:
        """Delegate to StatusDisplayManager."""
        return self.status.display_template_render_error(error, context)

    # ===== Internal Helper Methods =====

    def _render_file_tree_internal(
        self, root_label: str, files: list, get_file_info: callable
    ) -> Tree:
        """Render a file tree structure.

        Args:
            root_label: Label for root node
            files: List of files to display
            get_file_info: Function that takes a file and returns (path, display_name, color, extra_text)

        Returns:
            Tree object ready for display
        """
        file_tree = Tree(root_label)
        tree_nodes = {Path("."): file_tree}

        for file_item in sorted(files, key=lambda f: get_file_info(f)[0]):
            path, display_name, color, extra_text = get_file_info(file_item)
            parts = path.parts
            current_path = Path(".")
            current_node = file_tree

            # Build directory structure
            for part in parts[:-1]:
                current_path = current_path / part
                if current_path not in tree_nodes:
                    new_node = current_node.add(
                        f"{IconManager.folder()} [white]{part}[/white]"
                    )
                    tree_nodes[current_path] = new_node
                current_node = tree_nodes[current_path]

            # Add file
            icon = IconManager.get_file_icon(display_name)
            file_label = f"{icon} [{color}]{display_name}[/{color}]"
            if extra_text:
                file_label += f" {extra_text}"
            current_node.add(file_label)

        return file_tree

    # ===== Additional Methods =====

    def display_heading(
        self, text: str, icon_type: str | None = None, style: str = "bold"
    ) -> None:
        """Display a heading with optional icon.

        Args:
            text: Heading text
            icon_type: Type of icon to display (e.g., 'folder', 'file', 'config')
            style: Rich style to apply
        """
        if icon_type:
            icon = self._get_icon_by_type(icon_type)
            console.print(f"[{style}]{icon} {text}[/{style}]")
        else:
            console.print(f"[{style}]{text}[/{style}]")

    def get_lock_icon(self) -> str:
        """Get the lock icon for sensitive variables.

        Returns:
            Lock icon unicode character
        """
        return IconManager.lock()

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

    def display_next_steps(self, next_steps: str, variable_values: dict) -> None:
        """Display next steps after template generation, rendering them as a Jinja2 template.

        Args:
            next_steps: The next_steps string from template metadata (may contain Jinja2 syntax)
            variable_values: Dictionary of variable values to use for rendering
        """
        if not next_steps:
            return

        console.print("\n[bold cyan]Next Steps:[/bold cyan]")

        try:
            from jinja2 import Template as Jinja2Template

            next_steps_template = Jinja2Template(next_steps)
            rendered_next_steps = next_steps_template.render(variable_values)
            console.print(rendered_next_steps)
        except Exception as e:
            logger.warning(f"Failed to render next_steps as template: {e}")
            # Fallback to plain text if rendering fails
            console.print(next_steps)
