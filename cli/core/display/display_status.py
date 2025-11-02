from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from rich.console import Console

from .display_icons import IconManager
from .display_settings import DisplaySettings

if TYPE_CHECKING:
    from .display_base import BaseDisplay

logger = logging.getLogger(__name__)
console_err = Console(stderr=True)  # Keep for error output


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

    def _display_message(
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
        should_print = use_stderr or not self.quiet

        if not should_print:
            return

        settings = self.settings
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

    def error(self, message: str, context: str | None = None) -> None:
        """Display an error message.

        Args:
            message: Error message
            context: Optional context
        """
        self._display_message("error", message, context)

    def warning(self, message: str, context: str | None = None) -> None:
        """Display a warning message.

        Args:
            message: Warning message
            context: Optional context
        """
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
        icon = IconManager.get_status_icon("skipped")
        if reason:
            self.base.text(f"\n{icon} {message} (skipped - {reason})", style="dim")
        else:
            self.base.text(f"\n{icon} {message} (skipped)", style="dim")
