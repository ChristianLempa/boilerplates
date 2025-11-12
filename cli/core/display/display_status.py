from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from rich import box
from rich.console import Console, ConsoleOptions, RenderResult
from rich.markdown import Heading, Markdown
from rich.panel import Panel

from .display_icons import IconManager
from .display_settings import DisplaySettings

if TYPE_CHECKING:
    from .display_base import BaseDisplay

logger = logging.getLogger(__name__)
console_err = Console(stderr=True)  # Keep for error output


class LeftAlignedHeading(Heading):
    """Custom Heading element with left alignment and no extra spacing."""

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        text = self.text
        text.justify = "left"  # Override center justification
        if self.tag == "h1":
            # Draw a border around h1s (left-aligned)
            yield Panel(
                text,
                box=box.HEAVY,
                style="markdown.h1.border",
            )
        else:
            # Styled text for h2 and beyond (no blank line before h2)
            yield text


class LeftAlignedMarkdown(Markdown):
    """Custom Markdown renderer with left-aligned headings."""

    def __init__(self, markup: str, **kwargs):
        """Initialize with custom heading element."""
        super().__init__(markup, **kwargs)

        # Replace heading element to use left alignment
        self.elements["heading_open"] = LeftAlignedHeading


class StatusDisplay:
    """Status messages and error display.

    Provides methods for displaying success, error, warning,
    and informational messages with consistent formatting.
    """

    def __init__(self, settings: DisplaySettings, quiet: bool, base: BaseDisplay):
        """Initialize StatusDisplay.

        Args:
            settings: Display settings for formatting
            quiet: If True, suppress non-error output
            base: BaseDisplay instance
        """
        self.settings = settings
        self.quiet = quiet
        self.base = base

    def _display_message(self, level: str, message: str, context: str | None = None) -> None:
        """Display a message with consistent formatting.

        Args:
            level: Message level (error, warning, success, info)
            message: The message to display
            context: Optional context information
        """
        # Errors and warnings always go to stderr, even in quiet mode
        # Success and info respect quiet mode and go to stdout
        use_stderr = level in ("error", "warning")
        should_print = use_stderr or not self.quiet

        if not should_print:
            return

        settings = self.settings
        colors = {
            "error": settings.COLOR_ERROR,
            "warning": settings.COLOR_WARNING,
            "success": settings.COLOR_SUCCESS,
        }
        color = colors.get(level)

        # Format message based on context
        if context:
            text = (
                f"{level.capitalize()} in {context}: {message}"
                if level in {"error", "warning"}
                else f"{context}: {message}"
            )
        else:
            text = f"{level.capitalize()}: {message}" if level in {"error", "warning"} else message

        # Only use icons and colors for actual status indicators (error, warning, success)
        # Plain info messages use default terminal color (no markup)
        if level in {"error", "warning", "success"}:
            icon = IconManager.get_status_icon(level)
            formatted_text = f"[{color}]{icon} {text}[/{color}]"
        else:
            formatted_text = text

        if use_stderr:
            console_err.print(formatted_text)
        else:
            self.base.text(formatted_text)

        # Log appropriately
        log_message = f"{context}: {message}" if context else message
        log_methods = {
            "error": logger.error,
            "warning": logger.warning,
            "success": logger.info,
            "info": logger.info,
        }
        log_methods.get(level, logger.info)(log_message)

    def error(self, message: str, context: str | None = None, details: str | None = None) -> None:
        """Display an error message.

        Args:
            message: Error message
            context: Optional context
            details: Optional additional details (shown in dim style on same line)
        """
        if details:
            # Combine message and details on same line with different formatting
            settings = self.settings
            color = settings.COLOR_ERROR
            icon = IconManager.get_status_icon("error")

            # Format: Icon Error: Message (details in dim)
            formatted = f"[{color}]{icon} Error: {message}[/{color}] [dim]({details})[/dim]"
            console_err.print(formatted)

            # Log at debug level to avoid duplicate console output (already printed to stderr)
            logger.debug(f"Error displayed: {message} ({details})")
        else:
            # No details, use standard display
            self._display_message("error", message, context)

    def warning(self, message: str, context: str | None = None, details: str | None = None) -> None:
        """Display a warning message.

        Args:
            message: Warning message
            context: Optional context
            details: Optional additional details (shown in dim style on same line)
        """
        if details:
            # Combine message and details on same line with different formatting
            settings = self.settings
            color = settings.COLOR_WARNING
            icon = IconManager.get_status_icon("warning")

            # Format: Icon Warning: Message (details in dim)
            formatted = f"[{color}]{icon} Warning: {message}[/{color}] [dim]({details})[/dim]"
            console_err.print(formatted)

            # Log at debug level to avoid duplicate console output (already printed to stderr)
            logger.debug(f"Warning displayed: {message} ({details})")
        else:
            # No details, use standard display
            self._display_message("warning", message, context)

    def success(self, message: str, context: str | None = None) -> None:
        """Display a success message.

        Args:
            message: Success message
            context: Optional context
        """
        self._display_message("success", message, context)

    def info(self, message: str, context: str | None = None) -> None:
        """Display an informational message.

        Args:
            message: Info message
            context: Optional context
        """
        self._display_message("info", message, context)

    def skipped(self, message: str, reason: str | None = None) -> None:
        """Display a skipped/disabled message.

        Args:
            message: The main message to display
            reason: Optional reason why it was skipped
        """
        if reason:
            self.base.text(f"\n{message} (skipped - {reason})", style="dim")
        else:
            self.base.text(f"\n{message} (skipped)", style="dim")

    def markdown(self, content: str) -> None:
        """Render markdown content with left-aligned headings.

        Args:
            content: Markdown-formatted text to render
        """
        if not self.quiet:
            console = Console()
            console.print(LeftAlignedMarkdown(content))
