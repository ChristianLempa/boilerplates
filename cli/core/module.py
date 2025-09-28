from __future__ import annotations

import logging
from abc import ABC
from pathlib import Path
from typing import Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table
from rich.tree import Tree
from typer import Argument, Context, Option, Typer

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

  # --------------------------
  # SECTION: Public Commands
  # --------------------------

  def list(
    self, 
    filter_name: Optional[str] = Argument(None, help="Filter templates by name (e.g., 'traefik' shows traefik.*)"),
    all_templates: bool = Option(False, "--all", "-a", help="Show all templates including sub-templates")
  ) -> list[Template]:
    """List templates with optional filtering."""
    logger.debug(f"Listing templates for module '{self.name}' with filter='{filter_name}', all={all_templates}")
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
    filtered_templates = self._filter_templates(templates, filter_name, all_templates)
    
    if filtered_templates:
      # Group templates for hierarchical display
      grouped_templates = self._group_templates(filtered_templates)
      
      logger.info(f"Listing {len(filtered_templates)} templates for module '{self.name}'")
      table = Table(title=f"{self.name.capitalize()} templates")
      table.add_column("ID", style="bold", no_wrap=True)
      table.add_column("Name")
      table.add_column("Description")
      table.add_column("Version", no_wrap=True)
      table.add_column("Library", no_wrap=True)

      for template_info in grouped_templates:
        template = template_info['template']
        indent = template_info['indent']
        name = template.metadata.name or 'Unnamed Template'
        desc = template.metadata.description or 'No description available'
        version = template.metadata.version or ''
        library = template.metadata.library or ''

        # Add indentation for sub-templates
        template_id = f"{indent}{template.id}"
        table.add_row(template_id, name, desc, version, library)

      console.print(table)
    else:
      filter_msg = f" matching '{filter_name}'" if filter_name else ""
      logger.info(f"No templates found for module '{self.name}'{filter_msg}")

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
      
      # If we have a filter, apply it
      if filter_name:
        if is_sub_template:
          # For sub-templates, check if they start with filter_name.
          if template_id.startswith(f"{filter_name}."):
            filtered.append(template)
        else:
          # For main templates, exact match
          if template_id == filter_name:
            filtered.append(template)
      else:
        # No filter - include based on all_templates flag
        if not all_templates and is_sub_template:
          continue
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
    
    # Insert sub-templates after their parents
    for sub_template in sub_templates:
      parent_name = sub_template.id.split('.')[0]
      
      # Find where to insert this sub-template
      insert_index = -1
      for i, item in enumerate(grouped):
        if item['template'].id == parent_name:
          # Find the last sub-template for this parent
          j = i + 1
          while j < len(grouped) and not grouped[j]['is_main']:
            j += 1
          insert_index = j
          break
      
      sub_name = sub_template.id.split('.', 1)[1]  # Get part after first dot
      sub_template_info = {
        'template': sub_template,
        'indent': '├─ ' if insert_index < len(grouped) - 1 else '└─ ',
        'is_main': False
      }
      
      if insert_index >= 0:
        grouped.insert(insert_index, sub_template_info)
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
    
    # Build metadata info text
    info_lines = []
    info_lines.append(f"{template.metadata.description or 'No description available'}")
    info_lines.append("")  # Empty line
    
    # Print template information with simple heading
    template_name = template.metadata.name or 'Unnamed Template'
    console.print(f"[bold blue]{template_name} ({template_id} - [cyan]{template.metadata.version or 'Not specified'}[/cyan])[/bold blue]")
    for line in info_lines:
      console.print(line)
    
    # Build the file structure tree
    file_tree = Tree("[bold blue]Template File Structure:[/bold blue]")
    
    # Create a dictionary to hold the tree nodes for directories
    # This will allow us to build a proper tree structure
    tree_nodes = {Path('.'): file_tree} # Root of the template directory

    for template_file in sorted(template.template_files, key=lambda f: f.relative_path):
        parts = template_file.relative_path.parts
        current_path = Path('.')
        current_node = file_tree

        # Build the directory path in the tree
        for part in parts[:-1]: # Iterate through directories
            current_path = current_path / part
            if current_path not in tree_nodes:
                new_node = current_node.add(f"\uf07b [bold blue]{part}[/bold blue]") # Folder icon
                tree_nodes[current_path] = new_node
                current_node = new_node
            else:
                current_node = tree_nodes[current_path]

        # Add the file to the appropriate directory node
        if template_file.file_type == 'j2':
            current_node.add(f"[green]\ue235 {template_file.relative_path.name}[/green]") # Jinja2 file icon
        elif template_file.file_type == 'static':
            current_node.add(f"[yellow]\uf15b {template_file.relative_path.name}[/yellow]") # Generic file icon
            
    # Print the file tree separately if it has content
    if file_tree.children: # Check if any files were added to the branches
        console.print() # Add spacing
        console.print(file_tree) # Print the Tree object directly

    if template.variables and template.variables.has_sections():
      console.print()  # Add spacing
      
      # Print variables heading
      console.print(f"[bold blue]Template Variables:[/bold blue]")
      
      # Create variables table
      variables_table = Table(show_header=True, header_style="bold blue")
      variables_table.add_column("Variable", style="cyan", no_wrap=True)
      variables_table.add_column("Type", style="magenta")
      variables_table.add_column("Default", style="green")
      variables_table.add_column("Description", style="white")
      variables_table.add_column("Origin", style="yellow")
      
      # Add variables grouped by section
      first_section = True
      for section_key, section in template.variables.get_sections().items():
        if section.variables:
          # Add spacing between sections (except before first section)
          if not first_section:
            variables_table.add_row("", "", "", "", "", style="dim")
          first_section = False
          
          # Check if section should be dimmed (toggle is False)
          is_dimmed = False
          
          if section.toggle:
            toggle_var = section.variables.get(section.toggle)
            if toggle_var:
              # Get the actual typed value and check if it's falsy
              try:
                toggle_value = toggle_var.get_typed_value()
                if not toggle_value:
                  is_dimmed = True
              except Exception as e:
                # Fallback to raw value check
                if not toggle_var.value:
                  is_dimmed = True
              
          # Add section header row with proper styling
          disabled_text = " (disabled)" if is_dimmed else ""
          required_text = " [yellow](required)[/yellow]" if section.required else ""
          
          if is_dimmed:
            # Use Rich markup for dimmed bold text
            header_text = f"[bold dim]{section.title}{required_text}{disabled_text}[/bold dim]"
          else:
            # Use Rich markup for bold text
            header_text = f"[bold]{section.title}{required_text}{disabled_text}[/bold]"
          
          variables_table.add_row(
            header_text,
            "", "", "", ""
          )
          
          # Add variables in this section
          for var_name, variable in section.variables.items():
            # Apply dim style to ALL variables if section toggle is False
            row_style = "dim" if is_dimmed else None
            
            # Format default value
            default_val = str(variable.value) if variable.value is not None else ""
            if variable.sensitive:
              default_val = "********"
            elif len(default_val) > 30:
              default_val = default_val[:27] + "..."
            
            variables_table.add_row(
              f"  {var_name}",
              variable.type or "str",
              default_val,
              variable.description or "",
              variable.origin or "unknown",
              style=row_style
            )
      
      console.print(variables_table)

# !SECTION