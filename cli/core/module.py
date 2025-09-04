from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, List
import logging
from typer import Typer, Option, Argument
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.syntax import Syntax
from rich.table import Table
from io import StringIO
from rich import box

from .library import LibraryManager
from .prompt import PromptHandler
from .template import Template
from .variables import VariableGroup, VariableManager
from .config import ConfigManager

logger = logging.getLogger('boilerplates')


class Module(ABC):
  """
  Base Module for all CLI Commands.
  
  This class now uses VariableManager for centralized variable management,
  providing better organization and more advanced variable operations.
  """

  def __init__(self, name: str, description: str, files: list[str], vars: list[VariableGroup] = None):
    self.name = name
    self.description = description
    self.files = files
    
    # Initialize ConfigManager and VariableManager with it
    self.config_manager = ConfigManager()
    self.variable_manager = VariableManager(vars if vars is not None else [], self.config_manager)

    self.app = Typer()
    self.libraries = LibraryManager()  # Initialize library manager
    
    # Validate that required attributes are set
    if not self.name:
      raise ValueError("Module name must be set")
    if not self.description:
      raise ValueError("Module description must be set")
    if not isinstance(self.files, list) or len(self.files) == 0:
      raise ValueError("Module files must be a non-empty list")
    if not all(isinstance(var, VariableGroup) for var in (vars if vars is not None else [])):
      raise ValueError("Module vars must be a list of VariableGroup instances")
  
  @property
  def vars(self) -> List[VariableGroup]:
    """Backward compatibility property for accessing variable groups."""
    return self.variable_manager.variable_groups
  
  def get_variable_summary(self) -> Dict[str, Any]:
    """Get a summary of all variables managed by this module."""
    return self.variable_manager.get_summary()
  
  def add_variable_group(self, group: VariableGroup) -> None:
    """Add a new variable group to this module."""
    self.variable_manager.add_group(group)
  
  def has_variable(self, name: str) -> bool:
    """Check if this module has a variable with the given name."""
    return self.variable_manager.has_variable(name)

  def list(self):
    """List all templates in the module."""
    logger.debug(f"Listing templates for module: {self.name}")
    templates = self.libraries.find(self.name, self.files, sorted=True)
    logger.debug(f"Found {len(templates)} templates")
    
    for template in templates:
      print(f"{template.id} ({template.name}, {template.directory})")
    return templates

  def show(self, id: str = Argument(..., metavar="template", help="The template to show details for")):
    """Show details about a template"""
    logger.debug(f"Showing details for template: {id} in module: {self.name}")

    template = self.libraries.find_by_id(module_name=self.name, files=self.files, template_id=id)
    
    if not template:
      logger.error(f"Template with ID '{id}' not found")
      print(f"Template with ID '{id}' not found.")
      return

    console = Console()
    
    # Build title with version if available
    version_suffix = f" v{template.version}" if template.version else ""
    title = f"[bold magenta]{template.name} ({template.id}{version_suffix})[/bold magenta]"
    
    # Print header
    console.print(title)
    console.print(f"[dim white]{template.description}[/dim white]")
    console.print()
    
    # Build and print metadata fields
    metadata = []
    if template.author:
      metadata.append(f"Author: [cyan]{template.author}[/cyan]")
    if template.date:
      metadata.append(f"Date: [cyan]{template.date}[/cyan]")
    if template.tags:
      metadata.append(f"Tags: [cyan]{', '.join(template.tags)}[/cyan]")
    
    # Find variable groups used by this template
    template_var_groups = [
      group.name for group in self.variable_manager.variable_groups
      if any(var.name in template.vars for var in group.vars)
    ]
    
    if template_var_groups:
      metadata.append(f"Functions: [cyan]{', '.join(template_var_groups)}[/cyan]")
    
    # Print all metadata
    for item in metadata:
      console.print(item)
    
    # Template content
    if template.content:
      console.print(f"\n{template.content}")


  def generate(self, id: str = Argument(..., metavar="template", help="The template to generate from"), out: Optional[Path] = Option(None, "--out", "-o", help="Output file to save the generated template")):
    """Generate a new template with complex variable prompting logic"""
    logger.info(f"Generating template '{id}' from module '{self.name}'")
    
    # Step 1: Find template by ID
    logger.debug(f"Step 1: Finding template by ID: {id}")
    template = self.libraries.find_by_id(module_name=self.name, files=self.files, template_id=id)
    if not template:
      logger.error(f"Template '{id}' not found")
      print(f"Template '{id}' not found.")
      return
    
    logger.debug(f"Template found: {template.name} with {len(template.vars)} variables")
    
    # Step 2: Validate if the variables in the template are valid ones
    logger.debug(f"Step 2: Validating template variables: {template.vars}")
    success, missing = self.variable_manager.validate_template_variables(template.vars)
    if not success:
      logger.error(f"Template '{id}' has invalid variables: {missing}")
      print(f"Template '{id}' has invalid variables: {missing}")
      return
    
    logger.debug("All template variables are valid")
    
    # Step 3: Disable variables not found in template
    logger.debug(f"Step 3: Disabling variables not used by template")
    self.variable_manager.disable_variables_not_in_template(template.vars)
    logger.debug("Unused variables disabled")

    # Step 4: Resolve variable defaults with priority (module -> template -> user config)
    logger.debug(f"Step 4: Resolving variable defaults with priority")
    resolved_defaults = self.variable_manager.resolve_variable_defaults(
      self.name, 
      template.vars, 
      template.var_defaults
    )
    logger.debug(f"Resolved defaults: {resolved_defaults}")
    
    # Step 5: Match template vars with vars of the module (only enabled ones)
    logger.debug(f"Step 5: Filtering variables for template")
    filtered_vars = self.variable_manager.filter_variables_for_template(template.vars)
    logger.debug(f"Filtered variables: {list(filtered_vars.keys())}")
    
    # Step 6: Execute complex group-based prompting logic
    logger.debug(f"Step 6: Starting complex prompting logic")
    try:
      prompt = PromptHandler(filtered_vars, resolved_defaults)
      final_variable_values = prompt()
      logger.debug(f"Prompting completed with values: {final_variable_values}")
    except KeyboardInterrupt:
      logger.info("Template generation cancelled by user")
      print("\n[red]Template generation cancelled.[/red]")
      return
    except Exception as e:
      logger.error(f"Error during prompting: {e}")
      print(f"Error during variable prompting: {e}")
      return
    
    # Step 7: Generate template with final variable values
    logger.debug(f"Step 7: Generating template with final values")
    try:
      generated_content = template.render(final_variable_values)
      logger.debug("Template rendered successfully")
    except Exception as e:
      logger.error(f"Error rendering template: {e}")
      print(f"Error rendering template: {e}")
      return
    
    # Step 8: Output the generated content
    logger.debug(f"Step 8: Outputting generated content")
    if out:
      try:
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, 'w', encoding='utf-8') as f:
          f.write(generated_content)
        logger.info(f"Template generated and saved to {out}")
        print(f"✅ Template generated and saved to {out}")
      except Exception as e:
        logger.error(f"Error saving to file {out}: {e}")
        print(f"Error saving to file {out}: {e}")
    else:
      print("\n" + "="*60)
      print("📄 Generated Template Content:")
      print("="*60)
      print(generated_content)
  
  def register(self, app: Typer):
    self.app.command()(self.list)
    self.app.command()(self.show)
    self.app.command()(self.generate)
    app.add_typer(self.app, name=self.name, help=self.description, no_args_is_help=True)
