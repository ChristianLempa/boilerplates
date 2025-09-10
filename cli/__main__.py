#!/usr/bin/env python3
"""
Main entry point for the Boilerplates CLI application.
This file serves as the primary executable when running the CLI.
"""
import importlib
import pkgutil
import sys
from pathlib import Path
from typer import Typer, Context
from rich.console import Console
import cli.modules
from cli.core.registry import registry
from cli.core.exceptions import BoilerplateError

app = Typer(no_args_is_help=True)
console = Console()

@app.callback()
def main(ctx: Context):
  """Main CLI application for managing boilerplates."""
  pass

def init_app():
  """Initialize the application by discovering and registering modules."""
  try:
    # Auto-discover and import all modules
    modules_path = Path(cli.modules.__file__).parent
    
    for finder, name, ispkg in pkgutil.iter_modules([str(modules_path)]):
      if not ispkg and not name.startswith('_') and name != 'base':
        try:
          importlib.import_module(f"cli.modules.{name}")
        except ImportError as e:
          # Silently skip modules that can't be imported
          pass
    
    # Register modules with app
    for module in registry.create_instances():
      try:
        module.register_cli(app)
      except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Error registering {module.__class__.__name__}: {e}")
    
  except Exception as e:
    console.print(f"[bold red]Application initialization error:[/bold red] {e}")
    sys.exit(1)

def run():
  """Run the CLI application."""
  try:
    init_app()
    app()
  except BoilerplateError as e:
    # Handle our custom exceptions cleanly without stack trace
    console.print(f"[bold red]Error:[/bold red] {e}")
    sys.exit(1)
  except KeyboardInterrupt:
    # Handle Ctrl+C gracefully
    console.print("\n[yellow]Operation cancelled by user[/yellow]")
    sys.exit(130)
  except Exception as e:
    # Handle unexpected errors - show simplified message
    console.print(f"[bold red]Unexpected error:[/bold red] {e}")
    console.print("[dim]Run with --debug for more details[/dim]")
    sys.exit(1)

if __name__ == "__main__":
  run()
