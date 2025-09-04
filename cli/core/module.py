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
from .processor import VariableProcessor

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
    self.config = ConfigManager()
    self.vars = VariableManager(vars if vars is not None else [], self.config)

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

  def _validate_variables(self, variables: List[str]) -> Tuple[bool, List[str]]:
    """Validate if all template variables exist in the variable groups.
    
    Args:
        variables: List of variable names to validate
        
    Returns:
        Tuple of (success: bool, missing_variables: List[str])
    """
    missing_variables = [var for var in variables if not self.vars.has_variable(var)]
    success = len(missing_variables) == 0
    return success, missing_variables

  def _get_variable_defaults_for_template(self, template_vars: List[str]) -> Dict[str, Any]:
    """Get default values for variables used in a template.
    
    Args:
        template_vars: List of variable names used in the template
        
    Returns:
        Dictionary mapping variable names to their default values
    """
    defaults = {}
    for group in self.vars.variable_groups:
      for variable in group.vars:
        if variable.name in template_vars and variable.value is not None:
          defaults[variable.name] = variable.value
    return defaults

  def _get_groups_with_template_vars(self, template_vars: List[str]) -> List[VariableGroup]:
    """Get groups that contain at least one template variable.
    
    Args:
        template_vars: List of variable names used in the template
        
    Returns:
        List of VariableGroup objects that have variables used by the template
    """
    result = []
    for group in self.vars.variable_groups:
      if any(var.name in template_vars for var in group.vars):
        result.append(group)
    return result

  def _resolve_variable_defaults(self, template_vars: List[str], template_defaults: Dict[str, Any] = None) -> Dict[str, Any]:
    """Resolve variable default values with priority handling.
    
    Priority order:
    1. Module variable defaults (low priority)
    2. Template's built-in defaults (medium priority)  
    3. User config defaults (high priority)
    """
    if template_defaults is None:
      template_defaults = {}
    
    # Start with module defaults, then override with template and user config
    defaults = self._get_variable_defaults_for_template(template_vars)
    defaults.update(template_defaults)
    defaults.update({var: value for var, value in self.config.get_variable_defaults(self.name).items() if var in template_vars})
    
    return defaults

  def _filter_variables_for_template(self, template_vars: List[str]) -> Dict[str, Any]:
    """Filter the variable groups to only include variables needed by the template."""
    filtered_vars = {}
    template_vars_set = set(template_vars)  # Convert to set for O(1) lookup
    
    for group in self._get_groups_with_template_vars(template_vars):
      # Get variables that match template vars and convert to dict format
      group_vars = {
        var.name: var.to_dict() for var in group.vars if var.name in template_vars_set
      }
      
      # Only include groups that have variables
      if group_vars:
        filtered_vars[group.name] = {
          'description': group.description,
          'enabled': group.enabled,
          'prompt_to_set': getattr(group, 'prompt_to_set', ''),
          'prompt_to_enable': getattr(group, 'prompt_to_enable', ''),
          'vars': group_vars
        }
    
    return filtered_vars

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
      group.name for group in self._get_groups_with_template_vars(template.vars)
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
    
    # Find template by ID
    template = self.libraries.find_by_id(module_name=self.name, files=self.files, template_id=id)
    if not template:
      logger.error(f"Template '{id}' not found")
      print(f"Template '{id}' not found.")
      return

    # Validate if the variables in the template are valid ones
    success, missing = self._validate_variables(template.vars)
    if not success:
      logger.error(f"Template '{id}' has invalid variables: {missing}")
      print(f"Template '{id}' has invalid variables: {missing}")
      return
    
    # Process variables using dedicated processor
    try:
      processor = VariableProcessor(self.vars, self.config, self.name)
      final_variable_values = processor.process_variables_for_template(template)
      logger.debug(f"Variable processing completed with {len(final_variable_values)} variables")
      
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
