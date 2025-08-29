"""
Base classes and utilities for CLI modules and commands.
Provides common functionality and patterns for all modules.
"""

import logging
from abc import ABC
from typing import Optional

import typer
from rich.console import Console



class BaseModule(ABC):
    """Abstract base class for all CLI modules with shared commands."""
    
    def __init__(self, name: str, icon: str = "", description: str = ""):
        self.name = name
        self.icon = icon
        self.description = description
        self.console = Console()
        self.logger = logging.getLogger(f"boilerplates.module.{name}")
    
    def get_app(self) -> typer.Typer:
        """
        Create and return the Typer app with shared commands.
        Subclasses can override this to add module-specific commands.
        """
        app = typer.Typer(
            name=self.name,
            help=f"{self.icon} {self.description}",
            rich_markup_mode="rich"
        )
        
        # Add module-specific commands
        self._add_module_commands(app)
        
        return app
    
    def _add_module_commands(self, app: typer.Typer) -> None:
        """
        Override this method in subclasses to add module-specific commands.
        This is called after the shared commands are added.
        """
        pass
