"""
Base classes and utilities for CLI modules and commands.
Provides common functionality and patterns for all modules.
"""

import logging
from abc import ABC
from typing import Optional, Set

import typer
from rich.console import Console

from .config import ConfigManager



class BaseModule(ABC):
    """Abstract base class for all CLI modules with shared commands."""
    
    def __init__(self, name: str, icon: str = "", description: str = ""):
        self.name = name
        self.icon = icon
        self.description = description
        self.console = Console()
        self.logger = logging.getLogger(f"boilerplates.module.{name}")
    
    def get_valid_variables(self) -> Set[str]:
        """
        Get the set of valid variable names for this module.
        Subclasses can override this to provide module-specific validation.
        """
        return set()
    
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
        
        # Add shared config commands
        self._add_config_commands(app)
        
        # Add module-specific commands
        self._add_module_commands(app)
        
        return app
    
    def _add_config_commands(self, app: typer.Typer) -> None:
        """
        Add shared configuration commands to the app.
        These commands are available for all modules.
        """
        config_app = typer.Typer(name="config", help="Manage module configuration")
        app.add_typer(config_app, name="config")
        
        @config_app.command("set", help="Set a configuration value")
        def set_config(
            key: str = typer.Argument(..., help="Configuration key"),
            value: str = typer.Argument(..., help="Configuration value")
        ):
            """Set a configuration value for this module."""
            # Validate that the key is a valid variable for this module
            valid_vars = self.get_valid_variables()
            if valid_vars and key not in valid_vars:
                self.console.print(f"[red]✗[/red] Invalid config key '{key}'. Valid keys are: {', '.join(sorted(valid_vars))}")
                raise typer.Exit(code=1)
            
            config_manager = ConfigManager(self.name)
            try:
                # Try to parse as JSON for complex values
                import json
                try:
                    parsed_value = json.loads(value)
                except json.JSONDecodeError:
                    parsed_value = value
                
                config_manager.set(key, parsed_value)
                self.console.print(f"[green]✓[/green] Set {self.name} config '{key}' = {parsed_value}")
            except Exception as e:
                self.console.print(f"[red]✗[/red] Failed to set config: {e}")
        
        @config_app.command("get", help="Get a configuration value")
        def get_config(
            key: str = typer.Argument(..., help="Configuration key"),
            default: Optional[str] = typer.Option(None, "--default", "-d", help="Default value if key not found")
        ):
            """Get a configuration value for this module."""
            config_manager = ConfigManager(self.name)
            value = config_manager.get(key, default)
            if value is None:
                self.console.print(f"[yellow]⚠[/yellow] Config key '{key}' not found")
                return
            
            import json
            if isinstance(value, (dict, list)):
                self.console.print(json.dumps(value, indent=2))
            else:
                self.console.print(f"{key}: {value}")
        
        @config_app.command("list", help="List all configuration values")
        def list_config():
            """List all configuration values for this module."""
            config_manager = ConfigManager(self.name)
            config = config_manager.list_all()
            if not config:
                self.console.print(f"[yellow]No configuration found for {self.name}[/yellow]")
                return
            
            from rich.table import Table
            table = Table(title=f"⚙️  {self.name.title()} Configuration", title_style="bold blue")
            table.add_column("Key", style="cyan", no_wrap=True)
            table.add_column("Value", style="green")
            
            import json
            for key, value in config.items():
                if isinstance(value, (dict, list)):
                    value_str = json.dumps(value, indent=2)
                else:
                    value_str = str(value)
                table.add_row(key, value_str)
            
            self.console.print(table)
        
        @config_app.command("delete", help="Delete a configuration value")
        def delete_config(key: str = typer.Argument(..., help="Configuration key")):
            """Delete a configuration value for this module."""
            config_manager = ConfigManager(self.name)
            if config_manager.delete(key):
                self.console.print(f"[green]✓[/green] Deleted config key '{key}'")
            else:
                self.console.print(f"[yellow]⚠[/yellow] Config key '{key}' not found")
        
        @config_app.command("variables", help="List valid configuration variables for this module")
        def list_variables():
            """List all valid configuration variables for this module."""
            valid_vars = self.get_valid_variables()
            if not valid_vars:
                self.console.print(f"[yellow]No variables defined for {self.name} module yet.[/yellow]")
                return
            
            from rich.table import Table
            table = Table(title=f"🔧 Valid {self.name.title()} Variables", title_style="bold blue")
            table.add_column("Variable Name", style="cyan", no_wrap=True)
            table.add_column("Set", style="magenta")
            table.add_column("Type", style="green")
            table.add_column("Description", style="dim")
            
            # Get detailed variable information
            if hasattr(self, '_get_variable_details'):
                var_details = self._get_variable_details()
                for var_name in sorted(valid_vars):
                    if var_name in var_details:
                        detail = var_details[var_name]
                        table.add_row(
                            var_name,
                            detail.get('set', 'unknown'),
                            detail.get('type', 'str'),
                            detail.get('display_name', '')
                        )
                    else:
                        table.add_row(var_name, 'unknown', 'str', '')
            else:
                for var_name in sorted(valid_vars):
                    table.add_row(var_name, 'unknown', 'str', '')
            
            self.console.print(table)
    
    def _add_module_commands(self, app: typer.Typer) -> None:
        """
        Override this method in subclasses to add module-specific commands.
        This is called after the shared commands are added.
        """
        pass
