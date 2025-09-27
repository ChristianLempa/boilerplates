from __future__ import annotations

from abc import ABC
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
from typer import Typer, Option, Argument, Context
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .library import LibraryManager
from .template import Template
from .prompt import PromptHandler

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
  
  name: str | None = None
  description: str | None = None  
  files: list[str] | None = None

  def __init__(self) -> None:
    if not all([self.name, self.description, self.files]):
      raise ValueError(
        f"Module {self.__class__.__name__} must define name, description, and files"
      )
    
    logger.info(f"Initializing module '{self.name}'")
    logger.debug(f"Module '{self.name}' configuration: files={self.files}, description='{self.description}'")
    self.libraries = LibraryManager()

  # --------------------------
  # SECTION: Public Commands
  # --------------------------

  def list(self) -> list[Template]:
    """List all templates."""
    logger.debug(f"Listing templates for module '{self.name}'")
    templates = []

    entries = self.libraries.find(self.name, self.files, sort_results=True)
    for template_dir, library_name in entries:
      # Find the first matching template file
      template_file = None
      for file_name in self.files:
        candidate = template_dir / file_name
        if candidate.exists():
          template_file = candidate
          break
      
      if template_file:
        try:
          template = Template(template_file, library_name=library_name)
          templates.append(template)
        except Exception as exc:
          logger.error(f"Failed to load template from {template_file}: {exc}")
          continue
    
    if templates:
      logger.info(f"Listing {len(templates)} templates for module '{self.name}'")
      table = Table(title=f"{self.name.capitalize()} templates")
      table.add_column("ID", style="bold", no_wrap=True)
      table.add_column("Name")
      table.add_column("Description")
      table.add_column("Version", no_wrap=True)
      table.add_column("Tags")
      table.add_column("Library", no_wrap=True)

      for template in templates:
        name = template.metadata.name or 'Unnamed Template'
        desc = template.metadata.description or 'No description available'
        version = template.metadata.version or ''
        tags_list = template.metadata.tags or []
        tags = ", ".join(tags_list) if isinstance(tags_list, list) else str(tags_list)
        library = template.metadata.library or ''
        table.add_row(template.id, name, desc, version, tags, library)

      console.print(table)
    else:
      logger.info(f"No templates found for module '{self.name}'")

    return templates

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
    out: Optional[Path] = Option(None, "--out", "-o"),
    interactive: bool = Option(True, "--interactive/--no-interactive", "-i/-n", help="Enable interactive prompting for variables"),
    var: Optional[list[str]] = Option(None, "--var", "-v", help="Variable override (repeatable). Use KEY=VALUE or --var KEY VALUE"),
    ctx: Context = None,
  ) -> None:
    """Generate from template.

    Supports variable overrides via:
      --var KEY=VALUE
      --var KEY VALUE
    """

    logger.info(f"Starting generation for template '{id}' from module '{self.name}'")
    template = self._load_template_by_id(id)

    # Build variable overrides from Typer-collected options and any extra args BEFORE displaying template
    extra_args = []
    try:
      if ctx is not None and hasattr(ctx, "args"):
        extra_args = list(ctx.args)
    except Exception:
      extra_args = []

    cli_overrides = parse_var_inputs(var or [], extra_args)
    if cli_overrides:
      logger.info(f"Received {len(cli_overrides)} variable overrides from CLI")
      # Apply CLI overrides to template variables before display
      if template.variables:
        successful_overrides = template.variables.apply_overrides(cli_overrides, " -> cli")
        if successful_overrides:
          logger.debug(f"Applied CLI overrides for: {', '.join(successful_overrides)}")

    # Show template details with CLI overrides already applied
    self._display_template_details(template, id)
    console.print()  # Add spacing before variable collection

    # Collect variable values interactively if enabled
    variable_values = {}
    if interactive and template.variables:
      prompt_handler = PromptHandler()
      
      # Collect values with simplified sectioned flow
      collected_values = prompt_handler.collect_variables(template.variables)
      
      if collected_values:
        variable_values.update(collected_values)
        logger.info(f"Collected {len(collected_values)} variable values from user input")

    # CLI overrides are already applied to the template variables, so collect all current values
    # This includes defaults, interactive changes, and CLI overrides
    if template.variables:
      variable_values.update(template.variables.get_all_values())

    # Render template with collected values
    try:
      rendered_content = template.render(variable_values)
      logger.info(f"Successfully rendered template '{id}'")
      
      # Output handling
      if out:
        # Write to specified file
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, 'w', encoding='utf-8') as f:
          f.write(rendered_content)
        console.print(f"[green]Generated template to: {out}[/green]")
        logger.info(f"Template written to file: {out}")
      else:
        # Output to stdout
        console.print("\n\n[bold blue]Generated Template:[/bold blue]")
        console.print("─" * 50)
        console.print(rendered_content)
        logger.info("Template output to stdout")
        
    except Exception as e:
      logger.error(f"Error rendering template '{id}': {str(e)}")
      console.print(f"[red]Error generating template: {str(e)}[/red]")
      raise

  # !SECTION

  # ------------------------------
  # SECTION: CLI Registration
  # ------------------------------

  @classmethod
  def register_cli(cls, app: Typer) -> None:
    """Register module commands with the main app."""
    logger.debug(f"Registering CLI commands for module '{cls.name}'")
    
    # Create a module instance
    module_instance = cls()
    
    # Create subapp for this module
    module_app = Typer(help=cls.description)
    
    # Register commands directly on the instance
    module_app.command("list")(module_instance.list)
    module_app.command("show")(module_instance.show)
    
    # Generate command needs special handling for context
    module_app.command(
      "generate", 
      context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
    )(module_instance.generate)
    
    # Add the module subapp to main app
    app.add_typer(module_app, name=cls.name, help=cls.description)
    logger.info(f"Module '{cls.name}' CLI commands registered")

  # !SECTION

  # --------------------------
  # SECTION: Private Methods
  # --------------------------

  def _load_template_by_id(self, template_id: str) -> Template:
    result = self.libraries.find_by_id(self.name, self.files, template_id)
    if not result:
      logger.debug(f"Template '{template_id}' not found in module '{self.name}'")
      raise FileNotFoundError(f"Template '{template_id}' not found in module '{self.name}'")

    template_dir, library_name = result
    
    # Find the first matching template file
    template_file = None
    for file_name in self.files:
      candidate = template_dir / file_name
      if candidate.exists():
        template_file = candidate
        break
    
    if not template_file:
      raise FileNotFoundError(f"Template directory '{template_dir}' missing expected files {self.files}")
    
    try:
      return Template(template_file, library_name=library_name)
    except ValueError as exc:
      # FIXME: Refactor error handling chain to avoid redundant exception wrapping
      # ValueError (like validation errors) already logged - just re-raise with context
      raise FileNotFoundError(f"Template '{template_id}' validation failed in module '{self.name}'") from exc
    except Exception as exc:
      logger.error(f"Failed to load template from {template_file}: {exc}")
      raise FileNotFoundError(f"Template file for '{template_id}' not found in module '{self.name}'") from exc

  def _display_template_details(self, template: Template, template_id: str) -> None:
    """Display template information panel and variables table.
    
    Args:
      template: The Template object to display
      template_id: The template ID for display purposes
    """
    # Show template info panel
    console.print(Panel(
      f"[bold]{template.metadata.name or 'Unnamed Template'}[/bold]\n\n{template.metadata.description or 'No description available'}", 
      title=f"Template: {template_id}", 
      subtitle=f"Module: {self.name}"
    ))
    
    # Show variables table if any variables exist
    if template.variables and template.variables._set:
      console.print()  # Add spacing
      
      # Create variables table
      variables_table = Table(title="Template Variables", show_header=True, header_style="bold blue")
      variables_table.add_column("Variable", style="cyan", no_wrap=True)
      variables_table.add_column("Type", style="magenta")
      variables_table.add_column("Default", style="green")
      variables_table.add_column("Description", style="white")
      variables_table.add_column("Origin", style="yellow")
      
      # Add variables grouped by section
      first_section = True
      for section_key, section in template.variables._set.items():
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
            if len(default_val) > 30:
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

