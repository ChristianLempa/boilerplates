from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.table import Table
from rich.tree import Tree

if TYPE_CHECKING:
    from .exceptions import TemplateRenderError
    from .template import Template

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


class VariableDisplayManager:
    """Handles all variable-related rendering.
    
    This manager is responsible for displaying variables, sections,
    and their values with appropriate formatting based on context.
    """

    def __init__(self, parent: "DisplayManager"):
        """Initialize VariableDisplayManager.
        
        Args:
            parent: Reference to parent DisplayManager for accessing shared resources
        """
        self.parent = parent

    def render_variable_value(
        self,
        variable,
        context: str = "default",
        is_dimmed: bool = False,
        var_satisfied: bool = True,
    ) -> str:
        """Render variable value with appropriate formatting based on context.
        
        Args:
            variable: Variable instance to render
            context: Display context ("default", "override", "disabled")
            is_dimmed: Whether the variable should be dimmed
            var_satisfied: Whether the variable's dependencies are satisfied
            
        Returns:
            Formatted string representation of the variable value
        """
        # Handle disabled bool variables
        if (is_dimmed or not var_satisfied) and variable.type == "bool":
            if (
                hasattr(variable, "_original_disabled")
                and variable._original_disabled is not False
            ):
                return f"{variable._original_disabled} {IconManager.arrow_right()} False"
            return "False"

        # Handle config overrides with arrow
        if (
            variable.origin == "config"
            and hasattr(variable, "_original_stored")
            and variable.original_value != variable.value
        ):
            settings = self.parent.settings
            orig = self._format_value(variable, variable.original_value, max_length=settings.VALUE_MAX_LENGTH_SHORT)
            curr = variable.get_display_value(
                mask_sensitive=True, max_length=settings.VALUE_MAX_LENGTH_SHORT, show_none=False
            )
            if not curr:
                curr = str(variable.value) if variable.value else settings.TEXT_EMPTY_OVERRIDE
            return (
                f"{orig} [bold {settings.COLOR_WARNING}]{IconManager.arrow_right()} {curr}[/bold {settings.COLOR_WARNING}]"
            )

        # Default formatting
        settings = self.parent.settings
        value = variable.get_display_value(
            mask_sensitive=True, max_length=settings.VALUE_MAX_LENGTH_DEFAULT, show_none=True
        )
        if not variable.value:
            return f"[{settings.COLOR_MUTED}]{value}[/{settings.COLOR_MUTED}]"
        return value

    def _format_value(self, variable, value, max_length: int | None = None) -> str:
        """Helper to format a specific value.
        
        Args:
            variable: Variable instance
            value: Value to format
            max_length: Maximum length before truncation
            
        Returns:
            Formatted value string
        """
        settings = self.parent.settings
        
        if variable.sensitive:
            return settings.SENSITIVE_MASK
        if value is None or value == "":
            return f"[{settings.COLOR_MUTED}]({settings.TEXT_EMPTY_VALUE})[/{settings.COLOR_MUTED}]"
        
        val_str = str(value)
        return self.parent._truncate_value(val_str, max_length)

    def render_section(self, title: str, description: str | None) -> None:
        """Display a section header.
        
        Args:
            title: Section title
            description: Optional section description
        """
        settings = self.parent.settings
        if description:
            console.print(
                f"\n[{settings.STYLE_SECTION_TITLE}]{title}[/{settings.STYLE_SECTION_TITLE}] [{settings.STYLE_SECTION_DESC}]- {description}[/{settings.STYLE_SECTION_DESC}]"
            )
        else:
            console.print(f"\n[{settings.STYLE_SECTION_TITLE}]{title}[/{settings.STYLE_SECTION_TITLE}]")
        console.print(settings.SECTION_SEPARATOR_CHAR * settings.SECTION_SEPARATOR_LENGTH, style=settings.COLOR_MUTED)

    def _render_section_header(self, section, is_dimmed: bool, has_dependencies: bool) -> str:
        """Build section header text with appropriate styling.
        
        Args:
            section: VariableSection instance
            is_dimmed: Whether section is dimmed (disabled)
            has_dependencies: Whether section has dependency requirements
            
        Returns:
            Formatted header text with Rich markup
        """
        settings = self.parent.settings
        disabled_text = settings.LABEL_DISABLED if (is_dimmed and not has_dependencies) else ""
        
        if is_dimmed:
            required_part = " (required)" if section.required else ""
            return f"[bold {settings.STYLE_DISABLED}]{section.title}{required_part}{disabled_text}[/bold {settings.STYLE_DISABLED}]"
        else:
            required_text = settings.LABEL_REQUIRED if section.required else ""
            return f"[bold]{section.title}{required_text}{disabled_text}[/bold]"
    
    def _render_variable_row(self, var_name: str, variable, is_dimmed: bool, var_satisfied: bool) -> tuple:
        """Build variable row data for table display.
        
        Args:
            var_name: Variable name
            variable: Variable instance
            is_dimmed: Whether containing section is dimmed
            var_satisfied: Whether variable dependencies are satisfied
            
        Returns:
            Tuple of (var_display, type, default_val, description, row_style)
        """
        settings = self.parent.settings
        
        # Build row style
        row_style = settings.STYLE_DISABLED if (is_dimmed or not var_satisfied) else None
        
        # Build default value
        default_val = self.render_variable_value(
            variable, is_dimmed=is_dimmed, var_satisfied=var_satisfied
        )
        
        # Build variable display name
        sensitive_icon = f" {IconManager.lock()}" if variable.sensitive else ""
        required_indicator = settings.LABEL_REQUIRED if variable.required else ""
        var_display = f"{settings.VAR_NAME_INDENT}{var_name}{sensitive_icon}{required_indicator}"
        
        return (
            var_display,
            variable.type or "str",
            default_val,
            variable.description or "",
            row_style,
        )

    def render_variables_table(self, template: "Template") -> None:
        """Display a table of variables for a template.

        All variables and sections are always shown. Disabled sections/variables
        are displayed with dimmed styling.

        Args:
            template: Template instance
        """
        if not (template.variables and template.variables.has_sections()):
            return

        settings = self.parent.settings
        console.print()
        console.print(f"[{settings.STYLE_HEADER}]Template Variables:[/{settings.STYLE_HEADER}]")

        variables_table = Table(show_header=True, header_style=settings.STYLE_TABLE_HEADER)
        variables_table.add_column("Variable", style=settings.STYLE_VAR_COL_NAME, no_wrap=True)
        variables_table.add_column("Type", style=settings.STYLE_VAR_COL_TYPE)
        variables_table.add_column("Default", style=settings.STYLE_VAR_COL_DEFAULT)
        variables_table.add_column("Description", style=settings.STYLE_VAR_COL_DESC)

        first_section = True
        for section in template.variables.get_sections().values():
            if not section.variables:
                continue

            if not first_section:
                variables_table.add_row("", "", "", "", style=settings.STYLE_DISABLED)
            first_section = False

            # Check if section is enabled AND dependencies are satisfied
            is_enabled = section.is_enabled()
            dependencies_satisfied = template.variables.is_section_satisfied(section.key)
            is_dimmed = not (is_enabled and dependencies_satisfied)
            has_dependencies = section.needs and len(section.needs) > 0

            # Render section header
            header_text = self._render_section_header(section, is_dimmed, has_dependencies)
            variables_table.add_row(header_text, "", "", "")

            # Render variables
            for var_name, variable in section.variables.items():
                # Skip toggle variable in required sections
                if section.required and section.toggle and var_name == section.toggle:
                    continue

                # Check if variable's needs are satisfied
                var_satisfied = template.variables.is_variable_satisfied(var_name)

                # Build and add row
                row_data = self._render_variable_row(var_name, variable, is_dimmed, var_satisfied)
                variables_table.add_row(*row_data)

        console.print(variables_table)


