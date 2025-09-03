"""
Base classes and utilities for CLI modules and commands.
Provides common functionality and patterns for all modules.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Set, Dict, Any, List, Tuple

from rich.console import Console
import typer

from .config import ConfigManager
from .helpers import find_boilerplates
from . import template, values, render



class BaseModule(ABC):
    """Abstract base class for all CLI modules with shared commands."""
    
    def __init__(self, name: str, icon: str = "", description: str = ""):
        self.name = name
        self.icon = icon
        self.description = description
        self.console = Console()
        self.logger = logging.getLogger(f"boilerplates.module.{name}")
    
    @property
    def template_paths(self) -> List[str]:
        """Return list of valid template file paths/patterns for this module.
        Override this in modules that support template generation."""
        return []
        
    @property
    def library_path(self) -> Optional[Path]:
        """Return the path to the template library for this module.
        Override this in modules that support template generation."""
        return None
        
    @property
    def variable_handler_class(self) -> Any:
        """Return the variable handler class for this module."""
        return None
        
    def get_valid_variables(self) -> Set[str]:
        """Get the set of valid variable names for this module."""
        if self.variable_handler_class:
            handler = self.variable_handler_class()
            return set(handler._declared.keys())
        return set()
        
    def process_template_content(self, content: str) -> str:
        """Process template content before rendering. Override if needed."""
        return content
        
    def get_template_syntax(self) -> str:
        """Return the syntax highlighting to use for this template type."""
        return "yaml"
    
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
        """Add module-specific commands to the app."""
        # Only add generate command if module supports templates
        if self.library_path is not None and self.template_paths:
            self._add_generate_command(app)
        self._add_custom_commands(app)
    
    def _add_custom_commands(self, app: typer.Typer) -> None:
        """Override this method in subclasses to add module-specific commands."""
        pass
    
    def _add_generate_command(self, app: typer.Typer) -> None:
        """Add the generate command to the app."""
        
        @app.command("generate", help="Generate from a template and write to --out")
        def generate(
            name: str,
            out: Optional[Path] = typer.Option(None, "--out", "-o",
                help="Output path to write rendered template (prints to stdout when omitted)"),
            values_file: Optional[Path] = typer.Option(None, "--values-file", "-f",
                help="Load values from YAML/JSON file"),
            values: Optional[List[str]] = typer.Option(None, "--values",
                help="Set values (format: key=value)")
        ):
            """Generate output from a template with optional value overrides."""
            # Find and validate template
            bps = find_boilerplates(self.library_path, self.template_paths)
            bp = next((b for b in bps if b.file_path.parent.name.lower() == name.lower()), None)
            if not bp:
                self.console.print(f"[red]Template '{name}' not found.[/red]")
                raise typer.Exit(code=1)
            
            # Get variable handler if module provides one
            var_handler = None
            if self.variable_handler_class:
                var_handler = self.variable_handler_class()
            
            # Clean and process template content
            content = self.process_template_content(bp.content)
            cleaned_content = template.clean_template_content(content)
            
            # Find variables if handler exists
            used_vars = set()
            if var_handler:
                _, used_vars = var_handler.determine_variable_sets(cleaned_content)
            
            if not used_vars:
                rendered = content
            else:
                # Validate template syntax
                is_valid, error = template.validate_template(cleaned_content, bp.file_path)
                if not is_valid:
                    self.console.print(f"[red]{error}[/red]")
                    raise typer.Exit(code=2)
                
                # Extract defaults and metadata if handler exists
                template_defaults = {}
                if var_handler:
                    template_defaults = var_handler.extract_template_defaults(cleaned_content)
                    try:
                        meta_overrides = var_handler.extract_variable_meta_overrides(content)
                        for var_name, overrides in meta_overrides.items():
                            if var_name in var_handler._declared and isinstance(overrides, dict):
                                existing = var_handler._declared[var_name][1]
                                existing.update(overrides)
                    except Exception:
                        pass
                
                # Get subscript keys and load values from all sources
                used_subscripts = set()
                if var_handler:
                    used_subscripts = var_handler.find_used_subscript_keys(content)
                
                # Load and merge values from all sources
                try:
                    merged_values = values.load_and_merge_values(
                        values_file=values_file,
                        cli_values=values,
                        config_values=ConfigManager(self.name).list_all(),
                        defaults=template_defaults
                    )
                except Exception as e:
                    self.console.print(f"[red]{str(e)}[/red]")
                    raise typer.Exit(code=1)
                
                # Collect final values and render template
                values_dict = {}
                if var_handler:
                    values_dict = var_handler.collect_values(
                        used_vars,
                        merged_values,
                        used_subscripts
                    )
                else:
                    values_dict = merged_values
                
                success, rendered, error = template.render_template(
                    cleaned_content,
                    values_dict
                )
                
                if not success:
                    self.console.print(f"[red]{error}[/red]")
                    raise typer.Exit(code=2)
            
            # Output the rendered content
            output_handler = render.RenderOutput(self.console)
            output_handler.output_rendered_content(
                rendered,
                out,
                self.get_template_syntax(),
                bp.name
            )
