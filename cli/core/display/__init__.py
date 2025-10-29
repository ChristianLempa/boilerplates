from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.tree import Tree

from .variable_display import VariableDisplayManager
from .template_display import TemplateDisplayManager
from .status_display import StatusDisplayManager
from .table_display import TableDisplayManager

if TYPE_CHECKING:
    from ..exceptions import TemplateRenderError
    from ..template import Template

logger = logging.getLogger(__name__)
console = Console()
console_err = Console(stderr=True)


class DisplaySettings:
    """Centralized display configuration settings.
    
    This class holds all configurable display parameters including colors,
    styles, layouts, and formatting options. Modify these values to customize
    the CLI appearance.
    """

    # === Color Scheme ===
    COLOR_ERROR = "red"
    COLOR_WARNING = "yellow"
    COLOR_SUCCESS = "green"
    COLOR_INFO = "blue"
    COLOR_MUTED = "dim"
    
    # Library type colors
    COLOR_LIBRARY_GIT = "blue"
    COLOR_LIBRARY_STATIC = "yellow"

    # === Style Constants ===
    STYLE_HEADER = "bold blue"
    STYLE_HEADER_ALT = "bold cyan"
    STYLE_DISABLED = "bright_black"
    STYLE_SECTION_TITLE = "bold cyan"
    STYLE_SECTION_DESC = "dim"
    
    # Table styles
    STYLE_TABLE_HEADER = "bold blue"
    STYLE_VAR_COL_NAME = "white"
    STYLE_VAR_COL_TYPE = "magenta"
    STYLE_VAR_COL_DEFAULT = "green"
    STYLE_VAR_COL_DESC = "white"

    # === Text Labels ===
    LABEL_REQUIRED = " [yellow](required)[/yellow]"
    LABEL_DISABLED = " (disabled)"
    TEXT_EMPTY_VALUE = "(none)"
    TEXT_EMPTY_OVERRIDE = "(empty)"
    TEXT_UNNAMED_TEMPLATE = "Unnamed Template"
    TEXT_NO_DESCRIPTION = "No description available"
    TEXT_VERSION_NOT_SPECIFIED = "Not specified"
    
    # === Value Formatting ===
    SENSITIVE_MASK = "********"
    TRUNCATION_SUFFIX = "..."
    VALUE_MAX_LENGTH_SHORT = 15
    VALUE_MAX_LENGTH_DEFAULT = 30
    
    # === Layout Constants ===
    SECTION_SEPARATOR_CHAR = "─"
    SECTION_SEPARATOR_LENGTH = 40
    VAR_NAME_INDENT = "  "  # 2 spaces
    
    # === Size Formatting ===
    SIZE_KB_THRESHOLD = 1024
    SIZE_MB_THRESHOLD = 1024 * 1024
    SIZE_DECIMAL_PLACES = 1
    
    # === Table Padding ===
    PADDING_PANEL = (1, 2)
    PADDING_TABLE_COMPACT = (0, 1)
    PADDING_TABLE_NORMAL = (0, 2)


class IconManager:
    """Centralized icon management system for consistent CLI display.

    This class provides standardized icons for file types, status indicators,
    and UI elements. Icons use Nerd Font glyphs for consistent display.

    Categories:
        - File types: .yaml, .j2, .json, .md, etc.
        - Status: success, warning, error, info, skipped
        - UI elements: folders, config, locks, etc.
    """

    # File Type Icons
    FILE_FOLDER = "\uf07b"  #
    FILE_DEFAULT = "\uf15b"  #
    FILE_YAML = "\uf15c"  #
    FILE_JSON = "\ue60b"  #
    FILE_MARKDOWN = "\uf48a"  #
    FILE_JINJA2 = "\ue235"  #
    FILE_DOCKER = "\uf308"  #
    FILE_COMPOSE = "\uf308"  #
    FILE_SHELL = "\uf489"  #
    FILE_PYTHON = "\ue73c"  #
    FILE_TEXT = "\uf15c"  #

    # Status Indicators
    STATUS_SUCCESS = "\uf00c"  #  (check)
    STATUS_ERROR = "\uf00d"  #  (times/x)
    STATUS_WARNING = "\uf071"  #  (exclamation-triangle)
    STATUS_INFO = "\uf05a"  #  (info-circle)
    STATUS_SKIPPED = "\uf05e"  #  (ban/circle-slash)

    # UI Elements
    UI_CONFIG = "\ue5fc"  #
    UI_LOCK = "\uf084"  #
    UI_SETTINGS = "\uf013"  #
    UI_ARROW_RIGHT = "\uf061"  #  (arrow-right)
    UI_BULLET = "\uf111"  #  (circle)
    UI_LIBRARY_GIT = "\uf418"  #  (git icon)
    UI_LIBRARY_STATIC = "\uf07c"  #  (folder icon)

    @classmethod
    def get_file_icon(cls, file_path: str | Path) -> str:
        """Get the appropriate icon for a file based on its extension or name.

        Args:
            file_path: Path to the file (can be string or Path object)

        Returns:
            Unicode icon character for the file type

        Examples:
            >>> IconManager.get_file_icon("config.yaml")
            '\uf15c'
            >>> IconManager.get_file_icon("template.j2")
            '\ue235'
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)

        file_name = file_path.name.lower()
        suffix = file_path.suffix.lower()

        # Check for Docker Compose files
        compose_names = {
            "docker-compose.yml",
            "docker-compose.yaml",
            "compose.yml",
            "compose.yaml",
        }
        if file_name in compose_names or file_name.startswith("docker-compose"):
            return cls.FILE_DOCKER

        # Check by extension
        extension_map = {
            ".yaml": cls.FILE_YAML,
            ".yml": cls.FILE_YAML,
            ".json": cls.FILE_JSON,
            ".md": cls.FILE_MARKDOWN,
            ".j2": cls.FILE_JINJA2,
            ".sh": cls.FILE_SHELL,
            ".py": cls.FILE_PYTHON,
            ".txt": cls.FILE_TEXT,
        }

        return extension_map.get(suffix, cls.FILE_DEFAULT)

    @classmethod
    def get_status_icon(cls, status: str) -> str:
        """Get the appropriate icon for a status indicator.

        Args:
            status: Status type (success, error, warning, info, skipped)

        Returns:
            Unicode icon character for the status

        Examples:
            >>> IconManager.get_status_icon("success")
            '✓'
            >>> IconManager.get_status_icon("warning")
            '⚠'
        """
        status_map = {
            "success": cls.STATUS_SUCCESS,
            "error": cls.STATUS_ERROR,
            "warning": cls.STATUS_WARNING,
            "info": cls.STATUS_INFO,
            "skipped": cls.STATUS_SKIPPED,
        }
        return status_map.get(status.lower(), cls.STATUS_INFO)

    @classmethod
    def folder(cls) -> str:
        """Get the folder icon."""
        return cls.FILE_FOLDER

    @classmethod
    def config(cls) -> str:
        """Get the config icon."""
        return cls.UI_CONFIG

    @classmethod
    def lock(cls) -> str:
        """Get the lock icon (for sensitive variables)."""
        return cls.UI_LOCK

    @classmethod
    def arrow_right(cls) -> str:
        """Get the right arrow icon (for showing transitions/changes)."""
        return cls.UI_ARROW_RIGHT


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
            return value[: max_length - len(self.settings.TRUNCATION_SUFFIX)] + self.settings.TRUNCATION_SUFFIX
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


# Export public API
__all__ = [
    "DisplayManager",
    "DisplaySettings",
    "IconManager",
    "console",
    "console_err",
]