class TemplateDisplayManager:
    """Handles all template-related rendering.
    
    This manager is responsible for displaying template information,
    file trees, and metadata.
    """

    def __init__(self, parent: "DisplayManager"):
        """Initialize TemplateDisplayManager.
        
        Args:
            parent: Reference to parent DisplayManager for accessing shared resources
        """
        self.parent = parent

    def render_template(self, template: "Template", template_id: str) -> None:
        """Display template information panel and variables table.

        Args:
            template: Template instance to display
            template_id: ID of the template
        """
        self.render_template_header(template, template_id)
        self.render_file_tree(template)
        self.parent.variables.render_variables_table(template)

    def render_template_header(self, template: "Template", template_id: str) -> None:
        """Display the header for a template with library information.
        
        Args:
            template: Template instance
            template_id: ID of the template
        """
        settings = self.parent.settings
        
        template_name = template.metadata.name or settings.TEXT_UNNAMED_TEMPLATE
        version = (
            str(template.metadata.version)
            if template.metadata.version
            else settings.TEXT_VERSION_NOT_SPECIFIED
        )
        schema = template.schema_version if hasattr(template, "schema_version") else "1.0"
        description = template.metadata.description or settings.TEXT_NO_DESCRIPTION

        # Get library information and format with helper
        library_name = template.metadata.library or ""
        library_type = template.metadata.library_type or "git"
        library_display = self.parent._format_library_display(library_name, library_type)

        console.print(
            f"[{settings.STYLE_HEADER}]{template_name} ({template_id} - [cyan]{version}[/cyan] - [magenta]schema {schema}[/magenta]) {library_display}[/{settings.STYLE_HEADER}]"
        )
        console.print(description)

    def render_file_tree(self, template: "Template") -> None:
        """Display the file structure of a template.
        
        Args:
            template: Template instance
        """
        settings = self.parent.settings
        console.print()
        console.print(f"[{settings.STYLE_HEADER}]Template File Structure:[/{settings.STYLE_HEADER}]")

        def get_template_file_info(template_file):
            display_name = (
                template_file.output_path.name
                if hasattr(template_file, "output_path")
                else template_file.relative_path.name
            )
            return (template_file.relative_path, display_name, "white", None)

        file_tree = self.parent._render_file_tree_internal(
            f"{IconManager.folder()} [white]{template.id}[/white]",
            template.template_files,
            get_template_file_info,
        )

        if file_tree.children:
            console.print(file_tree)

    def render_file_generation_confirmation(
        self,
        output_dir: Path,
        files: dict[str, str],
        existing_files: list[Path] | None = None,
    ) -> None:
        """Display files to be generated with confirmation prompt.
        
        Args:
            output_dir: Output directory path
            files: Dictionary of file paths to content
            existing_files: List of existing files that will be overwritten
        """
        console.print()
        console.print("[bold]Files to be generated:[/bold]")

        def get_file_generation_info(file_path_str):
            file_path = Path(file_path_str)
            file_name = file_path.parts[-1] if file_path.parts else file_path.name
            full_path = output_dir / file_path

            if existing_files and full_path in existing_files:
                return (file_path, file_name, "yellow", "[red](will overwrite)[/red]")
            else:
                return (file_path, file_name, "green", None)

        file_tree = self.parent._render_file_tree_internal(
            f"{IconManager.folder()} [cyan]{output_dir.resolve()}[/cyan]",
            files.keys(),
            get_file_generation_info,
        )

        console.print(file_tree)
        console.print()


