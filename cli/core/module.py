from __future__ import annotations

import logging
from abc import ABC
from pathlib import Path
from typing import Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from typer import Argument, Context, Option, Typer, Exit

from .display import DisplayManager
from .library import LibraryManager
from .prompt import PromptHandler
from .template import Template

logger = logging.getLogger(__name__)
console = Console()


# ------------------------------- 
# SECTION: Helper Functions
# ------------------------------- 

def parse_var_inputs(var_options: list[str], extra_args: list[str]) -> dict[str, Any]:
  """Parse variable inputs from --var options and extra args.
  
  Supports formats:
    --var KEY=VALUE
    --var KEY VALUE
    
  Args:
    var_options: List of variable options from CLI
    extra_args: Additional arguments that may contain values
    
  Returns:
    Dictionary of parsed variables
  """
  variables = {}
  
  # Parse --var KEY=VALUE format
  for var_option in var_options:
    if '=' in var_option:
      key, value = var_option.split('=', 1)
      variables[key] = value
    else:
      # --var KEY VALUE format - value should be in extra_args
      if extra_args:
        variables[var_option] = extra_args.pop(0)
      else:
        logger.warning(f"No value provided for variable '{var_option}'")
  
  return variables

# !SECTION

# ---------------------
# SECTION: Module Class
# ---------------------

