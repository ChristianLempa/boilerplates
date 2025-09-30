from __future__ import annotations

import logging
from abc import ABC
from pathlib import Path
from typing import Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from typer import Argument, Context, Option, Typer

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
    
    self._display_template_details(template, id)

  def generate(
    self,
    id: str = Argument(..., help="Template ID"),
    out: Optional[Path] = Option(None, "--out", "-o", help="Output directory"),
    interactive: bool = Option(True, "--interactive/--no-interactive", "-i/-n", help="Enable interactive prompting for variables"),
    var: Optional[list[str]] = Option(None, "--var", "-v", help="Variable override (repeatable). Use KEY=VALUE or --var KEY VALUE"),
    ctx: Context = None,
  ) -> None:
    """Generate from template."""

    logger.info(f"Starting generation for template '{id}' from module '{self.name}'")
    template = self._load_template_by_id(id)

    extra_args = list(ctx.args) if ctx and hasattr(ctx, "args") else []
    cli_overrides = parse_var_inputs(var or [], extra_args)
    if cli_overrides:
      logger.info(f"Received {len(cli_overrides)} variable overrides from CLI")
      if template.variables:
        successful_overrides = template.variables.apply_overrides(cli_overrides, " -> cli")
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
      raise

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