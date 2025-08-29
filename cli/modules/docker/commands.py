"""
Docker module commands and functionality.
Handles Docker container management with shared base commands.
"""

from typing import Optional
import typer
from ...core.command import BaseModule


class DockerModule(BaseModule):
    """Module for managing Docker configurations and containers."""
    
    def __init__(self):
        super().__init__(name="docker", icon="🐳", description="Manage Docker configurations and containers")

    def add_module_commands(self, app: typer.Typer) -> None:
        """Add Module-specific commands to the app."""
        pass
