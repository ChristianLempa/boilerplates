from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.syntax import Syntax

from .icon_manager import IconManager

if TYPE_CHECKING:
    from ..exceptions import TemplateRenderError
    from . import DisplayManager

logger = logging.getLogger(__name__)
console_err = Console(stderr=True)  # Keep for error output


class StatusDisplayManager:
    """Handles status messages and error display.

    This manager is responsible for displaying success, error, warning,
    and informational messages with consistent formatting.
    """

    def __init__(self, parent: DisplayManager):
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
        use_stderr = level in ("error", "warning")
        should_print = use_stderr or not self.parent.quiet

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
                if level in {"error", "warning"}
                else f"{context}: {message}"
            )
        else:
            text = (
                f"{level.capitalize()}: {message}"
                if level in {"error", "warning"}
                else message
            )

        formatted_text = f"[{color}]{icon} {text}[/{color}]"
        if use_stderr:
            console_err.print(formatted_text)
        else:
            self.parent.text(formatted_text)

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
            self.parent.text(f"\n{icon} {message} (skipped - {reason})", style="dim")
        else:
            self.parent.text(f"\n{icon} {message} (skipped)", style="dim")

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
        self.parent.text(f"\n{icon} {message}", style="yellow")

        if details:
            for detail in details:
                self.parent.text(f"  {detail}", style="yellow")

        return Confirm.ask("Continue?", default=default)

    def _display_error_header(self, icon: str, context: str | None) -> None:
        """Display error header with optional context."""
        if context:
            console_err.print(
                f"\n[red bold]{icon} Template Rendering Error[/red bold] [dim]({context})[/dim]"
            )
        else:
            console_err.print(f"\n[red bold]{icon} Template Rendering Error[/red bold]")
        console_err.print()

    def _display_error_location(self, error: TemplateRenderError) -> None:
        """Display error file path and location."""
        if not error.file_path:
            return

        console_err.print(f"[red]Error in file:[/red] [cyan]{error.file_path}[/cyan]")
        if error.line_number:
            location = f"Line {error.line_number}"
            if error.column:
                location += f", Column {error.column}"
            console_err.print(f"[red]Location:[/red] {location}")

    def _display_code_context(self, error: TemplateRenderError) -> None:
        """Display code context with syntax highlighting."""
        if not error.context_lines:
            return

        console_err.print("[bold cyan]Code Context:[/bold cyan]")
        context_text = "\n".join(error.context_lines)

        # Determine lexer for syntax highlighting
        lexer = self._get_lexer_for_file(error.file_path)

        # Try to display with syntax highlighting, fallback to plain on error
        try:
            self._display_syntax_panel(context_text, lexer)
        except Exception:
            console_err.print(Panel(context_text, border_style="red", padding=(1, 2)))

        console_err.print()

    def _get_lexer_for_file(self, file_path: str | None) -> str | None:
        """Determine lexer based on file extension."""
        if not file_path:
            return None

        file_ext = Path(file_path).suffix
        if file_ext == ".j2":
            base_name = Path(file_path).stem
            base_ext = Path(base_name).suffix
            return "jinja2" if not base_ext else None
        return None

    def _display_syntax_panel(self, text: str, lexer: str | None) -> None:
        """Display text in a panel with optional syntax highlighting."""
        if lexer:
            syntax = Syntax(text, lexer, line_numbers=False, theme="monokai")
            console_err.print(Panel(syntax, border_style="red", padding=(1, 2)))
        else:
            console_err.print(Panel(text, border_style="red", padding=(1, 2)))

    def display_template_render_error(
        self, error: TemplateRenderError, context: str | None = None
    ) -> None:
        """Display a detailed template rendering error with context and suggestions.

        Args:
            error: TemplateRenderError exception with detailed error information
            context: Optional context information (e.g., template ID)
        """
        # Display error header
        icon = IconManager.get_status_icon("error")
        self._display_error_header(icon, context)

        # Display error location
        self._display_error_location(error)

        # Display error message
        console_err.print(
            f"[red]Message:[/red] {str(error.original_error) if error.original_error else str(error)}"
        )
        console_err.print()

        # Display code context
        self._display_code_context(error)

        # Display suggestions if available
        if error.suggestions:
            console_err.print("[bold yellow]Suggestions:[/bold yellow]")
            for _i, suggestion in enumerate(error.suggestions, 1):
                bullet = IconManager.UI_BULLET
                console_err.print(f"  [yellow]{bullet}[/yellow] {suggestion}")
            console_err.print()

        # Display variable context in debug mode
        if error.variable_context:
            console_err.print("[bold blue]Available Variables (Debug):[/bold blue]")
            var_list = ", ".join(sorted(error.variable_context.keys()))
            console_err.print(f"[dim]{var_list}[/dim]")
            console_err.print()
