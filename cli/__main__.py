#!/usr/bin/env python3
"""
Main entry point for the Boilerplates CLI application.
This file serves as the primary executable when running the CLI.
"""
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
# Using standard Python exceptions instead of custom ones

app = Typer(no_args_is_help=True)
console = Console()

def setup_logging(log_level: str = "WARNING"):
  """Configure the logging system with the specified log level.
  
  Args:
      log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  
  Raises:
      ValueError: If the log level is invalid
      RuntimeError: If logging configuration fails
  """
  # Convert string to logging level
  numeric_level = getattr(logging, log_level.upper(), None)
  if not isinstance(numeric_level, int):
    raise ValueError(
      f"Invalid log level '{log_level}'. Valid levels: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )
  
  try:
    # Configure root logger
    logging.basicConfig(
      level=numeric_level,
      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
      datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Get the boilerplates logger and set its level
    logger = logging.getLogger('boilerplates')
    logger.setLevel(numeric_level)
  except Exception as e:
    raise RuntimeError(f"Failed to configure logging: {e}")


@app.callback()
def main(
  ctx: Context,
  loglevel: Optional[str] = Option(
    "WARNING", 
    "--loglevel", 
    help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
  )
):
  """Main CLI application for managing boilerplates."""
  # Configure logging based on the provided log level
  setup_logging(loglevel)
  
  # Store log level in context for potential use by other commands
  ctx.ensure_object(dict)
  ctx.obj['loglevel'] = loglevel

def init_app():
  """Initialize the application by discovering and registering modules.
  
  Raises:
      ImportError: If critical module import operations fail
      RuntimeError: If application initialization fails
  """
  logger = logging.getLogger('boilerplates')
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
    
    # Register modules with app
    modules = registry.create_instances()
    logger.debug(f"Registering {len(modules)} discovered modules")
    
    for module in modules:
      try:
        logger.debug(f"Registering module: {module.__class__.__name__}")
        module.register_cli(app)
      except Exception as e:
        error_info = f"Registration failed for '{module.__class__.__name__}': {str(e)}"
        failed_registrations.append(error_info)
        # Log warning but don't raise exception for individual module failures
        logger.warning(error_info)
        console.print(f"[yellow]Warning:[/yellow] {error_info}")
    
    # If we have no modules registered at all, that's a critical error
    if not modules and not failed_imports:
      raise RuntimeError("No modules found to register")
    
    # Log summary
    successful_modules = len(modules) - len(failed_registrations)
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

def run():
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
    console.print("[dim]Use --loglevel DEBUG for more details[/dim]")
    sys.exit(1)

if __name__ == "__main__":
  run()
