"""Display module for CLI output rendering.

This package provides centralized display management with specialized managers
for different types of output (variables, templates, status messages, tables).
"""

from __future__ import annotations

from rich.console import Console

from .display_manager import DisplayManager
from .display_settings import DisplaySettings
from .icon_manager import IconManager

# Console instances for stdout and stderr
console = Console()
console_err = Console(stderr=True)


# Export public API
__all__ = [
    "DisplayManager",
    "DisplaySettings",
    "IconManager",
    "console",
    "console_err",
]
