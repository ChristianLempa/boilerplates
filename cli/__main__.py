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
from typer import Typer, Option, Context
import cli.modules
from cli.core.registry import registry

app = Typer(no_args_is_help=True)

# Set up logging
logging.basicConfig(
    level=logging.CRITICAL,
    format='[%(levelname)s] %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger('boilerplates')

@app.callback()
def main(
    ctx: Context,
    debug: bool = Option(False, "--debug", help="Enable debug logging")
):
  """Main CLI application for managing boilerplates."""
  # Enable debug logging if requested
  if debug:
    logging.getLogger('boilerplates').setLevel(logging.DEBUG)
    logger.debug("Debug logging enabled")
  
  logger.debug("Starting boilerplates CLI application")

def init_app():
  """Initialize the application by discovering and registering modules."""
  try:
    # Auto-discover and import all modules
    modules_path = Path(cli.modules.__file__).parent
    logger.debug(f"Discovering modules in: {modules_path}")
    
    for finder, name, ispkg in pkgutil.iter_modules([str(modules_path)]):
      if not ispkg and not name.startswith('_') and name != 'base':
        try:
          logger.debug(f"Importing module: {name}")
          importlib.import_module(f"cli.modules.{name}")
        except ImportError as e:
          logger.warning(f"Could not import {name}: {e}")
    
    # Register modules with app
    logger.debug(f"Registering {len(registry.create_instances())} modules")
    for module in registry.create_instances():
      try:
        logger.debug(f"Registering module: {module.__class__.__name__}")
        module.register_cli(app)
      except Exception as e:
        logger.error(f"Error registering {module.__class__.__name__}: {e}")
    
  except Exception as e:
    logger.error(f"Application initialization error: {e}")
    exit(1)

def run():
  """Run the CLI application."""
  init_app()
  app()

if __name__ == "__main__":
  run()
