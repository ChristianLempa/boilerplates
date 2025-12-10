"""Input Manager for standardized user input handling.

This module provides a centralized interface for all user input operations,
ensuring consistent styling and validation across the CLI.
"""

from __future__ import annotations

import logging
import re
from typing import Callable

from rich.console import Console
from rich.prompt import Confirm, IntPrompt, Prompt

from .input_settings import InputSettings

logger = logging.getLogger(__name__)
console = Console()


class InputManager:
    """Manages all user input operations with standardized styling.

    This class provides primitives for various types of user input including
    text, passwords, confirmations, choices, and validated inputs.
    """

    def __init__(self, settings: InputSettings | None = None):
        """Initialize InputManager.

        Args:
            settings: Input configuration settings (uses default if None)
        """
        self.settings = settings or InputSettings()

    def text(
        self,
        prompt: str,
        default: str | None = None,
        password: bool = False,
        validator: Callable[[str], bool] | None = None,
        error_message: str | None = None,
    ) -> str:
        """Prompt for text input.

        Args:
            prompt: Prompt message to display
            default: Default value if user presses Enter
            password: If True, mask the input
            validator: Optional validation function
            error_message: Custom error message for validation failure

        Returns:
            User input string
        """
        if password:
            return self.password(prompt, default)

        while True:
            result = Prompt.ask(
                f"[{self.settings.PROMPT_STYLE}]{prompt}[/{self.settings.PROMPT_STYLE}]",
                default=default or "",
                console=console,
            )

            if validator and not validator(result):
                msg = error_message or "Invalid input"
                console.print(f"[{self.settings.PROMPT_ERROR_STYLE}]{msg}[/{self.settings.PROMPT_ERROR_STYLE}]")
                continue

            return result

    def password(self, prompt: str, default: str | None = None) -> str:
        """Prompt for password input (masked).

        Args:
            prompt: Prompt message to display
            default: Default value if user presses Enter

        Returns:
            User input string (masked during entry)
        """
        return Prompt.ask(
            f"[{self.settings.PROMPT_STYLE}]{prompt}[/{self.settings.PROMPT_STYLE}]",
            default=default or "",
            password=True,
            console=console,
        )

    def confirm(self, prompt: str, default: bool | None = None) -> bool:
        """Prompt for yes/no confirmation.

        Args:
            prompt: Prompt message to display
            default: Default value if user presses Enter

        Returns:
            True for yes, False for no
        """
        if default is None:
            default = self.settings.DEFAULT_CONFIRM_YES

        return Confirm.ask(
            f"[{self.settings.PROMPT_STYLE}]{prompt}[/{self.settings.PROMPT_STYLE}]",
            default=default,
            console=console,
        )

    def integer(
        self,
        prompt: str,
        default: int | None = None,
        min_value: int | None = None,
        max_value: int | None = None,
    ) -> int:
        """Prompt for integer input with optional range validation.

        Args:
            prompt: Prompt message to display
            default: Default value if user presses Enter
            min_value: Minimum allowed value
            max_value: Maximum allowed value

        Returns:
            Integer value
        """
        while True:
            if default is not None:
                result = IntPrompt.ask(
                    f"[{self.settings.PROMPT_STYLE}]{prompt}[/{self.settings.PROMPT_STYLE}]",
                    default=default,
                    console=console,
                )
            else:
                try:
                    result = IntPrompt.ask(
                        f"[{self.settings.PROMPT_STYLE}]{prompt}[/{self.settings.PROMPT_STYLE}]",
                        console=console,
                    )
                except ValueError:
                    console.print(
                        f"[{self.settings.PROMPT_ERROR_STYLE}]{self.settings.MSG_INVALID_INTEGER}[/{self.settings.PROMPT_ERROR_STYLE}]"
                    )
                    continue

            # Validate range
            if min_value is not None and result < min_value:
                error_style = self.settings.PROMPT_ERROR_STYLE
                console.print(f"[{error_style}]Value must be at least {min_value}[/{error_style}]")
                continue

            if max_value is not None and result > max_value:
                error_style = self.settings.PROMPT_ERROR_STYLE
                console.print(f"[{error_style}]Value must be at most {max_value}[/{error_style}]")
                continue

            return result

    def choice(self, prompt: str, choices: list[str], default: str | None = None) -> str:
        """Prompt user to select one option from a list.

        Args:
            prompt: Prompt message to display
            choices: List of valid options
            default: Default choice if user presses Enter

        Returns:
            Selected choice
        """
        if not choices:
            raise ValueError("Choices list cannot be empty")

        choices_display = f"[{', '.join(choices)}]"
        full_prompt = f"{prompt} {choices_display}"

        while True:
            result = Prompt.ask(
                f"[{self.settings.PROMPT_STYLE}]{full_prompt}[/{self.settings.PROMPT_STYLE}]",
                default=default or "",
                console=console,
            )

            if result in choices:
                return result

            console.print(
                f"[{self.settings.PROMPT_ERROR_STYLE}]{self.settings.MSG_INVALID_CHOICE}[/{self.settings.PROMPT_ERROR_STYLE}]"
            )

    def validate_email(self, email: str) -> bool:
        """Validate email address format.

        Args:
            email: Email address to validate

        Returns:
            True if valid, False otherwise
        """
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    def validate_url(self, url: str) -> bool:
        """Validate URL format.

        Args:
            url: URL to validate

        Returns:
            True if valid, False otherwise
        """
        pattern = r"^https?://[^\s/$.?#].[^\s]*$"
        return bool(re.match(pattern, url, re.IGNORECASE))

    def validate_hostname(self, hostname: str) -> bool:
        """Validate hostname/domain format.

        Args:
            hostname: Hostname to validate

        Returns:
            True if valid, False otherwise
        """
        pattern = (
            r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*"
            r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$"
        )
        return bool(re.match(pattern, hostname))