class StatusDisplayManager:
    """Handles status messages and error display.
    
    This manager is responsible for displaying success, error, warning,
    and informational messages with consistent formatting.
    """

    def __init__(self, parent: "DisplayManager"):
        """Initialize StatusDisplayManager.
        
        Args:
            parent: Reference to parent DisplayManager for accessing shared resources
        """
        self.parent = parent

    def display_message(
        self, level: str, message: str, context: str | None = None
    ) -> None:
        """Display a message with consistent formatting.

        Args:
            level: Message level (error, warning, success, info)
            message: The message to display
            context: Optional context information
        """
        # Errors and warnings always go to stderr, even in quiet mode
        # Success and info respect quiet mode and go to stdout
        if level in ("error", "warning"):
            output_console = console_err
            should_print = True
        else:
            output_console = console
            should_print = not self.parent.quiet

        if not should_print:
            return

        settings = self.parent.settings
        icon = IconManager.get_status_icon(level)
        colors = {
            "error": settings.COLOR_ERROR,
            "warning": settings.COLOR_WARNING,
            "success": settings.COLOR_SUCCESS,
            "info": settings.COLOR_INFO,
        }
        color = colors.get(level, "white")

        # Format message based on context
        if context:
            text = (
                f"{level.capitalize()} in {context}: {message}"
                if level == "error" or level == "warning"
                else f"{context}: {message}"
            )
        else:
            text = (
                f"{level.capitalize()}: {message}"
                if level == "error" or level == "warning"
                else message
            )

        output_console.print(f"[{color}]{icon} {text}[/{color}]")

        # Log appropriately
        log_message = f"{context}: {message}" if context else message
        log_methods = {
            "error": logger.error,
            "warning": logger.warning,
            "success": logger.info,
            "info": logger.info,
        }
        log_methods.get(level, logger.info)(log_message)

    def display_error(self, message: str, context: str | None = None) -> None:
        """Display an error message.
        
        Args:
            message: Error message
            context: Optional context
        """
        self.display_message("error", message, context)

    def display_warning(self, message: str, context: str | None = None) -> None:
        """Display a warning message.
        
        Args:
            message: Warning message
            context: Optional context
        """
        self.display_message("warning", message, context)

    def display_success(self, message: str, context: str | None = None) -> None:
        """Display a success message.
        
        Args:
            message: Success message
            context: Optional context
        """
        self.display_message("success", message, context)

    def display_info(self, message: str, context: str | None = None) -> None:
        """Display an informational message.
        
        Args:
            message: Info message
            context: Optional context
        """
        self.display_message("info", message, context)

    def display_validation_error(self, message: str) -> None:
        """Display a validation error message.
        
        Args:
            message: Validation error message
        """
        self.display_message("error", message)

    def display_version_incompatibility(
        self, template_id: str, required_version: str, current_version: str
    ) -> None:
        """Display a version incompatibility error with upgrade instructions.

        Args:
            template_id: ID of the incompatible template
            required_version: Minimum CLI version required by template
            current_version: Current CLI version
        """
        console_err.print()
        console_err.print(
            f"[bold red]{IconManager.STATUS_ERROR} Version Incompatibility[/bold red]"
        )
        console_err.print()
        console_err.print(
            f"Template '[cyan]{template_id}[/cyan]' requires CLI version [green]{required_version}[/green] or higher."
        )
        console_err.print(f"Current CLI version: [yellow]{current_version}[/yellow]")
        console_err.print()
        console_err.print("[bold]Upgrade Instructions:[/bold]")
        console_err.print(
            f"  {IconManager.UI_ARROW_RIGHT} Run: [cyan]pip install --upgrade boilerplates[/cyan]"
        )
        console_err.print(
            f"  {IconManager.UI_ARROW_RIGHT} Or install specific version: [cyan]pip install boilerplates=={required_version}[/cyan]"
        )
        console_err.print()

        logger.error(
            f"Template '{template_id}' requires CLI version {required_version}, "
            f"current version is {current_version}"
        )

    def display_skipped(self, message: str, reason: str | None = None) -> None:
        """Display a skipped/disabled message.

        Args:
            message: The main message to display
            reason: Optional reason why it was skipped
        """
        icon = IconManager.get_status_icon("skipped")
        if reason:
            console.print(f"\n[dim]{icon} {message} (skipped - {reason})[/dim]")
        else:
            console.print(f"\n[dim]{icon} {message} (skipped)[/dim]")

    def display_warning_with_confirmation(
        self, message: str, details: list[str] | None = None, default: bool = False
    ) -> bool:
        """Display a warning message with optional details and get confirmation.

        Args:
            message: Warning message to display
            details: Optional list of detail lines to show
            default: Default value for confirmation

        Returns:
            True if user confirms, False otherwise
        """
        icon = IconManager.get_status_icon("warning")
        console.print(f"\n[yellow]{icon} {message}[/yellow]")

        if details:
            for detail in details:
                console.print(f"[yellow]  {detail}[/yellow]")

        from rich.prompt import Confirm

        return Confirm.ask("Continue?", default=default)

    def display_template_render_error(
        self, error: "TemplateRenderError", context: str | None = None
    ) -> None:
        """Display a detailed template rendering error with context and suggestions.

        Args:
            error: TemplateRenderError exception with detailed error information
            context: Optional context information (e.g., template ID)
        """
        from rich.panel import Panel
        from rich.syntax import Syntax

        # Always display errors to stderr
        icon = IconManager.get_status_icon("error")
        if context:
            console_err.print(
                f"\n[red bold]{icon} Template Rendering Error[/red bold] [dim]({context})[/dim]"
            )
        else:
            console_err.print(
                f"\n[red bold]{icon} Template Rendering Error[/red bold]"
            )

        console_err.print()

        # Display error message
        if error.file_path:
            console_err.print(
                f"[red]Error in file:[/red] [cyan]{error.file_path}[/cyan]"
            )
            if error.line_number:
                location = f"Line {error.line_number}"
                if error.column:
                    location += f", Column {error.column}"
                console_err.print(f"[red]Location:[/red] {location}")

        console_err.print(
            f"[red]Message:[/red] {str(error.original_error) if error.original_error else str(error)}"
        )
        console_err.print()

        # Display code context if available
        if error.context_lines:
            console_err.print("[bold cyan]Code Context:[/bold cyan]")

            # Build the context text
            context_text = "\n".join(error.context_lines)

            # Display in a panel with syntax highlighting if possible
            file_ext = Path(error.file_path).suffix if error.file_path else ""
            if file_ext == ".j2":
                # Remove .j2 to get base extension for syntax highlighting
                base_name = Path(error.file_path).stem
                base_ext = Path(base_name).suffix
                lexer = "jinja2" if not base_ext else None
            else:
                lexer = None

            try:
                if lexer:
                    syntax = Syntax(
                        context_text, lexer, line_numbers=False, theme="monokai"
                    )
                    console_err.print(
                        Panel(syntax, border_style="red", padding=(1, 2))
                    )
                else:
                    console_err.print(
                        Panel(context_text, border_style="red", padding=(1, 2))
                    )
            except Exception:
                # Fallback to plain panel if syntax highlighting fails
                console_err.print(
                    Panel(context_text, border_style="red", padding=(1, 2))
                )

            console_err.print()

        # Display suggestions if available
        if error.suggestions:
            console_err.print("[bold yellow]Suggestions:[/bold yellow]")
            for i, suggestion in enumerate(error.suggestions, 1):
                bullet = IconManager.UI_BULLET
                console_err.print(f"  [yellow]{bullet}[/yellow] {suggestion}")
            console_err.print()

        # Display variable context in debug mode
        if error.variable_context:
            console_err.print("[bold blue]Available Variables (Debug):[/bold blue]")
            var_list = ", ".join(sorted(error.variable_context.keys()))
            console_err.print(f"[dim]{var_list}[/dim]")
            console_err.print()


