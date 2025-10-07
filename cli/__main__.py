#!/usr/bin/env python3
"""
Main entry point for the Boilerplates CLI application.
This file serves as the primary executable when running the CLI.
"""
from __future__ import annotations

import importlib
import logging
import pkgutil
import sys
from pathlib import Path
from typing import Optional
from typer import Typer, Context, Option
from rich.console import Console
import cli.modules
from cli.core.registry import registry
from cli.core import repo
# Using standard Python exceptions instead of custom ones

# NOTE: Placeholder version - will be overwritten by release script (.github/workflows/release.yaml)
__version__ = "0.0.4"

app = Typer(
  help="CLI tool for managing infrastructure boilerplates.\n\n[dim]Easily generate, customize, and deploy templates for Docker Compose, Terraform, Kubernetes, and more.\n\n [white]Made with 💜 by [bold]Christian Lempa[/bold]",
  add_completion=True,
  rich_markup_mode="rich",
)
console = Console()

def setup_logging(log_level: str = "WARNING") -> None:
  """Configure the logging system with the specified log level.
  
  Args:
      log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  
  Raises:
      ValueError: If the log level is invalid
      RuntimeError: If logging configuration fails
  """
  numeric_level = getattr(logging, log_level.upper(), None)
  if not isinstance(numeric_level, int):
    raise ValueError(
      f"Invalid log level '{log_level}'. Valid levels: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )
  
  try:
    logging.basicConfig(
      level=numeric_level,
      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
      datefmt='%Y-%m-%d %H:%M:%S'
    )

    logger = logging.getLogger(__name__)
    logger.setLevel(numeric_level)
  except Exception as e:
    raise RuntimeError(f"Failed to configure logging: {e}")

@app.callback(invoke_without_command=True)
def main(
  ctx: Context,
  version: Optional[bool] = Option(
    None,
    "--version",
    "-v",
    help="Show the application version and exit.",
    is_flag=True,
    callback=lambda v: console.print(f"boilerplates version {__version__}") or sys.exit(0) if v else None,
    is_eager=True,
  ),
  log_level: Optional[str] = Option(
    None,
    "--log-level",
    help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). If omitted, logging is disabled."
  )
) -> None:
  """CLI tool for managing infrastructure boilerplates."""
  # Disable logging by default; only enable when user provides --log-level
  if log_level:
    # Re-enable logging and configure
    logging.disable(logging.NOTSET)
    setup_logging(log_level)
  else:
    # Silence all logging (including third-party) unless user explicitly requests it
    logging.disable(logging.CRITICAL)
  
  # Store log level in context for potential use by other commands
  ctx.ensure_object(dict)
  ctx.obj['log_level'] = log_level
  
  # If no subcommand is provided, show help and friendly intro
  if ctx.invoked_subcommand is None:
    console.print(ctx.get_help())
    sys.exit(0)

def init_app() -> None:
  """Initialize the application by discovering and registering modules.
  
  Raises:
      ImportError: If critical module import operations fail
      RuntimeError: If application initialization fails
  """
  logger = logging.getLogger(__name__)
  failed_imports = []
  failed_registrations = []
  
  try:
    # Auto-discover and import all modules
    modules_path = Path(cli.modules.__file__).parent
    logger.debug(f"Discovering modules in {modules_path}")
    
    for finder, name, ispkg in pkgutil.iter_modules([str(modules_path)]):
      if not ispkg and not name.startswith('_') and name != 'base':
        try:
          logger.debug(f"Importing module: {name}")
          importlib.import_module(f"cli.modules.{name}")
        except ImportError as e:
          error_info = f"Import failed for '{name}': {str(e)}"
          failed_imports.append(error_info)
          logger.warning(error_info)
        except Exception as e:
          error_info = f"Unexpected error importing '{name}': {str(e)}"
          failed_imports.append(error_info)
          logger.error(error_info)
    
    # Register core repo command
    try:
      logger.debug("Registering repo command")
      repo.register_cli(app)
    except Exception as e:
      error_info = f"Repo command registration failed: {str(e)}"
      failed_registrations.append(error_info)
      logger.warning(error_info)
    
    # Register template-based modules with app
    module_classes = list(registry.iter_module_classes())
    logger.debug(f"Registering {len(module_classes)} template-based modules")
    
    for name, module_cls in module_classes:
      try:
        logger.debug(f"Registering module class: {module_cls.__name__}")
        module_cls.register_cli(app)
      except Exception as e:
        error_info = f"Registration failed for '{module_cls.__name__}': {str(e)}"
        failed_registrations.append(error_info)
        # Log warning but don't raise exception for individual module failures
        logger.warning(error_info)
        console.print(f"[yellow]Warning:[/yellow] {error_info}")
    
    # If we have no modules registered at all, that's a critical error
    if not module_classes and not failed_imports:
      raise RuntimeError("No modules found to register")
    
    # Log summary
    successful_modules = len(module_classes) - len(failed_registrations)
    logger.info(f"Application initialized: {successful_modules} modules registered successfully")
    
    if failed_imports:
      logger.info(f"Module import failures: {len(failed_imports)}")
    if failed_registrations:
      logger.info(f"Module registration failures: {len(failed_registrations)}")
      
  except Exception as e:
    error_details = []
    if failed_imports:
      error_details.extend(["Import failures:"] + [f"  - {err}" for err in failed_imports])
    if failed_registrations:
      error_details.extend(["Registration failures:"] + [f"  - {err}" for err in failed_registrations])
    
    details = "\n".join(error_details) if error_details else str(e)
    raise RuntimeError(f"Application initialization failed: {details}")

def run() -> None:
  """Run the CLI application."""
  try:
    init_app()
    app()
  except (ValueError, RuntimeError) as e:
    # Handle configuration and initialization errors cleanly
    console.print(f"[bold red]Error:[/bold red] {e}")
    sys.exit(1)
  except ImportError as e:
    # Handle module import errors with detailed info
    console.print(f"[bold red]Module Import Error:[/bold red] {e}")
    sys.exit(1)
  except KeyboardInterrupt:
    # Handle Ctrl+C gracefully
    console.print("\n[yellow]Operation cancelled by user[/yellow]")
    sys.exit(130)
  except Exception as e:
    # Handle unexpected errors - show simplified message
    console.print(f"[bold red]Unexpected error:[/bold red] {e}")
    console.print("[dim]Use --log-level DEBUG for more details[/dim]")
    sys.exit(1)

if __name__ == "__main__":
  run()
