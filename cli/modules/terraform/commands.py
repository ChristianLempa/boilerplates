"""
Terraform module commands and functionality.
Manage Terraform infrastructure as code and template operations.
"""

from pathlib import Path
from typing import List, Optional

import typer
from rich.table import Table

from ...core.command import BaseModule


class TerraformModule(BaseModule):
    """Module for managing terraform configurations."""
    
    def __init__(self):
        super().__init__(name="terraform", icon="🏗️", description="Manage Terraform infrastructure as code")

    def add_module_commands(self, app: typer.Typer) -> None:
        """Add Module-specific commands to the app."""
        pass