class Module(ABC):
  """Streamlined base module that auto-detects variables from templates."""

  def __init__(self) -> None:
    if not all([self.name, self.description]):
      raise ValueError(
        f"Module {self.__class__.__name__} must define name and description"
      )
    
    logger.info(f"Initializing module '{self.name}'")
    logger.debug(f"Module '{self.name}' configuration: description='{self.description}'")
    self.libraries = LibraryManager()
    self.display = DisplayManager()

  # --------------------------
  # SECTION: Public Commands
  # --------------------------

  def list(self) -> list[Template]:
    """List all templates."""
    logger.debug(f"Listing templates for module '{self.name}'")
    templates = []

    entries = self.libraries.find(self.name, sort_results=True)
    for template_dir, library_name in entries:
      try:
        template = Template(template_dir, library_name=library_name)
        templates.append(template)
      except Exception as exc:
        logger.error(f"Failed to load template from {template_dir}: {exc}")
        continue
    
    filtered_templates = templates
    
    if filtered_templates:
      self.display.display_templates_table(
        filtered_templates,
        self.name,
        f"{self.name.capitalize()} templates"
      )
    else:
      logger.info(f"No templates found for module '{self.name}'")

    return filtered_templates

  def search(
    self,
    query: str = Argument(..., help="Search string to filter templates by ID")
  ) -> list[Template]:
    """Search for templates by ID containing the search string."""
    logger.debug(f"Searching templates for module '{self.name}' with query='{query}'")
    templates = []

    entries = self.libraries.find(self.name, sort_results=True)
    for template_dir, library_name in entries:
      try:
        template = Template(template_dir, library_name=library_name)
        templates.append(template)
      except Exception as exc:
        logger.error(f"Failed to load template from {template_dir}: {exc}")
        continue
    
    # Apply search filtering
    filtered_templates = [t for t in templates if query.lower() in t.id.lower()]
    
    if filtered_templates:
      logger.info(f"Found {len(filtered_templates)} templates matching '{query}' for module '{self.name}'")
      self.display.display_templates_table(
        filtered_templates,
        self.name,
        f"{self.name.capitalize()} templates matching '{query}'"
      )
    else:
      logger.info(f"No templates found matching '{query}' for module '{self.name}'")
      console.print(f"[yellow]No templates found matching '{query}' for module '{self.name}'[/yellow]")

    return filtered_templates


  def show(
    self,
    id: str,
    show_content: bool = False,
  ) -> None:
    """Show template details."""
    logger.debug(f"Showing template '{id}' from module '{self.name}'")
    template = self._load_template_by_id(id)

    if not template:
      logger.warning(f"Template '{id}' not found in module '{self.name}'")
      console.print(f"[red]Template '{id}' not found in module '{self.name}'[/red]")
      return
    
    # Apply config defaults (same as in generate)
    # This ensures the display shows the actual defaults that will be used
    if template.variables:
      from .config import ConfigManager
      config = ConfigManager()
      config_defaults = config.get_defaults(self.name)
      
      if config_defaults:
        logger.debug(f"Loading config defaults for module '{self.name}'")
        # Apply config defaults (this respects the variable types and validation)
        successful = template.variables.apply_defaults(config_defaults, "config")
        if successful:
          logger.debug(f"Applied config defaults for: {', '.join(successful)}")
    
    self._display_template_details(template, id)

  def generate(
    self,
    id: str = Argument(..., help="Template ID"),
    directory: Optional[str] = Argument(None, help="Output directory (defaults to template ID)"),
    interactive: bool = Option(True, "--interactive/--no-interactive", "-i/-n", help="Enable interactive prompting for variables"),
    var: Optional[list[str]] = Option(None, "--var", "-v", help="Variable override (repeatable). Use KEY=VALUE or --var KEY VALUE"),
    ctx: Context = None,
  ) -> None:
    """Generate from template.
    
    Variable precedence chain (lowest to highest):
    1. Module spec (defined in cli/modules/*.py)
    2. Template spec (from template.yaml)
    3. Config defaults (from ~/.config/boilerplates/config.yaml)
    4. CLI overrides (--var flags)
    
    Examples:
        # Generate to directory named after template
        cli compose generate traefik
        
        # Generate to custom directory
        cli compose generate traefik my-proxy
        
        # Generate with variables
        cli compose generate traefik --var traefik_enabled=false
    """

    logger.info(f"Starting generation for template '{id}' from module '{self.name}'")
    template = self._load_template_by_id(id)

    # Apply config defaults (precedence: config > template > module)
    # Config only sets VALUES, not the spec structure
    if template.variables:
      from .config import ConfigManager
      config = ConfigManager()
      config_defaults = config.get_defaults(self.name)
      
      if config_defaults:
        logger.info(f"Loading config defaults for module '{self.name}'")
        # Apply config defaults (this respects the variable types and validation)
        successful = template.variables.apply_defaults(config_defaults, "config")
        if successful:
          logger.debug(f"Applied config defaults for: {', '.join(successful)}")
    
    # Apply CLI overrides (highest precedence)
    extra_args = list(ctx.args) if ctx and hasattr(ctx, "args") else []
    cli_overrides = parse_var_inputs(var or [], extra_args)
    if cli_overrides:
      logger.info(f"Received {len(cli_overrides)} variable overrides from CLI")
      if template.variables:
        successful_overrides = template.variables.apply_defaults(cli_overrides, "cli")
        if successful_overrides:
          logger.debug(f"Applied CLI overrides for: {', '.join(successful_overrides)}")

    self._display_template_details(template, id)
    console.print()

    variable_values = {}
    if interactive and template.variables:
      prompt_handler = PromptHandler()
      collected_values = prompt_handler.collect_variables(template.variables)
      if collected_values:
        variable_values.update(collected_values)
        logger.info(f"Collected {len(collected_values)} variable values from user input")

    if template.variables:
      # Use get_satisfied_values() to exclude variables from sections with unsatisfied dependencies
      variable_values.update(template.variables.get_satisfied_values())

    try:
      # Validate all variables before rendering
      if template.variables:
        template.variables.validate_all()
      
      rendered_files = template.render(template.variables)
      
      # Safety check for render result
      if not rendered_files:
        console.print("[red]Error: Template rendering returned no files[/red]")
        raise Exit(code=1)
      
      logger.info(f"Successfully rendered template '{id}'")
      
      # Determine output directory (default to template ID)
      output_dir = Path(directory) if directory else Path(id)
      
      # Check if directory exists and is not empty
      dir_exists = output_dir.exists()
      dir_not_empty = dir_exists and any(output_dir.iterdir())
      
      # Check which files already exist
      existing_files = []
      if dir_exists:
        for file_path in rendered_files.keys():
          full_path = output_dir / file_path
          if full_path.exists():
            existing_files.append(full_path)
      
      # Warn if directory is not empty (both interactive and non-interactive)
      if dir_not_empty:
        if interactive:
          console.print(f"\n[yellow]⚠ Warning: Directory '{output_dir}' is not empty.[/yellow]")
          if existing_files:
            console.print(f"[yellow]  {len(existing_files)} file(s) will be overwritten.[/yellow]")
          
          if not Confirm.ask(f"Continue and potentially overwrite files in '{output_dir}'?", default=False):
            console.print("[yellow]Generation cancelled.[/yellow]")
            return
        else:
          # Non-interactive mode: show warning but continue
          logger.warning(f"Directory '{output_dir}' is not empty")
          if existing_files:
            logger.warning(f"{len(existing_files)} file(s) will be overwritten")
      
      # Display file generation confirmation in interactive mode
      if interactive:
        self.display.display_file_generation_confirmation(
          output_dir, 
          rendered_files, 
          existing_files if existing_files else None
        )
        
        # Final confirmation (only if we didn't already ask about overwriting)
        if not dir_not_empty:
          if not Confirm.ask("Generate these files?", default=True):
            console.print("[yellow]Generation cancelled.[/yellow]")
            return
      
      # Create the output directory if it doesn't exist
      output_dir.mkdir(parents=True, exist_ok=True)

      # Write rendered files to the output directory
      for file_path, content in rendered_files.items():
        full_path = output_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
          f.write(content)
        console.print(f"[green]Generated file: {file_path}[/green]")
      
      console.print(f"\n[green]✓ Template generated successfully in '{output_dir}'[/green]")
      logger.info(f"Template written to directory: {output_dir}")
      
      # Display next steps if provided in template metadata
      if template.metadata.next_steps:
        self.display.display_next_steps(template.metadata.next_steps, variable_values)

    except Exception as e:
      logger.error(f"Error rendering template '{id}': {e}")
      console.print(f"[red]Error generating template: {e}[/red]")
      # Stop execution without letting Typer/Click print the exception again.
      raise Exit(code=1)

  # --------------------------
  # SECTION: Config Commands
  # --------------------------

  def config_get(
    self,
    var_name: Optional[str] = Argument(None, help="Variable name to get (omit to show all defaults)"),
  ) -> None:
    """Get default value(s) for this module.
    
    Examples:
        # Get all defaults for module
        cli compose defaults get
        
        # Get specific variable default
        cli compose defaults get service_name
    """
    from .config import ConfigManager
    config = ConfigManager()
    
    if var_name:
      # Get specific variable default
      value = config.get_default_value(self.name, var_name)
      if value is not None:
        console.print(f"[green]{var_name}[/green] = [yellow]{value}[/yellow]")
      else:
        console.print(f"[red]No default set for variable '{var_name}' in module '{self.name}'[/red]")
    else:
      # Show all defaults (flat list)
      defaults = config.get_defaults(self.name)
      if defaults:
        console.print(f"[bold]Config defaults for module '{self.name}':[/bold]\n")
        for var_name, var_value in defaults.items():
          console.print(f"  [green]{var_name}[/green] = [yellow]{var_value}[/yellow]")
      else:
        console.print(f"[yellow]No defaults configured for module '{self.name}'[/yellow]")

  def config_set(
    self,
    var_name: str = Argument(..., help="Variable name to set default for"),
    value: str = Argument(..., help="Default value"),
  ) -> None:
    """Set a default value for a variable.
    
    This only sets the DEFAULT VALUE, not the variable spec.
    The variable must be defined in the module or template spec.
    
    Examples:
        # Set default value
        cli compose defaults set service_name my-awesome-app
        
        # Set author for all compose templates
        cli compose defaults set author "Christian Lempa"
    """
    from .config import ConfigManager
    config = ConfigManager()
    
    # Set the default value
    config.set_default_value(self.name, var_name, value)
    console.print(f"[green] Set default:[/green] [cyan]{var_name}[/cyan] = [yellow]{value}[/yellow]")
    console.print(f"\n[dim]This will be used as the default value when generating templates with this module.[/dim]")

  def config_remove(
    self,
    var_name: str = Argument(..., help="Variable name to remove"),
  ) -> None:
    """Remove a specific default variable value.
    
    Examples:
        # Remove a default value
        cli compose defaults remove service_name
    """
    from .config import ConfigManager
    config = ConfigManager()
    defaults = config.get_defaults(self.name)
    
    if not defaults:
      console.print(f"[yellow]No defaults configured for module '{self.name}'[/yellow]")
      return
    
    if var_name in defaults:
      del defaults[var_name]
      config.set_defaults(self.name, defaults)
      console.print(f"[green] Removed default for '{var_name}'[/green]")
    else:
      console.print(f"[red]No default found for variable '{var_name}'[/red]")

  def config_clear(
    self,
    var_name: Optional[str] = Argument(None, help="Variable name to clear (omit to clear all defaults)"),
    force: bool = Option(False, "--force", "-f", help="Skip confirmation prompt"),
  ) -> None:
    """Clear default value(s) for this module.
    
    Examples:
        # Clear specific variable default
        cli compose defaults clear service_name
        
        # Clear all defaults for module
        cli compose defaults clear --force
    """
    from .config import ConfigManager
    config = ConfigManager()
    defaults = config.get_defaults(self.name)
    
    if not defaults:
      console.print(f"[yellow]No defaults configured for module '{self.name}'[/yellow]")
      return
    
    if var_name:
      # Clear specific variable
      if var_name in defaults:
        del defaults[var_name]
        config.set_defaults(self.name, defaults)
        console.print(f"[green] Cleared default for '{var_name}'[/green]")
      else:
        console.print(f"[red]No default found for variable '{var_name}'[/red]")
    else:
      # Clear all defaults
      if not force:
        console.print(f"[bold yellow]  Warning:[/bold yellow] This will clear ALL defaults for module '[cyan]{self.name}[/cyan]'")
        console.print()
        # Show what will be cleared
        for var_name, var_value in defaults.items():
          console.print(f"  [green]{var_name}[/green] = [yellow]{var_value}[/yellow]")
        console.print()
        if not Confirm.ask(f"[bold red]Are you sure?[/bold red]", default=False):
          console.print("[green]Operation cancelled.[/green]")
          return
      
      config.clear_defaults(self.name)
      console.print(f"[green] Cleared all defaults for module '{self.name}'[/green]")

  def config_list(self) -> None:
    """Display the defaults for this specific module in YAML format.
    
    Examples:
        # Show the defaults for the current module
        cli compose defaults list
    """
    from .config import ConfigManager
    import yaml
    
    config = ConfigManager()
    
    # Get only the defaults for this module
    defaults = config.get_defaults(self.name)
    
    if not defaults:
      console.print(f"[yellow]No configuration found for module '{self.name}'[/yellow]")
      console.print(f"\n[dim]Config file location: {config.get_config_path()}[/dim]")
      return
    
    # Create a minimal config structure with only this module's defaults
    module_config = {
      "defaults": {
        self.name: defaults
      }
    }
    
    # Convert config to YAML string
    yaml_output = yaml.dump(module_config, default_flow_style=False, sort_keys=False)
    
    console.print(f"[bold]Configuration for module:[/bold] [cyan]{self.name}[/cyan]")
    console.print(f"[dim]Config file: {config.get_config_path()}[/dim]\n")
    console.print(Panel(yaml_output, title=f"{self.name.capitalize()} Config", border_style="blue"))

  def validate(
    self,
    template_id: str = Argument(None, help="Template ID to validate (if omitted, validates all templates)"),
    verbose: bool = Option(False, "--verbose", "-v", help="Show detailed validation information")
  ) -> None:
    """Validate templates for Jinja2 syntax errors and undefined variables.
    
    Examples:
        # Validate all templates in this module
        cli compose validate
        
        # Validate a specific template
        cli compose validate gitlab
        
        # Validate with verbose output
        cli compose validate --verbose
    """
    from rich.table import Table
    
    if template_id:
      # Validate a specific template
      try:
        template = self._load_template_by_id(template_id)
        console.print(f"[bold]Validating template:[/bold] [cyan]{template_id}[/cyan]\n")
        
        try:
          # Trigger validation by accessing used_variables
          _ = template.used_variables
          # Trigger variable definition validation by accessing variables
          _ = template.variables
          console.print(f"[green] Template '{template_id}' is valid[/green]")
          
          if verbose:
            console.print(f"\n[dim]Template path: {template.template_dir}[/dim]")
            console.print(f"[dim]Found {len(template.used_variables)} variables[/dim]")
        except ValueError as e:
          console.print(f"[red] Validation failed for '{template_id}':[/red]")
          console.print(f"\n{e}")
          raise Exit(code=1)
          
      except Exception as e:
        console.print(f"[red]Error loading template '{template_id}': {e}[/red]")
        raise Exit(code=1)
    else:
      # Validate all templates
      console.print(f"[bold]Validating all {self.name} templates...[/bold]\n")
      
      entries = self.libraries.find(self.name, sort_results=True)
      total = len(entries)
      valid_count = 0
      invalid_count = 0
      errors = []
      
      for template_dir, library_name in entries:
        template_id = template_dir.name
        try:
          template = Template(template_dir, library_name=library_name)
          # Trigger validation
          _ = template.used_variables
          _ = template.variables
          valid_count += 1
          if verbose:
            console.print(f"[green][/green] {template_id}")
        except ValueError as e:
          invalid_count += 1
          errors.append((template_id, str(e)))
          if verbose:
            console.print(f"[red][/red] {template_id}")
        except Exception as e:
          invalid_count += 1
          errors.append((template_id, f"Load error: {e}"))
          if verbose:
            console.print(f"[yellow]?[/yellow] {template_id}")
      
      # Summary
      console.print(f"\n[bold]Validation Summary:[/bold]")
      summary_table = Table(show_header=False, box=None, padding=(0, 2))
      summary_table.add_column(style="bold")
      summary_table.add_column()
      summary_table.add_row("Total templates:", str(total))
      summary_table.add_row("[green]Valid:[/green]", str(valid_count))
      summary_table.add_row("[red]Invalid:[/red]", str(invalid_count))
      console.print(summary_table)
      
      # Show errors if any
      if errors:
        console.print(f"\n[bold red]Validation Errors:[/bold red]")
        for template_id, error_msg in errors:
          console.print(f"\n[yellow]Template:[/yellow] [cyan]{template_id}[/cyan]")
          console.print(f"[dim]{error_msg}[/dim]")
        raise Exit(code=1)
      else:
        console.print(f"\n[green] All templates are valid![/green]")

  # !SECTION

  # ------------------------------
  # SECTION: CLI Registration
  # ------------------------------

  @classmethod
  def register_cli(cls, app: Typer) -> None:
    """Register module commands with the main app."""
    logger.debug(f"Registering CLI commands for module '{cls.name}'")
    
    module_instance = cls()
    
    module_app = Typer(help=cls.description)
    
    module_app.command("list")(module_instance.list)
    module_app.command("search")(module_instance.search)
    module_app.command("show")(module_instance.show)
    module_app.command("validate")(module_instance.validate)
    
    module_app.command(
      "generate", 
      context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
    )(module_instance.generate)
    
    # Add defaults commands (simplified - only manage default values)
    defaults_app = Typer(help="Manage default values for template variables")
    defaults_app.command("get", help="Get default value(s)")(module_instance.config_get)
    defaults_app.command("set", help="Set a default value")(module_instance.config_set)
    defaults_app.command("remove", help="Remove a specific default value")(module_instance.config_remove)
    defaults_app.command("clear", help="Clear default value(s)")(module_instance.config_clear)
    defaults_app.command("list", help="Display the config for this module in YAML format")(module_instance.config_list)
    module_app.add_typer(defaults_app, name="defaults")
    
    app.add_typer(module_app, name=cls.name, help=cls.description)
    logger.info(f"Module '{cls.name}' CLI commands registered")

  # !SECTION



  # --------------------------
  # SECTION: Private Methods
  # --------------------------

  def _load_template_by_id(self, template_id: str) -> Template:
    result = self.libraries.find_by_id(self.name, template_id)
    if not result:
      logger.debug(f"Template '{template_id}' not found in module '{self.name}'")
      raise FileNotFoundError(f"Template '{template_id}' not found in module '{self.name}'")

    template_dir, library_name = result
    
    try:
      return Template(template_dir, library_name=library_name)
    except (ValueError, FileNotFoundError) as exc:
      raise FileNotFoundError(f"Template '{template_id}' validation failed in module '{self.name}'") from exc
    except Exception as exc:
      logger.error(f"Failed to load template from {template_dir}: {exc}")
      raise FileNotFoundError(f"Template '{template_id}' could not be loaded in module '{self.name}'") from exc

  def _display_template_details(self, template: Template, template_id: str) -> None:
    """Display template information panel and variables table."""
    self.display.display_template_details(template, template_id)

# !SECTION
