"""
Main application factory and CLI entry point.
Creates and configures the main Typer application with all modules.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.traceback import install

from cli import __version__
from ..modules import get_all_modules


from .logging import setup_logging


def version_callback(value: bool):
    """Callback for version option."""
    if value:
        console = Console()
        console.print(f"Boilerplates CLI v{__version__}", style="bold blue")
        raise typer.Exit()


def create_app() -> typer.Typer:
    """
    Create and configure the main CLI application.
    
    Returns:
        Configured Typer application with all modules registered.
    """
    # Install rich traceback handler for better error display
    install(show_locals=True)
    
    # Create main app
    app = typer.Typer(
        name="boilerplates",
        help="🚀 Sophisticated CLI tool for managing infrastructure boilerplates",
        epilog="Made with ❤️  by Christian Lempa",
        rich_markup_mode="rich",
        no_args_is_help=True,
    )
    
    @app.callback()
    def main(
        ctx: typer.Context,
        version: Optional[bool] = typer.Option(
            None, 
            "--version", 
            "-v",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit"
        ),
        log_level: str = typer.Option(
            "WARNING",
            "--log-level",
            "-l",
            help="Set logging level",
            case_sensitive=False,
        ),
    ):
        """
        🚀 Boilerplates CLI - Manage your infrastructure templates with ease!
        """
        
        # Configure logging
        setup_logging(log_level=log_level.upper())
        
        # Store context for subcommands
        ctx.ensure_object(dict)
    
    # Register all module commands
    modules = get_all_modules()
    for module in modules:
        try:
            module_app = module.get_app()
            app.add_typer(
                module_app,
                name=module.name,
                # Don't override help - let the module define it
            )
            logging.getLogger("boilerplates.app").info(f"Registered module: {module.name}")
        except Exception as e:
            logging.getLogger("boilerplates.app").error(f"Failed to register module {module.name}: {e}")
    
    return app