class TableDisplayManager:
    """Handles table rendering.
    
    This manager is responsible for displaying various types of tables
    including templates lists, status tables, and summaries.
    """

    def __init__(self, parent: "DisplayManager"):
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
        table = Table(title=title)
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
            version = str(template.metadata.version) if template.metadata.version else ""
            schema = template.schema_version if hasattr(template, "schema_version") else "1.0"

            # Use helper for library display
            library_name = template.metadata.library or ""
            library_type = template.metadata.library_type or "git"
            library_display = self.parent._format_library_display(library_name, library_type)

            table.add_row(template.id, name, tags, version, schema, library_display)

        console.print(table)

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
        table = Table(title=title, show_header=True)
        table.add_column(columns[0], style="cyan", no_wrap=True)
        table.add_column(columns[1])

        for name, message, success in rows:
            status_style = "green" if success else "red"
            status_icon = IconManager.get_status_icon(
                "success" if success else "error"
            )
            table.add_row(
                name, f"[{status_style}]{status_icon} {message}[/{status_style}]"
            )

        console.print(table)

    def render_summary_table(self, title: str, items: dict[str, str]) -> None:
        """Display a simple two-column summary table.

        Args:
            title: Table title
            items: Dictionary of key-value pairs to display
        """
        settings = self.parent.settings
        table = Table(title=title, show_header=False, box=None, padding=settings.PADDING_TABLE_NORMAL)
        table.add_column(style="bold")
        table.add_column()

        for key, value in items.items():
            table.add_row(key, value)

        console.print(table)

    def render_file_operation_table(
        self, files: list[tuple[str, int, str]]
    ) -> None:
        """Display a table of file operations with sizes and statuses.

        Args:
            files: List of tuples (file_path, size_bytes, status)
        """
        settings = self.parent.settings
        table = Table(
            show_header=True, header_style=settings.STYLE_HEADER_ALT, box=None, padding=settings.PADDING_TABLE_COMPACT
        )
        table.add_column("File", style="white", no_wrap=False)
        table.add_column("Size", justify="right", style=settings.COLOR_MUTED)
        table.add_column("Status", style=settings.COLOR_WARNING)

        for file_path, size_bytes, status in files:
            size_str = self.parent._format_file_size(size_bytes)
            table.add_row(str(file_path), size_str, status)

        console.print(table)

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
            console.print(
                f"[yellow]No configuration found for module '{module_name}'[/yellow]"
            )
            return

        # Create root tree node
        tree = Tree(
            f"[bold blue]{IconManager.config()} {str.capitalize(module_name)} Configuration[/bold blue]"
        )

        for section_name, section_data in spec.items():
            if not isinstance(section_data, dict):
                continue

            # Determine if this is a section with variables
            section_vars = section_data.get("vars") or {}
            section_desc = section_data.get("description", "")
            section_required = section_data.get("required", False)
            section_toggle = section_data.get("toggle", None)
            section_needs = section_data.get("needs", None)

            # Build section label
            section_label = f"[cyan]{section_name}[/cyan]"
            if section_required:
                section_label += " [yellow](required)[/yellow]"
            if section_toggle:
                section_label += f" [dim](toggle: {section_toggle})[/dim]"
            if section_needs:
                needs_str = (
                    ", ".join(section_needs)
                    if isinstance(section_needs, list)
                    else section_needs
                )
                section_label += f" [dim](needs: {needs_str})[/dim]"

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
                        var_label = (
                            f"[green]{var_name}[/green] [dim]({var_type})[/dim]"
                        )

                        if var_default is not None and var_default != "":
                            settings = self.parent.settings
                            display_val = settings.SENSITIVE_MASK if var_sensitive else str(var_default)
                            if not var_sensitive:
                                display_val = self.parent._truncate_value(display_val, settings.VALUE_MAX_LENGTH_DEFAULT)
                            var_label += f" = [{settings.COLOR_WARNING}]{display_val}[/{settings.COLOR_WARNING}]"

                        if show_all and var_desc:
                            var_label += f"\n    [dim]{var_desc}[/dim]"

                        section_node.add(var_label)
                    else:
                        # Simple key-value pair
                        section_node.add(
                            f"[green]{var_name}[/green] = [yellow]{var_data}[/yellow]"
                        )

        console.print(tree)


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
