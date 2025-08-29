"""
Kestra module commands and functionality.
Manage Kestra workflows and orchestration and template operations.
"""

from pathlib import Path
from typing import List, Optional

import typer
from rich.table import Table

from ...core.command import BaseModule


class KestraModule(BaseModule):
    """Module for managing Kestra workflows and orchestration."""

    def __init__(self):
        super().__init__(name="kestra", icon="⚡", description="Manage Kestra workflows and orchestration")

    def add_module_commands(self, app: typer.Typer) -> None:
        """Add Module-specific commands to the app."""
        pass
