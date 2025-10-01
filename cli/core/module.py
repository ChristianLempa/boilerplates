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

  def list(
    self, 
    all_templates: bool = Option(False, "--all", "-a", help="Show all templates including sub-templates")
  ) -> list[Template]:
    """List all templates."""
    logger.debug(f"Listing templates for module '{self.name}' with all={all_templates}")
    templates = []

    entries = self.libraries.find(self.name, sort_results=True)
    for template_dir, library_name in entries:
      try:
        template = Template(template_dir, library_name=library_name)
        templates.append(template)
      except Exception as exc:
        logger.error(f"Failed to load template from {template_dir}: {exc}")
        continue
    
    # Apply filtering logic
    filtered_templates = self._filter_templates(templates, None, all_templates)
    
    if filtered_templates:
      # Group templates for hierarchical display
      grouped_templates = self._group_templates(filtered_templates)
      
      self.display.display_templates_table(
        grouped_templates,
        self.name,
        f"{self.name.capitalize()} templates"
      )
    else:
      logger.info(f"No templates found for module '{self.name}'")

    return filtered_templates

  def search(
    self,
    query: str = Argument(..., help="Search string to filter templates by ID"),
    all_templates: bool = Option(False, "--all", "-a", help="Show all templates including sub-templates")
  ) -> list[Template]:
    """Search for templates by ID containing the search string."""
    logger.debug(f"Searching templates for module '{self.name}' with query='{query}', all={all_templates}")
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
    filtered_templates = self._search_templates(templates, query, all_templates)
    
    if filtered_templates:
      # Group templates for hierarchical display
      grouped_templates = self._group_templates(filtered_templates)
      
      logger.info(f"Found {len(filtered_templates)} templates matching '{query}' for module '{self.name}'")
      self.display.display_templates_table(
        grouped_templates,
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
    out: Optional[Path] = Option(None, "--out", "-o", help="Output directory"),
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
      variable_values.update(template.variables.get_all_values())

    try:
      # Validate all variables before rendering
      if template.variables:
        template.variables.validate_all()
      
      rendered_files = template.render(template.variables)
      logger.info(f"Successfully rendered template '{id}'")
      output_dir = out or Path(".")

      # Check if the directory is empty and confirm overwrite if necessary
      if output_dir.exists() and any(output_dir.iterdir()):
        if interactive:
          if not Confirm.ask(f"Output directory '{output_dir}' is not empty. Overwrite files?", default=False):
            console.print("[yellow]Generation cancelled.[/yellow]")
            return
        else:
          logger.warning(f"Output directory '{output_dir}' is not empty. Existing files may be overwritten.")
      
      # Create the output directory if it doesn't exist
      output_dir.mkdir(parents=True, exist_ok=True)

      # Write rendered files to the output directory
      for file_path, content in rendered_files.items():
        full_path = output_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
          f.write(content)
        console.print(f"[green]Generated file: {full_path}[/green]")
      
      logger.info(f"Template written to directory: {output_dir}")

      # If no output directory was specified, print the masked content to the console
      if not out:
        console.print("\n[bold]Rendered output (sensitive values masked):[/bold]")
        masked_files = template.mask_sensitive_values(rendered_files, template.variables)
        for file_path, content in masked_files.items():
          console.print(Panel(content, title=file_path, border_style="green"))

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
    """Get config default value(s) for this module.
    
    Examples:
        # Get all defaults for module
        cli compose config get
        
        # Get specific variable default
        cli compose config get service_name
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
    """Set a default value for a variable in config.
    
    This only sets the DEFAULT VALUE, not the variable spec.
    The variable must be defined in the module or template spec.
    
    Examples:
        # Set default value
        cli compose config set service_name my-awesome-app
        
        # Set author for all compose templates
        cli compose config set author "Christian Lempa"
    """
    from .config import ConfigManager
    config = ConfigManager()
    
    # Set the default value
    config.set_default_value(self.name, var_name, value)
    console.print(f"[green]✓ Set default:[/green] [cyan]{var_name}[/cyan] = [yellow]{value}[/yellow]")
    console.print(f"\n[dim]This will be used as the default value when generating templates with this module.[/dim]")

  def config_remove(
    self,
    var_name: str = Argument(..., help="Variable name to remove"),
  ) -> None:
    """Remove a specific default variable value.
    
    Examples:
        # Remove a default value
        cli compose config remove service_name
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
      console.print(f"[green]✓ Removed default for '{var_name}'[/green]")
    else:
      console.print(f"[red]No default found for variable '{var_name}'[/red]")

  def config_clear(
    self,
    var_name: Optional[str] = Argument(None, help="Variable name to clear (omit to clear all defaults)"),
    force: bool = Option(False, "--force", "-f", help="Skip confirmation prompt"),
  ) -> None:
    """Clear config default value(s) for this module.
    
    Examples:
        # Clear specific variable default
        cli compose config clear service_name
        
        # Clear all defaults for module
        cli compose config clear --force
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
        console.print(f"[green]✓ Cleared default for '{var_name}'[/green]")
      else:
        console.print(f"[red]No default found for variable '{var_name}'[/red]")
    else:
      # Clear all defaults
      if not force:
        console.print(f"[bold yellow]⚠️  Warning:[/bold yellow] This will clear ALL defaults for module '[cyan]{self.name}[/cyan]'")
        console.print()
        # Show what will be cleared
        for var_name, var_value in defaults.items():
          console.print(f"  [green]{var_name}[/green] = [yellow]{var_value}[/yellow]")
        console.print()
        if not Confirm.ask(f"[bold red]Are you sure?[/bold red]", default=False):
          console.print("[green]Operation cancelled.[/green]")
          return
      
      config.clear_defaults(self.name)
      console.print(f"[green]✓ Cleared all defaults for module '{self.name}'[/green]")

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
    
    module_app.command(
      "generate", 
      context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
    )(module_instance.generate)
    
    # Add config commands (simplified - only manage default values)
    config_app = Typer(help="Manage default values for template variables")
    config_app.command("get", help="Get default value(s)")(module_instance.config_get)
    config_app.command("set", help="Set a default value")(module_instance.config_set)
    config_app.command("remove", help="Remove a specific default value")(module_instance.config_remove)
    config_app.command("clear", help="Clear default value(s)")(module_instance.config_clear)
    module_app.add_typer(config_app, name="config")
    
    app.add_typer(module_app, name=cls.name, help=cls.description)
    logger.info(f"Module '{cls.name}' CLI commands registered")

  # !SECTION

  # --------------------------
  # SECTION: Template Organization Methods
  # --------------------------

  def _filter_templates(self, templates: list[Template], filter_name: Optional[str], all_templates: bool) -> list[Template]:
    """Filter templates based on name and sub-template visibility."""
    filtered = []
    
    for template in templates:
      template_id = template.id
      is_sub_template = '.' in template_id
      
      # No filter - include based on all_templates flag
      if not all_templates and is_sub_template:
        continue
      filtered.append(template)
    
    return filtered
  
  def _search_templates(self, templates: list[Template], query: str, all_templates: bool) -> list[Template]:
    """Search templates by ID containing the query string."""
    filtered = []
    query_lower = query.lower()
    
    for template in templates:
      template_id = template.id
      is_sub_template = '.' in template_id
      
      # Skip sub-templates if not showing all
      if not all_templates and is_sub_template:
        continue
      
      # Check if query is contained in the template ID
      if query_lower in template_id.lower():
        filtered.append(template)
    
    return filtered

  def _group_templates(self, templates: list[Template]) -> list[dict]:
    """Group templates hierarchically for display."""
    grouped = []
    main_templates = {}
    sub_templates = []
    
    # Separate main templates and sub-templates
    for template in templates:
      if '.' in template.id:
        sub_templates.append(template)
      else:
        main_templates[template.id] = template
        grouped.append({
          'template': template,
          'indent': '',
          'is_main': True
        })
    
    # Sort sub-templates by parent
    sub_templates.sort(key=lambda t: t.id)
    
    # Group sub-templates by parent for proper indentation
    sub_by_parent = {}
    for sub_template in sub_templates:
      parent_name = sub_template.id.split('.')[0]
      if parent_name not in sub_by_parent:
        sub_by_parent[parent_name] = []
      sub_by_parent[parent_name].append(sub_template)
    
    # Insert sub-templates after their parents with proper indentation
    for parent_name, parent_subs in sub_by_parent.items():
      # Find the parent in the grouped list
      insert_index = -1
      for i, item in enumerate(grouped):
        if item['template'].id == parent_name:
          insert_index = i + 1
          break
      
      # Add each sub-template with proper indentation
      for idx, sub_template in enumerate(parent_subs):
        is_last = (idx == len(parent_subs) - 1)
        sub_template_info = {
          'template': sub_template,
          'indent': '└─ ' if is_last else '├─ ',
          'is_main': False
        }
        
        if insert_index >= 0:
          grouped.insert(insert_index, sub_template_info)
          insert_index += 1
        else:
          # Parent not found, add at end
          grouped.append(sub_template_info)
    
    return grouped

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
