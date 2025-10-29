from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.syntax import Syntax

if TYPE_CHECKING:
    from . import DisplayManager
    from ..exceptions import TemplateRenderError

logger = logging.getLogger(__name__)
console = Console()
console_err = Console(stderr=True)


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
        from . import IconManager

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
        from . import IconManager

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
        from . import IconManager

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
        from . import IconManager

        icon = IconManager.get_status_icon("warning")
        console.print(f"\n[yellow]{icon} {message}[/yellow]")

        if details:
            for detail in details:
                console.print(f"[yellow]  {detail}[/yellow]")

        return Confirm.ask("Continue?", default=default)

    def display_template_render_error(
        self, error: "TemplateRenderError", context: str | None = None
    ) -> None:
        """Display a detailed template rendering error with context and suggestions.

        Args:
            error: TemplateRenderError exception with detailed error information
            context: Optional context information (e.g., template ID)
        """
        from . import IconManager

        # Always display errors to stderr
        icon = IconManager.get_status_icon("error")
        if context:
            console_err.print(
                f"\n[red bold]{icon} Template Rendering Error[/red bold] [dim]({context})[/dim]"
            )
        else:
            console_err.print(f"\n[red bold]{icon} Template Rendering Error[/red bold]")

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
                    console_err.print(Panel(syntax, border_style="red", padding=(1, 2)))
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
